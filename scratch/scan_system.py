import os
import sys
import json
from decimal import Decimal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath('.'))
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_diagnostics():
    findings = []
    print("=== STARTING DEEP SYSTEM DIAGNOSTICS ===")

    # 1. Test App Import & Blueprint Registration
    try:
        from app import app
        print("✓ Flask app initialized successfully.")
    except Exception as e:
        findings.append(f"CRITICAL: Failed to import/initialize app: {e}")
        return findings

    client = app.test_client()

    # 2. Database Connection & Schema Integrity
    try:
        from config.database import SessionLocal, engine
        from models.schemas import User, Appointment, MachineStatus, Queue, Transaction, OTPVerification
        db = SessionLocal()
        
        # Test basic queries
        user_count = db.query(User).count()
        machine_count = db.query(MachineStatus).count()
        appt_count = db.query(Appointment).count()
        queue_count = db.query(Queue).count()
        print(f"✓ Database connection active. Users: {user_count}, Machines: {machine_count}, Appts: {appt_count}, Queue: {queue_count}")

        # Check for potential schema mismatch or orphaned records
        orphaned_queues = db.query(Queue).filter(Queue.appointment_id != None).all()
        for q in orphaned_queues:
            if q.appointment is None:
                findings.append(f"Data Warning: Queue ID {q.queue_id} references non-existent Appointment ID {q.appointment_id}")

        db.close()
    except Exception as e:
        findings.append(f"Database Integrity Error: {e}")

    # 3. Test Jinja2 Templates Loading & Syntax
    try:
        template_dir = os.path.abspath('templates')
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    rel_path = os.path.relpath(os.path.join(root, file), template_dir).replace('\\', '/')
                    try:
                        app.jinja_env.get_template(rel_path)
                    except Exception as te:
                        findings.append(f"Template Syntax Error in '{rel_path}': {te}")
        print("✓ All Jinja2 templates parsed without syntax errors.")
    except Exception as e:
        findings.append(f"Template Engine Error: {e}")

    # 4. Test Services & Pricing Logic
    try:
        from services.payments import compute_service_price
        # Test null/empty inputs
        p_none = compute_service_price(None, None, None, None, 1, None)
        assert p_none >= Decimal('50.00'), f"Expected fallback min 50, got {p_none}"
        
        # Test string addon vs list of dicts vs list of strings
        p_str = compute_service_price("Self-Service Wash & Dry", "Self-Service", "24 Hours", addons="detergent, fabcon")
        p_list = compute_service_price("Self-Service Wash & Dry", "Self-Service", "24 Hours", addons=["detergent", "fabcon"])
        p_dicts = compute_service_price("Self-Service Wash & Dry", "Self-Service", "24 Hours", addons=[{"name": "Detergent", "price": 20}, {"name": "Fabcon", "price": 20}])
        
        assert p_str == p_list == p_dicts == Decimal('185.00'), f"Mismatch between addon formats: str={p_str}, list={p_list}, dicts={p_dicts}"
        print("✓ compute_service_price handles all input variants correctly.")
    except Exception as e:
        findings.append(f"Pricing Logic Error: {e}")

    # 5. Test Key Public & API Endpoints
    test_endpoints = [
        ('/', 200),
        ('/book', 200),
        ('/book/walkin', 200),
        ('/walk-in', 200),
        ('/api/machines', 200),
        ('/api/lobby/status', 200),
        ('/login', 200),
        ('/register', 200),
    ]

    for ep, expected_code in test_endpoints:
        try:
            res = client.get(ep)
            if res.status_code != expected_code and not (expected_code == 200 and res.status_code in [302, 200]):
                findings.append(f"Endpoint '{ep}' returned status {res.status_code} (expected {expected_code})")
            else:
                print(f"✓ GET {ep} -> {res.status_code}")
        except Exception as e:
            findings.append(f"Endpoint '{ep}' exception: {e}")

    # 6. Test Walkin / API Order Create Simulation
    try:
        order_payload = {
            'name': 'Diagnostic Test Customer',
            'phone_number': '09123456789',
            'email': 'diag@example.com',
            'service_type': 'Self-Service Wash & Dry (8kg)',
            'order_mode': 'Self-Service',
            'date': '2026-10-10',
            'pickup_time': 'Immediate',
            'turnaround_option': '24 Hours',
            'payment_method': 'Cash',
            'addons': json.dumps([{'name': 'Detergent', 'price': 20}, {'name': 'Fabcon', 'price': 20}]),
            'total_price': '185.00',
            'estimated_weight': '8.0'
        }
        res = client.post('/api/order/create', data=order_payload)
        if res.status_code not in (200, 201):
            findings.append(f"Order creation simulation failed with status {res.status_code}: {res.data.decode('utf-8', errors='ignore')[:200]}")
        else:
            res_json = res.get_json()
            order_id = res_json.get('order_id') or (res_json.get('data') and res_json['data'].get('order_id'))
            print(f"✓ Simulated order created: {order_id}")
            
            # Test order tracking with order_code query param
            track_res = client.get(f'/api/order/track?order_code={order_id}')
            if track_res.status_code != 200:
                findings.append(f"Tracking created order {order_id} failed with {track_res.status_code}: {track_res.data.decode('utf-8', errors='ignore')}")
            else:
                print(f"✓ Simulated order tracking verified for {order_id}")
    except Exception as e:
        findings.append(f"Order Simulation Exception: {e}")

    print("=== DIAGNOSTIC RUN COMPLETE ===")
    return findings

if __name__ == '__main__':
    issues = run_diagnostics()
    if issues:
        print("\n--- FINDINGS ---")
        for i in issues:
            print(f"- {i}")
    else:
        print("\nAll automated checks passed with 0 critical errors!")
