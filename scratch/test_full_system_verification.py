import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from config.database import SessionLocal
from models.schemas import User, Appointment, Queue

class FullSystemVerificationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_01_landing_page_html(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        # Check Payment Method radio options
        self.assertIn('name="payment_method"', html)
        self.assertIn('value="Cash"', html)
        self.assertIn('value="GCash / E-Wallet"', html)
        self.assertIn('value="Bank Transfer"', html)
        # Check Tracking elements
        self.assertIn('id="res-payment-method"', html)
        self.assertIn('id="res-payment-status"', html)
        self.assertIn('id="res-fulfillment"', html)

    def test_02_customer_dashboard_html(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['user_role'] = 'Customer'
            sess['user_name'] = 'Customer Test'
        resp = self.client.get('/customer/dashboard')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn('id="cust-payment-method"', html)
        self.assertIn('💵 Cash (Counter/COD)', html)
        self.assertIn('📱 GCash / E-Wallet', html)
        self.assertIn('🏦 Bank Transfer', html)

    def test_03_manager_dashboard_html(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'Manager'
            sess['user_name'] = 'Manager Test'
        resp = self.client.get('/manager/dashboard')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        # Check Order Details Modal
        self.assertIn('id="order-details-modal"', html)
        self.assertIn('id="modal-order-id"', html)
        self.assertIn('id="modal-payment-status-badge"', html)
        self.assertIn('id="modal-payment-toggle-btn"', html)
        self.assertIn('id="modal-fulfillment-select"', html)
        # Check Order Lobby filter elements
        self.assertIn('id="appt-search-input"', html)
        self.assertIn('setLobbyFilter', html)
        self.assertIn('🚚 Condo Pickup & Delivery', html)
        self.assertIn('💵 Cash Pending / Unpaid', html)

    def test_04_payment_rules_and_lifecycle(self):
        future_slot = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00')

        # 1. Cash Order (Pending by default)
        resp_cash = self.client.post('/api/order/create', json={
            'name': 'Cash Customer',
            'phone_number': '09170001111',
            'handling_mode': 'Drop-off',
            'package_type': 'Classic (Wash, Dry, Fold)',
            'payment_method': 'Cash',
            'turnaround_option': '24 Hours',
            'schedule_time': future_slot
        })
        self.assertEqual(resp_cash.status_code, 201)
        cash_data = resp_cash.get_json()
        self.assertEqual(cash_data['payment_status'], 'Pending')
        cash_order_id = cash_data['order_id']

        # 2. GCash Order (Auto-Paid)
        resp_gcash = self.client.post('/api/order/create', json={
            'name': 'GCash Customer',
            'phone_number': '09180002222',
            'handling_mode': 'Pick-up & Delivery',
            'package_type': 'Premium Package',
            'payment_method': 'GCash / E-Wallet',
            'turnaround_option': '24 Hours',
            'schedule_time': future_slot
        })
        self.assertEqual(resp_gcash.status_code, 201)
        gcash_data = resp_gcash.get_json()
        self.assertEqual(gcash_data['payment_status'], 'Paid')
        gcash_order_id = gcash_data['order_id']

        # 3. Bank Transfer Order (Auto-Paid)
        resp_bank = self.client.post('/api/order/create', json={
            'name': 'Bank Customer',
            'phone_number': '09190003333',
            'handling_mode': 'Drop-off',
            'package_type': 'Saver Bundle',
            'payment_method': 'Bank Transfer',
            'turnaround_option': '2 Days',
            'schedule_time': future_slot
        })
        self.assertEqual(resp_bank.status_code, 201)
        bank_data = resp_bank.get_json()
        self.assertEqual(bank_data['payment_status'], 'Paid')

        # 4. Verify Tracking Endpoint for Cash & GCash
        track_cash = self.client.get(f'/api/order/track?q={cash_order_id}').get_json()['data']
        self.assertEqual(track_cash['payment_method'], 'Cash')
        self.assertEqual(track_cash['payment_status'], 'Pending')

        track_gcash = self.client.get(f'/api/order/track?q={gcash_order_id}').get_json()['data']
        self.assertEqual(track_gcash['payment_method'], 'GCash / E-Wallet')
        self.assertEqual(track_gcash['payment_status'], 'Paid')

        # 5. Manager Toggles Cash Order to Paid
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'Manager'
            sess['user_name'] = 'Manager Test'

        db = SessionLocal()
        try:
            cash_appt = db.query(Appointment).filter(Appointment.order_code == cash_order_id).first()
            cash_appt_id = cash_appt.appointment_id
        finally:
            db.close()

        toggle_res = self.client.post(f'/api/appointments/{cash_appt_id}/payment-status', json={
            'payment_status': 'Paid'
        })
        self.assertEqual(toggle_res.status_code, 200)

        # Verify tracking is now Paid
        track_cash_after = self.client.get(f'/api/order/track?q={cash_order_id}').get_json()['data']
        self.assertEqual(track_cash_after['payment_status'], 'Paid')

        # 6. Fulfillment Progression for GCash Order
        try:
            gcash_appt = db.query(Appointment).filter(Appointment.order_code == gcash_order_id).first()
            gcash_appt_id = gcash_appt.appointment_id
        finally:
            db.close()

        for stage in ['Picked Up', 'In Laundry', 'Out for Delivery', 'Delivered']:
            f_resp = self.client.post(f'/api/appointments/{gcash_appt_id}/fulfillment-status', json={
                'fulfillment_status': stage
            })
            self.assertEqual(f_resp.status_code, 200)
            track_stage = self.client.get(f'/api/order/track?q={gcash_order_id}').get_json()['data']
            self.assertEqual(track_stage['fulfillment_status'], stage)

if __name__ == '__main__':
    unittest.main()
