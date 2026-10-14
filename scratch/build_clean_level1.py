# scratch/build_clean_level1.py
"""
Generates Level 1 DFDs (Processes 2.0 – 5.0) with strict layout:
  - 300px+ horizontal between columns
  - 200px+ vertical between sub-processes
  - Orthogonal routing, arc jumps (jumpStyle=arc;jumpSize=15)
  - Explicit exit/entry port attributes on EVERY edge
  - Short labels (1-4 words MAX)
  - ALL SHAPES FIRST, ALL EDGES LAST in XML
"""

from pathlib import Path
import xml.etree.ElementTree as ET

DIAG_DIR = Path(r"c:\Users\genes\bon-laundry\docs\diagrams")

# ── Style tokens ──────────────────────────────────────────────────────────────
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
EDGE_BASE = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;"
             "jumpStyle=arc;jumpSize=15;"
             "strokeColor=#000000;strokeWidth=1.2;"
             "endArrow=classic;endFill=1;"
             "fontFamily=Helvetica;fontSize=10;fontColor=#000000;"
             "labelBackgroundColor=#ffffff;")

import html as htmllib

def _e(s):
    return htmllib.escape(str(s), quote=True)

def vx(cid, label, style, x, y, w, h):
    return (f'<mxCell id="{cid}" value="{_e(label)}" style="{style}" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
            f'</mxCell>')

def ex(cid, label, ports, src, tgt, waypoints=None):
    px = ports.get("exitX",""); py2 = ports.get("exitY","")
    nx = ports.get("entryX",""); ny = ports.get("entryY","")
    ps = ""
    if px != "": ps += f"exitX={px};exitY={py2};exitDx=0;exitDy=0;"
    if nx != "": ps += f"entryX={nx};entryY={ny};entryDx=0;entryDy=0;"
    wps = ""
    if waypoints:
        inner = "".join(f'<mxPoint x="{a}" y="{b}"/>' for a,b in waypoints)
        wps = f'<Array as="points">{inner}</Array>'
    return (f'<mxCell id="{cid}" value="{_e(label)}" '
            f'style="{EDGE_BASE}{ps}" '
            f'edge="1" parent="1" source="{src}" target="{tgt}">\n'
            f'  <mxGeometry relative="1" as="geometry">{wps}</mxGeometry>\n'
            f'</mxCell>')

def store(base_id, label, x, y, sw=200, sh=46, sd_w=34):
    """Returns (d_cell, n_cell) strings for a Yourdon data store."""
    d = vx(f"{base_id}_d", "d1",   STORE_D, x,        y, sd_w,      sh)
    n = vx(f"{base_id}_n", label,  STORE_N, x+sd_w,   y, sw-sd_w,   sh)
    return d, n

def process(base_id, num, label, x, y, w=220, hdr=24, bod=56):
    h = vx(f"{base_id}h", num,   PROC_HDR, x, y,       w, hdr)
    b = vx(f"{base_id}b", label, PROC_BOD, x, y+hdr,   w, bod)
    return h, b

def write_diagram(name, shapes, edges, pw=1700, ph=1200):
    out = DIAG_DIR / f"{name}.drawio"
    s_xml = "\n        ".join(shapes)
    e_xml = "\n        ".join(edges)
    xml = f'''<mxfile host="app.diagrams.net" version="22.0.0" type="device">
  <diagram id="{name}" name="{name.replace("_"," ").title()}">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="{pw}" pageHeight="{ph}"
                  math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        {s_xml}
        {e_xml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    ET.fromstring(xml)
    out.write_text(xml, encoding="utf-8")
    print(f"  {name}.drawio  shapes={len(shapes)} edges={len(edges)}")

# =============================================================================
# PROCESS 2.0 — Appointment & Order Intake (Level 1)
# =============================================================================
# Sub-processes:
#   2.1 Validate Appointment Slot
#   2.2 Book/Queue Appointment
#   2.3 Send Confirmation
# External entities: Customer (left)
# Stores: tbl_appointment (right)
#
# Layout (process column x=520, w=220):
#   2.1  y=80
#   2.2  y=360   gap=200
#   2.3  y=640   gap=200
#
# Customer: x=50, y=350, w=160, h=80
# tbl_appointment: x=840, y=100 (right of 2.1)
# =============================================================================
def build_process2():
    S, E = [], []

    # Sub-processes
    h, b = process("p21","2.1","Validate Appointment Slot",520,80)
    S += [h, b]
    h, b = process("p22","2.2","Book/Queue Appointment",520,360)
    S += [h, b]
    h, b = process("p23","2.3","Send Confirmation",520,640)
    S += [h, b]

    # Entities
    S.append(vx("e_cust","Customer",ENTITY_ST, 50,350,160,80))

    # Stores
    d, n = store("s_apt","tbl_appointment", 840, 100)
    S += [d, n]

    # tbl_queue (for checking availability)
    d, n = store("s_que","tbl_queue", 200, 100)
    S += [d, n]

    # ── EDGES ──
    # 1. Customer → 2.1  "Booking Form"
    #    Lane x=390. Customer(R,0.25)=(210,370) → 2.1b(L,0.25)=(520,118)
    E.append(ex("e1","Booking Form",
        {"exitX":1,"exitY":0.25,"entryX":0,"entryY":0.25},
        "e_cust","p21b",[(390,370),(390,118)]))

    # 2. 2.1b → Customer  "Invalid / Unavailable"
    E.append(ex("e2","Invalid / Unavailable",
        {"exitX":0,"exitY":0.75,"entryX":1,"entryY":0.25},
        "p21b","e_cust",[(350,146),(350,370)]))

    # 3. tbl_queue → 2.1b  "Available Slots" (check availability)
    #    s_que_n right → 2.1b left top
    E.append(ex("e3","Available Slots",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
        "s_que_n","p21b"))

    # 4. 2.1b → 2.2b  "Validated Slot"  (internal flow, short lane x=470)
    E.append(ex("e4","Validated Slot",
        {"exitX":0,"exitY":0.75,"entryX":0,"entryY":0.25},
        "p21b","p22b",[(460,146),(460,398)]))

    # 5. 2.2b → tbl_appointment  "New Appointment"
    E.append(ex("e5","New Appointment",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
        "p22b","s_apt_n"))

    # 6. 2.2b → tbl_queue  "Queue Entry"
    #    Lane: go left via x=190.  2.2b(L,0.3)=(520,395) → s_que_n(R,0.5)=(380,123)
    E.append(ex("e6","Queue Entry",
        {"exitX":0,"exitY":0.3,"entryX":1,"entryY":0.7},
        "p22b","s_que_n",[(190,395),(190,136)]))

    # 7. 2.2b → 2.3b  "Booking Details"  (internal, lane x=475)
    E.append(ex("e7","Booking Details",
        {"exitX":0,"exitY":0.75,"entryX":0,"entryY":0.25},
        "p22b","p23b",[(470,426),(470,678)]))

    # 8. 2.3b → Customer  "Confirmation SMS/Email"
    #    Lane x=410.  2.3b(L,0.5)=(520,692) → Customer(R,0.75)=(210,410)
    E.append(ex("e8","Confirmation SMS/Email",
        {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.75},
        "p23b","e_cust",[(410,692),(410,410)]))

    # 9. tbl_appointment → 2.3b  "Appointment Record"  (for confirmation details)
    #    s_apt_n(L,0.8)=(840,130) → 2.3b(R,0.3)=(740,678)
    E.append(ex("e9","Appointment Record",
        {"exitX":0,"exitY":0.8,"entryX":1,"entryY":0.3},
        "s_apt_n","p23b",[(790,130),(790,680)]))

    write_diagram("level_1_process_2_appointment", S, E, pw=1200, ph=900)

# =============================================================================
# PROCESS 3.0 — Process Sales & Transactions (Level 1)
# =============================================================================
# Sub-processes:
#   3.1 Compute Service Charges
#   3.2 Record Transaction
#   3.3 Generate Receipt
# Entities: Customer (left), Staff (right)
# Stores: tbl_transaction (right-top), tbl_appointment (right-bottom)
# =============================================================================
def build_process3():
    S, E = [], []

    h, b = process("p31","3.1","Compute Service Charges",520,80)
    S += [h, b]
    h, b = process("p32","3.2","Record Transaction",520,360)
    S += [h, b]
    h, b = process("p33","3.3","Generate Receipt",520,640)
    S += [h, b]

    S.append(vx("e_cust","Customer",ENTITY_ST,  50,350,160,80))
    S.append(vx("e_staff","Staff",  ENTITY_ST,1380,200,160,80))

    d, n = store("s_trx","tbl_transaction",  840, 100)
    S += [d, n]
    d, n = store("s_apt","tbl_appointment",  840, 380)
    S += [d, n]
    d, n = store("s_set","tbl_system_settings", 200, 100)
    S += [d, n]

    # ── EDGES ──
    # 1. Staff → 3.1b  "Load & Laundry Details"
    E.append(ex("e1","Load & Laundry Details",
        {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.25},
        "e_staff","p31b",[(1280,240),(1280,118)]))

    # 2. tbl_system_settings → 3.1b  "Service Rates"
    E.append(ex("e2","Service Rates",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
        "s_set_n","p31b"))

    # 3. tbl_appointment → 3.1b  "Appointment Data"
    #    s_apt_n(L,0.3)=(840,394) → 3.1b(R,0.5)=(740,132)
    E.append(ex("e3","Appointment Data",
        {"exitX":0,"exitY":0.3,"entryX":1,"entryY":0.5},
        "s_apt_n","p31b",[(780,394),(780,132)]))

    # 4. 3.1b → Customer  "Service Fee Quote"
    E.append(ex("e4","Service Fee Quote",
        {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.25},
        "p31b","e_cust",[(410,132),(410,370)]))

    # 5. Customer → 3.1b  "Payment Confirmation"
    E.append(ex("e5","Payment Confirmation",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.75},
        "e_cust","p31b",[(440,390),(440,146)]))

    # 6. 3.1b → 3.2b  "Charge Details"  (internal lane x=476)
    E.append(ex("e6","Charge Details",
        {"exitX":0,"exitY":0.75,"entryX":0,"entryY":0.25},
        "p31b","p32b",[(470,146),(470,398)]))

    # 7. 3.2b → tbl_transaction  "Sales Record"
    E.append(ex("e7","Sales Record",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
        "p32b","s_trx_n"))

    # 8. 3.2b → tbl_appointment  "Update Status"
    E.append(ex("e8","Update Status",
        {"exitX":1,"exitY":0.75,"entryX":0,"entryY":0.5},
        "p32b","s_apt_n",[(870,426),(870,403)]))

    # 9. 3.2b → 3.3b  "Transaction ID"  (internal lane x=472)
    E.append(ex("e9","Transaction ID",
        {"exitX":0,"exitY":0.75,"entryX":0,"entryY":0.25},
        "p32b","p33b",[(466,426),(466,678)]))

    # 10. 3.3b → Customer  "Digital Receipt"
    E.append(ex("e10","Digital Receipt",
        {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.75},
        "p33b","e_cust",[(420,692),(420,410)]))

    # 11. 3.3b → Staff  "Transaction Summary"
    E.append(ex("e11","Transaction Summary",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":1},
        "p33b","e_staff",[(1310,692),(1310,280)]))

    write_diagram("level_1_process_3_sales_pos", S, E, pw=1600, ph=900)

# =============================================================================
# PROCESS 4.0 — Real-time Operational Status (Level 1)
# =============================================================================
# Sub-processes:
#   4.1 Monitor Machine Status
#   4.2 Compute EWT
#   4.3 Update Queue Display
# Entities: Staff (right), Customer (left-bottom)
# Stores: tbl_machine_status (left), tbl_queue (right-top)
# =============================================================================
def build_process4():
    S, E = [], []

    h, b = process("p41","4.1","Monitor Machine Status",520,80)
    S += [h, b]
    h, b = process("p42","4.2","Compute EWT",520,360)
    S += [h, b]
    h, b = process("p43","4.3","Update Queue Display",520,640)
    S += [h, b]

    S.append(vx("e_staff",  "Staff",   ENTITY_ST, 1350,200,160,80))
    S.append(vx("e_cust",   "Customer",ENTITY_ST,   50,620,160,80))

    d, n = store("s_mac","tbl_machine_status", 200, 100)
    S += [d, n]
    d, n = store("s_que","tbl_queue",          840,  90)
    S += [d, n]
    d, n = store("s_log","tbl_prediction_logs",840, 380)
    S += [d, n]

    # ── EDGES ──
    # 1. Staff → 4.1b  "Status Update"  (manual override / report)
    E.append(ex("e1","Status Update",
        {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.25},
        "e_staff","p41b",[(1280,240),(1280,118)]))

    # 2. 4.1b → tbl_machine_status  "Machine State"
    E.append(ex("e2","Machine State",
        {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.5},
        "p41b","s_mac_n"))

    # 3. tbl_machine_status → 4.2b  "Fleet Data"
    #    s_mac_n(R,0.7)=(380,121) → 4.2b(L,0.25)=(520,398)
    E.append(ex("e3","Fleet Data",
        {"exitX":1,"exitY":0.7,"entryX":0,"entryY":0.25},
        "s_mac_n","p42b",[(450,121),(450,398)]))

    # 4. tbl_queue → 4.2b  "Queue Size"
    E.append(ex("e4","Queue Size",
        {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.5},
        "s_que_n","p42b"))

    # 5. 4.2b → tbl_prediction_logs  "EWT Entry"
    E.append(ex("e5","EWT Entry",
        {"exitX":1,"exitY":0.75,"entryX":0,"entryY":0.25},
        "p42b","s_log_n",[(870,426),(870,393)]))

    # 6. 4.2b → 4.3b  "Computed EWT"  (internal lane x=475)
    E.append(ex("e6","Computed EWT",
        {"exitX":0,"exitY":0.75,"entryX":0,"entryY":0.25},
        "p42b","p43b",[(470,426),(470,678)]))

    # 7. 4.3b → tbl_queue  "Queue Update"
    #    4.3b(R,0.25)=(740,678) → s_que_n(L,0.8)=(840,120)
    E.append(ex("e7","Queue Update",
        {"exitX":1,"exitY":0.25,"entryX":0,"entryY":0.8},
        "p43b","s_que_n",[(870,678),(870,127)]))

    # 8. 4.3b → Customer  "EWT & Queue Info"
    E.append(ex("e8","EWT & Queue Info",
        {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.5},
        "p43b","e_cust",[(410,692),(410,660)]))

    # 9. 4.3b → Staff  "Fleet EWT Summary"
    E.append(ex("e9","Fleet EWT Summary",
        {"exitX":1,"exitY":0.75,"entryX":0,"entryY":1},
        "p43b","e_staff",[(1300,706),(1300,280)]))

    # 10. 4.1b → 4.2b  "Status Change Alert"  (internal lane x=480)
    E.append(ex("e10","Status Change Alert",
        {"exitX":0,"exitY":0.75,"entryX":0,"entryY":0.25},
        "p41b","p42b",[(478,146),(478,398)]))

    write_diagram("level_1_process_4_operational_status", S, E, pw=1600, ph=900)

# =============================================================================
# PROCESS 5.0 — Generate Analytics & Forecasts (Level 1)
# =============================================================================
# Sub-processes:
#   5.1 Aggregate Historical Data
#   5.2 Run Forecast Model
#   5.3 Generate Reports
# Entities: Manager (right)
# Stores: tbl_transaction (left-top), tbl_appointment (left-mid), tbl_prediction_logs (right)
# =============================================================================
def build_process5():
    S, E = [], []

    h, b = process("p51","5.1","Aggregate Historical Data",520,80)
    S += [h, b]
    h, b = process("p52","5.2","Run Forecast Model",520,360)
    S += [h, b]
    h, b = process("p53","5.3","Generate Reports",520,640)
    S += [h, b]

    S.append(vx("e_mgr","Manager",ENTITY_ST,1350,350,160,80))

    d, n = store("s_trx","tbl_transaction",  180, 90)
    S += [d, n]
    d, n = store("s_apt","tbl_appointment",  180,360)
    S += [d, n]
    d, n = store("s_mac","tbl_machine_status",180,600)
    S += [d, n]
    d, n = store("s_log","tbl_prediction_logs",840,100)
    S += [d, n]

    # ── EDGES ──
    # 1. tbl_transaction → 5.1b  "Sales History"
    E.append(ex("e1","Sales History",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.25},
        "s_trx_n","p51b",[(460,113),(460,118)]))

    # 2. tbl_appointment → 5.1b  "Booking History"
    #    s_apt_n(R,0.5)=(380,383) → 5.1b(L,0.5)=(520,132)
    E.append(ex("e2","Booking History",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.75},
        "s_apt_n","p51b",[(450,383),(450,146)]))

    # 3. tbl_machine_status → 5.1b  "Fleet Utilization"
    #    s_mac_n(R,0.3)=(380,614) → 5.1b(L,0.75)=(520,146)   use far lane x=440
    E.append(ex("e3","Fleet Utilization",
        {"exitX":1,"exitY":0.3,"entryX":0,"entryY":1},
        "s_mac_n","p51b",[(440,614),(440,160)]))

    # 4. 5.1b → 5.2b  "Aggregated Dataset"  (internal lane x=476)
    E.append(ex("e4","Aggregated Dataset",
        {"exitX":0,"exitY":0.75,"entryX":0,"entryY":0.25},
        "p51b","p52b",[(475,146),(475,398)]))

    # 5. 5.2b → tbl_prediction_logs  "Forecast Results"
    E.append(ex("e5","Forecast Results",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
        "p52b","s_log_n"))

    # 6. 5.2b → 5.3b  "Forecast Data"  (internal lane x=472)
    E.append(ex("e6","Forecast Data",
        {"exitX":0,"exitY":0.75,"entryX":0,"entryY":0.25},
        "p52b","p53b",[(470,426),(470,678)]))

    # 7. tbl_prediction_logs → 5.3b  "Historical Forecasts"
    #    s_log_n(L,0.8)=(840,130) → 5.3b(R,0.3)=(740,678)
    E.append(ex("e7","Historical Forecasts",
        {"exitX":0,"exitY":0.8,"entryX":1,"entryY":0.3},
        "s_log_n","p53b",[(800,130),(800,678)]))

    # 8. 5.3b → Manager  "Demand Forecasts"
    E.append(ex("e8","Demand Forecasts",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
        "p53b","e_mgr"))

    # 9. Manager → 5.3b  "Report Request"
    E.append(ex("e9","Report Request",
        {"exitX":0,"exitY":0.25,"entryX":1,"entryY":0.25},
        "e_mgr","p53b",[(1280,368),(1280,678)]))

    write_diagram("level_1_process_5_analytics_forecasts", S, E, pw=1600, ph=900)

# =============================================================================
# PROCESS 6.0 → 5.0 in user's naming — Manage System Settings (Level 1)
# =============================================================================
# Sub-processes:
#   5.1 (here: s1) Authenticate Manager
#   5.2 Update Pricing/Settings
#   5.3 View Configuration
# Entities: Manager (right)
# Stores: tbl_system_settings (right)
# =============================================================================
def build_process5_settings():
    S, E = [], []

    h, b = process("q51","5.1","Authenticate Manager",520,80)
    S += [h, b]
    h, b = process("q52","5.2","Update Pricing & Settings",520,360)
    S += [h, b]
    h, b = process("q53","5.3","View Configuration",520,640)
    S += [h, b]

    S.append(vx("e_mgr","Manager",ENTITY_ST,50,360,160,80))

    d, n = store("s_set","tbl_system_settings",840,100)
    S += [d, n]
    d, n = store("s_log","tbl_audit_logs",840,380)
    S += [d, n]

    # ── EDGES ──
    # 1. Manager → 5.1b  "Login Credentials"
    E.append(ex("e1","Login Credentials",
        {"exitX":1,"exitY":0.25,"entryX":0,"entryY":0.5},
        "e_mgr","q51b",[(390,378),(390,132)]))

    # 2. 5.1b → Manager  "Auth Error"
    E.append(ex("e2","Auth Error",
        {"exitX":0,"exitY":0.75,"entryX":1,"entryY":0.5},
        "q51b","e_mgr",[(350,146),(350,400)]))

    # 3. 5.1b → 5.2b  "Auth Token"  (lane x=472)
    E.append(ex("e3","Auth Token",
        {"exitX":0,"exitY":0.75,"entryX":0,"entryY":0.25},
        "q51b","q52b",[(468,146),(468,398)]))

    # 4. 5.1b → 5.3b  "Auth Token"  (lane x=478)
    E.append(ex("e4","Auth Token",
        {"exitX":0,"exitY":0.9,"entryX":0,"entryY":0.1},
        "q51b","q53b",[(478,157),(478,668)]))

    # 5. 5.2b → tbl_system_settings  "Updated Config"
    E.append(ex("e5","Updated Config",
        {"exitX":1,"exitY":0.5,"entryX":0,"entryY":0.5},
        "q52b","s_set_n"))

    # 6. tbl_system_settings → 5.2b  "Current Settings"
    E.append(ex("e6","Current Settings",
        {"exitX":0,"exitY":0.3,"entryX":1,"entryY":0.3},
        "s_set_n","q52b",[(800,110),(800,408)]))

    # 7. 5.2b → s_log  "Config Change Log"
    E.append(ex("e7","Config Change Log",
        {"exitX":1,"exitY":0.75,"entryX":0,"entryY":0.25},
        "q52b","s_log_n",[(870,426),(870,394)]))

    # 8. tbl_system_settings → 5.3b  "All Settings"
    #    s_set_n(L,0.8)=(840,130) → 5.3b(R,0.3)=(740,678)
    E.append(ex("e8","All Settings",
        {"exitX":0,"exitY":0.8,"entryX":1,"entryY":0.3},
        "s_set_n","q53b",[(800,130),(800,678)]))

    # 9. 5.3b → Manager  "Config View"
    E.append(ex("e9","Config View",
        {"exitX":0,"exitY":0.5,"entryX":1,"entryY":0.75},
        "q53b","e_mgr",[(390,692),(390,410)]))

    write_diagram("level_1_process_5_system_settings", S, E, pw=1600, ph=900)

# =============================================================================
print("Building Level 1 DFDs...")
build_process2()
build_process3()
build_process4()
build_process5()
build_process5_settings()
print("Done.")
