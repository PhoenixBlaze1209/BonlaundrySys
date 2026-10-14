# scratch/generate_dfd_svgs.py
"""
Generates high-definition, publication-ready SVG diagrams for Bon Laundry Station
conforming to Gane-Sarson / Yourdon DFD standards:
1. Level 0: System Overview / Context Diagram
2. Level 1: Process 2.0 (Appointment & Order Lifecycle)
3. Level 1: Process 3.0 (Process Sales & Transactions)
4. Level 1: Process 4.0 (Real-Time Operational Telemetry & Queue Progression)
5. Level 1: Process 5.0 (Generate Analytics, Forecasts & Ghost Slots)
"""

import os
from pathlib import Path

OUT_DIR = Path(r"c:\Users\genes\bon-laundry\docs\diagrams")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SVG_HEAD = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 __W__ __H__" width="__W__" height="__H__">
<defs>
  <style>
    .bg { fill: #FFFFFF; }
    .entity { fill: #FFFFFF; stroke: #000000; stroke-width: 1.5; rx: 0; }
    .entity-title { font-family: 'Helvetica', Arial, sans-serif; font-size: 13px; font-weight: 400; fill: #000000; text-anchor: middle; }
    
    .proc-outer { fill: #FFFFFF; stroke: #000000; stroke-width: 1.5; rx: 8; }
    .proc-hdr { fill: #FFFFFF; stroke: #000000; stroke-width: 1.5; }
    .proc-id { font-family: 'Helvetica', Arial, sans-serif; font-size: 12px; font-weight: 400; fill: #000000; text-anchor: middle; }
    .proc-label { font-family: 'Helvetica', Arial, sans-serif; font-size: 12px; font-weight: 400; fill: #000000; text-anchor: middle; }
    
    .store-outer { fill: #FFFFFF; stroke: #000000; stroke-width: 1.5; }
    .store-id-box { fill: #FFFFFF; stroke: #000000; stroke-width: 1.5; }
    .store-id { font-family: 'Helvetica', Arial, sans-serif; font-size: 12px; font-weight: 400; fill: #000000; text-anchor: middle; }
    .store-name { font-family: 'Helvetica', Arial, sans-serif; font-size: 12px; font-weight: 400; fill: #000000; text-anchor: middle; }
    
    .flow { stroke: #000000; stroke-width: 1.2; fill: none; }
    .flow-highlight { stroke: #000000; stroke-width: 1.2; fill: none; }
    .flow-label { font-family: 'Helvetica', Arial, sans-serif; font-size: 11px; font-weight: 400; fill: #000000; text-anchor: middle; }
    .flow-bg { fill: #FFFFFF; opacity: 1; }
    
    .diagram-title { font-family: 'Helvetica', Arial, sans-serif; font-size: 18px; font-weight: 700; fill: #000000; }
    .diagram-subtitle { font-family: 'Helvetica', Arial, sans-serif; font-size: 12px; font-weight: 400; fill: #555555; }
  </style>
  
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
  </marker>
  
  <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
  </marker>

  <marker id="arrow-rev" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 8 1.5 L 0 5 L 8 8.5 z" fill="#000000"/>
  </marker>
</defs>
<rect width="__W__" height="__H__" class="bg"/>
"""

def get_svg_head(w, h):
    return SVG_HEAD.replace("__W__", str(w)).replace("__H__", str(h))

import html

def make_entity(x, y, w, h, title):
    lines = title.split("\n")
    if len(lines) > 1:
        tspans = "".join([f'<tspan x="{w/2}" dy="{16 if i > 0 else 0}">{html.escape(l)}</tspan>' for i, l in enumerate(lines)])
        start_y = h/2 - (len(lines)-1)*8 + 4
        text_node = f'<text x="{w/2}" y="{start_y}" class="entity-title">{tspans}</text>'
    else:
        text_node = f'<text x="{w/2}" y="{h/2 + 5}" class="entity-title">{html.escape(title)}</text>'
    return f"""
    <g transform="translate({x},{y})">
      <rect width="{w}" height="{h}" class="entity"/>
      {text_node}
    </g>"""

def make_process(x, y, w, h, pid, lines):
    hdr_h = 24
    line_svg = ""
    start_y = hdr_h + (h - hdr_h)/2 - (len(lines)-1)*8 + 4
    for i, line in enumerate(lines):
        line_svg += f'<text x="{w/2}" y="{start_y + i*16}" class="proc-label">{html.escape(line)}</text>'
    
    return f"""
    <g transform="translate({x},{y})">
      <rect width="{w}" height="{h}" class="proc-outer"/>
      <line x1="0" y1="{hdr_h}" x2="{w}" y2="{hdr_h}" stroke="#000000" stroke-width="1.5"/>
      <text x="{w/2}" y="16.5" class="proc-id">{html.escape(pid)}</text>
      {line_svg}
    </g>"""

def make_store(x, y, w, h, sid, sname):
    id_w = 34
    return f"""
    <g transform="translate({x},{y})">
      <rect width="{w}" height="{h}" class="store-outer"/>
      <line x1="{id_w}" y1="0" x2="{id_w}" y2="{h}" stroke="#000000" stroke-width="1.5"/>
      <text x="{id_w/2}" y="{h/2 + 4.5}" class="store-id">{html.escape(sid)}</text>
      <text x="{id_w + (w - id_w)/2}" y="{h/2 + 4.5}" class="store-name">{html.escape(sname)}</text>
    </g>"""

def make_path(points, label="", label_pos=None, label_w=140, label_h=18, highlight=False, marker="arrow", start_marker=None):
    d = f"M {points[0][0]} {points[0][1]}"
    for p in points[1:]:
        d += f" L {p[0]} {p[1]}"
    
    marker_attr = f'marker-end="url(#{marker})"' if marker else ""
    start_attr = f'marker-start="url(#{start_marker})"' if start_marker else ""
    cls = "flow-highlight" if highlight else "flow"
    
    res = f'<path d="{d}" class="{cls}" {marker_attr} {start_attr}/>'
    if label and label_pos:
        lx, ly = label_pos
        res += f"""
        <g transform="translate({lx},{ly})">
          <rect x="{-label_w/2}" y="{-label_h/2}" width="{label_w}" height="{label_h}" class="flow-bg"/>
          <text x="0" y="4" class="flow-label">{html.escape(label)}</text>
        </g>"""
    return res

def make_header(title, subtitle, w):
    return f"""
    <text x="40" y="42" class="diagram-title">{html.escape(title)}</text>
    <text x="40" y="62" class="diagram-subtitle">{html.escape(subtitle)}</text>
    <line x1="40" y1="74" x2="{w - 40}" y2="74" stroke="#CCCCCC" stroke-width="1"/>
    """


# ==============================================================================
# 1. DIAGRAM 1: Level 1 DFD for 5.0 (Generate Analytics & Forecasts)
# ==============================================================================
def gen_dfd_5():
    w, h = 1000, 1150
    svg = get_svg_head(w, h)
    svg += make_header(
        "Level 1 DFD: 5.0 Generate Analytics & Forecasts",
        "Updated System Architecture • Bon Laundry Station (Corrected Inverted Stores, 5.4 Numbering & Ghost Slots)",
        w
    )
    
    # Processes (Left Column)
    p_x, p_w, p_h = 70, 220, 85
    svg += make_process(p_x, 110, p_w, p_h, "5.1", ["Data Ingestion &", "Extraction Pipeline"])
    svg += make_process(p_x, 320, p_w, p_h, "5.2", ["Predictive Analytics &", "Peak Demand Engine"])
    svg += make_process(p_x, 540, p_w, p_h, "5.3", ["Operational Insights &", "Visualization Module"])
    svg += make_process(p_x, 750, p_w, p_h, "5.4", ["Financial Reconciliation", "& Sales Tally Generator"])
    svg += make_process(p_x, 960, p_w, p_h, "5.5", ["Ghost Slots & Habitual", "Pattern Discovery Engine"])

    # Data Stores (Right Column)
    s_x, s_w, s_h = 580, 210, 48
    svg += make_store(s_x, 110, s_w, s_h, "d1", "tbl_transaction")
    svg += make_store(s_x, 180, s_w, s_h, "d1", "tbl_queue")
    svg += make_store(s_x, 320, s_w, s_h, "d1", "tbl_machine_status")
    svg += make_store(s_x, 430, s_w, s_h, "d1", "tbl_prediction_logs")
    svg += make_store(s_x, 960, s_w, s_h, "d1", "tbl_users")

    # External Entity: Manager (Far Right)
    svg += make_entity(820, 550, 140, 70, "Manager")

    # Connectors & Flows:
    # 5.1 Inputs from Stores (FIXED from legacy diagram where arrows were inverted)
    svg += make_path([[s_x, 134], [p_x + p_w, 134]], "Transaction Logs & Revenue Data", [430, 124], label_w=190)
    svg += make_path([[s_x, 204], [400, 204], [400, 160], [p_x + p_w, 160]], "Queue Waiting & Volume Logs", [485, 194], label_w=170)

    # 5.1 to 5.2
    svg += make_path([[p_x + p_w//2, 195], [p_x + p_w//2, 320]], "Hourly Footfall Data", [p_x + p_w//2 + 75, 255], label_w=130)

    # 5.2 to Stores & 5.3
    svg += make_path([[s_x, 344], [p_x + p_w, 344]], "Machine Utilization Rates", [435, 334], label_w=150)
    svg += make_path([[p_x + p_w, 375], [510, 375], [510, 445], [s_x, 445]], "Log MAPE Score & Predictions", [540, 410], label_w=170)
    svg += make_path([[p_x + p_w//2, 405], [p_x + p_w//2, 540]], "Predicted Peak Hour & Regression Data", [p_x + p_w//2 + 115, 475], label_w=220)

    # 5.3 to Manager & Store
    svg += make_path([[s_x, 465], [450, 465], [450, 565], [p_x + p_w, 565]], "Audit Trail & Historical MAPE", [460, 515], label_w=170)
    svg += make_path([[p_x + p_w, 585], [820, 585]], "Peak Hour Charts & Operational Insights", [555, 575], label_w=230)

    # 5.4 Inputs & Outputs (Fixed numbering 4.4 -> 5.4)
    svg += make_path([[s_x + s_w, 134], [940, 134], [940, 775], [p_x + p_w, 775]], "Historical Sales & Payment Data", [750, 765], label_w=190)
    svg += make_path([[p_x + p_w, 805], [890, 805], [890, 620]], "Daily Sales Tally & CSV Reports", [620, 795], label_w=180)

    # 5.5 Ghost Slots (NEW FEATURE)
    svg += make_path([[s_x, 984], [p_x + p_w, 984]], "Customer Habits & History", [435, 974], label_w=160)
    svg += make_path([[s_x + s_w, 344], [800, 344], [800, 970], [p_x + p_w, 970]], "Fleet Capacity & Real-Time Availability", [620, 958], label_w=230)
    svg += make_path([[p_x + p_w, 1015], [860, 1015], [860, 620]], "Ghost Slot Recommendations", [600, 1005], label_w=180)
    svg += make_path([[860, 620], [860, 1035], [520, 1035], [520, 214], [s_x, 214]], "Ghost Slot Auto-Queue Entry", [520, 1025], label_w=170)

    svg += "</svg>"
    (OUT_DIR / "dfd_level_1_process_5_analytics_forecasts.svg").write_text(svg, encoding="utf-8")
    print("Saved dfd_level_1_process_5_analytics_forecasts.svg")


# ==============================================================================
# 2. DIAGRAM 2: Level 1 DFD for 4.0 (Real-Time Operational Status & Fleet)
# ==============================================================================
def gen_dfd_4():
    w, h = 1000, 1100
    svg = get_svg_head(w, h)
    svg += make_header(
        "Level 1 DFD: 4.0 Real-Time Operational Status & Machine Telemetry",
        "Updated Fleet Telemetry (19 Machines: 14 Washers, 5 Dryers) • Dynamic EWT • Auto-Progression",
        w
    )

    # Entities
    svg += make_entity(70, 120, 140, 70, "Staff")
    svg += make_entity(790, 560, 150, 70, "Customer")
    svg += make_entity(790, 940, 150, 70, "SMS & Email\nGateways")

    # Processes
    p_x, p_w, p_h = 360, 230, 85
    svg += make_process(p_x, 110, p_w, p_h, "4.1", ["Queue Entry & Fleet", "Allocation Dispatcher"])
    svg += make_process(p_x, 340, p_w, p_h, "4.2", ["Dynamic Machine-Specific", "Wait-Time Calculation (EWT)"])
    svg += make_process(p_x, 570, p_w, p_h, "4.3", ["Real-Time Machine Telemetry", "& Fleet Monitoring"])
    svg += make_process(p_x, 830, p_w, p_h, "4.4", ["Automated Cycle Completion", "& Queue Progression Engine"])

    # Stores
    s_x, s_w, s_h = 750, 200, 48
    svg += make_store(s_x, 110, s_w, s_h, "d1", "tbl_queue")
    svg += make_store(s_x, 210, s_w, s_h, "d1", "tbl_machine_status")
    svg += make_store(s_x, 310, s_w, s_h, "d1", "tbl_appointment")

    # Connectors 4.1
    svg += make_path([[210, 135], [p_x, 135]], "Queue Intake Request", [285, 125], label_w=130)
    svg += make_path([[p_x, 165], [210, 165]], "Assigned Queue Ticket", [285, 155], label_w=140)
    svg += make_path([[p_x + p_w, 135], [s_x, 135]], "New Queue Ticket & Priority", [670, 125], label_w=160)
    svg += make_path([[s_x, 225], [630, 225], [630, 165], [p_x + p_w, 165]], "Machine Capacity (8kg/13kg)", [675, 215], label_w=170)
    svg += make_path([[s_x, 325], [610, 325], [610, 185], [p_x + p_w, 185]], "Online Booking Data", [675, 315], label_w=130)

    # 4.1 to 4.2
    svg += make_path([[p_x + p_w//2, 195], [p_x + p_w//2, 340]], "Active Queue Sequence", [p_x + p_w//2 + 80, 265], label_w=140)

    # Connectors 4.2
    svg += make_path([[s_x, 240], [660, 240], [660, 360], [p_x + p_w, 360]], "Cycle Ends At & Timer Data", [680, 350], label_w=170)
    svg += make_path([[p_x + p_w, 390], [790, 390], [790, 560]], "Machine-Specific EWT", [715, 380], label_w=140)
    svg += make_path([[p_x, 365], [140, 365], [140, 190]], "Shop Estimated Wait Time", [240, 355], label_w=150)
    svg += make_path([[p_x + p_w, 375], [670, 375], [670, 155], [s_x, 155]], "Update Calculated EWT", [670, 280], label_w=140)

    # 4.2 to 4.3
    svg += make_path([[p_x + p_w//2, 425], [p_x + p_w//2, 570]], "Queue Wait Metrics", [p_x + p_w//2 + 70, 495], label_w=120)

    # Connectors 4.3
    svg += make_path([[p_x + p_w, 590], [790, 590]], "Live Lobby Status & Telemetry", [690, 580], label_w=175)
    svg += make_path([[p_x, 590], [120, 590], [120, 190]], "Machine Operational State", [230, 580], label_w=160)
    svg += make_path([[s_x + s_w//2, 258], [s_x + s_w//2, 500], [530, 500], [530, 570]], "19-Machine State Refresh", [640, 490], label_w=160)

    # 4.3 to 4.4
    svg += make_path([[p_x + p_w//2, 655], [p_x + p_w//2, 830]], "Running Cycle State", [p_x + p_w//2 + 70, 740], label_w=130)

    # Connectors 4.4
    svg += make_path([[p_x, 860], [100, 860], [100, 190]], "Cycle Finished Alert / Advance", [220, 850], label_w=170)
    svg += make_path([[p_x + p_w, 850], [720, 850], [720, 250], [s_x, 250]], "Reset Machine to Available", [720, 680], label_w=160)
    svg += make_path([[p_x + p_w, 870], [740, 870], [740, 150], [s_x, 150]], "Auto-Start Next Queued Job", [740, 710], label_w=170)
    svg += make_path([[p_x + p_w, 890], [790, 890], [790, 630]], "Order Ready / Delivery Update", [720, 880], label_w=175)
    svg += make_path([[p_x + p_w, 955], [790, 955]], "Ready Notification Dispatch", [690, 945], label_w=165)

    svg += "</svg>"
    (OUT_DIR / "dfd_level_1_process_4_operational_status.svg").write_text(svg, encoding="utf-8")
    print("Saved dfd_level_1_process_4_operational_status.svg")


# ==============================================================================
# 3. DIAGRAM 3: Level 1 DFD for 3.0 (Process Sales & Transactions)
# ==============================================================================
def gen_dfd_3():
    w, h = 1050, 1150
    svg = get_svg_head(w, h)
    svg += make_header(
        "Level 1 DFD: 3.0 Process Sales & Transactions",
        "Updated Rate Cards • Multi-Tier Add-ons • PayMongo Online Gateway & Counter POS • Dual Verification",
        w
    )

    # External Entities
    svg += make_entity(60, 120, 140, 70, "Staff")
    svg += make_entity(840, 120, 150, 70, "Customer")
    svg += make_entity(840, 880, 150, 70, "PayMongo\nPayment Gateway")
    svg += make_entity(60, 880, 140, 70, "Email Service\n(SMTP)")

    # Processes
    p_x, p_w, p_h = 390, 240, 85
    svg += make_process(p_x, 110, p_w, p_h, "3.1", ["Load Capacity & Service", "Package Validation"])
    svg += make_process(p_x, 340, p_w, p_h, "3.2", ["Multi-Tier Rate &", "Add-On Fee Calculation"])
    svg += make_process(p_x, 570, p_w, p_h, "3.3", ["Machine Fleet Allocation", "& Queue Dispatching"])
    svg += make_process(p_x, 820, p_w, p_h, "3.4", ["Payment Processing &", "Digital Receipt Settlement"])

    # Stores
    s_x, s_w, s_h = 750, 200, 48
    svg += make_store(70, 360, s_w, s_h, "d1", "tbl_system_settings")
    svg += make_store(760, 360, s_w, s_h, "d1", "tbl_machine_status")
    svg += make_store(70, 590, s_w, s_h, "d1", "tbl_queue")
    svg += make_store(760, 590, s_w, s_h, "d1", "tbl_transaction")

    # Connectors 3.1
    svg += make_path([[200, 145], [p_x, 145]], "Load Weight & Package", [295, 135], label_w=140)
    svg += make_path([[p_x, 175], [200, 175]], "Validation Status", [295, 165], label_w=110)
    svg += make_path([[840, 145], [p_x + p_w, 145]], "Drop-Off / Self Service Request", [735, 135], label_w=180)

    # 3.1 to 3.2
    svg += make_path([[p_x + p_w//2, 195], [p_x + p_w//2, 340]], "Validated Weight & Capacity", [p_x + p_w//2 + 95, 265], label_w=165)

    # Connectors 3.2
    svg += make_path([[270, 384], [p_x, 384]], "Price Rates & Service Rules", [330, 374], label_w=160)
    svg += make_path([[p_x, 405], [130, 405], [130, 190]], "Calculated Service Fee Breakdown", [250, 420], label_w=195)
    svg += make_path([[p_x + p_w, 384], [760, 384]], "Capacity Check (8kg / 13kg)", [685, 374], label_w=165)

    # 3.2 to 3.3
    svg += make_path([[p_x + p_w//2, 425], [p_x + p_w//2, 570]], "Final Price & Service Details", [p_x + p_w//2 + 90, 495], label_w=160)

    # Connectors 3.3
    svg += make_path([[760, 400], [670, 400], [670, 585], [p_x + p_w, 585]], "Machine Availability & State", [670, 490], label_w=170)
    svg += make_path([[p_x, 610], [270, 610]], "Write Queue Entry & SLA", [330, 600], label_w=160)
    svg += make_path([[p_x + p_w, 610], [720, 610], [720, 405], [760, 405]], "Trigger Machine Cycle Start", [720, 510], label_w=160)

    # 3.3 to 3.4
    svg += make_path([[p_x + p_w//2, 655], [p_x + p_w//2, 820]], "Queue & Assignment Record", [p_x + p_w//2 + 90, 735], label_w=165)

    # Connectors 3.4
    # Counter Payment
    svg += make_path([[110, 190], [110, 840], [p_x, 840]], "Counter Cash Payment Details", [250, 830], label_w=175)
    # Online Payment (PayMongo)
    svg += make_path([[840, 180], [870, 180], [870, 825], [p_x + p_w, 825]], "PayMongo Checkout Selection", [730, 815], label_w=185)
    svg += make_path([[p_x + p_w, 850], [760, 850], [760, 895], [840, 895]], "Create Checkout Session", [795, 875], label_w=150)
    svg += make_path([[840, 925], [740, 925], [740, 875], [p_x + p_w, 875]], "Webhook / Payment Paid", [770, 940], label_w=155)

    # 3.4 to Stores & Outputs
    svg += make_path([[p_x + p_w, 630], [760, 630]], "Record Transaction (tbl_transaction)", [685, 645], label_w=200)
    svg += make_path([[p_x, 630], [270, 630]], "Update Queue Payment = Paid", [330, 645], label_w=180)
    svg += make_path([[p_x, 875], [200, 875]], "Dispatch Email Receipt", [295, 865], label_w=145)
    svg += make_path([[p_x + p_w, 895], [910, 895], [910, 190]], "Digital Receipt & Order Code", [720, 710], label_w=175)

    svg += "</svg>"
    (OUT_DIR / "dfd_level_1_process_3_sales_pos.svg").write_text(svg, encoding="utf-8")
    print("Saved dfd_level_1_process_3_sales_pos.svg")


# ==============================================================================
# 4. DIAGRAM 4: Level 1 DFD for 2.0 (Appointment & Order Intake)
# ==============================================================================
def gen_dfd_2():
    w, h = 1050, 1200
    svg = get_svg_head(w, h)
    svg += make_header(
        "Level 1 DFD: 2.0 Appointment & Order Intake",
        "Deca Homes Logistics • Unique Order Tracking (ORD-XXXXX) • 2-Channel Secure OTP Cancellation",
        w
    )

    # Entities
    svg += make_entity(70, 120, 150, 70, "Customer\n(Web & Bot)")
    svg += make_entity(830, 120, 140, 70, "Staff")
    svg += make_entity(830, 700, 140, 70, "SMS & Email\nGateways")

    # Processes (Stacked)
    p_x, p_w, p_h = 390, 240, 85
    svg += make_process(p_x, 110, p_w, p_h, "2.1", ["Slot & Fleet Availability", "Check Engine"])
    svg += make_process(p_x, 300, p_w, p_h, "2.2", ["Booking & Deca Homes", "Logistics Validation"])
    svg += make_process(p_x, 490, p_w, p_h, "2.3", ["Order Creation & Queue", "Dispatching Module"])
    svg += make_process(p_x, 680, p_w, p_h, "2.4", ["Confirmation Issuance &", "Multi-Channel Dispatch"])
    svg += make_process(p_x, 870, p_w, p_h, "2.5", ["Live Order Tracking &", "Status Inquiry Engine"])
    svg += make_process(p_x, 1050, p_w, p_h, "2.6", ["Self-Service Cancellation", "with 2-Channel OTP"])

    # Stores (Side Placements)
    s_w, s_h = 200, 48
    svg += make_store(70, 310, s_w, s_h, "d1", "tbl_appointment")
    svg += make_store(780, 310, s_w, s_h, "d1", "tbl_machine_status")
    svg += make_store(70, 500, s_w, s_h, "d1", "tbl_queue")

    # Connectors 2.1
    svg += make_path([[220, 135], [p_x, 135]], "Slot / Lobby Availability Inquiry", [305, 125], label_w=180)
    svg += make_path([[p_x, 165], [220, 165]], "Available Slots & Traffic Status", [305, 155], label_w=175)
    svg += make_path([[p_x + p_w, 150], [780, 150], [780, 310]], "Machine Capacity & State", [720, 140], label_w=160)
    svg += make_path([[170, 310], [170, 185], [p_x, 185]], "Existing Schedule Slots", [270, 195], label_w=145)

    # 2.1 to 2.2
    svg += make_path([[p_x + p_w//2, 195], [p_x + p_w//2, 300]], "Validated Time Windows", [p_x + p_w//2 + 80, 245], label_w=140)

    # Connectors 2.2
    svg += make_path([[190, 190], [190, 325], [p_x, 325]], "Booking Request & Deca Bldg/Unit", [290, 315], label_w=185)
    svg += make_path([[p_x, 355], [210, 355], [210, 190]], "Validation Status & SLA Label", [285, 365], label_w=165)

    # 2.2 to 2.3
    svg += make_path([[p_x + p_w//2, 385], [p_x + p_w//2, 490]], "Approved Booking Payload", [p_x + p_w//2 + 85, 435], label_w=150)

    # Connectors 2.3
    svg += make_path([[p_x, 515], [270, 515]], "Create Order (ORD-XXXXX)", [330, 505], label_w=165)
    svg += make_path([[p_x, 545], [170, 545], [170, 548], [270, 548]], "Immediate Queue Reservation", [215, 570], label_w=170)
    svg += make_path([[p_x + p_w, 530], [830, 530], [830, 190]], "New Appointment Schedule Alert", [730, 520], label_w=190)

    # 2.3 to 2.4
    svg += make_path([[p_x + p_w//2, 575], [p_x + p_w//2, 680]], "Order Metadata & Code", [p_x + p_w//2 + 80, 625], label_w=140)

    # Connectors 2.4
    svg += make_path([[p_x, 705], [140, 705], [140, 190]], "Confirmation Details & Code", [245, 695], label_w=170)
    svg += make_path([[p_x + p_w, 725], [830, 725]], "Dispatch Confirmation Email", [735, 715], label_w=165)

    # 2.4 to 2.5
    svg += make_path([[p_x + p_w//2, 765], [p_x + p_w//2, 870]], "Active Tracking Record", [p_x + p_w//2 + 80, 815], label_w=140)

    # Connectors 2.5 (NEW: Tracking)
    svg += make_path([[110, 190], [110, 895], [p_x, 895]], "Tracking Query (Order Code / Phone)", [245, 885], label_w=200)
    svg += make_path([[p_x, 925], [90, 925], [90, 190]], "Live Multi-Stage Status (Placed/In-Wash/Ready)", [235, 940], label_w=235)
    svg += make_path([[270, 340], [330, 340], [330, 880], [p_x, 880]], "Fetch Order Details", [330, 620], label_w=120)

    # 2.5 to 2.6
    svg += make_path([[p_x + p_w//2, 955], [p_x + p_w//2, 1050]], "Order State Verification", [p_x + p_w//2 + 85, 1000], label_w=145)

    # Connectors 2.6 (NEW: OTP Cancellation)
    svg += make_path([[70, 190], [70, 1075], [p_x, 1075]], "Cancellation Request & OTP Submission", [225, 1065], label_w=215)
    svg += make_path([[p_x, 1105], [50, 1105], [50, 190]], "Cancellation Confirmation & Refund Notice", [215, 1120], label_w=230)
    svg += make_path([[p_x + p_w, 1075], [880, 1075], [880, 770]], "Send 6-Digit Verification OTP", [740, 1065], label_w=170)
    svg += make_path([[p_x, 1060], [310, 1060], [310, 350], [270, 350]], "Mark Cancelled & Pending Refund", [310, 720], label_w=195)
    svg += make_path([[p_x, 1085], [290, 1085], [290, 535], [270, 535]], "Release & Delete Waiting Queue Job", [290, 810], label_w=200)

    svg += "</svg>"
    (OUT_DIR / "dfd_level_1_process_2_appointment.svg").write_text(svg, encoding="utf-8")
    print("Saved dfd_level_1_process_2_appointment.svg")


# ==============================================================================
# 5. DIAGRAM 5: Level 0 DFD (System Overview - No Login, Zero Stacking)
# ==============================================================================
def gen_dfd_0():
    w, h = 1540, 1280
    svg = get_svg_head(w, h)
    svg += make_header(
        "Level 0 DFD: Bon Laundry Station Operating System Overview",
        "Spacious Layout • No Login Required (Public Booking Form) • Non-Overlapping Routing • Arc Intersections",
        w
    )

    # External Entities
    c_cust = (70, 230, 150, 90)
    c_staff = (1270, 230, 140, 90)
    c_mgr = (1270, 880, 140, 90)
    svg += make_entity(c_cust[0], c_cust[1], c_cust[2], c_cust[3], "Customer\n(Walk-in / Online Guest)")
    svg += make_entity(c_staff[0], c_staff[1], c_staff[2], c_staff[3], "Staff\n(Front Desk & Attendants)")
    svg += make_entity(c_mgr[0], c_mgr[1], c_mgr[2], c_mgr[3], "Manager\n(Store Administrator)")

    # Core System Processes (Center Column)
    p_x, p_w, p_h = 600, 280, 76
    svg += make_process(p_x, 100, p_w, p_h, "1.0", ["Appointment &", "Order Intake"])
    svg += make_process(p_x, 330, p_w, p_h, "2.0", ["Process Sales &", "Transactions"])
    svg += make_process(p_x, 560, p_w, p_h, "3.0", ["Real-time Operational", "Status"])
    svg += make_process(p_x, 800, p_w, p_h, "4.0", ["Generate Analytics &", "Forecasts"])
    svg += make_process(p_x, 1040, p_w, p_h, "5.0", ["Manage System", "Settings"])

    # Data Stores (Bilateral Distributed Layout)
    s_apt = (980, 115, 170, 46)
    s_trx = (980, 345, 170, 46)
    s_log = (980, 815, 170, 46)
    s_que = (310, 545, 170, 46)
    s_mac = (310, 675, 170, 46)
    s_set = (310, 1025, 170, 46)

    svg += make_store(s_apt[0], s_apt[1], s_apt[2], s_apt[3], "d1", "tbl_appointment")
    svg += make_store(s_trx[0], s_trx[1], s_trx[2], s_trx[3], "d1", "tbl_transaction")
    svg += make_store(s_log[0], s_log[1], s_log[2], s_log[3], "d1", "tbl_prediction_logs")
    svg += make_store(s_que[0], s_que[1], s_que[2], s_que[3], "d1", "tbl_queue")
    svg += make_store(s_mac[0], s_mac[1], s_mac[2], s_mac[3], "d1", "tbl_machine_status")
    svg += make_store(s_set[0], s_set[1], s_set[2], s_set[3], "d1", "tbl_system_settings")

    # Connectors & Flows - Zero Stacking, Dedicated Lanes
    # Process 1.0
    svg += make_path([[220, 252], [410, 252], [410, 119], [p_x, 119]], "Appointment Booking Details (Deca Address, Service)", [410, 185], label_w=280)
    svg += make_path([[p_x, 150], [370, 150], [370, 275], [220, 275]], "Available Slot Info & Order Confirmation", [330, 275], label_w=220)
    svg += make_path([[p_x + p_w, 138], [s_apt[0], 138]], "Appointment Entry & Order Code", [930, 126], label_w=180)
    svg += make_path([[p_x + int(p_w*0.9), 176], [p_x + int(p_w*0.9), 195], [1220, 195], [1220, 252], [1270, 252]], "Daily Appointment Schedule", [1050, 185], label_w=170)

    # Process 2.0
    svg += make_path([[220, 302], [420, 302], [420, 349], [p_x, 349]], "Payment Details (Cash / GCash via PayMongo)", [420, 325], label_w=250)
    svg += make_path([[p_x, 380], [360, 380], [360, 320], [190, 320]], "Digital Receipt & Payment Confirmation", [320, 360], label_w=230)
    svg += make_path([[p_x + p_w, 368], [s_trx[0], 368]], "Sales Record & Job Order Details", [930, 356], label_w=190)
    svg += make_path([[1270, 298], [1200, 298], [1200, 349], [p_x + p_w, 349]], "Load Information & Machine Assignment Data", [1080, 340], label_w=240)
    svg += make_path([[p_x + p_w, 390], [1170, 390], [1170, 275], [1270, 275]], "Service Fee Data & POS Transaction Summary", [1070, 399], label_w=240)
    svg += make_path([[p_x + int(p_w*0.65), 406], [1150, 406], [1150, 902], [1270, 902]], "Transaction Data & Revenue Logs", [1150, 650], label_w=190)

    # Process 3.0
    svg += make_path([[p_x, 490], [240, 490], [240, 320], [130, 320]], "Email / SMS Notifications, Queue Number & Live EWT", [380, 480], label_w=280)
    svg += make_path([[p_x, 590], [520, 590], [520, 568], [s_que[0] + s_que[2], 568]], "Queue Logs & Progression Status", [530, 558], label_w=180)
    svg += make_path([[p_x, 621], [510, 621], [510, 688], [s_mac[0] + s_mac[2], 688]], "Updated Machine Status Data", [510, 650], label_w=165)
    svg += make_path([[s_mac[0] + s_mac[2], 707], [550, 707], [550, 636], [p_x + int(p_w*0.15), 636]], "Machine Status Data & Cycle State", [555, 717], label_w=195)
    svg += make_path([[1340, 320], [1340, 460], [p_x + int(p_w*0.8), 460], [p_x + int(p_w*0.8), 560]], "Manual Machine Status Override", [1080, 450], label_w=180)
    svg += make_path([[p_x + p_w, 583], [1225, 583], [1225, 311], [1270, 311]], "Real-time Service Status Updates & Fleet EWT", [1100, 573], label_w=240)
    svg += make_path([[p_x + p_w, 621], [945, 621], [945, 829], [s_log[0], 829]], "Real-time EWT & Cycle Durations", [945, 725], label_w=185)
    svg += make_path([[p_x, 628], [180, 628], [180, 1039], [s_set[0], 1039]], "Machine ID & Fleet Configuration", [180, 830], label_w=185)

    # Process 4.0
    svg += make_path([[s_trx[0], 382], [915, 382], [915, 780], [p_x + int(p_w*0.85), 780], [p_x + int(p_w*0.85), 800]], "Historical Transaction Volume Data", [915, 580], label_w=195)
    svg += make_path([[s_mac[0] + int(s_mac[2]*0.8), 721], [446, 760], [540, 760], [540, 838], [p_x, 838]], "Real-time Machine Utilization Data", [490, 750], label_w=190)
    svg += make_path([[p_x + p_w, 838], [s_log[0], 838]], "EWT Prediction Data & MAPE Score", [930, 826], label_w=190)
    svg += make_path([[p_x + p_w, 865], [1180, 865], [1180, 925], [1270, 925]], "Peak Demand Forecasts, Operational Trends & Sales Analytics", [1050, 915], label_w=310)

    # Process 5.0
    svg += make_path([[1340, 970], [1340, 1078], [p_x + p_w, 1078]], "Configuration Data & System Parameters", [1150, 1068], label_w=225)
    svg += make_path([[p_x, 1078], [535, 1078], [535, 1048], [s_set[0] + s_set[2], 1048]], "Updated System Parameters & Rates", [535, 1038], label_w=195)
    svg += make_path([[s_set[0], 1057], [40, 1057], [40, 275], [70, 275]], "Service Rates & Turnaround Times", [40, 660], label_w=190)

    svg += "</svg>"
    (OUT_DIR / "dfd_level_0_system_overview.svg").write_text(svg, encoding="utf-8")
    print("Saved dfd_level_0_system_overview.svg")

if __name__ == "__main__":
    gen_dfd_5()
    gen_dfd_4()
    gen_dfd_3()
    gen_dfd_2()
    gen_dfd_0()
    print("All 5 DFD SVGs generated successfully.")
