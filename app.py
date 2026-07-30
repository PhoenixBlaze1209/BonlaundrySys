# app.py
from flask import Flask, redirect, url_for, jsonify, render_template, session, flash
from datetime import datetime
import random
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

# Register our role-based interface blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(pos_bp)
app.register_blueprint(appointments_bp)

def get_dashboard_metrics():
    return {
        "active_queue": 12,
        "est_wait_time_mins": 38,
        "machines_running": 8,
        "total_machines": 13,
        "today_revenue_php": 3240.00
    }

def get_live_activities():
    return [
        {"job_id": "JO-0042", "customer": "Maria Santos", "status": "Washing"},
        {"job_id": "JO-0043", "customer": "John Doe", "status": "Drying"},
        {"job_id": "JO-0044", "customer": "Genesis Samson", "status": "Pending"}
    ]

def calculate_predictive_analytics():
    # Dito papasok ang Predictive Analytics (PA) engine mo base sa historical logs
    # Halimbawa: Kinukuha ang trend ng parehong araw (e.g., Kapag Friday)
    current_hour = datetime.now().hour
    
    # Mock PA distribution para sa waveform/line chart
    labels = ["2 PM", "3 PM", "4 PM", "5 PM", "6 PM"]
    predicted_load = [40, 65, 85, 70, 45] # Porsyento ng load kada oras
    
    return {
        "day_title": "Friday Peak Demand",
        "insight": "System analysis predicts an 85% load increase between 2:00 PM and 6:00 PM based on monthly patterns.",
        "directive_suggestion": "High queue probability detected. It is recommended to set 3 backup dryers to 'Ready' status by 1:30 PM.",
        "predicted_peak_time": "2:30 PM",
        "estimated_load_percentage": 85,
        "chart_labels": labels,
        "chart_data": predicted_load,
        "current_date_string": datetime.now().strftime("%B %d, %Y").upper()
    }

# --- ROUTES ---

@app.route('/manager/dashboard')
def manager_dashboard():
    # I-render ang dashboard.html view
    return render_template('manager/dashboard.html')

@app.route('/api/manager/dashboard-counters', methods=['GET'])
def api_dashboard_counters():
    """Nagbabalik ng core metrics para sa 4 na card sa taas ng dashboard"""
    metrics = get_dashboard_metrics()
    return jsonify({
        "status": "success",
        "data": metrics
    })

@app.route('/api/manager/live-activity', methods=['GET'])
def api_live_activity():
    """Nagbabalik ng listahan ng mga kasalukuyang sumasalang na customers/jobs"""
    activities = get_live_activities()
    return jsonify({
        "status": "success",
        "data": activities
    })

@app.route('/api/manager/live-forecast', methods=['GET'])
def api_live_forecast():
    """Endpoint para sa Predictive Analytics section at Chart.js engine"""
    pa_data = calculate_predictive_analytics()
    return jsonify({
        "status": "success",
        "forecast": pa_data
    })

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