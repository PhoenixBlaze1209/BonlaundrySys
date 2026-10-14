import os
import urllib.request
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

payload = json.dumps({
    "sender_id": "PhilSMS",
    "recipient": "+639171234567",
    "message": "Bon Laundry: Your cancellation OTP is 123456.",
    "type": "plain"
}).encode('utf-8')

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {token}"
}

req = urllib.request.Request("https://app.philsms.com/api/v3/sms/send", data=payload, method="POST", headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("Response:", resp.read().decode('utf-8'))
except urllib.error.HTTPError as he:
    print(f"HTTPError {he.code}:", he.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print("Error:", e)
