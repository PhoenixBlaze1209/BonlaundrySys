import docx
from docx.oxml.ns import qn

doc = docx.Document('docs/BON_LAUNDRY_CUSTOMER_PORTAL_FUNCTIONAL_SPECIFICATION.docx')
for i, p in enumerate(doc.paragraphs):
    drawings = p._p.findall('.//' + qn('w:drawing'))
    if drawings:
        print(f'Paragraph {i}: {len(drawings)} drawing(s), text: "{p.text[:60]}"')
