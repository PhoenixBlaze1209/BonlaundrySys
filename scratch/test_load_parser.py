import re

def parse_order_loads(load_details, total_machines=1, default_service_type='Wash-Dry-Fold'):
    details = (load_details or '').strip()
    loads = []
    
    # Example format:
    # "2 Machines: Load 1 [8kg Regular: Undergarments, Bras & Delicates (Self-Service Wash & Dry)]; Load 2 [13kg Titan: Other / Mixed Fabrics (Premium Complete Care (Sort & Superwash))]"
    # Split by semicolon or look for "Load X"
    load_chunks = re.split(r';\s*(?=Load\s+\d+)', details, flags=re.IGNORECASE)
    for chunk in load_chunks:
        m = re.search(r'Load\s+(\d+)\s*(?:\[(.*?)\]|\((.*?)\))', chunk, flags=re.IGNORECASE)
        if m:
            idx = int(m.group(1))
            body = (m.group(2) if m.group(2) is not None else m.group(3)) or ''
            # body example: "8kg Regular: Undergarments, Bras & Delicates (Self-Service Wash & Dry)"
            is_titan = ('13' in body.lower()) or ('titan' in body.lower())
            cap = 13 if is_titan else 8
            
            # Extract package if in parentheses at end of body
            pkg_m = re.search(r'\((.*)\)\s*$', body)
            pkg = pkg_m.group(1).strip() if pkg_m else default_service_type
            
            # Remove capacity prefix like "8kg Regular:" or "13kg Titan:"
            cleaned = re.sub(r'^\s*\d+kg\s*(Regular|Titan)?\s*:?', '', body, flags=re.IGNORECASE).strip()
            # Remove the package in parens from category
            if pkg_m:
                cat = re.sub(r'\((.*)\)\s*$', '', cleaned).strip(' -:')
            else:
                cat = cleaned.strip(' -:')
            if not cat:
                cat = 'Delicates & Clothes' if cap == 8 else 'Bulky Items / Mixed'
            
            loads.append({
                'load_index': idx,
                'capacity_kg': cap,
                'label': f"Load {idx} ({cap}kg {'Titan' if cap == 13 else 'Regular'})",
                'category': cat,
                'service_type': pkg or default_service_type,
                'raw': chunk.strip()
            })

    if not loads:
        n = max(1, total_machines or 1)
        for i in range(1, n + 1):
            is_titan = ('13' in details.lower()) or ('titan' in details.lower()) or ('13' in (default_service_type or '').lower())
            cap = 13 if is_titan else 8
            loads.append({
                'load_index': i,
                'capacity_kg': cap,
                'label': f"Load {i} ({cap}kg {'Titan' if cap == 13 else 'Regular'})",
                'category': 'General Laundry',
                'service_type': default_service_type,
                'raw': f"Load {i} ({cap}kg)"
            })
            
    return loads

if __name__ == '__main__':
    s1 = '2 Machines: Load 1 [8kg Regular: Undergarments, Bras & Delicates (Self-Service Wash & Dry)]; Load 2 [13kg Titan: Other / Mixed Fabrics (Premium Complete Care (Sort & Superwash))]'
    print("Parsed s1:", parse_order_loads(s1, 2))
    
    s2 = '1 Machine (8kg Regular)'
    print("Parsed s2:", parse_order_loads(s2, 1))
    
    s3 = '2 Machines (8kg Regular)'
    print("Parsed s3:", parse_order_loads(s3, 2))
