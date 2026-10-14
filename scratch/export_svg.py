# scratch/export_svg.py
import re
from pathlib import Path

html_path = Path(r"c:\Users\genes\bon-laundry\scratch\dfd_level0_preview.html")
svg_out = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\level_0_system_overview.svg")

content = html_path.read_text(encoding="utf-8")
match = re.search(r'(<svg[^>]*>.*?</svg>)', content, re.DOTALL)
if match:
    svg_code = match.group(1)
    svg_out.write_text(svg_code, encoding="utf-8")
    print(f"SUCCESS: Exported {svg_out} ({len(svg_code)} bytes)")
else:
    print("SVG not found in HTML!")
