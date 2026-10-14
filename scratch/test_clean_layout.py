# scratch/test_clean_layout.py
import html
import xml.etree.ElementTree as ET
from pathlib import Path

def escape_xml_attr(s: str) -> str:
    return html.escape(s, quote=True).replace("\n", "&lt;br&gt;")

class CleanDFDBuilder:
    def __init__(self, page_w=1520, page_h=1300):
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
        style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.2;endArrow=classic;endFill=1;fontFamily=Helvetica;fontSize=10;fontColor=#000000;labelBackgroundColor=#ffffff;"
        
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
        return f'''<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.page_w}" pageHeight="{self.page_h}" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    {body}
  </root>
</mxGraphModel>'''

def build_spacious_level_0():
    b = CleanDFDBuilder(1520, 1300)

    # 1. Central Processes (Width 280, Height 75, Vertical gap 115px)
    px, pw, ph = 600, 280, 75
    p1 = b.add_process(px, 70, pw, ph, "1.0", "Staff & Admin Authentication")
    p2 = b.add_process(px, 260, pw, ph, "2.0", "Omnichannel Appointment & Order Lifecycle")
    p3 = b.add_process(px, 460, pw, ph, "3.0", "Process Sales & Transactions")
    p4 = b.add_process(px, 660, pw, ph, "4.0", "Real-time Operational Status & Fleet Telemetry")
    p5 = b.add_process(px, 870, pw, ph, "5.0", "Generate Analytics & Forecasts (Ghost Slots)")
    p6 = b.add_process(px, 1080, pw, ph, "6.0", "Manage System Settings")

    # 2. Entities
    # Customer: centered on the left between 2.0 and 3.0
    c_cust = b.add_entity(70, 360, 150, 90, "Customer\n(Guest / Form-Based)")
    # Staff: right side top
    c_staff = b.add_entity(1270, 260, 140, 85, "Staff")
    # Manager: right side bottom
    c_mgr = b.add_entity(1270, 960, 140, 85, "Manager")

    # 3. Data Stores (Distributed on Left and Right)
    # Right side stores:
    s_usr = b.add_store(960, 85, 170, 44, "d1", "tbl_users")
    s_apt = b.add_store(960, 275, 170, 44, "d1", "tbl_appointment")
    s_trx = b.add_store(960, 475, 170, 44, "d1", "tbl_transaction")
    s_log = b.add_store(960, 885, 170, 44, "d1", "tbl_prediction_logs")

    # Left side stores:
    s_que = b.add_store(320, 645, 170, 44, "d1", "tbl_queue")
    s_mac = b.add_store(320, 755, 170, 44, "d1", "tbl_machine_status")
    s_set = b.add_store(320, 1065, 170, 44, "d1", "tbl_system_settings")

    # 4. CONNECTORS - EVERY LANE IS DEDICATED (ZERO STACKING, ZERO CROSSING THROUGH BOXES)

    # --- PROCESS 1.0 (Staff & Manager Auth, NO Customer Login) ---
    b.add_edge(p1, s_usr, "Staff & Admin Account Data", exit_side=(1, 0.5), entry_side=(0, 0.5))
    b.add_edge(c_staff, p1, "Staff Login Credentials", exit_side=(0, 0.25), entry_side=(1, 0.25), waypoints=[(1200, 281), (1200, 88)])
    b.add_edge(p1, c_staff, "Staff Role Authorization", exit_side=(1, 0.8), entry_side=(0, 0.6), waypoints=[(1180, 130), (1180, 311)])
    
    # Manager -> 1.0 (Far right outer margin lane x=1450)
    b.add_edge(c_mgr, p1, "Manager Login Credentials", exit_side=(1, 0.3), entry_side=(0.8, 0), waypoints=[(1450, 985), (1450, 40), (824, 40)])
    b.add_edge(p1, c_mgr, "Manager Authorization & Privileges", exit_side=(0.6, 0), entry_side=(1, 0.7), waypoints=[(768, 25), (1470, 25), (1470, 1019)])

    # --- PROCESS 2.0 (Guest Appointment Booking Form) ---
    # Customer <-> 2.0: Dedicated horizontal lanes (y=280 and y=320)
    b.add_edge(c_cust, p2, "Appointment Booking Form (Deca Address, Service)", exit_side=(1, 0.2), entry_side=(0, 0.25), waypoints=[(400, 378), (400, 280)])
    b.add_edge(p2, c_cust, "Booking Confirmation, Order Code & EWT", exit_side=(0, 0.75), entry_side=(1, 0.4), waypoints=[(430, 320), (430, 396)])
    b.add_edge(p2, s_apt, "Appointment & Order Record", exit_side=(1, 0.5), entry_side=(0, 0.5))
    b.add_edge(p2, c_staff, "Daily Appointment Schedule", exit_side=(1, 0.2), entry_side=(0, 0.8), waypoints=[(920, 275), (920, 220), (1230, 220), (1230, 328)])

    # --- PROCESS 3.0 (Sales & POS Transactions) ---
    # Customer <-> 3.0: Dedicated horizontal lanes (y=480 and y=520)
    b.add_edge(c_cust, p3, "Payment Details (Cash / GCash via PayMongo)", exit_side=(1, 0.65), entry_side=(0, 0.3), waypoints=[(410, 418), (410, 483)])
    b.add_edge(p3, c_cust, "Digital Receipt & Transaction Confirmation", exit_side=(0, 0.75), entry_side=(1, 0.85), waypoints=[(390, 516), (390, 436)])
    b.add_edge(p3, s_trx, "Sales Record & PayMongo Details", exit_side=(1, 0.5), entry_side=(0, 0.5))
    b.add_edge(c_staff, p3, "POS Load Weight & Counter Cash", exit_side=(0.3, 1), entry_side=(0.85, 0), waypoints=[(1312, 390), (838, 390)])
    b.add_edge(p3, c_staff, "POS Transaction Summary", exit_side=(0.95, 0), entry_side=(0.6, 1), waypoints=[(866, 410), (1354, 410)])

    # --- PROCESS 4.0 (Real-Time Telemetry & Operational Queue) ---
    # 4.0 <-> tbl_queue
    b.add_edge(p4, s_que, "Queue Logs & Progression Status", exit_side=(0, 0.3), entry_side=(1, 0.5), waypoints=[(540, 683), (540, 667)])
    # 4.0 <-> tbl_machine_status
    b.add_edge(p4, s_mac, "Active Machine Timers & State", exit_side=(0, 0.8), entry_side=(1, 0.5), waypoints=[(560, 720), (560, 777)])
    # 4.0 -> Customer (Dedicated wide lane around left side)
    b.add_edge(p4, c_cust, "Live Queue Status, EWT & Ready for Pickup Alert", exit_side=(0, 0.5), entry_side=(0.5, 1), waypoints=[(280, 698), (280, 490), (145, 490)])
    # Staff <-> 4.0
    b.add_edge(c_staff, p4, "Manual Machine Status Override", exit_side=(0.8, 1), entry_side=(1, 0.25), waypoints=[(1382, 430), (1210, 430), (1210, 679)])
    b.add_edge(p4, c_staff, "19-Machine Fleet Telemetry", exit_side=(1, 0.75), entry_side=(0.9, 1), waypoints=[(1240, 716), (1240, 450), (1396, 450)])

    # --- PROCESS 5.0 (Analytics & Ghost Slots) ---
    # tbl_transaction -> 5.0 (Dedicated clean channel between columns)
    b.add_edge(s_trx, p5, "Historical Sales Footfall Data", exit_side=(0.3, 1), entry_side=(0.8, 0), waypoints=[(1011, 560), (920, 560), (920, 820), (824, 820)])
    # tbl_machine_status -> 5.0
    b.add_edge(s_mac, p5, "Fleet Utilization Rates", exit_side=(0.8, 1), entry_side=(0, 0.5), waypoints=[(456, 830), (540, 830), (540, 908)])
    # 5.0 -> tbl_prediction_logs
    b.add_edge(p5, s_log, "Log MAPE Scores & Prediction Audit", exit_side=(1, 0.3), entry_side=(0, 0.5), waypoints=[(920, 893), (920, 907)])
    # 5.0 -> Manager (Direct, clean horizontal lane)
    b.add_edge(p5, c_mgr, "Demand Forecasts, MAPE & Ghost Slot Recommendations", exit_side=(1, 0.75), entry_side=(0, 0.4), waypoints=[(940, 926), (1200, 926), (1200, 994)])

    # --- PROCESS 6.0 (System Settings) ---
    # Manager -> 6.0
    b.add_edge(c_mgr, p6, "Configuration Updates & System Rules", exit_side=(0.3, 1), entry_side=(1, 0.5), waypoints=[(1312, 1118)])
    # 6.0 -> tbl_system_settings
    b.add_edge(p6, s_set, "Updated Pricing, SLAs & Capacity Rules", exit_side=(0, 0.5), entry_side=(0.8, 1), waypoints=[(550, 1118), (550, 1140), (456, 1140)])
    # tbl_system_settings -> Customer (Dedicated outer margin lane x=40)
    b.add_edge(s_set, c_cust, "Laundry Rates & Turnaround Times", exit_side=(0, 0.5), entry_side=(0, 0.5), waypoints=[(40, 1087), (40, 405)])

    return b

b = build_spacious_level_0()
raw_xml = b.to_raw_model()
ET.fromstring(raw_xml)
print("Spacious Level 0 parsed cleanly with 0 errors!")
