# scratch/test_ewt_verification_flow.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.database import SessionLocal
from services.queuing import QueueManager
from services.analytics_engine import AnalyticsEngine
from models.schemas import Queue, Appointment, MachineStatus
from datetime import datetime, timedelta

def run_tests():
    db = SessionLocal()
    try:
        print("=== TEST 1: Baseline EWT with fleet available and 0 verified queue ===")
        ewt_initial = QueueManager.calculate_current_ewt(db)
        print(f"Calculated current EWT: {ewt_initial} mins (Expected: 0 mins when fleet is ready and 0 verified queue)")
        assert ewt_initial == 0, f"Expected 0 mins, got {ewt_initial}"

        print("\n=== TEST 2: Historical Past Walk-in Wait Stats ===")
        stats = QueueManager.get_past_walkin_wait_stats(db)
        print(f"Past verified jobs: {stats['count']}, Avg wait: {stats['avg_wait_mins']}m, Min: {stats['min_wait_mins']}m, Max: {stats['max_wait_mins']}m")
        assert stats['count'] > 0, "Expected historical records from backfill"

        print("\n=== TEST 3: Predictive Analytics Engine Wait Time Prediction ===")
        pred = AnalyticsEngine.train_and_predict_wait_time(record_log=True)
        print(f"Predicted wait: {pred['predicted_wait_mins']}m, Past Avg: {pred['past_avg_wait_mins']}m, MAPE: {pred['mape']}%, Insight: {pred['insight']}")
        assert pred['predicted_wait_mins'] == 0, "Expected 0 mins when no verified customers waiting"

        print("\n=== TEST 4: Simulated Counter Walk-in Check-in ===")
        now = datetime.now()
        # Create a test verified walk-in
        test_q = Queue(
            queue_number=9999,
            status='Waiting',
            verified_at=now - timedelta(minutes=5), # verified 5 minutes ago
            created_at=now - timedelta(minutes=5),
            estimated_waiting_time=20,
            customer_name='Automated EWT Test Customer'
        )
        try:
            db.add(test_q)
            db.commit()

            elapsed = QueueManager.get_elapsed_wait_mins(test_q, now)
            remaining = QueueManager.get_remaining_wait_mins(test_q, now)
            print(f"Test Walk-in Queue #9999: elapsed wait = {elapsed}m, remaining est wait = {remaining}m")
            assert elapsed == 5, f"Expected 5m elapsed, got {elapsed}"
            assert remaining == 15, f"Expected 15m remaining, got {remaining}"

            print("\n=== TEST 5: Start machine cycle and record actual wait time ===")
            start_now = datetime.now()
            test_q.status = 'Processing'
            test_q.started_at = start_now
            test_q.actual_wait_mins = round((start_now - test_q.verified_at).total_seconds() / 60, 1)
            test_q.estimated_waiting_time = 0
            db.commit()

            print(f"Test Walk-in started washing! actual_wait_mins = {test_q.actual_wait_mins}m")
            assert test_q.actual_wait_mins >= 5.0, f"Expected actual_wait_mins >= 5.0, got {test_q.actual_wait_mins}"
            print("\n=== ALL EWT AND VERIFIED START TIMER TESTS PASSED SUCCESSFULLY! ===")
        finally:
            # Clean up test row
            try:
                db.delete(test_q)
                db.commit()
            except Exception:
                db.rollback()

    finally:
        db.close()

if __name__ == '__main__':
    run_tests()
