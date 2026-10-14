import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from app import app
from config.database import SessionLocal
from models.schemas import Appointment, Queue, MachineStatus

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_role'] = 'Staff'
        sess['user_name'] = 'Test Staff'
    
    # 1. Lookup ORD-77663
    lookup_resp = client.get('/api/staff/verify-order?code=ORD-77663')
    assert lookup_resp.status_code == 200, f"Lookup failed: {lookup_resp.data}"
    lookup_data = lookup_resp.get_json()
    order = lookup_data['order']
    rec = order['machine_recommendation']
    print("1. Order Lookup:")
    print("   Total machines:", order['total_machines'])
    print("   Is multi-load:", rec['is_multi_load'])
    print("   Loads count in recommendation:", len(rec['loads']))
    
    load1_pick = rec['loads'][0]['best_pick']['machine_id']
    load2_pick = rec['loads'][1]['best_pick']['machine_id']
    print(f"   Recommended: Load 1 -> M{load1_pick}, Load 2 -> M{load2_pick}")
    
    # In DB, Machine 6 was already in use for Load 1. So Load 1 keeps Machine 6, Load 2 gets load2_pick.
    # If load2_pick is 6, pick an available machine (e.g. 7).
    if load2_pick == 6:
        load2_pick = 7
        
    payload = {
        'order_code': 'ORD-77663',
        'start_now': True,
        'assignments': [
            {'load_index': 1, 'machine_id': 6},
            {'load_index': 2, 'machine_id': load2_pick}
        ]
    }
    
    # 2. Confirm order
    confirm_resp = client.post('/api/staff/confirm-order', json=payload)
    print("2. Confirm Order Response status:", confirm_resp.status_code)
    confirm_data = confirm_resp.get_json()
    print("   Confirm result status:", confirm_data.get('status'))
    print("   Assigned machines count:", len(confirm_data.get('assigned_machines', [])))
    for a in confirm_data.get('assigned_machines', []):
        print("   ->", a['load_title'], a['machine_name'], "status:", a['status'], "started:", a['started_immediately'])
        
    # 3. Check DB
    db = SessionLocal()
    queues = db.query(Queue).filter(Queue.appointment_id == 195).order_by(Queue.queue_id.asc()).all()
    print(f"3. DB Verification for Appointment 195:")
    print(f"   Total Queue records: {len(queues)}")
    assert len(queues) == 2, f"Expected 2 queue records, got {len(queues)}"
    for q in queues:
        m = db.get(MachineStatus, q.machine_id)
        print(f"   Queue ID {q.queue_id}: Ticket #{q.queue_number} | M{q.machine_id} ({m.machine_name if m else 'N/A'}) | Status: {q.status} | Load: {q.load_details[:50]}...")
        assert q.queue_number == 94, f"Expected queue_number 94, got {q.queue_number}"
        assert q.machine_id in (6, load2_pick), f"Unexpected machine_id {q.machine_id}"
        assert m.status == 'In-Use', f"Machine {m.machine_id} should be In-Use"
        
    db.close()
    
    # 4. Lookup again - should show already_verified = True
    lookup2 = client.get('/api/staff/verify-order?code=ORD-77663').get_json()
    print("4. Re-lookup verification:")
    print("   Already verified:", lookup2['order']['already_verified'])
    assert lookup2['order']['already_verified'] is True, "Expected already_verified to be True now that both loads are assigned"
    print("   Assigned machines count:", len(lookup2['order']['assigned_machines']))
    assert len(lookup2['order']['assigned_machines']) == 2, "Expected 2 assigned machines in order response"
    
    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
