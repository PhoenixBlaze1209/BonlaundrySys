import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from config.database import SessionLocal
from models.schemas import Appointment, Queue, MachineStatus
from datetime import datetime

# 1. Create a dummy single-load appointment
db = SessionLocal()
order_code = 'ORD-TEST-SINGLE'
existing = db.query(Appointment).filter(Appointment.order_code == order_code).first()
if existing:
    db.query(Queue).filter(Queue.appointment_id == existing.appointment_id).delete()
    db.delete(existing)
    db.commit()

appt = Appointment(
    customer_id=1,
    order_code=order_code,
    customer_name='Single Load Test',
    customer_email='single@example.com',
    phone_number='09123456789',
    service_type='Wash-Dry-Fold',
    load_details='1 Machine (8kg Regular)',
    total_machines=1,
    turnaround_option='24 Hours',
    priority_level='Standard',
    order_mode='Drop-Off',
    payment_method='Cash',
    payment_status='Pending',
    fulfillment_status='Received',
    status='Pending',
    schedule_time=datetime.now()
)
db.add(appt)
db.commit()
appt_id = appt.appointment_id
db.close()

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_role'] = 'Staff'
        sess['user_name'] = 'Test Staff'
        
    # Lookup single-load
    res = client.get(f'/api/staff/verify-order?code={order_code}')
    assert res.status_code == 200
    data = res.get_json()
    order = data['order']
    assert order['total_machines'] == 1
    assert order['already_verified'] is False
    rec = order['machine_recommendation']
    assert rec['is_multi_load'] is False
    assert rec['best_pick'] is not None
    picked_mid = rec['best_pick']['machine_id']
    print(f"Single load recommendation: Machine {picked_mid} ({rec['best_pick']['machine_name']})")
    
    # Confirm single-load using legacy payload format: {'order_code': ..., 'machine_id': ..., 'start_now': True}
    confirm_res = client.post('/api/staff/confirm-order', json={
        'order_code': order_code,
        'machine_id': picked_mid,
        'start_now': True
    })
    assert confirm_res.status_code == 200
    c_data = confirm_res.get_json()
    assert c_data['status'] == 'success'
    print("Single load confirmed successfully, ticket:", c_data['queue_number'])
    
    # Check DB
    db = SessionLocal()
    q_list = db.query(Queue).filter(Queue.appointment_id == appt_id).all()
    assert len(q_list) == 1
    assert q_list[0].machine_id == picked_mid
    assert q_list[0].status == 'Processing'
    db.close()
    
    # Cleanup test appointment
    db = SessionLocal()
    from models.schemas import AuditLog
    db.query(AuditLog).filter(AuditLog.entity_id == order_code).delete()
    q_to_del = db.query(Queue).filter(Queue.appointment_id == appt_id).all()
    for q in q_to_del:
        m = db.get(MachineStatus, q.machine_id)
        if m:
            m.status = 'Available'
            m.assigned_customer_name = None
            m.cycle_type = None
            m.cycle_started_at = None
            m.cycle_ends_at = None
        db.delete(q)
    db.commit()
    db.query(Appointment).filter(Appointment.appointment_id == appt_id).delete()
    db.commit()
    db.close()
    
print("SINGLE LOAD REGRESSION TEST PASSED!")
