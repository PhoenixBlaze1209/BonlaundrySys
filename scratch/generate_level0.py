# scratch/generate_level0.py
import html as htmllib
import xml.etree.ElementTree as ET
from pathlib import Path

OUT_FILE = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\level_0_system_overview.drawio")

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
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;"
    "align=center;verticalAlign=middle;"
)
STORE_N = (
    "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;"
    "strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;"
    "align=center;verticalAlign=middle;"
)
EDGE_BASE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;"
    "jumpStyle=arc;jumpSize=14;"
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


def proc(pid, num, body, x, y, w=320, hdr=28, bod=52):
    return [
        vx(f"{pid}h", num, PROC_HDR, x, y, w, hdr),
        vx(f"{pid}b", body, PROC_BOD, x, y + hdr, w, bod),
    ]


def store(sid, did, label, x, y, sw=250, sh=46, sd=40):
    return [
        vx(f"{sid}_d", did, STORE_D, x, y, sd, sh),
        vx(f"{sid}_n", label, STORE_N, x + sd, y, sw - sd, sh),
    ]


def ent(eid, label, x, y, w=190, h=140):
    return vx(eid, label, ENTITY_ST, x, y, w, h)


def build():
    S, E = [], []

    # 1. PROCESSES (X=1120, W=320, Total Height=80 each)
    S += proc("p1", "1.0", "User Account & Profile Management", 1120, 70)
    S += proc("p2", "2.0", "Appointment & Order Intake", 1120, 350)
    S += proc("p3", "3.0", "Process Sales & Transactions", 1120, 650)
    S += proc("p4", "4.0", "Queue & Machine Fleet Monitoring", 1120, 970)
    S += proc("p5", "5.0", "Generate Analytics & Forecasts", 1120, 1290)
    S += proc("p6", "6.0", "Manage System Settings & Tariffs", 1120, 1600)

    # 2. EXTERNAL ENTITIES
    S.append(ent("e_cust", "Customer", 60, 350, w=190, h=300))
    S.append(ent("e_staff", "Staff", 2480, 350, w=190, h=300))
    S.append(ent("e_mgr", "Manager", 2480, 1180, w=190, h=300))
    S.append(ent("e_admin", "Super Admin", 2480, 1720, w=190, h=250))

    # 3. DATA STORES (Distinct IDs D1 to D7)
    # Right Column: X=1780, W=250
    S += store("s_usr", "D1", "tbl_users", 1780, 87)
    S += store("s_apt", "D2", "tbl_appointment", 1780, 367)
    S += store("s_trx", "D5", "tbl_transaction", 1780, 667)
    S += store("s_log", "D7", "tbl_prediction_logs", 1780, 1307)

    # Left Column: X=580, W=250
    S += store("s_que", "D3", "tbl_queue", 580, 950)
    S += store("s_mac", "D4", "tbl_machine_status", 580, 1090)
    S += store("s_set", "D6", "tbl_system_settings", 580, 1617)

    # ── PROCESS 1.0 FLOWS ─────────────────────────────────────────────────────
    # Customer -> 1.0
    E.append(ex("l0_p1_in1", "Registration & Account Credentials",
                {"exitX": 1, "exitY": 0.12, "entryX": 0, "entryY": 0.3},
                "e_cust", "p1b", [(340, 386), (340, 114)]))

    # 1.0 -> Customer
    E.append(ex("l0_p1_out1", "Account Confirmation & Access Session",
                {"exitX": 0, "exitY": 0.7, "entryX": 1, "entryY": 0.22},
                "p1b", "e_cust", [(380, 134), (380, 416)]))

    # Staff -> 1.0
    E.append(ex("l0_p1_in2", "Staff Login Credentials",
                {"exitX": 0, "exitY": 0.12, "entryX": 1, "entryY": 0.3},
                "e_staff", "p1b", [(2200, 386), (2200, 114)]))

    # 1.0 -> Staff
    E.append(ex("l0_p1_out2", "Staff Authentication Status",
                {"exitX": 1, "exitY": 0.7, "entryX": 0, "entryY": 0.22},
                "p1b", "e_staff", [(2160, 134), (2160, 416)]))

    # Manager -> 1.0
    E.append(ex("l0_p1_in3", "Manager Login Credentials",
                {"exitX": 1, "exitY": 0.15, "entryX": 0.8, "entryY": 0},
                "e_mgr", "p1b", [(2720, 1225), (2720, 50), (1376, 50)]))

    # 1.0 -> Manager
    E.append(ex("l0_p1_out3", "Manager Authentication Status",
                {"exitX": 0.6, "exitY": 0, "entryX": 1, "entryY": 0.3},
                "p1b", "e_mgr", [(1312, 35), (2740, 35), (2740, 1270)]))

    # Manager -> 1.0 (Staff Account Configuration)
    E.append(ex("l0_p1_in4", "Staff Account Role Configuration",
                {"exitX": 0, "exitY": 0.15, "entryX": 1, "entryY": 0.85},
                "e_mgr", "p1b", [(2120, 1225), (2120, 142)]))

    # 1.0 <-> tbl_users (D1)
    E.append(ex("l0_p1_db1", "User Account Records",
                {"exitX": 1, "exitY": 0.4, "entryX": 0, "entryY": 0.4},
                "p1b", "s_usr_n", [(1620, 119), (1620, 105)]))

    E.append(ex("l0_p1_db2", "Stored User & Role Credentials",
                {"exitX": 0, "exitY": 0.75, "entryX": 1, "entryY": 0.55},
                "s_usr_n", "p1b", [(1640, 122), (1640, 127)]))

    # ── PROCESS 2.0 FLOWS ─────────────────────────────────────────────────────
    # Customer -> 2.0: Booking Details
    E.append(ex("l0_p2_in1", "Booking Details & Address Data",
                {"exitX": 1, "exitY": 0.35, "entryX": 0, "entryY": 0.25},
                "e_cust", "p2b", [(420, 455), (420, 391)]))

    # Customer -> 2.0: Tracking Query
    E.append(ex("l0_p2_in2", "Order Tracking Query (Code / Phone)",
                {"exitX": 1, "exitY": 0.45, "entryX": 0, "entryY": 0.45},
                "e_cust", "p2b", [(460, 485), (460, 401)]))

    # Customer -> 2.0: Cancellation Request & OTP
    E.append(ex("l0_p2_in3", "Cancellation Request & OTP Verification",
                {"exitX": 1, "exitY": 0.55, "entryX": 0, "entryY": 0.65},
                "e_cust", "p2b", [(500, 515), (500, 412)]))

    # 2.0 -> Customer: Booking Confirmation Ticket
    E.append(ex("l0_p2_out1", "Appointment Confirmation & Order Code Ticket",
                {"exitX": 0, "exitY": 0.15, "entryX": 1, "entryY": 0.65},
                "p2b", "e_cust", [(520, 386), (520, 545)]))

    # 2.0 -> Customer: Live Order Tracking Status
    E.append(ex("l0_p2_out2", "Live Order Tracking Status & Progress Details",
                {"exitX": 0, "exitY": 0.8, "entryX": 1, "entryY": 0.75},
                "p2b", "e_cust", [(480, 420), (480, 575)]))

    # 2.0 -> Customer: Cancellation Notice & Refund Status
    E.append(ex("l0_p2_out3", "Cancellation Notice & Refund Status",
                {"exitX": 0, "exitY": 0.95, "entryX": 1, "entryY": 0.85},
                "p2b", "e_cust", [(440, 427), (440, 605)]))

    # 2.0 -> Staff: Daily Intake Schedule
    E.append(ex("l0_p2_out4", "Daily Intake Schedule & Delivery Manifest",
                {"exitX": 1, "exitY": 0.25, "entryX": 0, "entryY": 0.35},
                "p2b", "e_staff", [(1520, 391), (1520, 300), (2350, 300), (2350, 455)]))

    # Staff -> 2.0: Check-in Status
    E.append(ex("l0_p2_in4", "Appointment Verification & Check-in Status",
                {"exitX": 0, "exitY": 0.45, "entryX": 1, "entryY": 0.45},
                "e_staff", "p2b", [(2330, 485), (2330, 320), (1540, 320), (1540, 401)]))

    # 2.0 <-> tbl_appointment (D2)
    E.append(ex("l0_p2_db1", "New Appointment & Cancellation Entries",
                {"exitX": 1, "exitY": 0.7, "entryX": 0, "entryY": 0.35},
                "p2b", "s_apt_n", [(1620, 414), (1620, 383)]))

    E.append(ex("l0_p2_db2", "Appointment Records & Order History",
                {"exitX": 0, "exitY": 0.75, "entryX": 1, "entryY": 0.85},
                "s_apt_n", "p2b", [(1640, 402), (1640, 422)]))

    # D6 (tbl_system_settings) -> 2.0 (Active Service Rates & Delivery Tariffs)
    # (LEGITIMATE Process flow - NOT entity to store!)
    E.append(ex("l0_p2_db3", "Active Service Rates & Delivery Tariffs",
                {"exitX": 0, "exitY": 0.2, "entryX": 0.1, "entryY": 0},
                "s_set_n", "p2b", [(540, 1626), (300, 1626), (300, 320), (1152, 320)]))

    # ── PROCESS 3.0 FLOWS ─────────────────────────────────────────────────────
    # Customer -> 3.0: Payment Details & Proof
    E.append(ex("l0_p3_in1", "Payment Details & Proof of Payment Screenshot",
                {"exitX": 1, "exitY": 0.92, "entryX": 0, "entryY": 0.3},
                "e_cust", "p3b", [(400, 626), (400, 694)]))

    # 3.0 -> Customer: Digital Payment Receipt
    E.append(ex("l0_p3_out1", "Digital Payment Receipt & Confirmation",
                {"exitX": 0, "exitY": 0.7, "entryX": 0.9, "entryY": 1},
                "p3b", "e_cust", [(440, 714), (440, 660), (231, 660)]))

    # Staff -> 3.0: Walk-in Load Weight
    E.append(ex("l0_p3_in2", "Walk-in Load Weight & Service Specifications",
                {"exitX": 0, "exitY": 0.65, "entryX": 1, "entryY": 0.25},
                "e_staff", "p3b", [(2280, 545), (2280, 691)]))

    # Staff -> 3.0: Cash Payment Collection
    E.append(ex("l0_p3_in3", "Cash Payment Collection & Counter Verification",
                {"exitX": 0, "exitY": 0.8, "entryX": 1, "entryY": 0.45},
                "e_staff", "p3b", [(2250, 590), (2250, 701)]))

    # 3.0 -> Staff: Calculated Service Fee
    E.append(ex("l0_p3_out2", "Calculated Service Fee & Bill Breakdown",
                {"exitX": 1, "exitY": 0.7, "entryX": 0, "entryY": 0.92},
                "p3b", "e_staff", [(2220, 714), (2220, 626)]))

    # 3.0 -> Manager: Sales Stream
    E.append(ex("l0_p3_out3", "Sales Transaction Stream & Revenue Feeds",
                {"exitX": 0.85, "exitY": 1, "entryX": 0, "entryY": 0.2},
                "p3b", "e_mgr", [(1392, 730), (1392, 770), (2260, 770), (2260, 1240)]))

    # 3.0 -> tbl_transaction (D5)
    E.append(ex("l0_p3_db1", "Completed Transaction Records",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p3b", "s_trx_n", [(1620, 704), (1620, 690)]))

    # D6 (tbl_system_settings) -> 3.0: Base Weight Rates & Pricing Rules
    E.append(ex("l0_p3_db2", "Base Weight Rates & Operational Pricing Rules",
                {"exitX": 0, "exitY": 0.5, "entryX": 0.2, "entryY": 0},
                "s_set_n", "p3b", [(520, 1640), (330, 1640), (330, 630), (1184, 630)]))

    # ── PROCESS 4.0 FLOWS ─────────────────────────────────────────────────────
    # 4.0 -> Customer: Queue Ticket, EWT & Service Status
    E.append(ex("l0_p4_out1", "Queue Ticket Number, EWT & Service Status",
                {"exitX": 0, "exitY": 0.2, "entryX": 0.8, "entryY": 1},
                "p4b", "e_cust", [(260, 1008), (260, 675), (212, 675)]))

    # 4.0 -> Customer: Live Machine Lobby Availability
    E.append(ex("l0_p4_out2", "Live Machine Lobby Availability & Rush Level",
                {"exitX": 0, "exitY": 0.5, "entryX": 0.6, "entryY": 1},
                "p4b", "e_cust", [(230, 1024), (230, 700), (174, 700)]))

    # 4.0 -> Customer: SMS / Email Notifications
    E.append(ex("l0_p4_out3", "SMS / Email Status Notifications",
                {"exitX": 0, "exitY": 0.8, "entryX": 0.4, "entryY": 1},
                "p4b", "e_cust", [(200, 1040), (200, 725), (136, 725)]))

    # Staff -> 4.0: Machine Allocation & Cycle Timers
    E.append(ex("l0_p4_in1", "Machine Allocation & Cycle Start Timers",
                {"exitX": 0.2, "exitY": 1, "entryX": 1, "entryY": 0.25},
                "e_staff", "p4b", [(2518, 650), (2518, 860), (2200, 860), (2200, 1011)]))

    # Staff -> 4.0: Queue Status Progression
    E.append(ex("l0_p4_in2", "Queue Status Progression & Fulfillment Advance",
                {"exitX": 0.4, "exitY": 1, "entryX": 1, "entryY": 0.5},
                "e_staff", "p4b", [(2556, 650), (2556, 890), (2170, 890), (2170, 1024)]))

    # Staff -> 4.0: Hardware Operational State
    E.append(ex("l0_p4_in3", "Hardware Operational State (Available/Maintenance)",
                {"exitX": 0.6, "exitY": 1, "entryX": 1, "entryY": 0.75},
                "e_staff", "p4b", [(2594, 650), (2594, 920), (2140, 920), (2140, 1037)]))

    # 4.0 -> Staff: Active Queue Sequence & EWT List
    E.append(ex("l0_p4_out4", "Active Queue Sequence & EWT List",
                {"exitX": 1, "exitY": 0.15, "entryX": 0.1, "entryY": 1},
                "p4b", "e_staff", [(2110, 1006), (2110, 830), (2499, 830), (2499, 650)]))

    # 4.0 -> Staff: Running Machine Timers & Alerts
    E.append(ex("l0_p4_out5", "Running Machine Timers & Maintenance Alerts",
                {"exitX": 1, "exitY": 0.85, "entryX": 0.8, "entryY": 1},
                "p4b", "e_staff", [(2080, 1042), (2080, 800), (2632, 800), (2632, 650)]))

    # 4.0 <-> tbl_queue (D3)
    E.append(ex("l0_p4_db1", "Queue State & Sequence Entries",
                {"exitX": 0, "exitY": 0.35, "entryX": 1, "entryY": 0.4},
                "p4b", "s_que_n", [(950, 1016), (950, 968)]))

    E.append(ex("l0_p4_db2", "Active Queue Entries & Status Details",
                {"exitX": 1, "exitY": 0.75, "entryX": 0, "entryY": 0.65},
                "s_que_n", "p4b", [(930, 985), (930, 1032)]))

    # 4.0 <-> tbl_machine_status (D4)
    E.append(ex("l0_p4_db3", "Machine Operational State & Cycle Timers",
                {"exitX": 0, "exitY": 0.85, "entryX": 1, "entryY": 0.35},
                "p4b", "s_mac_n", [(950, 1042), (950, 1106)]))

    E.append(ex("l0_p4_db4", "Live Machine Fleet Records",
                {"exitX": 1, "exitY": 0.75, "entryX": 0, "entryY": 0.95},
                "s_mac_n", "p4b", [(930, 1125), (930, 1047)]))

    # D7 (tbl_prediction_logs) -> 4.0: Historical EWT Multipliers
    E.append(ex("l0_p4_db5", "Historical EWT & Service Time Multipliers",
                {"exitX": 0, "exitY": 0.25, "entryX": 1, "entryY": 0.65},
                "s_log_n", "p4b", [(1560, 1318), (1560, 1032)]))

    # ── PROCESS 5.0 FLOWS ─────────────────────────────────────────────────────
    # Manager -> 5.0: Forecast Filter & Retrain
    E.append(ex("l0_p5_in1", "Forecast Date Filter & Retrain Parameters",
                {"exitX": 0, "exitY": 0.35, "entryX": 1, "entryY": 0.25},
                "e_mgr", "p5b", [(2280, 1285), (2280, 1331)]))

    # Manager -> 5.0: Ghost Slot Assignment
    E.append(ex("l0_p5_in2", "Ghost Slot Reservation Assignment",
                {"exitX": 0, "exitY": 0.55, "entryX": 1, "entryY": 0.45},
                "e_mgr", "p5b", [(2250, 1345), (2250, 1341)]))

    # D5 (tbl_transaction) -> 5.0: Historical Records
    E.append(ex("l0_p5_db1", "Historical Transaction Records & Load Volume",
                {"exitX": 0.3, "exitY": 1, "entryX": 0.8, "entryY": 0},
                "s_trx_n", "p5b", [(1843, 713), (1843, 800), (1600, 800), (1600, 1270), (1376, 1270)]))

    # D4 (tbl_machine_status) -> 5.0: Fleet Utilization
    E.append(ex("l0_p5_db2", "Machine Fleet Utilization & Cycle History",
                {"exitX": 0.5, "exitY": 1, "entryX": 0, "entryY": 0.3},
                "s_mac_n", "p5b", [(705, 1136), (705, 1338), (1100, 1338), (1100, 1333)]))

    # 5.0 -> tbl_prediction_logs (D7): Forecast Logs & MAPE
    E.append(ex("l0_p5_db3", "Regression Forecast Logs & Model Accuracy (MAPE)",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p5b", "s_log_n", [(1600, 1344), (1600, 1330)]))

    # 5.0 -> Manager: Peak Demand Forecasts
    E.append(ex("l0_p5_out1", "Peak Demand Forecasts & Hourly Footfall Trends",
                {"exitX": 1, "exitY": 0.65, "entryX": 0, "entryY": 0.65},
                "p5b", "e_mgr", [(2220, 1352), (2220, 1375)]))

    # 5.0 -> Manager: Ghost Slot Recommendations
    E.append(ex("l0_p5_out2", "Habitual Resident Ghost Slot Recommendations",
                {"exitX": 1, "exitY": 0.8, "entryX": 0, "entryY": 0.8},
                "p5b", "e_mgr", [(2190, 1360), (2190, 1420)]))

    # 5.0 -> Manager: Financial Summary & Reports
    E.append(ex("l0_p5_out3", "Financial Summary, Daily Sales Tally & Audit Reports",
                {"exitX": 1, "exitY": 0.95, "entryX": 0, "entryY": 0.92},
                "p5b", "e_mgr", [(2160, 1367), (2160, 1456)]))

    # ── PROCESS 6.0 FLOWS ─────────────────────────────────────────────────────
    # Manager -> 6.0: System Parameter Configurations
    E.append(ex("l0_p6_in1", "System Parameter & Tariff Configurations",
                {"exitX": 0.3, "exitY": 1, "entryX": 1, "entryY": 0.35},
                "e_mgr", "p6b", [(2537, 1480), (2537, 1640)]))

    # 6.0 -> Manager: Current System Settings
    E.append(ex("l0_p6_out1", "Current System Settings & Parameter Audit Data",
                {"exitX": 1, "exitY": 0.75, "entryX": 0.6, "entryY": 1},
                "p6b", "e_mgr", [(2594, 1661), (2594, 1480)]))

    # 6.0 -> tbl_system_settings (D6): Updated System Parameters
    E.append(ex("l0_p6_db1", "Updated System Parameters & Thresholds",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "p6b", "s_set_n", [(980, 1652), (980, 1640)]))

    # ── SUPER ADMIN FLOWS ─────────────────────────────────────────────────────
    # Super Admin -> 1.0 (Login & Dynamic Role Perspective Switch)
    E.append(ex("l0_p1_in5", "Super Admin Credentials & Role Switch Request",
                {"exitX": 1, "exitY": 0.2, "entryX": 0.94, "entryY": 0},
                "e_admin", "p1b", [(2760, 1770), (2760, 25), (1420, 25), (1420, 98)]))

    # 1.0 -> Super Admin (Authentication & Dynamic Perspective View Render)
    E.append(ex("l0_p1_out4", "Super Admin Auth Status & Perspective Render",
                {"exitX": 0.4, "exitY": 0, "entryX": 1, "entryY": 0.45},
                "p1b", "e_admin", [(1248, 12), (2780, 12), (2780, 1832)]))

    # Super Admin -> 1.0 (Staff Account Provisioning & Role Reassignment)
    E.append(ex("l0_p1_in6", "Staff Google SSO Provisioning & Role Reassignment",
                {"exitX": 0, "exitY": 0.6, "entryX": 0.81, "entryY": 1},
                "e_admin", "p1b", [(2060, 1870), (2060, 180), (1380, 180), (1380, 150)]))

    # 1.0 -> Super Admin (User Directory Records & Account Audit Data)
    E.append(ex("l0_p1_out5", "User Directory Records & Account Audit Data",
                {"exitX": 0.68, "exitY": 1, "entryX": 0, "entryY": 0.78},
                "p1b", "e_admin", [(1338, 220), (2090, 220), (2090, 1915)]))

    # Super Admin -> 5.0 (Audit Trail & Forecast Query Filter)
    E.append(ex("l0_p5_in3", "Audit Trail Query & Filter Parameters",
                {"exitX": 0, "exitY": 0.1, "entryX": 0.72, "entryY": 1},
                "e_admin", "p5b", [(2310, 1745), (2310, 1490), (1350, 1490), (1350, 1370)]))

    # 5.0 -> Super Admin (Executive Audit Trail & Prediction Logs)
    E.append(ex("l0_p5_out4", "Executive Operational Audit Trail & Prediction Logs",
                {"exitX": 0.5, "exitY": 1, "entryX": 0, "entryY": 0.22},
                "p5b", "e_admin", [(1280, 1530), (2340, 1530), (2340, 1775)]))

    # Super Admin -> 6.0 (Master Tariffs & Hardware Fleet Matrix Configuration)
    E.append(ex("l0_p6_in2", "Master Tariffs & Hardware Fleet Matrix Configurations",
                {"exitX": 0, "exitY": 0.35, "entryX": 0.81, "entryY": 1},
                "e_admin", "p6b", [(1380, 1807), (1380, 1680)]))

    # 6.0 -> Super Admin (Active Store Policies & Machine Matrix Audit Data)
    E.append(ex("l0_p6_out2", "Active Store Policies & Machine Matrix Audit Data",
                {"exitX": 0.6, "exitY": 1, "entryX": 0, "entryY": 0.48},
                "p6b", "e_admin", [(1312, 1840), (2480, 1840)]))

    # ── COMPILE DIAGRAM XML ───────────────────────────────────────────────────
    cells = "\n    ".join(S + E)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" version="22.0.0">\n'
        '  <diagram id="level_0_system_overview_drawio" name="Level 0 - System Overview">\n'
        '    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        'pageScale="1" pageWidth="2800" pageHeight="2050" math="0" shadow="0">\n'
        '      <root>\n'
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f'        {cells}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )
    # Parse check to guarantee 100% valid XML
    ET.fromstring(xml)
    OUT_FILE.write_text(xml, encoding="utf-8")
    print(f"SUCCESS: level_0_system_overview.drawio generated with {len(S)} shapes and {len(E)} edges.")


if __name__ == "__main__":
    build()
