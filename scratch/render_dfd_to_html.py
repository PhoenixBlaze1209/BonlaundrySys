# scratch/render_dfd_to_html.py
"""
Renders level_0_system_overview.drawio into a standalone HTML+SVG page
for visual verification and high-res export.
"""

import xml.etree.ElementTree as ET
import html as htmllib
from pathlib import Path

DRAWIO_PATH = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\level_0_system_overview.drawio")
OUT_HTML = Path(r"c:\Users\genes\bon-laundry\scratch\dfd_level0_preview.html")

tree = ET.parse(DRAWIO_PATH)
root = tree.getroot()

# Find mxGraphModel
model = root.find(".//mxGraphModel")
pw = int(model.get("pageWidth", 2800))
ph = int(model.get("pageHeight", 2050))

cells = root.findall(".//mxCell")

# Separate vertices and edges
vertices = {}
edges = []

for c in cells:
    cid = c.get("id")
    if cid in ("0", "1"):
        continue
    val = c.get("value", "")
    style = c.get("style", "")
    geom = c.find("mxGeometry")
    
    if c.get("vertex") == "1" and geom is not None:
        x = float(geom.get("x", 0))
        y = float(geom.get("y", 0))
        w = float(geom.get("width", 0))
        h = float(geom.get("height", 0))
        vertices[cid] = {
            "id": cid, "val": val, "style": style,
            "x": x, "y": y, "w": w, "h": h
        }
    elif c.get("edge") == "1":
        src = c.get("source")
        tgt = c.get("target")
        pts = []
        arr = c.find(".//Array")
        if arr is not None:
            for pt in arr.findall("mxPoint"):
                pts.append((float(pt.get("x")), float(pt.get("y"))))
        
        edges.append({
            "id": cid, "val": val, "style": style,
            "src": src, "tgt": tgt, "pts": pts
        })

# Parse style helper
def parse_style(s):
    d = {}
    for part in s.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            d[k.strip()] = v.strip()
        elif part.strip():
            d[part.strip()] = True
    return d

svg_elements = []

# Defs
svg_elements.append("""
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
  </marker>
  <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
    <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.08"/>
  </filter>
</defs>
""")

# Background
svg_elements.append(f'<rect width="{pw}" height="{ph}" fill="#ffffff"/>')

# Title watermark
svg_elements.append(f"""
<g transform="translate(60, 60)">
  <text font-family="Helvetica, Arial, sans-serif" font-size="28" font-weight="bold" fill="#0f172a">BON LAUNDRY STATION — LEVEL 0 SYSTEM OVERVIEW DFD</text>
  <text y="30" font-family="Helvetica, Arial, sans-serif" font-size="14" fill="#64748b">Updated with Super Admin Actor, Google SSO Provisioning, Role Perspective Switching, Tariffs &amp; Audit Trail</text>
</g>
""")

# Draw Vertices
for vid, v in vertices.items():
    st = parse_style(v["style"])
    fill = st.get("fillColor", "#ffffff")
    stroke = st.get("strokeColor", "#000000")
    sw = st.get("strokeWidth", "1.5")
    fsize = st.get("fontSize", "11")
    fbold = "bold" if st.get("fontStyle") == "1" else "normal"
    rx = 8 if "rounded=1" in v["style"] else 0
    
    val_lines = v["val"].split("\n")
    
    svg_elements.append(f"""
    <!-- Vertex: {vid} -->
    <g id="v_{vid}">
      <rect x="{v['x']}" y="{v['y']}" width="{v['w']}" height="{v['h']}"
            rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" filter="url(#shadow)"/>
    """)
    
    # Text positioning
    line_h = float(fsize) * 1.3
    total_h = len(val_lines) * line_h
    start_y = v["y"] + (v["h"] - total_h)/2 + float(fsize)*0.85
    
    for idx, l in enumerate(val_lines):
        ly = start_y + idx * line_h
        escaped_l = htmllib.escape(l)
        svg_elements.append(
            f'<text x="{v["x"] + v["w"]/2}" y="{ly}" font-family="Helvetica, Arial, sans-serif" '
            f'font-size="{fsize}" font-weight="{fbold}" fill="#000000" text-anchor="middle">{escaped_l}</text>'
        )
    svg_elements.append('</g>')

# Draw Edges
for e in edges:
    st = parse_style(e["style"])
    src_v = vertices.get(e["src"])
    tgt_v = vertices.get(e["tgt"])
    
    if not src_v or not tgt_v:
        continue
    
    # Calculate start point
    exx = float(st.get("exitX", 0.5))
    exy = float(st.get("exitY", 0.5))
    sx = src_v["x"] + exx * src_v["w"]
    sy = src_v["y"] + exy * src_v["h"]
    
    # Calculate end point
    enx = float(st.get("entryX", 0.5))
    eny = float(st.get("entryY", 0.5))
    tx = tgt_v["x"] + enx * tgt_v["w"]
    ty = tgt_v["y"] + eny * tgt_v["h"]
    
    all_pts = [(sx, sy)] + e["pts"] + [(tx, ty)]
    
    # Construct orthogonal path d
    d_parts = [f"M {all_pts[0][0]} {all_pts[0][1]}"]
    for p in all_pts[1:]:
        d_parts.append(f"L {p[0]} {p[1]}")
    path_d = " ".join(d_parts)
    
    # Highlight super admin flows with subtle color or keep uniform black
    is_admin_flow = "e_admin" in (e["src"], e["tgt"]) or "sa_" in e["id"] or "in5" in e["id"] or "out4" in e["id"] or "in6" in e["id"] or "out5" in e["id"] or "p5_in3" in e["id"] or "p5_out4" in e["id"] or "p6_in2" in e["id"] or "p6_out2" in e["id"]
    stroke_col = "#0369a1" if is_admin_flow else "#000000"
    stroke_w = "1.6" if is_admin_flow else "1.2"
    
    svg_elements.append(f"""
    <!-- Edge: {e['id']} -->
    <path d="{path_d}" fill="none" stroke="{stroke_col}" stroke-width="{stroke_w}" marker-end="url(#arrow)"/>
    """)
    
    # Label placement
    if e["val"]:
        # Find midpoint of path
        if len(all_pts) >= 2:
            # pick segment closest to center
            mid_idx = len(all_pts) // 2
            p1 = all_pts[mid_idx - 1]
            p2 = all_pts[mid_idx]
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2
            
            val_txt = htmllib.escape(e["val"])
            txt_len = len(e["val"]) * 6 + 12
            
            svg_elements.append(f"""
            <g transform="translate({mx}, {my})">
              <rect x="{-txt_len/2}" y="-9" width="{txt_len}" height="18" fill="#ffffff" fill-opacity="0.95" rx="3" stroke="#cbd5e1" stroke-width="0.5"/>
              <text x="0" y="3.5" font-family="Helvetica, Arial, sans-serif" font-size="9.5" font-weight="{'600' if is_admin_flow else 'normal'}" fill="{stroke_col}" text-anchor="middle">{val_txt}</text>
            </g>
            """)

html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Bon Laundry Station - DFD Level 0 System Overview</title>
  <style>
    body {{
      margin: 0;
      padding: 20px;
      background: #0f172a;
      display: flex;
      flex-direction: column;
      align-items: center;
      font-family: system-ui, -apple-system, sans-serif;
    }}
    .container {{
      background: white;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
      border-radius: 8px;
      overflow: hidden;
    }}
    svg {{
      display: block;
    }}
  </style>
</head>
<body>
  <div class="container">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {pw} {ph}" width="{pw}" height="{ph}">
      {"".join(svg_elements)}
    </svg>
  </div>
</body>
</html>
"""

OUT_HTML.write_text(html_content, encoding="utf-8")
print(f"Generated {OUT_HTML} with {len(vertices)} vertices and {len(edges)} edges.")
