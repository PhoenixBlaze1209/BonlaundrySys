# routes/dashboard.py
import re
import secrets
import urllib.parse
from io import BytesIO
from datetime import datetime, time, timedelta
from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request, Response
from config.database import SessionLocal
from models.schemas import SystemSettings, Queue
from models.schemas import Appointment, Queue, User
from services.analytics_engine import AnalyticsEngine
from services.queuing import QueueManager
from models.schemas import Transaction, PredictionLog, MachineStatus
from sqlalchemy import func, or_, case
from services.machines import (
    refresh_machine_cycles, is_machine_available, start_machine_cycle,
    start_next_queued_job, recommend_machine_for_order, estimated_wait_for_machine,
    is_walkin_machine, parse_order_loads, service_tier, queue_cycle_type, begin_dry_stage,
    package_includes_dry, is_bulky_garment_category
)
from services.email_service import EmailService
from decimal import Decimal
from services.rbac import has_role, Role
from services.audit_service import AuditService, AuditAction
from services.payments import compute_service_price, validate_counter_payment, apply_counter_payment

dashboard_bp = Blueprint('dashboard', __name__)


def _pdf_safe_text(value):
    """Keep report values compatible with the built-in PDF Helvetica font."""
    text = str(value or '')
    return text.encode('latin-1', 'replace').decode('latin-1').replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _build_sales_tally_pdf(rows, generated_at):
    """Create a dependency-free, print-ready PDF sales report."""
    page_width, page_height = 792, 612  # US letter, landscape
    margin, footer_y = 36, 28
    streams, commands, page_number, cursor_y = [], [], 0, page_height - 44

    def text(x, y, size, value, bold=False, color=None):
        face = 'F2' if bold else 'F1'
        color_cmd = '' if color is None else f'{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg '
        commands.append(f'BT {color_cmd}/{face} {size} Tf 1 0 0 1 {x} {y} Tm ({_pdf_safe_text(value)}) Tj ET')

    def line(x1, y1, x2, y2, width=0.5, color=(0.82, 0.84, 0.83)):
        commands.append(f'{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} RG {width} w {x1} {y1} m {x2} {y2} l S')

    def rect(x, y, width, height, color):
        commands.append(f'{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg {x} {y} {width} {height} re f')

    def new_page():
        nonlocal commands, page_number, cursor_y
        if commands:
            text(margin, footer_y, 8, 'Bon Laundry Station  |  Confidential operational report', color=(0.35, 0.40, 0.42))
            text(page_width - 92, footer_y, 8, f'Page {page_number}', color=(0.35, 0.40, 0.42))
            streams.append('\n'.join(commands))
        page_number += 1
        commands, cursor_y = [], page_height - 44
        rect(0, page_height - 30, page_width, 30, (0.075, 0.145, 0.192))
        text(margin, page_height - 20, 13, 'BON LAUNDRY STATION', bold=True, color=(1, 1, 0.98))
        text(page_width - 212, page_height - 20, 8, 'SALES & TALLY REPORT', bold=True, color=(0.82, 0.91, 0.94))

    def section_heading(title):
        nonlocal cursor_y
        if cursor_y < 74:
            new_page()
        text(margin, cursor_y, 11, title.upper(), bold=True, color=(0.075, 0.145, 0.192))
        line(margin, cursor_y - 5, page_width - margin, cursor_y - 5, 0.8, (0.05, 0.43, 0.61))
        cursor_y -= 22

    def table(headers, widths, data, alignments=None):
        nonlocal cursor_y
        alignments = alignments or ['left'] * len(headers)

        def draw_header():
            nonlocal cursor_y
            if cursor_y < 66:
                new_page()
            rect(margin, cursor_y - 14, sum(widths), 18, (0.92, 0.92, 0.89))
            x = margin
            for header, width in zip(headers, widths):
                text(x + 4, cursor_y - 8, 7, header.upper(), bold=True, color=(0.28, 0.33, 0.34))
                x += width
            cursor_y -= 20

        draw_header()
        for row in data:
            if cursor_y < 52:
                new_page()
                draw_header()
            x = margin
            for value, width, alignment in zip(row, widths, alignments):
                raw = _pdf_safe_text(value)
                clipped = raw if len(raw) <= max(1, int(width / 4.1)) else raw[:max(1, int(width / 4.1) - 1)] + '...'
                estimated_width = len(clipped) * 4.0
                tx = x + 4 if alignment == 'left' else x + max(4, width - estimated_width - 4)
                text(tx, cursor_y, 7.5, clipped, color=(0.10, 0.15, 0.16))
                x += width
            line(margin, cursor_y - 5, page_width - margin, cursor_y - 5)
            cursor_y -= 16

    total_sales = sum(float(tx.total_amount or 0) for tx, _ in rows)
    paid_sales = sum(float(tx.total_amount or 0) for tx, _ in rows if tx.payment_status == 'Paid')
    pending_sales = total_sales - paid_sales
    total_weight = sum(float(tx.weight_kg or 0) for tx, _ in rows)
    daily = {}
    for tx, _ in rows:
        tx_date = tx.created_at.date() if tx.created_at else None
        if not tx_date:
            continue
        record = daily.setdefault(tx_date, {'orders': 0, 'weight': 0.0, 'paid': 0.0, 'pending': 0.0, 'gross': 0.0})
        amount = float(tx.total_amount or 0)
        record['orders'] += 1
        record['weight'] += float(tx.weight_kg or 0)
        record['gross'] += amount
        record['paid' if tx.payment_status == 'Paid' else 'pending'] += amount

    new_page()
    text(margin, cursor_y, 18, 'Sales & Tally Report', bold=True, color=(0.075, 0.145, 0.192))
    text(margin, cursor_y - 15, 8, f'Generated {generated_at.strftime("%B %d, %Y at %I:%M %p")}', color=(0.35, 0.40, 0.42))
    cursor_y -= 42
    section_heading('Report Summary')
    summary = [
        ('Total receipts', str(len(rows))),
        ('Total load weight', f'{total_weight:,.2f} kg'),
        ('Paid collected', f'PHP {paid_sales:,.2f}'),
        ('Pending / unpaid', f'PHP {pending_sales:,.2f}'),
        ('Gross sales', f'PHP {total_sales:,.2f}'),
    ]
    table(['Measure', 'Value'], [290, 240], summary, ['left', 'right'])
    cursor_y -= 10
    section_heading('Daily Reconciliation')
    daily_data = [
        (day.strftime('%b %d, %Y'), value['orders'], f"{value['weight']:,.2f} kg", f"PHP {value['paid']:,.2f}", f"PHP {value['pending']:,.2f}", f"PHP {value['gross']:,.2f}", 'Balanced' if value['pending'] == 0 else 'Pending')
        for day, value in sorted(daily.items(), reverse=True)
    ] or [('No recorded sales', '', '', '', '', '', '')]
    table(['Date', 'Orders', 'Weight', 'Paid', 'Pending', 'Gross', 'Status'], [130, 55, 75, 95, 95, 95, 70], daily_data, ['left', 'right', 'right', 'right', 'right', 'right', 'left'])
    cursor_y -= 10
    section_heading('Itemized Receipts Ledger')
    ledger_data = [
        (
            tx.created_at.strftime('%Y-%m-%d %I:%M %p') if tx.created_at else '—',
            f'TRX-{tx.transaction_id:04d}',
            name or tx.customer_name or 'Walk-in customer',
            f'{float(tx.weight_kg or 0):.2f} kg / {tx.cycle_type or "washing"}',
            f'{tx.payment_status or "—"} / {tx.payment_method or "—"}',
            tx.processed_by or '—',
            f'PHP {float(tx.total_amount or 0):,.2f}',
        )
        for tx, name in rows
    ] or [('No recorded receipts', '', '', '', '', '', '')]
    table(['Date & Time', 'Receipt', 'Customer', 'Load', 'Payment', 'Handled by', 'Amount'], [110, 62, 120, 105, 100, 100, 73], ledger_data, ['left', 'left', 'left', 'left', 'left', 'left', 'right'])
    new_page()

    # Assemble a valid PDF document with standard Type 1 Helvetica fonts.
    page_object_start = 5
    objects = [
        '<< /Type /Catalog /Pages 2 0 R >>',
        f'<< /Type /Pages /Kids [{" ".join(f"{page_object_start + i} 0 R" for i in range(len(streams)))}] /Count {len(streams)} >>',
        '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>',
    ]
    content_object_start = page_object_start + len(streams)
    for index, _ in enumerate(streams):
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_object_start + index} 0 R >>')
    for stream in streams:
        objects.append(f'<< /Length {len(stream.encode("latin-1"))} >>\nstream\n{stream}\nendstream')

    output = BytesIO()
    output.write(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f'{index} 0 obj\n{obj}\nendobj\n'.encode('latin-1'))
    xref = output.tell()
    output.write(f'xref\n0 {len(objects) + 1}\n0000000000 65535 f \n'.encode('ascii'))
    for offset in offsets[1:]:
        output.write(f'{offset:010d} 00000 n \n'.encode('ascii'))
    output.write(f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode('ascii'))
    return output.getvalue()


def _has_role(*roles):
    return has_role(*roles)


def _api_access(*roles):
    if not _has_role(*roles):
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    return None


def _generate_counter_order_code(db):
    """Create a short, staff-friendly reference that can be used at verification."""
    for _ in range(10):
        code = f"ORD-{secrets.randbelow(90000) + 10000}"
        if not db.query(Appointment).filter(Appointment.order_code == code).first():
            return code
    return f"ORD-{secrets.randbelow(900000) + 100000}"


def _dashboard_metrics(db, include_revenue=False):
    """Returns live operational values derived from persisted POS/queue data."""
    refresh_machine_cycles(db)
    active_queue = db.query(Queue).filter(
        Queue.status.in_(['Waiting', 'Processing']),
        or_(Queue.verified_at.isnot(None), Queue.appointment_id.is_(None))
    ).count()
    machines = db.query(MachineStatus).all()
    ready_machines = sum(1 for machine in machines if is_machine_available(machine))
    total_machines = db.query(MachineStatus).count()
    total_capacity_kg = int(db.query(func.coalesce(func.sum(MachineStatus.capacity_kg), 0)).scalar())
    running_machines = sum(1 for machine in machines if machine.cycle_type in ('washing', 'drying'))
    estimated_wait = QueueManager.calculate_current_ewt(db)

    data = {
        "active_queue": active_queue,
        "est_wait_time_mins": estimated_wait,
        "machines_ready": ready_machines,
        "machines_running": running_machines,
        "total_machines": total_machines,
        "total_capacity_kg": total_capacity_kg,
    }
    if include_revenue:
        today_start = datetime.combine(datetime.today().date(), time.min)
        data["today_revenue_php"] = float(
            db.query(func.coalesce(func.sum(Transaction.total_amount), 0))
            .filter(Transaction.created_at >= today_start, Transaction.payment_status == 'Paid')
            .scalar()
        )
    return data


def _live_activity(db):
    now = datetime.now()
    pay_order = case(
        (func.coalesce(Queue.payment_status, Appointment.payment_status) != 'Paid', 1),
        else_=2
    )
    rows = (db.query(Queue, Appointment, User, MachineStatus)
            .outerjoin(Appointment, Queue.appointment_id == Appointment.appointment_id)
            .outerjoin(User, Appointment.customer_id == User.user_id)
            .outerjoin(MachineStatus, Queue.machine_id == MachineStatus.machine_id)
            .filter(Queue.status.in_(['Waiting', 'Processing']))
            .order_by(pay_order.asc(), Queue.queue_number.asc()).limit(15).all())
    
    activity_data = []
    for queue, appointment, user, machine in rows:
        is_verified = (queue.verified_at is not None) or (queue.appointment_id is None)
        wait_elapsed = max(0, int((now - queue.verified_at).total_seconds() / 60)) if queue.verified_at else 0
        rem_wait = max(0, (queue.estimated_waiting_time or 0) - wait_elapsed) if (queue.status == 'Waiting' and is_verified) else (queue.estimated_waiting_time or 0)
        activity_data.append({
            "job_id": f"Q-{queue.queue_number:03d}",
            "queue_number": queue.queue_number,
            "appointment_id": queue.appointment_id,
            "order_code": appointment.order_code if appointment else f"Q-{queue.queue_number:03d}",
            "customer": queue.customer_name or (user.name if user else "Walk-in customer"),
            "phone": appointment.phone_number if appointment else "—",
            "address": appointment.address if appointment else "—",
            "service_type": appointment.service_type if appointment else "Walk-in",
            "status": ("Drying" if queue.cycle_stage == 'drying' else "Washing") if queue.status == 'Processing' else "Waiting",
            "cycle_stage": queue.cycle_stage or 'washing',
            "service_tier": service_tier(appointment.service_type if appointment else None),
            "turnaround_option": None if ('self' in (queue.order_mode or (appointment.order_mode if appointment else '') or '').lower() or 'self' in (appointment.service_type if appointment else '').lower()) else (queue.turnaround_option or (appointment.turnaround_option if appointment else '24 Hours') or '24 Hours'),
            "priority_level": queue.priority_level or (appointment.priority_level if appointment else 'Standard') or 'Standard',
            "order_mode": queue.order_mode or (appointment.order_mode if appointment else ('Self-Service' if ('self' in (queue.order_mode or (appointment.order_mode if appointment else '') or '').lower() or 'self' in (appointment.service_type if appointment else '').lower()) else 'Drop-Off')) or 'Drop-Off',
            "payment_method": queue.payment_method or (appointment.payment_method if appointment else 'Cash') or 'Cash',
            "payment_status": queue.payment_status or (appointment.payment_status if appointment else 'Pending') or 'Pending',
            "fulfillment_status": queue.fulfillment_status or (appointment.fulfillment_status if appointment else 'Received') or 'Received',
            "load_details": queue.load_details or (appointment.load_details if appointment else "") or "",
            "total_machines": queue.total_machines or (appointment.total_machines if appointment else 1) or 1,
            "machine": (machine.machine_name or f"Machine {machine.machine_id} (Dryer and Washer)") if machine else "Unassigned",
            "is_verified": is_verified,
            "wait_elapsed_mins": wait_elapsed,
            "remaining_wait_mins": rem_wait,
            "estimated_waiting_time": queue.estimated_waiting_time or 0,
            "verified_at": queue.verified_at.strftime('%I:%M %p') if queue.verified_at else None
        })
    return activity_data

# Inside routes/dashboard.py update manager_home
@dashboard_bp.route('/manager/dashboard')
def manager_home():
    if not _has_role(Role.MANAGER, Role.SUPER_ADMIN):
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
        
    db = SessionLocal()
    try:
        total_revenue = db.query(func.sum(Transaction.total_amount)).scalar() or 0.00
        total_loads = db.query(Transaction).count()
        maintenance_machines = db.query(MachineStatus).filter(MachineStatus.status == 'Maintenance').count()

        # 1. Trigger the Machine Learning Analytics Engine pipeline
        # Persist one auditable prediction when the manager opens the dashboard;
        # the polling endpoints below intentionally do not create duplicate logs.
        forecast = AnalyticsEngine.train_and_predict_peak_hour(record_log=True)

        # 2. Fetch the historical logs table for auditing validation
        audit_logs = db.query(PredictionLog).order_by(PredictionLog.prediction_id.desc()).limit(10).all()

        return render_template(
            'manager/dashboard.html',
            manager_name=session.get('user_name'),
            total_revenue=float(total_revenue),
            total_loads=total_loads,
            maintenance_machines=maintenance_machines,
            forecast=forecast,
            audit_logs=audit_logs,
            role=session.get('user_role', 'Manager')
        )
    finally:
        db.close()


@dashboard_bp.route('/api/manager/live-forecast')
def live_forecast_api():
    # Siguraduhing tumutugma sa role verification framework ng core app mo
    denied = _api_access('Manager')
    if denied:
        return denied
        
    db = SessionLocal()
    try:
        # Hihigupin ang live data matrices mula sa bagong analytics algorithm natin
        forecast = AnalyticsEngine.train_and_predict_peak_hour()
        
        # Kakalkulahin ang live indicators para sa synchronous rendering cards
        total_revenue = db.query(func.sum(Transaction.total_amount)).scalar() or 0.00
        total_loads = db.query(Transaction).count()
        maintenance_machines = db.query(MachineStatus).filter(MachineStatus.status == 'Maintenance').count()

        return {
            "total_revenue": float(total_revenue),
            "total_loads": total_loads,
            "maintenance_machines": maintenance_machines,
            "forecast": forecast
        }
    finally:
        db.close()


@dashboard_bp.route('/api/manager/ghost-slots')
def manager_ghost_slots():
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    min_visits = request.args.get('min_visits', default=3, type=int)
    try:
        slots = AnalyticsEngine.get_ghost_slots(min_visits=min_visits)
        return jsonify({"status": "success", "data": slots, "count": len(slots)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@dashboard_bp.route('/api/manager/ghost-slots/assign', methods=['POST'])
def manager_assign_ghost_slot():
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    payload = request.get_json(silent=True) or request.form
    customer_name = (payload.get('customer_name') or '').strip()
    customer_email = (payload.get('customer_email') or '').strip() or None
    weight_kg = float(payload.get('weight_kg') or 8.0)
    cycle_type = payload.get('cycle_type') or 'washing'
    if not customer_name:
        return jsonify({"status": "error", "message": "Customer name is required."}), 400

    # A resident suggestion must be verified at the counter before it is sent
    # to a machine. Staff can revise all details in the normal checkout flow.
    if payload.get('create_verification_order'):
        db = SessionLocal()
        try:
            customer = None
            if customer_email:
                customer = db.query(User).filter(User.email == customer_email).first()
            if not customer:
                customer = db.query(User).filter(User.name == customer_name).first()

            capacity_kg = 13 if weight_kg > 8 else 8
            cycle_is_dry = str(cycle_type).lower() == 'drying'
            service_type = 'Dry Only' if cycle_is_dry else f'Self-Service {capacity_kg}kg'
            order_code = _generate_counter_order_code(db)
            appointment = Appointment(
                customer_id=customer.user_id if customer else None,
                order_code=order_code,
                customer_name=customer_name,
                customer_email=customer_email,
                schedule_time=datetime.now(),
                service_type=service_type,
                load_details=(
                    f"1 Machine ({capacity_kg}kg {'Titan' if capacity_kg == 13 else 'Regular'}) "
                    f"| Est: {weight_kg:.1f}kg | Resident counter check-in"
                ),
                estimated_weight=Decimal(str(weight_kg)).quantize(Decimal('0.01')),
                total_machines=1,
                turnaround_option='Immediate',
                priority_level='Standard',
                order_mode='Self-Service',
                payment_method='Cash',
                payment_status='Pending',
                fulfillment_status='Received',
                status='Pending'
            )
            db.add(appointment)
            db.commit()
            return jsonify({
                'status': 'success',
                'message': f'Counter order {order_code} is ready for verification.',
                'data': {
                    'order_code': order_code,
                    'appointment_id': appointment.appointment_id,
                    'verification_url': url_for('dashboard.verify_order_page', code=order_code)
                }
            }), 201
        except Exception as e:
            db.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            db.close()

    try:
        result = AnalyticsEngine.assign_ghost_slot(
            customer_name=customer_name,
            weight_kg=weight_kg,
            cycle_type=cycle_type,
            customer_email=customer_email,
            payment=payload.get('payment') if hasattr(payload, 'get') else None,
            preview=bool(payload.get('preview')) if hasattr(payload, 'get') else False,
            staff_name=session.get('user_name'),
            staff_id=session.get('user_id')
        )
        status_code = 200 if result.get("status") == "success" else (402 if result.get("code") == "payment_required" else 400)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@dashboard_bp.route('/staff/dashboard')
def staff_home():
    if not _has_role('Staff'):
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    db = SessionLocal()
    try:
        settings = db.query(SystemSettings).first()
        active_queues = db.query(Queue).filter(Queue.status != 'Done').all()
        total_loads = db.query(Transaction).count()
        maintenance_machines = db.query(MachineStatus).filter(MachineStatus.status == 'Maintenance').count()
        forecast = AnalyticsEngine.train_and_predict_peak_hour()
        audit_logs = db.query(PredictionLog).order_by(PredictionLog.prediction_id.desc()).limit(10).all()
        
        return render_template('staff/dashboard.html',
                               settings=settings,
                               active_queues=active_queues,
                               total_loads=total_loads,
                               maintenance_machines=maintenance_machines,
                               forecast=forecast,
                               audit_logs=audit_logs,
                               staff_name=session.get('user_name'),
                               role='Staff')
    finally:
        db.close()

@dashboard_bp.route('/customer/dashboard')
@dashboard_bp.route('/customer/portal')
def customer_home():
    if not session.get('user_id'):
        flash('Please sign in to access your customer portal.', 'info')
        return redirect(url_for('auth.login'))
        
    db = SessionLocal()
    try:
        user = db.get(User, session.get('user_id'))
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
            
        refresh_machine_cycles(db)
        
        # Pull all appointments linked to this customer (by ID or Email)
        appointments = (
            db.query(Appointment)
            .filter(or_(Appointment.customer_id == user.user_id, Appointment.customer_email == user.email))
            .order_by(Appointment.appointment_id.desc())
            .all()
        )
        
        # Build enriched order cards
        active_orders = []
        past_orders = []
        all_orders = []
        
        for appt in appointments:
            queue = db.query(Queue).filter(Queue.appointment_id == appt.appointment_id).first()
            machine = db.get(MachineStatus, queue.machine_id) if (queue and queue.machine_id) else None
            
            # Progress calculation
            if appt.status == 'Cancelled':
                progress_step = 0
                step_label = 'Cancelled'
            elif appt.status == 'Completed' or (queue and queue.status == 'Done'):
                progress_step = 4
                step_label = 'Ready for Pick-up / Delivered'
            elif queue and queue.status == 'Processing':
                progress_step = 3
                step_label = f"Processing ({'Drying' if machine and machine.cycle_type == 'drying' else 'Washing'})"
            elif queue and queue.status == 'Waiting':
                progress_step = 2
                step_label = f"In Queue (#{queue.queue_number})"
            else:
                progress_step = 1
                step_label = appt.fulfillment_status or 'Order Placed'
                
            is_self = 'self' in (appt.order_mode or '').lower() or 'self' in (appt.service_type or '').lower()
            order_data = {
                'appointment_id': appt.appointment_id,
                'order_code': appt.order_code or f"ORD-{appt.appointment_id:04d}",
                'service_type': appt.service_type,
                'turnaround_option': None if is_self else (appt.turnaround_option or '24 Hours'),
                'order_mode': appt.order_mode or ('Self-Service' if is_self else 'Drop-Off'),
                'payment_method': appt.payment_method or 'Cash',
                'payment_status': appt.payment_status or 'Pending',
                'fulfillment_status': appt.fulfillment_status or 'Received',
                'status': appt.status,
                'schedule_time': appt.schedule_time.strftime("%b %d, %Y %I:%M %p") if appt.schedule_time else "—",
                'progress_step': progress_step,
                'step_label': step_label,
                'queue_number': queue.queue_number if queue else None,
                'assigned_machine': (machine.machine_name or f"Machine {machine.machine_id} (Dryer and Washer)") if machine else "Auto-Allocation",
                'estimated_wait': queue.estimated_waiting_time if queue else 0,
                'load_details': appt.load_details or '',
                'total_machines': appt.total_machines or 1,
                'can_cancel': appt.status not in ('Completed', 'Cancelled') and (not queue or queue.status == 'Waiting'),
                'total_amount': float(appt.total_amount) if appt.total_amount is not None else None,
                'addons': [a.strip() for a in (appt.addons or '').split(',') if a.strip()],
                'weight': (
                    float(appt.actual_weight) if appt.actual_weight is not None else (
                        13.0 * (appt.total_machines or 1) if (('13kg' in (appt.load_details or '').lower() or 'titan' in (appt.load_details or '').lower()) and (appt.estimated_weight is None or float(appt.estimated_weight) <= 8.0)) else (
                            float(appt.estimated_weight) if appt.estimated_weight is not None else 8.0
                        )
                    )
                ),
                'cancellation_reason': appt.cancellation_reason,
                'cancelled_at': appt.cancelled_at.strftime("%b %d, %Y %I:%M %p") if appt.cancelled_at else None,
                'refund_status': appt.refund_status,
            }

            if appt.status == 'Cancelled':
                order_data['bucket'] = 'cancelled'
            elif progress_step == 4:
                order_data['bucket'] = 'completed'
            elif (appt.payment_status or 'Pending') != 'Paid' and (appt.payment_method or 'Cash') != 'Cash':
                order_data['bucket'] = 'to_pay'
            else:
                order_data['bucket'] = 'in_progress'
            all_orders.append(order_data)
            
            if appt.status in ('Completed', 'Cancelled'):
                past_orders.append(order_data)
            else:
                active_orders.append(order_data)
                
        # Machine Fleet Lobby Summary
        lobby_summary = QueueManager.get_lobby_status(db)
        machines = db.query(MachineStatus).all()
        ready_machines = sum(1 for m in machines if is_machine_available(m))
        running_machines = sum(1 for m in machines if m.cycle_type in ('washing', 'drying'))
        active_queue_count = db.query(Queue).filter(Queue.status.in_(['Waiting', 'Processing'])).count()
        est_wait = lobby_summary['ewt_mins']
        is_lobby_full = lobby_summary['is_full']
        
        # Sort machines: available first, then washers, then dryers
        machines_data = []
        for m in machines:
            free = is_machine_available(m)
            is_online = (m.operational_state == 'in_use_online')
            status_text = 'Available' if free else ('In Use (Online Order)' if is_online else ('Maintenance' if m.status == 'Maintenance' else 'In-Use (Walk-In)'))
            machines_data.append({
                'machine_id': m.machine_id,
                'machine_name': m.machine_name or f"Machine {m.machine_id} (Dryer and Washer)",
                'machine_type': m.machine_type or 'Dryer and Washer',
                'capacity_kg': m.capacity_kg,
                'status': status_text,
                'operational_state': m.operational_state,
                'cycle_type': m.cycle_type,
                'usage_count': m.usage_count,
                'price_per_cycle': float(m.price_per_cycle or 145.00),
                'is_available': free,
                'is_walkin': is_walkin_machine(m)
            })
            
        machines_data.sort(key=lambda x: (0 if x['is_available'] else 1, x['machine_id']))
        
        avatar = user.avatar_url or session.get('avatar_url') or f"https://ui-avatars.com/api/?name={urllib.parse.quote(user.name)}&background=0284c7&color=fff&rounded=true"
        
        initial_active_page = max(1, request.args.get('active_page', 1, type=int))

        return render_template(
            'customer/dashboard.html',
            user=user,
            customer_name=user.name,
            customer_email=user.email,
            avatar_url=avatar,
            active_orders=active_orders,
            past_orders=past_orders,
            all_orders=all_orders,
            active_count=len(active_orders),
            total_orders=len(appointments),
            initial_active_page=initial_active_page,
            machines=machines_data,
            ready_machines=ready_machines,
            running_machines=running_machines,
            total_machines=len(machines),
            active_queue_count=active_queue_count,
            est_wait=est_wait,
            is_lobby_full=is_lobby_full,
            lobby_summary=lobby_summary,
            role='Customer'
        )
    finally:
        db.close()


@dashboard_bp.route('/api/customer/my-orders')
def customer_my_orders_api():
    """Live API for customer portal auto-refreshing with optional status and pagination limiting."""
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Unauthorized.'}), 401
        
    db = SessionLocal()
    try:
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        
        status_filter = (request.args.get('status') or '').strip().lower()
        page = max(1, request.args.get('page', 1, type=int))
        limit = request.args.get('limit', type=int)
        
        query = (
            db.query(Appointment)
            .filter(or_(Appointment.customer_id == user_id, Appointment.customer_email == user_email))
            .order_by(Appointment.appointment_id.desc())
        )
        
        if status_filter == 'active':
            query = query.filter(Appointment.status.notin_(['Completed', 'Cancelled']))
        elif status_filter == 'past':
            query = query.filter(Appointment.status.in_(['Completed', 'Cancelled']))
            
        total_records = query.count()
        
        if limit and limit > 0:
            total_pages = max(1, (total_records + limit - 1) // limit)
            offset = (page - 1) * limit
            appointments = query.offset(offset).limit(limit).all()
        else:
            total_pages = 1
            appointments = query.all()
        
        orders_payload = []
        for appt in appointments:
            queue = db.query(Queue).filter(Queue.appointment_id == appt.appointment_id).first()
            machine = db.get(MachineStatus, queue.machine_id) if (queue and queue.machine_id) else None
            orders_payload.append({
                'order_code': appt.order_code,
                'service_type': appt.service_type,
                'status': appt.status,
                'fulfillment_status': appt.fulfillment_status,
                'payment_status': appt.payment_status,
                'queue_number': queue.queue_number if queue else None,
                'queue_status': queue.status if queue else 'Pending',
                'machine_name': (machine.machine_name or f"Machine {machine.machine_id} (Dryer and Washer)") if machine else None,
                'load_details': appt.load_details or '',
                'total_machines': appt.total_machines or 1,
                'estimated_wait': queue.estimated_waiting_time if queue else 0
            })
            
        response_payload = {
            'status': 'success',
            'data': orders_payload
        }
        if limit and limit > 0:
            response_payload['pagination'] = {
                'total': total_records,
                'page': page,
                'limit': limit,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        return jsonify(response_payload)
    finally:
        db.close()


@dashboard_bp.route('/api/dashboard/summary')
def dashboard_summary():
    """Shared operational feed. Financial and prediction data are manager-only."""
    db = SessionLocal()
    try:
        is_manager = _has_role('Manager', 'Super Admin')
        is_customer = _has_role('Customer')
        return jsonify({
            "status": "success",
            "data": {
                "metrics": _dashboard_metrics(db, include_revenue=is_manager),
                "activities": [] if is_customer else _live_activity(db),
                "forecast": AnalyticsEngine.train_and_predict_peak_hour() if is_manager else None,
            }
        })
    finally:
        db.close()


@dashboard_bp.route('/api/manager/dashboard-counters')
def manager_dashboard_counters():
    denied = _api_access('Manager')
    if denied:
        return denied
    db = SessionLocal()
    try:
        return jsonify({"status": "success", "data": _dashboard_metrics(db, include_revenue=True)})
    finally:
        db.close()


@dashboard_bp.route('/api/manager/live-activity')
def manager_live_activity():
    denied = _api_access('Manager')
    if denied:
        return denied
    db = SessionLocal()
    try:
        return jsonify({"status": "success", "data": _live_activity(db)})
    finally:
        db.close()


@dashboard_bp.route('/api/manager/transactions')
def manager_transactions():
    denied = _api_access('Manager')
    if denied:
        return denied
    db = SessionLocal()
    try:
        rows = (db.query(Transaction, User.name)
                .outerjoin(User, Transaction.customer_id == User.user_id)
                .order_by(Transaction.created_at.desc()).limit(50).all())
        return jsonify({"status": "success", "data": [{
            "transaction_id": transaction.transaction_id,
            "customer": customer or "Walk-in customer",
            "weight_kg": float(transaction.weight_kg),
            "total_amount": float(transaction.total_amount),
            "payment_status": transaction.payment_status,
            "payment_method": transaction.payment_method or '—',
            "payment_reference": transaction.payment_reference or '',
            "processed_by": transaction.processed_by or '—',
            "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
        } for transaction, customer in rows]})
    finally:
        db.close()


@dashboard_bp.route('/api/manager/sales-tally')
def sales_tally_api():
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    db = SessionLocal()
    try:
        limit_days = request.args.get('limit_days', default=7, type=int)
        
        # 1. Daily Aggregations (Reconciliation Tally)
        query = (db.query(
            func.date(Transaction.created_at).label('tx_date'),
            func.count(Transaction.transaction_id).label('tx_count'),
            func.sum(Transaction.weight_kg).label('total_weight'),
            func.sum(Transaction.total_amount).label('gross_sales'),
            func.sum(case((Transaction.payment_status == 'Paid', Transaction.total_amount), else_=0.0)).label('paid_sales'),
            func.sum(case((Transaction.payment_status != 'Paid', Transaction.total_amount), else_=0.0)).label('unpaid_sales'),
        ).group_by(func.date(Transaction.created_at))
         .order_by(func.date(Transaction.created_at).desc()))
        
        if limit_days and limit_days > 0:
            query = query.limit(limit_days)
            
        rows = query.all()
        
        today_date = datetime.now().date()
        yesterday_date = today_date - timedelta(days=1)
        
        daily_records = []
        for r in rows:
            d = r.tx_date
            if isinstance(d, str):
                d = datetime.strptime(d, '%Y-%m-%d').date()
            
            if d == today_date:
                display_date = "Today, " + d.strftime('%b %d, %Y')
            elif d == yesterday_date:
                display_date = "Yesterday, " + d.strftime('%b %d, %Y')
            else:
                display_date = d.strftime('%a, %b %d, %Y')
                
            gross = float(r.gross_sales or 0.0)
            paid = float(r.paid_sales or 0.0)
            unpaid = float(r.unpaid_sales or 0.0)
            count = int(r.tx_count or 0)
            weight = round(float(r.total_weight or 0.0), 2)
            avg_ticket = round(gross / count, 2) if count > 0 else 0.0
            
            daily_records.append({
                "date": d.isoformat(),
                "display_date": display_date,
                "day_name": d.strftime('%A'),
                "tx_count": count,
                "total_weight_kg": weight,
                "gross_sales": gross,
                "paid_sales": paid,
                "unpaid_sales": unpaid,
                "avg_ticket": avg_ticket,
                "tally_status": "Balanced" if unpaid == 0 else f"₱{unpaid:.2f} Pending"
            })
            
        # 2. Overall Summary Cards
        today_row = next((r for r in daily_records if r["date"] == today_date.isoformat()), None)
        seven_days_ago = today_date - timedelta(days=7)
        thirty_days_ago = today_date - timedelta(days=30)
        
        week_gross = db.query(func.sum(Transaction.total_amount)).filter(func.date(Transaction.created_at) >= seven_days_ago).scalar() or 0.0
        month_gross = db.query(func.sum(Transaction.total_amount)).filter(func.date(Transaction.created_at) >= thirty_days_ago).scalar() or 0.0
        all_time_gross = db.query(func.sum(Transaction.total_amount)).scalar() or 0.0
        all_time_count = db.query(Transaction).count()
        all_time_weight = db.query(func.sum(Transaction.weight_kg)).scalar() or 0.0
        
        metrics = {
            "today_gross": today_row["gross_sales"] if today_row else 0.0,
            "today_count": today_row["tx_count"] if today_row else 0,
            "today_weight": today_row["total_weight_kg"] if today_row else 0.0,
            "week_gross": float(week_gross),
            "month_gross": float(month_gross),
            "all_time_gross": float(all_time_gross),
            "all_time_count": all_time_count,
            "all_time_weight": round(float(all_time_weight), 2)
        }
        
        return jsonify({
            "status": "success",
            "data": daily_records,
            "metrics": metrics,
            "limit_days": limit_days
        })
    finally:
        db.close()


@dashboard_bp.route('/api/transactions')
def transactions_api():
    denied = _api_access('Manager', 'Staff', 'Customer')
    if denied:
        return denied
    db = SessionLocal()
    try:
        page = max(1, request.args.get('page', default=1, type=int))
        limit = max(1, min(100, request.args.get('limit', default=15, type=int)))
        date_filter = request.args.get('date', default=None, type=str)
        status_filter = request.args.get('status', default=None, type=str)
        
        query = db.query(Transaction, User.name).outerjoin(User, Transaction.customer_id == User.user_id)
        
        if date_filter:
            try:
                parsed_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(func.date(Transaction.created_at) == parsed_date)
            except ValueError:
                pass
                
        if status_filter and status_filter.lower() != 'all':
            query = query.filter(Transaction.payment_status == status_filter)
            
        total_records = query.count()
        total_pages = max(1, (total_records + limit - 1) // limit)
        offset = (page - 1) * limit
        
        rows = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
        
        data = [{
            "transaction_id": tx.transaction_id,
            "customer": name or (tx.customer_name if tx.customer_name else 'Walk-in customer'),
            "weight_kg": float(tx.weight_kg),
            "cycle_type": tx.cycle_type or 'washing',
            "total_amount": float(tx.total_amount),
            "payment_status": tx.payment_status,
            "payment_method": tx.payment_method or '—',
            "payment_reference": tx.payment_reference or '',
            "cash_tendered": float(tx.cash_tendered) if tx.cash_tendered is not None else None,
            "change_given": float(tx.change_given) if tx.change_given is not None else None,
            "processed_by": tx.processed_by or '—',
            "created_at": tx.created_at.isoformat() if tx.created_at else None
        } for tx, name in rows]
        
        return jsonify({
            'status': 'success',
            'data': data,
            'pagination': {
                'total_records': total_records,
                'page': page,
                'limit': limit,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            },
            'filters': {
                'date': date_filter,
                'status': status_filter
            }
        })
    finally:
        db.close()


@dashboard_bp.route('/api/manager/transactions.csv')
@dashboard_bp.route('/sales/export')
def transactions_csv():
    denied = _api_access('Manager', 'Super Admin')
    if denied:
        return denied
    db = SessionLocal()
    try:
        rows = (db.query(Transaction, User.name).outerjoin(User, Transaction.customer_id == User.user_id)
                .order_by(Transaction.created_at.desc()).all())
        lines = ['Timestamp,Transaction ID,Customer,Weight (kg),Amount,Payment status,Payment method,Reference / ID No.,Processed by']
        for tx, name in rows:
            timestamp = tx.created_at.isoformat() if tx.created_at else ''
            lines.append(
                f'{timestamp},TRX-{tx.transaction_id:04d},"{name or "Walk-in customer"}",{float(tx.weight_kg):.2f},'
                f'{float(tx.total_amount):.2f},{tx.payment_status},{tx.payment_method or ""},'
                f'{tx.payment_reference or ""},"{tx.processed_by or ""}"'
            )
        return Response('\n'.join(lines), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=transactions.csv'})
    finally:
        db.close()


@dashboard_bp.route('/api/manager/sales-tally.pdf')
def sales_tally_pdf():
    """Download the full Sales & Tally ledger as a print-ready PDF report."""
    denied = _api_access('Manager', 'Super Admin')
    if denied:
        return denied
    db = SessionLocal()
    try:
        rows = (db.query(Transaction, User.name)
                .outerjoin(User, Transaction.customer_id == User.user_id)
                .order_by(Transaction.created_at.desc()).all())
        report = _build_sales_tally_pdf(rows, datetime.now())
        filename = f'sales-tally-{datetime.now().strftime("%Y%m%d")}.pdf'
        return Response(
            report,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    finally:
        db.close()


@dashboard_bp.route('/api/appointments', methods=['GET', 'POST'])
def appointments_api():
    denied = _api_access('Manager', 'Staff', 'Customer')
    if denied:
        return denied
    db = SessionLocal()
    try:
        if request.method == 'POST':
            payload = request.get_json(silent=True) or request.form
            raw_time = payload.get('schedule_time')
            service_type = payload.get('service_type')
            email = (payload.get('customer_email') or '').strip().lower()
            if not raw_time or service_type not in ('Wash-Dry-Fold', 'Wash-Only', 'Dry-Only') or not email:
                return jsonify({'status': 'error', 'message': 'Customer email, service type, and appointment time are required.'}), 400
            schedule_time = datetime.strptime(raw_time, '%Y-%m-%dT%H:%M')
            customer = db.query(User).filter(User.email == email, User.user_role == 'Customer').first()
            capacity = db.query(MachineStatus).filter(MachineStatus.status != 'Maintenance').count()
            booked = db.query(Appointment).filter(Appointment.schedule_time == schedule_time, Appointment.status.in_(['Pending', 'Confirmed', 'In Progress'])).count()
            if not customer:
                return jsonify({'status': 'error', 'message': 'Customer email was not found.'}), 404
            if schedule_time <= datetime.now() or booked >= capacity:
                return jsonify({'status': 'error', 'message': 'The selected time is unavailable.'}), 409
            appointment = Appointment(customer_id=customer.user_id, schedule_time=schedule_time, service_type=service_type, status='Pending')
            db.add(appointment)
            db.flush()
            queue = Queue(
                queue_number=QueueManager.generate_next_queue_number(db),
                appointment_id=appointment.appointment_id,
                status='Waiting',
                verified_at=None,
                created_at=datetime.now(),
                estimated_waiting_time=QueueManager.calculate_current_ewt(db)
            )
            db.add(queue)
            db.commit()
            return jsonify({'status': 'success', 'message': 'Appointment saved and added to the queue.'}), 201
            
        status_filter = request.args.get('status', default='active').strip().lower()
        query = (db.query(Appointment, User.name, Queue.queue_id, Queue.status, Queue.queue_number, MachineStatus.machine_name)
                .outerjoin(User, Appointment.customer_id == User.user_id)
                .outerjoin(Queue, Queue.appointment_id == Appointment.appointment_id)
                .outerjoin(MachineStatus, Queue.machine_id == MachineStatus.machine_id))
                
        if _has_role('Customer'):
            query = query.filter(Appointment.customer_id == session.get('user_id'))
        else:
            if status_filter == 'active':
                query = query.filter(Appointment.status.in_(['Pending', 'Confirmed', 'In Progress']))
            elif status_filter == 'completed':
                query = query.filter(Appointment.status == 'Completed')
            elif status_filter == 'cancelled':
                query = query.filter(Appointment.status == 'Cancelled')
            elif status_filter == 'pending':
                query = query.filter(Appointment.status == 'Pending')
            elif status_filter == 'confirmed':
                query = query.filter(Appointment.status.in_(['Confirmed', 'In Progress']))

        pay_order = case(
            (Appointment.payment_status != 'Paid', 1),
            else_=2
        )
        order = Appointment.schedule_time.desc() if status_filter in ('completed', 'cancelled') else Appointment.schedule_time.asc()
        default_limit = 60 if status_filter in ('completed', 'cancelled') else 150
        req_limit = request.args.get('limit', default=default_limit, type=int)
        limit_val = max(1, min(req_limit, 500))
        rows = query.order_by(pay_order.asc(), order).limit(limit_val).all()
        
        # Summary counts for quick UI tab badges
        counts_base = db.query(Appointment)
        if _has_role('Customer'):
            counts_base = counts_base.filter(Appointment.customer_id == session.get('user_id'))
        active_count = counts_base.filter(Appointment.status.in_(['Pending', 'Confirmed', 'In Progress'])).count()
        completed_count = counts_base.filter(Appointment.status == 'Completed').count()
        
        return jsonify({
            'status': 'success',
            'counts': {
                'active': active_count,
                'completed': completed_count,
                'showing': len(rows),
                'limit': limit_val
            },
            'data': [{
                'appointment_id': appointment.appointment_id,
                'order_code': appointment.order_code or f"ORD-{appointment.appointment_id:04d}",
                'customer': appointment.customer_name or name or 'Walk-in customer',
                'customer_email': appointment.customer_email,
                'phone_number': appointment.phone_number,
                'address': appointment.address or '—',
                'schedule_time': appointment.schedule_time.isoformat(),
                'pickup_time': appointment.pickup_time,
                'service_type': appointment.service_type,
                'turnaround_option': appointment.turnaround_option or '24 Hours',
                'priority_level': appointment.priority_level or 'Standard',
                'order_mode': appointment.order_mode or 'Drop-Off',
                'payment_method': appointment.payment_method or 'Cash',
                'payment_status': appointment.payment_status or 'Pending',
                'fulfillment_status': appointment.fulfillment_status or ('Waiting Drop-off' if (appointment.order_mode or '') != 'Pick-up & Delivery' else 'For Pickup'),
                'status': appointment.status,
                'cancellation_reason': appointment.cancellation_reason,
                'cancelled_at': appointment.cancelled_at.isoformat() if appointment.cancelled_at else None,
                'refund_status': appointment.refund_status,
                'load_details': appointment.load_details or '',
                'total_machines': appointment.total_machines or 1,
                'queue_id': queue_id,
                'queue_number': queue_number,
                'queue_status': queue_status,
                'machine_name': machine_name
            } for appointment, name, queue_id, queue_status, queue_number, machine_name in rows]
        })
    finally:
        db.close()


@dashboard_bp.route('/api/appointments/availability')
def appointment_availability():
    denied = _api_access('Manager', 'Staff', 'Customer')
    if denied:
        return denied
    db = SessionLocal()
    try:
        raw_time = request.args.get('schedule_time')
        selected = datetime.strptime(raw_time, '%Y-%m-%dT%H:%M') if raw_time else datetime.now().replace(minute=0, second=0, microsecond=0)
        capacity = db.query(MachineStatus).filter(MachineStatus.status != 'Maintenance').count()
        booked = db.query(Appointment).filter(Appointment.schedule_time == selected, Appointment.status.in_(['Pending', 'Confirmed', 'In Progress'])).count()
        return jsonify({'status': 'success', 'data': {'schedule_time': selected.isoformat(), 'available': max(capacity - booked, 0), 'capacity': capacity, 'booked': booked}})
    finally:
        db.close()


@dashboard_bp.route('/api/appointments/<int:appointment_id>/check-in', methods=['POST'])
def check_in_appointment(appointment_id):
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    db = SessionLocal()
    try:
        refresh_machine_cycles(db)
        appointment = db.get(Appointment, appointment_id)
        if not appointment:
            return jsonify({'status': 'error', 'message': 'Appointment not found.'}), 404
        now = datetime.now()
        if (appointment.payment_status or 'Pending') != 'Paid':
            return jsonify({'status': 'error', 'message': 'Payment is required before a machine can be assigned. Use Verify Order to collect payment and assign.'}), 402
        appointment.status = 'Confirmed'
        appointment.verified_at = now
        queue = db.query(Queue).filter(Queue.appointment_id == appointment_id).first()
        if queue:
            queue.verified_at = now
            if queue.status == 'Waiting':
                eff_weight = float(appointment.actual_weight) if appointment.actual_weight else (float(appointment.estimated_weight) if appointment.estimated_weight else 8.0)
                is_13kg = eff_weight > 8.0 or ('13' in (appointment.load_details or '')) or ('titan' in (appointment.load_details or '').lower()) or ('13' in (appointment.service_type or ''))
                req_capacity = 13 if is_13kg else 8
                
                avail_query = db.query(MachineStatus).filter(
                    MachineStatus.status == 'Available',
                    MachineStatus.operational_state == 'available',
                    MachineStatus.capacity_kg >= req_capacity
                )
                machine = avail_query.order_by(MachineStatus.usage_count.asc()).first()

                if machine:
                    dry_only = 'dry only' in (appointment.service_type or '').lower()
                    cycle_name = "drying" if dry_only else "washing"
                    start_machine_cycle(machine, appointment.customer_name or "Appointment Customer", cycle_name)
                    queue.cycle_stage = cycle_name
                    queue.machine_id = machine.machine_id
                    queue.status = 'Processing'
                    queue.started_at = now
                    queue.actual_wait_mins = 0
                    queue.estimated_waiting_time = 0
                    queue.fulfillment_status = 'In Laundry'
                    appointment.fulfillment_status = 'In Laundry'
                    appointment.status = 'Confirmed'
                else:
                    queue.estimated_waiting_time = QueueManager.calculate_current_ewt(db)
        db.commit()
        AuditService.log(
            action=AuditAction.APPOINTMENT_CHECKIN,
            entity_type='Appointment',
            entity_id=str(appointment.order_code or appointment_id),
            details=f"Checked in appointment {appointment.order_code or appointment_id} for {appointment.customer_name or 'Customer'}"
        )
        return jsonify({'status': 'success', 'message': f'Appointment for {appointment.customer_name or "Customer"} accepted & checked in.'})
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


@dashboard_bp.route('/api/appointments/<int:appointment_id>/complete', methods=['POST'])
def complete_appointment(appointment_id):
    """Marks appointment as Completed/Picked Up, removing it from active workflow."""
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    db = SessionLocal()
    try:
        refresh_machine_cycles(db)
        appointment = db.get(Appointment, appointment_id)
        if not appointment:
            return jsonify({'status': 'error', 'message': 'Appointment not found.'}), 404
            
        appointment.status = 'Completed'
        appointment.fulfillment_status = 'Picked Up by Customer'
        
        # Complete corresponding queue entry and free machine if currently tied
        queue = db.query(Queue).filter(Queue.appointment_id == appointment_id).first()
        if queue:
            queue.status = 'Done'
            queue.fulfillment_status = 'Picked Up by Customer'
            if queue.machine_id:
                machine = db.get(MachineStatus, queue.machine_id)
                if machine and machine.status == 'In-Use':
                    machine.status = 'Available'
                    machine.assigned_customer_name = None
                    machine.cycle_type = None
                    machine.cycle_started_at = None
                    machine.cycle_ends_at = None
                    start_next_queued_job(db, machine)

        # Ensure a Transaction record exists for completed paid appointments
        if appointment.payment_status == 'Paid':
            from services.payments import compute_service_price
            from decimal import Decimal
            tx = None
            if queue and queue.transaction_id:
                tx = db.get(Transaction, queue.transaction_id)
            if not tx:
                amount = compute_service_price(
                    appointment.service_type,
                    appointment.order_mode or 'Drop-Off',
                    appointment.turnaround_option or '24 Hours'
                )
                tx = Transaction(
                    customer_id=appointment.customer_id,
                    customer_name=appointment.customer_name or "Customer",
                    weight_kg=Decimal('8.00'),
                    total_amount=amount,
                    payment_status='Paid',
                    created_at=datetime.now(),
                    cycle_type='washing',
                    payment_method=appointment.payment_method,
                    processed_by=session.get('user_name'),
                    processed_by_id=session.get('user_id')
                )
                db.add(tx)
                db.flush()
                if queue:
                    queue.transaction_id = tx.transaction_id
        if appointment.customer_email:
            EmailService.send_order_completed(
                appointment.customer_email,
                appointment.order_code or f"ORD-{appointment.appointment_id:04d}",
                appointment.customer_name or "Valued Customer"
            )
            
        db.commit()
        AuditService.log(
            action=AuditAction.APPOINTMENT_COMPLETED,
            entity_type='Appointment',
            entity_id=str(appointment.order_code or appointment_id),
            details=f"Completed appointment {appointment.order_code or appointment_id} for {appointment.customer_name or 'Customer'}"
        )
        return jsonify({'status': 'success', 'message': f'Appointment for {appointment.customer_name or "Customer"} marked as Picked Up & Completed.'})
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


@dashboard_bp.route('/api/appointments/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    """Cancels an appointment or marks as no-show."""
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    db = SessionLocal()
    try:
        appointment = db.get(Appointment, appointment_id)
        if not appointment:
            return jsonify({'status': 'error', 'message': 'Appointment not found.'}), 404
            
        appointment.status = 'Cancelled'
        
        queue = db.query(Queue).filter(Queue.appointment_id == appointment_id).first()
        if queue and queue.status == 'Waiting':
            db.delete(queue)
            
        db.commit()
        AuditService.log(
            action=AuditAction.APPOINTMENT_CANCELLED,
            entity_type='Appointment',
            entity_id=str(appointment.order_code or appointment_id),
            details=f"Cancelled appointment {appointment.order_code or appointment_id} for {appointment.customer_name or 'Customer'}"
        )
        return jsonify({'status': 'success', 'message': f'Appointment for {appointment.customer_name or "Customer"} has been cancelled.'})
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


@dashboard_bp.route('/api/queue', methods=['GET', 'POST'])
def queue_api():
    denied = _api_access('Manager', 'Staff', 'Customer')
    if denied:
        return denied
    db = SessionLocal()
    try:
        if request.method == 'POST':
            if not _has_role('Manager', 'Staff'):
                return jsonify({'status': 'error', 'message': 'Staff access is required to add walk-ins.'}), 403
            now = datetime.now()
            next_q = QueueManager.generate_next_queue_number(db)
            est_wait = QueueManager.calculate_current_ewt(db)
            queue = Queue(
                queue_number=next_q,
                status='Waiting',
                verified_at=now,
                created_at=now,
                estimated_waiting_time=est_wait
            )
            db.add(queue)
            db.commit()
            return jsonify({'status': 'success', 'message': 'Walk-in added to queue.', 'data': {'queue_id': queue.queue_id, 'queue_number': queue.queue_number, 'estimated_waiting_time': est_wait}}), 201
        pay_order = case(
            (func.coalesce(Queue.payment_status, Appointment.payment_status) != 'Paid', 1),
            else_=2
        )
        rows = (db.query(Queue, Appointment, User, MachineStatus)
                .outerjoin(Appointment, Queue.appointment_id == Appointment.appointment_id)
                .outerjoin(User, Appointment.customer_id == User.user_id)
                .outerjoin(MachineStatus, Queue.machine_id == MachineStatus.machine_id)
                .filter(Queue.status != 'Done').order_by(pay_order.asc(), Queue.queue_number.asc()))
        if _has_role('Customer'):
            rows = rows.filter(or_(
                Queue.customer_name == session.get('user_name'),
                Appointment.customer_id == session.get('user_id')
            ))
        rows = rows.all()
        now = datetime.now()
        queue_payload = []
        for queue, appointment, name, machine in rows:
            is_verified = (queue.verified_at is not None) or (queue.appointment_id is None)
            wait_elapsed = max(0, int((now - queue.verified_at).total_seconds() / 60)) if queue.verified_at else 0
            rem_wait = max(0, (queue.estimated_waiting_time or 0) - wait_elapsed) if (queue.status == 'Waiting' and is_verified) else (queue.estimated_waiting_time or 0)
            is_self_queue = 'self' in (queue.order_mode or (appointment.order_mode if appointment else '') or '').lower() or 'self' in (appointment.service_type if appointment else '').lower()
            queue_payload.append({
                'queue_id': queue.queue_id, 'queue_number': queue.queue_number,
                'appointment_id': queue.appointment_id,
                'order_code': appointment.order_code if appointment else f"Q-{queue.queue_number:03d}",
                'customer': queue.customer_name or (name.name if name else None) or 'Walk-in customer',
                'phone': appointment.phone_number if appointment else '—',
                'address': appointment.address if appointment else '—',
                'service_type': appointment.service_type if appointment else 'Walk-in',
                'turnaround_option': None if is_self_queue else (queue.turnaround_option or (appointment.turnaround_option if appointment else '24 Hours') or '24 Hours'),
                'priority_level': queue.priority_level or (appointment.priority_level if appointment else 'Standard') or 'Standard',
                'order_mode': queue.order_mode or (appointment.order_mode if appointment else ('Self-Service' if is_self_queue else 'Drop-Off')) or ('Self-Service' if is_self_queue else 'Drop-Off'),
                'payment_method': queue.payment_method or (appointment.payment_method if appointment else 'Cash') or 'Cash',
                'payment_status': queue.payment_status or (appointment.payment_status if appointment else 'Pending') or 'Pending',
                'fulfillment_status': queue.fulfillment_status or (appointment.fulfillment_status if appointment else 'Received') or 'Received',
                'status': queue.status,
                'cycle_stage': queue.cycle_stage or 'washing',
                'service_tier': service_tier(appointment.service_type if appointment else None),
                'includes_dry': bool(appointment and package_includes_dry(appointment.service_type, appointment.addons)),
                'load_details': queue.load_details or (appointment.load_details if appointment else '') or '',
                'total_machines': queue.total_machines or (appointment.total_machines if appointment else 1) or 1,
                'machine': (machine.machine_name or f'Machine {machine.machine_id} (Dryer and Washer)') if machine else 'Unassigned',
                'estimated_waiting_time': queue.estimated_waiting_time or 0,
                'wait_elapsed_mins': wait_elapsed,
                'remaining_wait_mins': rem_wait,
                'is_verified': is_verified,
                'verified_at': queue.verified_at.strftime('%I:%M %p') if queue.verified_at else None
            })
        return jsonify({'status': 'success', 'data': queue_payload})
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


@dashboard_bp.route('/api/appointments/<int:appointment_id>/payment-status', methods=['POST'])
def update_appointment_payment_status(appointment_id):
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    payload = request.get_json(silent=True) or request.form
    new_status = (payload.get('payment_status') or 'Paid').strip()
    if new_status not in ('Paid', 'Pending'):
        return jsonify({'status': 'error', 'message': 'Invalid payment status. Must be Paid or Pending.'}), 400

    db = SessionLocal()
    try:
        appointment = db.get(Appointment, appointment_id)
        if not appointment:
            return jsonify({'status': 'error', 'message': 'Appointment not found.'}), 404
        appointment.payment_status = new_status
        queue = db.query(Queue).filter(Queue.appointment_id == appointment_id).first()
        if queue:
            queue.payment_status = new_status

        # Synchronize with Transaction table so it tallies in Sales & Tally
        if new_status == 'Paid':
            from services.payments import compute_service_price
            from decimal import Decimal
            tx = None
            if queue and queue.transaction_id:
                tx = db.get(Transaction, queue.transaction_id)
            if not tx:
                amount = compute_service_price(
                    appointment.service_type,
                    appointment.order_mode or 'Drop-Off',
                    appointment.turnaround_option or '24 Hours'
                )
                tx = Transaction(
                    customer_id=appointment.customer_id,
                    customer_name=appointment.customer_name or "Customer",
                    weight_kg=Decimal('8.00'),
                    total_amount=amount,
                    payment_status='Paid',
                    created_at=datetime.now(),
                    cycle_type='washing',
                    payment_method=appointment.payment_method,
                    processed_by=session.get('user_name'),
                    processed_by_id=session.get('user_id')
                )
                db.add(tx)
                db.flush()
                if queue:
                    queue.transaction_id = tx.transaction_id
            else:
                tx.payment_status = 'Paid'
        elif new_status == 'Pending':
            if queue and queue.transaction_id:
                tx = db.get(Transaction, queue.transaction_id)
                if tx:
                    tx.payment_status = 'Pending'

        db.commit()
        AuditService.log(
            action=AuditAction.PAYMENT_UPDATED,
            entity_type='Appointment',
            entity_id=str(appointment.order_code or appointment_id),
            details=f"Updated payment status to {new_status} for {appointment.order_code or appointment_id}"
        )
        return jsonify({'status': 'success', 'message': f'Payment marked as {new_status} for {appointment.order_code or "Order"}.', 'data': {'payment_status': new_status}})
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


@dashboard_bp.route('/api/appointments/<int:appointment_id>/fulfillment-status', methods=['POST'])
def update_appointment_fulfillment_status(appointment_id):
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    payload = request.get_json(silent=True) or request.form
    new_status = (payload.get('fulfillment_status') or '').strip()
    if not new_status:
        return jsonify({'status': 'error', 'message': 'Fulfillment status is required.'}), 400

    db = SessionLocal()
    try:
        appointment = db.get(Appointment, appointment_id)
        if not appointment:
            return jsonify({'status': 'error', 'message': 'Appointment not found.'}), 404
        
        appointment.fulfillment_status = new_status
        queue = db.query(Queue).filter(Queue.appointment_id == appointment_id).first()
        if queue:
            queue.fulfillment_status = new_status

        # If delivered or picked up, mark overall appointment completed and release queue/machines if appropriate
        if new_status in ('Delivered', 'Picked Up by Customer', 'Fulfilled & Picked Up'):
            appointment.status = 'Completed'
            if queue:
                queue.status = 'Done'
                if queue.machine_id:
                    machine = db.get(MachineStatus, queue.machine_id)
                    if machine and machine.status == 'In-Use':
                        machine.status = 'Available'
                        machine.assigned_customer_name = None
                        machine.cycle_type = None
                        machine.cycle_started_at = None
                        machine.cycle_ends_at = None
                        start_next_queued_job(db, machine)
            if appointment.customer_email:
                EmailService.send_order_completed(
                    appointment.customer_email,
                    appointment.order_code or f"ORD-{appointment.appointment_id:04d}",
                    appointment.customer_name or "Valued Customer"
                )

        db.commit()
        AuditService.log(
            action=AuditAction.FULFILLMENT_UPDATED,
            entity_type='Appointment',
            entity_id=str(appointment.order_code or appointment_id),
            details=f"Updated fulfillment to '{new_status}' (status={appointment.status}) for {appointment.order_code or appointment_id}"
        )
        return jsonify({'status': 'success', 'message': f'Fulfillment status updated to {new_status}.', 'data': {'fulfillment_status': new_status, 'status': appointment.status}})
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


@dashboard_bp.route('/api/queue/<int:queue_id>/advance', methods=['POST'])
def advance_queue(queue_id):
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    db = SessionLocal()
    try:
        refresh_machine_cycles(db)
        queue = db.get(Queue, queue_id)
        if not queue:
            return jsonify({'status': 'error', 'message': 'Queue entry not found.'}), 404
        if queue.status == 'Waiting':
            if queue.appointment_id and (queue.payment_status or 'Pending') != 'Paid':
                return jsonify({'status': 'error', 'message': 'Payment is required before this order can be assigned a machine. Use Verify Order to collect payment.'}), 402
            machine = db.get(MachineStatus, queue.machine_id) if queue.machine_id else None
            if machine and not is_machine_available(machine):
                return jsonify({'status': 'error', 'message': 'The selected machine is still occupied; this customer remains queued for it.'}), 409
            if not machine:
                appt = db.get(Appointment, queue.appointment_id) if queue.appointment_id else None
                trans = db.get(Transaction, queue.transaction_id) if queue.transaction_id else None
                eff_weight = 8.0
                if appt:
                    eff_weight = float(appt.actual_weight) if appt.actual_weight else (float(appt.estimated_weight) if appt.estimated_weight else 8.0)
                elif trans and trans.weight_kg:
                    eff_weight = float(trans.weight_kg)
                
                is_13kg = eff_weight > 8.0 or ('13' in (queue.load_details or '')) or ('titan' in (queue.load_details or '').lower())
                if appt and not is_13kg:
                    is_13kg = ('13' in (appt.load_details or '')) or ('titan' in (appt.load_details or '').lower()) or ('13' in (appt.service_type or ''))
                req_capacity = 13 if is_13kg else 8
                
                candidates = [item for item in db.query(MachineStatus).all() if is_machine_available(item) and (item.capacity_kg or 8) >= req_capacity]
                candidates.sort(key=lambda item: (item.usage_count or 0, item.last_used_at or datetime.min, item.machine_id))
                machine = candidates[0] if candidates else None
            if not machine:
                return jsonify({'status': 'error', 'message': 'No machine is ready yet.'}), 409
            transaction = db.get(Transaction, queue.transaction_id) if queue.transaction_id else None
            cycle_type = queue_cycle_type(db, queue)
            now = datetime.now()
            cust_name = queue.customer_name or (transaction.customer_name if transaction else None) or 'Walk-in customer'
            start_machine_cycle(machine, cust_name, cycle_type)
            queue.cycle_stage = cycle_type
            queue.status, queue.machine_id = 'Processing', machine.machine_id
            queue.started_at = now
            if queue.verified_at:
                queue.actual_wait_mins = round((now - queue.verified_at).total_seconds() / 60, 1)
            else:
                queue.actual_wait_mins = 0
            queue.estimated_waiting_time = 0
            queue.fulfillment_status = 'In Laundry'
            if queue.appointment_id:
                appointment = db.get(Appointment, queue.appointment_id)
                if appointment:
                    appointment.status = 'Confirmed'
                    appointment.fulfillment_status = 'In Laundry'
        elif queue.status == 'Processing':
            finished_machine = db.get(MachineStatus, queue.machine_id) if queue.machine_id else None
            if finished_machine and finished_machine.status == 'In-Use':
                finished_machine.status = 'Available'
                finished_machine.assigned_customer_name = None
                finished_machine.cycle_type = None
                finished_machine.cycle_started_at = None
                finished_machine.cycle_ends_at = None
            # Wash finished and the package includes drying -> hand over to a dryer
            moved_to_dry = begin_dry_stage(db, queue)
            if moved_to_dry:
                result_message = 'Wash finished — load moved to the dry stage.'
            else:
                result_message = 'Cycle finished.'
                queue.status = 'Done'
                queue.cycle_completed_at = datetime.now()
                if queue.appointment_id:
                    appointment = db.get(Appointment, queue.appointment_id)
                    if appointment:
                        is_delivery = (appointment.order_mode or '') == 'Pick-up & Delivery'
                        next_fulfillment = 'Out for Delivery' if is_delivery else 'Ready for Pick-up'
                        appointment.fulfillment_status = next_fulfillment
                        queue.fulfillment_status = next_fulfillment
                        appointment.status = 'Confirmed'
                        if appointment.customer_email:
                            EmailService.send_order_completed(
                                appointment.customer_email,
                                appointment.order_code or f"ORD-{appointment.appointment_id:04d}",
                                appointment.customer_name or "Valued Customer"
                            )
            if finished_machine:
                start_next_queued_job(db, finished_machine)
        db.commit()
        AuditService.log(
            action=AuditAction.QUEUE_ADVANCED,
            entity_type='Queue',
            entity_id=str(queue.queue_number),
            details=f"Advanced queue #{queue.queue_number} ({queue.customer_name or 'Walk-in'}) to {queue.status} (fulfillment={queue.fulfillment_status})"
        )
        return jsonify({'status': 'success', 'message': locals().get('result_message', 'Queue status updated.')})
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


# =============================================================================
# VERIFICATION TERMINAL — Replaces POS counter
# Counter staff enters Order Code → verifies details → queues order
# =============================================================================

@dashboard_bp.route('/staff/verify-order')
def verify_order_page():
    """Renders the Verification Terminal (replaces old POS screen)."""
    if not _has_role('Staff', 'Manager'):
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template(
        'staff/verify_order.html',
        staff_name=session.get('user_name'),
        role=session.get('user_role')
    )


def find_appointment_for_verification(db, raw_code: str):
    """
    Finds appointment by order_code, accepting numeric-only input (e.g. '77663'),
    standard codes ('ORD-77663'), unhyphenated codes ('ORD77663'), or appointment_id ('195').
    """
    if not raw_code:
        return None
    raw = str(raw_code).strip()
    
    # 1. Direct match (e.g. 'ORD-77663')
    appt = db.query(Appointment).filter(Appointment.order_code.ilike(raw)).first()
    if appt:
        return appt
        
    # 2. If input contains digits (e.g. '77663', '#77663')
    clean_digits = re.sub(r'\D', '', raw)
    if clean_digits:
        # Check standard ORD-<digits>
        appt = db.query(Appointment).filter(Appointment.order_code.ilike(f"ORD-{clean_digits}")).first()
        if appt:
            return appt
            
        # Check if it matches appointment_id directly (e.g. '195')
        if clean_digits.isdigit():
            appt = db.query(Appointment).filter(Appointment.appointment_id == int(clean_digits)).first()
            if appt:
                return appt
                
        # Suffix / substring match on order_code
        appt = db.query(Appointment).filter(Appointment.order_code.like(f"%{clean_digits}%")).order_by(Appointment.appointment_id.desc()).first()
        if appt:
            return appt

    # 3. Clean alphanumeric (e.g. 'ORD77663')
    alnum = re.sub(r'[^A-Za-z0-9]', '', raw).upper()
    if alnum.startswith('ORD'):
        suffix = alnum[3:]
        if suffix:
            appt = db.query(Appointment).filter(Appointment.order_code.ilike(f"ORD-{suffix}")).first()
            if appt:
                return appt

    return None


@dashboard_bp.route('/api/staff/verify-order', methods=['GET'])
def api_lookup_order():
    """Look up an appointment by Order Code or number. Returns full order details and load recommendations as JSON."""
    denied = _api_access('Staff', 'Manager')
    if denied:
        return denied

    raw_code = (request.args.get('code') or '').strip()
    if not raw_code:
        return jsonify({'status': 'error', 'message': 'Order code or number is required.'}), 400

    db = SessionLocal()
    try:
        appt = find_appointment_for_verification(db, raw_code)
        if not appt:
            return jsonify({'status': 'error', 'message': f'No order found for "{raw_code}".'}), 404
        order_code = appt.order_code

        queues = db.query(Queue).filter(Queue.appointment_id == appt.appointment_id).order_by(Queue.queue_id.asc()).all()
        first_queue = queues[0] if queues else None

        assigned_machines = []
        for q in queues:
            m = db.get(MachineStatus, q.machine_id) if q.machine_id else None
            assigned_machines.append({
                'queue_id': q.queue_id,
                'queue_number': q.queue_number,
                'machine_id': q.machine_id,
                'machine_name': (m.machine_name or f"Machine {m.machine_id} (Dryer and Washer)") if m else 'Unassigned',
                'machine_type': (m.machine_type or 'Dryer and Washer') if m else None,
                'capacity_kg': m.capacity_kg if m else None,
                'status': q.status,
                'load_details': q.load_details
            })

        # Derive load requirements and detect 13kg Titan machine selection
        parsed_loads = parse_order_loads(
            getattr(appt, 'load_details', None) or '',
            getattr(appt, 'total_machines', 1) or 1,
            appt.service_type,
            weight=None
        )
        has_13kg_load = any(ld.get('capacity_kg', 8) >= 13 for ld in parsed_loads)
        capacity_weight = sum(float(ld.get('capacity_kg', 8)) for ld in parsed_loads) if parsed_loads else (13.0 if has_13kg_load else 8.0)

        effective_weight = None
        if getattr(appt, 'actual_weight', None) is not None:
            effective_weight = float(appt.actual_weight)
        elif getattr(appt, 'estimated_weight', None) is not None:
            raw_w = float(appt.estimated_weight)
            # Prioritize customer chosen 13kg Titan drum over default 8.0
            effective_weight = capacity_weight if (raw_w <= 8.0 and has_13kg_load) else raw_w
        else:
            effective_weight = capacity_weight

        # Consistent estimated weight matching chosen drum capacity
        raw_est = float(appt.estimated_weight) if getattr(appt, 'estimated_weight', None) is not None else None
        final_est_weight = capacity_weight if (raw_est is None or (raw_est <= 8.0 and has_13kg_load)) else raw_est

        recommendation = recommend_machine_for_order(
            db,
            service_type=appt.service_type,
            load_details=getattr(appt, 'load_details', None) or '',
            total_machines=getattr(appt, 'total_machines', 1) or 1,
            weight=effective_weight
        )

        expected_machines = getattr(appt, 'total_machines', 1) or 1
        all_loads_assigned = (len(assigned_machines) >= expected_machines) and all(a['machine_id'] for a in assigned_machines)
        is_already_verified = (appt.status in ('Confirmed', 'Completed')) and all_loads_assigned

        total_amount = float(appt.total_amount) if getattr(appt, 'total_amount', None) else float(
            compute_service_price(appt.service_type, appt.order_mode or 'Drop-Off', appt.turnaround_option or '24 Hours', total_machines=expected_machines)
        )
        addons_data = []
        if getattr(appt, 'addons', None):
            try:
                import json
                addons_data = json.loads(appt.addons)
            except Exception:
                addons_data = [appt.addons]

        is_self_service = 'self' in (appt.order_mode or '').lower() or 'self' in (appt.service_type or '').lower()
        return jsonify({
            'status': 'success',
            'order': {
                'appointment_id': appt.appointment_id,
                'order_code': appt.order_code,
                'customer_name': appt.customer_name or '—',
                'customer_email': appt.customer_email or '—',
                'phone_number': appt.phone_number or '—',
                'service_type': appt.service_type,
                'order_mode': appt.order_mode or ('Self-Service' if is_self_service else 'Drop-Off'),
                'turnaround_option': None if is_self_service else (appt.turnaround_option or '24 Hours'),
                'priority_level': appt.priority_level or 'Standard',
                'payment_method': appt.payment_method or 'Cash',
                'payment_status': appt.payment_status or 'Pending',
                'fulfillment_status': appt.fulfillment_status or 'Received',
                'address': appt.address or '—',
                'pickup_time': appt.pickup_time or '—',
                'schedule_time': appt.schedule_time.strftime('%b %d, %Y %I:%M %p') if appt.schedule_time else '—',
                'total_machines': getattr(appt, 'total_machines', 1) or 1,
                'load_details': getattr(appt, 'load_details', None) or '—',
                'estimated_weight': final_est_weight,
                'actual_weight': float(appt.actual_weight) if getattr(appt, 'actual_weight', None) else None,
                'machine_capacity': 13 if has_13kg_load else 8,
                'addons': addons_data,
                'total_amount': total_amount,
                'formatted_total': f"₱{total_amount:.2f}",
                'status': appt.status,
                'already_verified': is_already_verified,
                'queue_number': first_queue.queue_number if first_queue else None,
                'queue_status': first_queue.status if first_queue else None,
                'assigned_machine_id': first_queue.machine_id if first_queue else None,
                'assigned_machines': assigned_machines,
                'penalty_amount': float(first_queue.penalty_amount or 0) if first_queue else 0.0,
                'penalty_reason': first_queue.penalty_reason if first_queue else None,
                'machine_recommendation': recommendation
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error looking up order: {str(e)}'}), 500
    finally:
        db.close()


@dashboard_bp.route('/api/staff/recommend-machine', methods=['GET'])
def api_recommend_machine():
    """Returns dynamic AI machine recommendation based on service_type and load_details."""
    denied = _api_access('Staff', 'Manager')
    if denied:
        return denied
    db = SessionLocal()
    try:
        service_type = request.args.get('service_type', 'Wash-Dry-Fold')
        load_details = request.args.get('load_details', '')
        total_machines = int(request.args.get('total_machines', 1) or 1)
        raw_weight = request.args.get('weight')
        weight = float(raw_weight) if raw_weight else None
        rec = recommend_machine_for_order(db, service_type=service_type, load_details=load_details, total_machines=total_machines, weight=weight)
        return jsonify({'status': 'success', 'recommendation': rec})
    finally:
        db.close()


@dashboard_bp.route('/api/staff/alter-order', methods=['POST'])
def api_alter_order():
    """
    Counter Staff / Manager alters an order during verification:
    - Alter scale/actual weight
    - Alter service package
    - Adjust machine fleet/capacity (8kg Regular vs 13kg Titan, 1 or multiple machines)
    - Add supplies & add-ons (extra detergent, fabcon, bleach, fold, sort, add dry)
    - Automatically recalculates authoritative totals and updates Appointment & Queue
    - Dynamically refreshes AI machine recommendation
    """
    denied = _api_access('Staff', 'Manager')
    if denied:
        return denied

    payload = request.get_json(silent=True) or request.form
    raw_code = (payload.get('order_code') or '').strip()
    if not raw_code:
        return jsonify({'status': 'error', 'message': 'Order code or number is required.'}), 400

    db = SessionLocal()
    try:
        appt = find_appointment_for_verification(db, raw_code)
        if not appt:
            return jsonify({'status': 'error', 'message': f'No order found for "{raw_code}".'}), 404

        if appt.status in ('Cancelled', 'Completed'):
            return jsonify({'status': 'error', 'message': f'This order is {appt.status} and cannot be altered.'}), 409

        raw_weight = payload.get('actual_weight')
        actual_weight = None
        if raw_weight is not None and str(raw_weight).strip():
            try:
                actual_weight = round(float(raw_weight), 2)
                if actual_weight <= 0:
                    return jsonify({'status': 'error', 'message': 'Weight must be greater than 0 kg.'}), 400
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': 'Invalid actual weight value.'}), 400

        service_type = (payload.get('service_type') or appt.service_type or 'Drop-off Service').strip()

        try:
            total_machines = max(1, int(payload.get('total_machines') or appt.total_machines or 1))
        except (ValueError, TypeError):
            total_machines = 1

        is_bulky = is_bulky_garment_category(service_type) or is_bulky_garment_category(appt.load_details)
        weight_threshold = 6.0 if is_bulky else 8.0
        machine_capacity = int(payload.get('machine_capacity') or (13 if (actual_weight and actual_weight > weight_threshold and total_machines == 1) else 8))

        # Add-ons parsing
        addons_raw = payload.get('addons') or []
        addons_list = []
        addons_total = Decimal('0.00')
        if isinstance(addons_raw, str):
            try:
                import json
                addons_list = json.loads(addons_raw)
            except Exception:
                addons_list = [a.strip() for a in addons_raw.split(',') if a.strip()]
        elif isinstance(addons_raw, list):
            addons_list = addons_raw

        addon_rates = {
            'extra detergent': Decimal('20.00'),
            'detergent': Decimal('20.00'),
            'fabric conditioner': Decimal('20.00'),
            'fabcon': Decimal('20.00'),
            'color-safe bleach': Decimal('30.00'),
            'bleach': Decimal('30.00'),
            'stain treatment': Decimal('30.00'),
            'extra dry': Decimal('70.00'),
            'add dry': Decimal('70.00'),
            'superwash': Decimal('35.00'),
            'fold': Decimal('40.00'),
            'sort': Decimal('30.00'),
            'plastic': Decimal('10.00'),
            'plastic packaging': Decimal('10.00'),
        }

        addons_summary_parts = []
        for item in addons_list:
            if isinstance(item, dict):
                name = item.get('name', 'Add-on')
                qty = int(item.get('qty', 1) or 1)
                price = Decimal(str(item.get('price', 0) or 0))
                if price <= 0:
                    price = addon_rates.get(name.lower(), Decimal('20.00'))
                addons_total += price * Decimal(str(qty))
                addons_summary_parts.append(f"{qty}x {name}")
            elif isinstance(item, str):
                name = item
                price = addon_rates.get(name.lower(), Decimal('20.00'))
                addons_total += price
                addons_summary_parts.append(name)

        base_price = compute_service_price(
            service_type,
            appt.order_mode or 'Drop-Off',
            appt.turnaround_option or '24 Hours',
            total_machines=total_machines
        )

        if machine_capacity >= 13 and 'titan' not in service_type.lower():
            base_price += Decimal('95.00') * Decimal(str(total_machines))

        new_total_amount = base_price + addons_total

        cap_label = "13kg Titan" if machine_capacity >= 13 else "8kg Regular"
        if machine_capacity >= 13 and (appt.estimated_weight is None or float(appt.estimated_weight) <= 8.0):
            appt.estimated_weight = 13.0 * total_machines
        weight_part = f"Scale Weight: {actual_weight}kg" if actual_weight else f"Est: {appt.estimated_weight or 8.0}kg"
        addon_part = f" | Add-ons: {', '.join(addons_summary_parts)}" if addons_summary_parts else ""
        load_details = f"{total_machines} Machine{'s' if total_machines > 1 else ''} ({cap_label}) | {weight_part}{addon_part}"

        appt.actual_weight = actual_weight
        appt.service_type = service_type
        appt.total_machines = total_machines
        appt.load_details = load_details
        import json
        appt.addons = json.dumps(addons_list)
        appt.total_amount = new_total_amount

        existing_queues = db.query(Queue).filter(Queue.appointment_id == appt.appointment_id).all()
        for q in existing_queues:
            q.total_machines = total_machines
            q.load_details = load_details

        db.commit()

        effective_weight = float(actual_weight) if actual_weight else None
        new_rec = recommend_machine_for_order(
            db,
            service_type=appt.service_type,
            load_details=appt.load_details,
            total_machines=appt.total_machines,
            weight=effective_weight
        )

        audit_details = (
            f"Altered order {appt.order_code}: Weight {actual_weight}kg (Est: {appt.estimated_weight}kg), "
            f"Service: {service_type}, Fleet: {total_machines} ({cap_label}), "
            f"Addons: {', '.join(addons_summary_parts) if addons_summary_parts else 'None'}, "
            f"New Total Due: PHP {float(new_total_amount):.2f}"
        )
        AuditService.log(
            action=AuditAction.ORDER_ALTERED,
            entity_type='Appointment',
            entity_id=appt.order_code,
            details=audit_details
        )

        return jsonify({
            'status': 'success',
            'message': 'Order details and load requirements successfully updated.',
            'order': {
                'appointment_id': appt.appointment_id,
                'order_code': appt.order_code,
                'customer_name': appt.customer_name or '—',
                'customer_email': appt.customer_email or '—',
                'phone_number': appt.phone_number or '—',
                'service_type': appt.service_type,
                'order_mode': appt.order_mode or ('Self-Service' if ('self' in (appt.order_mode or '').lower() or 'self' in (appt.service_type or '').lower()) else 'Drop-Off'),
                'turnaround_option': None if ('self' in (appt.order_mode or '').lower() or 'self' in (appt.service_type or '').lower()) else (appt.turnaround_option or '24 Hours'),
                'priority_level': appt.priority_level or 'Standard',
                'payment_method': appt.payment_method or 'Cash',
                'payment_status': appt.payment_status or 'Pending',
                'fulfillment_status': appt.fulfillment_status or 'Received',
                'total_machines': appt.total_machines,
                'load_details': appt.load_details,
                'estimated_weight': float(appt.estimated_weight) if appt.estimated_weight else 8.0,
                'actual_weight': float(appt.actual_weight) if appt.actual_weight else None,
                'addons': addons_list,
                'total_amount': float(new_total_amount),
                'formatted_total': f"₱{float(new_total_amount):.2f}",
                'machine_recommendation': new_rec
            }
        })
    except Exception as e:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()


def _settle_counter_payment(db, appt, queues, payment_data):
    """
    Books a validated counter payment for an appointment: creates (or completes) the
    Transaction with MOP / reference / cashier, then marks the appointment and all of
    its queue rows Paid. Caller owns the commit.
    """
    tx = None
    for q in queues:
        if q.transaction_id:
            tx = db.get(Transaction, q.transaction_id)
            if tx:
                break
    weight = appt.actual_weight or appt.estimated_weight or Decimal('8.00')
    cycle = 'drying' if 'dry only' in (appt.service_type or '').lower() else 'washing'
    if not tx:
        tx = Transaction(
            customer_id=appt.customer_id,
            customer_name=appt.customer_name or 'Customer',
            weight_kg=Decimal(str(weight)).quantize(Decimal('0.01')),
            total_amount=payment_data['amount'],
            created_at=datetime.now(),
            cycle_type=cycle
        )
        db.add(tx)
    else:
        tx.total_amount = payment_data['amount']
    apply_counter_payment(tx, payment_data, session.get('user_name'), session.get('user_id'))
    db.flush()
    appt.payment_status = 'Paid'
    appt.payment_method = payment_data['method']
    for q in queues:
        q.payment_status = 'Paid'
        q.payment_method = payment_data['method']
        q.transaction_id = tx.transaction_id
    return tx


@dashboard_bp.route('/api/staff/confirm-order', methods=['POST'])
def api_confirm_order():
    """Verify an order at the counter: Pending → Confirmed, assign machine(s), enqueue it, return queue number."""
    denied = _api_access('Staff', 'Manager')
    if denied:
        return denied

    payload = request.get_json(silent=True) or request.form
    raw_code = (payload.get('order_code') or '').strip()
    if not raw_code:
        return jsonify({'status': 'error', 'message': 'Order code or number is required.'}), 400

    assignments_raw = payload.get('assignments')
    machine_ids_raw = payload.get('machine_ids')
    single_machine_id = payload.get('machine_id')
    start_now = payload.get('start_now', True)
    if isinstance(start_now, str):
        start_now = start_now.lower() in ('true', '1', 'yes')

    db = SessionLocal()
    try:
        appt = find_appointment_for_verification(db, raw_code)
        if not appt:
            return jsonify({'status': 'error', 'message': f'No order found for "{raw_code}".'}), 404
        order_code = appt.order_code

        if appt.status == 'Cancelled':
            return jsonify({'status': 'error', 'message': 'This order has been cancelled and cannot be verified.'}), 409

        if appt.status == 'Completed':
            return jsonify({'status': 'error', 'message': 'This order has already been completed.'}), 409

        existing_queues = db.query(Queue).filter(Queue.appointment_id == appt.appointment_id).order_by(Queue.queue_id.asc()).all()
        expected_machines = getattr(appt, 'total_machines', 1) or 1
        all_already_assigned = (len(existing_queues) >= expected_machines) and all(q.machine_id for q in existing_queues)

        if appt.status == 'Confirmed' and all_already_assigned and not payload.get('reassign'):
            return jsonify({
                'status': 'already_verified',
                'message': 'Order is already verified and all machines are assigned in queue.',
                'queue_number': existing_queues[0].queue_number,
                'customer_name': appt.customer_name
            }), 200

        # --- Payment gate: an order cannot be assigned a machine until it is paid ---
        amount_due = Decimal(str(appt.total_amount)) if getattr(appt, 'total_amount', None) else compute_service_price(
            appt.service_type, appt.order_mode or 'Drop-Off', appt.turnaround_option or '24 Hours',
            total_machines=expected_machines
        )
        payment_data = None
        if (appt.payment_status or 'Pending') != 'Paid':
            payment_data, pay_error = validate_counter_payment(payload.get('payment'), amount_due)
            if pay_error:
                return jsonify({
                    'status': 'error', 'code': 'payment_required',
                    'message': pay_error, 'amount_due': float(amount_due)
                }), 402

        now = datetime.now()
        appt.status = 'Confirmed'
        appt.verified_at = now

        order_tx = None
        if payment_data:
            order_tx = _settle_counter_payment(db, appt, existing_queues, payment_data)
        else:
            for _q in existing_queues:
                if _q.transaction_id:
                    order_tx = db.get(Transaction, _q.transaction_id)
                    break
        initial_cycle = 'drying' if 'dry only' in (appt.service_type or '').lower() else 'washing'

        # Parse structured loads
        effective_weight = float(appt.actual_weight) if getattr(appt, 'actual_weight', None) else (float(appt.estimated_weight) if getattr(appt, 'estimated_weight', None) else None)
        parsed_loads = parse_order_loads(appt.load_details, appt.total_machines, appt.service_type, weight=effective_weight)
        if not parsed_loads:
            is_13 = (effective_weight and effective_weight > 8.0) or ('13' in (appt.load_details or '')) or ('13' in (appt.service_type or ''))
            fallback_cap = 13 if is_13 else 8
            parsed_loads = [{
                'load_index': 1,
                'capacity_kg': fallback_cap,
                'label': f"Load 1 ({fallback_cap}kg {'Titan' if fallback_cap == 13 else 'Regular'})",
                'category': 'General Laundry',
                'service_type': appt.service_type,
                'raw': getattr(appt, 'load_details', None) or f'Single Load ({fallback_cap}kg)'
            }]

        # Build load_index -> target_machine_id mapping
        target_machine_map = {}
        if isinstance(assignments_raw, list):
            for a in assignments_raw:
                idx = a.get('load_index') or a.get('load_id') or 1
                mid = a.get('machine_id')
                target_machine_map[idx] = int(mid) if mid else None
        elif isinstance(machine_ids_raw, list):
            for i, mid in enumerate(machine_ids_raw):
                idx = parsed_loads[i]['load_index'] if i < len(parsed_loads) else i + 1
                target_machine_map[idx] = int(mid) if mid else None
        elif single_machine_id:
            target_machine_map[parsed_loads[0]['load_index']] = int(single_machine_id)

        from services.queuing import QueueManager
        computed_ewt = QueueManager.calculate_current_ewt(db)

        # Determine shared queue ticket number
        if existing_queues and existing_queues[0].queue_number:
            queue_number = existing_queues[0].queue_number
        else:
            queue_number = QueueManager.generate_next_queue_number(db)

        assigned_summary = []
        started_any = False

        for i, ld in enumerate(parsed_loads):
            load_idx = ld['load_index']
            mid = target_machine_map.get(load_idx)

            # Match with existing queue row or create new
            if i < len(existing_queues):
                q = existing_queues[i]
            else:
                q = Queue(
                    queue_number=queue_number,
                    appointment_id=appt.appointment_id,
                    customer_name=appt.customer_name,
                    turnaround_option=appt.turnaround_option,
                    priority_level=appt.priority_level,
                    order_mode=appt.order_mode,
                    payment_method=appt.payment_method,
                    payment_status=appt.payment_status,
                    total_machines=getattr(appt, 'total_machines', 1) or 1,
                    created_at=now
                )
                db.add(q)
                db.flush()

            q.queue_number = queue_number
            q.verified_at = now
            q.customer_name = appt.customer_name
            q.load_details = ld['raw']
            if order_tx:
                q.transaction_id = order_tx.transaction_id
            q.payment_status = appt.payment_status
            q.payment_method = appt.payment_method
            load_svc_lower = (ld.get('service_type') or appt.service_type or '').lower()
            load_cycle = 'drying' if ('dry' in load_svc_lower and 'wash' not in load_svc_lower) else 'washing'
            if q.status != 'Processing':
                q.cycle_stage = load_cycle

            machine_obj = db.get(MachineStatus, mid) if mid else None
            if machine_obj:
                q.machine_id = machine_obj.machine_id
                m_name = machine_obj.machine_name or f"Machine {machine_obj.machine_id} (Dryer and Washer)"
                started_this = False

                if q.status == 'Processing' and machine_obj.status == 'In-Use':
                    # Already in progress on this machine
                    started_this = True
                    started_any = True
                elif start_now and is_machine_available(machine_obj):
                    cycle_type = load_cycle
                    start_machine_cycle(machine_obj, appt.customer_name or 'Walk-in customer', cycle_type)
                    q.status = 'Processing'
                    q.started_at = now
                    q.actual_wait_mins = 0
                    q.estimated_waiting_time = 0
                    q.fulfillment_status = 'In Laundry'
                    started_this = True
                    started_any = True
                else:
                    q.status = 'Waiting'
                    q.estimated_waiting_time = estimated_wait_for_machine(db, machine_obj)
                    q.fulfillment_status = 'In Queue'

                assigned_summary.append({
                    'load_index': load_idx,
                    'load_title': ld['label'],
                    'machine_id': machine_obj.machine_id,
                    'machine_name': f"{m_name} ({machine_obj.capacity_kg}kg)",
                    'status': q.status,
                    'started_immediately': started_this
                })
            else:
                q.machine_id = None
                q.status = 'Waiting'
                q.estimated_waiting_time = computed_ewt
                q.fulfillment_status = 'In Queue'
                assigned_summary.append({
                    'load_index': load_idx,
                    'load_title': ld['label'],
                    'machine_id': None,
                    'machine_name': 'Unassigned',
                    'status': 'Waiting',
                    'started_immediately': False
                })

        appt.fulfillment_status = 'In Laundry' if started_any else 'In Queue'
        db.commit()

        assigned_desc = ", ".join(f"{s['load_title']} -> {s['machine_name']}" for s in assigned_summary)
        pay_note = ''
        if payment_data:
            ref_part = f", ref {payment_data['reference']}" if payment_data['reference'] else ''
            pay_note = f" | Paid ₱{payment_data['amount']:.2f} via {payment_data['method']}{ref_part}"
        AuditService.log(
            action=AuditAction.ORDER_VERIFIED,
            entity_type='Appointment',
            entity_id=order_code,
            details=f"Verified order {order_code} for {appt.customer_name or 'Walk-in'}, queue #{queue_number}: {assigned_desc}{pay_note}"
        )
        payment_summary = None
        if payment_data:
            payment_summary = {
                'transaction_id': order_tx.transaction_id if order_tx else None,
                'method': payment_data['method'],
                'amount': float(payment_data['amount']),
                'reference': payment_data['reference'],
                'cash_tendered': float(payment_data['tendered']) if payment_data['tendered'] is not None else None,
                'change': float(payment_data['change']) if payment_data['change'] is not None else None,
            }

        first_assigned = assigned_summary[0] if assigned_summary else {}
        return jsonify({
            'status': 'success',
            'message': f"Order {order_code} verified: {assigned_desc}",
            'queue_number': queue_number,
            'customer_name': appt.customer_name,
            'service_type': appt.service_type,
            'total_machines': len(parsed_loads),
            'assigned_machines': assigned_summary,
            'assigned_machine': first_assigned.get('machine_name', 'Unassigned'),
            'machine_id': first_assigned.get('machine_id'),
            'started_immediately': started_any,
            'payment': payment_summary
        })
    except Exception as e:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db.close()


@dashboard_bp.route('/book')
@dashboard_bp.route('/walk-in')
@dashboard_bp.route('/book/walkin')
def public_walk_in_booking():
    """Public walk-in booking page — no authentication required."""
    db = SessionLocal()
    try:
        refresh_machine_cycles(db)
        lobby = QueueManager.get_lobby_status(db)
        return render_template('booking/walkin.html', lobby=lobby)
    finally:
        db.close()


@dashboard_bp.route('/api/lobby/status')
def api_lobby_status():
    """Public API returning real-time shop lobby congestion, available machines, and EWT only when full."""
    db = SessionLocal()
    try:
        refresh_machine_cycles(db)
        lobby = QueueManager.get_lobby_status(db)
        return jsonify({'status': 'success', 'data': lobby})
    finally:
        db.close()


@dashboard_bp.route('/api/manager/audit-logs')
def manager_audit_logs():
    """Returns paginated, filtered audit logs for Super Admin and Manager."""
    if not _has_role(Role.MANAGER, Role.SUPER_ADMIN):
        return jsonify({'status': 'error', 'message': 'Manager/Super Admin access required.'}), 403
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    staff_id = request.args.get('staff_id', type=int)
    action = request.args.get('action', type=str)
    search = request.args.get('search', type=str)
    result = AuditService.get_logs(page=page, limit=limit, staff_id=staff_id, action=action, search=search)
    return jsonify({'status': 'success', 'data': result})
