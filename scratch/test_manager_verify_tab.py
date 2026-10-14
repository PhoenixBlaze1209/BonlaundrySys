import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

def test_manager_dashboard_verify():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Manager Test'
            sess['user_role'] = 'Manager'

        res = client.get('/manager/dashboard')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert b'id="view-verify"' in res.data, "view-verify tab missing"
        assert b'id="btn-verify"' in res.data, "btn-verify button missing"
        assert b'dashLookupOrder' in res.data, "dashLookupOrder function missing"
        assert b'switchTab(\'verify\')' in res.data or b'switchTab("verify")' in res.data, "switchTab verify missing"
        print("PASS: Manager dashboard rendered with integrated view-verify tab successfully!")

        # Also test staff dashboard (which includes manager dashboard)
        with client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['user_name'] = 'Staff Test'
            sess['user_role'] = 'Staff'

        res_staff = client.get('/staff/dashboard')
        assert res_staff.status_code == 200, f"Expected 200 on staff dashboard, got {res_staff.status_code}"
        assert b'id="view-verify"' in res_staff.data, "view-verify missing from staff view"
        assert b'id="btn-verify"' in res_staff.data, "btn-verify missing from staff view"
        print("PASS: Staff dashboard also inherits integrated view-verify tab successfully!")

if __name__ == '__main__':
    test_manager_dashboard_verify()
