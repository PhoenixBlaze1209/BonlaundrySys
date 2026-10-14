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
# Also test the token without the prefix 4243| in case it's only the hash part
hash_part = token.split('|', 1)[1] if '|' in token else token

headers_list = [
    ("Bearer token", {'Authorization': f'Bearer {token}'}),
    ("Bearer hash_part", {'Authorization': f'Bearer {hash_part}'}),
    ("Token token", {'Authorization': f'Token {token}'}),
    ("X-API-KEY token", {'X-API-KEY': token}),
    ("x-api-key hash_part", {'x-api-key': hash_part}),
    ("api-key", {'api-key': token}),
    ("X-Auth-Token", {'X-Auth-Token': token}),
]

for name, h in headers_list:
    h['Accept'] = 'application/json'
    h['Content-Type'] = 'application/json'
    h['User-Agent'] = 'Mozilla/5.0'
    try:
        req = urllib.request.Request('https://app.philsms.com/api/v3/balance', headers=h)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read().decode('utf-8')
            print(f"[{name}]: {data}")
    except Exception as e:
        print(f"[{name}] error: {e}")
