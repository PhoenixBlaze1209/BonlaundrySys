import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from config.database import SessionLocal
from models.schemas import Appointment, Queue

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_role'] = 'Staff'
        sess['user_name'] = 'Test Staff'
        
    print("Testing verification with various input formats for ORD-77663 (Appointment 195):")
    
    # 1. Number only: '77663'
    r1 = client.get('/api/staff/verify-order?code=77663')
    assert r1.status_code == 200, f"Expected 200 for '77663', got {r1.status_code}: {r1.data}"
    d1 = r1.get_json()
    assert d1['order']['order_code'] == 'ORD-77663'
    print("PASS: Number-only '77663' resolved to", d1['order']['order_code'])

    # 2. Canonical full code: 'ORD-77663'
    r2 = client.get('/api/staff/verify-order?code=ORD-77663')
    assert r2.status_code == 200, f"Expected 200 for 'ORD-77663', got {r2.status_code}"
    d2 = r2.get_json()
    assert d2['order']['order_code'] == 'ORD-77663'
    print("PASS: Full code 'ORD-77663' resolved to", d2['order']['order_code'])

    # 3. Lowercase without hyphen: 'ord77663'
    r3 = client.get('/api/staff/verify-order?code=ord77663')
    assert r3.status_code == 200, f"Expected 200 for 'ord77663', got {r3.status_code}"
    d3 = r3.get_json()
    assert d3['order']['order_code'] == 'ORD-77663'
    print("PASS: Unhyphenated 'ord77663' resolved to", d3['order']['order_code'])

    # 4. Hash prefix: '#77663'
    r4 = client.get('/api/staff/verify-order?code=%2377663')
    assert r4.status_code == 200, f"Expected 200 for '#77663', got {r4.status_code}"
    d4 = r4.get_json()
    assert d4['order']['order_code'] == 'ORD-77663'
    print("PASS: Hash-prefixed '#77663' resolved to", d4['order']['order_code'])

    # 5. Appointment ID: '195'
    r5 = client.get('/api/staff/verify-order?code=195')
    assert r5.status_code == 200, f"Expected 200 for '195', got {r5.status_code}"
    d5 = r5.get_json()
    assert d5['order']['order_code'] == 'ORD-77663'
    print("PASS: Appointment ID '195' resolved to", d5['order']['order_code'])

    # 6. Customer tracking search with number only: '77663'
    r6 = client.get('/api/order/track?q=77663')
    assert r6.status_code == 200, f"Expected 200 for customer tracking '77663', got {r6.status_code}: {r6.data}"
    d6 = r6.get_json()
    assert d6['data']['order_id'] == 'ORD-77663' or d6['data']['order_code'] == 'ORD-77663'
    print("PASS: Customer portal search with '77663' resolved to", d6['data'].get('order_code') or d6['data'].get('order_id'))

    # 7. Confirm order using number-only in payload: {'order_code': '77663'}
    r7 = client.post('/api/staff/confirm-order', json={
        'order_code': '77663',
        'reassign': True,
        'assignments': [
            {'load_index': 1, 'machine_id': 6},
            {'load_index': 2, 'machine_id': 2}
        ]
    })
    assert r7.status_code == 200, f"Expected 200 for confirm with '77663', got {r7.status_code}: {r7.data}"
    d7 = r7.get_json()
    assert d7['status'] in ('success', 'already_verified')
    print("PASS: Confirm-order with number-only '77663' succeeded!")

    # 8. Invalid code returns 404
    r8 = client.get('/api/staff/verify-order?code=000000')
    assert r8.status_code == 404, f"Expected 404 for '000000', got {r8.status_code}"
    print("PASS: Non-existent number '000000' properly returned 404.")

print("\nALL NUMERIC ORDER VERIFICATION TESTS PASSED SUCCESSFULLY!")
