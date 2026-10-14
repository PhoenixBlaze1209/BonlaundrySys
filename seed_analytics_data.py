# seed_analytics_data.py
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from config.database import SessionLocal
from models.schemas import User, Transaction, Appointment, MachineStatus, PredictionLog

def seed_data():
    db = SessionLocal()
    try:
        print("[+] Starting dataset seeding for Bon Laundry PA & Analytics...")

        # 1. Seed Customer Users if they don't exist
        customers_info = [
            ("Maria Santos", "maria.santos@gmail.com"),
            ("Juan Dela Cruz", "juan.delacruz@gmail.com"),
            ("Angelica Reyes", "angelica.reyes@gmail.com"),
            ("Carl Justine", "carl.justine@gmail.com"),
            ("Bea Alonzo", "bea.alonzo@gmail.com"),
            ("David Licauco", "david.licauco@gmail.com"),
            ("Katrina Halili", "katrina.halili@gmail.com"),
            ("Mark Anthony", "mark.anthony@gmail.com"),
            ("Sarah Geronimo", "sarah.g@gmail.com"),
            ("Alden Richards", "alden.r@gmail.com"),
        ]

        created_users = []
        for name, email in customers_info:
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                user = User(
                    name=name,
                    email=email,
                    password=generate_password_hash("password123"),
                    user_role="Customer",
                    failed_login_attempts=0
                )
                db.add(user)
                db.flush()
                created_users.append(user)
            else:
                created_users.append(existing)

        all_customers = db.query(User).filter(User.user_role == 'Customer').all()
        customer_ids = [c.user_id for c in all_customers]
        customer_names = [c.name for c in all_customers] + [
            "Walk-in Customer", "Patricia Lim", "Robert Chen", "Eileen Gu", 
            "Danilo Ramos", "Grace Poe", "Michael Tan", "Jessica Soho"
        ]

        # Machines list
        machines = db.query(MachineStatus).all()
        washer_ids = [m.machine_id for m in machines if m.machine_type == 'Washer'] or [1, 2, 3, 4, 5, 6, 7, 8]
        dryer_ids = [m.machine_id for m in machines if m.machine_type == 'Dryer'] or [15, 16, 17, 18, 19]

        # Services & Price configurations
        services_catalog = [
            {"name": "Self-Service Wash & Dry (8kg)", "weight": 8.0, "price": 145.00, "cycle": "washing"},
            {"name": "Self-Service Wash & Dry (13kg)", "weight": 13.0, "price": 240.00, "cycle": "washing"},
            {"name": "Drop-Off Classic (8kg)", "weight": 8.0, "price": 130.00, "cycle": "washing"},
            {"name": "Drop-Off Saver (8kg)", "weight": 8.0, "price": 160.00, "cycle": "washing"},
            {"name": "Drop-Off Signature (8kg)", "weight": 8.0, "price": 200.00, "cycle": "washing"},
            {"name": "Drop-Off Premium (8kg)", "weight": 8.0, "price": 260.00, "cycle": "washing"},
            {"name": "Drying Express (8kg)", "weight": 8.0, "price": 145.00, "cycle": "drying"},
            {"name": "Drying Heavy (13kg)", "weight": 13.0, "price": 240.00, "cycle": "drying"},
        ]

        # 2. Generate Realistic Historical Transactions spanning past 45 days
        # Operating hours: 8 AM - 8 PM (08:00 to 20:00)
        # Peak demand around 1:00 PM - 3:00 PM (13:00 - 15:00)
        hour_probabilities = {
            8: 0.04,
            9: 0.06,
            10: 0.08,
            11: 0.10,
            12: 0.12,
            13: 0.14,
            14: 0.18,  # Peak hour (2:00 PM)
            15: 0.15,
            16: 0.11,
            17: 0.08,
            18: 0.06,
            19: 0.04,
            20: 0.02
        }

        hours_list = list(hour_probabilities.keys())
        prob_weights = list(hour_probabilities.values())

        now = datetime.now()
        start_date = now - timedelta(days=45)

        transactions_to_add = []
        appointments_to_add = []
        
        current_day = start_date
        app_counter = 100

        while current_day.date() <= now.date():
            is_weekend = current_day.weekday() in (5, 6)
            daily_tx_count = random.randint(7, 12) if is_weekend else random.randint(4, 8)
            
            for _ in range(daily_tx_count):
                chosen_hour = random.choices(hours_list, weights=prob_weights, k=1)[0]
                chosen_minute = random.randint(0, 59)
                chosen_second = random.randint(0, 59)
                tx_timestamp = current_day.replace(hour=chosen_hour, minute=chosen_minute, second=chosen_second)

                if tx_timestamp > now:
                    continue

                svc = random.choice(services_catalog)
                customer_name = random.choice(customer_names)
                cust_id = random.choice(customer_ids) if customer_name in [c.name for c in all_customers] else None

                weight_variance = round(random.uniform(-0.5, 1.2), 2)
                actual_weight = max(2.0, round(svc["weight"] + weight_variance, 2))

                if svc["cycle"] == "drying":
                    assigned_machine = random.choice(dryer_ids)
                else:
                    assigned_machine = random.choice(washer_ids)

                tx = Transaction(
                    customer_id=cust_id,
                    weight_kg=actual_weight,
                    total_amount=svc["price"],
                    payment_status="Paid",
                    created_at=tx_timestamp,
                    customer_name=customer_name if not cust_id else None,
                    machine_id=assigned_machine,
                    cycle_type=svc["cycle"]
                )
                transactions_to_add.append(tx)

                if random.random() < 0.35:
                    app_counter += 1
                    app = Appointment(
                        customer_id=cust_id,
                        order_code=f"ORD-{app_counter:04d}",
                        customer_name=customer_name,
                        customer_email=f"{customer_name.lower().replace(' ', '.')}@gmail.com",
                        phone_number=f"09{random.randint(100000000, 999999999)}",
                        address="Naga City, Camarines Sur",
                        pickup_time=f"{chosen_hour}:00",
                        schedule_time=tx_timestamp,
                        service_type="Wash-Dry-Fold" if svc["price"] >= 160 else "Wash-Only",
                        status="Completed" if tx_timestamp < now - timedelta(hours=2) else "Confirmed",
                        verified_at=tx_timestamp
                    )
                    appointments_to_add.append(app)

            current_day += timedelta(days=1)

        db.bulk_save_objects(transactions_to_add)
        db.bulk_save_objects(appointments_to_add)
        db.commit()
        print(f"[+] Added {len(transactions_to_add)} historical transactions and {len(appointments_to_add)} appointments.")

        # 3. Seed Prediction Logs in tbl_prediction_logs for Auditing
        print("[+] Seeding historical prediction logs for PA auditing...")
        prediction_logs_to_add = []
        for d in range(30, 0, -1):
            log_date = now - timedelta(days=d, hours=random.randint(6, 10))
            pred_time = random.choice(["2:00 PM", "2:00 PM", "2:00 PM", "3:00 PM", "1:00 PM"])
            actual_time = random.choice(["2:00 PM", "2:00 PM", "3:00 PM", "2:00 PM"])
            mape_val = round(random.uniform(4.5, 8.8), 2)

            log_entry = PredictionLog(
                prediction_target="Peak_Demand_Hour",
                predicted_value=pred_time,
                actual_value=actual_time,
                mape_score=mape_val,
                logged_at=log_date
            )
            prediction_logs_to_add.append(log_entry)

        db.bulk_save_objects(prediction_logs_to_add)
        db.commit()
        print(f"[+] Added {len(prediction_logs_to_add)} historical prediction logs.")

        # 4. Update machine usage counts based on total assigned transactions
        for m in machines:
            usage_count = db.query(Transaction).filter(Transaction.machine_id == m.machine_id).count()
            m.usage_count = usage_count
            m.last_used_at = now - timedelta(hours=random.randint(1, 24))
        db.commit()
        print("[+] Updated machine usage statistics.")

        print("[SUCCESS] Successfully populated past data for Bon Laundry System!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
