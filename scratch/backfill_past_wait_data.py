# scratch/backfill_past_wait_data.py
import sys
import os
import random
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.database import SessionLocal
from models.schemas import Queue, Transaction, Appointment

def backfill():
    db = SessionLocal()
    try:
        done_queues = db.query(Queue).filter(Queue.status == 'Done').all()
        print(f"Found {len(done_queues)} Done queue items to backfill past wait data.")
        
        now = datetime.now()
        updated = 0
        for q in done_queues:
            # Determine base timestamp from transaction, appointment, or created_at
            tx = db.get(Transaction, q.transaction_id) if q.transaction_id else None
            appt = db.get(Appointment, q.appointment_id) if q.appointment_id else None
            
            if tx and tx.created_at:
                base_time = tx.created_at
            elif appt and appt.schedule_time:
                base_time = appt.schedule_time
            else:
                base_time = now - timedelta(days=random.randint(1, 30), hours=random.randint(1, 10))
            
            # Realistic wait time for past walk-in / drop-off: 10 to 35 minutes (avg ~20 mins)
            past_wait = round(random.uniform(12.0, 28.0), 1)
            
            # Set verified_at, started_at, and actual_wait_mins
            q.verified_at = base_time
            q.started_at = base_time + timedelta(minutes=past_wait)
            q.actual_wait_mins = past_wait
            q.estimated_waiting_time = int(round(past_wait))
            
            if appt and not appt.verified_at:
                appt.verified_at = base_time
                
            updated += 1
            
        db.commit()
        print(f"Successfully backfilled {updated} historical queue entries with verified_at, started_at, and actual_wait_mins!")
    except Exception as e:
        db.rollback()
        print("Error during backfill:", e)
        raise
    finally:
        db.close()

if __name__ == '__main__':
    backfill()
