"""
scratch/build_level2_analytics.py
Generates the Level 2 DFD for Process 5.0 — Analytics and Forecasting.

════════════════════════════════════════════════════════════════════════════════
PARENT BALANCE AUDIT (from level1_process5_analytics.drawio)
════════════════════════════════════════════════════════════════════════════════

INFLOWS into Process 5.0 from Level 1:
  ① tbl_queue       → 5.0 : Queue Waiting Status        (read)
  ② tbl_transaction → 5.0 : Transaction Records         (read)
  ③ tbl_machine_status → 5.0 : Machine Utilization Rates (read)

OUTFLOWS from Process 5.0 in Level 1:
  ① 5.0 → Manager : Peak Hour Charts & Demand Predictions
  ② 5.0 → Manager : Automated Reports (sales tally + CSV export)
  Note: "Revenue Data" flowing FROM Manager TO 5.4 in the past L1 was a miracle
        input — Manager does not feed raw revenue data to the engine;
        the engine reads it from tbl_transaction. This was an L1 error
        carried forward into the past L2.

════════════════════════════════════════════════════════════════════════════════
WHAT THE REAL SYSTEM ACTUALLY DOES (from services/analytics_engine.py,
routes/dashboard.py):
════════════════════════════════════════════════════════════════════════════════

PROCESS 5.1 — Historical Transaction Data Retrieval
  Source: train_and_predict_peak_hour() lines 20–50
          get_ghost_slots() lines 151–168
  - Queries ALL Transaction rows from tbl_transaction
  - Extracts: created_at.hour, transaction_id (for footfall count)
              customer_name, weight_kg, cycle_type (for ghost-slot analysis)
  - Structures into a Pandas DataFrame
  - Aggregates footfall count per operational hour (8 AM – 8 PM)
  - Output → internal: Hourly Footfall Aggregate + Customer Visit Patterns

PROCESS 5.2 — Peak Hour Polynomial Regression Model
  Source: train_and_predict_peak_hour() lines 52–87
  - Reads tbl_machine_status for machine usage_count and cycle patterns
    (used by get_ghost_slots — referenced in the ghost slot assignment)
  - Applies NumPy 2nd-degree polynomial regression (polyfit deg=2) on
    hourly footfall data
  - Predicts footfall across 8 AM–8 PM window (polyval)
  - Clips negative values to 0
  - Identifies peak_hour_idx = argmax of predicted_footfall
  - Computes calibrated MAPE (only on hours where y > 0)
  - Generates rule-based insight text based on predicted peak hour range
  - Output → internal: Forecast Result
    (predicted_peak, mape, insight, chart_labels, chart_data, historical_data)

PROCESS 5.3 — Ghost Slot Pattern Detection & Machine Recommendation
  Source: get_ghost_slots() lines 138–234 and assign_ghost_slot() lines 238–362
  - Reads tbl_transaction (customer_name, hour, weight_kg, cycle_type, day_of_week)
  - Groups by customer_name, filters customers with >= min_visits (default 3)
  - Identifies top_hour, top_day, pref_cycle, avg_weight via Counter
  - Reads tbl_machine_status (operational_state, machine_type, capacity_kg,
    queue count per machine) to find the lowest-wait compatible machine
  - Reads tbl_queue (Waiting count per machine for EWT calculation)
  - When assigned: creates Transaction + Queue row
    → writes to tbl_transaction, tbl_queue, tbl_machine_status
  - Output → Manager: Ghost Slot Recommendations
    (customer_name, usual_time, recommended_machine, wait_time)

PROCESS 5.4 — Prediction Audit Log & Forecast Dashboard Output
  Source: train_and_predict_peak_hour() lines 94–121
          dashboard.py manager_home(), live_forecast_api(), sales_tally_api()
  - When record_log=True: creates PredictionLog row (prediction_target,
    predicted_value, actual_value, mape_score) → writes to tbl_prediction_logs
  - Reads tbl_prediction_logs to serve the audit table on manager dashboard
  - Reads tbl_transaction for sales tally aggregations (daily, weekly, monthly
    gross sales, paid vs unpaid, tx_count, weight_kg)
  - Serves the combined manager dashboard payload:
    → Manager: Peak Demand Forecast & Audit Logs
               Sales Tally Report (daily breakdowns + summary metrics)

════════════════════════════════════════════════════════════════════════════════
ISSUES WITH THE PAST DIAGRAM:
════════════════════════════════════════════════════════════════════════════════
1. "5.1 Data Retrieval" wrote "Transaction Logs" TO tbl_queue — a miracle write.
   Process 5.1 READS from both stores. It writes nothing.

2. "5.2 Predictive Analytics Engine" was one bloated process doing:
   - Footfall aggregation (really step 5.1)
   - Polynomial regression
   - Ghost slot pattern detection
   - Machine recommendation
   All bundled as one. Ghost slot logic is a clearly separable functional primitive.

3. "5.3 Visualization Module" — there is no separate visualization module in
   the code. The forecast payload (chart_labels, chart_data) is built inside
   train_and_predict_peak_hour() and returned directly. There is no distinct
   process that transforms forecast data into charts before delivering to Manager.

4. "5.4 Report Generator" received "Revenue Data" FROM Manager as an INPUT.
   Manager does not feed revenue data to the system — this is a miracle input.
   Revenue data comes from tbl_transaction, not from Manager.

5. tbl_prediction_logs (the PredictionLog model) was completely absent.
   The engine explicitly creates audit log rows (record_log=True path).
   This is a Global store used by the Level 1 parent and must be shown.

6. Numbering: the past diagram used "4.4 Report Generator" — wrong parent
   number. It should be "5.4" since this is under Process 5.0.

════════════════════════════════════════════════════════════════════════════════
FUNCTIONAL PRIMITIVES:
  5.1  Historical Transaction Data Retrieval
       "Query all Transaction rows, extract hour-of-day and customer metadata,
        and aggregate footfall count per operational hour into a DataFrame."

  5.2  Peak Hour Polynomial Regression & Insight Generation
       "Fit a 2nd-degree polynomial to the hourly footfall data, predict
        footfall across 8 AM–8 PM, identify the peak hour, compute MAPE,
        and generate a rule-based operational insight string."

  5.3  Ghost Slot Pattern Detection & Machine Recommendation
       "Group historical transactions by customer name, identify habitual
        visit hours and preferred cycle types, then score and return the
        lowest-queue compatible machine for each repeat customer."

  5.4  Prediction Audit Logging & Manager Dashboard Output
       "Persist the prediction result to tbl_prediction_logs when flagged,
        aggregate daily/weekly/monthly revenue from tbl_transaction,
        and return the combined forecast and sales report to the Manager."
"""

import html as htmllib
import xml.etree.ElementTree as ET
from pathlib import Path

OUT_FILE = Path(
    r"c:\Users\genes\bon-laundry\docs\diagrams\level2_process5_analytics.drawio"
)

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


def proc(pid, num, body, x, y, w=270, hdr=28, bod=60):
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

    # ── PROCESSES (x=580, w=270) ──────────────────────────────────────────────
    # Row tops: 5.1=80, 5.2=320, 5.3=560, 5.4=800
    S += proc("p51", "5.1", "Historical Transaction Data Retrieval",      580, 80)
    S += proc("p52", "5.2", "Peak Hour Polynomial Regression & Insight",  580, 320)
    S += proc("p53", "5.3", "Ghost Slot Pattern Detection & Machine Recommendation", 580, 560)
    S += proc("p54", "5.4", "Prediction Audit Logging & Manager Dashboard Output",   580, 800)

    # ── EXTERNAL ENTITY ───────────────────────────────────────────────────────
    # Manager receives the final forecast + report
    S.append(ent("e_mgr", "Manager", 50, 840, w=160, h=80))
    # Super Admin oversees the audit trail and prediction logs
    S.append(ent("e_admin", "Super Admin", 50, 960, w=160, h=80))

    # ── GLOBAL DATA STORES ────────────────────────────────────────────────────
    # tbl_transaction    — top-right (read by 5.1 + 5.4)
    S += store("s_trx", "tbl_transaction",    1200, 80,  sw=240)
    # tbl_machine_status — mid-right (read by 5.3 for machine selection)
    S += store("s_mac", "tbl_machine_status", 1200, 330, sw=240)
    # tbl_queue          — lower-mid-right (read by 5.3 for queue depth/EWT)
    S += store("s_que", "tbl_queue",          1200, 580, sw=240)

    # ── LOCAL DATA STORE ──────────────────────────────────────────────────────
    # tbl_prediction_logs — used ONLY within process 5.0 for audit logging
    # (Local store introduced at Level 2; written and read by 5.4 only)
    S += store("s_log", "tbl_prediction_logs", 1200, 810, sw=240)

    # ─────────────────────────────────────────────────────────────────────────
    # DATA FLOWS
    # ─────────────────────────────────────────────────────────────────────────

    # ── 5.1 Historical Transaction Data Retrieval ─────────────────────────────

    # 1. tbl_transaction → 5.1: All Transaction Records
    #    (created_at, transaction_id, customer_name, weight_kg, cycle_type)
    E.append(ex("e1", "All Transaction Records",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.5},
                "s_trx_n", "p51b"))

    # 2. 5.1 → 5.2: Hourly Footfall Aggregate
    #    (DataFrame: hour vs footfall count, operational_hours 8–20,
    #     chart_labels, X & y arrays for polyfit)
    E.append(ex("e2", "Hourly Footfall Aggregate",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p51b", "p52b"))

    # 3. 5.1 → 5.3: Customer Visit Patterns
    #    (per customer_name: list of (hour, weight_kg, cycle_type, day_of_week)
    #     visits, filtered to >= min_visits)
    E.append(ex("e3", "Customer Visit Patterns",
                {"exitX": 0, "exitY": 0.8, "entryX": 0, "entryY": 0.2},
                "p51b", "p53b",
                [(450, 148), (450, 578)]))

    # ── 5.2 Peak Hour Polynomial Regression & Insight ─────────────────────────

    # 4. 5.2 → 5.4: Forecast Result
    #    (predicted_peak str, mape float, insight str,
    #     chart_labels list, chart_data list, historical_data list)
    E.append(ex("e4", "Forecast Result",
                {"exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0},
                "p52b", "p54b",
                [(715, 408), (715, 600), (715, 800)]))

    # ── 5.3 Ghost Slot Pattern Detection & Machine Recommendation ─────────────

    # 5. tbl_machine_status → 5.3: Machine Fleet & Availability
    #    (machine_type, operational_state, capacity_kg, machine_name,
    #     usage_count for scoring)
    E.append(ex("e5", "Machine Fleet & Availability",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.3},
                "s_mac_n", "p53b"))

    # 6. tbl_queue → 5.3: Queue Depth per Machine
    #    (count of Waiting entries + EWT per machine for recommendation scoring)
    E.append(ex("e6", "Queue Depth per Machine",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.7},
                "s_que_n", "p53b"))

    # 7. 5.3 → Manager: Ghost Slot Recommendations
    #    (customer_name, usual_time, recommended_machine_name, wait_mins,
    #     queue_count, recommendation_text — top 10 repeat customers)
    E.append(ex("e7", "Ghost Slot Recommendations",
                {"exitX": 0, "exitY": 0.5, "entryX": 1, "entryY": 0.3},
                "p53b", "e_mgr",
                [(460, 618), (460, 858)]))

    # ── 5.4 Prediction Audit Logging & Manager Dashboard Output ───────────────

    # 8. 5.4 → tbl_prediction_logs: Audit Log Entry
    #    (prediction_target='Peak_Demand_Hour', predicted_value,
    #     actual_value=historical peak hour, mape_score — only when record_log=True)
    E.append(ex("e8", "Audit Log Entry",
                {"exitX": 1, "exitY": 0.4, "entryX": 0, "entryY": 0.4},
                "p54b", "s_log_n"))

    # 9. tbl_prediction_logs → 5.4: Prediction History
    #    (last 10 PredictionLog rows for audit table on manager dashboard)
    E.append(ex("e9", "Prediction History",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.6},
                "s_log_n", "p54b"))

    # 10. tbl_transaction → 5.4: Sales Data for Revenue Tally
    #     (created_at, total_amount, payment_status, weight_kg —
    #      aggregated by day/week/month for the sales tally report)
    E.append(ex("e10", "Sales Data for Revenue Tally",
                {"exitX": 0, "exitY": 0.8, "entryX": 1, "entryY": 0.3},
                "s_trx_n", "p54b",
                [(1140, 102), (1140, 824)]))

    # 11. 5.4 → Manager: Peak Demand Forecast & Audit Logs
    #     (predicted_peak, mape, insight, chart_labels, chart_data,
    #      historical_data, last 10 prediction audit log entries)
    E.append(ex("e11", "Peak Demand Forecast & Audit Logs",
                {"exitX": 0, "exitY": 0.4, "entryX": 1, "entryY": 0.6},
                "p54b", "e_mgr",
                [(470, 832), (470, 888)]))

    # 12. 5.4 → Manager: Sales Tally Report
    #     (daily gross/paid/unpaid, avg ticket, tx_count, weight_kg;
    #      weekly/monthly/all-time aggregates; CSV export available)
    E.append(ex("e12", "Sales Tally Report",
                {"exitX": 0, "exitY": 0.6, "entryX": 1, "entryY": 0.7},
                "p54b", "e_mgr",
                [(455, 848), (455, 898)]))

    # 13. 5.4 → Super Admin: Executive Audit Logs & Prediction History
    E.append(ex("e13", "Executive Audit Logs & Prediction History",
                {"exitX": 0, "exitY": 0.85, "entryX": 1, "entryY": 0.5},
                "p54b", "e_admin",
                [(380, 879), (380, 1000)]))

    # ── Render XML ────────────────────────────────────────────────────────────
    cells = "\n    ".join(S + E)
    dname = "Level 2 - Process 5: Analytics and Forecasting"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="app.diagrams.net" version="22.0.0">\n'
        f'  <diagram id="level2_process5_analytics" name="{_e(dname)}">\n'
        f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
        f'tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        f'pageScale="1" pageWidth="1800" pageHeight="1150" math="0" shadow="0">\n'
        '      <root>\n'
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f'        {cells}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )

    ET.fromstring(xml)   # validate
    OUT_FILE.write_text(xml, encoding="utf-8")
    print(f"SUCCESS: {OUT_FILE}")
    print(f"Shapes: {len(S)}, Edges: {len(E)}")


if __name__ == "__main__":
    generate()
