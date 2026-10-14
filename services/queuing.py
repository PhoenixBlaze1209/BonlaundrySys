# services/queuing.py
from math import ceil
from datetime import datetime
from sqlalchemy import or_
from config.database import SessionLocal
from models.schemas import Queue, SystemSettings, MachineStatus, PredictionLog

class QueueManager:
    @staticmethod
    def get_past_walkin_wait_stats(db):
        """
        Calculates historical wait times in minutes for past verified walk-ins and orders
        from counter verification (verified_at) to washing cycle start (started_at).
        """
        past_jobs = db.query(Queue).filter(
            Queue.actual_wait_mins.isnot(None),
            Queue.actual_wait_mins > 0
        ).all()
        
        if not past_jobs:
            # Calibrated baseline empirical wait time
            return {
                "count": 0,
                "avg_wait_mins": 20.0,
                "min_wait_mins": 10.0,
                "max_wait_mins": 30.0
            }
        
        waits = [float(j.actual_wait_mins) for j in past_jobs]
        return {
            "count": len(waits),
            "avg_wait_mins": round(sum(waits) / len(waits), 1),
            "min_wait_mins": round(min(waits), 1),
            "max_wait_mins": round(max(waits), 1)
        }

    @staticmethod
    def calculate_current_ewt(db_session=None):
        """
        Calculates and predicts the Estimated Waiting Time (EWT) in minutes
        for an incoming walk-in customer based on hardware cycle times (44m wash / 45m dry).
        
        Logic:
        1. Only considers orders that are VERIFIED (verified_at is set or counter walk-in).
           Unverified online bookings have not arrived at the shop yet and do not inflate floor wait.
        2. THRESHOLD: If washers are currently available (not full) and no waiting line,
           EWT is 0 (UI will hide EWT or display 'Available Now / Direct Loading').
        3. CONGESTION: Only when the lobby is FULL of in-use machines (0 available washers or waiting queue exists)
           does the system calculate the EWT using the 39-minute wash cycle countdowns.
        """
        db = db_session or SessionLocal()
        should_close = db_session is None
        try:
            now = datetime.now()
            
            from services.machines import is_machine_available, is_walkin_machine
            
            # Fetch machine configuration defaults (39 mins wash / 40 mins dry)
            settings = db.query(SystemSettings).first()
            wash_time = settings.standard_washer_time_mins if settings else 39
            
            # Operational washers (excluding maintenance, out of service)
            all_washers = db.query(MachineStatus).filter(
                or_(MachineStatus.machine_type.in_(['Washer', 'Dryer and Washer']), MachineStatus.machine_type.like('%Washer%'), MachineStatus.machine_type.is_(None))
            ).all()
            operational_washers = [
                m for m in all_washers
                if m.operational_state not in ('maintenance', 'out_of_service') and m.status != 'Maintenance'
            ]
            total_lanes = max(1, len(operational_washers))
            
            available_washers = [
                m for m in operational_washers 
                if is_machine_available(m)
            ]
            
            # Running washers with active countdown
            running_washers = [
                m for m in operational_washers 
                if m.status == 'In-Use' and m.cycle_ends_at and m.cycle_ends_at > now
            ]
            
            # Active verified jobs waiting on the floor:
            # Must be status == 'Waiting' AND (verified_at is not None or appointment_id is None)
            verified_waiting = db.query(Queue).filter(
                Queue.status == 'Waiting',
                or_(Queue.verified_at.isnot(None), Queue.appointment_id.is_(None))
            ).count()
            
            # THRESHOLD CHECK: If available washers can accommodate the waiting line,
            # this walk-in customer can immediately use a machine without waiting.
            # EWT is strictly 0 when machines are available!
            if len(available_washers) > verified_waiting:
                return 0
                
            # If all washers are running or there are waiting customers:
            # Lobby is FULL (congested). Calculate EWT based on deterministic cycle times.
            if running_washers:
                next_free_mins = min(
                    max(1, ceil((m.cycle_ends_at - now).total_seconds() / 60))
                    for m in running_washers
                )
            else:
                next_free_mins = 0
                
            if verified_waiting == 0:
                # All washers are occupied, but this customer is next in line
                return next_free_mins
                
            # Historical empirical wait time from past verified walk-ins
            stats = QueueManager.get_past_walkin_wait_stats(db)
            past_avg_wait = stats["avg_wait_mins"]
            
            # Number of turnovers needed to serve waiting verified queue + new incoming customer
            turnovers = ceil((verified_waiting + 1) / total_lanes)
            
            # Blended prediction: 50% historical empirical average wait modulated by queue load,
            # and 50% physical machine turnover time (based on 39m cycle)
            historical_component = past_avg_wait * turnovers
            physical_component = next_free_mins + (turnovers - 1) * wash_time
            
            predicted_ewt = int(round(0.5 * historical_component + 0.5 * physical_component))
            return max(1, predicted_ewt)
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_lobby_status(db_session=None):
        """
        Returns full real-time lobby status and machine breakdown,
        classifying walk-in in-use, online in-use, maintenance, and available washers.
        Determines if lobby is full to trigger EWT calculation.
        """
        db = db_session or SessionLocal()
        should_close = db_session is None
        try:
            now = datetime.now()
            from services.machines import is_machine_available, is_walkin_machine
            washers = db.query(MachineStatus).filter(
                or_(MachineStatus.machine_type.in_(['Washer', 'Dryer and Washer']), MachineStatus.machine_type.like('%Washer%'), MachineStatus.machine_type.is_(None))
            ).all()
            total_washers = len(washers)
            
            operational_washers = [
                m for m in washers 
                if m.operational_state not in ('maintenance', 'out_of_service') and m.status != 'Maintenance'
            ]
            available_washers = [
                m for m in operational_washers 
                if is_machine_available(m)
            ]
            walkin_in_use = [
                m for m in operational_washers 
                if is_walkin_machine(m)
            ]
            online_in_use = [
                m for m in operational_washers 
                if m.operational_state == 'in_use_online'
            ]
            maintenance = [
                m for m in washers 
                if m.status == 'Maintenance' or m.operational_state in ('maintenance', 'out_of_service')
            ]
            
            verified_waiting = db.query(Queue).filter(
                Queue.status == 'Waiting',
                or_(Queue.verified_at.isnot(None), Queue.appointment_id.is_(None))
            ).count()
            
            # Lobby is FULL ONLY when available washers are exhausted by in-use machines & waiting queue
            is_full = len(available_washers) <= verified_waiting
            ewt = QueueManager.calculate_current_ewt(db) if is_full else 0
            should_display = is_full and (ewt > 0)
            
            return {
                'is_full': is_full,
                'total_washers': total_washers,
                'available_count': len(available_washers),
                'walkin_in_use_count': len(walkin_in_use),
                'online_in_use_count': len(online_in_use),
                'maintenance_count': len(maintenance),
                'verified_waiting': verified_waiting,
                'ewt_mins': ewt,
                'should_display_ewt': should_display,
                'status_label': 'Lobby Full — In Queue' if should_display else 'Available Now — No Wait',
                'badge_class': 'bg-amber-100 text-amber-800' if should_display else 'bg-emerald-100 text-emerald-800'
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_elapsed_wait_mins(queue_entry, now=None):
        """
        Returns how many minutes have elapsed since the order was verified at the counter.
        Returns 0 if not verified yet.
        """
        if not queue_entry or not queue_entry.verified_at:
            return 0
        now = now or datetime.now()
        diff = (now - queue_entry.verified_at).total_seconds()
        return max(0, int(diff / 60))

    @staticmethod
    def get_remaining_wait_mins(queue_entry, now=None):
        """
        Calculates dynamic remaining wait time in minutes for a waiting verified order.
        As elapsed time increases from verification, remaining time decreases.
        """
        if not queue_entry:
            return 0
        if queue_entry.status in ('Processing', 'Done'):
            return 0
        if not queue_entry.verified_at:
            return queue_entry.estimated_waiting_time or 0
        elapsed = QueueManager.get_elapsed_wait_mins(queue_entry, now)
        base_est = queue_entry.estimated_waiting_time or 0
        return max(0, base_est - elapsed)

    @staticmethod
    def generate_next_queue_number(db=None):
        """
        Grabs the highest current legitimate queue number and increments it by 1.
        Guards against test or out-of-band sentinel numbers (>= 9000).
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        try:
            last_queue = (
                db.query(Queue)
                .filter(Queue.queue_number < 9000)
                .order_by(Queue.queue_number.desc())
                .first()
            )
            if last_queue and last_queue.queue_number:
                return last_queue.queue_number + 1
            return 1  # Start at 1 if queue log is cleared or empty
        finally:
            if should_close:
                db.close()
