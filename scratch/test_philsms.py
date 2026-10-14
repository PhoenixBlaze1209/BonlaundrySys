import os
import urllib.request
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
print("Loaded token:", token[:15] + "..." if token else "None")

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'User-Agent': 'BonLaundry/1.0'
}

endpoints_to_probe = [
    ('GET', 'https://app.philsms.com/api/v3/profile'),
    ('GET', 'https://app.philsms.com/api/v3/balance'),
    ('GET', 'https://app.philsms.com/api/v3/sender-ids'),
    ('GET', 'https://app.philsms.com/api/v3/sms'),
]

for method, url in endpoints_to_probe:
    print(f"\n--- Testing {method} {url} ---")
    try:
        req = urllib.request.Request(url, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode('utf-8')
            print(f"Status: {resp.status}")
            print(f"Response: {data[:500]}")
    except urllib.error.HTTPError as he:
        body = he.read().decode('utf-8', errors='ignore')
        print(f"HTTPError {he.code}: {body}")
    except Exception as e:
        print(f"Error: {e}")
