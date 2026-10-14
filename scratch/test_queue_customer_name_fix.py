import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from config.database import SessionLocal
from models.schemas import Queue, MachineStatus, Transaction
from services.machines import start_next_queued_job, is_machine_available
from services.queuing import QueueManager
from app import app

def test_start_next_queued_job():
    db = SessionLocal()
    try:
        # Find or create a test washer
        washer = db.query(MachineStatus).filter(
            MachineStatus.machine_type == 'Washer',
            MachineStatus.operational_state == 'available'
        ).first()
        assert washer is not None, "Need at least 1 washer"

        # Ensure washer is available
        washer.status = 'Available'
        washer.assigned_customer_name = None
        washer.cycle_type = None
        washer.cycle_started_at = None
        washer.cycle_ends_at = None

        # Create a test waiting queue entry for this washer
        next_num = QueueManager.generate_next_queue_number(db)
        q = Queue(
            queue_number=next_num,
            machine_id=washer.machine_id,
            customer_name="Test Queued Customer",
            status='Waiting',
            fulfillment_status='In Queue',
            verified_at=datetime.now()
        )
        db.add(q)
        db.commit()
        db.refresh(q)

        # Call start_next_queued_job
        res = start_next_queued_job(db, washer)
        db.commit()

        assert res is not None, "Expected start_next_queued_job to return the queued job"
        assert res.status == 'Processing'
        assert washer.status == 'In-Use'
        assert washer.assigned_customer_name == "Test Queued Customer"
        print("PASS: start_next_queued_job ran without NameError and assigned customer_name correctly!")

        # Clean up
        washer.status = 'Available'
        washer.assigned_customer_name = None
        washer.cycle_type = None
        washer.cycle_started_at = None
        washer.cycle_ends_at = None
        db.delete(q)
        db.commit()
    finally:
        db.close()

def test_advance_queue_api():
    db = SessionLocal()
    try:
        washer = db.query(MachineStatus).filter(
            MachineStatus.machine_type == 'Washer',
            MachineStatus.operational_state == 'available'
        ).first()
        washer.status = 'Available'
        washer.assigned_customer_name = None
        washer.cycle_ends_at = None

        next_num = QueueManager.generate_next_queue_number(db)
        q = Queue(
            queue_number=next_num,
            machine_id=washer.machine_id,
            customer_name="Test Advance Customer",
            status='Waiting',
            fulfillment_status='In Queue',
            verified_at=datetime.now()
        )
        db.add(q)
        db.commit()
        db.refresh(q)
        q_id = q.queue_id

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = 1
                sess['user_role'] = 'Staff'
                sess['user_name'] = 'Test Staff'

            res = client.post(f'/api/queue/{q_id}/advance')
            assert res.status_code == 200, f"Expected 200 from /advance, got {res.status_code}: {res.data}"
            print("PASS: /api/queue/<id>/advance ran without NameError!")

        # Clean up
        washer.status = 'Available'
        washer.assigned_customer_name = None
        washer.cycle_type = None
        washer.cycle_started_at = None
        washer.cycle_ends_at = None
        db.delete(q)
        db.commit()
    finally:
        db.close()

if __name__ == '__main__':
    test_start_next_queued_job()
    test_advance_queue_api()
    print("ALL TESTS PASSED SUCCESSFULLY!")
