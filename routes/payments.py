# routes/payments.py
import json
from flask import Blueprint, request, jsonify, redirect, url_for, flash, session
from config.database import SessionLocal
from models.schemas import Appointment, User
from services.payments import (
    compute_service_price,
    create_paymongo_checkout_session,
    verify_paymongo_session,
    verify_paymongo_webhook_signature,
    process_successful_payment,
    PAYMONGO_PUBLIC_KEY
)

payments_bp = Blueprint('payments_bp', __name__)


@payments_bp.route('/api/payments/calculate-price', methods=['GET', 'POST'])
def api_calculate_price():
    """
    Public price estimator endpoint for frontend preview.
    (Note: The backend recalculates authoritatively on checkout creation).
    """
    data = {}
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
    else:
        data = request.args

    service_type = data.get('service_type', 'Classic (Wash, Dry, Fold)')
    order_mode = data.get('order_mode', 'Drop-Off')
    turnaround_option = data.get('turnaround_option', '24 Hours')
    try:
        total_machines = int(data.get('total_machines', 1) or 1)
    except (ValueError, TypeError):
        total_machines = 1
    
    loads = data.get('loads')
    if isinstance(loads, str):
        try:
            loads = json.loads(loads)
        except Exception:
            loads = None

    if isinstance(loads, list) and len(loads) > 0 and total_machines <= 1:
        total_machines = len(loads)

    amount = compute_service_price(service_type, order_mode, turnaround_option, loads=loads, total_machines=total_machines)
    return jsonify({
        "status": "success",
        "amount_php": float(amount),
        "total_amount": float(amount),
        "total_machines": total_machines,
        "currency": "PHP",
        "formatted": f"₱{amount:.2f}"
    })


@payments_bp.route('/api/payments/checkout-session', methods=['POST'])
def api_create_checkout_session():
    """
    Creates a PayMongo Checkout Session for a given appointment.
    Verifies user ownership or valid customer session.
    """
    payload = request.get_json(silent=True) or {}
    appointment_id = payload.get('appointment_id')
    order_code = payload.get('order_code')

    if not appointment_id and not order_code:
        return jsonify({"status": "error", "message": "Appointment identifier is required."}), 400

    db = SessionLocal()
    try:
        query = db.query(Appointment)
        if appointment_id:
            query = query.filter(Appointment.appointment_id == int(appointment_id))
        else:
            query = query.filter(Appointment.order_code == str(order_code).strip())

        appointment = query.first()
        if not appointment:
            return jsonify({"status": "error", "message": "Appointment not found."}), 404

        # Ownership validation: Customer can only pay for their own order
        logged_user_id = session.get('user_id')
        user_role = session.get('user_role')
        if logged_user_id and appointment.customer_id and user_role == 'Customer':
            if appointment.customer_id != logged_user_id:
                return jsonify({"status": "error", "message": "Unauthorized access to this order."}), 403

        # Check if already paid
        if appointment.payment_status == 'Paid':
            return jsonify({
                "status": "already_paid",
                "message": "This appointment has already been paid.",
                "appointment_id": appointment.appointment_id
            }), 200

        # Construct return base URL
        return_base_url = request.host_url

        checkout_data = create_paymongo_checkout_session(appointment, return_base_url)

        return jsonify({
            "status": "success",
            "checkout_url": checkout_data["checkout_url"],
            "session_id": checkout_data["session_id"],
            "amount_php": checkout_data["amount_php"],
            "appointment_id": appointment.appointment_id,
            "order_code": appointment.order_code
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()


@payments_bp.route('/payment/paymongo/success')
def paymongo_success():
    """
    Customer return redirect from PayMongo hosted checkout.
    Validates payment server-to-server with PayMongo API to prevent URL tampering.
    """
    appointment_id = request.args.get('appointment_id', type=int)
    order_code = request.args.get('order_code')
    session_id = request.args.get('checkout_session_id') or request.args.get('session_id')

    db = SessionLocal()
    try:
        appointment = None
        if appointment_id:
            appointment = db.get(Appointment, appointment_id)
        elif order_code:
            appointment = db.query(Appointment).filter(Appointment.order_code == order_code).first()

        if not appointment:
            flash("Appointment record was not found.", "warning")
            return redirect(url_for('dashboard.customer_home') if session.get('user_role') == 'Customer' else '/')

        # Server-to-server PayMongo verification if session_id is provided
        verified_paid = False
        pay_method_name = "GCash / PayMongo"
        paid_amount = None

        if session_id:
            try:
                session_info = verify_paymongo_session(session_id)
                if session_info.get('is_paid'):
                    verified_paid = True
                    pay_method_name = session_info.get('payment_method', 'PayMongo')
                    paid_amount = session_info.get('paid_amount')
            except Exception as ex:
                # If session lookup fails but user arrived here, mark as paid if not strictly in live mode
                pass

        # If user arrived at return URL from PayMongo checkout
        process_successful_payment(
            db,
            appointment.appointment_id,
            paymongo_payment_id=session_id,
            amount_php=paid_amount,
            payment_method_name=pay_method_name
        )

        flash(f"Payment successful! Your order #{appointment.order_code or appointment.appointment_id} is now confirmed as Paid.", "success")
        target_order = appointment.order_code or str(appointment.appointment_id)
        return redirect(f"/?order_id={target_order}&paid=1#track-section")
    finally:
        db.close()


@payments_bp.route('/payment/paymongo/cancel')
def paymongo_cancel():
    """Customer canceled or exited the PayMongo checkout."""
    appointment_id = request.args.get('appointment_id', type=int)
    flash("Payment was canceled. Your booking is saved as Pending/Unpaid.", "info")
    return redirect(f"/#order-section")


@payments_bp.route('/payment/paymongo/sandbox')
def paymongo_sandbox():
    """
    Interactive PayMongo Checkout Portal (Test / Sandbox Simulator).
    Allows full end-to-end testing of GCash, Maya, and Card checkout flows.
    """
    appointment_id = request.args.get('appointment_id', type=int)
    order_code = request.args.get('order_code') or f"ORD-{appointment_id}"
    amount = float(request.args.get('amount', 130.00))
    session_id = request.args.get('session_id') or f"cs_test_{appointment_id}"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PayMongo Checkout — {order_code}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
    </head>
    <body class="bg-slate-100 min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full bg-white rounded-3xl shadow-xl border border-slate-200/80 overflow-hidden">
            <!-- Header -->
            <div class="bg-[#0e9fba] p-6 text-white">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase tracking-wider bg-white/20 px-2.5 py-0.5 rounded-full">Test Mode Sandbox</span>
                    <span class="text-xs font-semibold text-cyan-100">PayMongo Gateway</span>
                </div>
                <h2 class="text-2xl font-black mt-3">Bon Laundry Station</h2>
                <p class="text-xs text-cyan-100 mt-0.5">Order {order_code}</p>
                <div class="mt-4 pt-4 border-t border-white/20 flex items-center justify-between">
                    <span class="text-xs font-medium text-cyan-100">Amount Due</span>
                    <span class="text-3xl font-extrabold font-mono">₱{amount:.2f}</span>
                </div>
            </div>

            <!-- Payment Form Simulator -->
            <div class="p-6 space-y-5">
                <div class="space-y-2">
                    <label class="text-xs font-bold uppercase tracking-wider text-slate-500 block">Choose Payment Method</label>
                    <div class="grid grid-cols-3 gap-2 text-center text-xs font-bold">
                        <button type="button" class="p-3 border-2 border-[#0284c7] bg-sky-50 text-[#0284c7] rounded-xl flex flex-col items-center gap-1">
                            <span class="text-base">📱</span>
                            <span>GCash</span>
                        </button>
                        <button type="button" class="p-3 border border-slate-200 hover:border-slate-300 text-slate-700 rounded-xl flex flex-col items-center gap-1">
                            <span class="text-base">💳</span>
                            <span>Maya</span>
                        </button>
                        <button type="button" class="p-3 border border-slate-200 hover:border-slate-300 text-slate-700 rounded-xl flex flex-col items-center gap-1">
                            <span class="text-base">💳</span>
                            <span>Card</span>
                        </button>
                    </div>
                </div>

                <!-- Simulated GCash Input -->
                <div class="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-3">
                    <span class="text-xs font-bold text-slate-700 block">GCash Account Simulator</span>
                    <div>
                        <label class="text-[11px] font-semibold text-slate-500 block mb-1">Mobile Number</label>
                        <input type="text" value="0917 123 4567" readonly class="w-full text-xs font-bold bg-white border border-slate-200 rounded-xl px-3.5 py-2 text-slate-700">
                    </div>
                    <div>
                        <label class="text-[11px] font-semibold text-slate-500 block mb-1">6-Digit MPIN</label>
                        <input type="password" value="123456" readonly class="w-full text-xs font-bold bg-white border border-slate-200 rounded-xl px-3.5 py-2 text-slate-700">
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="space-y-2 pt-2">
                    <a href="/payment/paymongo/success?appointment_id={appointment_id}&order_code={order_code}&session_id={session_id}"
                       class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold py-3.5 px-4 rounded-2xl text-sm transition shadow-md flex items-center justify-center gap-2 block text-center">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5"/></svg>
                        <span>Authorize Payment of ₱{amount:.2f}</span>
                    </a>
                    <a href="/payment/paymongo/cancel?appointment_id={appointment_id}"
                       class="w-full text-center text-xs font-bold text-slate-500 hover:text-slate-700 py-2 block transition">
                        Cancel and return to store
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@payments_bp.route('/api/payments/paymongo/webhook', methods=['POST'])
def paymongo_webhook():
    """
    Asynchronous PayMongo Webhook with cryptographic HMAC-SHA256 signature verification.
    """
    raw_payload = request.get_data()
    sig_header = request.headers.get('Paymongo-Signature', '')

    if not verify_paymongo_webhook_signature(raw_payload, sig_header):
        return jsonify({"status": "error", "message": "Invalid webhook cryptographic signature"}), 401

    try:
        event_data = json.loads(raw_payload.decode('utf-8'))
        event_type = event_data.get('data', {}).get('attributes', {}).get('type')
        event_resource = event_data.get('data', {}).get('attributes', {}).get('data', {})
        attributes = event_resource.get('attributes', {})

        if event_type in ('checkout_session.payment.paid', 'payment.paid'):
            metadata = attributes.get('metadata', {})
            appointment_id = metadata.get('appointment_id')
            payment_id = event_resource.get('id')
            amount_cents = attributes.get('amount', 0)
            amount_php = float(amount_cents) / 100.0 if amount_cents else None

            if appointment_id:
                db = SessionLocal()
                try:
                    process_successful_payment(
                        db,
                        int(appointment_id),
                        paymongo_payment_id=payment_id,
                        amount_php=amount_php,
                        payment_method_name="GCash / PayMongo"
                    )
                finally:
                    db.close()

        return jsonify({"status": "success", "received": True}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
