# scratch/build_drawio_diagrams.py
"""
Generates native .drawio files conforming strictly to Capstone & Bon Laundry Station requirements:
1. Exact visual styling matching reference design:
   - Process headers: Light blue (#dae8fc, stroke #6c8ebf)
   - Process body: White (#ffffff, stroke #6c8ebf)
   - Entities: Light grey (#f5f5f5, stroke #666666)
   - Data Stores: Standard Gane & Sarson d1 split boxes
2. Strict "DONT STACK UP" Layout Rules:
   - Spacious canvas (1540 x 1280) with generous spacing between processes and columns.
   - Bilateral distributed data store architecture: every data store is immediately adjacent to writing process.
   - Zero crossing through data store boxes or entity boxes.
   - Dedicated routing channels for every connector line with minimum 30-80px clearance.
3. System Requirements:
   - NO LOGIN: Process 1.0 (User Account & Profile Management), tbl_users, and login credentials/authentication lines are completely removed.
   - Five core operational processes:
     1.0 Appointment & Order Intake
     2.0 Process Sales & Transactions
     3.0 Real-time Operational Status
     4.0 Generate Analytics & Forecasts
     5.0 Manage System Settings
   - Pure human entities: Customer (Guest/Public Form), Staff, Manager.
4. Arc Line Jumps:
   - jumpStyle=arc; jumpSize=6; on all orthogonal connectors so intersections render as clean arc bridges.
"""

import html
import urllib.parse
import zlib
import base64
from pathlib import Path

OUT_DIR = Path(r"c:\Users\genes\bon-laundry\docs\diagrams")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def compress_for_drawio(xml_str: str) -> str:
    """Standard Draw.io compression: URL-quote -> raw Deflate -> Base64"""
    quoted = urllib.parse.quote(xml_str, safe="~()*!.'")
    deflated = zlib.compress(quoted.encode('utf-8'), 9)[2:-4]
    return base64.b64encode(deflated).decode('utf-8')

def escape_xml_attr(s: str) -> str:
    """Escapes text for an XML attribute value, converting newlines to &lt;br&gt; for Draw.io HTML labels."""
    return html.escape(s, quote=True).replace("\n", "&lt;br&gt;")

class DrawIOBuilder:
    def __init__(self, page_w=1540, page_h=1280):
        self.page_w = page_w
        self.page_h = page_h
        self.cells = []
        self.cell_id = 2

    def next_id(self):
        self.cell_id += 1
        return str(self.cell_id)

    def add_entity(self, x, y, w, h, label):
        cid = self.next_id()
        esc = escape_xml_attr(label)
        # Reference image style: light grey fill #f5f5f5, border #666666
        style = "rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#000000;align=center;verticalAlign=middle;"
        self.cells.append(f'<mxCell id="{cid}" value="{esc}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" /></mxCell>')
        return cid

    def add_process(self, x, y, w, h, pid, name):
        cid_top = self.next_id()
        cid_bot = self.next_id()
        esc_top = escape_xml_attr(pid)
        esc_bot = escape_xml_attr(name)
        hdr_h = 24
        bot_h = h - hdr_h
        
        # Reference image style: header light blue #dae8fc border #6c8ebf, body white border #6c8ebf
        style_top = "rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#000000;align=center;verticalAlign=middle;"
        style_bot = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#6c8ebf;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=0;fontColor=#000000;align=center;verticalAlign=middle;"
        
        self.cells.append(f'<mxCell id="{cid_top}" value="{esc_top}" style="{style_top}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{hdr_h}" as="geometry" /></mxCell>')
        self.cells.append(f'<mxCell id="{cid_bot}" value="{esc_bot}" style="{style_bot}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y + hdr_h}" width="{w}" height="{bot_h}" as="geometry" /></mxCell>')
        return cid_bot

    def add_store(self, x, y, w, h, sid, sname):
        cid_id = self.next_id()
        cid_name = self.next_id()
        id_w = 34
        name_w = w - id_w
        
        style_id = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=0;align=center;verticalAlign=middle;"
        style_name = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;strokeWidth=1.5;fontFamily=Helvetica;fontSize=11;fontStyle=1;align=center;verticalAlign=middle;"
        
        self.cells.append(f'<mxCell id="{cid_id}" value="{escape_xml_attr(sid)}" style="{style_id}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{id_w}" height="{h}" as="geometry" /></mxCell>')
        self.cells.append(f'<mxCell id="{cid_name}" value="{escape_xml_attr(sname)}" style="{style_name}" vertex="1" parent="1"><mxGeometry x="{x + id_w}" y="{y}" width="{name_w}" height="{h}" as="geometry" /></mxCell>')
        return cid_name

    def add_edge(self, src_id, tgt_id, label="", exit_side=None, entry_side=None, waypoints=None, curved=False, label_pos=None):
        eid = self.next_id()
        esc = escape_xml_attr(label)
        
        if curved:
            style = "curved=1;endArrow=classic;endFill=1;html=1;strokeColor=#000000;strokeWidth=1.2;fontFamily=Helvetica;fontSize=10;fontColor=#000000;labelBackgroundColor=#ffffff;"
        else:
            style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.2;endArrow=classic;endFill=1;jumpStyle=arc;jumpSize=6;fontFamily=Helvetica;fontSize=10;fontColor=#000000;labelBackgroundColor=#ffffff;"
        
        if exit_side:
            style += f"exitX={exit_side[0]};exitY={exit_side[1]};exitDx=0;exitDy=0;"
        if entry_side:
            style += f"entryX={entry_side[0]};entryY={entry_side[1]};entryDx=0;entryDy=0;"
            
        pts_xml = ""
        if waypoints:
            pts_xml = '<Array as="points">' + ''.join([f'<mxPoint x="{px}" y="{py}" />' for px, py in waypoints]) + '</Array>'
            
        geom_extra = ""
        if label_pos:
            lx, ly = label_pos
            geom_extra = f' x="{lx}" y="{ly}"'
            
        self.cells.append(f'''<mxCell id="{eid}" value="{esc}" style="{style}" edge="1" parent="1" source="{src_id}" target="{tgt_id}">
          <mxGeometry{geom_extra} relative="1" as="geometry">{pts_xml}</mxGeometry>
        </mxCell>''')
        return eid

    def to_raw_model(self):
        body = "\n        ".join(self.cells)
        return f'''<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.page_w}" pageHeight="{self.page_h}" math="0" shadow="0" lineJumps="1">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    {body}
  </root>
</mxGraphModel>'''

    def to_diagram_xml(self, name, did, compress=False):
        raw_model = self.to_raw_model()
        if compress:
            compressed = compress_for_drawio(raw_model)
            return f'  <diagram id="{did}" name="{escape_xml_attr(name)}">{compressed}</diagram>'
        else:
            indented = "\n".join("    " + line for line in raw_model.split("\n"))
            return f'  <diagram id="{did}" name="{escape_xml_attr(name)}">\n{indented}\n  </diagram>'


# ==============================================================================
# 1. Level 0 - System Overview (Clean, Spacious, No Login, Zero Stacking)
# ==============================================================================
def build_level_0():
    b = DrawIOBuilder(1540, 1280)

    # 1. Central Processes Column (Width 280, Height 76, 5 Operational Processes - NO LOGIN)
    px, pw, ph = 600, 280, 76
    p1 = b.add_process(px, 100, pw, ph, "1.0", "Appointment & Order Intake")
    p2 = b.add_process(px, 330, pw, ph, "2.0", "Process Sales & Transactions")
    p3 = b.add_process(px, 560, pw, ph, "3.0", "Real-time Operational Status")
    p4 = b.add_process(px, 800, pw, ph, "4.0", "Generate Analytics & Forecasts")
    p5 = b.add_process(px, 1040, pw, ph, "5.0", "Manage System Settings")

    # 2. External Entities
    # Customer: left side adjacent to 1.0 and 2.0
    c_cust = b.add_entity(70, 230, 150, 90, "Customer\n(Walk-in / Online Guest)")
    # Staff: right side adjacent to 1.0, 2.0, and 3.0
    c_staff = b.add_entity(1270, 230, 140, 90, "Staff\n(Front Desk & Attendants)")
    # Manager: right side adjacent to 4.0 and 5.0
    c_mgr = b.add_entity(1270, 880, 140, 90, "Manager\n(Store Administrator)")

    # 3. Data Stores (Bilateral Distributed Layout - Placed right next to writing processes)
    # Right column stores:
    s_apt = b.add_store(980, 115, 170, 46, "d1", "tbl_appointment")
    s_trx = b.add_store(980, 345, 170, 46, "d1", "tbl_transaction")
    s_log = b.add_store(980, 815, 170, 46, "d1", "tbl_prediction_logs")

    # Left column stores:
    s_que = b.add_store(310, 545, 170, 46, "d1", "tbl_queue")
    s_mac = b.add_store(310, 675, 170, 46, "d1", "tbl_machine_status")
    s_set = b.add_store(310, 1025, 170, 46, "d1", "tbl_system_settings")

    # 4. Connectors - Every single lane has dedicated coordinates (ZERO STACKING, ARC JUMPS)

    # --- PROCESS 1.0 (Appointment & Order Intake) ---
    # Customer -> 1.0: Appointment Booking Form (x=410, y=119)
    b.add_edge(c_cust, p1, "Appointment Booking Details (Deca Address, Service)", 
               exit_side=(1, 0.25), entry_side=(0, 0.25), 
               waypoints=[(410, 252), (410, 119)],
               label_pos=(-0.2, 0))
    # 1.0 -> Customer: Available Slot & Booking Confirmation (x=370, y=150)
    b.add_edge(p1, c_cust, "Available Slot Info & Order Confirmation", 
               exit_side=(0, 0.65), entry_side=(1, 0.5), 
               waypoints=[(370, 150), (370, 275)],
               label_pos=(0.2, 0))
    # 1.0 -> tbl_appointment: Direct horizontal store flow (length 100px)
    b.add_edge(p1, s_apt, "Appointment Entry & Order Code", 
               exit_side=(1, 0.5), entry_side=(0, 0.5))
    # 1.0 -> Staff: Daily Appointment Schedule (Bypasses tbl_appointment at y=195, x=1220)
    b.add_edge(p1, c_staff, "Daily Appointment Schedule", 
               exit_side=(0.9, 1), entry_side=(0, 0.25), 
               waypoints=[(852, 195), (1220, 195), (1220, 252)])

    # --- PROCESS 2.0 (Process Sales & Transactions) ---
    # Customer -> 2.0: Payment Details (x=420, y=349)
    b.add_edge(c_cust, p2, "Payment Details (Cash / GCash via PayMongo)", 
               exit_side=(1, 0.8), entry_side=(0, 0.25), 
               waypoints=[(420, 302), (420, 349)])
    # 2.0 -> Customer: Digital Receipt Information (x=360, y=380)
    b.add_edge(p2, c_cust, "Digital Receipt & Payment Confirmation", 
               exit_side=(0, 0.65), entry_side=(0.8, 1), 
               waypoints=[(360, 380), (360, 320)])
    # 2.0 -> tbl_transaction: Direct horizontal store flow (length 100px)
    b.add_edge(p2, s_trx, "Sales Record & Job Order Details", 
               exit_side=(1, 0.5), entry_side=(0, 0.5))
    # Staff -> 2.0: Load Information & Machine Assignment (x=1200, y=349)
    b.add_edge(c_staff, p2, "Load Information & Machine Assignment Data", 
               exit_side=(0, 0.75), entry_side=(1, 0.25), 
               waypoints=[(1200, 298), (1200, 349)],
               label_pos=(-0.3, 0))
    # 2.0 -> Staff: Service Fee & POS Summary (x=1170, y=390)
    b.add_edge(p2, c_staff, "Service Fee Data & POS Transaction Summary", 
               exit_side=(1, 0.8), entry_side=(0, 0.5), 
               waypoints=[(1170, 390), (1170, 275)],
               label_pos=(0.3, 0))
    # 2.0 -> Manager: Transaction Data & Revenue Logs (x=1150 outer channel)
    b.add_edge(p2, c_mgr, "Transaction Data & Revenue Logs", 
               exit_side=(1, 0.65), entry_side=(0, 0.25), 
               waypoints=[(1150, 380), (1150, 902)])

    # --- PROCESS 3.0 (Real-time Operational Status) ---
    # 3.0 -> Customer: Clean channel at y=490 (above tbl_queue) and x=240 down to Customer bottom
    b.add_edge(p3, c_cust, "Email / SMS Notifications, Queue Number & Live EWT", 
               exit_side=(0, 0.2), entry_side=(0.4, 1), 
               waypoints=[(550, 490), (240, 490), (240, 320)])
    # 3.0 -> tbl_queue: Direct horizontal / clean step
    b.add_edge(p3, s_que, "Queue Logs & Progression Status", 
               exit_side=(0, 0.4), entry_side=(1, 0.5), 
               waypoints=[(520, 590), (520, 568)])
    # 3.0 -> tbl_machine_status
    b.add_edge(p3, s_mac, "Updated Machine Status Data", 
               exit_side=(0, 0.8), entry_side=(1, 0.3), 
               waypoints=[(510, 621), (510, 688)])
    # tbl_machine_status -> 3.0
    b.add_edge(s_mac, p3, "Machine Status Data & Cycle State", 
               exit_side=(1, 0.7), entry_side=(0.15, 1), 
               waypoints=[(550, 707), (550, 636)])
    # Staff -> 3.0: Status override
    b.add_edge(c_staff, p3, "Manual Machine Status Override", 
               exit_side=(0.5, 1), entry_side=(0.8, 0), 
               waypoints=[(1340, 460), (824, 460)])
    # 3.0 -> Staff: Fleet Telemetry (x=1225)
    b.add_edge(p3, c_staff, "Real-time Service Status Updates & Fleet EWT", 
               exit_side=(1, 0.3), entry_side=(0, 0.9), 
               waypoints=[(1225, 583), (1225, 311)])
    # 3.0 -> tbl_prediction_logs: EWT updates (x=945)
    b.add_edge(p3, s_log, "Real-time EWT & Cycle Durations", 
               exit_side=(1, 0.8), entry_side=(0, 0.3), 
               waypoints=[(945, 621), (945, 829)])
    # 3.0 -> tbl_system_settings: Machine ID (Outer left channel x=180)
    b.add_edge(p3, s_set, "Machine ID & Fleet Configuration", 
               exit_side=(0, 0.9), entry_side=(0, 0.3), 
               waypoints=[(540, 628), (180, 628), (180, 1039)])

    # --- PROCESS 4.0 (Generate Analytics & Forecasts) ---
    # tbl_transaction -> 4.0: Historical sales volume (x=915)
    b.add_edge(s_trx, p4, "Historical Transaction Volume Data", 
               exit_side=(0, 0.8), entry_side=(0.85, 0), 
               waypoints=[(915, 382), (915, 780), (838, 780)])
    # tbl_machine_status -> 4.0: Fleet utilization
    b.add_edge(s_mac, p4, "Real-time Machine Utilization Data", 
               exit_side=(0.8, 1), entry_side=(0, 0.5), 
               waypoints=[(446, 760), (540, 760), (540, 838)])
    # 4.0 -> tbl_prediction_logs: Direct horizontal store flow (length 100px)
    b.add_edge(p4, s_log, "EWT Prediction Data & MAPE Score", 
               exit_side=(1, 0.5), entry_side=(0, 0.5))
    # 4.0 -> Manager: Direct horizontal lane at y=925
    b.add_edge(p4, c_mgr, "Peak Demand Forecasts, Operational Trends & Sales Analytics", 
               exit_side=(1, 0.8), entry_side=(0, 0.5), 
               waypoints=[(880, 925), (1270, 925)])

    # --- PROCESS 5.0 (Manage System Settings) ---
    # Manager -> 5.0: Configuration updates
    b.add_edge(c_mgr, p5, "Configuration Data & System Parameters", 
               exit_side=(0.5, 1), entry_side=(1, 0.5), 
               waypoints=[(1340, 1078)])
    # 5.0 -> tbl_system_settings: Direct horizontal store flow
    b.add_edge(p5, s_set, "Updated System Parameters & Rates", 
               exit_side=(0, 0.5), entry_side=(1, 0.5), 
               waypoints=[(535, 1078), (535, 1048)])
    # tbl_system_settings -> Customer: Far-left outer margin channel (x=40)
    b.add_edge(s_set, c_cust, "Service Rates & Turnaround Times", 
               exit_side=(0, 0.7), entry_side=(0, 0.5), 
               waypoints=[(40, 1057), (40, 275)])

    return b, "Level 0 - System Overview", "page_lvl0"


# ==============================================================================
# 2. Level 1 - Process 1.0 (Appointment & Order Lifecycle)
# ==============================================================================
def build_level_2():
    b = DrawIOBuilder(1150, 1150)
    
    # Entities
    c_cust = b.add_entity(60, 140, 110, 50, "Customer\n(Guest Form)")
    c_staff = b.add_entity(960, 140, 110, 50, "Staff")

    px, pw, ph = 430, 240, 70
    p21 = b.add_process(px, 100, pw, ph, "1.1", "Slot Availability\nCheck Engine")
    p22 = b.add_process(px, 260, pw, ph, "1.2", "Booking Request &\nDeca Logistics Validation")
    p23 = b.add_process(px, 420, pw, ph, "1.3", "Appointment Storage &\nQueue Dispatch")
    p24 = b.add_process(px, 580, pw, ph, "1.4", "Confirmation Issuance &\nMulti-Channel Dispatch")
    p25 = b.add_process(px, 740, pw, ph, "1.5", "Guest Order Tracking &\nStatus Inquiry")
    p26 = b.add_process(px, 900, pw, ph, "1.6", "Self-Service Cancellation\nwith 2-Channel OTP")

    # Data Stores
    s_apt = b.add_store(80, 310, 160, 45, "d1", "tbl_appointment")
    s_mac = b.add_store(900, 310, 160, 45, "d1", "tbl_machine_status")
    s_que = b.add_store(80, 470, 160, 45, "d1", "tbl_queue")

    # Connectors
    b.add_edge(c_cust, p21, "Slot / Lobby Inquiry", exit_side=(1, 0.3), entry_side=(0, 0.3))
    b.add_edge(p21, c_cust, "Slot Availability & Traffic", exit_side=(0, 0.7), entry_side=(1, 0.7))
    b.add_edge(s_mac, p21, "Machine Fleet Status", exit_side=(0, 0.5), entry_side=(1, 0.6))
    b.add_edge(s_apt, p21, "Existing Bookings", exit_side=(0.8, 0), entry_side=(0, 0.8))
    b.add_edge(p21, p22, "Validated Time Window", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(c_cust, p22, "Appointment Details & Deca Unit", exit_side=(0.8, 1), entry_side=(0, 0.4), waypoints=[(140, 285)])
    b.add_edge(p22, c_cust, "Validation Result", exit_side=(0, 0.7), entry_side=(0.5, 1), waypoints=[(260, 305), (110, 305)])
    b.add_edge(p22, p23, "Approved Booking Payload", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(p23, s_apt, "Order Entry (ORD-XXXXX)", exit_side=(0, 0.3), entry_side=(1, 0.5))
    b.add_edge(p23, s_que, "Immediate Queue Reservation", exit_side=(0, 0.7), entry_side=(1, 0.5))
    b.add_edge(p23, c_staff, "Appointment Status Alert", exit_side=(1, 0.5), entry_side=(0, 0.5))
    b.add_edge(p23, p24, "Order Metadata & Code", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(p24, c_cust, "Booking Confirmation & Code", exit_side=(0, 0.5), entry_side=(0.2, 1), waypoints=[(240, 615), (80, 615)])
    b.add_edge(p24, p25, "Active Order Reference", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(c_cust, p25, "Tracking Query (Code/Phone)", exit_side=(0.1, 1), entry_side=(0, 0.3), waypoints=[(70, 760)])
    b.add_edge(p25, c_cust, "Live Status (Placed/In-Wash/Ready)", exit_side=(0, 0.7), entry_side=(0.3, 1), waypoints=[(250, 790), (90, 790)])
    b.add_edge(p25, p26, "Cancellation Guard Check", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(p26, c_cust, "Send 6-Digit OTP via SMS/Email", exit_side=(0, 0.3), entry_side=(0.05, 1), waypoints=[(220, 920), (50, 920)])
    b.add_edge(c_cust, p26, "Submit 6-Digit OTP Verification", exit_side=(0, 0.8), entry_side=(0, 0.7), waypoints=[(30, 950), (340, 950)])
    b.add_edge(p26, s_apt, "Mark Status = Cancelled", exit_side=(0, 0.6), entry_side=(0.2, 1), waypoints=[(280, 940), (280, 380), (120, 380)])
    b.add_edge(p26, s_que, "Release / Delete Waiting Queue", exit_side=(0, 0.8), entry_side=(0.2, 1), waypoints=[(300, 960), (300, 540), (120, 540)])
    
    return b, "Level 1 - 1.0 Appointment", "page_lvl1"


# ==============================================================================
# 3. Level 1 - Process 2.0 (Process Sales & Transactions)
# ==============================================================================
def build_level_3():
    b = DrawIOBuilder(1150, 1000)

    c_staff = b.add_entity(60, 100, 110, 50, "Staff")
    c_cust = b.add_entity(960, 100, 110, 50, "Customer")

    px, pw, ph = 430, 240, 70
    p31 = b.add_process(px, 100, pw, ph, "2.1", "Load Validation &\nWeight Check")
    p32 = b.add_process(px, 280, pw, ph, "2.2", "Multi-Tier Fee\nCalculation")
    p33 = b.add_process(px, 470, pw, ph, "2.3", "Machine & Queue\nAssignment")
    p34 = b.add_process(px, 670, pw, ph, "2.4", "Confirmation Issuance &\nPayment Processing")

    s_set = b.add_store(60, 290, 160, 45, "d1", "tbl_system_settings")
    s_mac = b.add_store(900, 290, 160, 45, "d1", "tbl_machine_status")
    s_que = b.add_store(60, 480, 160, 45, "d1", "tbl_queue")
    s_trx = b.add_store(900, 480, 160, 45, "d1", "tbl_transaction")

    b.add_edge(c_staff, p31, "Load Weight & Service", exit_side=(1, 0.3), entry_side=(0, 0.3))
    b.add_edge(p31, c_staff, "Validation Status", exit_side=(0, 0.7), entry_side=(1, 0.7))
    b.add_edge(c_cust, p31, "Self-Service / Drop-Off Choice", exit_side=(0, 0.5), entry_side=(1, 0.5))
    b.add_edge(p31, p32, "Validated Load Weight", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(s_set, p32, "Price Rates & Add-on Rules", exit_side=(1, 0.5), entry_side=(0, 0.4))
    b.add_edge(p32, c_staff, "Calculated Service Fee", exit_side=(0, 0.7), entry_side=(0.7, 1), waypoints=[(220, 330), (130, 330)])
    b.add_edge(s_mac, p32, "Capacity Rates (8kg/13kg)", exit_side=(0, 0.5), entry_side=(1, 0.5))
    b.add_edge(p32, p33, "Calculated Fee & Package", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(s_mac, p33, "Machine Availability Status", exit_side=(0.5, 1), entry_side=(1, 0.3), waypoints=[(980, 490)])
    b.add_edge(p33, s_que, "Queue Data & Turnaround SLA", exit_side=(0, 0.5), entry_side=(1, 0.5))
    b.add_edge(p33, s_mac, "Trigger Machine Cycle Start", exit_side=(1, 0.7), entry_side=(0.2, 1), waypoints=[(720, 520), (720, 360), (930, 360)])
    b.add_edge(p33, p34, "Assignment Details", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(c_staff, p34, "Counter Cash Payment Details", exit_side=(0.2, 1), entry_side=(0, 0.3), waypoints=[(80, 690)])
    b.add_edge(c_cust, p34, "PayMongo Checkout (GCash/Card)", exit_side=(0.8, 1), entry_side=(1, 0.3), waypoints=[(1040, 690)])
    b.add_edge(p34, s_trx, "Sales Record Data", exit_side=(1, 0.2), entry_side=(0.5, 1), waypoints=[(740, 680), (980, 680)])
    b.add_edge(p34, c_cust, "Payment Receipt & Token", exit_side=(1, 0.7), entry_side=(0.3, 1), waypoints=[(720, 720), (990, 720)])
    b.add_edge(p34, c_staff, "Cash Drawer Ledger Entry", exit_side=(0, 0.7), entry_side=(0.5, 1), waypoints=[(360, 720), (110, 720)])

    return b, "Level 1 - 2.0 Sales & POS", "page_lvl2"


# ==============================================================================
# 4. Level 1 - Process 3.0 (Real-Time Operational Status)
# ==============================================================================
def build_level_4():
    b = DrawIOBuilder(1150, 1050)

    c_staff = b.add_entity(60, 100, 110, 50, "Staff")
    c_cust = b.add_entity(960, 100, 110, 50, "Customer")

    px, pw, ph = 430, 240, 70
    p41 = b.add_process(px, 100, pw, ph, "3.1", "Fleet Telemetry &\nHardware Listener")
    p42 = b.add_process(px, 280, pw, ph, "3.2", "Dynamic Cycle &\nState Transition Engine")
    p43 = b.add_process(px, 470, pw, ph, "3.3", "Multi-Channel Notification\nDispatcher")
    p44 = b.add_process(px, 660, pw, ph, "3.4", "Live Machine Lobby &\nDisplay Kiosk Feed")
    p45 = b.add_process(px, 850, pw, ph, "3.5", "Queue Transition &\nMachine Release")

    s_mac = b.add_store(60, 290, 160, 45, "d1", "tbl_machine_status")
    s_que = b.add_store(900, 290, 160, 45, "d1", "tbl_queue")
    s_apt = b.add_store(60, 670, 160, 45, "d1", "tbl_appointment")
    s_log = b.add_store(900, 670, 160, 45, "d1", "tbl_prediction_logs")

    b.add_edge(c_staff, p41, "Physical Machine Cycle Start", exit_side=(1, 0.3), entry_side=(0, 0.3))
    b.add_edge(s_mac, p41, "Current Machine Running State", exit_side=(0.8, 0), entry_side=(0, 0.7))
    b.add_edge(p41, p42, "Raw Cycle Pulses & Active Timers", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(p42, s_mac, "Live Countdown (M1-M19)", exit_side=(0, 0.5), entry_side=(1, 0.5))
    b.add_edge(s_que, p42, "Active Queue Positions", exit_side=(0, 0.5), entry_side=(1, 0.5))
    b.add_edge(p42, s_log, "Record Wait-Time Actuals", exit_side=(1, 0.7), entry_side=(0.2, 0), waypoints=[(720, 330), (930, 330), (930, 670)])
    b.add_edge(p42, p43, "State Trigger (Done / Delayed)", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(p43, c_cust, "SMS / Email (Done / Pickup Ready)", exit_side=(1, 0.5), entry_side=(0.5, 1), waypoints=[(720, 505), (1010, 505)])
    b.add_edge(p43, c_staff, "Audible Alert / Audio Ping", exit_side=(0, 0.5), entry_side=(0.5, 1), waypoints=[(360, 505), (110, 505)])
    b.add_edge(p43, s_apt, "Update Fulfillment Status", exit_side=(0, 0.8), entry_side=(1, 0.3), waypoints=[(390, 526), (390, 680)])
    b.add_edge(p43, p44, "Lobby Refresh Signal", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(p44, c_cust, "Real-Time Lobby View (Free/In-Use)", exit_side=(1, 0.5), entry_side=(0.8, 1), waypoints=[(740, 695), (1040, 695)])
    b.add_edge(p44, p45, "Unload Confirmation", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(c_staff, p45, "Manual Unload / Basket Clearance", exit_side=(0.2, 1), entry_side=(0, 0.5), waypoints=[(80, 885)])
    b.add_edge(p45, s_mac, "Set State = Available", exit_side=(0, 0.3), entry_side=(0.2, 1), waypoints=[(360, 871), (360, 360), (100, 360)])
    b.add_edge(p45, s_que, "Promote Next Ticket to Active", exit_side=(1, 0.5), entry_side=(0.8, 1), waypoints=[(740, 885), (1030, 885)])

    return b, "Level 1 - 3.0 Operational Status", "page_lvl3"


# ==============================================================================
# 5. Level 1 - Process 4.0 (Generate Analytics & Forecasts)
# ==============================================================================
def build_level_5():
    b = DrawIOBuilder(1150, 1050)

    c_mgr = b.add_entity(960, 100, 110, 50, "Manager")

    px, pw, ph = 430, 240, 70
    p51 = b.add_process(px, 100, pw, ph, "4.1", "Sales & Volume Data\nIngestion Engine")
    p52 = b.add_process(px, 280, pw, ph, "4.2", "XGBoost & Holt-Winters\nPredictive Forecaster")
    p53 = b.add_process(px, 470, pw, ph, "4.3", "Peak Demand & Traffic\nVisualizer")
    p54 = b.add_process(px, 660, pw, ph, "4.4", "Revenue & Turnaround\nAnalytics Engine")
    p55 = b.add_process(px, 850, pw, ph, "4.5", "Ghost Slot Generation &\nCapacity Dispatcher")

    s_trx = b.add_store(60, 100, 160, 45, "d1", "tbl_transaction")
    s_log = b.add_store(60, 390, 160, 45, "d1", "tbl_prediction_logs")
    s_mac = b.add_store(900, 290, 160, 45, "d1", "tbl_machine_status")
    s_que = b.add_store(900, 480, 160, 45, "d1", "tbl_queue")
    s_apt = b.add_store(60, 840, 160, 45, "d1", "tbl_appointment")

    b.add_edge(s_trx, p51, "Completed Sales & Volume", exit_side=(1, 0.5), entry_side=(0, 0.5))
    b.add_edge(p51, p52, "Aggregated Time-Series Data", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(p52, s_log, "Log MAPE Score & Predictions", exit_side=(0, 0.8), entry_side=(1, 0.3), waypoints=[(360, 340), (360, 400)])
    b.add_edge(p52, p53, "Demand Predictions & Curves", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(s_log, p53, "Audit Trail & Historical MAPE", exit_side=(1, 0.8), entry_side=(0, 0.5), waypoints=[(380, 430), (380, 505)])
    b.add_edge(p53, c_mgr, "Peak Hour Charts & Demand Predictions", exit_side=(1, 0.5), entry_side=(0.5, 1), waypoints=[(720, 505), (1010, 505)])
    b.add_edge(p53, p54, "Operational Directives", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(s_trx, p54, "Revenue & Sales Data", exit_side=(0.5, 1), entry_side=(0, 0.3), waypoints=[(140, 150), (140, 680)])
    b.add_edge(p54, c_mgr, "Automated Reports & Daily Sales Tally", exit_side=(1, 0.5), entry_side=(0.8, 1), waypoints=[(740, 695), (1040, 695)])
    b.add_edge(p54, p55, "Sales Aggregation", exit_side=(0.5, 1), entry_side=(0.5, 0))

    b.add_edge(s_apt, p55, "Historical Booking Patterns", exit_side=(1, 0.5), entry_side=(0, 0.5))
    b.add_edge(s_mac, p55, "Fleet Capacity & Real-Time Slots", exit_side=(0.5, 1), entry_side=(1, 0.3), waypoints=[(980, 350), (980, 870)])
    b.add_edge(p55, c_mgr, "Ghost Slot Recommendations", exit_side=(1, 0.5), entry_side=(0.2, 1), waypoints=[(720, 885), (980, 885)])
    b.add_edge(c_mgr, p55, "Ghost Slot Allocation Request", exit_side=(0, 0.8), entry_side=(1, 0.8), waypoints=[(950, 140), (800, 140), (800, 910)])
    b.add_edge(p55, s_que, "Auto-Queue Reservation Entry", exit_side=(0.8, 0), entry_side=(0.2, 1), waypoints=[(620, 850), (940, 850), (940, 540)])

    return b, "Level 1 - 4.0 Analytics & Forecasts", "page_lvl4"


def main():
    builders = [
        build_level_0(),
        build_level_2(),
        build_level_3(),
        build_level_4(),
        build_level_5()
    ]
    
    # 1. Master Multi-Page File (Uncompressed Draw.io XML)
    diagram_nodes_uncompressed = "\n".join([b.to_diagram_xml(name, did, compress=False) for b, name, did in builders])
    master_xml = f"""<mxfile host="app.diagrams.net" modified="2026-09-10T19:40:00.000Z" agent="Antigravity" version="22.0.0" type="device">
{diagram_nodes_uncompressed}
</mxfile>"""
    (OUT_DIR / "bon_laundry_dfd.drawio").write_text(master_xml, encoding="utf-8")
    print("Saved master multi-page: bon_laundry_dfd.drawio")

    # Also save compressed master version
    diagram_nodes_comp = "\n".join([b.to_diagram_xml(name, did, compress=True) for b, name, did in builders])
    master_comp_xml = f"""<mxfile host="app.diagrams.net" modified="2026-09-10T19:40:00.000Z" agent="Antigravity" version="22.0.0" type="device">
{diagram_nodes_comp}
</mxfile>"""
    (OUT_DIR / "bon_laundry_dfd_compressed.drawio").write_text(master_comp_xml, encoding="utf-8")
    print("Saved master multi-page compressed: bon_laundry_dfd_compressed.drawio")

    # 2. Individual Standalone Files
    filenames = [
        "level_0_system_overview",
        "level_1_process_2_appointment",
        "level_1_process_3_sales_pos",
        "level_1_process_4_operational_status",
        "level_1_process_5_analytics_forecasts"
    ]
    for (b, name, did), fname in zip(builders, filenames):
        # A. Uncompressed .drawio file
        single_drawio = f"""<mxfile host="app.diagrams.net" modified="2026-09-10T19:40:00.000Z" agent="Antigravity" version="22.0.0" type="device">
{b.to_diagram_xml(name, did, compress=False)}
</mxfile>"""
        (OUT_DIR / f"{fname}.drawio").write_text(single_drawio, encoding="utf-8")
        
        # B. Raw uncompressed XML file (root is <mxGraphModel>)
        raw_xml = b.to_raw_model()
        (OUT_DIR / f"{fname}.xml").write_text(raw_xml, encoding="utf-8")
        
    print("Saved all 5 standalone .drawio and uncompressed .xml files successfully.")

if __name__ == "__main__":
    main()
