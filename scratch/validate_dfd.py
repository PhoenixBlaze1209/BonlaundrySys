import re

xml = open(r'c:\Users\genes\bon-laundry\docs\diagrams\level_0_system_overview.drawio', encoding='utf-8').read()

arc_count  = xml.count('jumpStyle=arc')
exit_count = xml.count('exitX=')
entry_count= xml.count('entryX=')
label_bg   = xml.count('labelBackgroundColor=#ffffff')

vertex_positions = [m.start() for m in re.finditer(r'vertex="1"', xml)]
edge_positions   = [m.start() for m in re.finditer(r'edge="1"', xml)]

last_vertex = max(vertex_positions)
first_edge  = min(edge_positions)

print("=== Level 0 DFD Validation ===")
print(f"Arc jumps (jumpStyle=arc): {arc_count}")
print(f"exitX= attributes: {exit_count}")
print(f"entryX= attributes: {entry_count}")
print(f"labelBackgroundColor: {label_bg}")
print(f"All shapes before edges: {last_vertex < first_edge}")
print(f"Vertices: {len(vertex_positions)}  Edges: {len(edge_positions)}")
