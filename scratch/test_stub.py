# scratch/build_all_dfd.py
"""
Rebuilds ALL Bon Laundry DFD diagrams from scratch.
Clears docs/diagrams/ then generates 6 fresh .drawio files:
  1. context_diagram.drawio
  2. level_0_system_overview.drawio
  3. level1_process2_appointment.drawio
  4. level1_process3_pos_sales.drawio
  5. level1_process4_queue.drawio
  6. level1_process5_analytics.drawio

Layout constants (Level-1 diagrams):
  Left col   (entities/stores) x=50
  Process col                  x=600, w=240 (or 260 for long labels)
  Right col  (stores/entities) x=1180
  Process row y: 60 / 340 / 620 / 900  (200 px gaps)
  Process hdr=28 px, body=52 px  -> total=80 px
"""

import html as htmllib
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(r"c:\Users\genes\bon-laundry\docs\diagrams")

# ── Style Tokens ──────────────────────────────────────────────────────────────
PROC_HDR = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;"
    "fontColor=#000000;align=center;verticalAlign=middle;"
)
PROC_BOD = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#6c8ebf;"
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=0;"
    "fontColor=#000000;align=center;verticalAlign=middle;"
)
ENTITY_ST = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;"
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
    "fontColor=#000000;align=center;verticalAlign=middle;"
)
STORE_D = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=0;"
    "align=center;verticalAlign=middle;"
)
STORE_N = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;"
    "align=center;verticalAlign=middle;"
)
EDGE_BASE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;"
    "jumpStyle=arc;jumpSize=15;"
    "strokeColor=#000000;strokeWidth=1.2;"
    "endArrow=classic;endFill=1;"
    "fontFamily=Helvetica;fontSize=10;fontColor=#000000;"
    "labelBackgroundColor=#ffffff;"
)


# ── XML primitives ─────────────────────────────────────────────────────────────
def _e(s):
    return htmllib.escape(str(s), quote=True)


def vx(cid, label, style, x, y, w, h):
    return (
        f'<mxCell id="{cid}" value="{_e(label)}" style="{style}" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
        f'</mxCell>'
    )


def ex(cid, label, ports, src, tgt, wpts=None):
    exx = ports.get("exitX", "");  exy = ports.get("exitY", "")
    enx = ports.get("entryX", ""); eny = ports.get("entryY", "")
    ps = ""
    if exx != "": ps += f"exitX={exx};exitY={exy};exitDx=0;exitDy=0;"
    if enx != "": ps += f"entryX={enx};entryY={eny};entryDx=0;entryDy=0;"
    wp = ""
    if wpts:
        pts = "".join(f'<mxPoint x="{a}" y="{b}"/>' for a, b in wpts)
        wp = f'<Array as="points">{pts}</Array>'
    return (
        f'<mxCell id="{cid}" value="{_e(label)}" '
        f'style="{EDGE_BASE}{ps}" '
        f'edge="1" parent="1" source="{src}" target="{tgt}">'
        f'<mxGeometry relative="1" as="geometry">{wp}</mxGeometry>'
        f'</mxCell>'
    )


# ── Shape factories ───────────────────────────────────────────────────────────
def proc(pid, num, body, x, y, w=240, hdr=28, bod=52):
    return [
        vx(f"{pid}h", num,  PROC_HDR, x, y,       w, hdr),
        vx(f"{pid}b", body, PROC_BOD, x, y + hdr, w, bod),
    ]


def store(sid, label, x, y, sw=230, sh=46, sd=34):
    return [
        vx(f"{sid}_d", "d1",  STORE_D, x,      y, sd,      sh),
        vx(f"{sid}_n", label, STORE_N, x + sd, y, sw - sd, sh),
    ]


def ent(eid, label, x, y, w=160, h=80):
    return vx(eid, label, ENTITY_ST, x, y, w, h)


# ── Diagram writer ────────────────────────────────────────────────────────────
def write_diagram(fname, shapes, edges, pw=1700, ph=1100, title=""):
    cells = "\n    ".join(shapes + edges)
    did   = fname.replace(".", "_")
    dname = title or fname
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" version="22.0.0">\n'
        f'  <diagram id="{did}" name="{_e(dname)}">\n'
        f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        f'pageScale="1" pageWidth="{pw}" pageHeight="{ph}" math="0" shadow="0">\n'
        '      <root>\n'
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f'        {cells}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )
    ET.fromstring(xml)  # validate
    path = OUT / fname
    path.write_text(xml, encoding="utf-8")
    print(f"  OK  {fname}  [shapes={len(shapes)}, edges={len(edges)}]")


# =============================================================================
# STEP 0 — Clear every file in docs/diagrams/
# =============================================================================
print("Clearing docs/diagrams/ ...")
for f in OUT.iterdir():
    if f.is_file():
        f.unlink()
        print(f"    del  {f.name}")
print()


# =============================================================================
# DIAGRAM 1 — Context Diagram
# =============================================================================
# System : x=570 y=260 w=400 hdr=28 bod=160  -> sysb(570,288,400,160) right=970 bot=448
# Customer: x=50 y=390 w=160 h=80   right=210  gap-to-system=360 px
# Staff   : x=1300 y=290 w=160 h=80 left=1300  gap-from-system=330 px
# Manager : x=50 y=700 w=160 h=80   right=210
# =============================================================================
def build_context():
    S, E = [], []

    S += proc("sys", "0",
              "Point-of-Sale, Appointment, and\n"
              "Queuing Management System\n"
              "with Predictive Analytics",
              570, 260, w=400, hdr=28, bod=160)

    S.append(ent("e_cust",  "Customer",  50,  390))
    S.append(ent("e_staff", "Staff",    1300,  290))
    S.append(ent("e_mgr",   "Manager",   50,  700))

    # Customer -> System (rightward - Guest / Walk-in Booking & Payments, NO LOGIN)
    E.append(ex("c2", "Booking Request Data",
                {"exitX": 1, "exitY": 0.35, "entryX": 0, "entryY": 0.35},
                "e_cust", "sysb"))
    E.append(ex("c3", "Payment Details",
                {"exitX": 1, "exitY": 0.65, "entryX": 0, "entryY": 0.65},
                "e_cust", "sysb"))

    # System -> Customer (leftward Z-paths, corridors x=480/460/440/420)
    E.append(ex("c4", "Booking Confirmation",
                {"exitX": 0, "exitY": 0.1,  "entryX": 1, "entryY": 0.1},
                "sysb", "e_cust",  [(480, 304), (480, 398)]))
    E.append(ex("c5", "Payment Confirmation",
                {"exitX": 0, "exitY": 0.25, "entryX": 1, "entryY": 0.25},
                "sysb", "e_cust",  [(460, 328), (460, 410)]))
    E.append(ex("c6", "Service Status Info",
                {"exitX": 0, "exitY": 0.6,  "entryX": 1, "entryY": 0.6},
                "sysb", "e_cust",  [(440, 384), (440, 438)]))
    E.append(ex("c7", "Receipt Information",
                {"exitX": 0, "exitY": 0.75, "entryX": 1, "entryY": 0.75},
                "sysb", "e_cust",  [(420, 408), (420, 450)]))

    # System -> Staff (rightward)
    E.append(ex("s3", "Queue Status Info",
                {"exitX": 1, "exitY": 0.2, "entryX": 0, "entryY": 0.2},
                "sysb", "e_staff"))
    E.append(ex("s4", "Booking Schedule Info",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "sysb", "e_staff"))

    # Staff -> System (leftward, corridor x=1100/1080)
    E.append(ex("s1", "Booking Updates",
                {"exitX": 0, "exitY": 0.35, "entryX": 1, "entryY": 0.3},
                "e_staff", "sysb", [(1100, 318), (1100, 336)]))
    E.append(ex("s2", "Service Status Updates",
                {"exitX": 0, "exitY": 0.65, "entryX": 1, "entryY": 0.6},
                "e_staff", "sysb", [(1080, 342), (1080, 384)]))

    # System -> Manager (down-left corridors y=560/590)
    E.append(ex("m1", "Financial Summary Reports",
                {"exitX": 0.1,  "exitY": 1, "entryX": 0.4,  "entryY": 0},
                "sysb", "e_mgr", [(610, 560), (114, 560)]))
    E.append(ex("m2", "Operational Reports",
                {"exitX": 0.2,  "exitY": 1, "entryX": 0.65, "entryY": 0},
                "sysb", "e_mgr", [(650, 590), (154, 590)]))

    # Manager -> System (right-up-right-up to system bottom)
    E.append(ex("m3", "Pricing Update Data",
                {"exitX": 1, "exitY": 0.35, "entryX": 0.15, "entryY": 1},
                "e_mgr", "sysb", [(280, 728), (280, 480), (630, 480)]))
    E.append(ex("m4", "Verification Input",
                {"exitX": 1, "exitY": 0.65, "entryX": 0.25, "entryY": 1},
                "e_mgr", "sysb", [(310, 752), (310, 460), (670, 460)]))

    write_diagram("context_diagram.drawio", S, E,
                  pw=1800, ph=950,
                  title="Context Diagram - Bon Laundry System (No Login)")


build_context()


# =============================================================================
# DIAGRAM 2 — Level 0: System Overview (NO LOGIN REQUIRED)
# =============================================================================
# 5 Operational Processes (1.0 - 5.0)
# 6 Data Stores (tbl_appointment, tbl_transaction, tbl_prediction_logs,
#                tbl_queue, tbl_machine_status, tbl_system_settings)
# 3 Entities (Customer, Staff, Manager)
# =============================================================================
def build_level0():
    S, E = [], []

    # 1. PROCESSES (Stacked at x=1040, w=280, vertical gap=220px)
    S += proc("p1", "1.0", "Appointment & Order Intake",       1040, 80,   w=280)
    S += proc("p2", "2.0", "Process Sales & Transactions",     1040, 380,  w=280)
    S += proc("p3", "3.0", "Real-time Operational Status",      1040, 680,  w=280)
    S += proc("p4", "4.0", "Generate Analytics & Forecasts",   1040, 980,  w=280)
    S += proc("p5", "5.0", "Manage System Settings",           1040, 1280, w=280)

    # 2. EXTERNAL ENTITIES
    # Customer: x=50, y=250, w=180, h=140 (adjacent to P1.0 and P2.0)
    S.append(ent("e_cust",  "Customer",  50,  250, w=180, h=140))
    # Staff: x=2200, y=250, w=180, h=130 (adjacent to P1.0, P2.0, P3.0)
    S.append(ent("e_staff", "Staff",    2200, 250, w=180, h=130))
    # Manager: x=2200, y=980, w=180, h=130 (adjacent to P2.0, P4.0, P5.0)
    S.append(ent("e_mgr",   "Manager",  2200, 980, w=180, h=130))

    # 3. DATA STORES (Right Column: x=1640, w=240)
    S += store("s_apt", "tbl_appointment",     1640, 97,   sw=240)
    S += store("s_trx", "tbl_transaction",     1640, 397,  sw=240)
    S += store("s_log", "tbl_prediction_logs", 1640, 840,  sw=240)

    # 4. DATA STORES (Left Column: x=480, w=240)
    S += store("s_que", "tbl_queue",           480, 697,   sw=240)
    S += store("s_mac", "tbl_machine_status",  480, 840,   sw=240)
    S += store("s_set", "tbl_system_settings", 480, 1297,  sw=240)

    # ── CONNECTORS (32 Strict Orthogonal Edges, Arc Jumps) ───────────────────

    # --- PROCESS 1.0 (Appointment & Order Intake: x=1040..1320, y=108..160) ---
    # 1. Customer -> 1.0: Appointment Request Data
    E.append(ex("l0_e1", "Appointment Request Data",
                {"exitX": 1, "exitY": 0.25, "entryX": 0, "entryY": 0.3},
                "e_cust", "p1b", [(380, 285), (380, 124)]))

    # 2. 1.0 -> Customer: Available Slot Information
    E.append(ex("l0_e2", "Available Slot Information",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.4},
                "p1b", "e_cust", [(420, 139), (420, 306)]))

    # 3. 1.0 -> Customer: Appointment Confirmation
    E.append(ex("l0_e3", "Appointment Confirmation",
                {"exitX": 0, "exitY": 0.85, "entryX": 1, "entryY": 0.55},
                "p1b", "e_cust", [(460, 152), (460, 327)]))

    # 4. 1.0 -> tbl_appointment: Appointment Entry
    E.append(ex("l0_e4", "Appointment Entry",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p1b", "s_apt_n", [(1480, 134), (1480, 120)]))

    # 5. 1.0 -> Staff: Daily Appointment Schedule
    E.append(ex("l0_e5", "Daily Appointment Schedule",
                {"exitX": 1, "exitY": 0.8, "entryX": 0, "entryY": 0.25},
                "p1b", "e_staff", [(1480, 150), (1480, 165), (2060, 165), (2060, 282)]))

    # --- PROCESS 2.0 (Process Sales & Transactions: x=1040..1320, y=408..460) ---
    # 6. Customer -> 2.0: Payment Details
    E.append(ex("l0_e6", "Payment Details",
                {"exitX": 1, "exitY": 0.75, "entryX": 0, "entryY": 0.25},
                "e_cust", "p2b", [(400, 355), (400, 421)]))

    # 7. Customer -> 2.0: Transaction Data
    E.append(ex("l0_e7", "Transaction Data",
                {"exitX": 1, "exitY": 0.9, "entryX": 0, "entryY": 0.45},
                "e_cust", "p2b", [(440, 376), (440, 431)]))

    # 8. 2.0 -> Customer: Digital Receipt Information
    E.append(ex("l0_e8", "Digital Receipt Information",
                {"exitX": 0, "exitY": 0.75, "entryX": 0.9, "entryY": 1},
                "p2b", "e_cust", [(480, 447), (480, 410), (212, 410)]))

    # 9. Staff -> 2.0: Machine Assignment Data
    E.append(ex("l0_e9", "Machine Assignment Data",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.2},
                "e_staff", "p2b", [(2020, 328), (2020, 418)]))

    # 10. Staff -> 2.0: Load Information
    E.append(ex("l0_e10", "Load Information",
                {"exitX": 0, "exitY": 0.75, "entryX": 1, "entryY": 0.4},
                "e_staff", "p2b", [(2040, 348), (2040, 429)]))

    # 11. Staff -> 2.0: Payment Details
    E.append(ex("l0_e11", "Payment Details",
                {"exitX": 0, "exitY": 0.9, "entryX": 1, "entryY": 0.65},
                "e_staff", "p2b", [(2060, 367), (2060, 442)]))

    # 12. 2.0 -> Staff: Service Fee Data
    E.append(ex("l0_e12", "Service Fee Data",
                {"exitX": 1, "exitY": 0.85, "entryX": 0.5, "entryY": 1},
                "p2b", "e_staff", [(2080, 452), (2080, 410), (2290, 410)]))

    # 13. 2.0 -> tbl_transaction: Sales Record & Job Order Details
    E.append(ex("l0_e13", "Sales Record & Job Order Details",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p2b", "s_trx_n", [(1490, 434), (1490, 420)]))

    # 14. 2.0 -> Manager: Transaction Data
    E.append(ex("l0_e14", "Transaction Data",
                {"exitX": 0.85, "exitY": 1, "entryX": 0, "entryY": 0.25},
                "p2b", "e_mgr", [(1278, 480), (1960, 480), (1960, 1012)]))

    # --- PROCESS 3.0 (Real-time Operational Status: x=1040..1320, y=708..760) ---
    # 15. 3.0 -> Customer: Email Notifications
    E.append(ex("l0_e15", "Email Notifications",
                {"exitX": 0, "exitY": 0.25, "entryX": 0.3, "entryY": 1},
                "p3b", "e_cust", [(320, 721), (320, 430), (104, 430)]))

    # 16. 3.0 -> Customer: Queue Number, EWT & Service Status
    E.append(ex("l0_e16", "Queue Number, EWT & Service Status",
                {"exitX": 0, "exitY": 0.45, "entryX": 0.6, "entryY": 1},
                "p3b", "e_cust", [(360, 731), (360, 450), (158, 450)]))

    # 17. 3.0 -> tbl_queue: Queue Logs
    E.append(ex("l0_e17", "Queue Logs",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.4},
                "p3b", "s_que_n", [(880, 739), (880, 715)]))

    # 18. tbl_queue -> 3.0: Queue Logs
    E.append(ex("l0_e18", "Queue Logs",
                {"exitX": 1, "exitY": 0.75, "entryX": 0, "entryY": 0.8},
                "s_que_n", "p3b", [(860, 732), (860, 750)]))

    # 19. tbl_machine_status -> 3.0: Machine Status Data
    E.append(ex("l0_e19", "Machine Status Data",
                {"exitX": 1, "exitY": 0.3, "entryX": 0, "entryY": 0.92},
                "s_mac_n", "p3b", [(900, 854), (900, 756)]))

    # 20. 3.0 -> tbl_machine_status: Updated Machine Status Data
    E.append(ex("l0_e20", "Updated Machine Status Data",
                {"exitX": 0.2, "exitY": 1, "entryX": 1, "entryY": 0.65},
                "p3b", "s_mac_n", [(1096, 800), (860, 800), (860, 870)]))

    # 21. Staff -> 3.0: Real-time Service Status Updates
    E.append(ex("l0_e21", "Real-time Service Status Updates",
                {"exitX": 0.3, "exitY": 1, "entryX": 1, "entryY": 0.2},
                "e_staff", "p3b", [(2254, 430), (1940, 430), (1940, 718)]))

    # 22. Staff -> 3.0: Machine Status Data
    E.append(ex("l0_e22", "Machine Status Data",
                {"exitX": 0.1, "exitY": 1, "entryX": 1, "entryY": 0.4},
                "e_staff", "p3b", [(2218, 450), (1920, 450), (1920, 729)]))

    # 23. tbl_prediction_logs -> 3.0: EWT
    E.append(ex("l0_e23", "EWT",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.7},
                "s_log_n", "p3b", [(1480, 854), (1480, 744)]))

    # --- PROCESS 4.0 (Generate Analytics & Forecasts: x=1040..1320, y=1008..1060) ---
    # 24. tbl_machine_status -> 4.0: Real-time Machine Utilization Data
    E.append(ex("l0_e24", "Real-time Machine Utilization Data",
                {"exitX": 1, "exitY": 0.85, "entryX": 0, "entryY": 0.3},
                "s_mac_n", "p4b", [(880, 879), (880, 1024)]))

    # 25. tbl_transaction -> 4.0: Historical Transaction Volume Data
    E.append(ex("l0_e25", "Historical Transaction Volume Data",
                {"exitX": 0.2, "exitY": 1, "entryX": 1, "entryY": 0.25},
                "s_trx_n", "p4b", [(1716, 470), (1520, 470), (1520, 1021)]))

    # 26. 4.0 -> tbl_prediction_logs: EWT Prediction Data & Mape Score
    E.append(ex("l0_e26", "EWT Prediction Data & Mape Score",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.7},
                "p4b", "s_log_n", [(1460, 1034), (1460, 872)]))

    # 27. 4.0 -> Manager: Peak Demand Forecasts & Operational Trends
    E.append(ex("l0_e27", "Peak Demand Forecasts & Operational Trends",
                {"exitX": 1, "exitY": 0.75, "entryX": 0, "entryY": 0.5},
                "p4b", "e_mgr", [(1980, 1047), (1980, 1045)]))

    # 28. 4.0 -> Manager: Financial Summary & Sales Analytics
    E.append(ex("l0_e28", "Financial Summary & Sales Analytics",
                {"exitX": 1, "exitY": 0.9, "entryX": 0, "entryY": 0.7},
                "p4b", "e_mgr", [(2000, 1055), (2000, 1071)]))

    # --- PROCESS 5.0 (Manage System Settings: x=1040..1320, y=1308..1360) ---
    # 29. Manager -> 5.0: Configuration Data
    E.append(ex("l0_e29", "Configuration Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 1, "entryY": 0.25},
                "e_mgr", "p5b", [(2290, 1321)]))

    # 30. 5.0 -> tbl_system_settings: Updated System Parameters
    E.append(ex("l0_e30", "Updated System Parameters",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "p5b", "s_set_n", [(880, 1334), (880, 1320)]))

    # 31. tbl_system_settings -> Customer: Service Rates
    E.append(ex("l0_e31", "Service Rates",
                {"exitX": 0, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "s_set_n", "e_cust", [(20, 1320), (20, 320)]))

    # 32. tbl_system_settings -> 3.0: Machine ID
    E.append(ex("l0_e32", "Machine ID",
                {"exitX": 0.3, "exitY": 0, "entryX": 0, "entryY": 0.75},
                "s_set_n", "p3b", [(552, 1250), (420, 1250), (420, 747)]))

    write_diagram("level_0_system_overview.drawio", S, E,
                  pw=2550, ph=1500,
                  title="Level 0 - System Overview (No Login)")


build_level0()


# =============================================================================
# DIAGRAM 2 — Level 1, Process 2: Appointment & Order Intake
# =============================================================================
# Process col x=600, w=240(260 for P2.3)
# P2.1 y=60  body 88..140
# P2.2 y=340 body 368..420
# P2.3 y=620 body 648..700 (w=260 -> right=860)
# P2.4 y=900 body 928..980
# Left  x=50 : Customer (y=60)
# Right x=1180: tbl_appointment(y=60), tbl_machine_status(y=260), Staff(y=620)
# =============================================================================
def build_l1_appointment():
    S, E = [], []

    S += proc("p21", "2.1", "Slot Availability Check",             600, 60)
    S += proc("p22", "2.2", "Booking Request Validation",          600, 340)
    S += proc("p23", "2.3", "Appointment Storage & Status Update", 600, 620, w=260)
    S += proc("p24", "2.4", "Confirmation Issuance",               600, 900)

    S.append(ent("e_cust",  "Customer", 50,  60))
    S.append(ent("e_staff", "Staff",   1180, 620))

    S += store("s_apt", "tbl_appointment",   1180, 60)
    S += store("s_mac", "tbl_machine_status", 1180, 260)

    # 1. Customer -> P2.1 "Booking Data"
    E.append(ex("e1", "Booking Data",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "e_cust", "p21b"))

    # 2. P2.1 -> Customer "Slot Availability"  corridor x=480
    E.append(ex("e2", "Slot Availability",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.3},
                "p21b", "e_cust", [(480, 104), (480, 84)]))

    # 3. tbl_appointment -> P2.1 "Booking Data"  corridor x=1050
    E.append(ex("e3", "Booking Data",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_apt_n", "p21b", [(1050, 83), (1050, 114)]))

    # 4. tbl_machine_status -> P2.1 "Machine Status"
    E.append(ex("e4", "Machine Status",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.9},
                "s_mac_n", "p21b", [(1070, 283), (1070, 135)]))

    # 5. P2.1 -> P2.2 "Validated Data"  left corridor x=480
    E.append(ex("e5", "Validated Data",
                {"exitX": 0, "exitY": 0.8, "entryX": 0, "entryY": 0.2},
                "p21b", "p22b", [(480, 130), (480, 378)]))

    # 6. Customer -> P2.2 "Appointment Details"
    E.append(ex("e6", "Appointment Details",
                {"exitX": 0.5, "exitY": 1, "entryX": 0, "entryY": 0.3},
                "e_cust", "p22b", [(130, 384)]))

    # 7. P2.2 -> Customer "Validation Result"  corridor x=500
    E.append(ex("e7", "Validation Result",
                {"exitX": 0, "exitY": 0.5, "entryX": 0, "entryY": 0.8},
                "p22b", "e_cust", [(500, 394), (500, 124)]))

    # 8. P2.2 -> P2.3 "Booking Details"  left corridor x=460
    E.append(ex("e8", "Booking Details",
                {"exitX": 0, "exitY": 0.8, "entryX": 0, "entryY": 0.2},
                "p22b", "p23b", [(460, 412), (460, 658)]))

    # 9. P2.3 -> tbl_appointment "Appointment Record"  corridor x=1100
    E.append(ex("e9", "Appointment Record",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p23b", "s_apt_n", [(1100, 674), (1100, 83)]))

    # 10. P2.3 -> Staff "Appointment Status"
    E.append(ex("e10", "Appointment Status",
                {"exitX": 1, "exitY": 0.35, "entryX": 0, "entryY": 0.35},
                "p23b", "e_staff"))

    # 11. P2.3 -> Staff "Booking Data"
    E.append(ex("e11", "Booking Data",
                {"exitX": 1, "exitY": 0.65, "entryX": 0, "entryY": 0.65},
                "p23b", "e_staff"))

    # 12. P2.3 -> P2.4 "Appointment Info"  straight down
    E.append(ex("e12", "Appointment Info",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p23b", "p24b"))

    # 13. P2.4 -> Customer "Booking Confirmation Details"  corridor x=100
    E.append(ex("e13", "Booking Confirmation Details",
                {"exitX": 0, "exitY": 0.35, "entryX": 0.3, "entryY": 1},
                "p24b", "e_cust", [(100, 946), (100, 140)]))

    # 14. P2.4 -> Customer "Estimated Wait Time"  corridor x=80
    E.append(ex("e14", "Estimated Wait Time",
                {"exitX": 0, "exitY": 0.65, "entryX": 0.1, "entryY": 1},
                "p24b", "e_cust", [(80, 962), (80, 140)]))

    write_diagram("level1_process2_appointment.drawio", S, E,
                  pw=1600, ph=1100,
                  title="Level 1 - Process 2: Appointment and Order Intake")


build_l1_appointment()


# =============================================================================
# DIAGRAM 3 — Level 1, Process 3: POS Sales & Transactions
# =============================================================================
# P3.1 y=60  body 88..140
# P3.2 y=340 body 368..420
# P3.3 y=620 body 648..700
# P3.4 y=900 body 928..980
# Left  x=50 : Staff(y=60), tbl_system_settings(y=360), tbl_queue(y=640), Customer-L(y=900)
# Right      : tbl_machine_status x=1180(y=620), tbl_transaction x=1180(y=880), Customer-R x=1420(y=940)
# =============================================================================
def build_l1_pos():
    S, E = [], []

    S += proc("p31", "3.1", "Load Validation & Weight Check", 600, 60)
    S += proc("p32", "3.2", "Fee Calculation",               600, 340)
    S += proc("p33", "3.3", "Machine & Queue Assignment",    600, 620)
    S += proc("p34", "3.4", "Confirmation Issuance",         600, 900)

    S.append(ent("e_staff",  "Staff",    50,   60))
    S += store("s_set", "tbl_system_settings", 50, 360)
    S += store("s_que", "tbl_queue",           50, 640)
    S.append(ent("e_cust_l", "Customer",  50,  900))

    S += store("s_mac", "tbl_machine_status", 1180, 620)
    S += store("s_trx", "tbl_transaction",    1180, 880)
    S.append(ent("e_cust_r", "Customer", 1420, 940))

    # 1. Staff -> P3.1 "Load Weight"
    E.append(ex("e1", "Load Weight",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "e_staff", "p31b"))

    # 2. P3.1 -> Staff "Validation Status"  corridor x=500
    E.append(ex("e2", "Validation Status",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.3},
                "p31b", "e_staff", [(500, 104), (500, 84)]))

    # 3. P3.1 -> P3.2 "Weight Data"
    E.append(ex("e3", "Weight Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p31b", "p32b"))

    # 4. tbl_system_settings -> P3.2 "Price Rates"  (s_set_n right=280, P32b left=600)
    E.append(ex("e4", "Price Rates",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "s_set_n", "p32b"))

    # 5. P3.2 -> Staff "Calculated Service Fee"  corridor x=500
    E.append(ex("e5", "Calculated Service Fee",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.8},
                "p32b", "e_staff", [(500, 384), (500, 124)]))

    # 6. P3.2 -> P3.3 "Fee Data"
    E.append(ex("e6", "Fee Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p32b", "p33b"))

    # 7. tbl_machine_status -> P3.3 "Machine Availability Status"  corridor x=1050
    E.append(ex("e7", "Machine Availability Status",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_mac_n", "p33b", [(1050, 643), (1050, 674)]))

    # 8. P3.3 -> tbl_queue "Queue Data"  (leftward)
    E.append(ex("e8", "Queue Data",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "p33b", "s_que_n"))

    # 9. P3.3 -> P3.4 "Assignment Data"
    E.append(ex("e9", "Assignment Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p33b", "p34b"))

    # 10. Customer-L -> P3.4 "Payment Details"
    E.append(ex("e10", "Payment Details",
                {"exitX": 1, "exitY": 0.4, "entryX": 0, "entryY": 0.7},
                "e_cust_l", "p34b", [(400, 932), (400, 964)]))

    # 11. P3.4 -> Customer-L "Digital Receipt Info"  corridor x=500
    E.append(ex("e11", "Digital Receipt Info",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.6},
                "p34b", "e_cust_l", [(500, 959), (500, 948)]))

    # 12. P3.4 -> tbl_transaction "Sales Record Data"  corridor x=1050
    E.append(ex("e12", "Sales Record Data",
                {"exitX": 1, "exitY": 0.35, "entryX": 0, "entryY": 0.5},
                "p34b", "s_trx_n", [(1050, 946), (1050, 903)]))

    # 13. P3.4 -> Customer-R "Transaction Data"  corridor x=1100
    E.append(ex("e13", "Transaction Data",
                {"exitX": 1, "exitY": 0.65, "entryX": 0, "entryY": 0.5},
                "p34b", "e_cust_r", [(1100, 962), (1100, 980)]))

    write_diagram("level1_process3_pos_sales.drawio", S, E,
                  pw=1700, ph=1100,
                  title="Level 1 - Process 3: POS Sales and Transactions")


build_l1_pos()


# =============================================================================
# DIAGRAM 4 — Level 1, Process 4: Queue & Operational Status
# =============================================================================
# P4.1 y=60  body 88..140
# P4.2 y=340 body 368..420 (w=260)
# P4.3 y=620 body 648..700
# P4.4 y=900 body 928..980 (w=260)
# Left  x=50  : Staff (y=60)
# Right x=1180: tbl_machine_status(y=60), tbl_queue(y=240), Customer(y=360)
# =============================================================================
def build_l1_queue():
    S, E = [], []

    S += proc("p41", "4.1", "Queue Entry",                       600, 60)
    S += proc("p42", "4.2", "Predictive Wait-Time Calculation",  600, 340, w=260)
    S += proc("p43", "4.3", "Real-Time Status Monitoring",       600, 620)
    S += proc("p44", "4.4", "Queue Progression & Notification",  600, 900, w=260)

    S.append(ent("e_staff", "Staff",    50,   60))
    S.append(ent("e_cust",  "Customer", 1180, 360))

    S += store("s_mac", "tbl_machine_status", 1180, 60)
    S += store("s_que", "tbl_queue",          1180, 240)

    # 1. Staff -> P4.1 "Queue Request"
    E.append(ex("e1", "Queue Request",
                {"exitX": 1, "exitY": 0.4, "entryX": 0, "entryY": 0.4},
                "e_staff", "p41b"))

    # 2. P4.1 -> Staff "Queue Status"  corridor x=500
    E.append(ex("e2", "Queue Status",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.6},
                "p41b", "e_staff", [(500, 119), (500, 108)]))

    # 3. P4.1 -> tbl_machine_status "Machine Status"  corridor x=1060
    E.append(ex("e3", "Machine Status",
                {"exitX": 1, "exitY": 0.4, "entryX": 0, "entryY": 0.5},
                "p41b", "s_mac_n", [(1060, 109), (1060, 83)]))

    # 4. tbl_machine_status -> P4.1 "Machine Status" (read)  corridor x=1100
    E.append(ex("e4", "Machine Status",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.3},
                "s_mac_n", "p41b", [(1100, 78), (1100, 104)]))

    # 5. P4.1 -> tbl_queue "Queue Status"  corridor x=1080
    E.append(ex("e5", "Queue Status",
                {"exitX": 1, "exitY": 0.7, "entryX": 0, "entryY": 0.5},
                "p41b", "s_que_n", [(1080, 125), (1080, 263)]))

    # 6. P4.1 -> P4.2 "Queue Data"
    E.append(ex("e6", "Queue Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p41b", "p42b"))

    # 7. tbl_machine_status -> P4.2 "Machine Status"  corridor x=1140
    E.append(ex("e7", "Machine Status",
                {"exitX": 0, "exitY": 0.7, "entryX": 1, "entryY": 0.2},
                "s_mac_n", "p42b", [(1140, 95), (1140, 378)]))

    # 8. P4.2 -> Customer "EWT Notification"
    E.append(ex("e8", "EWT Notification",
                {"exitX": 1, "exitY": 0.4, "entryX": 0, "entryY": 0.4},
                "p42b", "e_cust"))

    # 9. P4.2 -> P4.3 "EWT Data"
    E.append(ex("e9", "EWT Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p42b", "p43b"))

    # 10. Staff -> P4.3 "Machine Status"  long corridor x=130
    E.append(ex("e10", "Machine Status",
                {"exitX": 0.5, "exitY": 1, "entryX": 0, "entryY": 0.3},
                "e_staff", "p43b", [(130, 663)]))

    # 11. P4.3 -> Customer "Machine Status"  corridor x=1080
    E.append(ex("e11", "Machine Status",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.65},
                "p43b", "e_cust", [(1080, 674), (1080, 432)]))

    # 12. P4.3 -> P4.4 "Status Data"
    E.append(ex("e12", "Status Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p43b", "p44b"))

    # 13. P4.4 -> Staff "Service Commencement Alert"  corridor x=100
    E.append(ex("e13", "Service Commencement Alert",
                {"exitX": 0, "exitY": 0.5, "entryX": 0.5, "entryY": 1},
                "p44b", "e_staff", [(100, 954), (100, 140)]))

    # 14. P4.4 -> Customer "Queue Notification"  corridor x=1100
    E.append(ex("e14", "Queue Notification",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.8},
                "p44b", "e_cust", [(1100, 954), (1100, 444)]))

    write_diagram("level1_process4_queue.drawio", S, E,
                  pw=1600, ph=1100,
                  title="Level 1 - Process 4: Queue and Operational Status")


build_l1_queue()


# =============================================================================
# DIAGRAM 5 — Level 1, Process 5: Analytics & Forecasting
# =============================================================================
# P5.1 y=60  body 88..140
# P5.2 y=340 body 368..420 (w=260)
# P5.3 y=620 body 648..700
# P5.4 y=900 body 928..980
# Right x=1180: tbl_queue(y=60), tbl_transaction(y=210), tbl_machine_status(y=380), Manager(y=640)
# =============================================================================
def build_l1_analytics():
    S, E = [], []

    S += proc("p51", "5.1", "Data Retrieval",              600, 60)
    S += proc("p52", "5.2", "Predictive Analytics Engine", 600, 340, w=260)
    S += proc("p53", "5.3", "Visualization Module",        600, 620)
    S += proc("p54", "5.4", "Report Generator",            600, 900)

    S.append(ent("e_mgr", "Manager", 1180, 640))

    S += store("s_que", "tbl_queue",           1180, 60)
    S += store("s_trx", "tbl_transaction",     1180, 210)
    S += store("s_mac", "tbl_machine_status",  1180, 380)

    # 1. P5.1 -> tbl_queue "Transaction Logs"  corridor x=1060
    E.append(ex("e1", "Transaction Logs",
                {"exitX": 1, "exitY": 0.4, "entryX": 0, "entryY": 0.5},
                "p51b", "s_que_n", [(1060, 109), (1060, 83)]))

    # 2. tbl_queue -> P5.1 "Queue Waiting Status"  corridor x=1100
    E.append(ex("e2", "Queue Waiting Status",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.3},
                "s_que_n", "p51b", [(1100, 75), (1100, 104)]))

    # 3. tbl_transaction -> P5.1 "Transaction Records"  corridor x=1080
    E.append(ex("e3", "Transaction Records",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.7},
                "s_trx_n", "p51b", [(1080, 233), (1080, 126)]))

    # 4. P5.1 -> P5.2 "Aggregated Data"
    E.append(ex("e4", "Aggregated Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p51b", "p52b"))

    # 5. tbl_machine_status -> P5.2 "Machine Utilization Rates"
    E.append(ex("e5", "Machine Utilization Rates",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_mac_n", "p52b"))

    # 6. P5.2 -> P5.3 "Forecast Data"
    E.append(ex("e6", "Forecast Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p52b", "p53b"))

    # 7. P5.3 -> Manager "Peak Hour Charts & Demand Predictions"
    E.append(ex("e7", "Peak Hour Charts & Demand Predictions",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p53b", "e_mgr"))

    # 8. P5.3 -> P5.4 "Report Data"
    E.append(ex("e8", "Report Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p53b", "p54b"))

    # 9. P5.4 -> Manager "Automated Reports"  corridor x=1090
    E.append(ex("e9", "Automated Reports",
                {"exitX": 1, "exitY": 0.35, "entryX": 0, "entryY": 0.8},
                "p54b", "e_mgr", [(1090, 946), (1090, 704)]))

    # 10. Manager -> P5.4 "Revenue Data"  corridor x=1110
    E.append(ex("e10", "Revenue Data",
                {"exitX": 0, "exitY": 0.65, "entryX": 1, "entryY": 0.65},
                "e_mgr", "p54b", [(1110, 692), (1110, 962)]))

    write_diagram("level1_process5_analytics.drawio", S, E,
                  pw=1600, ph=1100,
                  title="Level 1 - Process 5: Analytics and Forecasting")


build_l1_analytics()

print("\nAll 6 DFD diagrams generated successfully!")
print(f"Output: {OUT}")
