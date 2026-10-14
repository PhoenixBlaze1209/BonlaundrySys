"""
scratch/build_use_case_drawio.py
Generates the UML 2.5 Use Case Diagram in draw.io XML format for Bon Laundry Station.
Actors: Customer, Staff, Manager, Super Admin.
Balanced 3-column layout. NO Telegram Bot.
"""

import html as htmllib
from pathlib import Path

OUT_FILE = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\use_case_diagram.drawio")

def escape(s):
    return htmllib.escape(str(s), quote=True)

# Styles
ACTOR_STYLE = (
    "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;"
    "fillColor=#ffffff;strokeColor=#0f172a;strokeWidth=2;fontFamily=Helvetica;fontSize=13;fontStyle=1;fontColor=#0f172a;"
)
SYS_BOUNDARY_STYLE = (
    "swimlane;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#0f172a;strokeWidth=2;"
    "fontFamily=Helvetica;fontSize=15;fontStyle=1;fontColor=#0f172a;startSize=45;"
)
UC_BASE_STYLE = (
    "ellipse;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#0284c7;strokeWidth=2;"
    "fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#0f172a;align=center;verticalAlign=middle;"
)
UC_INCLUDED_STYLE = (
    "ellipse;whiteSpace=wrap;html=1;fillColor=#f0f9ff;strokeColor=#0284c7;strokeWidth=2;dashed=1;"
    "fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#0369a1;align=center;verticalAlign=middle;"
)
UC_EXTENDED_STYLE = (
    "ellipse;whiteSpace=wrap;html=1;fillColor=#fffbeb;strokeColor=#d97706;strokeWidth=2;dashed=1;"
    "fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#b45309;align=center;verticalAlign=middle;"
)
UC_PAY_BASE_STYLE = (
    "ellipse;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#0f172a;strokeWidth=2;"
    "fontFamily=Helvetica;fontSize=13;fontStyle=1;fontColor=#0f172a;align=center;verticalAlign=middle;"
)
UC_PAY_ONLINE_STYLE = (
    "ellipse;whiteSpace=wrap;html=1;fillColor=#f0fdf4;strokeColor=#16a34a;strokeWidth=2;"
    "fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#15803d;align=center;verticalAlign=middle;"
)
UC_PAY_CASH_STYLE = (
    "ellipse;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#475569;strokeWidth=2;"
    "fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#1e293b;align=center;verticalAlign=middle;"
)
UC_ML_STYLE = (
    "ellipse;whiteSpace=wrap;html=1;fillColor=#fdf4ff;strokeColor=#a855f7;strokeWidth=2;"
    "fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#7e22ce;align=center;verticalAlign=middle;"
)
UC_SWITCHER_STYLE = (
    "ellipse;whiteSpace=wrap;html=1;fillColor=#f0fdfa;strokeColor=#0d9488;strokeWidth=2;"
    "fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#0f766e;align=center;verticalAlign=middle;"
)

ASSOC_STYLE = (
    "endArrow=none;html=1;rounded=0;strokeColor=#334155;strokeWidth=1.5;"
)
INCLUDE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;strokeColor=#0284c7;strokeWidth=1.6;"
    "endArrow=open;endFill=0;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#0284c7;labelBackgroundColor=#ffffff;"
)
EXTEND_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;dashed=1;strokeColor=#d97706;strokeWidth=1.6;"
    "endArrow=open;endFill=0;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#d97706;labelBackgroundColor=#ffffff;"
)
GEN_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#0f172a;strokeWidth=1.8;"
    "endArrow=block;endFill=0;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#0f172a;labelBackgroundColor=#ffffff;"
)

cells = []

def add_cell(cid, val, style, x, y, w, h, parent="1"):
    cells.append(
        f'<mxCell id="{cid}" value="{escape(val)}" style="{style}" vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
        f'</mxCell>'
    )

def add_edge(cid, val, style, src, tgt, parent="1", points=None):
    pts_xml = ""
    if points:
        pt_strs = "".join(f'<mxPoint x="{p[0]}" y="{p[1]}"/>' for p in points)
        pts_xml = f'<Array as="points">{pt_strs}</Array>'
    cells.append(
        f'<mxCell id="{cid}" value="{escape(val)}" style="{style}" edge="1" parent="{parent}" source="{src}" target="{tgt}">'
        f'<mxGeometry relative="1" as="geometry">{pts_xml}</mxGeometry>'
        f'</mxCell>'
    )

# 1. System Boundary
add_cell("sys_bound", "Bon Laundry Station Management System with Predictive Analytics", SYS_BOUNDARY_STYLE, 230, 40, 1680, 1240)

# 2. Actors
add_cell("act_cust", "Customer\n(Resident / Guest)", ACTOR_STYLE, 95, 210, 45, 80)
add_cell("act_staff", "Staff\n(Cashier & Floor)", ACTOR_STYLE, 95, 810, 45, 80)
add_cell("act_mgr", "Manager\n(Store Supervisor)", ACTOR_STYLE, 2005, 590, 45, 80)
add_cell("act_admin", "Super Admin\n(Business Owner)", ACTOR_STYLE, 2005, 1020, 45, 80)

# 3. Column 1: Customer & Staff Primary Use Cases
add_cell("uc1", "Book Laundry Service\n/ Online Appointment", UC_BASE_STYLE, 320, 115, 210, 65, "sys_bound")
add_cell("uc2", "Track Live Order & Queue\n(4-Step Progress Tracker & Milestones)", UC_BASE_STYLE, 310, 220, 230, 65, "sys_bound")
add_cell("uc3", "Request Order Cancellation\n(Self-Service Prior to Machine Cycle)", UC_EXTENDED_STYLE, 315, 320, 220, 60, "sys_bound")
add_cell("uc4", "View Machine Fleet Lobby\n& Traffic Rush Indicator", UC_BASE_STYLE, 315, 420, 220, 65, "sys_bound")

add_cell("uc5", "Verify Order QR Code\n& Counter Check-In", UC_BASE_STYLE, 320, 520, 210, 60, "sys_bound")
add_cell("uc6", "Process Walk-in POS\nJob Order", UC_BASE_STYLE, 325, 620, 200, 60, "sys_bound")
add_cell("uc7", "Manage & Intake\nOnline Appointments", UC_BASE_STYLE, 325, 720, 200, 60, "sys_bound")
add_cell("uc8", "Manage Live Queue Order\n& Floor Fleet Dispatch", UC_BASE_STYLE, 315, 820, 220, 60, "sys_bound")
add_cell("uc9", "Operate Machine Cycle\n& Monitor Live Timers", UC_BASE_STYLE, 320, 915, 210, 60, "sys_bound")
add_cell("uc10", "Complete Laundry Order\n& Release for Pickup / Delivery", UC_BASE_STYLE, 310, 1010, 230, 60, "sys_bound")
add_cell("uc11", "Update Machine Status\n(Available / In-Use / Maintenance)", UC_BASE_STYLE, 315, 1105, 220, 60, "sys_bound")

# 4. Column 2: Center Pricing, Validation & Payment
add_cell("uc12", "Calculate Service Price\n& Queue EWT Slot", UC_INCLUDED_STYLE, 755, 115, 210, 65, "sys_bound")
add_cell("uc13", "Pay for Order", UC_PAY_BASE_STYLE, 770, 270, 180, 65, "sys_bound")
add_cell("uc14", "Pay Online\n(GCash / Maya / Debit & Credit Card)", UC_PAY_ONLINE_STYLE, 1130, 210, 200, 65, "sys_bound")
add_cell("uc15", "Pay Cash on Counter / COD", UC_PAY_CASH_STYLE, 1140, 315, 180, 60, "sys_bound")
add_cell("uc16", "Validate Garment Weight &\nCalculate Load Fee / Add-ons", UC_INCLUDED_STYLE, 755, 620, 210, 60, "sys_bound")

# 5. Column 3: Manager & Super Admin
add_cell("uc17", "Access Store Operations Dashboard\n& ML Rush Forecast (Polynomial Reg & MAPE)", UC_ML_STYLE, 1445, 490, 270, 68, "sys_bound")
add_cell("uc18", "Manage Habitual Predictive Slots\n(Resident Routine Recommendations)", UC_ML_STYLE, 1455, 595, 250, 65, "sys_bound")
add_cell("uc19", "Monitor Sales History & Daily Tally\n(Drawer Reconciliation & CSV Export)", UC_BASE_STYLE, 1465, 700, 230, 60, "sys_bound")
add_cell("uc20", "Monitor Operational Audit Trail\n(Chronological Staff Activity Log)", UC_BASE_STYLE, 1470, 805, 220, 60, "sys_bound")

add_cell("uc21", "Switch View Mode Perspective\n(Super Admin / Manager / Staff / Customer)", UC_SWITCHER_STYLE, 1460, 925, 240, 65, "sys_bound")
add_cell("uc22", "Manage Staff & User Accounts\n(Google SSO Pre-Registration & Roles)", UC_BASE_STYLE, 1470, 1025, 220, 60, "sys_bound")
add_cell("uc23", "Configure Pricing, Tariffs & Fleet\n(Wash/Dry Rates, Add-ons & Capacities)", UC_BASE_STYLE, 1460, 1120, 240, 60, "sys_bound")

# 6. Actor Associations - Customer
add_edge("e_cust_uc1", "", ASSOC_STYLE, "act_cust", "uc1")
add_edge("e_cust_uc2", "", ASSOC_STYLE, "act_cust", "uc2")
add_edge("e_cust_uc4", "", ASSOC_STYLE, "act_cust", "uc4")

# Actor Associations - Staff
add_edge("e_staff_uc5", "", ASSOC_STYLE, "act_staff", "uc5")
add_edge("e_staff_uc6", "", ASSOC_STYLE, "act_staff", "uc6")
add_edge("e_staff_uc7", "", ASSOC_STYLE, "act_staff", "uc7")
add_edge("e_staff_uc8", "", ASSOC_STYLE, "act_staff", "uc8")
add_edge("e_staff_uc9", "", ASSOC_STYLE, "act_staff", "uc9")
add_edge("e_staff_uc10", "", ASSOC_STYLE, "act_staff", "uc10")
add_edge("e_staff_uc11", "", ASSOC_STYLE, "act_staff", "uc11")

# Actor Associations - Manager
add_edge("e_mgr_uc17", "", ASSOC_STYLE, "act_mgr", "uc17")
add_edge("e_mgr_uc18", "", ASSOC_STYLE, "act_mgr", "uc18")
add_edge("e_mgr_uc19", "", ASSOC_STYLE, "act_mgr", "uc19")
add_edge("e_mgr_uc20", "", ASSOC_STYLE, "act_mgr", "uc20")

# Actor Associations - Super Admin
add_edge("e_admin_uc21", "", ASSOC_STYLE, "act_admin", "uc21")
add_edge("e_admin_uc22", "", ASSOC_STYLE, "act_admin", "uc22")
add_edge("e_admin_uc23", "", ASSOC_STYLE, "act_admin", "uc23")

# Generalization - Actors
add_edge("gen_admin_mgr", "«inherits»", GEN_STYLE, "act_admin", "act_mgr")
add_edge("gen_mgr_staff", "Manager inherits all Staff privileges", GEN_STYLE, "act_mgr", "act_staff", points=[(2025, 1195), (115, 1195)])

# Include & Extend Dependencies
add_edge("inc_uc1_uc12", "«include»", INCLUDE_STYLE, "uc1", "uc12")
add_edge("ext_uc3_uc2", "«extend»", EXTEND_STYLE, "uc3", "uc2")
add_edge("inc_uc1_uc13", "«include»", INCLUDE_STYLE, "uc1", "uc13")
add_edge("inc_uc6_uc16", "«include»", INCLUDE_STYLE, "uc6", "uc16")
add_edge("inc_uc6_uc13", "«include»", INCLUDE_STYLE, "uc6", "uc13")

# Generalization - Payments
add_edge("gen_uc14_uc13", "", GEN_STYLE, "uc14", "uc13")
add_edge("gen_uc15_uc13", "", GEN_STYLE, "uc15", "uc13")

# Compile XML
xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" version="22.0.0">
  <diagram id="use_case_diagram_bon_laundry" name="UML Use Case Diagram - Bon Laundry Station">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2160" pageHeight="1360" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        {"".join(cells)}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""

OUT_FILE.write_text(xml_content, encoding="utf-8")
print(f"Successfully generated draw.io diagram at: {OUT_FILE}")
