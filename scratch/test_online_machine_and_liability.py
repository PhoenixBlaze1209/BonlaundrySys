import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from config.database import SessionLocal
from models.schemas import MachineStatus, User
from services.machines import is_machine_available, machine_payload

def run_tests():
    print("Running verification tests for Online Orders Machine State and Customer Liability Notice...")
    
    # 1. Test database model and services
    db = SessionLocal()
    try:
        machine = db.query(MachineStatus).first()
        if not machine:
            print("ERROR: No machine found in database.")
            sys.exit(1)
            
        orig_state = machine.operational_state
        orig_status = machine.status
        orig_cust = machine.assigned_customer_name
        
        print(f"Testing with Machine ID: {machine.machine_id} ({machine.machine_name})")
        print(f"Initial: status={orig_status}, state={orig_state}")
        
    finally:
        db.close()

    client = app.test_client()

    # Create manager session
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_email'] = 'manager@bonlaundry.ph'
        sess['user_role'] = 'Manager'

    # Test PUT /api/machines/<id> with in_use_online
    resp = client.put(f'/api/machines/{machine.machine_id}', json={
        'operational_state': 'in_use_online'
    })
    print("PUT /api/machines in_use_online response status:", resp.status_code)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.data}"
    
    data = resp.get_json()
    assert data['status'] == 'success'
    assert data['data']['status'] == 'in_use_online'
    print("PUT API returned status == 'in_use_online' successfully.")

    # Verify directly from DB
    db = SessionLocal()
    try:
        m_check = db.get(MachineStatus, machine.machine_id)
        assert m_check.operational_state == 'in_use_online'
        assert m_check.status == 'In-Use'
        assert not is_machine_available(m_check), "Machine in_use_online should NOT be available"
        print("DB check: operational_state='in_use_online', status='In-Use', is_machine_available=False verified.")
        
        payload = machine_payload(m_check)
        assert payload['status'] == 'in_use_online', f"Payload status was {payload['status']}"
        print("machine_payload display_status verified as 'in_use_online'.")
    finally:
        db.close()

    # Test GET /api/machines
    get_resp = client.get('/api/machines')
    assert get_resp.status_code == 200
    machines_list = get_resp.get_json()['data']
    target = next((item for item in machines_list if item['machine_id'] == machine.machine_id), None)
    assert target is not None
    assert target['status'] == 'in_use_online'
    print("GET /api/machines confirms machine status is 'in_use_online'.")

    # Test reverting back to available
    revert_resp = client.put(f'/api/machines/{machine.machine_id}', json={
        'operational_state': 'available'
    })
    assert revert_resp.status_code == 200
    
    # Restore original state
    db = SessionLocal()
    try:
        m_restore = db.get(MachineStatus, machine.machine_id)
        m_restore.operational_state = orig_state
        m_restore.status = orig_status
        m_restore.assigned_customer_name = orig_cust
        db.commit()
        print("Restored original machine state.")
    finally:
        db.close()

    # 2. Test Customer Dashboard HTML for liability notices & checkboxes
    # Temporarily set machine to in_use_online to test customer dashboard rendering
    db = SessionLocal()
    try:
        m_test = db.get(MachineStatus, machine.machine_id)
        m_test.operational_state = 'in_use_online'
        m_test.status = 'In-Use'
        db.commit()
    finally:
        db.close()

    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_email'] = 'customer@test.com'
        sess['user_role'] = 'Customer'

    cust_dash_resp = client.get('/customer/dashboard')
    assert cust_dash_resp.status_code == 200, f"Customer dashboard returned {cust_dash_resp.status_code}"
    html = cust_dash_resp.get_data(as_text=True)
    
    # Restore machine back
    db = SessionLocal()
    try:
        m_test = db.get(MachineStatus, machine.machine_id)
        m_test.operational_state = orig_state
        m_test.status = orig_status
        db.commit()
    finally:
        db.close()
    
    assert "Commercial Machine Protection &amp; Pocket Check Notice" in html or "Commercial Machine Protection & Pocket Check Notice" in html, "Missing Step 1 notice"
    assert "Customer Equipment Liability Agreement" in html, "Missing Step 4 agreement"
    assert "portal-liability-checkbox" in html, "Missing portal liability checkbox"
    assert "Equipment Protection &amp; Customer Liability Notice" in html or "Equipment Protection & Customer Liability Notice" in html, "Missing Tab 3 notice"
    assert "Notice for Machine Users:" in html, "Missing Tab 4 fleet notice"
    assert "In Use (Online)" in html, "Missing In Use (Online) badge in rendered customer dashboard"
    print("Customer Dashboard template verified: all liability notices, policy cards, and In Use (Online) badges present.")

    # 3. Test Walk-in Page HTML for liability notices & checkboxes
    walkin_resp = client.get('/book')
    assert walkin_resp.status_code == 200
    walkin_html = walkin_resp.get_data(as_text=True)
    assert "walkin-liability-checkbox" in walkin_html, "Missing walkin liability checkbox"
    assert "Equipment Protection &amp; Pocket Check Notice" in walkin_html or "Equipment Protection & Pocket Check Notice" in walkin_html, "Missing walkin Step 1 notice"
    assert "Customer Equipment Liability Agreement" in walkin_html, "Missing walkin Step 4 agreement"
    print("Walk-in booking template verified: liability notice, agreement, and checkbox present.")

    # 4. Test Manager Dashboard HTML for machine state dropdown & filter button
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_email'] = 'manager@bonlaundry.ph'
        sess['user_role'] = 'Manager'

    mgr_resp = client.get('/manager/dashboard')
    assert mgr_resp.status_code == 200
    mgr_html = mgr_resp.get_data(as_text=True)
    assert "m-filter-online" in mgr_html, "Missing m-filter-online button"
    assert "In Use (Online Orders)" in mgr_html, "Missing In Use (Online Orders) dropdown option"
    assert "releaseMachineToAvailable" in mgr_html, "Missing releaseMachineToAvailable JS function"
    assert "updateMachineDirectState" in mgr_html, "Missing updateMachineDirectState JS function"
    print("Manager Dashboard template verified: online orders filter, dropdown option, card state updater, and release function present.")

    # 5. Test Staff Order Verification HTML for liability acknowledgement badge
    with client.session_transaction() as sess:
        sess['user_id'] = 3
        sess['user_email'] = 'staff@bonlaundry.ph'
        sess['user_role'] = 'Staff'

    staff_verify_resp = client.get('/staff/verify-order')
    assert staff_verify_resp.status_code == 200
    staff_verify_html = staff_verify_resp.get_data(as_text=True)
    assert "Customer Equipment Liability Policy" in staff_verify_html, "Missing liability badge in verify-order template"
    assert "Acknowledged" in staff_verify_html, "Missing Acknowledged pill in verify-order template"
    print("Staff Verification template verified: Customer Equipment Liability Policy and Acknowledged badge present.")

    # 6. Test Backend validation of liability_agreed in /api/order/create
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_email'] = 'customer@test.com'
        sess['user_role'] = 'Customer'

    # Attempt to book with liability_agreed = false
    disagreed_resp = client.post('/api/order/create', json={
        'customer_name': 'Test User',
        'phone_number': '09123456789',
        'service_type': 'Saver Wash (8kg)',
        'order_mode': 'Drop-Off',
        'turnaround_option': 'Standard (48 hrs)',
        'payment_method': 'Cash',
        'liability_agreed': False
    })
    assert disagreed_resp.status_code == 400
    assert "liability" in disagreed_resp.get_json()['message'].lower()
    print("Backend API test: Disagreeing with liability agreement correctly returns HTTP 400 rejection.")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! (Code 0)")

if __name__ == '__main__':
    run_tests()
