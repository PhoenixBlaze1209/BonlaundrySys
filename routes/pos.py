# routes/pos.py
from flask import Blueprint, request, jsonify, session
from config.database import SessionLocal
from models.schemas import Transaction, User, Queue, MachineStatus
from services.pricing import POSProcessor
from services.email_service import EmailService
from services.machines import refresh_machine_cycles, start_machine_cycle

pos_bp = Blueprint('pos', __name__)

@pos_bp.route('/pos/checkout', methods=['POST'])
def checkout():
    # 1. Security Check: Enforce Role-Based Access Control (RBAC)
    if session.get('user_role') not in ['Staff', 'Manager']:
        return jsonify({"status": "error", "message": "Unauthorized access profile."}), 403
        
    # 2. Grab payload inputs
    payload = request.get_json(silent=True) or request.form
    customer_id = payload.get('customer_id') # Can be empty/null for walk-in guest customers
    customer_email = (payload.get('customer_email') or '').strip().lower()
    customer_name = (payload.get('customer_name') or '').strip()
    selected_machine_id = payload.get('machine_id')
    cycle_type = payload.get('cycle_type')
    raw_weight = payload.get('weight')
    service_code = payload.get('service_code')
    addon_codes = payload.get('addons') or []
    payment_status = payload.get('payment_status', 'Paid')

    if isinstance(addon_codes, str):
        addon_codes = [code for code in addon_codes.split(',') if code]
    
    if payment_status not in ('Pending', 'Paid'):
        return jsonify({"status": "error", "message": "Invalid payment status."}), 400
    if not customer_name or not selected_machine_id:
        return jsonify({"status": "error", "message": "Customer name and a selected machine are required."}), 400
        
    # 3. Run weight validation layer through our pricing engine
    validation_result = POSProcessor.calculate_service_total(service_code, raw_weight, addon_codes)
    
    if not validation_result["success"]:
        return jsonify({"status": "error", "message": validation_result["message"]}), 400
        
    # 4. If valid, save the transactional record directly to MySQL
    db = SessionLocal()
    try:
        refresh_machine_cycles(db)
        receipt_email = customer_email
        if customer_email and not customer_id:
            customer = db.query(User).filter(User.email == customer_email, User.user_role == 'Customer').first()
            # A receipt may be sent to a walk-in email address. Link the
            # transaction only when that email already belongs to a customer.
            if customer:
                customer_id = customer.user_id
        new_transaction = Transaction(
            customer_id=int(customer_id) if customer_id else None,
            weight_kg=validation_result["weight"],
            total_amount=validation_result["total_amount"],
            payment_status=payment_status, customer_name=customer_name,
            machine_id=int(selected_machine_id), cycle_type=cycle_type
        )
        db.add(new_transaction)
        machine = db.get(MachineStatus, int(selected_machine_id))
        if not machine or machine.capacity_kg < validation_result['weight']:
            return jsonify({'status': 'error', 'message': 'Selected machine cannot handle this load.'}), 409
        start_machine_cycle(machine, customer_name, cycle_type)
        last_queue = db.query(Queue).order_by(Queue.queue_number.desc()).first()
        next_queue_number = (last_queue.queue_number if last_queue else 0) + 1
        queue_entry = Queue(
            queue_number=next_queue_number,
            machine_id=machine.machine_id, status='Processing', estimated_waiting_time=0,
            customer_name=customer_name
        )
        db.add(queue_entry)
        db.flush()
        queue_entry.transaction_id = new_transaction.transaction_id
        db.commit()

        email_result = {'sent': False, 'message': 'Receipt email is available for paid customer transactions only.'}
        if payment_status == 'Paid' and receipt_email:
            email_result = EmailService.send_receipt(
                receipt_email, new_transaction.transaction_id, float(new_transaction.total_amount), validation_result['service_label']
            )
        
        return jsonify({
            "status": "success",
            "message": "Transaction recorded cleanly.",
            "data": {
                "transaction_id": new_transaction.transaction_id,
                "weight_kg": float(new_transaction.weight_kg),
                "total_amount": float(new_transaction.total_amount),
                "payment_status": new_transaction.payment_status,
                "service_label": validation_result['service_label'],
                "addons": validation_result['addons'],
                "email": email_result,
                "queue": {
                    "queue_number": queue_entry.queue_number,
                    "status": queue_entry.status,
                    "machine": machine.machine_name or f"Machine {machine.machine_id}",
                    "estimated_waiting_time": queue_entry.estimated_waiting_time
                }
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()
