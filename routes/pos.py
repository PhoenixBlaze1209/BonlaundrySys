# routes/pos.py
from flask import Blueprint, request, jsonify, session
from config.database import SessionLocal
from models.schemas import Transaction, User
from services.pricing import POSProcessor
from services.email_service import EmailService

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
    raw_weight = payload.get('weight')
    service_code = payload.get('service_code')
    addon_codes = payload.get('addons') or []
    payment_status = payload.get('payment_status', 'Paid')

    if isinstance(addon_codes, str):
        addon_codes = [code for code in addon_codes.split(',') if code]
    
    if not raw_weight:
        return jsonify({"status": "error", "message": "Weight input field is required."}), 400
    if payment_status not in ('Pending', 'Paid'):
        return jsonify({"status": "error", "message": "Invalid payment status."}), 400
        
    # 3. Run weight validation layer through our pricing engine
    validation_result = POSProcessor.calculate_service_total(service_code, raw_weight, addon_codes)
    
    if not validation_result["success"]:
        return jsonify({"status": "error", "message": validation_result["message"]}), 400
        
    # 4. If valid, save the transactional record directly to MySQL
    db = SessionLocal()
    try:
        receipt_email = customer_email
        if customer_email and not customer_id:
            customer = db.query(User).filter(User.email == customer_email, User.user_role == 'Customer').first()
            if not customer:
                return jsonify({"status": "error", "message": "Customer email was not found."}), 404
            customer_id = customer.user_id
        new_transaction = Transaction(
            customer_id=int(customer_id) if customer_id else None,
            weight_kg=validation_result["weight"],
            total_amount=validation_result["total_amount"],
            payment_status=payment_status
        )
        db.add(new_transaction)
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
                "email": email_result
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()
