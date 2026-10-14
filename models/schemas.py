# models/schemas.py
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.sql import func
from config.database import Base

class User(Base):
    __tablename__ = 'tbl_users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=True)
    user_role = Column(Enum('Super Admin', 'Manager', 'Staff', 'Customer'), nullable=False)
    google_id = Column(String(100), unique=True, nullable=True)
    avatar_url = Column(String(255), nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    login_locked_until = Column(DateTime, nullable=True)
    password_reset_token = Column(String(128), nullable=True)
    password_reset_expires_at = Column(DateTime, nullable=True)

class Appointment(Base):
    __tablename__ = 'tbl_appointment'
    
    appointment_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('tbl_users.user_id'), nullable=True)
    order_code = Column(String(30), unique=True, index=True, nullable=True)
    customer_name = Column(String(100), nullable=True)
    customer_email = Column(String(100), nullable=True)
    phone_number = Column(String(30), nullable=True)
    address = Column(String(255), nullable=True)
    pickup_time = Column(String(50), nullable=True)
    schedule_time = Column(DateTime, nullable=False)
    service_type = Column(String(255), nullable=False)
    load_details = Column(String(500), nullable=True)
    estimated_weight = Column(DECIMAL(5, 2), nullable=True)
    actual_weight = Column(DECIMAL(5, 2), nullable=True)
    addons = Column(String(500), nullable=True)
    total_amount = Column(DECIMAL(10, 2), nullable=True)
    total_machines = Column(Integer, nullable=False, default=1)
    turnaround_option = Column(String(30), nullable=True, default='24 Hours')
    priority_level = Column(String(30), nullable=True, default='Standard')
    order_mode = Column(String(30), nullable=True, default='Drop-Off')
    payment_method = Column(String(50), nullable=True, default='Cash')
    payment_status = Column(String(30), nullable=True, default='Pending')
    fulfillment_status = Column(String(50), nullable=True, default='Received')
    status = Column(Enum('Pending', 'Confirmed', 'Completed', 'Cancelled'), default='Pending')
    cancellation_reason = Column(String(255), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    refund_status = Column(String(50), nullable=True)
    cancellation_otp = Column(String(10), nullable=True)
    cancellation_otp_expires_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)


class MachineStatus(Base):
    __tablename__ = 'tbl_machine_status'
    
    machine_id = Column(Integer, primary_key=True, autoincrement=True)
    machine_type = Column(String(50), nullable=False, default='Dryer and Washer')
    capacity_kg = Column(Integer, default=8)
    status = Column(Enum('Available', 'In-Use', 'Maintenance'), default='Available')
    machine_name = Column(String(50), nullable=True)
    price_per_cycle = Column(DECIMAL(10, 2), nullable=False, default=145.00)
    operational_state = Column(String(20), nullable=False, default='available')
    assigned_customer_name = Column(String(100), nullable=True)
    cycle_type = Column(String(20), nullable=True)
    cycle_started_at = Column(DateTime, nullable=True)
    cycle_ends_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime, nullable=True)

class Transaction(Base):
    __tablename__ = 'tbl_transaction'
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('tbl_users.user_id'), nullable=True)
    weight_kg = Column(DECIMAL(4, 2), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    payment_status = Column(Enum('Pending', 'Paid'), default='Pending')
    created_at = Column(TIMESTAMP, server_default=func.now())
    customer_name = Column(String(100), nullable=True)
    machine_id = Column(Integer, nullable=True)
    cycle_type = Column(String(20), nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(30), nullable=True)
    cash_tendered = Column(DECIMAL(10, 2), nullable=True)
    change_given = Column(DECIMAL(10, 2), nullable=True)
    processed_by = Column(String(100), nullable=True)
    processed_by_id = Column(Integer, nullable=True)

class Queue(Base):
    __tablename__ = 'tbl_queue'
    
    queue_id = Column(Integer, primary_key=True, autoincrement=True)
    queue_number = Column(Integer, nullable=False)
    appointment_id = Column(Integer, ForeignKey('tbl_appointment.appointment_id'), nullable=True)
    machine_id = Column(Integer, ForeignKey('tbl_machine_status.machine_id'), nullable=True)
    status = Column(Enum('Waiting', 'Processing', 'Done'), default='Waiting')
    turnaround_option = Column(String(30), nullable=True, default='24 Hours')
    priority_level = Column(String(30), nullable=True, default='Standard')
    order_mode = Column(String(30), nullable=True, default='Drop-Off')
    payment_method = Column(String(50), nullable=True, default='Cash')
    payment_status = Column(String(30), nullable=True, default='Pending')
    fulfillment_status = Column(String(50), nullable=True, default='Received')
    estimated_waiting_time = Column(Integer, default=0)
    customer_name = Column(String(100), nullable=True)
    load_details = Column(String(500), nullable=True)
    total_machines = Column(Integer, nullable=False, default=1)
    transaction_id = Column(Integer, nullable=True)
    cycle_stage = Column(String(20), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    actual_wait_mins = Column(DECIMAL(6, 2), nullable=True)
    cycle_completed_at = Column(DateTime, nullable=True)
    penalty_amount = Column(DECIMAL(10, 2), default=0.00)
    penalty_reason = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)

class SystemSettings(Base):
    __tablename__ = 'tbl_system_settings'
    
    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    price_per_kg = Column(DECIMAL(10, 2), nullable=False, default=65.00)
    max_weight_limit_kg = Column(Integer, nullable=False, default=8)
    standard_washer_time_mins = Column(Integer, nullable=False, default=39)
    standard_dryer_time_mins = Column(Integer, nullable=False, default=40)
    late_retrieval_grace_mins = Column(Integer, nullable=False, default=10)
    late_retrieval_penalty_fee = Column(DECIMAL(10, 2), nullable=False, default=100.00)

class PredictionLog(Base):
    __tablename__ = 'tbl_prediction_logs'
    
    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_target = Column(String(50), nullable=False)
    predicted_value = Column(String(100), nullable=False)
    actual_value = Column(String(100), nullable=True)
    mape_score = Column(DECIMAL(5, 2), nullable=True)
    logged_at = Column(TIMESTAMP, server_default=func.now())


class AuditLog(Base):
    __tablename__ = 'tbl_audit_logs'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('tbl_users.user_id'), nullable=True)
    user_name = Column(String(100), nullable=True)
    user_email = Column(String(100), nullable=True)
    user_role = Column(String(30), nullable=True)
    action = Column(String(80), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(50), nullable=True)
    details = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

