# routes/appointments.py
from flask import Blueprint, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
from config.database import SessionLocal
from models.schemas import Appointment, Queue
from models.schemas import MachineStatus
from services.queuing import QueueManager

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/customer/book', methods=['POST'])
def book_appointment():
    # Enforce customer structural protection
    if session.get('user_role') != 'Customer':
        return jsonify({"status": "error", "message": "Access restricted to customer accounts."}), 403

    payload = request.get_json(silent=True) or request.form
    raw_time = payload.get('schedule_time') # Format expected: YYYY-MM-DDTHH:MM
    service_type = payload.get('service_type') # Wash-Dry-Fold, Wash-Only, Dry-Only

    if not raw_time or not service_type:
        return jsonify({"status": "error", "message": "Missing scheduling dependencies."}), 400

    db = SessionLocal()
    try:
        # 1. Commit the primary appointment logging row
        parsed_time = datetime.strptime(raw_time, '%Y-%m-%dT%H:%M')
        if parsed_time <= datetime.now():
            return jsonify({"status": "error", "message": "Select a future appointment time."}), 400
        capacity = db.query(MachineStatus).filter(MachineStatus.status != 'Maintenance').count()
        booked = db.query(Appointment).filter(Appointment.schedule_time == parsed_time, Appointment.status.in_(['Pending', 'Confirmed'])).count()
        if capacity == 0 or booked >= capacity:
            return jsonify({"status": "error", "message": "That time slot is no longer available."}), 409
        new_appointment = Appointment(
            customer_id=session.get('user_id'),
            schedule_time=parsed_time,
            service_type=service_type,
            status='Pending'
        )
        db.add(new_appointment)
        db.commit() # Commits to generate appointment_id

        # 2. Push directly into active operational line allocation
        next_num = QueueManager.generate_next_queue_number()
        computed_ewt = QueueManager.calculate_current_ewt()

        new_queue_entry = Queue(
            queue_number=next_num,
            appointment_id=new_appointment.appointment_id,
            status='Waiting',
            estimated_waiting_time=computed_ewt
        )
        db.add(new_queue_entry)
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Booking successful!",
            "queue_number": next_num,
            "ewt": computed_ewt
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()
