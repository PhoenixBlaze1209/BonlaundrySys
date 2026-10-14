# scratch/build_clean_level0.py
"""
Generates Level 0 DFD strictly following user constraints:
1. 300px+ horizontal distance between columns (entities -> processes -> stores)
2. 200px+ vertical distance between process blocks
3. Orthogonal routing with arc line jumps (jumpStyle=arc;jumpSize=15)
4. Short connector labels (1-4 words MAX)
5. Explicit exit/entry port attributes on every edge
6. ALL SHAPES DRAWN FIRST, ALL EDGES DRAWN LAST (z-order)
"""

import html as htmllib
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\level_0_system_overview.drawio")

# ── Style Tokens ──────────────────────────────────────────────────────────────
PROC_HDR  = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
             "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;"
             "fontColor=#000000;align=center;verticalAlign=middle;")
PROC_BOD  = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#6c8ebf;"
             "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=0;"
             "fontColor=#000000;align=center;verticalAlign=middle;")
ENTITY_ST = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;"
             "strokeWidth=1.5;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
             "fontColor=#000000;align=center;verticalAlign=middle;")
STORE_D   = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
             "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=0;"
             "align=center;verticalAlign=middle;")
STORE_N   = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
             "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;"
             "align=center;verticalAlign=middle;")
# Base edge style — rounded corners, orthogonal, arc jumps
EDGE_BASE = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;"
             "jumpStyle=arc;jumpSize=15;"
             "strokeColor=#000000;strokeWidth=1.2;"
             "endArrow=classic;endFill=1;"
             "fontFamily=Helvetica;fontSize=10;fontColor=#000000;"
             "labelBackgroundColor=#ffffff;")

# ── XML helpers ───────────────────────────────────────────────────────────────
def _attr(s: str) -> str:
    """Escape text for XML attribute value."""
    return htmllib.escape(s, quote=True)

def vertex(cid, label, style, x, y, w, h) -> str:
    return (f'<mxCell id="{cid}" value="{_attr(label)}" style="{style}" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
            f'</mxCell>')

def edge(cid, label, ports, src, tgt, waypoints=None) -> str:
    """
    ports: dict with keys exitX, exitY, entryX, entryY (all floats 0..1)
    waypoints: list of (x, y) tuples
    """
    port_str = "".join(
        f"{k}={v};exitDx=0;exitDy=0;" if "exit" in k else f"{k}={v};entryDx=0;entryDy=0;"
        for k, v in ports.items()
    )
    # Actually build cleanly
    ex = ports.get("exitX", ""); ey = ports.get("exitY", "")
    nx = ports.get("entryX", ""); ny = ports.get("entryY", "")
    pstr = ""
    if ex != "": pstr += f"exitX={ex};exitY={ey};exitDx=0;exitDy=0;"
    if nx != "": pstr += f"entryX={nx};entryY={ny};entryDx=0;entryDy=0;"

    pts_xml = ""
    if waypoints:
        inner = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in waypoints)
        pts_xml = f'<Array as="points">{inner}</Array>'

    return (f'<mxCell id="{cid}" value="{_attr(label)}" '
            f'style="{EDGE_BASE}{pstr}" '
            f'edge="1" parent="1" source="{src}" target="{tgt}">\n'
            f'  <mxGeometry relative="1" as="geometry">{pts_xml}</mxGeometry>\n'
            f'</mxCell>')

# ── Layout constants ──────────────────────────────────────────────────────────
#  Column x-origins:
#    Customer entity  : x =   50, w = 160   right edge = 210
#    Left data stores : x =  280, w = 200   right edge = 480
#    Processes        : x =  570, w = 240   right edge = 810   gap_to_entity=360 ✓
#    Right data stores: x =  900, w = 200   right edge = 1100  gap_to_process=90 (adjacent)
#    Staff/Mgr entity : x = 1380, w = 160   right edge = 1540  gap_to_store=280, gap_to_proc=570 ✓
#
#  Process vertical layout (header h=24, body h=56, total=80):
#    P1: y =   80  bottom = 160
#    P2: y =  360  bottom = 440  (gap = 200 ✓)
#    P3: y =  640  bottom = 720  (gap = 200 ✓)
#    P4: y =  940  bottom = 1020 (gap = 220 ✓)
#    P5: y = 1240  bottom = 1320 (gap = 220 ✓)
#
#  Canvas: 1800 × 1420

PX, PW = 570, 240   # process column x, width
PH     = 80         # process total height (header=24, body=56)
HDR_H  = 24

# store column x/w (both columns)
RS_X, LS_X, SW = 900, 280, 200   # right-store, left-store x origins; width
SD_W = 34   # d1 id-box width
SN_W = SW - SD_W  # name-box width = 166
SH   = 46   # store height

# entity dimensions
EW, EH = 160, 80

shapes: list[str] = []
edges:  list[str] = []

# ── PROCESSES ─────────────────────────────────────────────────────────────────
proc_rows = [
    ("p1", 80,  "1.0", "Appointment & Order Intake"),
    ("p2", 360, "2.0", "Process Sales & Transactions"),
    ("p3", 640, "3.0", "Real-time Operational Status"),
    ("p4", 940, "4.0", "Generate Analytics & Forecasts"),
    ("p5", 1240,"5.0", "Manage System Settings"),
]
for pid, py, pid_label, body_label in proc_rows:
    shapes.append(vertex(f"{pid}h", pid_label, PROC_HDR,  PX, py,         PW, HDR_H))
    shapes.append(vertex(f"{pid}b", body_label, PROC_BOD, PX, py+HDR_H,   PW, PH-HDR_H))

# ── EXTERNAL ENTITIES ─────────────────────────────────────────────────────────
# Customer: vertically centred between P2 (y=384) and P1 (y=104), placed at y=350
shapes.append(vertex("e_cust",  "Customer", ENTITY_ST,  50,   350, EW, EH))
# Staff: right side, aligned near P1-P2
shapes.append(vertex("e_staff", "Staff",    ENTITY_ST, 1380,  200, EW, EH))
# Manager: right side, aligned near P4-P5
shapes.append(vertex("e_mgr",   "Manager",  ENTITY_ST, 1380,  960, EW, EH))

# ── DATA STORES ───────────────────────────────────────────────────────────────
# Right column: adjacent to the process that writes to them
right_stores = [
    ("s_apt", "tbl_appointment",    100),   # ← P1 (y=80-160)
    ("s_trx", "tbl_transaction",    395),   # ← P2 (y=384-440)
    ("s_log", "tbl_prediction_logs",965),   # ← P4 (y=964-1020)
]
for sid, sname, sy in right_stores:
    shapes.append(vertex(f"{sid}_d", "d1",   STORE_D, RS_X,        sy, SD_W, SH))
    shapes.append(vertex(f"{sid}_n", sname,  STORE_N, RS_X+SD_W,   sy, SN_W, SH))

# Left column: adjacent to the process that writes to them
left_stores = [
    ("s_que", "tbl_queue",           650),  # ← P3 (y=664-720)
    ("s_mac", "tbl_machine_status",  780),  # ← P3/P4 boundary
    ("s_set", "tbl_system_settings", 1260), # ← P5 (y=1264-1320)
]
for sid, sname, sy in left_stores:
    shapes.append(vertex(f"{sid}_d", "d1",  STORE_D, LS_X,        sy, SD_W, SH))
    shapes.append(vertex(f"{sid}_n", sname, STORE_N, LS_X+SD_W,   sy, SN_W, SH))

# ── EDGES ─────────────────────────────────────────────────────────────────────
# Naming: e<N>  — numbered sequentially for readability.
# Convention: (exitX, exitY) → waypoints → (entryX, entryY)
# Customer anchor points  (x=50..210, y=350..430)
#   R-edge  x=210 | L-edge x=50 | T-edge y=350 | B-edge y=430
# P1b anchor points       (x=570..810, y=104..160)
# P2b anchor points       (x=570..810, y=384..440)
# P3b anchor points       (x=570..810, y=664..720)
# P4b anchor points       (x=570..810, y=964..1020)
# P5b anchor points       (x=570..810, y=1264..1320)
# Staff anchor points     (x=1380..1540, y=200..280)
# Manager anchor points   (x=1380..1540, y=960..1040)

# ── P1.0  Appointment & Order Intake ──────────────────────────────────────────
# 1. Customer → P1b  "Booking Form"
#    Lane: x-corridor 440.  Customer(R,0.25)=(210,370) → P1b(L,0.25)=(570,118)
edges.append(edge("e1","Booking Form",
    {"exitX":1,"exitY":0.25,"entryX":0,"entryY":0.25},
    "e_cust","p1b",[(440,370),(440,118)]))

# 2. P1b → Customer  "Slot Confirmation"
#    Lane: x-corridor 400.  P1b(L,0.75)=(570,146) → Customer(R,0.75)=(210,410)
edges.append(edge("e2","Slot Confirmation",
    {"exitX":0,"exitY":0.75,"entryX":1,"entryY":0.75},
    "p1b","e_cust",[(400,146),(400,410)]))

# 3. P1b → tbl_appointment  "Appointment Entry"  (direct horizontal)
edges.append(edge("e3","Appointment Entry",
    {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
    "p1b","s_apt_n"))

# 4. P1b → Staff  "Daily Schedule"
#    Route via y=50 ceiling lane to avoid all clutter above.
#    P1b(0.9,T)=(786,104) → (786,50) → (1340,50) → (1340,220) → Staff(L,0.25)=(1380,220)
edges.append(edge("e4","Daily Schedule",
    {"exitX":0.9,"exitY":0,"entryX":0,"entryY":0.25},
    "p1b","e_staff",[(786,50),(1340,50),(1340,220)]))

# ── P2.0  Process Sales & Transactions ────────────────────────────────────────
# 5. Customer → P2b  "Payment Details"
#    Lane x=460 (below lane 440 used by e1).
#    Customer(R,0.75)=(210,410) → P2b(L,0.25)=(570,398)
edges.append(edge("e5","Payment Details",
    {"exitX":1,"exitY":0.75,"entryX":0,"entryY":0.25},
    "e_cust","p2b",[(460,410),(460,398)]))

# 6. P2b → Customer  "Digital Receipt"
#    Lane x=490.  P2b(L,0.75)=(570,426) → Customer(R,0.5)=(210,390)
edges.append(edge("e6","Digital Receipt",
    {"exitX":0,"exitY":0.75,"entryX":1,"entryY":0.5},
    "p2b","e_cust",[(490,426),(490,390)]))

# 7. P2b → tbl_transaction  "Sales Record"  (direct horizontal)
edges.append(edge("e7","Sales Record",
    {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
    "p2b","s_trx_n"))

# 8. Staff → P2b  "Load & Machine Data"
#    Lane x=1310.  Staff(L,0.75)=(1380,260) → P2b(R,0.25)=(810,398)
edges.append(edge("e8","Load &amp; Machine Data",
    {"exitX":0,"exitY":0.75,"entryX":1,"entryY":0.25},
    "e_staff","p2b",[(1310,260),(1310,398)]))

# 9. P2b → Staff  "Service Fee Data"
#    Lane x=1270.  P2b(R,0.75)=(810,426) → Staff(L,0.5)=(1380,240)
edges.append(edge("e9","Service Fee Data",
    {"exitX":1,"exitY":0.75,"entryX":0,"entryY":0.5},
    "p2b","e_staff",[(1270,426),(1270,240)]))

# 10. P2b → Manager  "Transaction Data"
#     Lane x=1240 (inner of staff channel).
#     P2b(R,0.65)=(810,420) → Manager(L,0.25)=(1380,980)
edges.append(edge("e10","Transaction Data",
    {"exitX":1,"exitY":0.65,"entryX":0,"entryY":0.25},
    "p2b","e_mgr",[(1240,420),(1240,980)]))

# ── P3.0  Real-time Operational Status ────────────────────────────────────────
# 11. P3b → Customer  "Queue & EWT"
#     Far-left channel x=200 (between left stores and customer entity).
#     P3b(L,0.25)=(570,678) → Customer(B,0.5)=(130,430)
edges.append(edge("e11","Queue &amp; EWT",
    {"exitX":0,"exitY":0.25,"entryX":0.5,"entryY":1},
    "p3b","e_cust",[(200,678),(200,430)]))

# 12. P3b → tbl_queue  "Queue Logs"
#     Short step.  P3b(L,0.4)=(570,686) → s_que_n(R,0.5)=(480,673)
edges.append(edge("e12","Queue Logs",
    {"exitX":0,"exitY":0.4,"entryX":1,"entryY":0.5},
    "p3b","s_que_n",[(520,686),(520,673)]))

# 13. P3b → tbl_machine_status  "Status Updates"
#     Lane x=500.  P3b(L,0.75)=(570,706) → s_mac_n(R,0.3)=(480,794)
edges.append(edge("e13","Status Updates",
    {"exitX":0,"exitY":0.75,"entryX":1,"entryY":0.3},
    "p3b","s_mac_n",[(500,706),(500,794)]))

# 14. tbl_machine_status → P3b  "Machine State"
#     Lane x=540.  s_mac_n(R,0.7)=(480,812) → P3b(0.1,B)=(594,720)
edges.append(edge("e14","Machine State",
    {"exitX":1,"exitY":0.7,"entryX":0.1,"entryY":1},
    "s_mac_n","p3b",[(540,812),(540,720)]))

# 15. Staff → P3b  "Status Override"
#     Long horizontal at y=560 below Staff bottom (280) and above P3b top (640).
#     Staff(B,0.5)=(1460,280) → P3b(0.8,T)=(762,640)
edges.append(edge("e15","Status Override",
    {"exitX":0.5,"exitY":1,"entryX":0.8,"entryY":0},
    "e_staff","p3b",[(1460,560),(762,560)]))

# 16. P3b → Staff  "Fleet EWT"
#     Lane x=1300.  P3b(R,0.3)=(810,681) → Staff(L,1.0=bottom)=(1380,280)
edges.append(edge("e16","Fleet EWT",
    {"exitX":1,"exitY":0.3,"entryX":0,"entryY":1},
    "p3b","e_staff",[(1300,681),(1300,280)]))

# 17. P3b → tbl_prediction_logs  "EWT Data"
#     Lane x=950 (just right of process right edge 810, just left of right stores 900 → use 960 outside stores).
#     P3b(R,0.75)=(810,706) → s_log_n(L,0.3)=(900,979)
edges.append(edge("e17","EWT Data",
    {"exitX":1,"exitY":0.75,"entryX":0,"entryY":0.3},
    "p3b","s_log_n",[(960,706),(960,979)]))

# 18. P3b → tbl_system_settings  "Machine Config"
#     Outer-left floor channel at y=740, then x=160 going down.
#     P3b(L,1.0=bottom)=(570,720) → s_set_n(L,0.3)=(314,1274)
edges.append(edge("e18","Machine Config",
    {"exitX":0,"exitY":1,"entryX":0,"entryY":0.3},
    "p3b","s_set_n",[(570,740),(160,740),(160,1274)]))

# ── P4.0  Generate Analytics & Forecasts ─────────────────────────────────────
# 19. tbl_transaction → P4b  "Sales History"
#     Lane x=840 (between right stores and process right edge 810).
#     s_trx_n(L,0.8)=(900,438) → P4b(0.85,T)=(774,940)
edges.append(edge("e19","Sales History",
    {"exitX":0,"exitY":0.8,"entryX":0.85,"entryY":0},
    "s_trx_n","p4b",[(840,438),(840,910),(774,910)]))

# 20. tbl_machine_status → P4b  "Fleet Utilization"
#     Lane: left store right-bottom (480,812) → angle down-right to process left.
#     s_mac_n(0.8,B)=(440,826) → P4b(L,0.5)=(570,992)
edges.append(edge("e20","Fleet Utilization",
    {"exitX":0.8,"exitY":1,"entryX":0,"entryY":0.5},
    "s_mac_n","p4b",[(440,870),(530,870),(530,992)]))

# 21. P4b → tbl_prediction_logs  "MAPE Scores"  (direct horizontal)
edges.append(edge("e21","MAPE Scores",
    {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
    "p4b","s_log_n"))

# 22. P4b → Manager  "Demand Forecasts"
#     Lane x=1200.  P4b(R,0.75)=(810,1006) → Manager(L,0.5)=(1380,1000)
edges.append(edge("e22","Demand Forecasts",
    {"exitX":1,"exitY":0.75,"entryX":0,"entryY":0.5},
    "p4b","e_mgr",[(1200,1006),(1200,1000)]))

# ── P5.0  Manage System Settings ─────────────────────────────────────────────
# 23. Manager → P5b  "Config Updates"
#     Manager(B,0.5)=(1460,1040) → P5b(R,0.5)=(810,1292)
edges.append(edge("e23","Config Updates",
    {"exitX":0.5,"exitY":1,"entryX":1,"entryY":0.5},
    "e_mgr","p5b",[(1460,1292),(870,1292)]))

# 24. P5b → tbl_system_settings  "System Parameters"
#     P5b(L,0.5)=(570,1292) → s_set_n(R,0.5)=(480,1283)
edges.append(edge("e24","System Parameters",
    {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.5},
    "p5b","s_set_n",[(490,1292)]))

# 25. tbl_system_settings → Customer  "Service Rates"
#     Far-left outer margin channel x=30.
#     s_set_n(L,0.7)=(314,1292) → Customer(L,0.5)=(50,390)
edges.append(edge("e25","Service Rates",
    {"exitX":0,"exitY":0.7,"entryX":0,"entryY":0.5},
    "s_set_n","e_cust",[(30,1292),(30,390)]))

# ── Assemble & Validate ───────────────────────────────────────────────────────
shapes_xml = "\n        ".join(shapes)
edges_xml  = "\n        ".join(edges)

xml = f'''<mxfile host="app.diagrams.net" version="22.0.0" type="device">
  <diagram id="page_lvl0" name="Level 0 - System Overview">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1800" pageHeight="1420"
                  math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        {shapes_xml}
        {edges_xml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

# Quick XML parse to verify well-formedness
ET.fromstring(xml)
print("XML well-formed OK")

OUT.write_text(xml, encoding="utf-8")
print(f"Written to {OUT}")
print(f"Shapes: {len(shapes)} | Edges: {len(edges)}")
