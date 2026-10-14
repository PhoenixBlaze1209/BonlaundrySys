# app.py
from flask import Flask, redirect, url_for, jsonify, send_from_directory, render_template, session
from sqlalchemy import inspect, text
from config.database import engine, Base, SessionLocal
from werkzeug.middleware.proxy_fix import ProxyFix
# Import ALL models here so Base knows they exist for auto-generation
from models.schemas import User, Appointment, MachineStatus, Transaction, Queue, SystemSettings, PredictionLog
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.pos import pos_bp
from routes.appointments import appointments_bp
from routes.machines import machines_bp
from routes.payments import payments_bp
from routes.bot import bot_bp

app = Flask(__name__)
app.secret_key = "super_secret_bon_laundry_key_for_sessions"
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Automatically create the MySQL tables based on our schemas if they don't exist yet
Base.metadata.create_all(bind=engine)


def apply_schema_updates():
    """Small additive migration for installations created before these fields existed."""
    columns = {
        'tbl_users': {
            'google_id': 'VARCHAR(100) NULL', 'avatar_url': 'VARCHAR(255) NULL',
            'failed_login_attempts': 'INT NOT NULL DEFAULT 0', 'login_locked_until': 'DATETIME NULL',
            'password_reset_token': 'VARCHAR(128) NULL', 'password_reset_expires_at': 'DATETIME NULL'},
        'tbl_machine_status': {
            'machine_name': 'VARCHAR(50) NULL', 'price_per_cycle': 'DECIMAL(10,2) NOT NULL DEFAULT 145.00',
            'operational_state': "VARCHAR(20) NOT NULL DEFAULT 'available'", 'assigned_customer_name': 'VARCHAR(100) NULL',
            'cycle_type': 'VARCHAR(20) NULL', 'cycle_started_at': 'DATETIME NULL', 'cycle_ends_at': 'DATETIME NULL',
            'usage_count': 'INT NOT NULL DEFAULT 0', 'last_used_at': 'DATETIME NULL'},
        'tbl_transaction': {
            'customer_name': 'VARCHAR(100) NULL', 'machine_id': 'INT NULL', 'cycle_type': 'VARCHAR(20) NULL',
            'payment_method': 'VARCHAR(50) NULL', 'payment_reference': 'VARCHAR(30) NULL',
            'cash_tendered': 'DECIMAL(10,2) NULL', 'change_given': 'DECIMAL(10,2) NULL',
            'processed_by': 'VARCHAR(100) NULL', 'processed_by_id': 'INT NULL'},
        'tbl_queue': {
            'customer_name': 'VARCHAR(100) NULL', 'transaction_id': 'INT NULL', 'cycle_stage': 'VARCHAR(20) NULL',
            'load_details': 'VARCHAR(500) NULL', 'total_machines': 'INT NOT NULL DEFAULT 1',
            'turnaround_option': 'VARCHAR(30) NULL', 'priority_level': "VARCHAR(30) NOT NULL DEFAULT 'Standard'",
            'order_mode': "VARCHAR(30) NOT NULL DEFAULT 'Drop-Off'",
            'payment_method': "VARCHAR(50) NOT NULL DEFAULT 'Cash'",
            'payment_status': "VARCHAR(30) NOT NULL DEFAULT 'Pending'",
            'fulfillment_status': "VARCHAR(50) NOT NULL DEFAULT 'Received'"
        },
        'tbl_appointment': {
            'order_code': 'VARCHAR(30) NULL', 'customer_name': 'VARCHAR(100) NULL',
            'customer_email': 'VARCHAR(100) NULL', 'phone_number': 'VARCHAR(30) NULL',
            'address': 'VARCHAR(255) NULL', 'pickup_time': 'VARCHAR(50) NULL',
            'load_details': 'VARCHAR(500) NULL', 'total_machines': 'INT NOT NULL DEFAULT 1',
            'turnaround_option': 'VARCHAR(30) NULL', 'priority_level': "VARCHAR(30) NOT NULL DEFAULT 'Standard'",
            'order_mode': "VARCHAR(30) NOT NULL DEFAULT 'Drop-Off'",
            'payment_method': "VARCHAR(50) NOT NULL DEFAULT 'Cash'",
            'payment_status': "VARCHAR(30) NOT NULL DEFAULT 'Pending'",
            'fulfillment_status': "VARCHAR(50) NOT NULL DEFAULT 'Received'"
        }
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, additions in columns.items():
            if table in inspector.get_table_names():
                existing = {column['name'] for column in inspector.get_columns(table)}
                for name, definition in additions.items():
                    if name not in existing:
                        connection.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {definition}'))
        try:
            with engine.begin() as connection:
                connection.execute(text('ALTER TABLE tbl_users MODIFY COLUMN password VARCHAR(255) NULL'))
                connection.execute(text("ALTER TABLE tbl_machine_status MODIFY COLUMN machine_type VARCHAR(50) NOT NULL DEFAULT 'Dryer and Washer'"))
        except Exception:
            pass


apply_schema_updates()


def ensure_machine_inventory():
    """Initializes the declared 19-machine fleet once, and ensures standard Machine X (Dryer and Washer) naming."""
    db = SessionLocal()
    try:
        regular_count = db.query(MachineStatus).filter(MachineStatus.capacity_kg == 8).count()
        titan_count = db.query(MachineStatus).filter(MachineStatus.capacity_kg == 13).count()
        if regular_count < 14:
            db.add_all([
                MachineStatus(
                    machine_type='Dryer and Washer',
                    machine_name=f'Machine {regular_count + index + 1} (Dryer and Washer)',
                    capacity_kg=8,
                    price_per_cycle=145.00,
                    status='Available'
                ) for index in range(14 - regular_count)
            ])
        if titan_count < 5:
            db.add_all([
                MachineStatus(
                    machine_type='Dryer and Washer',
                    machine_name=f'Machine {14 + titan_count + index + 1} (Dryer and Washer)',
                    capacity_kg=13,
                    price_per_cycle=240.00,
                    status='Available'
                ) for index in range(5 - titan_count)
            ])
        if regular_count < 14 or titan_count < 5:
            db.commit()

        # Update any existing machines without specific names or using old naming convention
        machines = db.query(MachineStatus).all()
        for m in machines:
            if m.machine_type in ('Washer', 'Dryer', None):
                m.machine_type = 'Dryer and Washer'
            if (not m.machine_name or 
                m.machine_name.startswith('Regular ') or 
                m.machine_name.startswith('Titan ') or 
                m.machine_name == f'Machine {m.machine_id}'):
                m.machine_name = f'Machine {m.machine_id} (Dryer and Washer)'
        db.commit()
    finally:
        db.close()


ensure_machine_inventory()


@app.route('/logo.webp')
def logo():
    return send_from_directory(app.root_path, 'logo.webp')

# Register our role-based interface blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(pos_bp)
app.register_blueprint(appointments_bp)
app.register_blueprint(machines_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(bot_bp)

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/test-db')
def test_db():
    db = SessionLocal()
    try:
        # Simple query verification to ensure port 3307 remains accessible
        db.execute(text("SELECT 1"))
        return jsonify({"status": "success", "message": "Database connection verified."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()


@app.context_processor
def inject_user_context():
    """Exposes current role, underlying base role, and switching permissions to templates."""
    user_id = session.get('user_id')
    base_user_role = session.get('base_user_role')
    active_role = session.get('user_role')

    if user_id and not base_user_role:
        db = SessionLocal()
        try:
            u = db.get(User, user_id)
            if u:
                base_user_role = u.user_role
                session['base_user_role'] = base_user_role
        finally:
            db.close()

    return {
        'current_user_role': active_role,
        'base_user_role': base_user_role or active_role,
        'can_switch_role': (base_user_role == 'Super Admin')
    }

if __name__ == '__main__':
    # Bind to 0.0.0.0 so both IPv4 and tunnels can connect cleanly
    app.run(debug=True, host='0.0.0.0', port=5000)
