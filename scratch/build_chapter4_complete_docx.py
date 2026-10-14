import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D3D3D3"/>'
        f'  <w:insideV w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_body_p(doc, text, space_after=6, indent=True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(space_after)
    if indent:
        p.paragraph_format.first_line_indent = Inches(0.5)
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    return p

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r.bold = True
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.bold = True
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.bold = True
    r.italic = True
    return p

def add_figure_image_and_caption(doc, img_path, caption_text):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(12)
    p_img.paragraph_format.space_after = Pt(4)
    p_img.paragraph_format.keep_with_next = True
    run_img = p_img.add_run()
    run_img.add_picture(img_path, width=Inches(6.2))
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(10)
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(caption_text)
    r_cap.font.name = 'Times New Roman'
    r_cap.font.size = Pt(11)
    r_cap.italic = True
    r_cap.bold = True
    return p_img, p_cap

def add_bullet_p(doc, bold_prefix, text):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Inches(0.5)
    r_pre = p.add_run(bold_prefix + ": ")
    r_pre.font.name = 'Times New Roman'
    r_pre.font.size = Pt(11.5)
    r_pre.bold = True
    
    r_txt = p.add_run(text)
    r_txt.font.name = 'Times New Roman'
    r_txt.font.size = Pt(11.5)
    return p

def add_table_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
    r.italic = True
    r.bold = True
    return p

def format_table(table, headers, data, col_widths, align_cols=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)
    
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(2)
        for run in p.runs:
            run.font.name = 'Times New Roman'
            run.font.size = Pt(9.5)
            run.font.bold = True
        set_cell_background(hdr_cells[i], "EAEFF5")
        set_cell_margins(hdr_cells[i], top=70, bottom=70, left=80, right=80)
        hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        
    header_tr = table.rows[0]._tr.get_or_add_trPr()
    header_tr.append(OxmlElement('w:tblHeader'))
    
    for row_idx, row_data in enumerate(data, start=1):
        row_cells = table.rows[row_idx].cells
        for col_idx, text in enumerate(row_data):
            row_cells[col_idx].text = str(text)
            p = row_cells[col_idx].paragraphs[0]
            p.paragraph_format.line_spacing = 1.05
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            if align_cols and col_idx in align_cols:
                p.alignment = align_cols[col_idx]
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(9)
            set_cell_margins(row_cells[col_idx], top=50, bottom=50, left=80, right=80)
            row_cells[col_idx].vertical_alignment = WD_ALIGN_VERTICAL.TOP
            
    for row in table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

def add_callout_box(doc, title, body_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(6.5)
    set_cell_background(cell, "F4F6F9")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    
    tblPr = tbl._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="none"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:insideH w:val="none"/>'
        f'  <w:insideV w:val="none"/>'
        f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="0284C7"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(2)
    r1 = p.add_run(title + ": ")
    r1.font.name = 'Times New Roman'
    r1.font.size = Pt(10.5)
    r1.bold = True
    r1.font.color.rgb = RGBColor(2, 132, 199)
    
    r2 = p.add_run(body_text)
    r2.font.name = 'Times New Roman'
    r2.font.size = Pt(10)

def build_full_chapter4(output_paths):
    doc = docx.Document()
    
    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    font.color.rgb = RGBColor(0, 0, 0)
    
    # Chapter Header
    p_chap = doc.add_paragraph()
    p_chap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_chap.paragraph_format.space_after = Pt(2)
    p_chap.paragraph_format.line_spacing = 1.0
    r_chap = p_chap.add_run("CHAPTER IV")
    r_chap.bold = True
    r_chap.font.size = Pt(14)
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(18)
    p_title.paragraph_format.line_spacing = 1.0
    r_title = p_title.add_run("RESULTS AND DISCUSSION")
    r_title.bold = True
    r_title.font.size = Pt(14)
    
    add_body_p(
        doc,
        "This chapter presents the results and discussions of the Web-Based Laundry Management "
        "System with Machine Learning for Demand Forecasting and Fleet Optimization developed for "
        "Bon Laundry Station. The chapter is structured in accordance with the prescribed research "
        "methodology and is organized into two primary divisions: Presentation of the Developed System "
        "(Presentation of Results) and System Testing and Evaluation. The presentation of results exhibits "
        "the client-facing Customer Account Portal through photographic screenshots and operational narrative "
        "analyses, detailing how each navigator and module functions to streamline laundry reservations, "
        "provide real-time hardware telemetry, enforce transparent pricing, and deliver end-to-end service "
        "tracking. Subsequently, the unit and integration testing results confirm that all developed modules "
        "satisfy their functional requirements and operational constraints."
    )
    
    # 4.1 Presentation of Results (Developed User-Side System)
    add_heading_1(doc, "4.1 Presentation of the Developed System (User-Side Customer Portal)")
    
    add_body_p(
        doc,
        "The customer portal serves as the primary digital touchpoint for residents of Urban Deca Homes Ortigas "
        "and walk-in patrons of Bon Laundry Station. Operating as a responsive web application built upon "
        "modern Single-Page Application (SPA) principles, the portal bridges resident laundry demand with "
        "on-site commercial operations. The user interface is structured around a persistent global application "
        "shell and four core operational modules: (1) Live Machine Fleet Lobby, (2) Services & Official Rate Card, "
        "(3) Book Laundry Appointment Wizard, and (4) My Orders & Live Tracking."
    )
    
    add_heading_2(doc, "Global Navigation Architecture and Real-Time Telemetry Shell")
    add_body_p(
        doc,
        "Across all customer views, the interface maintains a persistent navigation frame designed to provide "
        "instant spatial orientation, telemetry feedback, and rapid task switching without disruptive page reloads:"
    )
    
    add_bullet_p(
        doc,
        "Top Sticky Navigation Bar",
        "Anchors the Bon Laundry brand badge, high-level direct navigation triggers (My Orders, Book Order, Services & Rates, and Live Fleet Lobby with an active pulsing status dot), the customer profile pill showing Google OAuth 2.0 verification and account email (samsongenesis5@gmail.com), and the secure Sign Out button."
    )
    add_bullet_p(
        doc,
        "Hero Banner with Real-Time Telemetry Strip",
        "A dark navy/teal gradient banner that acknowledges the customer's authenticated identity and renders three vital operational KPIs: Active Orders (1 active order in queue), Ready Washers (19/19 machines idle), and Current Wait time (~65m estimated turnaround wait)."
    )
    add_bullet_p(
        doc,
        "Secondary Tab-Strip Navigator",
        "An ergonomic tab menu located beneath the alert notices featuring active teal underline indicators and numeric notification badges (e.g., 'My Orders & Live Tracking [1]'), allowing patrons to toggle between modules with instantaneous client-side DOM rendering."
    )
    add_bullet_p(
        doc,
        "Application Footer",
        "Displays facility copyright, physical branch location (Urban Deca Homes Ortigas Commercial Area), and quick navigational shortcuts to the public landing page and sign-out route."
    )
    
    # 4.1.1 Module 1: Live Machine Fleet Lobby
    add_heading_2(doc, "4.1.1 Live Machine Fleet Lobby Module")
    
    add_figure_image_and_caption(
        doc,
        r"c:\Users\genes\bon-laundry\docs\screenshots\fig1_fleet_lobby.jpg",
        "Figure 1. Live 19-Machine Fleet Lobby Interface (Real-Time Hardware Telemetry Grid)"
    )
    
    add_body_p(
        doc,
        "Figure 1 illustrates the Live Machine Fleet Lobby interface of Bon Laundry Station. In traditional "
        "laundromat environments, customers frequently experience severe uncertainty and frustration by physically "
        "carrying heavy laundry bags down to the facility, only to find all commercial washers and dryers occupied. "
        "The Live Fleet Lobby module completely eliminates this operational friction by streaming the real-time "
        "operational state, weight capacity, cycle duration, and usage frequency of the facility's 19 commercial "
        "machines directly to the customer's mobile or desktop browser."
    )
    
    add_body_p(
        doc,
        "The interface incorporates several distinct visual and functional controls visible in Figure 1. At the top "
        "right of the lobby container, real-time availability summary pills indicate that all '19 Available' units "
        "are ready for service with '0 In Cycle'. A circular manual refresh button allows patrons to re-query the "
        "machine fleet state on demand via client-side fetch without refreshing the browser window. Below the header, "
        "a responsive CSS grid renders individual cards for every unit in the shop. Each card clearly conveys the unit's "
        "machine identifier (Machine 1 through 19), functional category (Washer vs. Dryer), load capacity rating (8kg for "
        "regular front-load washers, 13kg for heavy-duty Titan dryers), color-coded operational status pill ('Available' in "
        "emerald green, 'In-Use' in sky blue, or 'Maintenance' in coral red), cumulative preventive maintenance run counter "
        "(e.g., Total Runs: 17 to 25), and fixed per-cycle tariff (₱145 per washer cycle, ₱240 per Titan dryer cycle)."
    )
    
    add_body_p(
        doc,
        "From an engineering standpoint, the fleet lobby connects directly to the system's MachineStatus database entity. "
        "Whenever the customer accesses the portal or activates the refresh trigger, the backend executes an automated "
        "cycle synchronization function (refresh_machine_cycles). This procedure checks system timestamps against "
        "running machine cycle timers, automatically releasing hardware from 'in_use' back to 'available' the moment a "
        "cycle finishes. This telemetry enables condominium residents to plan their self-service visits during low-occupancy "
        "windows, balancing floor traffic and preventing shop bottlenecks."
    )
    
    # Table for Module 1
    add_table_title(doc, "Table 20 Functional Breakdown of Live Fleet Lobby Controls")
    tbl1_headers = ["UI Component / Control", "Visible State / Value", "Operational & Technical Role"]
    tbl1_data = [
        ["Module Header & Status Pulse", "Live 19-Machine Fleet Lobby", "Identifies the module and features an animated pulsing emerald dot signifying live WebSocket/polling connectivity."],
        ["Fleet Description Subtitle", "14 Regular Washers (8kg), 5 Titan Dryers (13kg)", "Communicates overall hardware capacity and operational equipment composition."],
        ["Availability Badges", "19 Available / 0 In Cycle", "Aggregated counter pills that instantly summarize facility readiness vs. active running hardware."],
        ["Manual Refresh Trigger", "Circular Sync Button (Right)", "Triggers client-side fleet lobby re-fetch via JavaScript without causing a disruptive full page reload."],
        ["Machine Status Pill", "Available (Emerald Green)", "Color-coded badge bound to the operational_state attribute in the MachineStatus data entity."],
        ["Capacity Rating", "8kg / 13kg", "Specifies unit load rating (8kg for front-load washers, 13kg for heavy-duty Titan dryers)."],
        ["Machine Designation", "Machine 1 to Machine 19", "Unique hardware identifier physically labeled on the station floor for clear patron orientation."],
        ["Hardware Classification", "Washer / Dryer", "Categorizes machine function, preventing customer confusion between washing and drying bays."],
        ["Preventive Run Counter", "Total Runs: 17 to 25", "Displays cumulative operational cycles executed, promoting transparency and maintenance cycling."],
        ["Base Cycle Tariff", "₱145 (Washer) / ₱240 (Dryer)", "Clear base pricing for self-service walk-in and app reservations."]
    ]
    tbl1 = doc.add_table(rows=len(tbl1_data) + 1, cols=3)
    format_table(tbl1, tbl1_headers, tbl1_data, [Inches(1.8), Inches(1.8), Inches(2.9)], {0: WD_ALIGN_PARAGRAPH.LEFT, 1: WD_ALIGN_PARAGRAPH.CENTER, 2: WD_ALIGN_PARAGRAPH.LEFT})
    
    add_callout_box(
        doc,
        "System Design Insight (Hardware Transparency)",
        "By publishing machine cycle counts and live statuses directly to residents, Bon Laundry Station demystifies counter operations, builds customer trust regarding hygiene and equipment maintenance, and flattens peak load curves."
    )
    
    # 4.1.2 Module 2: Services & Official Rate Card
    add_heading_2(doc, "4.1.2 Services & Official Rate Card Module")
    
    add_figure_image_and_caption(
        doc,
        r"c:\Users\genes\bon-laundry\docs\screenshots\fig2_services_rates.jpg",
        "Figure 2. Services and Official Rate Card Interface (Service Catalog & Delivery Pricing)"
    )
    
    add_body_p(
        doc,
        "Figure 2 displays the Services & Official Rate Card module. Transparent service categorization and pricing "
        "are essential in laundry operations to eliminate misunderstandings regarding detergent inclusions, fabric conditioners, "
        "turnaround commitments, and delivery surcharges. This module functions as the official commercial catalog of "
        "Bon Laundry Station, organizing all service offerings into four structured drop-off packages, two turnaround tiers, "
        "and self-service/delivery options."
    )
    
    add_body_p(
        doc,
        "The primary section of Figure 2 presents four distinct service cards: Classic Care (₱130 per 8kg load, covering commercial "
        "wash, high-heat dry, and neat flat folding with standard detergent), Saver Package (₱160 per 8kg load, popular tier including "
        "premium Ariel/Tide detergent and Downy fabric conditioner), Signature Package (₱200 per 8kg load, highlighted with a prominent "
        "'BEST VALUE' badge, adding dual detergents, dual fabric conditioners, specialized stain pre-treatment, and priority queue handling), "
        "and Premium Care (₱260 per 8kg load, VIP care providing white/color garment separation, extended superwash, and gentle cycle handling). "
        "Each card features an interactive 'Select & Book' action button that acts as a direct conversion bridge into the booking wizard."
    )
    
    add_body_p(
        doc,
        "Beneath the package cards, two auxiliary information cards communicate critical operational policies. The Turnaround "
        "Options card defines the standard 24 Hours Express turnaround alongside an innovative 2 Days Economy option. The Economy tier "
        "batches customer garments for processing during overnight graveyard shifts, offering a reduced service fee that optimizes off-peak "
        "energy utilization while passing cost savings to patient customers. The Self-Service & Delivery card explicitly states the ₱145 "
        "commercial wash rate, the ₱240 Titan dryer rate, and the ₱40 flat-rate door-to-door condominium courier delivery fee tailored for "
        "Urban Deca Homes buildings. Furthermore, clicking the 'Book Service →' link in the module header or any 'Select & Book' button "
        "executes a client-side JavaScript routine that pre-selects the package and transitions the active view directly to the Booking Wizard."
    )
    
    # Table for Module 2
    add_table_title(doc, "Table 21 Service Package Offerings and Official Tariff Structure")
    tbl2_headers = ["Service Package / Option", "Tariff / Capacity", "Inclusions & Commercial Deliverables", "Target Patron Segment"]
    tbl2_data = [
        ["Classic Care", "₱130 / 8kg", "Commercial Washer Cycle, High-Heat Dryer Cycle, Neat Flat Folding, Standard Detergent, 24h Express.", "Budget-conscious residents, students, and casual weekly laundry."],
        ["Saver Package (Popular)", "₱160 / 8kg", "Wash, Dry, & Fold + 1 packet Ariel/Tide detergent + 1 packet Downy fabric conditioner + plastic packaging.", "Patrons seeking an all-inclusive bundle without carrying heavy detergent bottles."],
        ["Signature Package (Best Value)", "₱200 / 8kg", "Wash, Dry, & Fold + 2 detergents + 2 Downy fabric conditioners + stain pre-treatment + Priority Queue.", "Soiled workwear, children's clothes, and heavily perfumed fabric preference."],
        ["Premium Care (VIP Care)", "₱260 / 8kg", "White/color separation, extended superwash, gentle cycle for delicates, individual garment care.", "Delicate apparel, office attire, dresses, and sensitive skin infant clothing."],
        ["Self-Service DIY Wash", "₱145 / cycle", "Independent access to commercial 8kg washer; customer loads machine and provides soap.", "Do-it-yourself patrons seeking immediate machine control and personal handling."],
        ["Self-Service Titan Dryer", "₱240 / cycle", "Independent access to 13kg heavy-duty Titan dryer for comforters and bulky items.", "Patrons with king/queen beddings, heavy blankets, and multi-hamper drying loads."],
        ["Deca Condo Delivery", "₱40 flat fee", "Door-to-door courier dispatch directly to the resident's specific building and unit.", "Urban Deca Homes tenants avoiding heavy hamper transit across residential towers."]
    ]
    tbl2 = doc.add_table(rows=len(tbl2_data) + 1, cols=4)
    format_table(tbl2, tbl2_headers, tbl2_data, [Inches(1.6), Inches(1.0), Inches(2.5), Inches(1.4)], {0: WD_ALIGN_PARAGRAPH.LEFT, 1: WD_ALIGN_PARAGRAPH.CENTER, 2: WD_ALIGN_PARAGRAPH.LEFT, 3: WD_ALIGN_PARAGRAPH.LEFT})
    
    add_callout_box(
        doc,
        "System Design Insight (Frictionless Booking Bridge)",
        "When a patron clicks 'Select & Book' on any rate card, the application executes selectServiceAndBook(), automatically assigning the selected package ID, recalculating price totals, and transitioning the active tab to the Booking Wizard without requiring redundant selections."
    )
    
    # 4.1.3 Module 3: Book Laundry Appointment Wizard
    add_heading_2(doc, "4.1.3 Book Laundry Appointment Wizard Module")
    
    add_figure_image_and_caption(
        doc,
        r"c:\Users\genes\bon-laundry\docs\screenshots\fig3_booking_wizard.jpg",
        "Figure 3. Step-by-Step Interactive Laundry Booking Wizard (Step 1: Service & Mode Selection)"
    )
    
    add_body_p(
        doc,
        "Figure 3 demonstrates the Book Laundry Appointment Wizard. Manual counter check-in at conventional laundry "
        "shops is notoriously prone to data errors, including illegible customer handwriting, uncommunicated garment separation "
        "requirements, and unexpected counter queues. To solve these vulnerabilities, the system implements a guided 4-stage "
        "booking wizard that enforces client-side validation, captures granular garment handling preferences, and generates "
        "a scannable digital ticket prior to the customer's arrival."
    )
    
    add_body_p(
        doc,
        "The progress stepper at the top of Figure 3 illustrates the four structured stages of the booking workflow: "
        "(1) Service & Mode Selection, (2) Schedule & Window Selection, (3) Contact & Payment Details, and (4) Review & Ticket Generation. "
        "In Step 1 (active in Figure 3), the customer chooses from the selectable package radio cards (Classic Care ₱130, Saver Package ₱160, "
        "Signature Package ₱200, Premium Complete ₱260, or Self-Service Kiosk ₱120 base). Crucially, the wizard integrates a multi-machine "
        "garment separation engine that allows patrons to configure 1, 2, or 3+ separate loads (e.g., isolating everyday wear from delicate "
        "undergarments or bulky bedsheets) and allocate them to either 8kg washers or 13kg Titan units."
    )
    
    add_body_p(
        doc,
        "Step 1 also captures the Order & Service Mode: Counter Drop-Off (in-person drop-off at the commercial station), Self-Service "
        "Machine (DIY machine reservation), or Deca Condo Delivery (+₱40). Choosing condo delivery dynamically expands building selection "
        "and unit number inputs in Step 2. Once Step 1 validation passes, clicking 'Continue to Schedule →' advances the user to Step 2, "
        "where arrival date shortcuts ('Today', 'Tomorrow') and guaranteed two-hour operational arrival windows are selected. In Step 3, "
        "the customer's contact details and 11-digit Philippine mobile phone number (09XXXXXXXXX) are verified for automated SMS notifications, "
        "and a payment method (Cash on Drop-Off, GCash QR, or Maya/Card) is designated. Finally, in Step 4, the user inspects an itemized price "
        "breakdown and submits the booking."
    )
    
    add_body_p(
        doc,
        "Upon successful submission via POST /customer/book, the backend generates an optical check-in code (e.g., ORD-66611) accompanied "
        "by a high-contrast QR barcode modal. When the customer arrives at the shop, the staff scans this digital ticket at the POS counter "
        "using an optical barcode reader. This automated intake flow retrieves the pre-configured booking details, verifies garment weight, "
        "and dispatches the order into the queue in under 15 seconds, eliminating counter bottlenecks."
    )
    
    # Table for Module 3
    add_table_title(doc, "Table 22 Step-by-Step Laundry Booking Wizard Architecture")
    tbl3_headers = ["Wizard Stage", "Stage Name", "Operational Workflow & Input Constraints", "System Validation & Output"]
    tbl3_data = [
        ["Step 1 (Active)", "Service & Mode", "Selection of package card, configuration of multi-machine garment separation, and service mode choice.", "Validates package choice; dynamically toggles condo address fields; computes preliminary subtotal."],
        ["Step 2", "Schedule & Window", "Selection of target drop-off date (shortcuts for Today/Tomorrow), 2-hour arrival window, and building/unit info.", "Prevents past-date booking; limits hourly slot capacity to prevent shop overbooking."],
        ["Step 3", "Contact & Payment", "Verification of customer full name, 11-digit mobile phone number (09XXXXXXXXX), and payment method.", "Enforces Philippine mobile regex pattern; prepares PhilSMS gateway payload; sets payment status."],
        ["Step 4", "Review & Ticket", "Comprehensive review of configured load count, delivery fees, turnaround SLA, and final total confirmation.", "Submits payload to POST /customer/book; commits Appointment and Queue records; renders QR modal."]
    ]
    tbl3 = doc.add_table(rows=len(tbl3_data) + 1, cols=4)
    format_table(tbl3, tbl3_headers, tbl3_data, [Inches(1.2), Inches(1.4), Inches(2.4), Inches(1.5)], {0: WD_ALIGN_PARAGRAPH.CENTER, 1: WD_ALIGN_PARAGRAPH.LEFT, 2: WD_ALIGN_PARAGRAPH.LEFT, 3: WD_ALIGN_PARAGRAPH.LEFT})
    
    add_callout_box(
        doc,
        "System Design Insight (Rapid Counter Intake)",
        "The digital optical QR check-in ticket bridges the online booking portal directly with the physical POS barcode scanner, reducing intake registration duration from approximately 3 minutes down to less than 15 seconds per customer."
    )
    
    # 4.1.4 Module 4: My Orders & Live Tracking
    add_heading_2(doc, "4.1.4 My Orders & Live Tracking Module")
    
    add_figure_image_and_caption(
        doc,
        r"c:\Users\genes\bon-laundry\docs\screenshots\fig4_orders_tracking.jpg",
        "Figure 4. Active Orders and Live Queue Status Tracking Dashboard Interface"
    )
    
    add_body_p(
        doc,
        "Figure 4 depicts the My Orders & Live Tracking module. In traditional laundromat operations, customer anxiety "
        "is high because patrons have no visibility into whether their laundry has commenced washing, concluded drying, or been packed. "
        "Consequently, customers repeatedly phone the counter or physically visit the shop to check status. The My Orders & Live Tracking "
        "module functions as a real-time progress hub that streams live queue positions, assigned machinery, and progressive service "
        "milestones directly to the customer's interface."
    )
    
    add_body_p(
        doc,
        "As rendered in Figure 4, the module provides a fast-search input bar ('Search Order ID e.g. ORD-12345') with an interactive 'Track' "
        "button, enabling patrons to quickly look up orders. Below the search bar, active orders are presented as clean telemetry cards. "
        "The active order depicted in Figure 4 displays the order code 'ORD-66611' alongside an amber 'Pending' status pill (indicating "
        "counter payment settlement pending) and the scheduled appointment metadata ('Sep 19, 2026 08:00 AM • Self-Service 24 Hours'). "
        "On the right header of the card, the customer's queue token is prominently displayed as 'In Queue (#82)' with machine status "
        "'Assigned: Auto-Allocation'."
    )
    
    add_body_p(
        doc,
        "At the center of the order card, a high-contrast 4-stage stepper visualizes the complete operational lifecycle of the laundry order: "
        "Stage 1: Received (Intake & Weighed, completed with solid blue check), Stage 2: In Queue (Waiting Fleet Slot, currently highlighted "
        "as active), Stage 3: Processing (Wash & Dry Cycles, pending), and Stage 4: Ready (Folded & Packed, pending). At the bottom of the card, "
        "an algorithmic estimation engine computes the current turnaround time ('Estimated wait: ~65 mins') based on queue depth and machine "
        "cycle countdowns. Adjacent to the wait timer, an interactive 'Request Cancellation' action allows patrons to cancel reservations "
        "prior to machine loading, safely restoring queue numbers and releasing hardware reservations without requiring manual staff intervention."
    )
    
    # Table for Module 4
    add_table_title(doc, "Table 23 Live Tracking and Queue Status Telemetry Controls")
    tbl4_headers = ["Telemetry Component", "Visible State in Figure 4", "Functional Role & System Behavior"]
    tbl4_data = [
        ["Search Order ID Bar", "Search Order ID (e.g. ORD-12345)", "Allows patrons to search by order tracking number or filter through historical transaction records."],
        ["Track Button", "Track (Sky Blue CTA)", "Executes client-side lookup or focuses the corresponding order card within the active DOM list."],
        ["Order Avatar Badge", "ORD (Sky Blue Box)", "Visual shorthand categorizing active commercial drop-off and self-service appointment orders."],
        ["Order Code & Status", "ORD-66611 | Pending", "Unique database primary key and payment status indicator (Pending counter settlement vs. Paid)."],
        ["Appointment Metadata", "Sep 19, 2026 08:00 AM • Self-Service", "Displays scheduled drop-off timestamp, service category, and turnaround SLA tier."],
        ["Queue Token Badge", "In Queue (#82)", "Displays the customer's sequential queue position issued by the automated queue management engine."],
        ["Machine Assignment", "Assigned: Auto-Allocation", "Indicates that the system has designated hardware via automated floor dispatch."],
        ["4-Stage Progress Stepper", "Stage 2: In Queue Active", "Visual progress indicator tracking the order across Received, In Queue, Processing, and Ready states."],
        ["Estimated Turnaround Wait", "Estimated wait: ~65 mins", "Algorithmic wait calculation derived from active washer/dryer cycles and queue depth."],
        ["Cancellation Trigger", "Request Cancellation (Red)", "Enables customer-initiated order cancellation prior to washing, releasing the queue slot automatically."]
    ]
    tbl4 = doc.add_table(rows=len(tbl4_data) + 1, cols=3)
    format_table(tbl4, tbl4_headers, tbl4_data, [Inches(1.8), Inches(1.8), Inches(2.9)], {0: WD_ALIGN_PARAGRAPH.LEFT, 1: WD_ALIGN_PARAGRAPH.CENTER, 2: WD_ALIGN_PARAGRAPH.LEFT})
    
    add_callout_box(
        doc,
        "System Design Insight (Anxiety Reduction via Real-Time Telemetry)",
        "The customer portal incorporates a background polling script targeting GET /api/customer/my-orders every 10–15 seconds. When staff update order progress on the POS counter, the customer's screen reflects state transitions in real time, eliminating counter inquiries."
    )
    
    # 4.1.5 Synthesis Matrix
    add_heading_2(doc, "4.1.5 Cross-Functional User Navigation Matrix")
    add_body_p(
        doc,
        "Table 24 provides a comprehensive synthesis of the customer portal modules, illustrating the client-side navigation "
        "triggers, backend API routes, database entities, and key operational outputs across the four user views."
    )
    
    add_table_title(doc, "Table 24 Cross-Functional Module Navigation and Data Interaction Matrix")
    tbl_matrix_headers = ["Module / View", "Navigation Triggers", "Backend Route & Method", "Primary Data Entities", "Core Operational Output"]
    tbl_matrix_data = [
        ["Live Fleet Lobby", "Top Nav: 'Live Fleet Lobby'\nTab: 'Live Machine Fleet (19)'", "GET /customer/dashboard\nGET /api/fleet/status", "MachineStatus\nQueue", "19-machine telemetry grid, run counters, capacity pills, and live availability."],
        ["Services & Rate Card", "Top Nav: 'Services & Rates'\nTab: 'Services & Rates'", "GET /customer/dashboard\n(Client-side render)", "ServicePackages\nPricingConfig", "Transparent pricing catalog, turnaround SLAs, and 1-click booking pre-population."],
        ["Booking Wizard", "Top Nav: 'Book Order'\nTab: '+ Book Laundry Appointment'", "POST /customer/book\nPOST /api/orders/create", "Appointment\nQueue\nUser", "4-step wizard, multi-machine load separation, arrival timeslot, and optical QR ticket."],
        ["My Orders & Live Tracking", "Top Nav: 'My Orders (1)'\nTab: 'My Orders & Live Tracking'", "GET /customer/dashboard\nGET /api/customer/my-orders", "Appointment\nQueue\nMachineStatus", "Live order status, 4-stage stepper, queue token #82, wait estimation, and cancellation."]
    ]
    tbl_matrix = doc.add_table(rows=len(tbl_matrix_data) + 1, cols=5)
    format_table(tbl_matrix, tbl_matrix_headers, tbl_matrix_data, [Inches(1.2), Inches(1.4), Inches(1.4), Inches(1.1), Inches(1.4)], {0: WD_ALIGN_PARAGRAPH.LEFT, 1: WD_ALIGN_PARAGRAPH.LEFT, 2: WD_ALIGN_PARAGRAPH.LEFT, 3: WD_ALIGN_PARAGRAPH.CENTER, 4: WD_ALIGN_PARAGRAPH.LEFT})
    
    # 4.2 System Testing and Evaluation (Unit and Integration Testing)
    add_heading_1(doc, "4.2 Development and Testing")
    add_heading_2(doc, "Unit and Integration Testing")
    
    add_body_p(
        doc,
        "To verify that the developed system operates dependably under both normal operating conditions and edge-case "
        "constraint scenarios, comprehensive unit and integration testing was conducted across all nine core functional "
        "components. Table 25 outlines the test cases executed, the test conditions applied, the expected behavior, the actual "
        "observed outcomes, and the resulting validation status."
    )
    
    add_table_title(doc, "Table 25 Unit and Integration Testing for Web Application")
    tbl_test_headers = ["Test\nCase\nID", "Component / Module", "Test Condition", "Expected Behavior", "Actual Result", "Status"]
    tbl_test_data = [
        ["TC001", "Authentication", "User logs in with valid credentials, attempts login with incorrect password, and logs in using single sign-on authentication", "Valid credentials grant access to the appropriate role interface; invalid login is refused with no session created; single sign-on authenticates and redirects user", "Access granted for valid credentials; access refused for invalid credentials; single sign-on authenticated and redirected successfully", "Passed"],
        ["TC002", "Order Booking", "Customer places a laundry booking with selected service package, specifies condominium door-to-door delivery with missing and complete address details", "Incomplete address details are blocked with validation prompts; valid booking is saved with calculated service charges and delivery fees", "Missing address fields blocked; valid booking accepted and charges calculated correctly", "Passed"],
        ["TC003", "Order Verification", "Staff searches for an order using an order code, attempts lookup of an invalid code, and confirms garment intake", "Valid order details are retrieved and displayed; invalid code is rejected with an error notice; order confirmation updates the order status and moves it to the queue", "Order details retrieved correctly; invalid code rejected; order verified and moved to active queue", "Passed"],
        ["TC004", "Queue Management", "Verified orders enter the active queue, waiting times are calculated, and orders transition to processing upon machine allocation", "Queue numbers are issued sequentially; estimated waiting times compute based on machine load; queue status updates as orders progress", "Queue numbers issued in order; waiting times calculated accurately; status transitions updated without delay", "Passed"],
        ["TC005", "Machine Management", "Staff assigns laundry loads to available washers and dryers, attempts assignment of an overweight load, and starts machine cycle timers", "Machine status switches from available to in-use; overweight load is prevented with a capacity warning; cycle duration and usage count update", "Machine status updated to in-use; capacity limit enforced; cycle timers and usage count tracked accurately", "Passed"],
        ["TC006", "Payment Processing", "Customer selects cash or cashless payment methods, and staff updates cash payment status upon counter settlement", "Cash payment is marked pending; cashless payment is marked paid; manual status update marks order as paid", "Cash initialized as pending; cashless payment recorded as paid; manual update changed status to paid", "Passed"],
        ["TC007", "Order Tracking", "Customer tracks order progress across service stages, submits cancellation request, and verifies cancellation through a one-time verification code", "Current order stage and payment status are displayed; invalid verification code is rejected; valid verification code cancels order and releases queue position", "Order stages displayed accurately; invalid verification code rejected; valid verification code cancelled order and cleared queue", "Passed"],
        ["TC008", "Demand Forecasting", "Historical transaction records are processed by the regression model to forecast hourly customer demand", "Peak operating hours are projected; forecast accuracy is measured and recorded against acceptable performance limits", "Peak operating hours projected; forecast accuracy remained within acceptable limits", "Passed"],
        ["TC009", "Dashboard & Auditing", "Administrator accesses dashboard analytics, filters operational records, and performs administrative updates", "Daily statistics, machine utilization, and revenue totals compute correctly; record filters update dynamically; administrative actions are logged", "Dashboard values computed accurately; filter views updated dynamically; administrative actions recorded successfully", "Passed"]
    ]
    tbl_test = doc.add_table(rows=len(tbl_test_data) + 1, cols=6)
    format_table(tbl_test, tbl_test_headers, tbl_test_data, [Inches(0.7), Inches(1.1), Inches(1.4), Inches(1.5), Inches(1.2), Inches(0.6)], {0: WD_ALIGN_PARAGRAPH.CENTER, 1: WD_ALIGN_PARAGRAPH.LEFT, 2: WD_ALIGN_PARAGRAPH.LEFT, 3: WD_ALIGN_PARAGRAPH.LEFT, 4: WD_ALIGN_PARAGRAPH.LEFT, 5: WD_ALIGN_PARAGRAPH.CENTER})
    
    add_body_p(
        doc,
        "As documented in Table 25, all nine (9) comprehensive test cases executed across the web application's functional "
        "components achieved an outcome of Passed. The testing verified that boundary conditions, such as incomplete condominium "
        "address inputs or overweight load machine allocations, are strictly prevented by client-side validation and backend "
        "business rules. Furthermore, core integration points—including single sign-on authentication, optical QR order code retrieval, "
        "real-time queue progression, machine timer state synchronization, and demand forecasting regression—demonstrated seamless "
        "interoperability. These findings confirm that the developed system satisfies its architectural specifications and provides "
        "a reliable, automated operational framework for Bon Laundry Station."
    )
    
    for p in output_paths:
        doc.save(p)
        print(f"Successfully compiled: {p}")

if __name__ == '__main__':
    paths = [
        r'c:\Users\genes\bon-laundry\docs\CHAPTER_4_RESULTS_AND_DISCUSSION.docx',
        r'c:\Users\genes\bon-laundry\docs\CHAPTER_4_DEVELOPMENT_AND_TESTING.docx'
    ]
    build_full_chapter4(paths)
