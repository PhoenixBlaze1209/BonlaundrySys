from flask import Blueprint, jsonify, request, session
from config.database import SessionLocal
from models.schemas import MachineStatus
from services.machines import refresh_machine_cycles, machine_payload

machines_bp = Blueprint('machines', __name__)


def _allowed(*roles):
    return session.get('user_role') in roles


@machines_bp.route('/api/machines')
def machine_list():
    if not _allowed('Manager', 'Staff', 'Customer'):
        return jsonify({'status': 'error', 'message': 'Unauthorized access.'}), 403
    db = SessionLocal()
    try:
        refresh_machine_cycles(db)
        machines = db.query(MachineStatus).order_by(MachineStatus.machine_id).all()
        return jsonify({'status': 'success', 'data': [machine_payload(machine) for machine in machines]})
    finally:
        db.close()


@machines_bp.route('/api/machines/<int:machine_id>', methods=['PUT'])
def update_machine(machine_id):
    if not _allowed('Manager'):
        return jsonify({'status': 'error', 'message': 'Manager access is required.'}), 403
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
            if state not in ('available', 'maintenance', 'not_available'):
                return jsonify({'status': 'error', 'message': 'Invalid machine state.'}), 400
            if machine.cycle_type and state != 'available':
                return jsonify({'status': 'error', 'message': 'Finish the active cycle before changing physical availability.'}), 409
            machine.operational_state = state
            machine.status = 'Maintenance' if state == 'maintenance' else ('Available' if state == 'available' else 'In-Use')
        db.commit()
        return jsonify({'status': 'success', 'data': machine_payload(machine)})
    except (ValueError, TypeError) as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 400
    finally:
        db.close()
