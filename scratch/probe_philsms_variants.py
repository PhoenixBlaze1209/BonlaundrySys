import os
import urllib.request
import urllib.parse
import urllib.error
import json
from pathlib import Path

def load_env():
    env_file = Path(__file__).resolve().parent.parent / '.env'
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

load_env()
token = os.getenv('PHILSMS_API_KEY')

tests = [
    # 1. Bearer header
    ('https://app.philsms.com/api/v3/balance', {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}),
    # 2. Query param api_token
    (f'https://app.philsms.com/api/v3/balance?api_token={token}', {'Accept': 'application/json'}),
    # 3. api.philsms.com domain
    ('https://api.philsms.com/api/v3/balance', {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}),
    # 4. philsms.com domain
    ('https://philsms.com/api/v3/balance', {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}),
    # 5. POST sms/send with bearer
    ('https://app.philsms.com/api/v3/sms/send', {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}, json.dumps({
        'recipient': '09171234567',
        'sender_id': 'PhilSMS',
        'type': 'plain',
        'message': 'Test OTP'
    }).encode('utf-8')),
    # 6. POST sms/send with api_token in body
    ('https://app.philsms.com/api/v3/sms/send', {'Content-Type': 'application/json', 'Accept': 'application/json'}, json.dumps({
        'api_token': token,
        'recipient': '09171234567',
        'sender_id': 'PhilSMS',
        'type': 'plain',
        'message': 'Test OTP'
    }).encode('utf-8')),
]

for idx, item in enumerate(tests, 1):
    url = item[0]
    headers = item[1]
    data = item[2] if len(item) > 2 else None
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    print(f"\n[Test {idx}] {('POST' if data else 'GET')} {url[:45]}...")
    try:
        req = urllib.request.Request(url, data=data, method=('POST' if data else 'GET'), headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode('utf-8')
            print(f"  Status {resp.status}: {body[:250]}")
    except urllib.error.HTTPError as he:
        body = he.read().decode('utf-8', errors='ignore')
        print(f"  HTTPError {he.code}: {body[:250]}")
    except Exception as e:
        print(f"  Error: {e}")
