# models/schemas.py
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.sql import func
from config.database import Base

class User(Base):
    __tablename__ = 'tbl_users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    user_role = Column(Enum('Manager', 'Staff', 'Customer'), nullable=False)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    login_locked_until = Column(DateTime, nullable=True)
    password_reset_token = Column(String(128), nullable=True)
    password_reset_expires_at = Column(DateTime, nullable=True)

class Appointment(Base):
    __tablename__ = 'tbl_appointment'
    
    appointment_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('tbl_users.user_id'))
    schedule_time = Column(DateTime, nullable=False)
    service_type = Column(Enum('Wash-Dry-Fold', 'Wash-Only', 'Dry-Only'), nullable=False)
    status = Column(Enum('Pending', 'Confirmed', 'Completed', 'Cancelled'), default='Pending')

class MachineStatus(Base):
    __tablename__ = 'tbl_machine_status'
    
    machine_id = Column(Integer, primary_key=True, autoincrement=True)
    machine_type = Column(Enum('Washer', 'Dryer'), nullable=False)
    capacity_kg = Column(Integer, default=8)
    status = Column(Enum('Available', 'In-Use', 'Maintenance'), default='Available')
    machine_name = Column(String(50), nullable=True)
    price_per_cycle = Column(DECIMAL(10, 2), nullable=False, default=145.00)
    operational_state = Column(String(20), nullable=False, default='available')
    assigned_customer_name = Column(String(100), nullable=True)
    cycle_type = Column(String(20), nullable=True)
    cycle_started_at = Column(DateTime, nullable=True)
    cycle_ends_at = Column(DateTime, nullable=True)

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

class Queue(Base):
    __tablename__ = 'tbl_queue'
    
    queue_id = Column(Integer, primary_key=True, autoincrement=True)
    queue_number = Column(Integer, nullable=False)
    appointment_id = Column(Integer, ForeignKey('tbl_appointment.appointment_id'), nullable=True)
    machine_id = Column(Integer, ForeignKey('tbl_machine_status.machine_id'), nullable=True)
    status = Column(Enum('Waiting', 'Processing', 'Done'), default='Waiting')
    estimated_waiting_time = Column(Integer, default=0)
    customer_name = Column(String(100), nullable=True)
    transaction_id = Column(Integer, nullable=True)

class SystemSettings(Base):
    __tablename__ = 'tbl_system_settings'
    
    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    price_per_kg = Column(DECIMAL(10, 2), nullable=False, default=65.00)
    max_weight_limit_kg = Column(Integer, nullable=False, default=8)
    standard_washer_time_mins = Column(Integer, nullable=False, default=35)
    standard_dryer_time_mins = Column(Integer, nullable=False, default=30)

class PredictionLog(Base):
    __tablename__ = 'tbl_prediction_logs'
    
    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_target = Column(String(50), nullable=False)
    predicted_value = Column(String(100), nullable=False)
    actual_value = Column(String(100), nullable=True)
    mape_score = Column(DECIMAL(5, 2), nullable=True)
    logged_at = Column(TIMESTAMP, server_default=func.now())
