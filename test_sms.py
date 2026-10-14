import os
import sys
from services.sms_service import SMSService, _load_env

def main():
    _load_env()
    target_phone = sys.argv[1] if len(sys.argv) > 1 else '09171234567'
    print(f"Testing Semaphore SMS to: {target_phone}")
    
    api_key = os.getenv('SEMAPHORE_API_KEY')
    print(f"SEMAPHORE_API_KEY detected: {'YES (starts with ' + api_key[:6] + '...)' if api_key else 'NO (Check .env)'}")

    res = SMSService.send_cancellation_otp(target_phone, 'ORD-TEST', '849201')
    print("Result:", res)

if __name__ == '__main__':
    main()
