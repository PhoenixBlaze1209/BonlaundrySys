import re
import os

def check_html_ids(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all IDs defined in HTML: id="..."
    defined_ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', content))

    # Find all getElementById('...')
    get_elem_ids = set(re.findall(r'document\.getElementById\([\'"]([^\'"]+)[\'"]\)', content))

    # Find all querySelector('#...')
    qs_ids = set(re.findall(r'querySelector(?:All)?\([\'"]#([a-zA-Z0-9_\-]+)[\'"]\)', content))

    used_ids = get_elem_ids.union(qs_ids)

    missing = []
    for uid in sorted(used_ids):
        # Allow dynamic IDs that end with ${...} or are constructed
        if uid not in defined_ids and not uid.startswith('chk-') and not uid.startswith('addon-') and not uid.startswith('step-') and not uid.startswith('wizard-step-') and not uid.startswith('load-'):
            missing.append(uid)

    return missing, len(defined_ids), len(used_ids)

for p in ['templates/booking/walkin.html', 'templates/customer/dashboard.html']:
    missing, defined_count, used_count = check_html_ids(p)
    print(f"=== {p} ===")
    print(f"Defined IDs: {defined_count}, Used in JS: {used_count}")
    if missing:
        print("Potentially missing DOM IDs:")
        for m in missing:
            print(f"  - {m}")
    else:
        print("All static IDs verified!")
