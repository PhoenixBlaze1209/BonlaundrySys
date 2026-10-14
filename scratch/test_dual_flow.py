import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from app import app
from config.database import SessionLocal
from models.schemas import Appointment
from services.sms_service import _load_env

_load_env()

with app.app_context():
    client = app.test_client()
    db = SessionLocal()
    
    # 1. Test Order with Email AND Phone
    order_with_email = Appointment(
        order_code="ORD-TEST-EMAIL",
        customer_name="Juan Cruz",
        customer_email="gratisa1200@gmail.com",
        phone_number="09171234567",
        service_type="Wash & Fold",
        schedule_time=datetime.utcnow(),
        status="Pending"
    )
    
    # 2. Test Order with Phone ONLY (no email)
    order_phone_only = Appointment(
        order_code="ORD-TEST-PHONEONLY",
        customer_name="Maria Santos",
        customer_email=None,
        phone_number="09987654321",
        service_type="Wash & Fold",
        schedule_time=datetime.utcnow(),
        status="Pending"
    )
    
    db.add_all([order_with_email, order_phone_only])
    db.commit()
    db.refresh(order_with_email)
    db.refresh(order_phone_only)
    
    print("\n=======================================================")
    print("--- TEST CASE 1: With Registered Email ---")
    print("=======================================================")
    res1 = client.post('/api/order/cancel/request-otp', json={
        'order_id': order_with_email.order_code,
        'phone_number': '09171234567'
    })
    print("Response 1:", res1.get_json())
    
    print("\n=======================================================")
    print("--- TEST CASE 2: Phone ONLY (No Email) ---")
    print("=======================================================")
    res2 = client.post('/api/order/cancel/request-otp', json={
        'order_id': order_phone_only.order_code,
        'phone_number': '09987654321'
    })
    print("Response 2:", res2.get_json())
    
    # Cleanup test records
    db.delete(order_with_email)
    db.delete(order_phone_only)
    db.commit()
    db.close()
    print("\n--- ALL TESTS COMPLETED CLEANLY ---")
