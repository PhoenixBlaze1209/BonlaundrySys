# services/bot_ai.py
import re
from datetime import datetime, timedelta
from config.database import SessionLocal
from models.schemas import Appointment, Queue, MachineStatus
from services.machines import refresh_machine_cycles
from services.queuing import QueueManager

# Comprehensive Store FAQ Knowledge Base
FAQS = [
    {
        "keywords": ["presyo", "rates", "magkano", "price", "magkanu", "bayad", "package", "packages"],
        "title": "📋 Mga Presyo at Package Rates",
        "answer": (
            "🧺 *OFFICIAL RATE CARD — BON LAUNDRY STATION*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📦 *Drop-off Service (Wash, Dry, Fold / 8kg load):*\n"
            "• *Classic:* ₱130 (Standard Wash, Dry, Fold)\n"
            "• *Saver:* ₱160 (Wash, Dry, Fold + 1 Detergent + 1 Fabcon)\n"
            "• *Signature:* ₱200 (Wash, Dry, Fold + 2 Det + 2 Fabcon)\n"
            "• *Premium:* ₱260 (Sort, Superwash, Dry, Fold + Complete Care)\n\n"
            "⏱️ *Turnaround Service Charges:*\n"
            "• *24 Hours Express:* ₱120\n"
            "• *2 Days Economy:* ₱70\n\n"
            "🧼 *Self-Service:* ₱145 (8kg) | ₱240 (13kg Titan)\n"
            "🛵 *Delivery Fee:* ₱40 (Deca Homes Buildings)"
        ),
        "buttons": [
            {"text": "🧺 Magpa-Laundry Na", "callback_data": "action_book"},
            {"text": "🔙 Main Menu", "callback_data": "show_menu"}
        ]
    },
    {
        "keywords": ["delivery", "pickup", "pick up", "hatid", "sundo", "bldg", "deca", "unit", "condo"],
        "title": "🛵 Urban Deca Homes Delivery & Pickup Info",
        "answer": (
            "🛵 *PICKUP & DELIVERY GUIDELINES — URBAN DECA HOMES, ORTIGAS*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📍 *Coverage:* Lahat ng Buildings sa loob ng Urban Deca Homes, Ortigas (Bldg 1 to 20).\n"
            "💵 *Delivery Fee:* ₱40 lamang bawat biyahe.\n"
            "🕒 *Schedule:* 8:00 AM hanggang 9:00 PM araw-araw.\n\n"
            "💡 *Paano magpa-pickup?*\n"
            "1. Piliin ang 'Magpa-Laundry' button sa ibaba.\n"
            "2. Piliin ang '🚗 Pickup & Delivery'.\n"
            "3. Ibigay ang inyong Building at Unit number.\n"
            "4. Pupuntahan po kayo ng aming staff para kunin ang labada."
        ),
        "buttons": [
            {"text": "🚗 Mag-book ng Pickup", "callback_data": "book_pickup"},
            {"text": "🔙 Main Menu", "callback_data": "show_menu"}
        ]
    },
    {
        "keywords": ["oras", "bukas", "open", "hours", "schedule", "sarado", "close", "operating"],
        "title": "🕒 Operating Hours & Location",
        "answer": (
            "🏬 *STORE HOURS & LOCATION*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🕒 *Operating Hours:* 8:00 AM – 10:00 PM (Lunes hanggang Linggo, walang day-off)\n"
            "📍 *Address:* Urban Deca Homes, Ortigas Commercial Area.\n"
            "⚡ *Power & Water:* May dedicated commercial backup water and stable power para continuous ang laba!"
        ),
        "buttons": [
            {"text": "🏬 Machine Lobby Status", "callback_data": "action_lobby"},
            {"text": "🔙 Main Menu", "callback_data": "show_menu"}
        ]
    },
    {
        "keywords": ["payment", "bayad", "gcash", "maya", "card", "cash", "cod", "bank", "bdo", "bpi", "online", "instapay", "qr", "transfer"],
        "title": "💳 Mode of Payment (GCash, Maya, Cash, Bank)",
        "answer": (
            "💳 *MGA PARAAN NG PAGBABAYAD (PAYMENT OPTIONS)*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Tumatanggap po kami ng iba't ibang cashless at cash options para sa inyong kaginhawahan:\n\n"
            "1. 📱 *GCash (Instant Send Money / InstaPay QR)*\n"
            "   • *Account Name:* `GE****S S.`\n"
            "   • *Mobile Number:* `+63 992 659 ****`\n"
            "   • _(Scan InstaPay QR o direct Send Money)_\n\n"
            "2. 💚 *Maya & QR Ph*\n"
            "   • Scan via Maya app o anumang QR Ph-enabled e-wallet\n\n"
            "3. 💵 *Cash on Delivery (COD) / Counter*\n"
            "   • Abot-bayad pagka-deliver ng rider sa inyong unit o pagka-drop-off sa store\n\n"
            "4. 🏦 *Bank Transfer (InstaPay / PESONet)*\n"
            "   • BDO, BPI, UnionBank, SeaBank, at iba pa via InstaPay\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💡 _Paalala: Pakisend po ang screenshot ng payment receipt dito sa chat o ipakita sa aming rider/staff._"
        ),
        "buttons": [
            {"text": "🧺 Magpa-Laundry Na", "callback_data": "action_book"},
            {"text": "🔍 I-track ang Order", "callback_data": "action_track"},
            {"text": "🔙 Main Menu", "callback_data": "show_menu"}
        ]
    },
    {
        "keywords": ["gaano katagal", "tagal", "kailan matatapos", "hours", "turnaround", "sla", "ready"],
        "title": "⏱️ Turnaround Time (Gaano Katagal?)",
        "answer": (
            "⏱️ *ESTIMATED TURNAROUND TIME*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "• ⚡ *24 Hours Express:* Ready for pickup/delivery kinabukasan (24 oras).\n"
            "• 🌙 *2 Days Economy:* Batched sa off-peak/overnight shift, ready within 48 oras sa mas murang service charge!\n"
            "• 🧼 *Self-Service:* Matatapos sa loob lamang ng ~1 hanggang 1.5 oras (44m Wash + 45m Dry)."
        ),
        "buttons": [
            {"text": "🧺 Mag-book Na", "callback_data": "action_book"},
            {"text": "🔙 Main Menu", "callback_data": "show_menu"}
        ]
    },
    {
        "keywords": ["cancel", "kansela", "bawi", "cancellation", "otp"],
        "title": "❌ Order Cancellation Policy",
        "answer": (
            "❌ *ORDER CANCELLATION*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Maaari po ninyong i-cancel ang appointment kung *Pending / Waiting* pa ito at hindi pa naisasalang sa washing machine.\n\n"
            "May 2-Channel Secure OTP verification via SMS / Gmail para protektado ang inyong order."
        ),
        "buttons": [
            {"text": "🔍 I-track ang Order", "callback_data": "action_track"},
            {"text": "📞 Kausapin ang Staff", "callback_data": "action_contact"}
        ]
    }
]


def normalize_order_query(text):
    """
    Extracts order reference codes from any messy user input.
    Examples:
      - 'ORD-84920' -> 'ORD-84920'
      - 'ord84920'   -> 'ORD-84920'
      - '84920'      -> 'ORD-84920'
      - 'track 84920'-> 'ORD-84920'
      - '09123456789'-> '09123456789' (Phone search)
    """
    if not text:
        return None
    raw = text.strip()

    # Match ORD-12345 or ORD12345 (case insensitive)
    match_ord = re.search(r'\bORD-?(\d{4,6})\b', raw, re.IGNORECASE)
    if match_ord:
        return f"ORD-{match_ord.group(1)}"

    # Match pure 5 or 6 digit number
    match_digits = re.search(r'\b(\d{5,6})\b', raw)
    if match_digits:
        return f"ORD-{match_digits.group(1)}"

    # Match 11-digit PH phone number (09XXXXXXXXX)
    match_phone = re.search(r'\b(09\d{9})\b', raw)
    if match_phone:
        return match_phone.group(1)

    return None


def process_bot_message(payload):
    """
    Intelligent master dispatcher that processes any Telegram interaction:
    1. Menu navigation & button callbacks
    2. Multi-step order booking with options
    3. Smart order tracking (handles messy inputs & numbers)
    4. Live machine lobby status
    5. FAQ Knowledge Base matching
    6. Graceful AI fallback with direct staff contact
    """
    user_name = payload.get('user_name') or 'Valued Customer'
    chat_id = payload.get('chat_id')
    base_url = (payload.get('base_url') or '').rstrip('/')

    # Extract text and telegram objects safely
    raw_msg = payload.get('message')
    has_photo = bool(payload.get('has_photo'))
    if isinstance(raw_msg, dict):
        text = str(raw_msg.get('text') or '').strip()
        caption = str(raw_msg.get('caption') or '').strip()
        if caption:
            text = f"{text} {caption}".strip()
        if raw_msg.get('photo') or raw_msg.get('document'):
            has_photo = True
        from_user = raw_msg.get('from') or {}
        user_name = from_user.get('first_name') or user_name
        chat_id = (raw_msg.get('chat') or {}).get('id') or chat_id
    elif isinstance(raw_msg, str):
        text = raw_msg.strip()
    else:
        text = str(payload.get('text') or '').strip()

    raw_cb = payload.get('callback_query')
    if isinstance(raw_cb, dict):
        callback_data = str(raw_cb.get('data') or '').strip()
        from_user = raw_cb.get('from') or {}
        user_name = from_user.get('first_name') or user_name
        chat_id = (raw_cb.get('message') or {}).get('chat', {}).get('id') or chat_id
    else:
        callback_data = str(payload.get('callback_data') or '').strip()

    # Normalize Action
    action = callback_data or ''
    if not action:
        lower_text = text.lower()
        if text in ['/start', 'menu', 'hi', 'hello', 'hey', 'start']:
            action = 'show_menu'
        elif any(k in lower_text for k in ['lobby', 'machine', 'bakante', 'makina']):
            action = 'action_lobby'
        elif any(k in lower_text for k in ['delivery', 'pickup', 'pick up', 'hatid', 'sundo']):
            action = 'action_delivery'
        elif any(k in lower_text for k in ['presyo', 'rates', 'magkano', 'price', 'package']):
            action = 'action_rates'
        elif any(k in lower_text for k in ['staff', 'tao', 'tawag', 'contact', 'number', 'tulong', 'help']):
            action = 'action_contact'
        elif any(k in lower_text for k in ['payment', 'bayad', 'gcash', 'maya', 'bank', 'cash', 'cod', 'instapay', 'qr']):
            action = 'action_payment'
        elif any(k in lower_text for k in ['faq', 'tanong', 'question']):
            action = 'action_faqs'

    # 1. SHOW MAIN MENU
    if action in ['show_menu', '/start']:
        return {
            "telegram_message": (
                f"🧺 *Mabuhay, {user_name}! Welcome to Bon Laundry Station*\n"
                f"📍 _Deca Homes, Ortigas_\n\n"
                f"Paano po namin kayo matutulungan ngayon? Pumili sa mga options sa ibaba:"
            ),
            "inline_keyboard": [
                [
                    {"text": "🧺 Magpa-Laundry (Book)", "callback_data": "action_book"},
                    {"text": "🔍 I-track ang Labada", "callback_data": "action_track"}
                ],
                [
                    {"text": "📋 Presyo & Packages", "callback_data": "action_rates"},
                    {"text": "🏬 Live Machine Lobby", "callback_data": "action_lobby"}
                ],
                [
                    {"text": "🛵 Deca Delivery Info", "callback_data": "action_delivery"},
                    {"text": "❓ FAQs & Tanong", "callback_data": "action_faqs"}
                ],
                [
                    {"text": "📞 Kausapin ang Staff", "callback_data": "action_contact"}
                ]
            ]
        }

    # 2. BOOKING STEP 1: CHOOSE SERVICE MODE
    if action == 'action_book':
        return {
            "telegram_message": (
                f"🧺 *MAGPA-LAUNDRY — STEP 1: PILIIN ANG SERVICE MODE*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Paano ninyo gustong iproseso ang inyong labada?\n\n"
                f"1. 🚗 *Pick-up & Delivery:* Kukunin at ihahatid ng aming staff sa inyong Deca Homes Unit (+₱40).\n"
                f"2. 🏪 *Drop-Off sa Counter:* Dadalhin ninyo ang labada sa aming store.\n"
                f"3. 🧼 *Self-Service:* Kayo mismo ang gagamit ng aming high-capacity washers & dryers."
            ),
            "inline_keyboard": [
                [{"text": "🚗 1. Pick-up & Delivery (Deca)", "callback_data": "mode_pickup"}],
                [{"text": "🏪 2. Drop-Off sa Store", "callback_data": "mode_dropoff"}],
                [{"text": "🧼 3. Self-Service Rates", "callback_data": "action_rates"}],
                [{"text": "🔙 Bumalik sa Main Menu", "callback_data": "show_menu"}]
            ]
        }

    # 2.1 BOOKING STEP 2: CHOOSE PACKAGE FOR PICKUP OR DROPOFF
    if action in ['mode_pickup', 'mode_dropoff', 'book_pickup']:
        mode_label = "Pick-up & Delivery (Deca Homes)" if 'pickup' in action else "Drop-Off sa Counter"
        return {
            "telegram_message": (
                f"🧺 *MAGPA-LAUNDRY — STEP 2: PILIIN ANG PACKAGE*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Mode: *{mode_label}*\n\n"
                f"Pumili po ng package para sa 8kg load:\n\n"
                f"• 🌟 *Saver (₱160):* Wash, Dry, Fold + Detergent + Fabcon _(Most Popular)_\n"
                f"• 🧺 *Classic (₱130):* Wash, Dry, Fold lamang\n"
                f"• 💎 *Signature (₱200):* Extra 2 Detergent + 2 Fabcon + Fold\n"
                f"• 👑 *Premium (₱260):* Sort, Superwash, Dry, Fold + Complete Care"
            ),
            "inline_keyboard": [
                [{"text": "🌟 Saver Package (₱160)", "callback_data": f"pkg_saver_{action}"}],
                [{"text": "🧺 Classic Package (₱130)", "callback_data": f"pkg_classic_{action}"}],
                [{"text": "💎 Signature Package (₱200)", "callback_data": f"pkg_signature_{action}"}],
                [{"text": "👑 Premium Package (₱260)", "callback_data": f"pkg_premium_{action}"}],
                [{"text": "🔙 Pumili ng Ibang Mode", "callback_data": "action_book"}]
            ]
        }

    # 2.2 BOOKING STEP 3: TURNAROUND SELECTION
    if action.startswith('pkg_'):
        parts = action.split('_')
        pkg_name = parts[1].capitalize()
        is_pickup = 'pickup' in action
        mode_code = "pickup" if is_pickup else "dropoff"
        mode_text = "Pick-up & Delivery" if is_pickup else "Drop-Off"

        return {
            "telegram_message": (
                f"⏱️ *MAGPA-LAUNDRY — STEP 3: GAANO KA-RUSH?*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Package: *{pkg_name}* ({mode_text})\n\n"
                f"Piliin ang inyong preferred turnaround speed:\n\n"
                f"• ⚡ *24 Hours Express (+₱120 Svc Charge):* Ready kinabukasan.\n"
                f"• 🌙 *2 Days Economy (+₱70 Svc Charge):* Mas tipid, ready in 48 hours."
            ),
            "inline_keyboard": [
                [{"text": "⚡ 24 Hours Express (+₱120)", "callback_data": f"conf_24h_{pkg_name}_{mode_code}"}],
                [{"text": "🌙 2 Days Economy (+₱70)", "callback_data": f"conf_2day_{pkg_name}_{mode_code}"}],
                [{"text": "🔙 Palitan ang Package", "callback_data": f"mode_{mode_code}"}]
            ]
        }

    # 2.3 BOOKING STEP 4: FINAL CONFIRMATION & DETAILS PROMPT
    if action.startswith('conf_'):
        parts = action.split('_')
        speed_code = parts[1]
        speed = "24 Hours" if speed_code == '24h' else "2 Days"
        pkg = parts[2]
        is_pickup = "pickup" in action or "pick" in action
        mode_label = "Pick-up & Delivery (Deca Homes)" if is_pickup else "Drop-Off sa Store"

        if is_pickup:
            instructions = (
                f"👤 *Customer Name:* {user_name} _(Galing sa Telegram Profile)_\n\n"
                f"I-type lamang ang inyong *Building Number & Unit* (at contact number kung nais):\n\n"
                f"📋 *Direktang Halimbawa (I-type o I-copy):*\n"
                f"👉 `Bldg 12 Unit 304, 09123456789`\n"
                f"👉 `Bldg 12 Unit 304`"
            )
            buttons = [
                [{"text": "🔙 Palitan ang Turnaround", "callback_data": f"pkg_{pkg.lower()}_mode_pickup"}],
                [{"text": "❌ Kanselahin", "callback_data": "show_menu"}]
            ]
        else:
            instructions = (
                f"👤 *Customer Name:* {user_name} _(Galing sa Telegram Profile)_\n\n"
                f"I-type lamang ang inyong *Contact Number* para sa updates o pindutin ang Confirm button sa ibaba:\n\n"
                f"📋 *Halimbawa:*\n"
                f"👉 `09123456789`"
            )
            buttons = [
                [{"text": f"✅ Kumpirmahin para kay {user_name}", "callback_data": f"quickbook_{speed_code}_{pkg}_dropoff"}],
                [{"text": "🔙 Palitan ang Turnaround", "callback_data": f"pkg_{pkg.lower()}_mode_dropoff"}],
                [{"text": "❌ Kanselahin", "callback_data": "show_menu"}]
            ]

        return {
            "telegram_message": (
                f"📝 *MAGPA-LAUNDRY — STEP 4: KUMPIRMASYON*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🧺 *Package:* {pkg} (Wash, Dry, Fold)\n"
                f"🚚 *Mode:* {mode_label}\n"
                f"⏱️ *Turnaround:* {speed}\n"
                f"💳 *Payment Options:* GCash (`GE****S S.`) / Maya / Cash (COD) / Bank\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{instructions}"
            ),
            "inline_keyboard": buttons
        }

    # 3. ORDER TRACKING PROMPT OR EXECUTION
    if action == 'action_track':
        return {
            "telegram_message": (
                f"🔍 *I-TRACK ANG INYONG LABADA*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Pakitype po ang inyong *Order Code* o *Contact Number* sa chat.\n\n"
                f"💡 _Kahit hindi kumpleto ang format, maiintindihan namin! Halimbawa:_ \n"
                f"• `ORD-84920`\n"
                f"• `84920` o `ord84920`\n"
                f"• `09123456789`"
            ),
            "inline_keyboard": [
                [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
            ]
        }

    # CHECK IF THE USER INPUT IS AN ORDER NUMBER / TRACKING QUERY
    order_query = normalize_order_query(text)
    if order_query or any(k in text.lower() for k in ['track', 'status', 'nasaan', 'labada', 'ord-']):
        # If text is something like "track 78378" or just "78378"
        query_to_search = order_query or text.strip()
        db = SessionLocal()
        try:
            refresh_machine_cycles(db)
            appointment = db.query(Appointment).filter(
                (Appointment.order_code == query_to_search) | 
                (Appointment.order_code == f"ORD-{query_to_search}") |
                (Appointment.phone_number == query_to_search)
            ).order_by(Appointment.appointment_id.desc()).first()

            if not appointment and query_to_search.isdigit():
                appointment = db.query(Appointment).filter(Appointment.appointment_id == int(query_to_search)).first()

            if appointment:
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
                        display_status = 'In Queue (Nasa Pila) ⏳'
                elif appointment.status == 'Confirmed':
                    display_status = 'Confirmed (Waiting Drop-off/Pickup) ⏳'

                turnaround = appointment.turnaround_option or '24 Hours'
                target_date = (appointment.schedule_time + timedelta(days=2)).strftime("%b %d, %Y") if ('2 day' in turnaround.lower() or '48' in turnaround.lower()) else ((appointment.schedule_time + timedelta(days=1)).strftime("%b %d, %Y") if appointment.schedule_time else "Within 24 Hours")
                order_id = appointment.order_code or f"ORD-{appointment.appointment_id:04d}"
                pay_status = appointment.payment_status or 'Pending'
                pay_badge = "✅ Paid" if pay_status.lower() == 'paid' else "⏳ Pending / Pay at Counter"

                return {
                    "telegram_message": (
                        f"🧺 *STATUS NG LABADA — BON LAUNDRY*\n"
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
                        f"_Salamat po sa pagtangkilik sa Bon Laundry Station!_"
                    ),
                    "inline_keyboard": [
                        [{"text": "🔍 I-track ang Ibang Order", "callback_data": "action_track"}],
                        [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
                    ]
                }
            else:
                if order_query:
                    return {
                        "telegram_message": (
                            f"🔍 *HINDI MAHANAP ANG ORDER*\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"Wala pong nahanap na record para sa `{query_to_search}`.\n\n"
                            f"Pakisigurado pong tama ang inyong Order Code o Contact Number."
                        ),
                        "inline_keyboard": [
                            [{"text": "🔍 Subukan Ulit", "callback_data": "action_track"}],
                            [{"text": "📞 Kausapin ang Staff", "callback_data": "action_contact"}],
                            [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
                        ]
                    }
        finally:
            db.close()

    # 4. RATES ACTION
    if action == 'action_rates':
        return {
            "telegram_message": (
                f"📋 *OFFICIAL RATE CARD — BON LAUNDRY STATION*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🧺 *DROP-OFF SERVICE PACKAGES (8kg Load):*\n"
                f"• *Classic:* ₱130 _(Wash, Dry, Fold)_\n"
                f"• *Saver:* ₱160 _(Wash, Dry, Fold + 1 Det + 1 Fabcon)_\n"
                f"• *Signature:* ₱200 _(Wash, Dry, Fold + 2 Det + 2 Fabcon)_\n"
                f"• *Premium:* ₱260 _(Sort, Superwash, Dry, Fold + Complete Care)_\n\n"
                f"⏱️ *SERVICE CHARGES / TURNAROUND:*\n"
                f"• *24 Hours Express:* ₱120\n"
                f"• *2 Days Economy:* ₱70\n\n"
                f"🧼 *SELF-SERVICE RATES:*\n"
                f"• *8kg Regular Load:* ₱145 | *13kg Titan Load:* ₱240\n"
                f"• *Superwash:* ₱105 | *Add Dry:* ₱70\n\n"
                f"🛵 *Delivery Fee:* ₱40 (Deca Homes) | ₱100 (Outside Deca)"
            ),
            "inline_keyboard": [
                [{"text": "🧺 Magpa-Laundry Na", "callback_data": "action_book"}],
                [{"text": "🏬 Live Machine Lobby", "callback_data": "action_lobby"}],
                [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
            ]
        }

    # 5. LIVE MACHINE LOBBY ACTION
    if action == 'action_lobby':
        db = SessionLocal()
        try:
            refresh_machine_cycles(db)
            machines = db.query(MachineStatus).all()
            total = len(machines)
            avail = len([m for m in machines if m.status.lower() == 'available'])
            running = len([m for m in machines if m.status.lower() == 'in-use'])
            maint = len([m for m in machines if m.status.lower() == 'maintenance'])

            traffic = "🟢 Light Traffic (Maraming Bakante)" if avail >= 10 else ("🟡 Moderate Rush" if avail >= 4 else "🔴 Heavy Traffic (Medyo Puno)")
            wait_time = "Walang pila — Ready for Wash!" if avail >= 8 else ("~15-30 mins" if avail >= 3 else "~45-60 mins")

            return {
                "telegram_message": (
                    f"🏬 *LIVE MACHINE LOBBY — BON LAUNDRY*\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📊 *Traffic Status:* {traffic}\n"
                    f"⏱️ *Estimated Wait Time:* {wait_time}\n\n"
                    f"⚡ *Live Machine Breakdown ({total} Total Units):*\n"
                    f"• 🟢 *Available / Ready:* *{avail} machines*\n"
                    f"• 🌀 *In Cycle / Running:* {running} machines\n"
                    f"• 🛠️ *Maintenance:* {maint} machines\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💡 _Tip: Pumunta o mag-book agad habang marami pang bakanteng machines!_"
                ),
                "inline_keyboard": [
                    [{"text": "🧺 Magpa-Laundry Na", "callback_data": "action_book"}],
                    [{"text": "🔄 Refresh Lobby", "callback_data": "action_lobby"}],
                    [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
                ]
            }
        finally:
            db.close()

    # 6. DECA DELIVERY INFO
    if action == 'action_delivery':
        return {
            "telegram_message": (
                f"🛵 *URBAN DECA HOMES PICKUP & DELIVERY INFO*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📍 *Service Area:* Urban Deca Homes, Ortigas (Buildings 1 hanggang 20).\n"
                f"💵 *Delivery Fee:* ₱40 lamang bawat biyahe.\n"
                f"🕒 *Operating Hours:* 8:00 AM – 10:00 PM Araw-araw.\n\n"
                f"✨ *Paano Gumagana?*\n"
                f"1. Mag-book gamit ang bot.\n"
                f"2. Ilagay ang Building at Unit number mo.\n"
                f"3. Kukunin ng rider ang labada sa unit mo.\n"
                f"4. Ihahatid pabalik nang malinis, mabango, at nakatupi!"
            ),
            "inline_keyboard": [
                [{"text": "🚗 Magpa-Pickup Na", "callback_data": "mode_pickup"}],
                [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
            ]
        }

    # 7. CONTACT & STAFF ESCALATION
    if action in ['action_contact', 'contact_staff']:
        return {
            "telegram_message": (
                f"📞 *KAUSAPIN ANG AMING STAFF & MANAGER*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🏬 *Store Branch:* Bon Laundry Station, Urban Deca Homes, Ortigas\n"
                f"👤 *Store Manager:* Genesis Samson\n"
                f"📞 *Direct Mobile / Viber:* 0917-XXX-XXXX / 0998-XXX-XXXX\n"
                f"🕒 *Customer Assistance Hours:* 8:00 AM – 10:00 PM Daily\n\n"
                f"May special request o customized order? Tawagan o i-message kami anumang oras!"
            ),
            "inline_keyboard": [
                [{"text": "🧺 Magpa-Laundry", "callback_data": "action_book"}],
                [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
            ]
        }

    # 7.1 PAYMENT OPTIONS ACTION
    if action in ['action_payment', 'faq_payment']:
        qr_img_link = f"{base_url}/static/images/gcash_qr.png" if base_url else "/static/images/gcash_qr.png"
        buttons = []
        if base_url:
            buttons.append([{"text": "📲 Tingnan / I-scan ang GCash QR Code", "url": qr_img_link}])
        buttons.extend([
            [{"text": "🧺 Magpa-Laundry Na", "callback_data": "action_book"}],
            [{"text": "🔍 I-track ang Order", "callback_data": "action_track"}],
            [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
        ])
        return {
            "telegram_message": (
                f"💳 *MGA PARAAN NG PAGBABAYAD (PAYMENT OPTIONS)*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Tumatanggap po kami ng sumusunod na payment methods:\n\n"
                f"1. 📱 *GCash (Instant Send Money / InstaPay QR)*\n"
                f"   • *Account Name:* `GE****S S.`\n"
                f"   • *Mobile Number:* `+63 992 659 ****`\n"
                f"   • 📲 [I-click dito para sa GCash QR Image]({qr_img_link})\n"
                f"   • _(Suportado ang direct scan via GCash o anumang banking app)_\n\n"
                f"2. 💚 *Maya & QR Ph*\n"
                f"   • Scan via Maya app o anumang QR Ph-enabled banking app\n\n"
                f"3. 💵 *Cash on Delivery (COD) / Counter*\n"
                f"   • Abot-bayad pagka-deliver ng rider sa inyong Unit o pag-dropoff sa store\n\n"
                f"4. 🏦 *Bank Transfer (InstaPay / PESONet)*\n"
                f"   • BPI, BDO, UnionBank, SeaBank, at iba pa via InstaPay\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📸 *PAALALA:* Pakisend po ang **screenshot ng inyong resibo / proof of payment** dito sa chat upang agad ma-verify ng aming cashier/staff!"
            ),
            "inline_keyboard": buttons
        }

    # 7.2 PAYMENT PROOF / SCREENSHOT SUBMISSION
    if has_photo or (text and any(k in text.lower() for k in ['screenshot', 'resibo', 'proof', 'nakabayad', 'bayad na', 'paid na', 'transferred', 'sent receipt', 'proof of payment'])):
        return {
            "telegram_message": (
                f"🧾 *NATANGGAP ANG IYONG PROOF OF PAYMENT! — BON LAUNDRY*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Maraming salamat po, *{user_name}*!\n\n"
                f"✅ *Matagumpay na natanggap ng aming system ang inyong payment screenshot / proof of transfer.*\n\n"
                f"🔍 *Status:* I-be-verify po ito agad ng aming cashier/staff upang mai-markang *Paid* ang inyong order.\n"
                f"💡 _Maaari ninyong subaybayan ang estado ng inyong labada anumang oras gamit ang Track Order button sa ibaba._"
            ),
            "inline_keyboard": [
                [{"text": "🔍 I-track ang Order", "callback_data": "action_track"}],
                [{"text": "📞 Kausapin ang Staff", "callback_data": "action_contact"}],
                [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
            ]
        }

    # 8. FAQS LIST ACTION
    if action == 'action_faqs':
        return {
            "telegram_message": (
                f"❓ *MGA MADALAS ITANONG (FAQS) — BON LAUNDRY*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Pumili ng paksa upang makita ang sagot:"
            ),
            "inline_keyboard": [
                [{"text": "💰 Magkano ang Laba & Presyo?", "callback_data": "action_rates"}],
                [{"text": "🛵 Paano ang Pickup & Delivery sa Deca?", "callback_data": "action_delivery"}],
                [{"text": "⏱️ Gaano katagal bago matapos?", "callback_data": "faq_turnaround"}],
                [{"text": "💳 Paano ang Bayaran (GCash/Cash)?", "callback_data": "faq_payment"}],
                [{"text": "❌ Paano mag-cancel ng Order?", "callback_data": "faq_cancel"}],
                [{"text": "📞 Kausapin ang Staff", "callback_data": "action_contact"}],
                [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
            ]
        }

    # 9. CHECK IF USER IS TRIGGERING DIRECT CONFIRMATION (Button or Text with Bldg/Unit/Phone)
    is_quickbook_action = action.startswith('quickbook_')
    bldg_match = re.search(r'\b(?:bldg|building|b)\.?\s*(\d+)\b', text, re.IGNORECASE) if text else None
    unit_match = re.search(r'\b(?:unit|u)\.?\s*(\d+)\b', text, re.IGNORECASE) if text else None
    phone_match = re.search(r'\b(09\d{9})\b', text) if text else None
    has_bldg_or_unit = bool(bldg_match or unit_match)

    if (is_quickbook_action or has_bldg_or_unit or phone_match) and not any(k in text.lower() for k in ['track', 'status', 'nasaan', 'ord-']):
        phone_num = phone_match.group(1) if phone_match else f"Telegram ({user_name})"
        bldg_num = bldg_match.group(1) if bldg_match else ''
        unit_num = unit_match.group(1) if unit_match else ''

        # Determine package, turnaround, and mode
        if is_quickbook_action:
            qb_parts = action.split('_')
            speed_code = qb_parts[1]
            turnaround = "24 Hours" if speed_code == '24h' else "2 Days"
            pkg_name = f"{qb_parts[2].capitalize()} (Wash, Dry, Fold)"
            is_pickup = 'pickup' in action
        else:
            is_pickup = bool(has_bldg_or_unit or 'pick' in text.lower() or 'deca' in text.lower())
            turnaround = '2 Days' if any(k in text.lower() for k in ['2 day', '2day', '48', 'tipid']) else '24 Hours'
            pkg_name = 'Saver (Wash, Dry, Fold)'
            if 'premium' in text.lower(): pkg_name = 'Premium (Complete Care)'
            elif 'signature' in text.lower(): pkg_name = 'Signature (Wash, Dry, Fold)'
            elif 'classic' in text.lower(): pkg_name = 'Classic (Wash, Dry, Fold)'

        order_mode = 'Pick-up & Delivery' if is_pickup else 'Drop-Off'
        priority_level = 'Graveyard Batch' if turnaround == '2 Days' else 'Express 24h'

        if bldg_num or unit_num:
            parts = []
            if bldg_num: parts.append(f"Deca Homes Bldg {bldg_num}")
            if unit_num: parts.append(f"Unit {unit_num}")
            condo_address = ", ".join(parts)
        else:
            condo_address = 'Urban Deca Homes, Ortigas (Store Counter)' if not is_pickup else 'Deca Homes Resident'

        clean_name = user_name

        db = SessionLocal()
        try:
            import secrets
            order_code = f"ORD-{secrets.randbelow(90000) + 10000}"
            now = datetime.now()

            new_appt = Appointment(
                order_code=order_code,
                customer_name=clean_name,
                customer_email=None,
                phone_number=phone_num,
                address=condo_address,
                service_type=pkg_name,
                turnaround_option=turnaround,
                priority_level=priority_level,
                order_mode=order_mode,
                payment_method='Cash on Delivery' if is_pickup else 'Cash on Counter',
                payment_status='Pending',
                fulfillment_status='For Pickup' if is_pickup else 'Waiting Drop-off',
                status='Confirmed',
                schedule_time=now,
                pickup_time=now.strftime("%I:%M %p")
            )
            db.add(new_appt)
            db.flush()

            new_queue = Queue(
                appointment_id=new_appt.appointment_id,
                customer_name=clean_name,
                status='Waiting',
                queue_number=QueueManager.generate_next_queue_number(db),
                turnaround_option=turnaround,
                priority_level=priority_level,
                order_mode=order_mode,
                payment_method='Cash on Delivery' if is_pickup else 'Cash on Counter',
                payment_status='Pending',
                fulfillment_status='For Pickup' if is_pickup else 'Waiting Drop-off'
            )
            db.add(new_queue)
            db.commit()

            est_price = "₱280.00" if is_pickup else "₱240.00"

            return {
                "telegram_message": (
                    f"🎉 *APPOINTMENT CONFIRMED! — BON LAUNDRY*\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📋 *Order Code:* `{order_code}`\n"
                    f"👤 *Customer:* {clean_name}\n"
                    f"📞 *Contact:* {phone_num}\n"
                    f"🧺 *Package:* {pkg_name}\n"
                    f"⏱️ *Turnaround:* {turnaround} Express\n"
                    f"🚚 *Mode:* {order_mode}\n"
                    f"📍 *Address:* {condo_address}\n"
                    f"💵 *Est. Total:* {est_price}\n\n"
                    f"💳 *Payment Options:*\n"
                    f"• 📱 *GCash:* `+63 992 659 ****` (`GE****S S.`)\n"
                    f"• 💚 *Maya:* QR Ph / Send Money\n"
                    f"• 💵 *Cash:* Pay upon delivery (COD) o sa counter\n"
                    f"• 🏦 *Bank Transfer:* InstaPay supported\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"✅ *Nai-save na sa aming system bilang Confirmed!*\n"
                    f"💡 _Gamitin ang Order Code `{order_code}` upang mai-track ang inyong labada anumang oras._"
                ),
                "inline_keyboard": [
                    [{"text": f"🔍 I-track ang {order_code}", "callback_data": f"track_{order_code}"}],
                    [{"text": "💳 Payment Details (GCash/Maya)", "callback_data": "action_payment"}],
                    [{"text": "🔙 Main Menu", "callback_data": "show_menu"}]
                ]
            }
        except Exception as e:
            db.rollback()
            print("Auto booking error:", e)
        finally:
            db.close()

    # 10. CHECK FAQS KNOWLEDGE BASE MATCHES
    lower_text = text.lower()
    for faq in FAQS:
        if any(k in lower_text for k in faq['keywords']) or action == f"faq_{faq['keywords'][0]}":
            return {
                "telegram_message": faq['answer'],
                "inline_keyboard": [faq.get("buttons", [{"text": "🔙 Main Menu", "callback_data": "show_menu"}])]
            }

    # 11. INTELLIGENT AI FALLBACK & CONTACT ESCALATION
    return {
        "telegram_message": (
            f"👋 Kumusta, *{user_name}*!\n\n"
            f"Nakatanggap kami ng iyong mensahe: _\"{text}\"_\n\n"
            f"Kung nais ninyong magpa-laundry, mag-track ng labada, o magtanong sa staff, pumili po sa mga sumusunod:"
        ),
        "inline_keyboard": [
            [
                {"text": "🧺 Magpa-Laundry", "callback_data": "action_book"},
                {"text": "🔍 I-track ang Labada", "callback_data": "action_track"}
            ],
            [
                {"text": "📋 Presyo & Packages", "callback_data": "action_rates"},
                {"text": "🏬 Machine Lobby", "callback_data": "action_lobby"}
            ],
            [
                {"text": "❓ FAQs & Tulong", "callback_data": "action_faqs"},
                {"text": "📞 Kausapin ang Staff", "callback_data": "action_contact"}
            ]
        ]
    }
