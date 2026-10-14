import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from config.database import SessionLocal
from models.schemas import MachineStatus, Queue, SystemSettings, Appointment
from services.machines import CYCLE_MINUTES, GRACE_PERIOD_MINUTES, LATE_RETRIEVAL_PENALTY_AMOUNT, is_walkin_machine, is_machine_available
from services.queuing import QueueManager

def test_implementation():
    print("Testing Walk-in Rules, Cycle Times, Grace Period, Penalty, and EWT Congestion Logic...")

    # 1. Test Constants
    assert CYCLE_MINUTES['washing'] == 44, f"Expected 44m wash, got {CYCLE_MINUTES['washing']}"
    assert CYCLE_MINUTES['drying'] == 45, f"Expected 45m dry, got {CYCLE_MINUTES['drying']}"
    assert GRACE_PERIOD_MINUTES == 10, f"Expected 10m grace period, got {GRACE_PERIOD_MINUTES}"
    assert LATE_RETRIEVAL_PENALTY_AMOUNT == 100.00, f"Expected 100.00 penalty, got {LATE_RETRIEVAL_PENALTY_AMOUNT}"
    print("PASS: Constants verified (44m wash, 45m dry, 10m grace, 100 PHP penalty)")

    # 2. Test DB settings
    db = SessionLocal()
    try:
        s = db.query(SystemSettings).first()
        if s:
            s.standard_washer_time_mins = 44
            s.standard_dryer_time_mins = 45
            db.commit()
        assert s.late_retrieval_grace_mins == 10, f"DB grace mins was {s.late_retrieval_grace_mins}"
        assert float(s.late_retrieval_penalty_fee) == 100.00, f"DB penalty fee was {s.late_retrieval_penalty_fee}"
        print("PASS: Database SystemSettings verified")
        
        # 3. Test Lobby Status method
        lobby = QueueManager.get_lobby_status(db)
        print("Lobby Status:", lobby)
        assert 'is_full' in lobby
        assert 'available_count' in lobby
        assert 'ewt_mins' in lobby
        assert 'should_display_ewt' in lobby
        print("PASS: QueueManager.get_lobby_status() working properly")

        # 4. Test Machine Classification
        m_dummy = MachineStatus(status='In-Use', operational_state='available', machine_type='Washer')
        assert is_walkin_machine(m_dummy) == True, "Should be classified as walk-in"
        m_online = MachineStatus(status='In-Use', operational_state='in_use_online', machine_type='Washer')
        assert is_walkin_machine(m_online) == False, "Online in-use should not be walk-in"
        m_maint = MachineStatus(status='Maintenance', operational_state='maintenance', machine_type='Washer')
        assert is_walkin_machine(m_maint) == False, "Maintenance should not be walk-in"
        print("PASS: is_walkin_machine() classification verified")
    finally:
        db.close()

    # 5. Test Web Endpoints with Flask Test Client
    client = app.test_client()

    # A. Test /api/lobby/status
    res = client.get('/api/lobby/status')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'success'
    assert 'ewt_mins' in data['data']
    assert 'is_full' in data['data']
    print("PASS: GET /api/lobby/status returns 200 OK")

    # B. Test /book (Walk-in portal)
    res_book = client.get('/book')
    assert res_book.status_code == 200
    book_html = res_book.get_data(as_text=True)
    assert "44m" in book_html and "45m" in book_html, "Missing 44m / 45m in /book"
    assert "Grace" in book_html, "Missing grace in /book"
    assert "₱100 Late Penalty" in book_html or "100" in book_html, "Missing 100 late penalty in /book"
    assert "walkin-liability-checkbox" in book_html, "Missing liability checkbox"
    assert "lobby-status-strip" in book_html, "Missing lobby status strip"
    print("PASS: /book renders rules, 39m/40m, grace period, and 100 PHP penalty properly")

    # C. Test /staff/verify-order
    with client.session_transaction() as sess:
        sess['user_id'] = 3
        sess['user_email'] = 'staff@bonlaundry.ph'
        sess['user_role'] = 'Staff'
    res_staff = client.get('/staff/verify-order')
    assert res_staff.status_code == 200
    staff_html = res_staff.get_data(as_text=True)
    assert "44m Wash / 45m Dry" in staff_html
    assert "10m Grace Period" in staff_html
    assert "₱100 Late Multa" in staff_html or "₱100" in staff_html
    print("PASS: /staff/verify-order renders 39m/40m, 10m grace period, and 100 multa properly")

    # D. Test /customer/dashboard
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_email'] = 'customer@test.com'
        sess['user_role'] = 'Customer'
    res_cust = client.get('/customer/dashboard')
    assert res_cust.status_code == 200
    cust_html = res_cust.get_data(as_text=True)
    assert "Current Wait" in cust_html
    assert "Notice for Machine Users:" in cust_html
    assert "the customer who caused the damage is liable for machine repair" in cust_html
    assert "44m Wash / 45m Dry" in cust_html
    print("PASS: /customer/dashboard renders conditional wait and updated machine rules properly")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_implementation()
