"""
scratch/build_level2_queue.py
Generates the Level 2 DFD for Process 4.0 — Queue and Operational Status.

════════════════════════════════════════════════════════════════════════════════
PARENT BALANCE AUDIT (from level1_process4_queue.drawio)
════════════════════════════════════════════════════════════════════════════════

INFLOWS into Process 4.0 from Level 1:
  ① Staff  → 4.0 : Queue Request
  ② Staff  → 4.0 : Machine Status  (staff providing machine state for monitoring)
  ③ tbl_machine_status → 4.0 : Machine Status  (read cycle/availability data)
  ④ tbl_queue → 4.0 : (implied: queue read for EWT calc — global store)

OUTFLOWS from Process 4.0 in Level 1:
  ① 4.0 → Staff     : Queue Status
  ② 4.0 → Customer  : EWT Notification
  ③ 4.0 → Customer  : Machine Status (live status push)
  ④ 4.0 → Customer  : Queue Notification
  ⑤ 4.0 → Staff     : Service Commencement Alert
  ⑥ 4.0 → tbl_machine_status : Machine Status  (write cycle updates)
  ⑦ 4.0 → tbl_queue : Queue Status  (write queue entries)

════════════════════════════════════════════════════════════════════════════════
WHAT THE REAL SYSTEM ACTUALLY DOES (from code):
════════════════════════════════════════════════════════════════════════════════

PROCESS 4.1 — Queue Slot & EWT Assignment
  - Triggered when staff adds an appointment or walk-in to the queue
    (dashboard.py → appointments_api POST / queue_api POST)
  - Reads tbl_machine_status for occupied/available count and cycle timings
  - Reads tbl_queue for current Waiting count
  - Calls QueueManager.calculate_current_ewt() → EWT in minutes
  - Reads tbl_system_settings for wash_time (35 min) and dry_time (30 min)
  - Writes new Queue row (queue_number, status='Waiting', estimated_waiting_time)
    to tbl_queue
  - Returns Queue Status (queue_number, EWT) → Staff display

PROCESS 4.2 — Machine Cycle Refresh & Queue Advancement
  - Triggered on every checkout/check-in call via refresh_machine_cycles(db)
  - Reads tbl_machine_status for cycles that have ended (cycle_ends_at <= now)
  - Marks finished machine as Available, clears cycle fields
  - Marks linked Queue rows as status='Done'
  - Calls start_next_queued_job() → picks next Waiting entry, starts cycle
  - Updates tbl_machine_status (status='In-Use', new cycle timestamps)
  - Updates tbl_queue (status='Processing', estimated_waiting_time=0)

PROCESS 4.3 — Waiting EWT Recalculation
  - Called from refresh_waiting_estimates() inside refresh_machine_cycles()
  - For every machine: recalculates cumulative EWT for all Waiting jobs
  - Reads tbl_machine_status (cycle_ends_at remaining time per machine)
  - Reads tbl_queue (Waiting entries per machine, ordered by queue_number)
  - Writes updated estimated_waiting_time back to each Waiting Queue row
    in tbl_queue
  - This data is what the Staff and Customer dashboard polls see

PROCESS 4.4 — Live Queue & Machine Status Feed
  - Staff and Customer dashboards poll /api/dashboard/summary and /api/queue
  - Reads tbl_queue (active rows: status IN ['Waiting','Processing'])
  - Reads tbl_machine_status (all machines for display)
  - Joins tbl_appointment + tbl_user for customer name, phone, service type
  - Outputs Live Queue & Machine Status Feed → Staff (dashboard table)
  - Outputs Live Queue Position & EWT → Customer (their own queue entry)

════════════════════════════════════════════════════════════════════════════════
ISSUES WITH THE PAST DIAGRAM:
════════════════════════════════════════════════════════════════════════════════
1. "4.1 Queue Entry" — was a black hole writing BOTH to tbl_machine_status AND
   tbl_queue in a single step. In reality, at this step the system only READS
   machine status (for EWT calc) and WRITES a new Queue row. Machine cycle
   updates happen separately in 4.2.

2. "4.2 Predictive Wait-Time Calculation" — sent EWT directly to Customer as a
   push notification. The real system has no real-time push/SMS; the EWT is
   stored in tbl_queue and served when dashboards poll. The Customer receives
   it passively via the queue status feed, not a direct notification.

3. "4.3 Real-Time Status Monitoring" — had Staff sending "Machine Status" as
   INPUT to this process. Staff does not send machine data TO the system; the
   system reads it from tbl_machine_status. The input is a "miracle" flow.

4. "4.4 Queue Progression & Notification" — sent "Queue Notification" to
   Customer as an active push. The real system sends email only on ORDER
   COMPLETION (send_order_completed), not a separate queue notification step.
   The customer sees live status by polling the feed.

5. tbl_system_settings was not in the past diagram at all, but
   QueueManager.calculate_current_ewt() reads wash_time and dry_time from it.
   This is a Global store that must be shown.

════════════════════════════════════════════════════════════════════════════════
FUNCTIONAL PRIMITIVES — each explainable in one sentence:
  4.1  Queue Slot & EWT Assignment
       "Compute the estimated wait time for a new customer based on
        current machine occupancy and waiting count, then create a Queue row."

  4.2  Machine Cycle Refresh & Queue Advancement
       "Detect machines whose cycle timer has elapsed, mark them available,
        promote the next Waiting queue entry to Processing, and start the
        machine cycle."

  4.3  Waiting EWT Recalculation
       "For every Waiting queue entry on each machine, recalculate its
        cumulative position-based wait time and persist the updated value."

  4.4  Live Queue & Machine Status Feed
       "Query all active queue rows and machine states and return the unified
        live status payload consumed by the Staff and Customer dashboards."
"""

import html as htmllib
import xml.etree.ElementTree as ET
from pathlib import Path

OUT_FILE = Path(
    r"c:\Users\genes\bon-laundry\docs\diagrams\level2_process4_queue.drawio"
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
        vx(f"{sid}_d", "d1",   STORE_D, x,      y, sd,      sh),
        vx(f"{sid}_n", label,  STORE_N, x + sd, y, sw - sd, sh),
    ]


def ent(eid, label, x, y, w=160, h=80):
    return vx(eid, label, ENTITY_ST, x, y, w, h)


def generate():
    S, E = [], []

    # ── PROCESSES (x=600, w=260) ──────────────────────────────────────────────
    # Rows: 4.1=80, 4.2=320, 4.3=560, 4.4=800
    S += proc("p41", "4.1", "Queue Slot & EWT Assignment",             600, 80)
    S += proc("p42", "4.2", "Machine Cycle Refresh & Queue Advancement", 600, 320)
    S += proc("p43", "4.3", "Waiting EWT Recalculation",               600, 560)
    S += proc("p44", "4.4", "Live Queue & Machine Status Feed",         600, 800)

    # ── EXTERNAL ENTITIES ─────────────────────────────────────────────────────
    S.append(ent("e_staff", "Staff",    50,  100, w=160, h=80))
    S.append(ent("e_cust",  "Customer", 50,  830, w=160, h=80))

    # ── GLOBAL DATA STORES ────────────────────────────────────────────────────
    # tbl_system_settings — top-right (read by 4.1 for cycle time params)
    S += store("s_set", "tbl_system_settings", 1200, 80,  sw=240)
    # tbl_machine_status  — mid-right (read by 4.1, 4.2, 4.3, 4.4; written by 4.2)
    S += store("s_mac", "tbl_machine_status",  1200, 330, sw=240)
    # tbl_queue           — lower-right (read by 4.1, 4.3, 4.4; written by 4.1, 4.2, 4.3)
    S += store("s_que", "tbl_queue",           1200, 570, sw=240)

    # ─────────────────────────────────────────────────────────────────────────
    # DATA FLOWS
    # ─────────────────────────────────────────────────────────────────────────

    # ── 4.1 Queue Slot & EWT Assignment ──────────────────────────────────────

    # 1. Staff → 4.1: Queue Request
    #    (customer_name, appointment_id or walk-in flag)
    E.append(ex("e1", "Queue Request",
                {"exitX": 1, "exitY": 0.4, "entryX": 0, "entryY": 0.4},
                "e_staff", "p41b"))

    # 2. tbl_system_settings → 4.1: Cycle Timing Parameters
    #    (standard_washer_time_mins=35, standard_dryer_time_mins=30)
    E.append(ex("e2", "Cycle Timing Parameters",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_set_n", "p41b"))

    # 3. tbl_machine_status → 4.1: Machine Occupancy Data
    #    (count of occupied vs available vs total non-Maintenance machines)
    E.append(ex("e3", "Machine Occupancy Data",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.3},
                "s_mac_n", "p41b",
                [(1120, 348), (1120, 118)]))

    # 4. tbl_queue → 4.1: Current Waiting Count
    #    (count of Queue rows with status='Waiting')
    E.append(ex("e4", "Current Waiting Count",
                {"exitX": 0, "exitY": 0.3, "entryX": 1, "entryY": 0.7},
                "s_que_n", "p41b",
                [(1100, 588), (1100, 148)]))

    # 5. 4.1 → tbl_queue: New Queue Entry
    #    (queue_number, appointment_id/null, status='Waiting', estimated_waiting_time)
    E.append(ex("e5", "New Queue Entry",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.7},
                "p41b", "s_que_n",
                [(1060, 138), (1060, 599)]))

    # 6. 4.1 → Staff: Queue Status
    #    (queue_number, estimated_waiting_time)
    E.append(ex("e6", "Queue Status",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.6},
                "p41b", "e_staff",
                [(490, 139), (490, 128)]))

    # 7. 4.1 → 4.2: Queue Entry Reference
    #    (triggers cycle refresh to check if machine is now idle and can start immediately)
    E.append(ex("e7", "Queue Entry Reference",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p41b", "p42b"))

    # ── 4.2 Machine Cycle Refresh & Queue Advancement ─────────────────────────

    # 8. tbl_machine_status → 4.2: Machine Cycle State
    #    (all machines: status, cycle_ends_at, operational_state)
    E.append(ex("e8", "Machine Cycle State",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_mac_n", "p42b"))

    # 9. tbl_queue → 4.2: Next Waiting Queue Entry
    #    (oldest Waiting entry for each newly freed machine)
    E.append(ex("e9", "Next Waiting Queue Entry",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.7},
                "s_que_n", "p42b",
                [(1080, 593), (1080, 398)]))

    # 10. 4.2 → tbl_machine_status: Updated Cycle Record
    #     (status='In-Use'/'Available', cycle_type, cycle_started_at, cycle_ends_at,
    #      assigned_customer_name, usage_count cleared to null when done)
    E.append(ex("e10", "Updated Cycle Record",
                {"exitX": 1, "exitY": 0.35, "entryX": 0, "entryY": 0.7},
                "p42b", "s_mac_n",
                [(1100, 361), (1100, 382)]))

    # 11. 4.2 → tbl_queue: Updated Queue Status
    #     (status='Processing'/'Done', estimated_waiting_time=0 for started entry)
    E.append(ex("e11", "Updated Queue Status",
                {"exitX": 1, "exitY": 0.65, "entryX": 0, "entryY": 0.35},
                "p42b", "s_que_n",
                [(1090, 401), (1090, 586)]))

    # 12. 4.2 → 4.3: Cycle Completion Signal
    #     (triggers EWT recalculation for all remaining Waiting entries)
    E.append(ex("e12", "Cycle Completion Signal",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p42b", "p43b"))

    # ── 4.3 Waiting EWT Recalculation ─────────────────────────────────────────

    # 13. tbl_machine_status → 4.3: Remaining Cycle Time per Machine
    #     (cycle_ends_at for all machines still running)
    E.append(ex("e13", "Remaining Cycle Time per Machine",
                {"exitX": 0, "exitY": 0.7, "entryX": 1, "entryY": 0.3},
                "s_mac_n", "p43b",
                [(1110, 376), (1110, 588)]))

    # 14. tbl_queue → 4.3: Waiting Entries per Machine
    #     (all Queue rows with status='Waiting', ordered by queue_number)
    E.append(ex("e14", "Waiting Entries per Machine",
                {"exitX": 0, "exitY": 0.7, "entryX": 1, "entryY": 0.7},
                "s_que_n", "p43b"))

    # 15. 4.3 → tbl_queue: Recalculated EWT per Entry
    #     (updated estimated_waiting_time for each Waiting Queue row)
    E.append(ex("e15", "Recalculated EWT per Entry",
                {"exitX": 1, "exitY": 0.5, "entryX": 0, "entryY": 0.5},
                "p43b", "s_que_n"))

    # 16. 4.3 → 4.4: EWT Refresh Complete Signal
    #     (signals feed process that fresh data is now readable)
    E.append(ex("e16", "EWT Refresh Complete",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p43b", "p44b"))

    # ── 4.4 Live Queue & Machine Status Feed ──────────────────────────────────

    # 17. tbl_queue → 4.4: Active Queue Rows
    #     (status IN ['Waiting','Processing'], joined to tbl_appointment, tbl_user)
    E.append(ex("e17", "Active Queue Rows",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.7},
                "s_que_n", "p44b",
                [(1060, 593), (1060, 858)]))

    # 18. tbl_machine_status → 4.4: All Machine States
    #     (name, status, cycle_type, capacity_kg, remaining_minutes for every machine)
    E.append(ex("e18", "All Machine States",
                {"exitX": 0, "exitY": 0.9, "entryX": 1, "entryY": 0.3},
                "s_mac_n", "p44b",
                [(1120, 362), (1120, 824)]))

    # 19. 4.4 → Staff: Live Queue & Machine Status
    #     (unified dashboard payload: queue table + machine cards + EWT metrics)
    E.append(ex("e19", "Live Queue & Machine Status",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "p44b", "e_staff",
                [(480, 848), (480, 140)]))

    # 20. 4.4 → Customer: Live Queue Position & EWT
    #     (customer's own queue_number, status, estimated_waiting_time, machine name)
    E.append(ex("e20", "Live Queue Position & EWT",
                {"exitX": 0, "exitY": 0.7, "entryX": 1, "entryY": 0.7},
                "p44b", "e_cust"))

    # ── Render XML ────────────────────────────────────────────────────────────
    cells = "\n    ".join(S + E)
    dname = "Level 2 - Process 4: Queue and Operational Status"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" version="22.0.0">\n'
        f'  <diagram id="level2_process4_queue" name="{_e(dname)}">\n'
        f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        f'pageScale="1" pageWidth="1800" pageHeight="1200" math="0" shadow="0">\n'
        '      <root>\n'
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f'        {cells}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )

    ET.fromstring(xml)  # validate XML well-formedness
    OUT_FILE.write_text(xml, encoding="utf-8")
    print(f"SUCCESS: {OUT_FILE}")
    print(f"Shapes: {len(S)}, Edges: {len(E)}")


if __name__ == "__main__":
    generate()
