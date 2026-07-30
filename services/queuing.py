# services/queuing.py
from config.database import SessionLocal
from models.schemas import Queue, SystemSettings, MachineStatus

class QueueManager:
    @staticmethod
    def calculate_current_ewt():
        """
        Calculates the baseline Estimated Waiting Time (EWT) in minutes
        for a new incoming customer based on unresolved jobs in the queue.
        """
        db = SessionLocal()
        try:
            # Fetch default machine configuration timings
            settings = db.query(SystemSettings).first()
            wash_time = settings.standard_washer_time_mins if settings else 35
            dry_time = settings.standard_dryer_time_mins if settings else 30
            avg_cycle_time = wash_time + dry_time # 65 minutes total average load time

            # Count how many machines are currently occupied
            occupied_machines = db.query(MachineStatus).filter(MachineStatus.status == 'In-Use').count()
            # Count total machines operational in the shop
            total_machines = db.query(MachineStatus).filter(MachineStatus.status != 'Maintenance').count()
            
            # Count how many people are currently waiting or processing
            active_queue_count = db.query(Queue).filter(Queue.status.in_(['Waiting', 'Processing'])).count()

            if total_machines == 0:
                return 0 # No active machines, wait time calculation defaults

            # Basic logic: (Active customers in line / available machine lanes) * time per complete process cycle
            estimated_wait = (active_queue_count / total_machines) * avg_cycle_time
            
            return int(estimated_wait)
        finally:
            db.close()

    @staticmethod
    def generate_next_queue_number():
        """
        Grabs the highest current queue number for the day and increments it by 1.
        """
        db = SessionLocal()
        try:
            last_queue = db.query(Queue).order_by(Queue.queue_number.desc()).first()
            if last_queue:
                return last_queue.queue_number + 1
            return 1 # Start at 1 if queue log is cleared or empty
        finally:
            db.close()