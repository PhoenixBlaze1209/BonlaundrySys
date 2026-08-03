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
    def send_password_reset(recipient, token):
        _load_local_smtp_environment()
        username, password = os.getenv('MAIL_USERNAME'), os.getenv('MAIL_APP_PASSWORD')
        if not username or not password:
            return False
        message = EmailMessage()
        message['Subject'], message['From'], message['To'] = 'Bon Laundry password reset', os.getenv('MAIL_FROM', username), recipient
        message.set_content(f'Use this password reset token within 30 minutes: {token}')
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
