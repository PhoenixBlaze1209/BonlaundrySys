# app.py
from flask import Flask, redirect, url_for, jsonify, send_from_directory
from config.database import engine, Base, SessionLocal
# Import ALL models here so Base knows they exist for auto-generation
from models.schemas import User, Appointment, MachineStatus, Transaction, Queue, SystemSettings, PredictionLog
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.pos import pos_bp
from routes.appointments import appointments_bp

app = Flask(__name__)
app.secret_key = "super_secret_bon_laundry_key_for_sessions"

# Automatically create the MySQL tables based on our schemas if they don't exist yet
Base.metadata.create_all(bind=engine)


def ensure_machine_inventory():
    """Initializes the declared 19-machine fleet once, without overwriting live statuses."""
    db = SessionLocal()
    try:
        regular_count = db.query(MachineStatus).filter(MachineStatus.capacity_kg == 8).count()
        titan_count = db.query(MachineStatus).filter(MachineStatus.capacity_kg == 13).count()
        if regular_count < 14:
            db.add_all([MachineStatus(machine_type='Washer', capacity_kg=8, status='Available') for _ in range(14 - regular_count)])
        if titan_count < 5:
            db.add_all([MachineStatus(machine_type='Dryer', capacity_kg=13, status='Available') for _ in range(5 - titan_count)])
        if regular_count < 14 or titan_count < 5:
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

@app.route('/')
def index():
    # Automatically route incoming root traffic straight to the login interface
    return redirect(url_for('auth.login'))

@app.route('/test-db')
def test_db():
    db = SessionLocal()
    try:
        # Simple query verification to ensure port 3307 remains accessible
        db.execute("SELECT 1")
        return jsonify({"status": "success", "message": "Database connection verified."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    # Debug mode is active to auto-reload your changes during development
    app.run(debug=True, port=5000)
