import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app

client = app.test_client()

# 1. Root Landing Page
r0 = client.get('/')
print("1. Root '/' status:", r0.status_code)
assert r0.status_code == 200

# 2. Manager Dashboard with session
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['user_role'] = 'Manager'
    sess['user_name'] = 'Admin Manager'
r_mgr = client.get('/manager/dashboard')
print("2. Manager Dashboard status:", r_mgr.status_code)
assert r_mgr.status_code == 200
assert b'openSignOutModal' in r_mgr.data
assert b'signout-confirm-modal' in r_mgr.data
print("   Manager sign-out modal successfully embedded!")

# 3. Customer Dashboard with session
with client.session_transaction() as sess:
    sess['user_id'] = 2
    sess['user_role'] = 'Customer'
    sess['user_name'] = 'Maria Santos'
r_cust = client.get('/customer/dashboard')
print("3. Customer Dashboard status:", r_cust.status_code)
assert r_cust.status_code == 200
assert b'openSignOutModal' in r_cust.data
assert b'signout-confirm-modal' in r_cust.data
print("   Customer sign-out modal successfully embedded!")

print("\n--- ALL SIGN-OUT MODAL RENDER TESTS PASSED! ---")
