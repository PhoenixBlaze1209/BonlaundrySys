# scratch/test_no_login_layout.py
import html
import xml.etree.ElementTree as ET
from pathlib import Path

def escape_xml_attr(s: str) -> str:
    return html.escape(s, quote=True).replace("\n", "&lt;br&gt;")

class NoLoginDFDBuilder:
    def __init__(self, page_w=1500, page_h=1260):
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
        # Reference styling: light grey #f5f5f5, stroke #666666, crisp black text
        style = "rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;strokeWidth=1.5;fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#000000;align=center;verticalAlign=middle;"
        self.cells.append(f'<mxCell id="{cid}" value="{esc}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" /></mxCell>')
        return cid

    def add_process(self, x, y, w, h, pid, name):
        cid_top = self.next_id()
        cid_bot = self.next_id()
        esc_top = escape_xml_attr(pid)
        esc_bot = escape_xml_attr(name)
        hdr_h = 24
        bot_h = h - hdr_h
        
        # Reference styling: top light blue #dae8fc border #6c8ebf, bottom white border #6c8ebf
        style_top = "rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;strokeWidth=1.5;fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#000000;align=center;verticalAlign=middle;"
        style_bot = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#6c8ebf;strokeWidth=1.5;fontFamily=Helvetica;fontSize=12;fontStyle=0;fontColor=#000000;align=center;verticalAlign=middle;"
        
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

    def add_edge(self, src_id, tgt_id, label="", exit_side=None, entry_side=None, waypoints=None):
        eid = self.next_id()
        esc = escape_xml_attr(label)
        # jumpStyle=arc and jumpSize=6 creates clean arc bridges whenever orthogonal lines cross!
        style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.2;endArrow=classic;endFill=1;jumpStyle=arc;jumpSize=6;fontFamily=Helvetica;fontSize=10;fontColor=#000000;labelBackgroundColor=#ffffff;"
        
        if exit_side:
            style += f"exitX={exit_side[0]};exitY={exit_side[1]};exitDx=0;exitDy=0;"
        if entry_side:
            style += f"entryX={entry_side[0]};entryY={entry_side[1]};entryDx=0;entryDy=0;"
            
        pts_xml = ""
        if waypoints:
            pts_xml = '<Array as="points">' + ''.join([f'<mxPoint x="{px}" y="{py}" />' for px, py in waypoints]) + '</Array>'
            
        self.cells.append(f'''<mxCell id="{eid}" value="{esc}" style="{style}" edge="1" parent="1" source="{src_id}" target="{tgt_id}">
          <mxGeometry relative="1" as="geometry">{pts_xml}</mxGeometry>
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

def build_no_login_level_0():
    b = NoLoginDFDBuilder(1480, 1260)

    # 1. Central Processes (Width 280, Height 76, 5 Operational Processes - NO LOGIN)
    px, pw, ph = 590, 280, 76
    p1 = b.add_process(px, 100, pw, ph, "1.0", "Appointment & Order Intake")
    p2 = b.add_process(px, 330, pw, ph, "2.0", "Process Sales & Transactions")
    p3 = b.add_process(px, 560, pw, ph, "3.0", "Real-time Operational Status")
    p4 = b.add_process(px, 800, pw, ph, "4.0", "Generate Analytics & Forecasts")
    p5 = b.add_process(px, 1040, pw, ph, "5.0", "Manage System Settings")

    # 2. Entities
    # Customer: left side adjacent to 1.0 and 2.0
    c_cust = b.add_entity(70, 230, 150, 90, "Customer\n(Walk-in / Online Guest)")
    # Staff: right side adjacent to 1.0, 2.0, and 3.0
    c_staff = b.add_entity(1250, 230, 140, 90, "Staff\n(Front Desk & Attendants)")
    # Manager: right side adjacent to 4.0 and 5.0
    c_mgr = b.add_entity(1250, 880, 140, 90, "Manager\n(Store Administrator)")

    # 3. Data Stores (Bilateral Layout - Placed right next to writing processes)
    # Right column stores:
    s_apt = b.add_store(970, 115, 170, 46, "d1", "tbl_appointment")
    s_trx = b.add_store(970, 345, 170, 46, "d1", "tbl_transaction")
    s_log = b.add_store(970, 815, 170, 46, "d1", "tbl_prediction_logs")

    # Left column stores:
    s_que = b.add_store(310, 545, 170, 46, "d1", "tbl_queue")
    s_mac = b.add_store(310, 675, 170, 46, "d1", "tbl_machine_status")
    s_set = b.add_store(310, 1025, 170, 46, "d1", "tbl_system_settings")

    # 4. CONNECTORS - EVERY LANE DEDICATED (ZERO STACKING, ZERO DATA STORE CROSSING, ARC JUMPS)

    # --- PROCESS 1.0 (Appointment & Order Intake) ---
    # Customer -> 1.0: Appointment Booking Form (x=410, y=120)
    b.add_edge(c_cust, p1, "Appointment Booking Details (Deca Address, Service)", exit_side=(1, 0.25), entry_side=(0, 0.25), waypoints=[(410, 252), (410, 120)])
    # 1.0 -> Customer: Available Slot & Booking Confirmation (x=370, y=150)
    b.add_edge(p1, c_cust, "Available Slot Info & Order Confirmation", exit_side=(0, 0.65), entry_side=(1, 0.5), waypoints=[(370, 150), (370, 275)])
    # 1.0 -> tbl_appointment: Direct horizontal store flow
    b.add_edge(p1, s_apt, "Appointment Entry & Order Code", exit_side=(1, 0.5), entry_side=(0, 0.5))
    # 1.0 -> Staff: Daily Appointment Schedule (Bypasses tbl_appointment at x=1190)
    b.add_edge(p1, c_staff, "Daily Appointment Schedule", exit_side=(1, 0.8), entry_side=(0, 0.25), waypoints=[(1190, 160), (1190, 252)])

    # --- PROCESS 2.0 (Process Sales & Transactions) ---
    # Customer -> 2.0: Payment Details (x=420, y=350)
    b.add_edge(c_cust, p2, "Payment Details (Cash / GCash via PayMongo)", exit_side=(1, 0.8), entry_side=(0, 0.25), waypoints=[(420, 302), (420, 350)])
    # 2.0 -> Customer: Digital Receipt Information (x=360, y=380)
    b.add_edge(p2, c_cust, "Digital Receipt & Payment Confirmation", exit_side=(0, 0.65), entry_side=(0.8, 1), waypoints=[(360, 380), (360, 320)])
    # 2.0 -> tbl_transaction: Direct horizontal store flow
    b.add_edge(p2, s_trx, "Sales Record & Job Order Details", exit_side=(1, 0.5), entry_side=(0, 0.5))
    # Staff -> 2.0: Load Information & Machine Assignment (x=1200, y=350)
    b.add_edge(c_staff, p2, "Load Information & Machine Assignment Data", exit_side=(0, 0.75), entry_side=(1, 0.25), waypoints=[(1200, 298), (1200, 350)])
    # 2.0 -> Staff: Service Fee & POS Summary (x=1170, y=390)
    b.add_edge(p2, c_staff, "Service Fee Data & POS Transaction Summary", exit_side=(1, 0.8), entry_side=(0, 0.5), waypoints=[(1170, 390), (1170, 275)])
    # 2.0 -> Manager: Transaction Data & Audit Logs (x=1220 outer channel)
    b.add_edge(p2, c_mgr, "Transaction Data & Revenue Logs", exit_side=(0.7, 1), entry_side=(0, 0.25), waypoints=[(786, 440), (1220, 440), (1220, 902)])

    # --- PROCESS 3.0 (Real-time Operational Status) ---
    # 3.0 -> Customer: Wide left channel (x=240) down to Customer bottom
    b.add_edge(p3, c_cust, "Email / SMS Notifications, Queue Number & Live EWT", exit_side=(0, 0.3), entry_side=(0.4, 1), waypoints=[(240, 583), (240, 320)])
    # 3.0 -> tbl_queue: Direct horizontal / clean step
    b.add_edge(p3, s_que, "Queue Logs & Progression Status", exit_side=(0, 0.5), entry_side=(1, 0.5), waypoints=[(530, 598), (530, 568)])
    # 3.0 -> tbl_machine_status
    b.add_edge(p3, s_mac, "Updated Machine Status Data", exit_side=(0, 0.8), entry_side=(1, 0.3), waypoints=[(510, 621), (510, 688)])
    # tbl_machine_status -> 3.0
    b.add_edge(s_mac, p3, "Machine Status Data & Cycle State", exit_side=(1, 0.7), entry_side=(0.15, 1), waypoints=[(550, 707), (550, 636)])
    # Staff -> 3.0: Status override
    b.add_edge(c_staff, p3, "Manual Machine Status Override", exit_side=(0.5, 1), entry_side=(0.8, 0), waypoints=[(1320, 460), (814, 460)])
    # 3.0 -> Staff: Fleet Telemetry (x=1190)
    b.add_edge(p3, c_staff, "Real-time Service Status Updates & Fleet EWT", exit_side=(1, 0.3), entry_side=(0, 0.9), waypoints=[(1190, 583), (1190, 311)])
    # 3.0 -> tbl_prediction_logs: EWT updates
    b.add_edge(p3, s_log, "Real-time EWT & Cycle Durations", exit_side=(1, 0.8), entry_side=(0, 0.3), waypoints=[(920, 621), (920, 829)])
    # 3.0 -> tbl_system_settings: Machine ID
    b.add_edge(p3, s_set, "Machine ID & Fleet Configuration", exit_side=(0.1, 1), entry_side=(0, 0.3), waypoints=[(618, 960), (200, 960), (200, 1039)])

    # --- PROCESS 4.0 (Generate Analytics & Forecasts) ---
    # tbl_transaction -> 4.0: Historical sales volume
    b.add_edge(s_trx, p4, "Historical Transaction Volume Data", exit_side=(0.4, 1), entry_side=(0.85, 0), waypoints=[(1038, 430), (940, 430), (940, 800)])
    # tbl_machine_status -> 4.0: Fleet utilization
    b.add_edge(s_mac, p4, "Real-time Machine Utilization Data", exit_side=(0.8, 1), entry_side=(0, 0.4), waypoints=[(446, 760), (540, 760), (540, 830)])
    # 4.0 -> tbl_prediction_logs: Direct horizontal store flow
    b.add_edge(p4, s_log, "EWT Prediction Data & MAPE Score", exit_side=(1, 0.5), entry_side=(0, 0.5))
    # 4.0 -> Manager: Direct horizontal lane
    b.add_edge(p4, c_mgr, "Peak Demand Forecasts, Operational Trends & Sales Analytics", exit_side=(1, 0.8), entry_side=(0, 0.5), waypoints=[(1200, 861), (1200, 925)])

    # --- PROCESS 5.0 (Manage System Settings) ---
    # Manager -> 5.0: Configuration updates
    b.add_edge(c_mgr, p5, "Configuration Data & System Parameters", exit_side=(0.5, 1), entry_side=(1, 0.5), waypoints=[(1320, 1078)])
    # 5.0 -> tbl_system_settings: Direct horizontal store flow
    b.add_edge(p5, s_set, "Updated System Parameters & Rates", exit_side=(0, 0.5), entry_side=(1, 0.5), waypoints=[(530, 1078), (530, 1048)])
    # tbl_system_settings -> Customer: Far-left outer margin channel (x=40)
    b.add_edge(s_set, c_cust, "Service Rates & Turnaround Times", exit_side=(0, 0.7), entry_side=(0, 0.5), waypoints=[(40, 1057), (40, 275)])

    return b

b = build_no_login_level_0()
raw_xml = b.to_raw_model()
ET.fromstring(raw_xml)
print("No-Login Spacious Level 0 parsed cleanly with 0 XML errors!")
