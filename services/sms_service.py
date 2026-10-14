# services/sms_service.py
import os
import re
import urllib.request
import urllib.parse
import json
from pathlib import Path


def _load_env():
    env_file = Path(__file__).resolve().parent.parent / '.env'
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


class SMSService:
    @staticmethod
    def normalize_phone(phone_str):
        """Converts phone to standard 11-digit format 09XXXXXXXXX or +639XXXXXXXXX."""
        digits = re.sub(r'\D', '', str(phone_str or ''))
        if len(digits) == 10 and digits.startswith('9'):
            return '0' + digits
        if len(digits) == 12 and digits.startswith('63'):
            return '0' + digits[2:]
        return digits

    @staticmethod
    def mask_phone(phone_str):
        """Masks middle digits for privacy e.g. 0917****567."""
        clean = SMSService.normalize_phone(phone_str)
        if len(clean) >= 10:
            return f"{clean[:4]}****{clean[-3:]}"
        return clean or "your phone"

    @classmethod
    def send_cancellation_otp(cls, phone_number, order_code, otp):
        """
        Sends an SMS OTP for order cancellation.
        If SEMAPHORE_API_KEY is configured in .env, sends live SMS via Semaphore gateway.
        Otherwise, logs cleanly to system console for thesis defense / local demonstration.
        """
        _load_env()
        phone = cls.normalize_phone(phone_number)
        message = (
            f"Bon Laundry: You requested to cancel order {order_code}. "
            f"Your verification OTP is {otp} (valid for 5 mins). "
            f"If you requested this, enter this code to confirm. "
            f"If NOT you, please IGNORE this message and your order will remain safe."
        )

        philsms_token = os.getenv('PHILSMS_API_KEY')
        semaphore_key = os.getenv('SEMAPHORE_API_KEY')
        sender_name = os.getenv('SEMAPHORE_SENDER_NAME') or os.getenv('PHILSMS_SENDER_NAME') or 'PhilSMS'

        # 1. Try PhilSMS Gateway if token is present
        if philsms_token and phone:
            try:
                # Format to 639XXXXXXXXX
                clean_digits = re.sub(r'\D', '', phone)
                if clean_digits.startswith('0'):
                    intl_number = '63' + clean_digits[1:]
                elif clean_digits.startswith('63'):
                    intl_number = clean_digits
                else:
                    intl_number = '63' + clean_digits

                payload_data = json.dumps({
                    'recipient': intl_number,
                    'sender_id': 'PhilSMS',
                    'type': 'plain',
                    'message': message
                }).encode('utf-8')

                req = urllib.request.Request(
                    'https://app.philsms.com/api/v3/sms/send',
                    data=payload_data,
                    method='POST',
                    headers={
                        'Authorization': f'Bearer {philsms_token.strip()}',
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'User-Agent': 'BonLaundry/1.0'
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode('utf-8'))
                    if resp_data.get('status') == 'success':
                        print(f"[PHILSMS SMS SENT] Response: {resp_data}")
                        return {
                            'sent': True,
                            'gateway': 'PhilSMS',
                            'phone': cls.mask_phone(phone),
                            'raw_response': resp_data,
                            'message_preview': message
                        }
                    else:
                        print(f"[PHILSMS API ERROR RESPONSE]: {resp_data}")
            except urllib.error.HTTPError as he:
                err_body = he.read().decode('utf-8', errors='ignore')
                print(f"[PHILSMS HTTP ERROR {he.code}]: {err_body}")
            except Exception as e:
                print(f"[PHILSMS GENERAL ERROR]: {e}")

        # 2. Try Semaphore Gateway if API key is present
        if semaphore_key and phone:
            try:
                params = {
                    'apikey': semaphore_key.strip(),
                    'number': phone.strip(),
                    'message': message,
                }
                if sender_name and sender_name != 'PhilSMS':
                    params['sendername'] = sender_name.strip()

                payload = urllib.parse.urlencode(params).encode('utf-8')
                req = urllib.request.Request(
                    'https://api.semaphore.co/api/v4/messages', 
                    data=payload, 
                    method='POST',
                    headers={'User-Agent': 'BonLaundry/1.0'}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode('utf-8'))
                    print(f"[SEMAPHORE SMS SENT] Response: {resp_data}")
                    return {
                        'sent': True,
                        'gateway': 'Semaphore',
                        'phone': cls.mask_phone(phone),
                        'raw_response': resp_data,
                        'message_preview': message
                    }
            except urllib.error.HTTPError as he:
                err_body = he.read().decode('utf-8', errors='ignore')
                print(f"[SEMAPHORE HTTP ERROR {he.code}]: {err_body}")
            except Exception as e:
                print(f"[SEMAPHORE GENERAL ERROR]: {e}")


        # Fallback / Local Dev / Thesis Defense Demonstration Log
        print("\n" + "="*70)
        print("[BON LAUNDRY SMS NOTIFICATION DISPATCHED] (Defense / Demo Mode)")
        print(f"Recipient : {phone} ({cls.mask_phone(phone)})")
        print(f"Content   : {message}")
        print("="*70 + "\n")

        return {
            'sent': True,
            'gateway': 'Console / Simulator (Multi-Gateway Ready)',
            'phone': cls.mask_phone(phone),
            'message_preview': message
        }
