from datetime import datetime, timedelta
from models.schemas import MachineStatus, Queue


CYCLE_MINUTES = {'washing': 35, 'drying': 30}


def refresh_machine_cycles(db):
    now = datetime.now()
    finished = db.query(MachineStatus).filter(
        MachineStatus.cycle_ends_at.isnot(None), MachineStatus.cycle_ends_at <= now
    ).all()
    for machine in finished:
        if machine.operational_state == 'available':
            machine.status = 'Available'
        machine.assigned_customer_name = None
        machine.cycle_type = None
        machine.cycle_started_at = None
        machine.cycle_ends_at = None
        db.query(Queue).filter(Queue.machine_id == machine.machine_id, Queue.status == 'Processing').update({'status': 'Done'})
    if finished:
        db.commit()


def machine_payload(machine):
    now = datetime.now()
    remaining = max(0, int((machine.cycle_ends_at - now).total_seconds() / 60)) if machine.cycle_ends_at else 0
    if machine.operational_state in ('maintenance', 'not_available'):
        display_status = machine.operational_state
    elif machine.cycle_type:
        display_status = machine.cycle_type
    else:
        display_status = 'available'
    return {
        'machine_id': machine.machine_id, 'name': machine.machine_name or f'Machine {machine.machine_id}',
        'capacity_kg': machine.capacity_kg, 'price_per_cycle': float(machine.price_per_cycle or 0),
        'status': display_status, 'customer_name': machine.assigned_customer_name,
        'cycle_started_at': machine.cycle_started_at.isoformat() if machine.cycle_started_at else None,
        'cycle_ends_at': machine.cycle_ends_at.isoformat() if machine.cycle_ends_at else None,
        'remaining_minutes': remaining
    }


def start_machine_cycle(machine, customer_name, cycle_type):
    if machine.operational_state != 'available' or machine.status != 'Available':
        raise ValueError('Selected machine is not available.')
    if cycle_type not in CYCLE_MINUTES:
        raise ValueError('Select washing or drying.')
    now = datetime.now()
    machine.status = 'In-Use'
    machine.assigned_customer_name = customer_name
    machine.cycle_type = cycle_type
    machine.cycle_started_at = now
    machine.cycle_ends_at = now + timedelta(minutes=CYCLE_MINUTES[cycle_type])
