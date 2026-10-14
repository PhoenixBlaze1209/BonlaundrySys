"""
scratch/build_level2_pos.py
Generates the Level 2 DFD for Process 3.0 — POS Sales & Transactions.

Parent Level 1 flows this must BALANCE with (from level1_process3_pos_sales.drawio):
  INFLOWS into Process 3.0:
    - Walk-in Order & Load Details        (Staff → 3.0)
    - Payment Details & Proof             (Customer → 3.0)
    - Cash Payment Collection Verification(Staff → 3.0)
    - tbl_system_settings → 3.0           Base Weight Rates & Pricing Rules
    - tbl_machine_status → 3.0            Machine Availability Status (read by Level 1 p33b)
  OUTFLOWS from Process 3.0:
    - Calculated Service Fee & Bill Info  (3.0 → Staff)
    - Active Queue & Machine Status Info  (3.0 → Staff)  [from p33b in Level 1]
    - Digital Payment Receipt             (3.0 → Customer)
    - tbl_queue  ← Queue Data
    - tbl_machine_status ← Machine Cycle Record
    - tbl_transaction ← Completed Transaction Record

Sub-processes (decimal numbered under parent 3.0):
  3.1  Service Package & Load Validation
  3.2  Fee Calculation
  3.3  Machine Availability Check & Cycle Initiation
  3.4  Queue Assignment & Record Entry
  3.5  Transaction Recording & Receipt Dispatch

Layout:
  Column A (entities / stores left)  x=50
  Column B (processes)               x=600, w=260
  Column C (stores / entities right) x=1200
  Process rows y:  80 / 320 / 560 / 800 / 1040
  hdr=28, bod=60 → total 88px per process
"""

import html as htmllib
import xml.etree.ElementTree as ET
from pathlib import Path

OUT_FILE = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\level2_process3_pos_sales.drawio")

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


def proc(pid, num, body, x, y, w=260, hdr=28, bod=60):
    return [
        vx(f"{pid}h", num,  PROC_HDR, x, y,       w, hdr),
        vx(f"{pid}b", body, PROC_BOD, x, y + hdr, w, bod),
    ]


def store(sid, label, x, y, sw=240, sh=46, sd=34):
    return [
        vx(f"{sid}_d", "d1",   STORE_D, x,      y, sd,      sh),
        vx(f"{sid}_n", label,  STORE_N, x + sd, y, sw - sd, sh),
    ]


def ent(eid, label, x, y, w=160, h=80):
    return vx(eid, label, ENTITY_ST, x, y, w, h)


def generate():
    S, E = [], []

    # ── PROCESS COLUMN (x=600, w=260) ─────────────────────────────────────────
    # Process row centres:
    #   3.1 top=80   body: 108–168
    #   3.2 top=320  body: 348–408
    #   3.3 top=560  body: 588–648
    #   3.4 top=800  body: 828–888
    #   3.5 top=1040 body: 1068–1128

    S += proc("p31", "3.1", "Service Package & Load Validation",        600, 80)
    S += proc("p32", "3.2", "Fee Calculation",                          600, 320)
    S += proc("p33", "3.3", "Machine Availability Check & Cycle Start", 600, 560)
    S += proc("p34", "3.4", "Queue Assignment & Record Entry",           600, 800)
    S += proc("p35", "3.5", "Transaction Recording & Receipt Dispatch", 600, 1040)

    # ── EXTERNAL ENTITIES ─────────────────────────────────────────────────────
    # Staff: Left column, spans the top half (aligned with 3.1–3.3)
    S.append(ent("e_staff", "Staff",    50, 100, w=160, h=80))
    # Customer: Left column, bottom (aligned with 3.5)
    S.append(ent("e_cust",  "Customer", 50, 1060, w=160, h=80))

    # ── GLOBAL DATA STORES ────────────────────────────────────────────────────
    # (Global = also used in Level 1 by process 3.0)
    # tbl_system_settings — Right column, top (feeds 3.1 for validation rules)
    S += store("s_set", "tbl_system_settings", 1200, 90,  sw=240)
    # tbl_machine_status  — Right column, middle (feeds 3.3 and receives update)
    S += store("s_mac", "tbl_machine_status",  1200, 570, sw=240)
    # tbl_queue           — Right column, lower  (receives from 3.4)
    S += store("s_que", "tbl_queue",           1200, 810, sw=240)
    # tbl_transaction     — Right column, bottom (receives from 3.5)
    S += store("s_trx", "tbl_transaction",     1200, 1050, sw=240)

    # ─────────────────────────────────────────────────────────────────────────
    # DATA FLOWS
    # ─────────────────────────────────────────────────────────────────────────

    # 1. Staff → 3.1: Walk-in Order & Load Details
    #    (service_code, weight_kg, addon_codes, customer_name, cycle_type)
    E.append(ex("e1", "Walk-in Order & Load Details",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "e_staff", "p31b"))

    # 2. tbl_system_settings → 3.1: Service Package Pricing Rules
    #    (SERVICES table: label, base_price, max_weight; ADDONS table)
    E.append(ex("e2", "Service Package Pricing Rules",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_set_n", "p31b"))

    # 3. 3.1 → Staff: Validation Status (pass/fail + reason)
    E.append(ex("e3", "Validation Status",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.3},
                "p31b", "e_staff",
                [(490, 124), (490, 110)]))

    # 4. 3.1 → 3.2: Validated Load & Package Data
    #    (validated weight, service_code, addon_codes)
    E.append(ex("e4", "Validated Load & Package Data",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p31b", "p32b"))

    # 5. tbl_system_settings → 3.2: Active Pricing Rates
    #    (price_per_kg, turnaround surcharges, delivery fee — via POSProcessor.ADDONS)
    E.append(ex("e5", "Active Pricing Rates & Add-on Costs",
                {"exitX": 0, "exitY": 0.75, "entryX": 1, "entryY": 0.5},
                "s_set_n", "p32b",
                [(1120, 124), (1120, 378)]))

    # 6. 3.2 → Staff: Calculated Service Fee & Bill Breakdown
    #    (base_price + addons_total, service_label, add-on list)
    E.append(ex("e6", "Calculated Service Fee & Bill Breakdown",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.7},
                "p32b", "e_staff",
                [(470, 378), (470, 140)]))

    # 7. 3.2 → 3.3: Service Fee & Assignment Request
    #    (total_amount, machine_id, cycle_type, customer_name, weight)
    E.append(ex("e7", "Service Fee & Assignment Request",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p32b", "p33b"))

    # 8. tbl_machine_status → 3.3: Machine Capacity & Operational State
    #    (machine_id, capacity_kg, status, operational_state, cycle_ends_at)
    E.append(ex("e8", "Machine Capacity & Operational State",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_mac_n", "p33b"))

    # 9. 3.3 → tbl_machine_status: Machine Cycle Record
    #    (status=In-Use, cycle_type, cycle_started_at, cycle_ends_at, assigned_customer_name)
    E.append(ex("e9", "Machine Cycle Record",
                {"exitX": 1, "exitY": 0.3, "entryX": 0, "entryY": 0.3},
                "p33b", "s_mac_n",
                [(1100, 606), (1100, 584)]))

    # 10. 3.3 → Staff: Machine Assignment & EWT Notice
    #     (machine_name, starts_now, estimated_waiting_time)
    E.append(ex("e10", "Machine Assignment & EWT Notice",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.9},
                "p33b", "e_staff",
                [(450, 618), (450, 170)]))

    # 11. 3.3 → 3.4: Queue Entry Request
    #     (next_queue_number, machine_id, status=Processing/Waiting, EWT, customer_name)
    E.append(ex("e11", "Queue Entry Request",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p33b", "p34b"))

    # 12. 3.4 → tbl_queue: New Queue Entry
    #     (queue_number, machine_id, status, estimated_waiting_time, customer_name, transaction_id)
    E.append(ex("e12", "New Queue Entry",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p34b", "s_que_n"))

    # 13. 3.4 → 3.5: Transaction & Queue Reference
    #     (transaction details + queue_number for receipt)
    E.append(ex("e13", "Transaction & Queue Reference",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p34b", "p35b"))

    # 14. Customer → 3.5: Payment Details & Proof
    #     (payment_status, customer_email for receipt, proof of payment)
    E.append(ex("e14", "Payment Details & Proof",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.7},
                "e_cust", "p35b",
                [(420, 1100), (420, 1108)]))

    # 15. 3.5 → tbl_transaction: Completed Transaction Record
    #     (customer_id/null, weight_kg, total_amount, payment_status,
    #      customer_name, machine_id, cycle_type)
    E.append(ex("e15", "Completed Transaction Record",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p35b", "s_trx_n"))

    # 16. 3.5 → Customer: Digital Payment Receipt & Confirmation
    #     (transaction_id=TRX-XXXX, service_label, total_amount, queue_number, EWT, email receipt)
    E.append(ex("e16", "Digital Payment Receipt & Confirmation",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "p35b", "e_cust",
                [(510, 1100), (510, 1100)]))

    # ── Render XML ───────────────────────────────────────────────────────────
    cells = "\n    ".join(S + E)
    dname = "Level 2 - Process 3: POS Sales and Transactions"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" version="22.0.0">\n'
        f'  <diagram id="level2_process3_pos_sales" name="{_e(dname)}">\n'
        f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        f'pageScale="1" pageWidth="1800" pageHeight="1400" math="0" shadow="0">\n'
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
    OUT_FILE.write_text(xml, encoding="utf-8")
    print(f"SUCCESS: {OUT_FILE}")
    print(f"Shapes: {len(S)}, Edges: {len(E)} (Expected 16 edges)")


if __name__ == "__main__":
    generate()
