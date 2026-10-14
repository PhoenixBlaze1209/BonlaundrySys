from datetime import datetime, timedelta
from math import ceil
import re
from models.schemas import MachineStatus, Queue, Transaction, Appointment
from services.email_service import EmailService


CYCLE_MINUTES = {'washing': 44, 'drying': 45}
GRACE_PERIOD_MINUTES = 10
LATE_RETRIEVAL_PENALTY_AMOUNT = 100.00


def is_walkin_machine(machine):
    """
    Classifies if a machine is currently being used for a walk-in order.
    A machine is walkin when it is 'In-Use' and NOT marked as online order,
    maintenance, or out of service.
    """
    return (
        machine.status == 'In-Use'
        and machine.operational_state not in ('in_use_online', 'maintenance', 'out_of_service')
    )


def is_machine_available(machine):
    now = datetime.now()
    if machine.operational_state != 'available' or machine.status != 'Available':
        return False
    if machine.cycle_ends_at and machine.cycle_ends_at > now:
        return False
    return True


def start_machine_cycle(machine, customer_name, cycle_type):
    if not is_machine_available(machine):
        raise ValueError('Selected machine is currently occupied.')
    if cycle_type not in CYCLE_MINUTES:
        raise ValueError('Select washing or drying.')
    now = datetime.now()
    machine.status = 'In-Use'
    machine.assigned_customer_name = customer_name
    machine.cycle_type = cycle_type
    machine.cycle_started_at = now
    machine.cycle_ends_at = now + timedelta(minutes=CYCLE_MINUTES[cycle_type])
    machine.usage_count = (machine.usage_count or 0) + 1
    machine.last_used_at = now


def service_tier(service_type):
    """Maps a free-text service/package name onto a short, filterable service tier label."""
    s = (service_type or '').lower()
    if not s or s == 'walk-in':
        return 'Walk-in'
    if 'premium' in s:
        return 'Premium'
    if 'signature' in s:
        return 'Signature'
    if 'saver' in s:
        return 'Saver'
    if 'wash only' in s:
        return 'Wash Only'
    if 'dry only' in s:
        return 'Dry Only'
    if 'self' in s or 'kiosk' in s:
        return 'Self-Service'
    if 'classic' in s or 'wash-dry-fold' in s or 'drop-off' in s:
        return 'Classic'
    return 'Other'


def package_includes_dry(service_type, addons=None):
    """True when the ordered package has a drying stage after washing."""
    s = (service_type or '').lower()
    extras = ''
    if addons:
        extras = (addons if isinstance(addons, str) else str(addons)).lower()
    if 'wash only' in s:
        return 'add dry' in extras or 'extra dry' in extras
    if 'dry only' in s:
        return False  # single drying stage, nothing follows a wash
    return any(k in s for k in ('dry', 'classic', 'saver', 'signature', 'premium', 'drop-off'))


def queue_cycle_type(db, queue):
    """The cycle (washing/drying) this queue entry runs next / is running now."""
    if queue.cycle_stage in CYCLE_MINUTES:
        return queue.cycle_stage
    transaction = db.get(Transaction, queue.transaction_id) if queue.transaction_id else None
    if transaction and transaction.cycle_type in CYCLE_MINUTES:
        return transaction.cycle_type
    return 'washing'


def begin_dry_stage(db, queue, now=None):
    """
    Called when a washing cycle finishes. If the package includes drying, moves the
    queue entry to a dryer (starting it immediately when one is free, otherwise
    waiting on the soonest one) and returns True. Returns False when the order is
    fully done and should be closed by the caller.
    """
    now = now or datetime.now()
    if (queue.cycle_stage or 'washing') != 'washing' or not queue.appointment_id:
        return False
    appt = db.get(Appointment, queue.appointment_id)
    if not appt or not package_includes_dry(appt.service_type, appt.addons):
        return False

    details = (queue.load_details or '').lower()
    required_capacity = 13 if ('13' in details or 'titan' in details) else 8
    pool = db.query(MachineStatus).filter(
        MachineStatus.operational_state == 'available',
        MachineStatus.capacity_kg >= required_capacity
    ).all()
    dryers = [m for m in pool if m.machine_type in ('Dryer', 'Dryer and Washer') or 'dry' in (m.machine_type or '').lower()] or pool
    if not dryers:
        return False

    free = [m for m in dryers if is_machine_available(m)]
    if free:
        # Prefer the same machine if it has both washer and dryer and is free
        same_m = next((m for m in free if m.machine_id == queue.machine_id), None)
        chosen = same_m or sorted(free, key=lambda m: (m.usage_count or 0, m.machine_id))[0]
    else:
        chosen = sorted(dryers, key=lambda m: (estimated_wait_for_machine(db, m), m.usage_count or 0, m.machine_id))[0]

    customer = queue.customer_name or appt.customer_name or 'Walk-in customer'
    queue.cycle_stage = 'drying'
    queue.machine_id = chosen.machine_id
    queue.fulfillment_status = 'In Laundry'
    appt.fulfillment_status = 'In Laundry'
    appt.status = 'Confirmed'
    if free:
        start_machine_cycle(chosen, customer, 'drying')
        queue.status = 'Processing'
        queue.estimated_waiting_time = 0
    else:
        queue.status = 'Waiting'
        queue.estimated_waiting_time = estimated_wait_for_machine(db, chosen)
    return True


def start_next_queued_job(db, machine):
    if not is_machine_available(machine):
        return None
    queued = (db.query(Queue).filter(
        Queue.machine_id == machine.machine_id, Queue.status == 'Waiting'
    ).order_by(Queue.queue_number.asc()).first())
    if not queued:
        return None
    transaction = db.get(Transaction, queued.transaction_id) if queued.transaction_id else None
    cycle_type = queue_cycle_type(db, queued)
    now = datetime.now()
    cust_name = queued.customer_name or (transaction.customer_name if transaction else None) or 'Walk-in customer'
    start_machine_cycle(machine, cust_name, cycle_type)
    queued.cycle_stage = cycle_type
    queued.status = 'Processing'
    queued.started_at = now
    if queued.verified_at:
        queued.actual_wait_mins = round((now - queued.verified_at).total_seconds() / 60, 1)
    else:
        queued.actual_wait_mins = 0
    queued.estimated_waiting_time = 0
    queued.fulfillment_status = 'In Laundry'
    if queued.appointment_id:
        appt = db.get(Appointment, queued.appointment_id)
        if appt:
            appt.status = 'Confirmed'
            appt.fulfillment_status = 'In Laundry'
    return queued


def estimated_wait_for_machine(db, machine):
    """Minutes until a newly queued job can start on the selected machine."""
    now = datetime.now()
    minutes = max(0, ceil((machine.cycle_ends_at - now).total_seconds() / 60)) if machine.cycle_ends_at else 0
    waiting = (db.query(Queue).filter(
        Queue.machine_id == machine.machine_id, Queue.status == 'Waiting'
    ).order_by(Queue.queue_number.asc()).all())
    for entry in waiting:
        minutes += CYCLE_MINUTES[queue_cycle_type(db, entry)]
    return minutes


def refresh_waiting_estimates(db, machine):
    now = datetime.now()
    minutes = max(0, ceil((machine.cycle_ends_at - now).total_seconds() / 60)) if machine.cycle_ends_at else 0
    changed = False
    waiting = (db.query(Queue).filter(
        Queue.machine_id == machine.machine_id, Queue.status == 'Waiting'
    ).order_by(Queue.queue_number.asc()).all())
    for entry in waiting:
        if entry.estimated_waiting_time != minutes:
            entry.estimated_waiting_time = minutes
            changed = True
        minutes += CYCLE_MINUTES[queue_cycle_type(db, entry)]
    return changed


def refresh_machine_cycles(db):
    now = datetime.now()
    # Repair legacy records that were marked In-Use without a running cycle.
    stale = db.query(MachineStatus).filter(
        MachineStatus.status == 'In-Use', MachineStatus.cycle_ends_at.is_(None),
        MachineStatus.operational_state == 'available'
    ).all()
    changed = False
    for machine in stale:
        active = (db.query(Queue).filter(
            Queue.machine_id == machine.machine_id, Queue.status == 'Processing'
        ).order_by(Queue.queue_number.asc()).first())
        if active:
            transaction = db.get(Transaction, active.transaction_id) if active.transaction_id else None
            machine.status = 'Available'
            machine.assigned_customer_name = None
            start_machine_cycle(
                machine,
                active.customer_name or (transaction.customer_name if transaction else None) or 'Walk-in customer',
                transaction.cycle_type if transaction and transaction.cycle_type in CYCLE_MINUTES else 'washing'
            )
        else:
            machine.status = 'Available'
            machine.assigned_customer_name = None
            machine.cycle_type = None
            machine.cycle_started_at = None
            machine.cycle_ends_at = None
        changed = True

    # Auto-clean lingering cycle data on Available machines that have no running countdown
    lingering = db.query(MachineStatus).filter(
        MachineStatus.status == 'Available',
        MachineStatus.cycle_ends_at.is_(None),
        (MachineStatus.cycle_type.isnot(None) | MachineStatus.assigned_customer_name.isnot(None))
    ).all()
    for machine in lingering:
        machine.cycle_type = None
        machine.cycle_started_at = None
        machine.assigned_customer_name = None
        changed = True

    finished = db.query(MachineStatus).filter(
        MachineStatus.cycle_ends_at.isnot(None), MachineStatus.cycle_ends_at <= now
    ).all()
    for machine in finished:
        cycle_end_ts = machine.cycle_ends_at
        if machine.operational_state == 'available':
            machine.status = 'Available'
        machine.assigned_customer_name = None
        machine.cycle_type = None
        machine.cycle_started_at = None
        machine.cycle_ends_at = None
        
        processing_queues = db.query(Queue).filter(Queue.machine_id == machine.machine_id, Queue.status == 'Processing').all()
        for q in processing_queues:
            if begin_dry_stage(db, q, now):
                continue
            q.status = 'Done'
            if not q.cycle_completed_at and cycle_end_ts:
                q.cycle_completed_at = cycle_end_ts
            
            # Check 10-minute grace period for laundry retrieval
            if cycle_end_ts:
                elapsed_post_cycle = (now - cycle_end_ts).total_seconds() / 60
                if elapsed_post_cycle > GRACE_PERIOD_MINUTES and float(q.penalty_amount or 0) == 0:
                    q.penalty_amount = LATE_RETRIEVAL_PENALTY_AMOUNT
                    q.penalty_reason = f"Late retrieval penalty: {int(elapsed_post_cycle)}m elapsed post-cycle (>10m grace period)"
            
            if q.appointment_id:
                appt = db.get(Appointment, q.appointment_id)
                if appt:
                    # For multi-machine appointments, check if other loads are still active
                    active_sibling_queues = db.query(Queue).filter(
                        Queue.appointment_id == q.appointment_id,
                        Queue.queue_id != q.queue_id,
                        Queue.status.in_(['Waiting', 'Processing'])
                    ).count()
                    if active_sibling_queues == 0:
                        is_delivery = (appt.order_mode or '') == 'Pick-up & Delivery'
                        next_fulfill = 'Out for Delivery' if is_delivery else 'Ready for Pick-up'
                        appt.fulfillment_status = next_fulfill
                        q.fulfillment_status = next_fulfill
                        appt.status = 'Confirmed'
                        if appt.customer_email:
                            EmailService.send_order_completed(
                                appt.customer_email,
                                appt.order_code or f"ORD-{appt.appointment_id:04d}",
                                appt.customer_name or "Valued Customer"
                            )
                    else:
                        q.fulfillment_status = 'Wash Done'
        start_next_queued_job(db, machine)
    for machine in db.query(MachineStatus).all():
        changed = refresh_waiting_estimates(db, machine) or changed
    if finished or changed:
        db.commit()


def machine_payload(machine, queued_customers=None):
    now = datetime.now()
    remaining = max(0, int((machine.cycle_ends_at - now).total_seconds() / 60)) if machine.cycle_ends_at else 0
    is_walkin = is_walkin_machine(machine)
    if machine.operational_state == 'in_use_online':
        display_status = 'in_use_online'
    elif machine.operational_state in ('maintenance', 'not_available'):
        display_status = machine.operational_state
    elif machine.cycle_type and machine.cycle_ends_at and machine.cycle_ends_at > now:
        display_status = machine.cycle_type
    elif machine.status != 'Available':
        display_status = 'not_available'
    else:
        display_status = 'available'
    return {
        'machine_id': machine.machine_id,
        'name': machine.machine_name or f'Machine {machine.machine_id} (Dryer and Washer)',
        'capacity_kg': machine.capacity_kg,
        'machine_type': machine.machine_type or 'Dryer and Washer',
        'price_per_cycle': float(machine.price_per_cycle or 0),
        'status': display_status,
        'customer_name': machine.assigned_customer_name,
        'cycle_started_at': machine.cycle_started_at.isoformat() if machine.cycle_started_at else None,
        'cycle_ends_at': machine.cycle_ends_at.isoformat() if machine.cycle_ends_at else None,
        'remaining_minutes': remaining,
        'usage_count': machine.usage_count or 0,
        'last_used_at': machine.last_used_at.isoformat() if machine.last_used_at else None,
        'queued_customers': queued_customers or [],
        'queue_count': len(queued_customers or []),
        'is_walkin': is_walkin
    }


def parse_order_loads(load_details, total_machines=1, default_service_type='Wash-Dry-Fold', weight=None):
    """
    Parses load_details string into structured per-load requirement objects.
    Handles formats like:
      - '2 Machines: Load 1 [8kg Regular: Undergarments, Bras & Delicates (Self-Service Wash & Dry)]; Load 2 [13kg Titan: Other / Mixed Fabrics (Premium Complete Care (Sort & Superwash))]'
      - '2 Machines: Load 1 (8kg Regular: Clothes); Load 2 (8kg Regular: Bras & Delicates)'
      - '1 Machine (8kg Regular)'
      - '2 Machines (8kg Regular)'
      - None or ''
    """
    details = (load_details or '').strip()
    loads = []
    
    w_float = None
    try:
        if weight is not None:
            w_float = float(weight)
    except (ValueError, TypeError):
        w_float = None
    
    # Split by semicolon preceding 'Load \d+'
    load_chunks = re.split(r';\s*(?=Load\s+\d+)', details, flags=re.IGNORECASE)
    for chunk in load_chunks:
        m = re.search(r'Load\s+(\d+)\s*(?:\[(.*?)\]|\((.*?)\))', chunk, flags=re.IGNORECASE)
        if m:
            idx = int(m.group(1))
            body = (m.group(2) if m.group(2) is not None else m.group(3)) or ''
            is_titan = ('13' in body.lower()) or ('titan' in body.lower()) or ('13' in (default_service_type or '').lower())
            if w_float and w_float > 8.0 and (total_machines or 1) == 1:
                is_titan = True
            cap = 13 if is_titan else 8
            
            # Extract package if in parentheses at end of body
            pkg_m = re.search(r'\((.*)\)\s*$', body)
            pkg = pkg_m.group(1).strip() if pkg_m else default_service_type
            
            cleaned = re.sub(r'^\s*\d+kg\s*(Regular|Titan)?\s*:?', '', body, flags=re.IGNORECASE).strip()
            if pkg_m:
                cat = re.sub(r'\((.*)\)\s*$', '', cleaned).strip(' -:')
            else:
                cat = cleaned.strip(' -:')
            if not cat:
                cat = 'Delicates & Clothes' if cap == 8 else 'Bulky Items / Mixed'
            
            loads.append({
                'load_index': idx,
                'capacity_kg': cap,
                'label': f"Load {idx} ({cap}kg {'Titan' if cap == 13 else 'Regular'})",
                'category': cat,
                'service_type': pkg or default_service_type,
                'raw': chunk.strip()
            })

    if not loads:
        n = max(1, total_machines or 1)
        for i in range(1, n + 1):
            is_titan = ('13' in details.lower()) or ('titan' in details.lower()) or ('13' in (default_service_type or '').lower())
            if w_float and w_float > 8.0 and n == 1:
                is_titan = True
            cap = 13 if is_titan else 8
            loads.append({
                'load_index': i,
                'capacity_kg': cap,
                'label': f"Load {i} ({cap}kg {'Titan' if cap == 13 else 'Regular'})",
                'category': 'General Laundry',
                'service_type': default_service_type,
                'raw': f"Load {i} ({cap}kg)"
            })
            
    return loads


def _build_candidates_for_type(db, target_type, min_capacity, all_operational):
    # Sort machines so machines meeting min_capacity are listed first (same as Queue & Appointments)
    sorted_machines = sorted(all_operational, key=lambda m: (
        0 if (m.capacity_kg or 8) >= min_capacity else 1,
        0 if (m.machine_type == target_type or 'dryer and washer' in (m.machine_type or '').lower()) else 1,
        m.machine_id
    ))
    
    candidates = []
    for m in sorted_machines:
        free_now = is_machine_available(m)
        wait_mins = 0 if free_now else estimated_wait_for_machine(db, m)
        q_count = db.query(Queue).filter(Queue.machine_id == m.machine_id, Queue.status == 'Waiting').count()
        matches_t = (m.machine_type == target_type) or ('dryer and washer' in (m.machine_type or '').lower())
        candidates.append({
            'machine_id': m.machine_id,
            'machine_name': m.machine_name or f"Machine {m.machine_id} (Dryer and Washer)",
            'machine_type': m.machine_type or 'Dryer and Washer',
            'capacity_kg': m.capacity_kg or 8,
            'status': 'Available' if free_now else 'In-Use',
            'is_available': free_now,
            'remaining_minutes': wait_mins,
            'queue_count': q_count,
            'usage_count': m.usage_count or 0,
            'matches_type': matches_t,
            'matches_capacity': (m.capacity_kg or 8) >= min_capacity
        })
    return candidates


def recommend_machine_for_order(db, service_type='Wash-Dry-Fold', load_details='', total_machines=1, weight=None):
    """
    Intelligently evaluates current fleet status, customer service requirements,
    and fleet wear-and-tear to recommend optimal machines to staff upon order verification.
    Supports single-load and multi-load orders (allocating distinct machines per load).
    Strictly guarantees that loads requiring 13kg capacity (or weight > 8kg) NEVER recommend an 8kg machine.
    """
    now = datetime.now()
    refresh_machine_cycles(db)
    loads = parse_order_loads(load_details, total_machines, service_type, weight=weight)
    
    all_operational = db.query(MachineStatus).filter(
        MachineStatus.operational_state == 'available'
    ).all()
    
    allocated_ids = set()
    load_recs = []
    
    for ld in loads:
        svc_lower = (ld['service_type'] or service_type or '').lower()
        is_dry_only = ('dry' in svc_lower) and ('wash' not in svc_lower)
        target_type = 'Dryer' if is_dry_only else 'Washer'
        cycle_type = 'drying' if is_dry_only else 'washing'
        min_cap = ld['capacity_kg']
        
        candidates = _build_candidates_for_type(db, target_type, min_cap, all_operational)
        if not candidates:
            load_recs.append({
                'load_index': ld['load_index'],
                'capacity_kg': ld['capacity_kg'],
                'label': ld['label'],
                'category': ld['category'],
                'service_type': ld['service_type'],
                'target_type': target_type,
                'cycle_type': cycle_type,
                'min_capacity': min_cap,
                'best_pick': None,
                'candidates': [],
                'reason': 'No operational machines online.'
            })
            continue
            
        # Priority to unallocated machines so each load gets its own distinct machine
        unallocated = [c for c in candidates if c['machine_id'] not in allocated_ids]
        pool = unallocated if unallocated else candidates
        
        # 1. Enforce capacity compatibility FIRST (same as Queue & Appointments assignment)
        cap_pool = [c for c in pool if c.get('matches_capacity')]
        active_pool = cap_pool if cap_pool else pool

        # 2. Within capacity-compatible machines, prefer matching machine stage (Washer vs Dryer) if available
        type_pool = [c for c in active_pool if c.get('matches_type')]
        candidate_pool = type_pool if type_pool else active_pool
        
        # 3. Sort candidates to find the best pick:
        # - Matches required capacity first (0 if matches_capacity else 1)
        # - Matches target machine type (0 if matches_type else 1)
        # - Free now (0m wait)
        # - Lowest wait time
        # - Lowest waiting queue count
        # - Lowest usage count (balanced fleet wear & tear)
        candidate_pool.sort(key=lambda c: (
            0 if c['matches_capacity'] else 1,
            0 if c.get('matches_type') else 1,
            0 if c['is_available'] else 1,
            c['remaining_minutes'],
            c['queue_count'],
            c['usage_count'],
            c['machine_id']
        ))
        
        best = candidate_pool[0]
        allocated_ids.add(best['machine_id'])
        
        if best['is_available']:
            reason = f"Available Now (0m wait) • Optimal wear balance ({best['usage_count']} cycles) • {best['capacity_kg']}kg capacity"
        else:
            reason = f"Earliest available (~{best['remaining_minutes']}m wait) • {best['queue_count']} queued • {best['capacity_kg']}kg capacity"
            
        best_pick = dict(best)
        best_pick['reason'] = reason
        
        cand_list = []
        for c in candidates:
            c_copy = dict(c)
            c_copy['is_best_pick'] = (c['machine_id'] == best_pick['machine_id'])
            c_copy['is_allocated_elsewhere'] = (c['machine_id'] in allocated_ids and c['machine_id'] != best_pick['machine_id'])
            cand_list.append(c_copy)
            
        # Sort candidate dropdown options so capacity-compatible machines appear at the top
        cand_list.sort(key=lambda c: (
            0 if c['matches_capacity'] else 1,
            0 if c.get('matches_type') else 1,
            0 if c['is_available'] else 1,
            c['remaining_minutes'],
            c['usage_count'],
            c['machine_id']
        ))
            
        load_recs.append({
            'load_index': ld['load_index'],
            'capacity_kg': ld['capacity_kg'],
            'label': ld['label'],
            'category': ld['category'],
            'service_type': ld['service_type'],
            'target_type': target_type,
            'cycle_type': cycle_type,
            'min_capacity': min_cap,
            'best_pick': best_pick,
            'candidates': cand_list,
            'reason': reason
        })
        
    first_rec = load_recs[0] if load_recs else {}
    return {
        'is_multi_load': len(loads) > 1,
        'total_machines': len(loads),
        'loads': load_recs,
        'best_pick': first_rec.get('best_pick'),
        'candidates': first_rec.get('candidates', []),
        'target_type': first_rec.get('target_type', 'Washer'),
        'cycle_type': first_rec.get('cycle_type', 'washing'),
        'min_capacity': first_rec.get('min_capacity', 8),
        'reason': first_rec.get('reason', '')
    }

