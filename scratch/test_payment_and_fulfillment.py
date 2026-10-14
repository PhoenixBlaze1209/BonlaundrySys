import os
import sys
import unittest
from datetime import datetime, timedelta

# Add workspace to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from config.database import SessionLocal
from models.schemas import User, Appointment, Queue

class PaymentAndFulfillmentTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_cash_order_creation_and_payment_toggle(self):
        # 1. Create a Drop-off Cash order
        resp = self.client.post('/api/order/create', json={
            'name': 'Juan Dela Cruz',
            'phone_number': '09171234567',
            'handling_mode': 'Drop-off',
            'package_type': 'Classic (Wash, Dry, Fold)',
            'payment_method': 'Cash',
            'turnaround_option': '24 Hours',
            'schedule_time': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00')
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['payment_method'], 'Cash')
        self.assertEqual(data['payment_status'], 'Pending')
        self.assertEqual(data['fulfillment_status'], 'Waiting Drop-off')
        order_id = data['order_id']

        # 2. Track order
        track_resp = self.client.get(f'/api/order/track?q={order_id}')
        self.assertEqual(track_resp.status_code, 200)
        track_data = track_resp.get_json()['data']
        self.assertEqual(track_data['payment_method'], 'Cash')
        self.assertEqual(track_data['payment_status'], 'Pending')
        self.assertEqual(track_data['fulfillment_status'], 'Waiting Drop-off')

        # 3. Manager/Staff login session to test toggle
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'Manager'
            sess['user_name'] = 'Manager Test'

        # Find appointment_id from db
        db = SessionLocal()
        try:
            appt = db.query(Appointment).filter(Appointment.order_code == order_id).first()
            self.assertIsNotNone(appt)
            appt_id = appt.appointment_id
        finally:
            db.close()

        # Toggle to Paid
        pay_toggle_resp = self.client.post(f'/api/appointments/{appt_id}/payment-status', json={
            'payment_status': 'Paid'
        })
        self.assertEqual(pay_toggle_resp.status_code, 200)
        self.assertEqual(pay_toggle_resp.get_json()['data']['payment_status'], 'Paid')

        # Verify tracking reflects Paid
        track_resp2 = self.client.get(f'/api/order/track?q={order_id}')
        self.assertEqual(track_resp2.get_json()['data']['payment_status'], 'Paid')

        # Toggle fulfillment stage to In Laundry
        fulfill_resp = self.client.post(f'/api/appointments/{appt_id}/fulfillment-status', json={
            'fulfillment_status': 'In Laundry'
        })
        self.assertEqual(fulfill_resp.status_code, 200)

        track_resp3 = self.client.get(f'/api/order/track?q={order_id}')
        self.assertEqual(track_resp3.get_json()['data']['fulfillment_status'], 'In Laundry')

    def test_ewallet_order_auto_paid(self):
        # Create Condo Pickup GCash order
        resp = self.client.post('/api/order/create', json={
            'name': 'Ana Lim',
            'phone_number': '09189876543',
            'handling_mode': 'Pick-up & Delivery',
            'package_type': 'Premium Package',
            'payment_method': 'GCash / E-Wallet',
            'turnaround_option': '2 Days',
            'building': '5',
            'unit': '402',
            'schedule_time': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT14:00')
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['payment_method'], 'GCash / E-Wallet')
        self.assertEqual(data['payment_status'], 'Paid')  # Digital payments auto-marked Paid!
        self.assertEqual(data['fulfillment_status'], 'For Pickup')
        self.assertEqual(data['priority_level'], 'Graveyard Batch')

    def test_bank_transfer_order_auto_paid(self):
        # Create Bank Transfer order
        resp = self.client.post('/api/order/create', json={
            'name': 'Carlos Gomez',
            'phone_number': '09201112233',
            'handling_mode': 'Drop-off',
            'package_type': 'Saver Bundle',
            'payment_method': 'Bank Transfer',
            'turnaround_option': '24 Hours',
            'schedule_time': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%dT11:00')
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['payment_method'], 'Bank Transfer')
        self.assertEqual(data['payment_status'], 'Paid')

if __name__ == '__main__':
    unittest.main()
