import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from app import app

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_role'] = 'Staff'
        sess['user_name'] = 'Test Staff'
    
    resp = client.get('/api/staff/verify-order?code=ORD-77663')
    print('Status code:', resp.status_code)
    data = resp.get_json()
    print('Status:', data.get('status'))
    order = data.get('order', {})
    print('Order code:', order.get('order_code'))
    print('Already verified:', order.get('already_verified'))
    print('Total machines:', order.get('total_machines'))
    print('Assigned machines:', json.dumps(order.get('assigned_machines'), indent=2))
    rec = order.get('machine_recommendation', {})
    print('Rec is_multi_load:', rec.get('is_multi_load'))
    for ld in rec.get('loads', []):
        bp = ld.get('best_pick') or {}
        print('Load', ld['load_index'], ld['label'], '-> Rec machine:', bp.get('machine_name'), 'ID:', bp.get('machine_id'), 'cap:', bp.get('capacity_kg'))
