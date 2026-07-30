# routes/pos.py
from flask import Blueprint, request, jsonify, session
from config.database import SessionLocal
from models.schemas import Transaction
from services.pricing import POSProcessor

pos_bp = Blueprint('pos', __name__)

@pos_bp.route('/pos/checkout', methods=['POST'])
def checkout():
    # 1. Security Check: Enforce Role-Based Access Control (RBAC)
    if session.get('user_role') not in ['Staff', 'Manager']:
        return jsonify({"status": "error", "message": "Unauthorized access profile."}), 403
        
    # 2. Grab payload inputs
    customer_id = request.form.get('customer_id') # Can be empty/null for walk-in guest customers
    raw_weight = request.form.get('weight')
    payment_status = request.form.get('payment_status', 'Pending') # Pending or Paid
    
    if not raw_weight:
        return jsonify({"status": "error", "message": "Weight input field is required."}), 400
        
    # 3. Run weight validation layer through our pricing engine
    validation_result = POSProcessor.validate_and_calculate(raw_weight)
    
    if not validation_result["success"]:
        return jsonify({"status": "error", "message": validation_result["message"]}), 400
        
    # 4. If valid, save the transactional record directly to MySQL
    db = SessionLocal()
    try:
        new_transaction = Transaction(
            customer_id=int(customer_id) if customer_id else None,
            weight_kg=validation_result["weight"],
            total_amount=validation_result["total_amount"],
            payment_status=payment_status
        )
        db.add(new_transaction)
        db.commit()
        
        return jsonify({
            "status": "success",
            "message": "Transaction recorded cleanly.",
            "data": {
                "transaction_id": new_transaction.transaction_id,
                "weight_kg": float(new_transaction.weight_kg),
                "total_amount": float(new_transaction.total_amount),
                "payment_status": new_transaction.payment_status
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()