# scratch/test_ewt_logic.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.database import SessionLocal
from models.schemas import Queue, Appointment, MachineStatus, Transaction, SystemSettings
from datetime import datetime, timedelta

def test():
    db = SessionLocal()
    try:
        # Check verified vs unverified waiting queues
        all_waiting = db.query(Queue).filter(Queue.status == 'Waiting').all()
        print(f"Total waiting rows in tbl_queue: {len(all_waiting)}")
        
        verified_waiting = [q for q in all_waiting if q.verified_at is not None]
        unverified_waiting = [q for q in all_waiting if q.verified_at is None]
        print(f"Verified waiting (on floor): {len(verified_waiting)}")
        print(f"Unverified waiting (online/scheduled): {len(unverified_waiting)}")
        
        # Check machine statuses
        washers = db.query(MachineStatus).filter(MachineStatus.machine_type == 'Washer', MachineStatus.operational_state == 'available').all()
        avail_washers = [m for m in washers if m.status == 'Available']
        print(f"Operational washers: {len(washers)}, Available: {len(avail_washers)}")
        
    finally:
        db.close()

if __name__ == '__main__':
    test()
