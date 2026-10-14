import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def _load_local_smtp_environment():
    """Load local development SMTP settings without committing credentials."""
    env_file = Path(__file__).resolve().parent.parent / '.env'
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


class EmailService:
    @staticmethod
    def send_password_reset(recipient, otp):
        _load_local_smtp_environment()
        username, password = os.getenv('MAIL_USERNAME'), os.getenv('MAIL_APP_PASSWORD')
        if not username or not password:
            return False
        message = EmailMessage()
        message['Subject'], message['From'], message['To'] = 'Bon Laundry password reset', os.getenv('MAIL_FROM', username), recipient
        message.set_content(
            'Use this 6-digit OTP to reset your Bon Laundry password.\n\n'
            f'OTP: {otp}\n\n'
            'This OTP expires in 30 minutes. If you did not request this, ignore this email.'
        )
        try:
            with smtplib.SMTP(os.getenv('MAIL_HOST', 'smtp.gmail.com'), int(os.getenv('MAIL_PORT', '587')), timeout=15) as server:
                server.starttls(); server.login(username, password); server.send_message(message)
            return True
        except (OSError, smtplib.SMTPException):
            return False
    @staticmethod
    def send_receipt(recipient, transaction_id, total_amount, service_label):
        _load_local_smtp_environment()
        username = os.getenv('MAIL_USERNAME')
        password = os.getenv('MAIL_APP_PASSWORD')
        if not username or not password:
            return {'sent': False, 'message': 'Receipt not sent: SMTP is not configured.'}

        message = EmailMessage()
        message['Subject'] = f'Bon Laundry receipt — TRX-{transaction_id:04d}'
        message['From'] = os.getenv('MAIL_FROM', username)
        message['To'] = recipient
        message.set_content(
            f'Thank you for choosing Bon Laundry.\n\n'
            f'Service: {service_label}\n'
            f'Transaction: TRX-{transaction_id:04d}\n'
            f'Amount paid: PHP {total_amount:,.2f}\n'
        )
        try:
            with smtplib.SMTP(os.getenv('MAIL_HOST', 'smtp.gmail.com'), int(os.getenv('MAIL_PORT', '587')), timeout=15) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(message)
            return {'sent': True, 'message': 'Receipt email sent.'}
        except (OSError, smtplib.SMTPException) as error:
            return {'sent': False, 'message': f'Receipt email could not be sent: {error}'}

    @staticmethod
    def send_order_confirmation(recipient, order_code, customer_name, service_type, schedule_info):
        _load_local_smtp_environment()
        username = os.getenv('MAIL_USERNAME')
        password = os.getenv('MAIL_APP_PASSWORD')
        if not username or not password or not recipient:
            return {'sent': False, 'message': 'Email not configured.'}

        message = EmailMessage()
        message['Subject'] = f'Bon Laundry Order Confirmation — {order_code}'
        message['From'] = os.getenv('MAIL_FROM', username)
        message['To'] = recipient
        message.set_content(
            f'Hello {customer_name},\n\n'
            f'Thank you for ordering with Bon Laundry Station!\n\n'
            f'Your Order ID: {order_code}\n'
            f'Service: {service_type}\n'
            f'Schedule / Pickup: {schedule_info}\n\n'
            'You can track your live laundry progress anytime using your Order ID on our website.\n'
            'We will send you another update as soon as your laundry is washed, dried, and ready.\n\n'
            'Best regards,\nBon Laundry Station Team'
        )
        try:
            with smtplib.SMTP(os.getenv('MAIL_HOST', 'smtp.gmail.com'), int(os.getenv('MAIL_PORT', '587')), timeout=15) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(message)
            return {'sent': True, 'message': 'Confirmation email sent.'}
        except Exception as error:
            return {'sent': False, 'message': f'Confirmation email error: {error}'}

    @staticmethod
    def send_order_completed(recipient, order_code, customer_name):
        _load_local_smtp_environment()
        username = os.getenv('MAIL_USERNAME')
        password = os.getenv('MAIL_APP_PASSWORD')
        if not username or not password or not recipient:
            return {'sent': False, 'message': 'Email not configured.'}

        message = EmailMessage()
        message['Subject'] = f'Your Laundry is Ready! — {order_code}'
        message['From'] = os.getenv('MAIL_FROM', username)
        message['To'] = recipient
        message.set_content(
            f'Hello {customer_name},\n\n'
            f'Great news! Your laundry for Order ID {order_code} is now complete, fresh, and ready for pick-up / delivery.\n\n'
            'Thank you for trusting Bon Laundry Station!\n\n'
            'Bon Laundry Station Team'
        )
        try:
            with smtplib.SMTP(os.getenv('MAIL_HOST', 'smtp.gmail.com'), int(os.getenv('MAIL_PORT', '587')), timeout=15) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(message)
            return {'sent': True, 'message': 'Completion notification email sent.'}
        except Exception as error:
            return {'sent': False, 'message': f'Completion notification error: {error}'}

    @staticmethod
    def send_cancellation_otp(recipient, order_code, customer_name, otp):
        _load_local_smtp_environment()
        username = os.getenv('MAIL_USERNAME')
        password = os.getenv('MAIL_APP_PASSWORD')
        if not username or not password or not recipient:
            return {'sent': False, 'message': 'Email not configured.'}

        message = EmailMessage()
        message['Subject'] = f'Security Notice: Cancellation Verification for {order_code}'
        message['From'] = os.getenv('MAIL_FROM', username)
        message['To'] = recipient
        message.set_content(
            f'Hello {customer_name or "Valued Customer"},\n\n'
            f'A request was made to cancel your laundry reservation for Order: {order_code}.\n\n'
            f'Your Cancellation Verification Code is:\n'
            f'>>> {otp} <<<\n\n'
            '• If you initiated this cancellation, enter this 6-digit code on the website to confirm.\n'
            '• If you did NOT request this, please IGNORE this email. Your order will remain active and secure.\n\n'
            'This code will expire in 5 minutes.\n\n'
            'Best regards,\nBon Laundry Station Security Team'
        )
        try:
            with smtplib.SMTP(os.getenv('MAIL_HOST', 'smtp.gmail.com'), int(os.getenv('MAIL_PORT', '587')), timeout=15) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(message)
            return {'sent': True, 'message': 'Cancellation OTP email sent.'}
        except Exception as error:
            return {'sent': False, 'message': f'Cancellation OTP email error: {error}'}

