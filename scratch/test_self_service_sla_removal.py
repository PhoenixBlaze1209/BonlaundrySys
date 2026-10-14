import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from datetime import datetime
from app import app
from config.database import SessionLocal
from models.schemas import Appointment

class TestSelfServiceSLARemoval(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.db = SessionLocal()

        # Clean existing test rows if any
        self.db.query(Appointment).filter(Appointment.order_code.in_(["ORD-TESTSELF", "ORD-TESTDROP"])).delete()
        self.db.commit()

        # Create a test self-service appointment
        self.self_order = Appointment(
            order_code="ORD-TESTSELF",
            customer_name="Test Self User",
            customer_email="testself@example.com",
            phone_number="09171234567",
            service_type="Self-Service Wash & Dry (8kg)",
            order_mode="Self-Service",
            turnaround_option=None,
            priority_level="Immediate",
            payment_method="Cash",
            payment_status="Pending",
            fulfillment_status="Waiting Drop-off",
            status="Pending",
            schedule_time=datetime.now()
        )
        self.db.add(self.self_order)

        # Create a test drop-off appointment
        self.dropoff_order = Appointment(
            order_code="ORD-TESTDROP",
            customer_name="Test Drop User",
            customer_email="testdrop@example.com",
            phone_number="09181234567",
            service_type="Drop-off Service (Wash, Dry, Fold)",
            order_mode="Drop-Off",
            turnaround_option="24 Hours",
            priority_level="Standard",
            payment_method="Cash",
            payment_status="Pending",
            fulfillment_status="Waiting Drop-off",
            status="Pending",
            schedule_time=datetime.now()
        )
        self.db.add(self.dropoff_order)
        self.db.commit()

    def tearDown(self):
        self.db.query(Appointment).filter(Appointment.order_code.in_(["ORD-TESTSELF", "ORD-TESTDROP"])).delete()
        self.db.commit()
        self.db.close()

    def test_verify_order_self_service_sla_null(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'Staff'
            sess['user_name'] = 'Staff Member'

        resp = self.client.get('/api/staff/verify-order?code=ORD-TESTSELF')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['status'] == 'success')
        self.assertIsNone(data['order']['turnaround_option'])
        self.assertEqual(data['order']['order_mode'], 'Self-Service')

    def test_verify_order_dropoff_sla_present(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'Staff'
            sess['user_name'] = 'Staff Member'

        resp = self.client.get('/api/staff/verify-order?code=ORD-TESTDROP')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['status'] == 'success')
        self.assertEqual(data['order']['turnaround_option'], '24 Hours')

    def test_track_order_self_service_sla_null(self):
        resp = self.client.get('/api/order/track?order_code=ORD-TESTSELF')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['status'] == 'success')
        self.assertIsNone(data['data']['turnaround_option'])
        self.assertIsNone(data['data']['target_ready_sla'])

    def test_track_order_dropoff_sla_present(self):
        resp = self.client.get('/api/order/track?order_code=ORD-TESTDROP')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['status'] == 'success')
        self.assertEqual(data['data']['turnaround_option'], '24 Hours')
        self.assertIsNotNone(data['data']['target_ready_sla'])

    def test_html_contains_turnaround_containers(self):
        with open('templates/staff/verify_order.html', 'r', encoding='utf-8') as f:
            staff_html = f.read()
        self.assertIn('id="card-turnaround-block"', staff_html)

        with open('templates/manager/dashboard.html', 'r', encoding='utf-8') as f:
            mgr_html = f.read()
        self.assertIn('id="dash-card-turnaround-block"', mgr_html)
        self.assertIn('id="modal-turnaround-sla-box"', mgr_html)

if __name__ == '__main__':
    unittest.main()
