# routes/bot.py
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from config.database import SessionLocal
from models.schemas import Appointment, Queue, MachineStatus
from services.machines import refresh_machine_cycles
from services.queuing import QueueManager

def calculate_laundry_estimate(service_type, turnaround='24 Hours', is_delivery=False):
    pkg_lower = (service_type or '').lower()
    if 'premium' in pkg_lower:
        base = 260.0
    elif 'signature' in pkg_lower:
        base = 200.0
    elif 'classic' in pkg_lower:
        base = 130.0
    elif 'self' in pkg_lower and '13' in pkg_lower:
        base = 240.0
    elif 'self' in pkg_lower:
        base = 145.0
    else:
        base = 160.0  # Saver default

    t_lower = (turnaround or '').lower()
    if '2 day' in t_lower or '48' in t_lower or 'graveyard' in t_lower:
        svc_charge = 70.0
    else:
        svc_charge = 120.0

    delivery = 40.0 if is_delivery else 0.0
    total = base + svc_charge + delivery
    return {
        'amount_php': total,
        'base': base,
        'svc_charge': svc_charge,
        'delivery': delivery,
        'formatted': f"₱{total:.2f}"
    }

bot_bp = Blueprint('bot', __name__)


def _generate_order_code(db):
    for _ in range(10):
        code = f"ORD-{secrets.randbelow(90000) + 10000}"
        if not db.query(Appointment).filter(Appointment.order_code == code).first():
            return code
    return f"ORD-{secrets.randbelow(900000) + 100000}"


@bot_bp.route('/api/bot/health', methods=['GET'])
def bot_health():
    return jsonify({
        "status": "online",
        "service": "Bon Laundry Bot Dispatcher",
        "timestamp": datetime.now().isoformat()
    })


from services.bot_ai import process_bot_message

@bot_bp.route('/api/bot/chat', methods=['POST'])
def bot_chat():
    """
    Intelligent Conversational Dispatcher.
    Takes user text or callback data, processes with FAQ knowledge base,
    normalized order tracking, multi-step booking, lobby availability,
    and returns Telegram message with structured inline keyboard buttons.
    """
    payload = request.get_json(silent=True) or request.form or {}
    if isinstance(payload, dict) and 'base_url' not in payload:
        payload['base_url'] = request.host_url.rstrip('/')
    try:
        response_data = process_bot_message(payload)
        return jsonify({
            "status": "success",
            "telegram_message": response_data.get("telegram_message", ""),
            "reply_markup": {
                "inline_keyboard": response_data.get("inline_keyboard", [])
            },
            "data": response_data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "telegram_message": f"⚠️ Paumanhin, nagkaroon ng error: {str(e)}",
            "reply_markup": {
                "inline_keyboard": [[{"text": "🔙 Main Menu", "callback_data": "show_menu"}]]
            }
        }), 500


@bot_bp.route('/api/bot/webhook', methods=['POST'])
def bot_webhook():
    """
    Unified webhook dispatcher for n8n and Telegram automations.
    Supported Actions:
      - 'book_appointment' / 'create_order'
      - 'track_order' / 'check_status'
      - 'rates_inquiry'
    """
    payload = request.get_json(silent=True) or request.form or {}
    action = (payload.get('action') or ('track_order' if 'order_code' in payload else 'book_appointment')).lower().strip()

    db = SessionLocal()
    try:
        # 1. TRACK ORDER ACTION
        if action in ['track_order', 'check_status', 'track']:
            query = (payload.get('order_code') or payload.get('query') or payload.get('order_id') or '').strip().upper()
            if not query:
                return jsonify({
                    "status": "error",
                    "action": "track_order",
                    "message": "Pakilagay po ang inyong Order Code (Halimbawa: ORD-84920).",
                    "telegram_message": "⚠️ *Pakilagay po ang Order Code*\n\nHalimbawa: `ORD-84920` o `84920` upang mahanap ang inyong labada."
                }), 400

            order_query = query if query.startswith('ORD-') else f"ORD-{query}"
            
            refresh_machine_cycles(db)
            appointment = db.query(Appointment).filter(
                (Appointment.order_code == query) | 
                (Appointment.order_code == order_query) |
                (Appointment.phone_number == query)
            ).order_by(Appointment.appointment_id.desc()).first()

            if not appointment and query.isdigit():
                appointment = db.query(Appointment).filter(Appointment.appointment_id == int(query)).first()

            if not appointment:
                return jsonify({
                    "status": "not_found",
                    "action": "track_order",
                    "found": False,
                    "order_code": query,
                    "message": f"No record found for '{query}'.",
                    "telegram_message": f"🔍 *Order Not Found*\n\nUnable to find Order Code: `{query}`.\nPlease verify your order code or consult our counter staff."
                }), 200

            queue = db.query(Queue).filter(Queue.appointment_id == appointment.appointment_id).first()
            machine = None
            if queue and queue.machine_id:
                machine = db.query(MachineStatus).filter(MachineStatus.machine_id == queue.machine_id).first()

            display_status = appointment.status
            if appointment.status == 'Completed':
                display_status = 'Ready for Pick-up / Done ✅'
            elif queue:
                if queue.status == 'Done':
                    display_status = 'Ready for Pick-up ✅'
                elif queue.status == 'Processing':
                    display_status = 'Drying 🌀' if (machine and machine.cycle_type == 'drying') else 'Washing 🧼'
                elif queue.status == 'Waiting':
                    display_status = 'In Queue ⏳'
            elif appointment.status == 'Confirmed':
                display_status = 'Confirmed (Waiting Drop-off/Pickup) ⏳'

            turnaround = appointment.turnaround_option or '24 Hours'
            target_date = (appointment.schedule_time + timedelta(days=2)).strftime("%b %d, %Y") if ('2 day' in turnaround.lower() or '48' in turnaround.lower()) else ((appointment.schedule_time + timedelta(days=1)).strftime("%b %d, %Y") if appointment.schedule_time else "Within 24 Hours")
            order_id = appointment.order_code or f"ORD-{appointment.appointment_id:04d}"
            pay_status = appointment.payment_status or 'Pending'
            pay_badge = "✅ Paid" if pay_status.lower() == 'paid' else "⏳ Pending / Pay at Counter"

            telegram_msg = (
                f"🧺 *LAUNDRY STATUS — BON LAUNDRY*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📋 *Order ID:* `{order_id}`\n"
                f"👤 *Customer:* {appointment.customer_name}\n"
                f"📊 *Status:* *{display_status}*\n"
                f"⚙️ *Machine:* {((machine.machine_name or f'Machine {machine.machine_id} (Dryer and Washer)') if machine else 'Queue Allocation')}\n"
                f"📦 *Package:* {appointment.service_type}\n"
                f"💳 *Payment:* {pay_badge} ({appointment.payment_method or 'Cash'})\n"
                f"⏱️ *Turnaround:* {turnaround}\n"
                f"📅 *Estimated Ready:* {target_date}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"_Thank you for choosing Bon Laundry Station!_"
            )

            return jsonify({
                "status": "success",
                "action": "track_order",
                "found": True,
                "telegram_message": telegram_msg,
                "data": {
                    "order_id": order_id,
                    "customer_name": appointment.customer_name,
                    "status": display_status,
                    "payment_status": pay_status,
                    "payment_method": appointment.payment_method or "Cash",
                    "service_type": appointment.service_type,
                    "turnaround": turnaround,
                    "estimated_ready": target_date
                }
            })

        # 2. BOOK APPOINTMENT ACTION
        elif action in ['book_appointment', 'create_order', 'book']:
            name = (payload.get('customer_name') or payload.get('name') or '').strip()
            phone = (payload.get('phone_number') or payload.get('phone') or '').strip()
            service_type = (payload.get('service_type') or payload.get('package') or 'Saver (Wash, Dry, Fold)').strip()
            turnaround = (payload.get('turnaround_option') or payload.get('turnaround') or '24 Hours').strip()
            order_mode = (payload.get('order_mode') or payload.get('mode') or 'Drop-Off').strip()
            payment_method = (payload.get('payment_method') or payload.get('payment') or 'Cash').strip()
            building = (payload.get('building') or payload.get('deca_building') or '').strip()
            unit = (payload.get('unit') or payload.get('unit_number') or '').strip()
            address = (payload.get('address') or '').strip()

            if not name or not phone:
                return jsonify({
                    "status": "error",
                    "action": "book_appointment",
                    "message": "Customer Name and Contact Number are required.",
                    "telegram_message": "⚠️ *Missing Information*\n\nPlease provide your:\n1. *Full Name*\n2. *Contact Number* (e.g., 09123456789)\n3. *Deca Homes Bldg & Unit* (for pickup orders)"
                }), 400

            # Format Deca Homes Address
            if building or unit:
                condo_parts = []
                if building:
                    condo_parts.append(f"Deca Homes Bldg {building}")
                if unit:
                    condo_parts.append(f"Unit {unit}")
                condo_str = ", ".join(condo_parts)
                address = f"{condo_str} ({address})" if (address and address != condo_str) else condo_str

            if '2 day' in turnaround.lower() or '48' in turnaround.lower():
                priority_level = 'Graveyard Batch'
            elif '24' in turnaround.lower() or 'express' in turnaround.lower():
                priority_level = 'Express 24h'
            else:
                priority_level = 'Standard'

            order_code = _generate_order_code(db)
            now = datetime.now()

            new_appt = Appointment(
                order_code=order_code,
                customer_name=name,
                customer_email=payload.get('customer_email') or payload.get('email') or None,
                phone_number=phone,
                address=address or 'Store Counter Walk-in / Drop-off',
                service_type=service_type,
                turnaround_option=turnaround,
                priority_level=priority_level,
                order_mode=order_mode,
                payment_method=payment_method,
                payment_status='Pending',
                fulfillment_status='For Pickup' if 'pick' in order_mode.lower() else 'Waiting Drop-off',
                status='Confirmed',
                schedule_time=now,
                pickup_time=payload.get('pickup_time') or now.strftime("%I:%M %p")
            )
            db.add(new_appt)
            db.flush()

            new_queue = Queue(
                appointment_id=new_appt.appointment_id,
                customer_name=name,
                status='Waiting',
                queue_number=QueueManager.generate_next_queue_number(db),
                turnaround_option=turnaround,
                priority_level=priority_level,
                order_mode=order_mode,
                payment_method=payment_method,
                payment_status='Pending',
                fulfillment_status='For Pickup' if 'pick' in order_mode.lower() else 'Waiting Drop-off'
            )
            db.add(new_queue)
            db.commit()

            pricing = calculate_laundry_estimate(service_type, turnaround=turnaround, is_delivery='pick' in order_mode.lower())

            telegram_msg = (
                f"🎉 *APPOINTMENT CONFIRMED! — BON LAUNDRY*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📋 *Order Code:* `{order_code}`\n"
                f"👤 *Customer:* {name}\n"
                f"📞 *Contact:* {phone}\n"
                f"🧺 *Package:* {service_type}\n"
                f"⏱️ *Turnaround:* {turnaround}\n"
                f"🚚 *Mode:* {order_mode}\n"
                f"📍 *Address:* {address or 'Store Drop-off'}\n"
                f"💵 *Est. Total:* {pricing.get('formatted', '₱160.00')} ({payment_method})\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 *Reminder:* Please save your Order Code `{order_code}` to track your laundry status anytime!"
            )

            return jsonify({
                "status": "success",
                "action": "book_appointment",
                "order_code": order_code,
                "appointment_id": new_appt.appointment_id,
                "telegram_message": telegram_msg,
                "data": {
                    "order_code": order_code,
                    "customer_name": name,
                    "phone": phone,
                    "package": service_type,
                    "turnaround": turnaround,
                    "estimated_total": pricing.get('amount_php', 160.0),
                    "formatted_total": pricing.get('formatted', '₱160.00')
                }
            })

        # 3. RATES INQUIRY ACTION
        elif action in ['rates_inquiry', 'rates', 'services']:
            telegram_msg = (
                f"📋 *OFFICIAL RATE CARD — BON LAUNDRY STATION*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🧺 *DROP-OFF SERVICE PACKAGES (8kg Load):*\n"
                f"• *Classic:* ₱130 _(Wash, Dry, Fold)_\n"
                f"• *Saver:* ₱160 _(Wash, Dry, Fold + 1 Det + 1 Fab)_\n"
                f"• *Signature:* ₱200 _(Wash, Dry, Fold + 2 Det + 2 Fab)_\n"
                f"• *Premium:* ₱260 _(Sort, Superwash, Dry, Fold + Complete Care)_\n\n"
                f"⏱️ *SERVICE CHARGES / TURNAROUND:*\n"
                f"• *24 Hours Express:* ₱120\n"
                f"• *2 Days Economy:* ₱70\n\n"
                f"🧼 *SELF-SERVICE RATES:*\n"
                f"• *8kg Regular Load:* ₱145\n"
                f"• *13kg Titan Load:* ₱240\n\n"
                f"🛵 *Delivery:* ₱40 (Deca Homes Buildings)\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"_Choose from the options below to book or track your laundry!_"
            )
            return jsonify({
                "status": "success",
                "action": "rates_inquiry",
                "telegram_message": telegram_msg
            })

        # 4. LIVE MACHINE LOBBY STATUS
        elif action in ['lobby_status', 'machines', 'lobby']:
            refresh_machine_cycles(db)
            machines = db.query(MachineStatus).all()
            total = len(machines)
            avail = len([m for m in machines if m.status.lower() == 'available'])
            running = len([m for m in machines if m.status.lower() == 'in-use'])
            maint = len([m for m in machines if m.status.lower() == 'maintenance'])

            traffic = "🟢 Light Traffic (Available Machines)" if avail >= 10 else ("🟡 Moderate Rush" if avail >= 4 else "🔴 Heavy Traffic")
            wait_time = "No wait time — Ready for wash" if avail >= 8 else ("~15-30 mins" if avail >= 3 else "~45-60 mins")

            telegram_msg = (
                f"🏬 *LIVE MACHINE LOBBY — BON LAUNDRY*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Traffic Status:* {traffic}\n"
                f"⏱️ *Estimated Wait Time:* {wait_time}\n\n"
                f"⚡ *Machine Breakdown ({total} Units):*\n"
                f"• 🟢 *Available / Ready:* {avail} machines\n"
                f"• 🌀 *In Cycle / Running:* {running} machines\n"
                f"• 🛠️ *Maintenance:* {maint} machines\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 _Tip: Drop by or book now while machines are ready!_"
            )
            return jsonify({
                "status": "success",
                "action": "lobby_status",
                "telegram_message": telegram_msg,
                "data": {
                    "total_machines": total,
                    "available": avail,
                    "running": running,
                    "maintenance": maint
                }
            })

        # 5. STORE INFO & CONTACT
        elif action in ['store_info', 'contact', 'delivery_info', 'info']:
            telegram_msg = (
                f"📍 *STORE LOCATION & CONTACT — BON LAUNDRY*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🏬 *Branch:* Urban Deca Homes, Ortigas\n"
                f"🕒 *Operating Hours:* 8:00 AM – 10:00 PM (Daily)\n"
                f"📞 *Contact Number:* 0917-XXX-XXXX / 0998-XXX-XXXX\n"
                f"🛵 *Pickup & Delivery Area:* Deca Homes Buildings 1-20 (₱40 Delivery fee)\n"
                f"💳 *Payment Options:* Cash upon drop-off/COD, GCash, Maya, Debit/Credit Card (via PayMongo)\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"_Have questions? Message us anytime!_"
            )
            return jsonify({
                "status": "success",
                "action": "store_info",
                "telegram_message": telegram_msg
            })

        else:
            return jsonify({
                "status": "error",
                "message": f"Unknown action '{action}'. Valid actions: 'book_appointment', 'track_order', 'rates_inquiry', 'lobby_status', 'store_info'."
            }), 400

    except Exception as e:
        db.rollback()
        return jsonify({
            "status": "error",
            "message": str(e),
            "telegram_message": f"⚠️ Server error encountered: {str(e)}"
        }), 500
    finally:
        db.close()

