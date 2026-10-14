import xml.etree.ElementTree as ET
from pathlib import Path

f = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\level_0_system_overview.drawio")
root = ET.parse(f).getroot()
edges = [c for c in root.findall(".//mxCell") if c.get("edge") == "1"]
for i, e in enumerate(edges, 1):
    src = e.get("source")
    tgt = e.get("target")
    lbl = e.get("value")
    pts = e.findall(".//mxPoint")
    wpts = [(p.get("x"), p.get("y")) for p in pts]
    print(f"{i:2d}. [{src}] -> [{tgt}]: \"{lbl}\" (waypoints: {len(wpts)})")
