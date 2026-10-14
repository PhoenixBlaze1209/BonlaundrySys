from flask import Blueprint, jsonify, request, session
from config.database import SessionLocal
from models.schemas import MachineStatus, Queue
from services.machines import (
    refresh_machine_cycles, machine_payload, is_machine_available,
    start_next_queued_job
)

from services.rbac import has_role, Role
from services.audit_service import AuditService, AuditAction

machines_bp = Blueprint('machines', __name__)


def _allowed(*roles):
    return has_role(*roles)


@machines_bp.route('/api/machines')
def machine_list():
    db = SessionLocal()
    try:
        refresh_machine_cycles(db)
        machines = db.query(MachineStatus).all()
        queue_rows = (db.query(Queue).filter(Queue.status == 'Waiting')
                      .order_by(Queue.queue_number.asc()).all())
        queued_by_machine = {}
        for entry in queue_rows:
            queued_by_machine.setdefault(entry.machine_id, []).append({
                'queue_number': entry.queue_number,
                'customer_name': entry.customer_name or 'Walk-in customer',
                'estimated_waiting_time': entry.estimated_waiting_time or 0
            })
        machines.sort(key=lambda machine: (
            0 if is_machine_available(machine) else 1,
            machine.usage_count or 0,
            (machine.last_used_at or machine.cycle_started_at or machine.cycle_ends_at).isoformat()
                if (machine.last_used_at or machine.cycle_started_at or machine.cycle_ends_at) else '',
            machine.machine_id
        ))
        return jsonify({'status': 'success', 'data': [
            machine_payload(machine, queued_by_machine.get(machine.machine_id, [])) for machine in machines
        ]})
    finally:
        db.close()


@machines_bp.route('/api/machines/<int:machine_id>', methods=['PUT'])
def update_machine(machine_id):
    if not _allowed(Role.MANAGER, Role.STAFF):
        return jsonify({'status': 'error', 'message': 'Manager or Staff access is required.'}), 403
    payload = request.get_json(silent=True) or request.form
    db = SessionLocal()
    try:
        machine = db.get(MachineStatus, machine_id)
        if not machine:
            return jsonify({'status': 'error', 'message': 'Machine not found.'}), 404
        if payload.get('machine_name'):
            machine.machine_name = payload['machine_name'].strip()
        if payload.get('capacity_kg'):
            machine.capacity_kg = int(payload['capacity_kg'])
        if payload.get('price_per_cycle'):
            machine.price_per_cycle = payload['price_per_cycle']
        state = payload.get('operational_state')
        if state:
            if state not in ('available', 'maintenance', 'not_available', 'in_use_online'):
                return jsonify({'status': 'error', 'message': 'Invalid machine state.'}), 400
            if machine.cycle_type and state != 'available':
                return jsonify({'status': 'error', 'message': 'Finish the active cycle before changing physical availability.'}), 409
            machine.operational_state = state
            if state == 'maintenance':
                machine.status = 'Maintenance'
            elif state == 'not_available':
                machine.status = 'In-Use'
            elif state == 'in_use_online':
                machine.status = 'In-Use'
                if not machine.assigned_customer_name or machine.assigned_customer_name in ('Idle / Open', ''):
                    machine.assigned_customer_name = payload.get('assigned_customer_name') or 'Online Order Batch'
            elif not machine.cycle_type:
                machine.status = 'Available'
                if machine.assigned_customer_name in ('Online Order Batch', 'Idle / Open'):
                    machine.assigned_customer_name = None
                start_next_queued_job(db, machine)
        db.commit()
        AuditService.log(
            action=AuditAction.MACHINE_STATE_CHANGED if state else AuditAction.MACHINE_PRICE_UPDATED,
            entity_type='Machine',
            entity_id=str(machine_id),
            details=f"Updated machine {machine.machine_name or machine_id}: state={machine.operational_state}, status={machine.status}, price={machine.price_per_cycle}"
        )
        return jsonify({'status': 'success', 'data': machine_payload(machine)})
    except (ValueError, TypeError) as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 400
    finally:
        db.close()
