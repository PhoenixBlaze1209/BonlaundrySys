"""
scratch/build_capstone_use_case_docx.py
Generates the publication-ready Capstone Documentation for UML Use Case Diagram
and Use Case Specifications for Bon Laundry Station (Urban Deca Homes Ortigas).
Adheres strictly to GRC / IEEE Software Engineering Use Case Modeling rules.
"""

import os
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOC_PATH = Path(r"c:\Users\genes\bon-laundry\docs\CAPSTONE_USE_CASE_DOCUMENTATION.docx")
IMG_PATH = Path(r"c:\Users\genes\bon-laundry\docs\diagrams\use_case_diagram.png")

# Palette constants
COLOR_PRIMARY = RGBColor(15, 23, 42)      # Deep Slate #0f172a
COLOR_SECONDARY = RGBColor(2, 132, 199)   # Ocean Blue #0284c7
COLOR_TEXT = RGBColor(30, 41, 59)         # Dark Slate #1e293b
COLOR_MUTED = RGBColor(100, 116, 139)     # Gray #64748b
HEX_HEADER_BG = "0F2942"                  # Deep Navy
HEX_SUBHEADER_BG = "F1F5F9"               # Light Slate
HEX_ALT_ROW = "F8FAFC"                    # Subtle Row Tint
HEX_BORDER = "CBD5E1"                     # Soft Border

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color=HEX_BORDER):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def format_paragraph(p, space_before=0, space_after=6, line_spacing=1.15, align=WD_ALIGN_PARAGRAPH.LEFT):
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    p.alignment = align

def add_heading_1(doc, text):
    h = doc.add_paragraph()
    format_paragraph(h, space_before=14, space_after=6)
    run = h.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(13.5)
    run.font.bold = True
    run.font.color.rgb = COLOR_PRIMARY
    return h

def add_heading_2(doc, text):
    h = doc.add_paragraph()
    format_paragraph(h, space_before=10, space_after=4)
    run = h.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = COLOR_SECONDARY
    return h

def add_body_p(doc, text, bold_prefix=""):
    p = doc.add_paragraph()
    format_paragraph(p, space_before=0, space_after=5, line_spacing=1.15)
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10.5)
        r_pre.font.bold = True
        r_pre.font.color.rgb = COLOR_TEXT
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.color.rgb = COLOR_TEXT
    return p

def create_spec_table(doc, uc_id, uc_title, actor, desc, pre, post, trigger, basic_flow, alt_flow, inc_ext):
    data_rows = [
        ("Primary Actor(s)", actor),
        ("Description", desc),
        ("Preconditions", pre),
        ("Postconditions", post),
        ("Trigger", trigger),
        ("Main Flow of Events", basic_flow),
        ("Alternative / Exception Flows", alt_flow),
        ("Stereotype Relationships", inc_ext)
    ]
    t = doc.add_table(rows=len(data_rows) + 1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t)

    col_widths = [Inches(1.8), Inches(4.7)]

    # Row 0: Title header
    cell_hdr = t.cell(0, 0)
    cell_hdr.merge(t.cell(0, 1))
    set_cell_background(cell_hdr, HEX_HEADER_BG)
    set_cell_margins(cell_hdr, 120, 120, 140, 140)
    p = cell_hdr.paragraphs[0]
    format_paragraph(p, space_before=2, space_after=2, align=WD_ALIGN_PARAGRAPH.LEFT)
    r = p.add_run(f"USE CASE SPECIFICATION: {uc_id} — {uc_title.upper()}")
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(255, 255, 255)

    for idx, (label, content) in enumerate(data_rows, start=1):
        c_lbl = t.cell(idx, 0)
        c_val = t.cell(idx, 1)

        c_lbl.width = col_widths[0]
        c_val.width = col_widths[1]

        set_cell_background(c_lbl, HEX_SUBHEADER_BG if idx % 2 == 1 else "FFFFFF")
        set_cell_background(c_val, HEX_ALT_ROW if idx % 2 == 1 else "FFFFFF")

        set_cell_margins(c_lbl, 90, 90, 120, 120)
        set_cell_margins(c_val, 90, 90, 120, 120)

        p_lbl = c_lbl.paragraphs[0]
        format_paragraph(p_lbl, space_before=0, space_after=0)
        r_lbl = p_lbl.add_run(label)
        r_lbl.font.name = "Calibri"
        r_lbl.font.size = Pt(9.5)
        r_lbl.font.bold = True
        r_lbl.font.color.rgb = COLOR_PRIMARY

        p_val = c_val.paragraphs[0]
        format_paragraph(p_val, space_before=0, space_after=0)
        
        lines = content.strip().split("\n")
        for line_idx, line in enumerate(lines):
            if line_idx > 0:
                p_val = c_val.add_paragraph()
                format_paragraph(p_val, space_before=0, space_after=2)
            r_val = p_val.add_run(line)
            r_val.font.name = "Calibri"
            r_val.font.size = Pt(9.5)
            r_val.font.color.rgb = COLOR_TEXT

    # Add spacing after table
    p_after = doc.add_paragraph()
    format_paragraph(p_after, space_before=0, space_after=8)

def build_capstone_use_case_docx():
    doc = Document()

    # 1-inch margins all around
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Document Header
    title_p = doc.add_paragraph()
    format_paragraph(title_p, space_before=0, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
    r_title = title_p.add_run("CHAPTER 3: SYSTEM DESIGN AND METHODOLOGY")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(15)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    sub_p = doc.add_paragraph()
    format_paragraph(sub_p, space_before=0, space_after=16, align=WD_ALIGN_PARAGRAPH.CENTER)
    r_sub = sub_p.add_run("3.3 Use Case Modeling and Functional Specifications\nBon Laundry Station Management System with Predictive Analytics")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(11)
    r_sub.font.italic = True
    r_sub.font.color.rgb = COLOR_MUTED

    # -------------------------------------------------------------
    # 3.3.1 OVERVIEW OF USE CASE MODELING
    # -------------------------------------------------------------
    add_heading_1(doc, "3.3.1 Overview of Use Case Modeling")
    add_body_p(
        doc,
        "Use case modeling serves as the behavioral foundation of the proposed Bon Laundry Station Management System. "
        "It formally captures the functional requirements, operational interactions, and business services provided by the system "
        "from the direct perspective of its end-users. The diagram and its accompanying specifications adhere strictly to the "
        "Object Management Group (OMG) Unified Modeling Language (UML 2.5) standard, applying formal principles of software engineering "
        "to ensure clarity, traceability, and architectural rigor for academic capstone presentation and technical defense."
    )

    add_body_p(
        doc,
        "In accordance with modern software design guidelines, the following fundamental rules of use case modeling were strictly enforced:",
        bold_prefix="Core Rules Applied in Use Case Formulation: "
    )

    rules = [
        ("1. Explicit System Boundary: ", "The system boundary is clearly demarcated by a labeled rectangle representing the internal software scope. All human actors reside outside the boundary, while all functional goals (use cases) are contained within."),
        ("2. Standard Actor Semantics: ", "Actors represent external entities or human roles that initiate or participate in system tasks. Individual identities, job titles, and internal hardware are avoided. Human actors are rendered using standard stick-figure notation."),
        ("3. Goal-Oriented Verb-Noun Phrasing: ", "Every use case oval represents an observable result of business value to an actor and is named using an active verb followed by a concise noun phrase (e.g., 'Book Laundry Service', 'Process Walk-in POS Job Order', 'Forecast Peak Demand Hours')."),
        ("4. Association Communication Paths: ", "Solid, undirected lines indicate bidirectional communication between an actor and a use case. Simple association lines do not possess arrowheads, confirming that actors and use cases engage in two-way information exchange."),
        ("5. Strict Dependency Stereotypes («include» vs. «extend»): ", "The «include» dependency (dashed arrow pointing from base to included use case) models compulsory sub-tasks that are unconditionally executed. The «extend» dependency (dashed arrow pointing from extending to base use case) represents optional or conditional behaviors activated only at explicit extension points."),
        ("6. Role Generalization / Inheritance: ", "Generalization relationships (solid line with an open hollow triangle pointing to the parent role) are applied across management roles (Super Admin inherits Manager, who in turn inherits Staff), ensuring that managerial actors inherently possess operational floor capabilities without duplicating communication links."),
        ("7. Architectural Scope & Bot Exclusion: ", "Third-party automated chat bots (e.g., Telegram bot) have been explicitly excluded from the system boundary. Operational automation is natively achieved via responsive mobile web interfaces, optical QR code validation, and direct transactional SMS alerts (PhilSMS), preventing external API failure points.")
    ]

    for prefix, body in rules:
        add_body_p(doc, body, bold_prefix=prefix)

    # -------------------------------------------------------------
    # 3.3.2 ACTOR IDENTIFICATION AND HIERARCHY
    # -------------------------------------------------------------
    add_heading_1(doc, "3.3.2 Actor Identification and Role Hierarchy")
    add_body_p(
        doc,
        "The proposed system identifies four primary human actors interacting within the operational environment of Bon Laundry Station "
        "(Urban Deca Homes Ortigas). The system leverages an inheritance structure where supervisory and administrative roles "
        "inherit operational privileges from the floor staff, establishing a clear separation of concerns."
    )

    # Actor Table
    t_act = doc.add_table(rows=5, cols=4)
    t_act.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_act)

    act_headers = ["Actor Name", "Role Category", "Operational Description", "Associated Core Use Cases"]
    hdr_widths = [Inches(1.2), Inches(1.1), Inches(2.3), Inches(1.9)]

    for col_idx, h_text in enumerate(act_headers):
        c = t_act.cell(0, col_idx)
        c.width = hdr_widths[col_idx]
        set_cell_background(c, HEX_HEADER_BG)
        set_cell_margins(c, 100, 100, 110, 110)
        p = c.paragraphs[0]
        format_paragraph(p, space_before=0, space_after=0)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    actors_data = [
        ("Customer", "Primary\n(Human)", "Residential client of Urban Deca Homes Ortigas. Interacts via public web portal without mandatory account registration (guest model).", "Book Laundry Service, Track Live Order & Queue, View Machine Lobby & Traffic, Settle Payment."),
        ("Staff", "Primary\n(Human)", "Front-desk cashier and laundry floor operator. Authenticates via Google Single Sign-On (SSO) or internal credentials.", "Verify QR Code, Process POS Job Orders, Manage Online Appointments, Dispatch Queue, Operate Machines, Update Fleet Status."),
        ("Manager", "Secondary\n(Supervisor)", "Store supervisor with supervisory authority. Inherits all Staff privileges (Manager ──▷ Staff). Oversees business reconciliation and ML insights.", "Access Operations Dashboard & ML Rush Forecast, Manage Habitual Predictive Slots, Reconcile Sales History, Monitor Audit Trail."),
        ("Super Admin", "Secondary\n(Executive)", "Business owner and chief system administrator. Inherits all Manager privileges (Super Admin ──▷ Manager ──▷ Staff). Controls core configurations.", "Switch View Mode Perspective, Manage Staff Accounts (Google SSO), Configure Pricing, Tariffs & Fleet Settings.")
    ]

    for row_idx, data in enumerate(actors_data, start=1):
        for col_idx, text in enumerate(data):
            c = t_act.cell(row_idx, col_idx)
            c.width = hdr_widths[col_idx]
            set_cell_background(c, HEX_ALT_ROW if row_idx % 2 == 1 else "FFFFFF")
            set_cell_margins(c, 80, 80, 100, 100)
            p = c.paragraphs[0]
            format_paragraph(p, space_before=0, space_after=0)
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            r.font.color.rgb = COLOR_TEXT

    p_sp = doc.add_paragraph()
    format_paragraph(p_sp, space_before=0, space_after=10)

    # -------------------------------------------------------------
    # 3.3.3 USE CASE DIAGRAM
    # -------------------------------------------------------------
    add_heading_1(doc, "3.3.3 System Use Case Diagram")
    add_body_p(
        doc,
        "Figure 16 illustrates the complete UML 2.5 Use Case Diagram for the proposed Bon Laundry Station Management System. "
        "The diagram visualizes the behavioral relationships between the four human actors and the twenty-three functional use cases, "
        "highlighting mandatory inclusion routines, optional extensions, and payment generalizations."
    )

    # Embed Figure
    if IMG_PATH.exists():
        fig_p = doc.add_paragraph()
        format_paragraph(fig_p, space_before=6, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
        fig_run = fig_p.add_run()
        fig_run.add_picture(str(IMG_PATH), width=Inches(6.5))

        cap_p = doc.add_paragraph()
        format_paragraph(cap_p, space_before=2, space_after=12, align=WD_ALIGN_PARAGRAPH.CENTER)
        r_cap = cap_p.add_run("Figure 16. UML Use Case Diagram for Bon Laundry Station Management System with Predictive Analytics")
        r_cap.font.name = "Calibri"
        r_cap.font.size = Pt(10)
        r_cap.font.bold = True
        r_cap.font.color.rgb = COLOR_PRIMARY
    else:
        add_body_p(doc, "[FIGURE 16: UML Use Case Diagram - Place Image Here]", bold_prefix="Note: ")

    add_body_p(
        doc,
        "As depicted in Figure 16, the system architecture organizes operational capabilities into cohesive subsystems:",
        bold_prefix="Architectural Narrative: "
    )

    subsystems_narrative = [
        ("• Customer Subsystem (Self-Service Portal): ", "Residents interact directly with 'Book Laundry Service / Online Appointment', 'Track Live Order & Queue', and 'View Machine Fleet Lobby & Traffic Indicator'. The booking flow mandates ('«include»') dynamic calculation of service fees and queue EWT slots, while order tracking allows an optional ('«extend»') self-service cancellation before machine cycles commence."),
        ("• Payment Processing Subsystem: ", "'Pay for Order' is modeled as an abstract base transaction interface included by both online bookings and walk-in counter POS orders. It is specialized via UML generalization into 'Pay Online (GCash / Maya / Card)' and 'Pay Cash on Counter / COD'."),
        ("• Staff Floor Operations Subsystem: ", "Staff members execute seven dedicated floor use cases ranging from optical QR code verification (<15 seconds counter intake) and walk-in POS job order processing, to machine timer dispatching, fleet status updating, and final order handover."),
        ("• Supervisory Predictive Analytics Subsystem: ", "The Store Manager accesses operational dashboards embedded with 2nd-Degree Polynomial Regression demand forecasting (evaluated via Mean Absolute Percentage Error, MAPE), manages habitual predictive slots for recurrent resident routines, reconciles daily drawer tallies, and audits chronological staff logs."),
        ("• System Administration Subsystem: ", "The Super Admin leverages executive utilities including the dynamic View Mode Perspective Switcher (enabling instant viewport transitions between Admin, Manager, Staff, and Customer for live quality assurance), staff Google SSO pre-registration, and system tariff configurations.")
    ]

    for prefix, body in subsystems_narrative:
        add_body_p(doc, body, bold_prefix=prefix)

    # -------------------------------------------------------------
    # 3.3.4 FORMAL USE CASE SPECIFICATIONS
    # -------------------------------------------------------------
    add_heading_1(doc, "3.3.4 Formal Use Case Specifications")
    add_body_p(
        doc,
        "To provide thorough technical specifications for software developers, testers, and academic evaluation panels, "
        "the following tables document the detailed narrative specifications for each core use case in accordance with the "
        "Cockburn / IEEE standard format."
    )

    # Spec 1: UC-01
    create_spec_table(
        doc,
        "UC-01", "Book Laundry Service / Online Appointment",
        "Customer (Resident of Urban Deca Homes Ortigas)",
        "Allows residential clients to schedule self-service or full-service laundry appointments online, "
        "specifying per-load service tiers, detergent and softener preferences per machine, and delivery mode.",
        "Resident accesses the Bon Laundry Station customer web portal via web browser; system pricing rules are active.",
        "A pending laundry job order is created in the database with a unique alphanumeric reference code and optical QR code; "
        "Estimated Waiting Time (EWT) is projected.",
        "Resident navigates to the booking section of the customer portal and clicks 'Book Appointment'.",
        "1. System displays service booking form with load customization options.\n"
        "2. Customer specifies contact details (Name, Condo Building/Unit, Mobile Phone Number).\n"
        "3. Customer selects service type (Wash & Dry, Wash Only, Dry Only) and sets load count.\n"
        "4. Customer customizes detergent and fabric softener selections per allocated machine load.\n"
        "5. Customer selects service fulfillment method (Doorstep Condo Pickup & Delivery or Self Drop-off at Station).\n"
        "6. System invokes «include» Calculate Service Price & Queue EWT Slot (UC-04).\n"
        "7. System invokes «include» Pay for Order (UC-05).\n"
        "8. Customer submits the booking request.\n"
        "9. System saves appointment record, issues Order Reference Code and QR code, and sends confirmation SMS.",
        "4a. Machine Fleet at maximum operational capacity:\n"
        "    1. System alerts customer of high queue density and displays projected delay.\n"
        "    2. Customer accepts projected slot or chooses alternate schedule.\n"
        "8a. Missing required contact or unit information:\n"
        "    1. System highlights invalid input fields and halts submission until resolved.",
        "«include» UC-04: Calculate Service Price & Queue EWT Slot\n«include» UC-05: Pay for Order"
    )

    # Spec 2: UC-02
    create_spec_table(
        doc,
        "UC-02", "Track Live Order & Queue Milestone",
        "Customer (Resident)",
        "Enables clients to monitor the real-time operational status and queue progression of their laundry garments "
        "through a synchronized four-step progress tracker.",
        "Order reference code exists in the database.",
        "Customer views current milestone (Order Received, In Queue, In Progress [Washing/Drying], Ready for Pickup/Delivery).",
        "Customer inputs order reference code in portal search or scans ticket QR code.",
        "1. Customer enters order tracking code or clicks tracking link from SMS.\n"
        "2. System retrieves order status, assigned machine units, and countdown timers.\n"
        "3. System renders active milestone stepper highlighting current laundry stage.\n"
        "4. System displays projected ready time and floor operator notes.",
        "2a. Order reference code not found:\n"
        "    1. System displays 'Invalid Reference Code' error message and prompts retry.\n"
        "3a. Customer elects to cancel pending order:\n"
        "    1. System invokes «extend» Request Order Cancellation (UC-03) if processing has not started.",
        "«extend» UC-03: Request Order Cancellation (Extension Point: Order not yet in wash cycle)"
    )

    # Spec 3: UC-03
    create_spec_table(
        doc,
        "UC-03", "Request Order Cancellation",
        "Customer (Resident)",
        "Permits customers to cancel a previously scheduled laundry appointment prior to physical intake or machine loading.",
        "Order exists in 'Pending' or 'In Queue' status; machine washing cycle has not been initiated.",
        "Order status is transitioned to 'Cancelled'; allocated machine queue slot is released; cancellation audit event logged.",
        "Customer clicks 'Cancel Order' button from the live order tracking viewport.",
        "1. Customer clicks 'Cancel Order' on tracking screen.\n"
        "2. System verifies that garments have not entered active wash cycle.\n"
        "3. System prompts customer to confirm cancellation reason.\n"
        "4. Customer confirms cancellation request.\n"
        "5. System updates order state to 'Cancelled', updates queue, and notifies customer via SMS.",
        "2a. Garments already loaded in washer or in-progress:\n"
        "    1. System disables cancellation and displays alert: 'Cannot cancel order currently in processing. Please contact staff directly.'",
        "Extends UC-02: Track Live Order & Queue"
    )

    # Spec 4: UC-04
    create_spec_table(
        doc,
        "UC-04", "Calculate Service Price & Queue EWT Slot",
        "System (Automated Functional Service)",
        "Automatically calculates total billing amount based on load weight/quantity, premium detergent add-ons, "
        "and condo doorstep delivery surcharges, while projecting queue Estimated Waiting Time (EWT).",
        "Pricing tariff matrix and live machine utilization metrics are loaded.",
        "Itemized bill breakdown and EWT time slot are returned to the calling use case.",
        "Invoked unconditionally by Book Laundry Service (UC-01).",
        "1. System inspects selected wash/dry tier and number of loads.\n"
        "2. System queries active machine fleet to calculate current cycle completion times.\n"
        "3. System adds add-on supply tariffs (detergent, fabric softener) and delivery fee.\n"
        "4. System calculates cumulative Estimated Waiting Time (EWT) based on active queue backlog.\n"
        "5. System returns total price and EWT to the customer booking form.",
        "None (Compulsory mathematical routine).",
        "Included by UC-01: Book Laundry Service / Online Appointment"
    )

    # Spec 5: UC-05
    create_spec_table(
        doc,
        "UC-05", "Pay for Order",
        "Customer (Resident) / Staff (Cashier)",
        "Abstract generalized transaction use case that handles settlement of laundry service fees, "
        "specialized into digital online payment or cash on counter/COD.",
        "Validated job order total has been calculated.",
        "Payment status updated to 'Paid' or 'Pending Cash Collection'; receipt record generated.",
        "Customer checks out online or Staff closes job order at POS counter.",
        "1. System presents payment options (Pay Online or Pay Cash).\n"
        "2. User selects payment channel.\n"
        "3. System delegates execution to specialized payment use case (UC-06 or UC-07).\n"
        "4. System records transaction reference and marks order payment status.",
        "3a. Transaction declined or cancelled by payment gateway:\n"
        "    1. System prompts user to retry or select cash on counter.",
        "Generalizes into UC-06 (Pay Online) and UC-07 (Pay Cash)\nIncluded by UC-01 (Booking) and UC-09 (POS)"
    )

    # Spec 6: UC-08
    create_spec_table(
        doc,
        "UC-08", "Verify Order QR Code & Counter Check-In",
        "Staff (Cashier / Front-Desk)",
        "Enables front-desk staff to rapidly verify arriving laundry bags against online booking records "
        "using optical QR scanning or alphanumeric order lookup in under 15 seconds.",
        "Staff is authenticated in Staff Portal; customer presents QR ticket or booking code.",
        "Order status transitions from 'Booked' to 'Received / Checked-In'; laundry bags tagged for floor dispatch.",
        "Staff scans customer QR code using integrated counter camera or enters code manually.",
        "1. Staff activates counter scanner or enters 6-character order code.\n"
        "2. System displays matched booking details, resident condo unit, and load configurations.\n"
        "3. Staff inspects physical garment bags and confirms piece/weight count.\n"
        "4. Staff confirms check-in.\n"
        "5. System updates order state to 'Received' and queues job for machine allocation.",
        "2a. QR code unreadable or expired:\n"
        "    1. Staff searches by customer phone number or resident name.\n"
        "3a. Physical garment count exceeds booked load specifications:\n"
        "    1. Staff updates load count and system recalculates balance.",
        "Direct Association: Staff"
    )

    # Spec 7: UC-09
    create_spec_table(
        doc,
        "UC-09", "Process Walk-in POS Job Order",
        "Staff (Cashier)",
        "Facilitates rapid counter intake for walk-in residents who drop off laundry without prior online appointment.",
        "Staff is logged into POS terminal.",
        "Walk-in job order logged, laundry tagged, payment collected, and order queued for floor dispatch.",
        "Walk-in resident approaches counter with laundry.",
        "1. Staff initiates 'New Walk-in Order' in POS module.\n"
        "2. Staff inputs customer name, phone number, and condo unit.\n"
        "3. Staff invokes «include» Validate Garment Weight & Calculate Load Fee (UC-10).\n"
        "4. Staff selects wash/dry package and customer detergent preferences.\n"
        "5. Staff invokes «include» Pay for Order (UC-05) to collect cash or QR Ph payment.\n"
        "6. System generates printed physical receipt and SMS job ticket.",
        "5a. Customer requests partial downpayment / COD:\n"
        "    1. Staff records downpayment; balance flagged for settlement upon pickup.",
        "«include» Validate Garment Weight\n«include» UC-05: Pay for Order"
    )

    # Spec 8: UC-13
    create_spec_table(
        doc,
        "UC-13", "Access Store Operations Dashboard & ML Rush Forecast",
        "Manager (Store Supervisor)",
        "Provides store supervisors with operational oversight and machine learning predictions of hourly store rush, "
        "utilizing a 2nd-Degree Polynomial Regression model evaluated against Mean Absolute Percentage Error (MAPE).",
        "Manager is authenticated with supervisory role credentials.",
        "Manager reviews active shop metrics, queue throughput, and predictive peak hour demand curves.",
        "Manager navigates to the Operations Dashboard tab.",
        "1. Manager accesses dashboard.\n"
        "2. System aggregates real-time metrics: active orders, pending pickups, and idle machines.\n"
        "3. System executes 2nd-degree polynomial regression pipeline on historical order telemetry.\n"
        "4. System displays predicted rush hours (e.g., peak demand at 6:00 PM - 8:00 PM) alongside model MAPE validation score.\n"
        "5. Manager adjusts staff floor schedules and machine pre-allocations accordingly.",
        "3a. Insufficient historical training records (<14 days):\n"
        "    1. System displays baseline moving average while continuing automated model training.",
        "Direct Association: Manager (Supervisory Role)"
    )

    # Spec 9: UC-18
    create_spec_table(
        doc,
        "UC-18", "Switch View Mode Perspective",
        "Super Admin (Business Owner)",
        "Provides the business owner with a dynamic viewport switcher to transition seamlessly between Super Admin, "
        "Manager, Staff, and Customer interfaces without requiring repeated logins.",
        "User is logged in with Super Admin executive permissions.",
        "Application viewport adjusts to simulate the selected user perspective with corresponding UI elements and constraints.",
        "Super Admin selects a role perspective from the top navigation role switcher dropdown.",
        "1. Super Admin opens Role Perspective dropdown menu.\n"
        "2. Super Admin selects target role (e.g., 'Staff View' or 'Customer View').\n"
        "3. System temporarily adjusts session context and renders target interface without re-authenticating.\n"
        "4. Super Admin inspects operational usability, verifies live staff queues, or tests customer booking flow.\n"
        "5. Super Admin clicks 'Exit View Mode' to return to master Super Admin panel.",
        "None (Internal diagnostic utility).",
        "Direct Association: Super Admin"
    )

    # Spec 10: UC-20
    create_spec_table(
        doc,
        "UC-20", "Configure Pricing, Tariffs & Fleet Settings",
        "Super Admin (Business Owner)",
        "Empowers the business owner to maintain master pricing structures, add-on costs, condo delivery surcharges, "
        "and machine fleet capacity specifications.",
        "Super Admin authenticated with administrative privileges.",
        "Master system tariffs and hardware parameters updated across all calculation engines.",
        "Super Admin navigates to 'System Settings' panel.",
        "1. Super Admin accesses Pricing & Fleet Settings.\n"
        "2. Super Admin updates base wash/dry tier pricing (e.g., 8kg Wash & Dry rate).\n"
        "3. Super Admin updates detergent and fabric softener unit tariffs.\n"
        "4. Super Admin adjusts condo doorstep pickup/delivery surcharges.\n"
        "5. Super Admin saves updated parameters.\n"
        "6. System validates inputs and broadcasts updated tariffs across POS and booking engines.",
        "2a. Invalid non-numeric or negative price entered:\n"
        "    1. System flags error and prevents database update.",
        "Direct Association: Super Admin"
    )

    # Save document
    try:
        doc.save(str(DOC_PATH))
        print(f"Successfully created Capstone Use Case Documentation at: {DOC_PATH}")
    except PermissionError:
        fallback_path = DOC_PATH.parent / "CAPSTONE_USE_CASE_DOCUMENTATION_UPDATED.docx"
        doc.save(str(fallback_path))
        print(f"Original file was open in Word. Successfully created updated document at: {fallback_path}")

if __name__ == "__main__":
    build_capstone_use_case_docx()
