import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.database import SessionLocal
from models.schemas import MachineStatus, Queue
from services.machines import (
    refresh_machine_cycles, is_machine_available, estimated_wait_for_machine
)
import re

def parse_order_loads(load_details, total_machines=1, default_service_type='Wash-Dry-Fold'):
    details = (load_details or '').strip()
    loads = []
    load_chunks = re.split(r';\s*(?=Load\s+\d+)', details, flags=re.IGNORECASE)
    for chunk in load_chunks:
        m = re.search(r'Load\s+(\d+)\s*(?:\[(.*?)\]|\((.*?)\))', chunk, flags=re.IGNORECASE)
        if m:
            idx = int(m.group(1))
            body = (m.group(2) if m.group(2) is not None else m.group(3)) or ''
            is_titan = ('13' in body.lower()) or ('titan' in body.lower())
            cap = 13 if is_titan else 8
            
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


def build_candidates_for_type(db, target_type, min_capacity, all_operational):
    matching = [m for m in all_operational if m.machine_type == target_type]
    if not matching:
        matching = all_operational
    
    candidates = []
    for m in matching:
        free_now = is_machine_available(m)
        wait_mins = 0 if free_now else estimated_wait_for_machine(db, m)
        q_count = db.query(Queue).filter(Queue.machine_id == m.machine_id, Queue.status == 'Waiting').count()
        candidates.append({
            'machine_id': m.machine_id,
            'machine_name': m.machine_name or f"{m.machine_type} #{m.machine_id:02d}",
            'machine_type': m.machine_type,
            'capacity_kg': m.capacity_kg or 8,
            'status': 'Available' if free_now else 'In-Use',
            'is_available': free_now,
            'remaining_minutes': wait_mins,
            'queue_count': q_count,
            'usage_count': m.usage_count or 0,
            'matches_capacity': (m.capacity_kg or 8) >= min_capacity
        })
    return candidates


def recommend_machine_for_order(db, service_type='Wash-Dry-Fold', load_details='', total_machines=1):
    refresh_machine_cycles(db)
    loads = parse_order_loads(load_details, total_machines, service_type)
    
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
        
        candidates = build_candidates_for_type(db, target_type, min_cap, all_operational)
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
            
        # Unallocated pool preferred
        unallocated = [c for c in candidates if c['machine_id'] not in allocated_ids]
        pool = unallocated if unallocated else candidates
        
        # Sort candidates
        pool.sort(key=lambda c: (
            0 if c['matches_capacity'] else 1,
            0 if c['is_available'] else 1,
            c['remaining_minutes'],
            c['queue_count'],
            c['usage_count'],
            c['machine_id']
        ))
        
        best = pool[0]
        allocated_ids.add(best['machine_id'])
        
        if best['is_available']:
            reason = f"Available Now (0m wait) • Optimal wear balance ({best['usage_count']} cycles) • {best['capacity_kg']}kg capacity"
        else:
            reason = f"Earliest available (~{best['remaining_minutes']}m wait) • {best['queue_count']} queued • {best['capacity_kg']}kg capacity"
            
        best_pick = dict(best)
        best_pick['reason'] = reason
        
        # Mark in candidate list
        cand_list = []
        for c in candidates:
            c_copy = dict(c)
            c_copy['is_best_pick'] = (c['machine_id'] == best_pick['machine_id'])
            c_copy['is_allocated_elsewhere'] = (c['machine_id'] in allocated_ids and c['machine_id'] != best_pick['machine_id'])
            cand_list.append(c_copy)
            
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

if __name__ == '__main__':
    db = SessionLocal()
    order_details = "2 Machines: Load 1 [8kg Regular: Undergarments, Bras & Delicates (Self-Service Wash & Dry)]; Load 2 [13kg Titan: Other / Mixed Fabrics (Premium Complete Care (Sort & Superwash))]"
    res = recommend_machine_for_order(db, 'Drop-off Service', order_details, 2)
    print("Is multi load:", res['is_multi_load'])
    for ld in res['loads']:
        bp = ld['best_pick']
        print(f"Load {ld['load_index']} ({ld['capacity_kg']}kg) -> Best Pick: {bp['machine_name']} (ID {bp['machine_id']}, {bp['capacity_kg']}kg, {bp['status']})")
    db.close()
