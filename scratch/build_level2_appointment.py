"""
scratch/build_level2_appointment.py
Generates the Level 2 DFD for Process 2.0 — Appointment and Order Intake.

════════════════════════════════════════════════════════════════════════════════
PARENT BALANCE AUDIT (from level1_process2_appointment.drawio)
════════════════════════════════════════════════════════════════════════════════

INFLOWS into Process 2.0 from Level 1:
  ① Customer → 2.0 : Booking Data
                      (name, phone, email, service_type, schedule_date/time,
                       pickup_time, order_mode, payment_method, turnaround_option,
                       building, unit)
  ② tbl_appointment → 2.0 : Booking Data   (read for slot availability check)
  ③ tbl_machine_status → 2.0 : Machine Status  (read for capacity calculation)

OUTFLOWS from Process 2.0 in Level 1:
  ① 2.0 → Customer : Slot Availability  (available slots returned before booking)
  ② 2.0 → Customer : Booking Confirmation Details
                      (order_id, queue_number, service details, EWT)
  ③ 2.0 → Customer : Estimated Wait Time
  ④ 2.0 → Staff    : Appointment Status  (new booking visible on staff dashboard)
  ⑤ 2.0 → Staff    : Booking Data        (full booking row visible in queue)
  ⑥ 2.0 → tbl_appointment : Appointment Record  (persisted row)

════════════════════════════════════════════════════════════════════════════════
WHAT THE REAL SYSTEM ACTUALLY DOES (from routes/appointments.py):
════════════════════════════════════════════════════════════════════════════════

PROCESS 2.1 — Slot Availability Check
  Source: /api/appointments/availability (dashboard.py) and the pre-booking check
          inside create_order() before saving.
  - Customer submits schedule_time
  - Reads tbl_machine_status (count of non-Maintenance machines = capacity)
  - Reads tbl_appointment (count of Pending/Confirmed/In Progress bookings
    at the same schedule_time = booked)
  - Returns: available = max(capacity - booked, 0)
  - Output → Customer: Slot Availability (available slots count)

PROCESS 2.2 — Order Data Validation & Priority Assignment
  Source: create_order() lines 82–123
  - Validates required fields: name (required), phone/logged_user_id
  - Validates date: cannot be in the past (< today)
  - Validates time: cannot be already-past time for same day
  - Assigns priority_level from turnaround_option:
      '2 day'/'48h' → 'Graveyard Batch'
      '24h'/'Express' → 'Express 24h'
      Walk-in → 'Immediate'
      else → 'Standard'
  - Assigns fulfillment_status based on order_mode:
      'Pick-up & Delivery' → 'For Pickup'
      else → 'Waiting Drop-off'
  - Assigns payment_status = 'Pending' (always starts Pending)
  - Assembles address string from building + unit fields
  - Output → internal: Validated Order Data + Priority Assignment

PROCESS 2.3 — Appointment & Queue Record Creation
  Source: create_order() lines 126–168
  - Generates unique order_code (ORD-XXXXX) via _generate_unique_order_code()
    reads tbl_appointment to check uniqueness
  - Creates Appointment row (status='Pending') → writes to tbl_appointment
  - Reads tbl_queue to compute next_queue_number via QueueManager.generate_next_queue_number()
  - Calls QueueManager.calculate_current_ewt() → reads tbl_machine_status + tbl_queue
    + tbl_system_settings for cycle timings
  - Creates Queue row (status='Waiting', estimated_waiting_time=EWT)
    → writes to tbl_queue
  - Output → internal: Appointment & Queue Reference (for confirmation)
  - Output → Staff: New Booking & Queue Entry visible on dashboard

PROCESS 2.4 — Booking Confirmation & Email Notification
  Source: create_order() lines 170–203
  - If customer provided email → calls EmailService.send_order_confirmation()
    dispatches: order_code, name, service_type, schedule_str
  - Returns full confirmation payload to Customer:
    order_id, queue_number, priority_level, turnaround_option,
    payment_method, payment_status, fulfillment_status, estimated_wait_mins

════════════════════════════════════════════════════════════════════════════════
ISSUES WITH THE PAST DIAGRAM:
════════════════════════════════════════════════════════════════════════════════
1. "2.1 Slot Availability Check" wrote "Machine Status" to tbl_machine_status —
   a miracle write. Process 2.1 only READS machine status, never writes it.

2. "2.2 Booking Request Validation" received "Appointment Details" and "Booking
   Data" as SEPARATE flows both directly from Customer, and sent "Validation
   Result" back to Customer mid-process. In reality, Customer submits a single
   POST payload. Validation is purely internal with no intermediate customer
   feedback at the L2 level (only the final confirmation is sent back).

3. "2.3 Appointment Storage & Status Update" sent "Appointment Status" AND
   "Booking Data" as two separate flows to Staff. These should be one precise
   flow: the new appointment record becoming visible on the staff dashboard.

4. tbl_queue was completely absent from the past diagram, even though the real
   system creates a Queue row in the same transaction as the Appointment row
   and computes EWT from it.

5. tbl_system_settings was absent, even though QueueManager.calculate_current_ewt()
   reads standard_washer_time_mins and standard_dryer_time_mins from it.

6. "2.4 Confirmation Issuance" sent "Estimated Wait Time" and "Booking
   Confirmation Details" as two separate flows. They are one payload returned
   by the same API response / email dispatch.

════════════════════════════════════════════════════════════════════════════════
FUNCTIONAL PRIMITIVES (each explainable in one sentence):
  2.1  Slot Availability Check
       "Count non-Maintenance machines (capacity) and active bookings at the
        requested schedule_time (booked) and return available = capacity - booked."

  2.2  Order Data Validation & Priority Assignment
       "Reject missing name/phone and past-date/time submissions, then derive
        priority_level, fulfillment_status, payment_status, and full address
        from the submitted order fields."

  2.3  Appointment & Queue Record Creation
       "Generate a unique Order Code, persist the Appointment row, compute
        EWT from current queue depth and machine cycle parameters, then create
        a linked Queue row in Waiting status."

  2.4  Booking Confirmation & Email Notification
       "Dispatch an order-confirmation email to the customer's address if
        provided, then return the full confirmation payload including order_id,
        queue_number, and estimated wait time."
"""

import html as htmllib
import xml.etree.ElementTree as ET
from pathlib import Path

OUT_FILE = Path(
    r"c:\Users\genes\bon-laundry\docs\diagrams\level2_process2_appointment.drawio"
)

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
        vx(f"{sid}_d", "d1",  STORE_D, x,      y, sd,      sh),
        vx(f"{sid}_n", label, STORE_N, x + sd, y, sw - sd, sh),
    ]


def ent(eid, label, x, y, w=160, h=80):
    return vx(eid, label, ENTITY_ST, x, y, w, h)


def generate():
    S, E = [], []

    # ── PROCESSES (x=600, w=260) ──────────────────────────────────────────────
    # Process row tops:  2.1=80, 2.2=320, 2.3=560, 2.4=800
    S += proc("p21", "2.1", "Slot Availability Check",                    600, 80)
    S += proc("p22", "2.2", "Order Data Validation & Priority Assignment", 600, 320)
    S += proc("p23", "2.3", "Appointment & Queue Record Creation",         600, 560)
    S += proc("p24", "2.4", "Booking Confirmation & Email Notification",   600, 800)

    # ── EXTERNAL ENTITIES ─────────────────────────────────────────────────────
    # Customer on the left
    S.append(ent("e_cust",  "Customer", 50, 100, w=160, h=80))
    # Staff on the right (receives booking notification from 2.3)
    S.append(ent("e_staff", "Staff",    1480, 590, w=160, h=80))

    # ── GLOBAL DATA STORES ────────────────────────────────────────────────────
    # tbl_machine_status — top-right (read by 2.1 for capacity count)
    S += store("s_mac", "tbl_machine_status",  1200, 80,  sw=240)
    # tbl_appointment    — mid-right (read by 2.1; read+written by 2.3)
    S += store("s_apt", "tbl_appointment",     1200, 320, sw=240)
    # tbl_queue          — lower-right (read+written by 2.3 for EWT + Queue entry)
    S += store("s_que", "tbl_queue",           1200, 560, sw=240)
    # tbl_system_settings— far-right (read by 2.3 via QueueManager.calculate_current_ewt)
    S += store("s_set", "tbl_system_settings", 1200, 800, sw=240)

    # ─────────────────────────────────────────────────────────────────────────
    # DATA FLOWS
    # ─────────────────────────────────────────────────────────────────────────

    # ── 2.1 Slot Availability Check ──────────────────────────────────────────

    # 1. Customer → 2.1: Schedule Date & Time Request
    #    (schedule_date, schedule_time submitted to check availability)
    E.append(ex("e1", "Schedule Date & Time Request",
                {"exitX": 1, "exitY": 0.4, "entryX": 0, "entryY": 0.4},
                "e_cust", "p21b"))

    # 2. tbl_machine_status → 2.1: Machine Capacity Count
    #    (count of non-Maintenance machines = total slot capacity)
    E.append(ex("e2", "Machine Capacity Count",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_mac_n", "p21b"))

    # 3. tbl_appointment → 2.1: Active Bookings at Requested Time
    #    (count of Pending/Confirmed/In Progress appointments matching schedule_time)
    E.append(ex("e3", "Active Bookings at Requested Time",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.7},
                "s_apt_n", "p21b",
                [(1120, 343), (1120, 138)]))

    # 4. 2.1 → Customer: Slot Availability
    #    (available = max(capacity - booked, 0))
    E.append(ex("e4", "Slot Availability",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.3},
                "p21b", "e_cust",
                [(490, 109), (490, 114)]))

    # 5. 2.1 → 2.2: Confirmed Available Slot
    #    (slot is confirmed open; passes the full order payload forward for validation)
    E.append(ex("e5", "Confirmed Available Slot",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p21b", "p22b"))

    # ── 2.2 Order Data Validation & Priority Assignment ───────────────────────

    # 6. Customer → 2.2: Full Order Submission
    #    (name, phone, email, service_type, schedule_date/time, pickup_time,
    #     order_mode, payment_method, turnaround_option, building, unit)
    E.append(ex("e6", "Full Order Submission",
                {"exitX": 1, "exitY": 0.6, "entryX": 0, "entryY": 0.5},
                "e_cust", "p22b",
                [(430, 148), (430, 378)]))

    # 7. 2.2 → Customer: Validation Error (if fields fail)
    #    (error message: missing name/phone, past date/time)
    E.append(ex("e7", "Validation Error",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.7},
                "p22b", "e_cust",
                [(470, 378), (470, 148)]))

    # 8. 2.2 → 2.3: Validated Order Data & Priority Assignment
    #    (all validated fields + derived priority_level, fulfillment_status,
    #     payment_status, formatted address)
    E.append(ex("e8", "Validated Order Data & Priority Assignment",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p22b", "p23b"))

    # ── 2.3 Appointment & Queue Record Creation ───────────────────────────────

    # 9. tbl_appointment → 2.3: Existing Order Codes
    #    (read to ensure uniqueness of new ORD-XXXXX code)
    E.append(ex("e9", "Existing Order Codes",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.3},
                "s_apt_n", "p23b"))

    # 10. tbl_queue → 2.3: Current Queue Depth
    #     (highest queue_number + Waiting count for EWT calculation)
    E.append(ex("e10", "Current Queue Depth",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_que_n", "p23b"))

    # 11. tbl_system_settings → 2.3: Cycle Timing Parameters
    #     (standard_washer_time_mins, standard_dryer_time_mins for EWT formula)
    E.append(ex("e11", "Cycle Timing Parameters",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.7},
                "s_set_n", "p23b",
                [(1120, 823), (1120, 638)]))

    # 12. 2.3 → tbl_appointment: New Appointment Record
    #     (order_code, customer fields, schedule_time, service_type,
    #      turnaround_option, priority_level, order_mode, payment_method,
    #      payment_status='Pending', fulfillment_status, status='Pending')
    E.append(ex("e12", "New Appointment Record",
                {"exitX": 1, "exitY": 0.3, "entryX": 0, "entryY": 0.7},
                "p23b", "s_apt_n",
                [(1100, 588), (1100, 366)]))

    # 13. 2.3 → tbl_queue: New Queue Entry
    #     (queue_number, appointment_id, customer_name, turnaround_option,
    #      priority_level, order_mode, payment_method, payment_status,
    #      fulfillment_status, status='Waiting', estimated_waiting_time=EWT)
    E.append(ex("e13", "New Queue Entry",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.7},
                "p23b", "s_que_n",
                [(1110, 618), (1110, 596)]))

    # 14. 2.3 → Staff: New Booking & Queue Entry Notification
    #     (new appointment row now visible on the staff dashboard queue table)
    E.append(ex("e14", "New Booking & Queue Entry Notification",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p23b", "e_staff"))

    # 15. 2.3 → 2.4: Appointment & Queue Reference
    #     (appointment_id, order_code, queue_number, EWT, email for dispatch)
    E.append(ex("e15", "Appointment & Queue Reference",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p23b", "p24b"))

    # ── 2.4 Booking Confirmation & Email Notification ─────────────────────────

    # 16. 2.4 → Customer: Booking Confirmation & EWT
    #     (order_id=ORD-XXXXX, queue_number, priority_level, turnaround_option,
    #      payment_method, payment_status, fulfillment_status, estimated_wait_mins,
    #      + email confirmation sent if email was provided)
    E.append(ex("e16", "Booking Confirmation & EWT",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "p24b", "e_cust",
                [(450, 848), (450, 140)]))

    # ── Render XML ────────────────────────────────────────────────────────────
    cells = "\n    ".join(S + E)
    dname = "Level 2 - Process 2: Appointment and Order Intake"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" version="22.0.0">\n'
        f'  <diagram id="level2_process2_appointment" name="{_e(dname)}">\n'
        f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        f'pageScale="1" pageWidth="1900" pageHeight="1100" math="0" shadow="0">\n'
        '      <root>\n'
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f'        {cells}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )

    ET.fromstring(xml)   # validate XML
    OUT_FILE.write_text(xml, encoding="utf-8")
    print(f"SUCCESS: {OUT_FILE}")
    print(f"Shapes: {len(S)}, Edges: {len(E)}")


if __name__ == "__main__":
    generate()
