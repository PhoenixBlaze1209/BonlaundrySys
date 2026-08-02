# routes/dashboard.py
from datetime import datetime, time
from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request, Response
from config.database import SessionLocal
from models.schemas import SystemSettings, Queue
from models.schemas import Appointment, Queue, User
from services.analytics_engine import AnalyticsEngine
from services.queuing import QueueManager
from models.schemas import Transaction, PredictionLog, MachineStatus
from sqlalchemy import func
dashboard_bp = Blueprint('dashboard', __name__)


def _has_role(*roles):
    return session.get('user_role') in roles


def _api_access(*roles):
    if not _has_role(*roles):
        return jsonify({"status": "error", "message": "Unauthorized access."}), 403
    return None


def _dashboard_metrics(db, include_revenue=False):
    """Returns live operational values derived from persisted POS/queue data."""
    active_queue = db.query(Queue).filter(Queue.status.in_(['Waiting', 'Processing'])).count()
    ready_machines = db.query(MachineStatus).filter(MachineStatus.status == 'Available').count()
    total_machines = db.query(MachineStatus).count()
    total_capacity_kg = int(db.query(func.coalesce(func.sum(MachineStatus.capacity_kg), 0)).scalar())
    running_machines = db.query(MachineStatus).filter(MachineStatus.status == 'In-Use').count()
    estimated_wait = QueueManager.calculate_current_ewt()

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
    rows = (db.query(Queue, Appointment, User, MachineStatus)
            .outerjoin(Appointment, Queue.appointment_id == Appointment.appointment_id)
            .outerjoin(User, Appointment.customer_id == User.user_id)
            .outerjoin(MachineStatus, Queue.machine_id == MachineStatus.machine_id)
            .filter(Queue.status.in_(['Waiting', 'Processing']))
            .order_by(Queue.queue_number.asc()).limit(8).all())
    return [{
        "job_id": f"Q-{queue.queue_number:03d}",
        "customer": user.name if user else "Walk-in customer",
        "status": "Washing" if queue.status == 'Processing' else "Waiting",
        "machine": f"{machine.machine_type[0]}-{machine.machine_id:02d}" if machine else "Unassigned",
    } for queue, appointment, user, machine in rows]

# Inside routes/dashboard.py update manager_home
@dashboard_bp.route('/manager/dashboard')
def manager_home():
    if not _has_role('Manager'):
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
            role='Manager'
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
        
@dashboard_bp.route('/staff/dashboard')
def staff_home():
    if not _has_role('Staff'):
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    db = SessionLocal()
    try:
        # Fetch operational parameters for the dynamic frontend calculator
        settings = db.query(SystemSettings).first()
        
        # Fetch active waiting queues to display on the staff dashboard
        active_queues = db.query(Queue).filter(Queue.status != 'Done').all()
        
        return render_template('staff/dashboard.html', settings=settings,
                               active_queues=active_queues,
                               staff_name=session.get('user_name'), role='Staff')
    finally:
        db.close()

@dashboard_bp.route('/customer/dashboard')
def customer_home():
    if session.get('user_role') != 'Customer':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
        
    db = SessionLocal()
    try:
        # Fetch the customer's active waiting queue entry if it exists
        my_queue = db.query(Queue).join(Appointment).filter(
            Appointment.customer_id == session.get('user_id'),
            Queue.status != 'Done'
        ).first()
        
        return render_template(
            'customer/dashboard.html',
            customer_name=session.get('user_name'),
            my_queue=my_queue,
            role='Customer'
        )
    finally:
        db.close()


@dashboard_bp.route('/api/dashboard/summary')
def dashboard_summary():
    """Shared operational feed. Financial and prediction data are manager-only."""
    denied = _api_access('Manager', 'Staff', 'Customer')
    if denied:
        return denied
    db = SessionLocal()
    try:
        is_manager = _has_role('Manager')
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
            "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
        } for transaction, customer in rows]})
    finally:
        db.close()


@dashboard_bp.route('/api/transactions')
def transactions_api():
    denied = _api_access('Manager', 'Staff', 'Customer')
    if denied:
        return denied
    db = SessionLocal()
    try:
        query = (db.query(Transaction, User.name)
                 .outerjoin(User, Transaction.customer_id == User.user_id)
                 .order_by(Transaction.created_at.desc()).limit(50))
        rows = query.all()
        data = [{"transaction_id": tx.transaction_id, "customer": name or 'Walk-in customer',
                 "weight_kg": float(tx.weight_kg), "total_amount": float(tx.total_amount),
                 "payment_status": tx.payment_status,
                 "created_at": tx.created_at.isoformat() if tx.created_at else None}
                for tx, name in rows]
        return jsonify({'status': 'success', 'data': data})
    finally:
        db.close()


@dashboard_bp.route('/api/manager/transactions.csv')
def transactions_csv():
    denied = _api_access('Manager')
    if denied:
        return denied
    db = SessionLocal()
    try:
        rows = (db.query(Transaction, User.name).outerjoin(User, Transaction.customer_id == User.user_id)
                .order_by(Transaction.created_at.desc()).all())
        lines = ['Timestamp,Reference,Customer,Weight (kg),Amount,Payment status']
        for tx, name in rows:
            timestamp = tx.created_at.isoformat() if tx.created_at else ''
            lines.append(f'{timestamp},TRX-{tx.transaction_id:04d},"{name or "Walk-in customer"}",{float(tx.weight_kg):.2f},{float(tx.total_amount):.2f},{tx.payment_status}')
        return Response('\n'.join(lines), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=transactions.csv'})
    finally:
        db.close()


@dashboard_bp.route('/api/appointments', methods=['GET', 'POST'])
def appointments_api():
    denied = _api_access('Manager', 'Staff')
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
            booked = db.query(Appointment).filter(Appointment.schedule_time == schedule_time, Appointment.status.in_(['Pending', 'Confirmed'])).count()
            if not customer:
                return jsonify({'status': 'error', 'message': 'Customer email was not found.'}), 404
            if schedule_time <= datetime.now() or booked >= capacity:
                return jsonify({'status': 'error', 'message': 'The selected time is unavailable.'}), 409
            appointment = Appointment(customer_id=customer.user_id, schedule_time=schedule_time, service_type=service_type, status='Pending')
            db.add(appointment)
            db.flush()
            queue = Queue(queue_number=(db.query(func.max(Queue.queue_number)).scalar() or 0) + 1,
                          appointment_id=appointment.appointment_id, status='Waiting', estimated_waiting_time=QueueManager.calculate_current_ewt())
            db.add(queue)
            db.commit()
            return jsonify({'status': 'success', 'message': 'Appointment saved and added to the queue.'}), 201
        rows = (db.query(Appointment, User.name, Queue.queue_id, Queue.status)
                .outerjoin(User, Appointment.customer_id == User.user_id)
                .outerjoin(Queue, Queue.appointment_id == Appointment.appointment_id)
                .order_by(Appointment.schedule_time.asc()))
        if _has_role('Customer'):
            rows = rows.filter(Appointment.customer_id == session.get('user_id'))
        rows = rows.limit(50).all()
        return jsonify({'status': 'success', 'data': [{
            'appointment_id': appointment.appointment_id, 'customer': name or 'Walk-in customer',
            'schedule_time': appointment.schedule_time.isoformat(), 'service_type': appointment.service_type,
            'status': appointment.status, 'queue_id': queue_id, 'queue_status': queue_status
        } for appointment, name, queue_id, queue_status in rows]})
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
        booked = db.query(Appointment).filter(Appointment.schedule_time == selected, Appointment.status.in_(['Pending', 'Confirmed'])).count()
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
        appointment = db.get(Appointment, appointment_id)
        if not appointment:
            return jsonify({'status': 'error', 'message': 'Appointment not found.'}), 404
        appointment.status = 'Confirmed'
        queue = db.query(Queue).filter(Queue.appointment_id == appointment_id).first()
        if queue and queue.status == 'Waiting':
            machine = db.query(MachineStatus).filter(MachineStatus.status == 'Available').first()
            if machine:
                queue.machine_id = machine.machine_id
                queue.status = 'Processing'
                machine.status = 'In-Use'
        db.commit()
        return jsonify({'status': 'success', 'message': 'Appointment checked in.'})
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()


@dashboard_bp.route('/api/queue', methods=['GET', 'POST'])
def queue_api():
    denied = _api_access('Manager', 'Staff')
    if denied:
        return denied
    db = SessionLocal()
    try:
        if request.method == 'POST':
            last = db.query(func.max(Queue.queue_number)).scalar() or 0
            queue = Queue(queue_number=last + 1, status='Waiting', estimated_waiting_time=_dashboard_metrics(db)['est_wait_time_mins'])
            db.add(queue)
            db.commit()
            return jsonify({'status': 'success', 'message': 'Walk-in added to queue.', 'data': {'queue_id': queue.queue_id, 'queue_number': queue.queue_number}}), 201
        rows = (db.query(Queue, Appointment, User, MachineStatus)
                .outerjoin(Appointment, Queue.appointment_id == Appointment.appointment_id)
                .outerjoin(User, Appointment.customer_id == User.user_id)
                .outerjoin(MachineStatus, Queue.machine_id == MachineStatus.machine_id)
                .filter(Queue.status != 'Done').order_by(Queue.queue_number.asc()).all())
        return jsonify({'status': 'success', 'data': [{
            'queue_id': queue.queue_id, 'queue_number': queue.queue_number, 'customer': name or 'Walk-in customer',
            'service_type': appointment.service_type if appointment else 'Walk-in', 'status': queue.status,
            'machine': f'{machine.machine_type[0]}-{machine.machine_id:02d}' if machine else 'Unassigned'
        } for queue, appointment, name, machine in rows]})
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
        queue = db.get(Queue, queue_id)
        if not queue:
            return jsonify({'status': 'error', 'message': 'Queue entry not found.'}), 404
        if queue.status == 'Waiting':
            machine = db.query(MachineStatus).filter(MachineStatus.status == 'Available').first()
            if not machine:
                return jsonify({'status': 'error', 'message': 'No available machine.'}), 409
            queue.status, queue.machine_id, machine.status = 'Processing', machine.machine_id, 'In-Use'
        elif queue.status == 'Processing':
            queue.status = 'Done'
            if queue.machine_id:
                machine = db.get(MachineStatus, queue.machine_id)
                if machine and machine.status == 'In-Use':
                    machine.status = 'Available'
        db.commit()
        return jsonify({'status': 'success', 'message': 'Queue status updated.'})
    except Exception as error:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(error)}), 500
    finally:
        db.close()
