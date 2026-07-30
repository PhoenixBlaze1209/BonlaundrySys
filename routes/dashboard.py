# routes/dashboard.py
from flask import Blueprint, render_template, session, redirect, url_for, flash
from config.database import SessionLocal
from models.schemas import SystemSettings, Queue
from models.schemas import Appointment, Queue, User
from services.analytics_engine import AnalyticsEngine
from models.schemas import Transaction, PredictionLog, MachineStatus
from sqlalchemy import func
dashboard_bp = Blueprint('dashboard', __name__)

# Inside routes/dashboard.py update manager_home
@dashboard_bp.route('/manager/dashboard')
def manager_home():
    if session.get('user_role') != 'Manager':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
        
    db = SessionLocal()
    try:
        total_revenue = db.query(func.sum(Transaction.total_amount)).scalar() or 0.00
        total_loads = db.query(Transaction).count()
        maintenance_machines = db.query(MachineStatus).filter(MachineStatus.status == 'Maintenance').count()

        # 1. Trigger the Machine Learning Analytics Engine pipeline
        forecast = AnalyticsEngine.train_and_predict_peak_hour()

        # 2. Fetch the historical logs table for auditing validation
        audit_logs = db.query(PredictionLog).order_by(PredictionLog.prediction_id.desc()).limit(10).all()

        return render_template(
            'manager/dashboard.html',
            manager_name=session.get('user_name'),
            total_revenue=float(total_revenue),
            total_loads=total_loads,
            maintenance_machines=maintenance_machines,
            forecast=forecast,
            audit_logs=audit_logs
        )
    finally:
        db.close()


@dashboard_bp.route('/api/manager/live-forecast')
def live_forecast_api():
    # Siguraduhing tumutugma sa role verification framework ng core app mo
    if session.get('user_role') != 'Manager':
        return {"error": "Unauthorized Access Denied"}, 401
        
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
    if session.get('user_role') != 'Staff':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    db = SessionLocal()
    try:
        # Fetch operational parameters for the dynamic frontend calculator
        settings = db.query(SystemSettings).first()
        
        # Fetch active waiting queues to display on the staff dashboard
        active_queues = db.query(Queue).filter(Queue.status != 'Done').all()
        
        return render_template(
            'staff/dashboard.html', 
            settings=settings, 
            active_queues=active_queues,
            staff_name=session.get('user_name')
        )
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
            my_queue=my_queue
        )
    finally:
        db.close()