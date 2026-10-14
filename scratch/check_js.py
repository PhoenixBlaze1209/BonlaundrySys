import re
import subprocess

with open('templates/manager/dashboard.html', 'r', encoding='utf-8') as f:
    m_html = f.read()

scripts = re.findall(r'<script>(.*?)</script>', m_html, re.DOTALL)
for i, s in enumerate(scripts):
    mock_s = re.sub(r'\{\{.*?\}\}', '[]', s)
    mock_s = re.sub(r'\{%.*?%\}', '', mock_s)
    with open(f'scratch/mgr_script_{i}.js', 'w', encoding='utf-8') as out:
        out.write(mock_s)

res = subprocess.run(['node', '-c', 'scratch/mgr_script_0.js'], capture_output=True, text=True)
print('Manager JS syntax check exit code:', res.returncode)
if res.stderr:
    print('Manager JS errors:', res.stderr)
