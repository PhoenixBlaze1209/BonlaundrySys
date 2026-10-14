# routes/appointments.py
import re
import secrets
from datetime import datetime, date, time, timedelta
from flask import Blueprint, request, jsonify, session
from sqlalchemy import or_
from config.database import SessionLocal
from models.schemas import Appointment, Queue, MachineStatus
from decimal import Decimal
from services.queuing import QueueManager
from services.email_service import EmailService
from services.sms_service import SMSService
from services.machines import refresh_machine_cycles
from services.payments import compute_service_price

appointments_bp = Blueprint('appointments', __name__)


def _generate_unique_order_code(db):
    """Generates a friendly unique Order ID like ORD-84920."""
    for _ in range(10):
        code = f"ORD-{secrets.randbelow(90000) + 10000}"
        if not db.query(Appointment).filter(Appointment.order_code == code).first():
            return code
    return f"ORD-{secrets.randbelow(900000) + 100000}"


@appointments_bp.route('/api/order/create', methods=['POST'])
def create_order():
    """Public customer order placement matching the mobile UI design."""
    payload = request.get_json(silent=True) or request.form
    service_type = (payload.get('service_type') or 'Drop-off Service').strip()
    raw_date = (payload.get('date') or payload.get('schedule_date') or '').strip()
    raw_schedule = (payload.get('schedule_time') or '').strip()
    pickup_time = (payload.get('pickup_time') or payload.get('time') or '').strip()
    
    logged_user_id = session.get('user_id')
    logged_name = session.get('user_name')
    logged_email = session.get('user_email')
    
    name = (payload.get('name') or payload.get('customer_name') or logged_name or '').strip()
    phone = (payload.get('phone_number') or payload.get('phone') or '').strip()
    email = (payload.get('email') or payload.get('customer_email') or logged_email or '').strip().lower()
    
    building = (payload.get('building') or payload.get('deca_building') or '').strip()
    unit = (payload.get('unit') or payload.get('unit_number') or '').strip()
    address = (payload.get('address') or '').strip()

    order_mode = (payload.get('order_mode') or payload.get('handling_mode') or payload.get('mode') or ('Pick-up & Delivery' if 'pick' in (payload.get('service_type') or '').lower() else 'Drop-Off')).strip()
    is_self_service = 'self' in order_mode.lower() or 'self' in (payload.get('service_type') or '').lower()
    if is_self_service:
        turnaround_option = None
    else:
        turnaround_option = (payload.get('turnaround_option') or payload.get('turnaround') or '24 Hours').strip()
    payment_method = (payload.get('payment_method') or payload.get('payment') or 'Cash').strip()

    # Parse Add-Ons
    raw_addons = payload.get('addons')
    addons_list = []
    if raw_addons:
        if isinstance(raw_addons, list):
            addons_list = raw_addons
        elif isinstance(raw_addons, str):
            try:
                import json
                parsed_a = json.loads(raw_addons)
                addons_list = parsed_a if isinstance(parsed_a, list) else [raw_addons]
            except Exception:
                addons_list = [a.strip() for a in raw_addons.split(',') if a.strip()]
    clean_addons_names = []
    for item in addons_list:
        if isinstance(item, dict):
            clean_addons_names.append(item.get('name', 'Addon'))
        elif isinstance(item, str):
            clean_addons_names.append(item)
    addons_str = ", ".join(clean_addons_names) if clean_addons_names else None

    # Payment status rule: All new orders start as 'Pending' until verified via PayMongo or collected by staff
    payment_status = 'Pending'
    is_online_payment = any(k in payment_method.lower() for k in ('gcash', 'wallet', 'maya', 'card', 'online', 'paymongo', 'bank', 'transfer'))

    # Initial fulfillment status
    if 'pick' in order_mode.lower():
        fulfillment_status = 'For Pickup'
    else:
        fulfillment_status = 'Waiting Drop-off'
    
    # Priority level assignment: 2-Day economy orders are batched for off-peak / graveyard overnight shift
    if is_self_service or 'walk' in order_mode.lower():
        priority_level = 'Immediate'
    elif turnaround_option and ('2 day' in turnaround_option.lower() or '48' in turnaround_option.lower()):
        priority_level = 'Graveyard Batch'
    elif turnaround_option and ('24' in turnaround_option.lower() or 'express' in turnaround_option.lower()):
        priority_level = 'Express 24h'
    else:
        priority_level = 'Standard'

    # Multi-load & Machine capacity separation parsing
    loads_data = payload.get('loads')
    loads_list = []
    if loads_data:
        if isinstance(loads_data, str):
            try:
                import json
                loads_list = json.loads(loads_data)
            except Exception:
                loads_list = []
        elif isinstance(loads_data, list):
            loads_list = loads_data

    total_machines = int(payload.get('total_machines') or (len(loads_list) if loads_list else 1))
    load_details = (payload.get('load_details') or '').strip()

    # Multi-load & Machine capacity separation parsing
    loads_capacity = sum(float(ld.get('capacity', 8) or 8) for ld in loads_list) if loads_list else None
    direct_capacity = payload.get('machine_capacity') or payload.get('capacity')
    if direct_capacity:
        try:
            direct_capacity = float(str(direct_capacity).replace('kg', '').strip())
        except (ValueError, TypeError):
            direct_capacity = None

    # Estimated weight parsing
    raw_est_weight = payload.get('estimated_weight') or payload.get('weight')
    estimated_weight = None
    if raw_est_weight:
        try:
            estimated_weight = round(float(raw_est_weight), 2)
        except (ValueError, TypeError):
            estimated_weight = None

    # Guarantee machine capacity chosen by customer matches estimated weight:
    # If customer selected a 13kg Titan machine (or multi-load), match estimated weight to chosen capacity
    if loads_capacity:
        if not estimated_weight or (estimated_weight <= 8.0 and loads_capacity > 8.0):
            estimated_weight = round(loads_capacity, 2)
    elif direct_capacity and direct_capacity >= 13:
        if not estimated_weight or estimated_weight <= 8.0:
            estimated_weight = round(direct_capacity * total_machines, 2)
    elif load_details:
        ld_lower = load_details.lower()
        if ('13kg' in ld_lower or 'titan' in ld_lower) and (not estimated_weight or estimated_weight <= 8.0):
            estimated_weight = 13.0 * total_machines

    is_titan_service = ('titan' in service_type.lower() or '13' in service_type.lower())
    if not estimated_weight:
        estimated_weight = (13.0 if is_titan_service else 8.0) * total_machines

    if loads_list:
        parts = []
        for idx, ld in enumerate(loads_list, start=1):
            cap = int(ld.get('capacity', 8) or 8)
            cat = ld.get('category', 'Clothes')
            pkg = ld.get('service_type') or service_type
            mac_label = "13kg Titan" if cap >= 13 else "8kg Regular"
            parts.append(f"Load {idx} [{mac_label}: {cat} ({pkg})]")
        load_details = f"{len(loads_list)} Machines: " + "; ".join(parts)
        if estimated_weight:
            load_details += f" | Est. Weight: {estimated_weight}kg"
    elif not load_details:
        if estimated_weight and estimated_weight > 13.0 and total_machines <= 1:
            total_machines = max(2, int((estimated_weight + 7.9) // 8))
            load_details = f"{total_machines} Machines (8kg Regular) | Est. Weight: {estimated_weight}kg"
        elif estimated_weight and estimated_weight > 8.0 and total_machines <= 1:
            total_machines = 1
            load_details = f"1 Machine (13kg Titan) | Est. Weight: {estimated_weight}kg"
        else:
            load_details = f"{total_machines} Machine{'s' if total_machines > 1 else ''} ({'13kg Titan' if is_titan_service or (estimated_weight and estimated_weight > 8.0 and total_machines == 1) else '8kg Regular'})"
            if estimated_weight:
                load_details += f" | Est. Weight: {estimated_weight}kg"

    # Multi-package determination for appointment.service_type
    if loads_list:
        pkg_names = []
        for ld in loads_list:
            p = ld.get('service_type') or service_type
            if p and p not in pkg_names:
                pkg_names.append(p)
        if len(pkg_names) == 1:
            service_type = pkg_names[0]
        elif len(pkg_names) > 1:
            short_names = []
            for p in pkg_names:
                p_lower = p.lower()
                if 'saver' in p_lower: short_names.append('Saver')
                elif 'signature' in p_lower: short_names.append('Signature')
                elif 'premium' in p_lower: short_names.append('Premium')
                elif 'self' in p_lower: short_names.append('Self-Service')
                elif 'classic' in p_lower: short_names.append('Classic')
                else: short_names.append(p[:12])
            service_type = f"Multi-Package ({' + '.join(short_names)})"

    if building or unit:
        condo_parts = []
        if building:
            condo_parts.append(f"Deca Homes Bldg {building}")
        if unit:
            condo_parts.append(f"Unit {unit}")
        condo_str = ", ".join(condo_parts)
        if address and address != condo_str:
            address = f"{condo_str} ({address})"
        else:
            address = condo_str

    if not name:
        name = "Condo Resident" if logged_user_id else ""
    if not phone and logged_user_id:
        phone = "In-App Customer"

    if not name or (not phone and not logged_user_id):
        return jsonify({"status": "error", "message": "Full name and contact number are required."}), 400

    liability_agreed = payload.get('liability_agreed')
    if liability_agreed is not None and str(liability_agreed).lower() in ('false', '0', 'no'):
        return jsonify({"status": "error", "message": "Customer Equipment Liability Policy agreement is required to book."}), 400

    # Parse scheduled date/time if provided, otherwise default to today
    parsed_schedule = datetime.now()
    if raw_schedule:
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                parsed_schedule = datetime.strptime(raw_schedule, fmt)
                break
            except ValueError:
                pass
    elif raw_date:
        parsed_schedule = None
        if pickup_time:
            if 'immediate' in pickup_time.lower() or 'now' in pickup_time.lower():
                parsed_schedule = datetime.now()
            else:
                time_clean = pickup_time.split(' - ')[0].strip()
                for t_fmt in ("%I:%M %p", "%I:%M%p", "%H:%M", "%H:%M:%S", "%I %p", "%I%p"):
                    try:
                        dt = datetime.strptime(f"{raw_date} {time_clean}", f"%Y-%m-%d {t_fmt}")
                        parsed_schedule = dt
                        pickup_time = dt.strftime("%I:%M %p")
                        break
                    except ValueError:
                        pass
        if not parsed_schedule:
            try:
                dt_raw = datetime.strptime(raw_date, "%Y-%m-%d")
                parsed_schedule = datetime.now() if dt_raw.date() == datetime.now().date() else dt_raw
            except ValueError:
                parsed_schedule = datetime.now()

    # Past Date / Time Booking Prevention Guard
    if parsed_schedule.date() < datetime.now().date():
        return jsonify({"status": "error", "message": "Cannot book for a past date. Please select an upcoming date."}), 400

    is_immediate = pickup_time and ('immediate' in pickup_time.lower() or 'now' in pickup_time.lower())
    if parsed_schedule.date() == datetime.now().date() and pickup_time and not is_immediate:
        if parsed_schedule < (datetime.now() - timedelta(minutes=10)):
            return jsonify({"status": "error", "message": "Selected time has already passed for today. Please select an upcoming time."}), 400

    db = SessionLocal()
    try:
        order_code = _generate_unique_order_code(db)
        
        # Calculate initial price
        computed_price = compute_service_price(
            service_type, order_mode, turnaround_option,
            loads=loads_list, total_machines=total_machines,
            addons=addons_list
        )
        if not loads_list and estimated_weight and estimated_weight > 8.0 and estimated_weight <= 13.0 and 'titan' not in service_type.lower():
            computed_price += Decimal('95.00')

        new_appointment = Appointment(
            customer_id=logged_user_id if logged_user_id else None,
            order_code=order_code,
            customer_name=name,
            customer_email=email or None,
            phone_number=phone or None,
            address=address or None,
            pickup_time=pickup_time or (parsed_schedule.strftime("%I:%M %p") if raw_schedule else None),
            schedule_time=parsed_schedule,
            service_type=service_type,
            load_details=load_details,
            estimated_weight=estimated_weight,
            addons=addons_str,
            total_amount=computed_price,
            total_machines=total_machines,
            turnaround_option=turnaround_option,
            priority_level=priority_level,
            order_mode=order_mode,
            payment_method=payment_method,
            payment_status=payment_status,
            fulfillment_status=fulfillment_status,
            status='Pending'
        )
        db.add(new_appointment)
        db.flush()

        # Allocate into active queue sequence
        next_num = QueueManager.generate_next_queue_number(db)
        computed_ewt = QueueManager.calculate_current_ewt(db)

        queue_entry = Queue(
            queue_number=next_num,
            appointment_id=new_appointment.appointment_id,
            customer_name=name,
            load_details=load_details,
            total_machines=total_machines,
            turnaround_option=turnaround_option,
            priority_level=priority_level,
            order_mode=order_mode,
            payment_method=payment_method,
            payment_status=payment_status,
            fulfillment_status=fulfillment_status,
            status='Waiting',
            verified_at=None,
            created_at=datetime.now(),
            estimated_waiting_time=computed_ewt
        )
        db.add(queue_entry)
        db.commit()

        # Optional email notification if customer provided email
        if email:
            schedule_str = f"{raw_date or parsed_schedule.strftime('%Y-%m-%d')} at {pickup_time or 'Scheduled slot'}"
            EmailService.send_order_confirmation(
                email, order_code, name, service_type, schedule_str
            )

        return jsonify({
            "status": "success",
            "message": "Order saved successfully!",
            "appointment_id": new_appointment.appointment_id,
            "order_id": order_code,
            "order_code": order_code,
            "queue_number": next_num,
            "priority_level": priority_level,
            "turnaround_option": turnaround_option,
            "total_machines": total_machines,
            "load_details": load_details,
            "estimated_weight": float(estimated_weight) if estimated_weight else 8.0,
            "total_amount": float(computed_price),
            "payment_method": payment_method,
            "payment_status": payment_status,
            "is_online_payment": is_online_payment,
            "fulfillment_status": fulfillment_status,
            "estimated_wait_mins": computed_ewt,
            "data": {
                "appointment_id": new_appointment.appointment_id,
                "order_id": order_code,
                "name": name,
                "service_type": service_type,
                "total_machines": total_machines,
                "load_details": load_details,
                "estimated_weight": float(estimated_weight) if estimated_weight else 8.0,
                "total_amount": float(computed_price),
                "turnaround_option": turnaround_option,
                "priority_level": priority_level,
                "payment_method": payment_method,
                "payment_status": payment_status,
                "is_online_payment": is_online_payment,
                "fulfillment_status": fulfillment_status,
                "queue_number": next_num
            }
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()


@appointments_bp.route('/api/order/track')
def track_order():
    """Public customer order status search by Order ID or Phone."""
    search_query = (request.args.get('order_id') or request.args.get('order_code') or request.args.get('q') or '').strip()
    if not search_query:
        return jsonify({"status": "error", "message": "Enter your Order ID or phone number."}), 400

    db = SessionLocal()
    try:
        refresh_machine_cycles(db)
        clean_digits = re.sub(r'\D', '', search_query)
        filters = [
            Appointment.order_code == search_query.upper(),
            Appointment.order_code == search_query,
            Appointment.phone_number == search_query,
            Appointment.customer_email == search_query.lower()
        ]
        if clean_digits:
            filters.append(Appointment.order_code.ilike(f"ORD-{clean_digits}"))
            if clean_digits.isdigit():
                filters.append(Appointment.appointment_id == int(clean_digits))

        appointment = db.query(Appointment).filter(or_(*filters)).order_by(Appointment.appointment_id.desc()).first()

        if not appointment:
            return jsonify({"status": "error", "message": f"No order found matching '{search_query}'."}), 404

        # Grab associated queue and machine details if any
        queue_row = (db.query(Queue, MachineStatus)
                     .outerjoin(MachineStatus, Queue.machine_id == MachineStatus.machine_id)
                     .filter(Queue.appointment_id == appointment.appointment_id)
                     .first())
        
        queue, machine = (queue_row[0], queue_row[1]) if queue_row else (None, None)

        # Derive customer-friendly readable status and progress step
        display_status = appointment.status or 'Order Placed'
        progress_step = 1  # 1: Placed, 2: In Queue, 3: Washing/Drying, 4: Ready/Completed

        if appointment.status == 'Cancelled':
            display_status = 'Cancelled'
            progress_step = 0
        elif appointment.status == 'Completed':
            display_status = 'Ready for Pick-up / Done'
            progress_step = 4
        elif queue:
            if queue.status == 'Done':
                display_status = 'Ready for Pick-up'
                progress_step = 4
            elif queue.status == 'Processing' or (machine and machine.status == 'In-Use' and machine.assigned_customer_name == appointment.customer_name):
                if machine and machine.cycle_type == 'drying':
                    display_status = 'Drying'
                else:
                    display_status = 'Washing'
                progress_step = 3
            elif queue.status == 'Waiting':
                display_status = 'In Queue (Scheduled)'
                progress_step = 2
            else:
                progress_step = 2
        elif appointment.status == 'Confirmed':
            display_status = 'In Queue (Scheduled)'
            progress_step = 2

        # SLA Target Date calculation
        mode = appointment.order_mode or (queue.order_mode if queue else None) or 'Drop-Off'
        is_self_service = 'self' in mode.lower() or 'self' in (appointment.service_type or '').lower()

        if is_self_service:
            turnaround = None
            priority = 'Immediate'
            target_sla_label = None
            target_sla_date = None
        else:
            turnaround = appointment.turnaround_option or (queue.turnaround_option if queue else None) or '24 Hours'
            priority = appointment.priority_level or (queue.priority_level if queue else None) or 'Standard'

            if '2 day' in turnaround.lower() or '48' in turnaround.lower() or 'graveyard' in priority.lower():
                target_sla_label = "2 Days Economy (Batched Off-Peak / Graveyard Shift)"
                target_sla_date = (appointment.schedule_time + timedelta(days=2)).strftime("%b %d, %Y") if appointment.schedule_time else "Within 2 Days"
            else:
                target_sla_label = "24 Hours Express (Standard Turnaround)"
                target_sla_date = (appointment.schedule_time + timedelta(days=1)).strftime("%b %d, %Y") if appointment.schedule_time else "Within 24 Hours"

        pay_method = appointment.payment_method or (queue.payment_method if queue else None) or 'Cash'
        pay_status = appointment.payment_status or (queue.payment_status if queue else None) or 'Pending'
        fulfill_status = appointment.fulfillment_status or (queue.fulfillment_status if queue else None) or ('Waiting Drop-off' if mode == 'Drop-Off' else 'For Pickup')

        # Check if the order is eligible for self-service cancellation
        is_cancellable = (
            appointment.status not in ['Completed', 'Cancelled'] and
            (not queue or queue.status == 'Waiting') and
            (not machine or machine.status != 'In-Use' or machine.assigned_customer_name != appointment.customer_name) and
            fulfill_status not in ['Washing', 'Drying', 'Folding', 'Ready for Pick-up', 'Completed', 'Done']
        )

        return jsonify({
            "status": "success",
            "data": {
                "appointment_id": appointment.appointment_id,
                "order_id": appointment.order_code or f"ORD-{appointment.appointment_id:04d}",
                "customer_name": appointment.customer_name or "Valued Customer",
                "phone_number": appointment.phone_number or "—",
                "email": appointment.customer_email or "—",
                "address": appointment.address or "—",
                "service_type": appointment.service_type,
                "turnaround_option": turnaround,
                "priority_level": priority,
                "order_mode": mode,
                "payment_method": pay_method,
                "payment_status": pay_status,
                "fulfillment_status": fulfill_status,
                "target_ready_sla": target_sla_label,
                "target_ready_date": target_sla_date,
                "schedule_date": appointment.schedule_time.strftime("%Y-%m-%d") if appointment.schedule_time else "—",
                "pickup_time": appointment.pickup_time or appointment.schedule_time.strftime("%I:%M %p") if appointment.schedule_time else "—",
                "order_status": display_status,
                "progress_step": progress_step,
                "queue_number": queue.queue_number if queue else None,
                "queue_status": queue.status if queue else "Pending",
                "assigned_machine": (machine.machine_name or f"Machine {machine.machine_id} (Dryer and Washer)") if machine else "Queue Allocation",
                "estimated_wait_time": queue.estimated_waiting_time if queue else 0,
                "is_cancellable": is_cancellable,
                "cancellation_reason": appointment.cancellation_reason,
                "cancelled_at": appointment.cancelled_at.strftime("%Y-%m-%d %I:%M %p") if appointment.cancelled_at else None,
                "refund_status": appointment.refund_status
            }
        })
    finally:
        db.close()


@appointments_bp.route('/api/order/cancel/request-otp', methods=['POST'])
def request_cancellation_otp():
    """
    Generates and dispatches a 6-digit cancellation OTP to the registered
    phone number (and email) of the order.
    """
    payload = request.get_json(silent=True) or request.form
    order_query = (payload.get('order_id') or payload.get('order_code') or '').strip()
    appt_id = payload.get('appointment_id')
    phone_input = (payload.get('phone_number') or payload.get('phone') or '').strip()

    if not order_query and not appt_id:
        return jsonify({"status": "error", "message": "Order ID or Appointment ID is required."}), 400

    db = SessionLocal()
    try:
        query = db.query(Appointment)
        if appt_id:
            try:
                appointment = query.filter(Appointment.appointment_id == int(appt_id)).first()
            except (ValueError, TypeError):
                appointment = None
        else:
            clean_digits = re.sub(r'\D', '', order_query)
            filters = [
                Appointment.order_code == order_query.upper(),
                Appointment.order_code == order_query
            ]
            if clean_digits:
                filters.append(Appointment.order_code.ilike(f"ORD-{clean_digits}"))
            appointment = query.filter(or_(*filters)).first()

        if not appointment:
            return jsonify({"status": "error", "message": f"No order found matching '{order_query or appt_id}'."}), 404

        # 1. Operational State Guards
        if appointment.status == 'Cancelled':
            return jsonify({"status": "error", "message": "This order has already been cancelled."}), 400

        if appointment.status == 'Completed':
            return jsonify({"status": "error", "message": "Completed orders cannot be cancelled."}), 400

        queue = db.query(Queue).filter(Queue.appointment_id == appointment.appointment_id).first()
        if queue and queue.status == 'Processing':
            return jsonify({
                "status": "error", 
                "message": "Laundry is currently processing in a machine and cannot be cancelled. Please speak with staff."
            }), 400

        if appointment.fulfillment_status in ['Washing', 'Drying', 'Folding', 'Ready for Pick-up', 'Completed', 'Done']:
            return jsonify({
                "status": "error", 
                "message": f"Order is already in '{appointment.fulfillment_status}' stage and cannot be cancelled."
            }), 400

        # 2. Verify identity / phone match
        user_id = session.get('user_id')
        user_role = session.get('user_role')
        is_owner = (user_id and appointment.customer_id and user_id == appointment.customer_id)
        is_staff = (user_role in ['Staff', 'Manager'])

        if not (is_owner or is_staff):
            if not phone_input:
                return jsonify({
                    "status": "error", 
                    "message": "Please enter your registered phone number to receive the cancellation OTP."
                }), 401

            clean_digits = lambda val: ''.join(filter(str.isdigit, str(val or '')))[-10:]
            rec_phone = clean_digits(appointment.phone_number)
            in_phone = clean_digits(phone_input)

            if not rec_phone or not in_phone or rec_phone != in_phone:
                return jsonify({
                    "status": "error", 
                    "message": "Phone verification failed. The number provided does not match the order record."
                }), 403

        # 3. Generate 6-digit OTP (valid for 5 minutes)
        otp = f"{secrets.randbelow(900000) + 100000}"
        appointment.cancellation_otp = otp
        appointment.cancellation_otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
        db.commit()

        # 4. Dispatch SMS & Optional Email
        order_code = appointment.order_code or f"ORD-{appointment.appointment_id:04d}"
        SMSService.send_cancellation_otp(appointment.phone_number, order_code, otp)
        
        has_email = False
        masked_email = None
        if appointment.customer_email and appointment.customer_email.strip():
            cust_em = appointment.customer_email.strip()
            EmailService.send_cancellation_otp(cust_em, order_code, appointment.customer_name, otp)
            has_email = True
            if '@' in cust_em:
                user_part, domain_part = cust_em.split('@', 1)
                if len(user_part) > 2:
                    masked_user = user_part[0] + ('*' * min(4, len(user_part) - 2)) + user_part[-1]
                else:
                    masked_user = user_part[0] + '*'
                masked_email = f"{masked_user}@{domain_part}"
            else:
                masked_email = cust_em

        masked_p = SMSService.mask_phone(appointment.phone_number)
        
        if has_email and masked_email:
            msg = f"A 6-digit cancellation OTP has been sent to your email ({masked_email}) and mobile ({masked_p})."
        else:
            msg = f"A 6-digit cancellation OTP has been dispatched to your mobile ({masked_p})."

        return jsonify({
            "status": "success",
            "message": msg,
            "masked_phone": masked_p,
            "has_email": has_email,
            "masked_email": masked_email,
            "order_id": order_code,
            "demo_otp": otp  # Facilitates testing and oral defense demonstration
        })
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": f"Failed to send OTP: {str(e)}"}), 500
    finally:
        db.close()


@appointments_bp.route('/api/order/cancel', methods=['POST'])
def cancel_order():
    """
    Customer self-service order cancellation.
    Verifies the 6-digit OTP code before releasing the queue and cancelling.
    """
    payload = request.get_json(silent=True) or request.form
    order_query = (payload.get('order_id') or payload.get('order_code') or '').strip()
    appt_id = payload.get('appointment_id')
    phone_input = (payload.get('phone_number') or payload.get('phone') or '').strip()
    otp_input = (payload.get('otp') or payload.get('verification_code') or '').strip()
    reason = (payload.get('reason') or payload.get('cancellation_reason') or 'Customer cancelled via tracker').strip()

    if not order_query and not appt_id:
        return jsonify({"status": "error", "message": "Order ID or Appointment ID is required."}), 400

    db = SessionLocal()
    try:
        query = db.query(Appointment)
        if appt_id:
            try:
                appointment = query.filter(Appointment.appointment_id == int(appt_id)).first()
            except (ValueError, TypeError):
                appointment = None
        else:
            appointment = query.filter(
                or_(
                    Appointment.order_code == order_query.upper(),
                    Appointment.order_code == order_query
                )
            ).first()

        if not appointment:
            return jsonify({"status": "error", "message": f"No order found matching '{order_query or appt_id}'."}), 404

        # 1. Operational State Guards
        if appointment.status == 'Cancelled':
            return jsonify({"status": "error", "message": "This order has already been cancelled."}), 400

        if appointment.status == 'Completed':
            return jsonify({"status": "error", "message": "Completed orders cannot be cancelled."}), 400

        queue = db.query(Queue).filter(Queue.appointment_id == appointment.appointment_id).first()
        if queue and queue.status == 'Processing':
            return jsonify({
                "status": "error", 
                "message": "Laundry is currently processing in a machine and cannot be cancelled. Please contact staff directly."
            }), 400

        if appointment.fulfillment_status in ['Washing', 'Drying', 'Folding', 'Ready for Pick-up', 'Completed', 'Done']:
            return jsonify({
                "status": "error", 
                "message": f"Order is already in '{appointment.fulfillment_status}' stage and cannot be cancelled."
            }), 400

        # 2. Security Verification (Ownership / OTP Check)
        user_id = session.get('user_id')
        user_role = session.get('user_role')
        is_owner = (user_id and appointment.customer_id and user_id == appointment.customer_id)
        is_staff = (user_role in ['Staff', 'Manager'])

        # If user is not an authenticated owner/staff, or if OTP was submitted, enforce OTP validation
        if not (is_owner or is_staff) or otp_input:
            if not otp_input:
                return jsonify({
                    "status": "error", 
                    "message": "Please enter the 6-digit OTP sent to your registered phone number."
                }), 401

            if not appointment.cancellation_otp:
                return jsonify({
                    "status": "error", 
                    "message": "No active cancellation code found. Please request a new OTP."
                }), 400

            if appointment.cancellation_otp_expires_at and appointment.cancellation_otp_expires_at < datetime.utcnow():
                return jsonify({
                    "status": "error", 
                    "message": "The verification OTP has expired. Please request a new code."
                }), 400

            if appointment.cancellation_otp.strip() != otp_input:
                return jsonify({
                    "status": "error", 
                    "message": "Incorrect verification code. If you did not request this, please ignore this notice."
                }), 403

        # 3. Apply Cancellation
        appointment.status = 'Cancelled'
        appointment.cancellation_reason = reason
        appointment.cancelled_at = datetime.utcnow()
        # Invalidate OTP once used
        appointment.cancellation_otp = None
        appointment.cancellation_otp_expires_at = None

        refund_note = None
        if appointment.payment_status == 'Paid':
            appointment.refund_status = 'Pending Refund'
            refund_note = "Your online payment has been flagged for refund processing by store management."

        # Remove from active queue if still waiting
        if queue and queue.status == 'Waiting':
            db.delete(queue)

        db.commit()

        order_label = appointment.order_code or f"ORD-{appointment.appointment_id:04d}"
        return jsonify({
            "status": "success",
            "message": f"Order {order_label} has been cancelled successfully.",
            "refund_notice": refund_note,
            "order_id": order_label
        })
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": f"Cancellation failed: {str(e)}"}), 500
    finally:
        db.close()


@appointments_bp.route('/customer/book', methods=['POST'])
def book_appointment():
    """Legacy redirect handler to create_order for backward compatibility."""
    return create_order()

