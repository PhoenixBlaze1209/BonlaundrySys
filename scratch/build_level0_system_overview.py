# scratch/build_level0_system_overview.py
"""
Generates the Level 0 - System Overview DFD (NO LOGIN REQUIRED) strictly following:
1. Massive Geometry Spacing (Anti-Overlap):
   - >= 300px horizontal spacing between columns
   - >= 200px vertical spacing between processes
2. Forced Orthogonal Routing & Line Jumps:
   - edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;
   - jumpStyle=arc;jumpSize=15;
3. Strict Port Connections:
   - Explicit exitX/Y and entryX/Y on every connector
   - Explicit orthogonal waypoints for all routing corridors
4. Label Readability & Brevity:
   - Short labels (1-4 words)
   - labelBackgroundColor=#ffffff;
5. Z-Order Enforcement:
   - ALL shapes rendered FIRST
   - ALL edges rendered LAST
"""

import html as htmllib
import xml.etree.ElementTree as ET
from pathlib import Path

OUT_DIR = Path(r"c:\Users\genes\bon-laundry\docs\diagrams")
OUT_FILE = OUT_DIR / "level_0_system_overview.drawio"

# ── Style Tokens (Gane & Sarson) ──────────────────────────────────────────────
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
    exx = ports.get("exitX", "")
    exy = ports.get("exitY", "")
    enx = ports.get("entryX", "")
    eny = ports.get("entryY", "")
    ps = ""
    if exx != "":
        ps += f"exitX={exx};exitY={exy};exitDx=0;exitDy=0;"
    if enx != "":
        ps += f"entryX={enx};entryY={eny};entryDx=0;entryDy=0;"
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


def proc(pid, num, body, x, y, w=280, hdr=28, bod=52):
    return [
        vx(f"{pid}h", num, PROC_HDR, x, y, w, hdr),
        vx(f"{pid}b", body, PROC_BOD, x, y + hdr, w, bod),
    ]


def store(sid, label, x, y, sw=240, sh=46, sd=34):
    return [
        vx(f"{sid}_d", "d1", STORE_D, x, y, sd, sh),
        vx(f"{sid}_n", label, STORE_N, x + sd, y, sw - sd, sh),
    ]


def ent(eid, label, x, y, w=180, h=130):
    return vx(eid, label, ENTITY_ST, x, y, w, h)


def build_level0_diagram():
    S, E = [], []

    # 1. PROCESSES (Stacked at x=1040, w=280, vertical gap=220px)
    S += proc("p1", "1.0", "Appointment & Order Intake",       1040, 80,   w=280)
    S += proc("p2", "2.0", "Process Sales & Transactions",     1040, 380,  w=280)
    S += proc("p3", "3.0", "Real-time Operational Status",      1040, 680,  w=280)
    S += proc("p4", "4.0", "Generate Analytics & Forecasts",   1040, 980,  w=280)
    S += proc("p5", "5.0", "Manage System Settings",           1040, 1280, w=280)

    # 2. EXTERNAL ENTITIES
    S.append(ent("e_cust",  "Customer",  50,  250, w=180, h=140))
    S.append(ent("e_staff", "Staff",    2200, 250, w=180, h=130))
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

    # --- PROCESS 1.0 (Appointment & Order Intake) ---
    E.append(ex("l0_e1", "Appointment Request Data",
                {"exitX": 1, "exitY": 0.25, "entryX": 0, "entryY": 0.3},
                "e_cust", "p1b", [(380, 285), (380, 124)]))
    E.append(ex("l0_e2", "Available Slot Information",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.4},
                "p1b", "e_cust", [(420, 139), (420, 306)]))
    E.append(ex("l0_e3", "Appointment Confirmation",
                {"exitX": 0, "exitY": 0.85, "entryX": 1, "entryY": 0.55},
                "p1b", "e_cust", [(460, 152), (460, 327)]))
    E.append(ex("l0_e4", "Appointment Entry",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p1b", "s_apt_n", [(1480, 134), (1480, 120)]))
    E.append(ex("l0_e5", "Daily Appointment Schedule",
                {"exitX": 1, "exitY": 0.8, "entryX": 0, "entryY": 0.25},
                "p1b", "e_staff", [(1480, 150), (1480, 165), (2060, 165), (2060, 282)]))

    # --- PROCESS 2.0 (Process Sales & Transactions) ---
    E.append(ex("l0_e6", "Payment Details",
                {"exitX": 1, "exitY": 0.75, "entryX": 0, "entryY": 0.25},
                "e_cust", "p2b", [(400, 355), (400, 421)]))
    E.append(ex("l0_e7", "Transaction Data",
                {"exitX": 1, "exitY": 0.9, "entryX": 0, "entryY": 0.45},
                "e_cust", "p2b", [(440, 376), (440, 431)]))
    E.append(ex("l0_e8", "Digital Receipt Information",
                {"exitX": 0, "exitY": 0.75, "entryX": 0.9, "entryY": 1},
                "p2b", "e_cust", [(480, 447), (480, 410), (222, 410)]))
    E.append(ex("l0_e9", "Machine Assignment Data",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.2},
                "e_staff", "p2b", [(2020, 328), (2020, 418)]))
    E.append(ex("l0_e10", "Load Information",
                {"exitX": 0, "exitY": 0.75, "entryX": 1, "entryY": 0.4},
                "e_staff", "p2b", [(2040, 348), (2040, 429)]))
    E.append(ex("l0_e11", "Payment Details",
                {"exitX": 0, "exitY": 0.9, "entryX": 1, "entryY": 0.65},
                "e_staff", "p2b", [(2060, 367), (2060, 442)]))
    E.append(ex("l0_e12", "Service Fee Data",
                {"exitX": 1, "exitY": 0.85, "entryX": 0.5, "entryY": 1},
                "p2b", "e_staff", [(2080, 452), (2080, 410), (2290, 410)]))
    E.append(ex("l0_e13", "Sales Record & Job Order Details",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p2b", "s_trx_n", [(1490, 434), (1490, 420)]))
    E.append(ex("l0_e14", "Transaction Data",
                {"exitX": 0.85, "exitY": 1, "entryX": 0, "entryY": 0.25},
                "p2b", "e_mgr", [(1278, 480), (1960, 480), (1960, 1012)]))

    # --- PROCESS 3.0 (Real-time Operational Status) ---
    E.append(ex("l0_e15", "Email Notifications",
                {"exitX": 0, "exitY": 0.25, "entryX": 0.3, "entryY": 1},
                "p3b", "e_cust", [(320, 721), (320, 430), (104, 430)]))
    E.append(ex("l0_e16", "Queue Number, EWT & Service Status",
                {"exitX": 0, "exitY": 0.45, "entryX": 0.6, "entryY": 1},
                "p3b", "e_cust", [(360, 731), (360, 450), (168, 450)]))
    E.append(ex("l0_e17", "Queue Logs",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.4},
                "p3b", "s_que_n", [(880, 739), (880, 715)]))
    E.append(ex("l0_e18", "Queue Logs",
                {"exitX": 1, "exitY": 0.75, "entryX": 0, "entryY": 0.8},
                "s_que_n", "p3b", [(860, 732), (860, 750)]))
    E.append(ex("l0_e19", "Machine Status Data",
                {"exitX": 1, "exitY": 0.3, "entryX": 0, "entryY": 0.92},
                "s_mac_n", "p3b", [(900, 854), (900, 756)]))
    E.append(ex("l0_e20", "Updated Machine Status Data",
                {"exitX": 0.2, "exitY": 1, "entryX": 1, "entryY": 0.65},
                "p3b", "s_mac_n", [(1096, 800), (860, 800), (860, 870)]))
    E.append(ex("l0_e21", "Real-time Service Status Updates",
                {"exitX": 0.3, "exitY": 1, "entryX": 1, "entryY": 0.2},
                "e_staff", "p3b", [(2254, 430), (1940, 430), (1940, 718)]))
    E.append(ex("l0_e22", "Machine Status Data",
                {"exitX": 0.1, "exitY": 1, "entryX": 1, "entryY": 0.4},
                "e_staff", "p3b", [(2218, 450), (1920, 450), (1920, 729)]))
    E.append(ex("l0_e23", "EWT",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.7},
                "s_log_n", "p3b", [(1480, 854), (1480, 744)]))

    # --- PROCESS 4.0 (Generate Analytics & Forecasts) ---
    E.append(ex("l0_e24", "Real-time Machine Utilization Data",
                {"exitX": 1, "exitY": 0.85, "entryX": 0, "entryY": 0.3},
                "s_mac_n", "p4b", [(880, 879), (880, 1024)]))
    E.append(ex("l0_e25", "Historical Transaction Volume Data",
                {"exitX": 0.2, "exitY": 1, "entryX": 1, "entryY": 0.25},
                "s_trx_n", "p4b", [(1716, 470), (1520, 470), (1520, 1021)]))
    E.append(ex("l0_e26", "EWT Prediction Data & Mape Score",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.7},
                "p4b", "s_log_n", [(1460, 1034), (1460, 872)]))
    E.append(ex("l0_e27", "Peak Demand Forecasts & Operational Trends",
                {"exitX": 1, "exitY": 0.75, "entryX": 0, "entryY": 0.5},
                "p4b", "e_mgr", [(1980, 1047), (1980, 1045)]))
    E.append(ex("l0_e28", "Financial Summary & Sales Analytics",
                {"exitX": 1, "exitY": 0.9, "entryX": 0, "entryY": 0.7},
                "p4b", "e_mgr", [(2000, 1055), (2000, 1071)]))

    # --- PROCESS 5.0 (Manage System Settings) ---
    E.append(ex("l0_e29", "Configuration Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 1, "entryY": 0.25},
                "e_mgr", "p5b", [(2290, 1321)]))
    E.append(ex("l0_e30", "Updated System Parameters",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "p5b", "s_set_n", [(880, 1334), (880, 1320)]))
    E.append(ex("l0_e31", "Service Rates",
                {"exitX": 0, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "s_set_n", "e_cust", [(20, 1320), (20, 320)]))
    E.append(ex("l0_e32", "Machine ID",
                {"exitX": 0.3, "exitY": 0, "entryX": 0, "entryY": 0.75},
                "s_set_n", "p3b", [(552, 1250), (420, 1250), (420, 747)]))

    cells = "\n    ".join(S + E)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" version="22.0.0">\n'
        '  <diagram id="level_0_system_overview" name="Level 0 - System Overview (No Login)">\n'
        '    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        'pageScale="1" pageWidth="2550" pageHeight="1500" math="0" shadow="0">\n'
        '      <root>\n'
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f'        {cells}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )

    ET.fromstring(xml)
    OUT_FILE.write_text(xml, encoding="utf-8")
    print(f"  OK  {OUT_FILE.name}  [shapes={len(S)}, edges={len(E)}]")
    print(f"Output saved to: {OUT_FILE}")


if __name__ == "__main__":
    build_level0_diagram()
