import docx

doc = docx.Document('docs/BON_LAUNDRY_CUSTOMER_PORTAL_FUNCTIONAL_SPECIFICATION.docx')

print(f"Total paragraphs: {len(doc.paragraphs)}")
print(f"Total tables: {len(doc.tables)}")

for i, p in enumerate(doc.paragraphs):
    if p.text.strip():
        # print first 80 chars
        print(f"P{i:02d} [{p.style.name}]: {p.text[:90]}")
