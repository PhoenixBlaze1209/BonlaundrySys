"""
scratch/build_context_diagram.py
Generates the simplified, textbook-compliant Bon Laundry Context Diagram (Process 0).
Strictly adheres to DFD Rules:
1. Single Process 0
2. External Entities (Customer, Staff, Manager)
3. No direct entity-to-entity flows
4. No data stores
5. Noun-phrase data flow labels
6. Balanced inputs & outputs (no miracles, no black holes)
7. Zero customer registration/login (orders ingested via landing page form)
"""

import html as htmllib
import xml.etree.ElementTree as ET
from pathlib import Path

OUT_FILE = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\context_diagram.drawio")

# ── Style Definitions ────────────────────────────────────────────────────────
PROC_HDR = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=13;fontStyle=1;"
    "fontColor=#000000;align=center;verticalAlign=middle;"
)
PROC_BOD = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#6c8ebf;"
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=12;fontStyle=0;"
    "fontColor=#000000;align=center;verticalAlign=middle;"
)
ENTITY_ST = (
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;"
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=13;fontStyle=1;"
    "fontColor=#000000;align=center;verticalAlign=middle;"
)
EDGE_BASE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;"
    "jumpStyle=arc;jumpSize=14;"
    "strokeColor=#000000;strokeWidth=1.3;"
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


def generate():
    shapes = []
    edges = []

    # 1. CENTRAL PROCESS 0
    # Header: x=840, y=400, w=420, h=30
    # Body  : x=840, y=430, w=420, h=250
    shapes.append(vx("sysh", "0", PROC_HDR, 840, 400, 420, 30))
    proc_text = (
        "Point-of-Sale, Appointment, and\n"
        "Queuing Management System\n"
        "with Predictive Analytics"
    )
    shapes.append(vx("sysb", proc_text, PROC_BOD, 840, 430, 420, 250))

    # 2. EXTERNAL ENTITIES
    # Customer: Left side (x=60, y=410, w=220, h=280)
    shapes.append(vx("e_cust", "Customer\n(Guest / Landing Page)", ENTITY_ST, 60, 410, 220, 280))
    # Staff: Top-Right (x=1620, y=140, w=240, h=300)
    shapes.append(vx("e_staff", "Staff\n(Cashier / Operator)", ENTITY_ST, 1620, 140, 240, 300))
    # Manager: Bottom-Right (x=1620, y=640, w=240, h=260)
    shapes.append(vx("e_mgr", "Manager\n(Administrator)", ENTITY_ST, 1620, 640, 240, 260))
    # Super Admin: Bottom-Right (x=1620, y=960, w=240, h=220)
    shapes.append(vx("e_admin", "Super Admin\n(Executive Owner)", ENTITY_ST, 1620, 960, 240, 220))

    # ─────────────────────────────────────────────────────────────────────────
    # 3. CUSTOMER DATA FLOWS (6 Flows - 3 In, 3 Out, Clean Horizontal Tracks)
    # Customer right edge: x=280. Process left edge: x=840.
    # Spans: Customer y in [410, 690], Process body y in [430, 680].
    # ─────────────────────────────────────────────────────────────────────────
    cust_flows = [
        # (id, label, direction, Y)
        ("c_in1",  "Laundry Order Details",                 "in",  450),
        ("c_out1", "Booking Confirmation & Order Ticket",   "out", 490),
        ("c_in2",  "Payment Details & Proof",               "in",  530),
        ("c_out2", "Payment Confirmation & Receipt",        "out", 570),
        ("c_in3",  "Order Status Inquiry",                  "in",  610),
        ("c_out3", "Service & Queue Status Updates",        "out", 650),
    ]

    for cid, label, direction, y in cust_flows:
        cust_rel = round((y - 410) / 280, 3)
        proc_rel = round((y - 430) / 250, 3)
        if direction == "in":
            ports = {"exitX": 1, "exitY": cust_rel, "entryX": 0, "entryY": proc_rel}
            edges.append(ex(cid, label, ports, "e_cust", "sysb"))
        else:
            ports = {"exitX": 0, "exitY": proc_rel, "entryX": 1, "entryY": cust_rel}
            edges.append(ex(cid, label, ports, "sysb", "e_cust"))

    # ─────────────────────────────────────────────────────────────────────────
    # 4. STAFF DATA FLOWS (6 Flows - 3 In, 3 Out, Concentric Planar Routing)
    # Staff left edge: x=1620, top=140, h=300
    # ─────────────────────────────────────────────────────────────────────────
    # Group A: 3 flows connecting to Process Top Edge (y=400, x in [840, 1260])
    staff_top_flows = [
        # (id, label, direction, staff_y, proc_x)
        ("s_out1", "Daily Booking Schedule & Delivery Manifest", "out", 180, 1060),
        ("s_out2", "Active Queue & Machine Status Information",  "out", 220, 1130),
        ("s_in1",  "Service & Queue Status Updates",             "in",  260, 1200),
    ]

    for cid, label, direction, sy, px in staff_top_flows:
        s_rely = round((sy - 140) / 300, 3)
        p_relx = round((px - 840) / 420, 3)
        if direction == "in":
            ports = {"exitX": 0, "exitY": s_rely, "entryX": p_relx, "entryY": 0}
            wpts = [(px, sy)]
            edges.append(ex(cid, label, ports, "e_staff", "sysh", wpts))
        else:
            ports = {"exitX": p_relx, "exitY": 0, "entryX": 0, "entryY": s_rely}
            wpts = [(px, sy)]
            edges.append(ex(cid, label, ports, "sysh", "e_staff", wpts))

    # Group B: 3 flows connecting to Process Upper Right Edge (x=1260, top=430, h=250)
    staff_right_flows = [
        # (id, label, direction, staff_y, corr_x, proc_y)
        ("s_in2",  "Walk-in Order & Load Details",           "in",  300, 1380, 460),
        ("s_out3", "Calculated Service Fee & Bill Information", "out", 340, 1440, 495),
        ("s_in3",  "Payment Collection Verification",        "in",  380, 1500, 530),
    ]

    for cid, label, direction, sy, cx, py in staff_right_flows:
        s_rely = round((sy - 140) / 300, 3)
        p_rely = round((py - 430) / 250, 3)
        if direction == "in":
            ports = {"exitX": 0, "exitY": s_rely, "entryX": 1, "entryY": p_rely}
            wpts = [(cx, sy), (cx, py)]
            edges.append(ex(cid, label, ports, "e_staff", "sysb", wpts))
        else:
            ports = {"exitX": 1, "exitY": p_rely, "entryX": 0, "entryY": s_rely}
            wpts = [(cx, py), (cx, sy)]
            edges.append(ex(cid, label, ports, "sysb", "e_staff", wpts))

    # ─────────────────────────────────────────────────────────────────────────
    # 5. MANAGER DATA FLOWS (4 Flows - 2 In, 2 Out, Planar Concentric Routing)
    # Manager left edge: x=1620, top=640, h=260
    # ─────────────────────────────────────────────────────────────────────────
    # Group A: 2 flows connecting to Process Lower Right Edge (x=1260, top=430, h=250)
    mgr_right_flows = [
        # (id, label, direction, mgr_y, corr_x, proc_y)
        ("m_in1",  "Tariff Rates & System Configurations",   "in",  680, 1380, 590),
        ("m_out1", "Financial & Sales Summary Reports",       "out", 720, 1440, 630),
    ]

    for cid, label, direction, my, cx, py in mgr_right_flows:
        m_rely = round((my - 640) / 260, 3)
        p_rely = round((py - 430) / 250, 3)
        if direction == "in":
            ports = {"exitX": 0, "exitY": m_rely, "entryX": 1, "entryY": p_rely}
            wpts = [(cx, my), (cx, py)]
            edges.append(ex(cid, label, ports, "e_mgr", "sysb", wpts))
        else:
            ports = {"exitX": 1, "exitY": p_rely, "entryX": 0, "entryY": m_rely}
            wpts = [(cx, py), (cx, my)]
            edges.append(ex(cid, label, ports, "sysb", "e_mgr", wpts))

    # Group B: 2 flows connecting to Process Bottom Edge (y=680, x in [840, 1260])
    mgr_bottom_flows = [
        # (id, label, direction, mgr_y, proc_x)
        ("m_in2",  "Analytics & Forecast Parameters",         "in",  780, 1200),
        ("m_out2", "Operational & Predictive Analytics Reports", "out", 830, 1120),
    ]

    for cid, label, direction, my, px in mgr_bottom_flows:
        m_rely = round((my - 640) / 260, 3)
        p_relx = round((px - 840) / 420, 3)
        if direction == "in":
            ports = {"exitX": 0, "exitY": m_rely, "entryX": p_relx, "entryY": 1}
            wpts = [(px, my)]
            edges.append(ex(cid, label, ports, "e_mgr", "sysb", wpts))
        else:
            ports = {"exitX": p_relx, "exitY": 1, "entryX": 0, "entryY": m_rely}
            wpts = [(px, my)]
            edges.append(ex(cid, label, ports, "sysb", "e_mgr", wpts))

    # ─────────────────────────────────────────────────────────────────────────
    # 6. SUPER ADMIN DATA FLOWS (2 Flows - 1 In, 1 Out, Planar Concentric Routing)
    # Super Admin left edge: x=1620, top=960, h=220
    # ─────────────────────────────────────────────────────────────────────────
    admin_bottom_flows = [
        # (id, label, direction, admin_y, proc_x)
        ("sa_in1",  "Tariff Configurations, SSO Provisioning & Role Switch Requests", "in",  1020, 1000),
        ("sa_out1", "Audit Logs, Perspective Views & System Status Reports",          "out", 1080, 920),
    ]

    for cid, label, direction, ay, px in admin_bottom_flows:
        a_rely = round((ay - 960) / 220, 3)
        p_relx = round((px - 840) / 420, 3)
        if direction == "in":
            ports = {"exitX": 0, "exitY": a_rely, "entryX": p_relx, "entryY": 1}
            wpts = [(px, ay)]
            edges.append(ex(cid, label, ports, "e_admin", "sysb", wpts))
        else:
            ports = {"exitX": p_relx, "exitY": 1, "entryX": 0, "entryY": a_rely}
            wpts = [(px, ay)]
            edges.append(ex(cid, label, ports, "sysb", "e_admin", wpts))

    # ── Render XML ───────────────────────────────────────────────────────────
    cells = "\n    ".join(shapes + edges)
    dname = "Context Diagram - Bon Laundry Station System"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" version="22.0.0">\n'
        f'  <diagram id="context_diagram_bon_laundry" name="{_e(dname)}">\n'
        f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        f'pageScale="1" pageWidth="2000" pageHeight="1300" math="0" shadow="0">\n'
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
    print(f"SUCCESS: Generated {OUT_FILE}")
    print(f"Shapes: {len(shapes)}, Edges: {len(edges)} (Expected 16 edges)")


if __name__ == "__main__":
    generate()
