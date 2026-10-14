import json, os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

from config.database import SessionLocal
from models.schemas import Appointment, Queue, User

def test_full_order_flow():
    client = app.test_client()

    print("--- 1. Testing /book and /walk-in public booking pages ---")
    res = client.get('/book')
    assert res.status_code == 200, f"Expected 200 on /book, got {res.status_code}"
    assert b"Walk-In" in res.data or b"Kiosk" in res.data
    print("PASS: /book loads successfully")

    res = client.get('/walk-in')
    assert res.status_code == 200, f"Expected 200 on /walk-in, got {res.status_code}"
    print("PASS: /walk-in loads successfully")

    print("\n--- 2. Testing Public Walk-In Order Placement (/api/order/create) ---")
    order_payload = {
        'service_type': 'Classic Care (Wash, Dry, Fold)',
        'order_mode': 'Drop-Off',
        'turnaround_option': '24 Hours',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'pickup_time': 'Immediate Walk-In / Now',
        'liability_agreed': 'true',
        'name': 'Test Walk-In Customer',
        'phone_number': '09171234567',
        'payment_method': 'Cash'
    }
    create_res = client.post('/api/order/create', data=order_payload)
    assert create_res.status_code in (200, 201), f"Expected 200/201, got {create_res.status_code}: {create_res.data}"

    create_data = create_res.get_json()
    assert create_data['status'] == 'success', f"Order creation failed: {create_data}"
    order_code = create_data.get('order_id') or create_data['data']['order_id']
    print(f"PASS: Walk-In order placed successfully with Code: {order_code}")

    print("\n--- 3. Testing Staff Verification Terminal Access & Lookup ---")
    # Simulate Staff Session
    with client.session_transaction() as sess:
        sess['user_id'] = 999
        sess['user_name'] = 'Test Staff'
        sess['user_role'] = 'Staff'

    # Terminal Page
    term_res = client.get('/staff/verify-order')
    assert term_res.status_code == 200, f"Expected 200 on /staff/verify-order, got {term_res.status_code}"
    assert b"Verification Terminal" in term_res.data
    print("PASS: Staff Verification Terminal page loads successfully")

    # API Lookup
    lookup_res = client.get(f'/api/staff/verify-order?code={order_code}')
    assert lookup_res.status_code == 200, f"Expected 200 on lookup, got {lookup_res.status_code}: {lookup_res.data}"
    lookup_data = lookup_res.get_json()
    assert lookup_data['status'] == 'success'
    assert lookup_data['order']['customer_name'] == 'Test Walk-In Customer'
    assert lookup_data['order']['status'] == 'Pending'
    print(f"PASS: Order code {order_code} looked up successfully! Details: {lookup_data['order']['customer_name']}, Status: {lookup_data['order']['status']}")

    print("\n--- 4. Testing Staff Confirm & Queue Order (/api/staff/confirm-order) ---")
    confirm_res = client.post('/api/staff/confirm-order', json={'order_code': order_code})
    assert confirm_res.status_code == 200, f"Expected 200 on confirm, got {confirm_res.status_code}: {confirm_res.data}"
    confirm_data = confirm_res.get_json()
    assert confirm_data['status'] in ('success', 'already_verified')
    queue_num = confirm_data['queue_number']
    print(f"PASS: Order {order_code} verified and enqueued with Queue #{queue_num}!")

    # Verify status changed in DB
    db = SessionLocal()
    try:
        appt = db.query(Appointment).filter(Appointment.order_code == order_code).first()
        assert appt is not None
        assert appt.status == 'Confirmed', f"Expected Confirmed status, got {appt.status}"
        assert appt.fulfillment_status == 'In Queue'
        print(f"PASS: DB verified! Appointment status is '{appt.status}', fulfillment is '{appt.fulfillment_status}'")
    finally:
        db.close()

    print("\n--- 5. Testing POS Deprecation Redirect ---")
    pos_res = client.get('/pos')
    assert pos_res.status_code == 302
    assert '/staff/verify-order' in pos_res.headers['Location']
    print("PASS: /pos redirects to /staff/verify-order")

    pos_chk = client.get('/pos/checkout')
    assert pos_chk.status_code == 302
    assert '/staff/verify-order' in pos_chk.headers['Location']
    print("PASS: /pos/checkout redirects to /staff/verify-order")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! 100%")

if __name__ == '__main__':
    test_full_order_flow()
