# CHAPTER III: METHODOLOGY AND PROJECT DESIGN
## 3.8 Data Dictionary Tables

The following data dictionary tables illustrate the structural schema, field definitions, data types, sizes, and constraint keys for all relational database tables implemented in the **Bon Laundry Station Management System** (`models/schemas.py`).

---

### Table 3. Users Table (`tbl_users`)
Table 3 illustrates the user accounts permitted to access the system across different authorization roles (Super Admin, Manager, Staff, Customer). It maintains secure password hashes, Google OAuth identity mappings, failed login counters, and temporary account lockout timestamps.

| Field Name | Description | Field Type | Field Size | Type of Key |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | Unique user identifier | Integer | 11 | Primary Key |
| `name` | Full name of the user | Varchar | 100 | None |
| `email` | Unique email address used for system login | Varchar | 100 | Unique Key |
| `password` | Hashed password string (bcrypt) | Varchar | 255 | None |
| `user_role` | System authorization role (`Super Admin`, `Manager`, `Staff`, `Customer`) | Enum | — | None |
| `google_id` | Unique Google OAuth 2.0 account identifier | Varchar | 100 | Unique Key |
| `avatar_url` | Profile avatar image URL | Varchar | 255 | None |
| `failed_login_attempts` | Counter for consecutive failed login attempts | Integer | 11 | None |
| `login_locked_until` | Timestamp until which account remains locked | DateTime | — | None |
| `password_reset_token` | Secure token generated for password recovery | Varchar | 128 | None |
| `password_reset_expires_at` | Expiration timestamp of password reset token | DateTime | — | None |

---

### Table 4. Appointment Table (`tbl_appointment`)
Table 4 illustrates the laundry appointment bookings created online or at the counter. It records customer details, order modes (Drop-Off or Pick-up & Delivery), Urban Deca Homes Ortigas building and unit numbers, service types, turnaround priorities, fulfillment progression stages, payment statuses, and cancellation OTP details.

| Field Name | Description | Field Type | Field Size | Type of Key |
| :--- | :--- | :--- | :--- | :--- |
| `appointment_id` | Unique appointment identifier | Integer | 11 | Primary Key |
| `customer_id` | Reference to the registered user | Integer | 11 | Foreign Key |
| `order_code` | Unique public tracking code (e.g., `ORD-XXXXX`) | Varchar | 30 | Unique Key, Index |
| `customer_name` | Name of the customer placing the order | Varchar | 100 | None |
| `customer_email` | Contact email address of the customer | Varchar | 100 | None |
| `phone_number` | Contact mobile number of the customer | Varchar | 30 | None |
| `address` | Delivery address or Urban Deca Homes Building & Unit | Varchar | 255 | None |
| `pickup_time` | Scheduled pickup time window | Varchar | 50 | None |
| `schedule_time` | Date and time scheduled for laundry service | DateTime | — | None |
| `service_type` | Laundry service type (e.g., Classic, Premium, Self-Service) | Varchar | 50 | None |
| `turnaround_option` | Turnaround option selected (`24 Hours`, `2 Days`) | Varchar | 30 | None |
| `priority_level` | Priority classification (`Standard`, `Express`, `Graveyard Batch`) | Varchar | 30 | None |
| `order_mode` | Handling mode (`Drop-Off`, `Pick-up & Delivery`) | Varchar | 30 | None |
| `payment_method` | Selected payment method (`Cash`, `GCash / E-Wallet`, `Bank Transfer`) | Varchar | 50 | None |
| `payment_status` | Status of payment (`Pending`, `Paid`, `Refunded`) | Varchar | 30 | None |
| `fulfillment_status` | Operational stage (`Waiting Drop-off`, `In Queue`, `In Laundry`, `Out for Delivery`, `Delivered`) | Varchar | 50 | None |
| `status` | Booking lifecycle status (`Pending`, `Confirmed`, `Completed`, `Cancelled`) | Enum | — | None |
| `cancellation_reason` | Reason specified upon order cancellation | Varchar | 255 | None |
| `cancelled_at` | Timestamp when cancellation was executed | DateTime | — | None |
| `refund_status` | Status of refund processing if applicable | Varchar | 50 | None |
| `cancellation_otp` | 6-digit numeric OTP for cancellation verification | Varchar | 10 | None |
| `cancellation_otp_expires_at`| Expiration timestamp for cancellation OTP | DateTime | — | None |

---

### Table 5. Machine Status Table (`tbl_machine_status`)
Table 5 illustrates the live telemetry and operational status of the 19 commercial machines in the laundromat fleet (14 Regular 8kg Washers and 5 Titan 13kg Dryers). It maintains cycle timers, assigned customer identifiers, pricing rates, and cumulative run counters.

| Field Name | Description | Field Type | Field Size | Type of Key |
| :--- | :--- | :--- | :--- | :--- |
| `machine_id` | Unique machine identifier | Integer | 11 | Primary Key |
| `machine_type` | Machine classification (`Washer`, `Dryer`) | Enum | — | None |
| `capacity_kg` | Load capacity in kilograms (8kg or 13kg) | Integer | 11 | None |
| `status` | Display status (`Available`, `In-Use`, `Maintenance`) | Enum | — | None |
| `machine_name` | Name/Label assigned to the machine (e.g., Regular Washer #1) | Varchar | 50 | None |
| `price_per_cycle` | Cost per machine operating cycle | Decimal | 10, 2 | None |
| `operational_state` | Technical state (`available`, `running`, `cooldown`) | Varchar | 20 | None |
| `assigned_customer_name` | Name of customer currently assigned to machine | Varchar | 100 | None |
| `cycle_type` | Cycle program (e.g., Quick, Heavy, Superwash) | Varchar | 20 | None |
| `cycle_started_at` | Timestamp when current cycle began | DateTime | — | None |
| `cycle_ends_at` | Timestamp when current cycle will conclude | DateTime | — | None |
| `usage_count` | Total completed cycles for maintenance scheduling | Integer | 11 | None |
| `last_used_at` | Timestamp of most recent cycle completion | DateTime | — | None |

---

### Table 6. Transaction Table (`tbl_transaction`)
Table 6 illustrates completed financial transactions and billing receipts. It records measured laundry load weights, calculated total charges, assigned machines, and payment completion timestamps.

| Field Name | Description | Field Type | Field Size | Type of Key |
| :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | Unique billing transaction identifier | Integer | 11 | Primary Key |
| `customer_id` | Reference to customer account | Integer | 11 | Foreign Key |
| `weight_kg` | Measured weight of laundry load in kilograms | Decimal | 4, 2 | None |
| `total_amount` | Total billed amount for the transaction | Decimal | 10, 2 | None |
| `payment_status` | Status of transaction payment (`Pending`, `Paid`) | Enum | — | None |
| `created_at` | Timestamp when transaction was recorded | Timestamp | — | None |
| `customer_name` | Name of customer associated with transaction | Varchar | 100 | None |
| `machine_id` | Reference to machine utilized | Integer | 11 | None |
| `cycle_type` | Cycle program applied | Varchar | 20 | None |

---

### Table 7. Queue Table (`tbl_queue`)
Table 7 illustrates the active operational queue within the laundromat facility. It manages sequential queue ticketing, estimated customer wait times based on active machine cycles, and link associations with appointments and machines.

| Field Name | Description | Field Type | Field Size | Type of Key |
| :--- | :--- | :--- | :--- | :--- |
| `queue_id` | Unique queue entry identifier | Integer | 11 | Primary Key |
| `queue_number` | Sequential queue ticket number | Integer | 11 | None |
| `appointment_id` | Reference to corresponding appointment | Integer | 11 | Foreign Key |
| `machine_id` | Reference to assigned machine | Integer | 11 | Foreign Key |
| `status` | Active queue status (`Waiting`, `Processing`, `Done`) | Enum | — | None |
| `turnaround_option` | Turnaround selection (`24 Hours`, `2 Days`) | Varchar | 30 | None |
| `priority_level` | Scheduling priority (`Standard`, `Express`, `Graveyard Batch`) | Varchar | 30 | None |
| `order_mode` | Service handling mode (`Drop-Off`, `Pick-up & Delivery`) | Varchar | 30 | None |
| `payment_method` | Method of payment | Varchar | 50 | None |
| `payment_status` | Current payment status | Varchar | 30 | None |
| `fulfillment_status` | Current fulfillment status | Varchar | 50 | None |
| `estimated_waiting_time` | Calculated waiting time in minutes | Integer | 11 | None |
| `customer_name` | Name of customer in queue | Varchar | 100 | None |
| `transaction_id` | Reference to associated transaction | Integer | 11 | None |

---

### Table 8. System Settings Table (`tbl_system_settings`)
Table 8 illustrates the administrative configuration parameters that govern global pricing rates and default machine cycle durations across the laundromat operations.

| Field Name | Description | Field Type | Field Size | Type of Key |
| :--- | :--- | :--- | :--- | :--- |
| `setting_id` | Unique setting record identifier | Integer | 11 | Primary Key |
| `price_per_kg` | Default rate per kilogram (₱65.00 default) | Decimal | 10, 2 | None |
| `max_weight_limit_kg` | Maximum load capacity limit per standard washer | Integer | 11 | None |
| `standard_washer_time_mins` | Standard wash cycle duration in minutes (35 default) | Integer | 11 | None |
| `standard_dryer_time_mins` | Standard dry cycle duration in minutes (30 default) | Integer | 11 | None |

---

### Table 9. Prediction Logs Table (`tbl_prediction_logs`)
Table 9 illustrates the historical forecast records generated by the machine learning engine (2nd-degree polynomial regression). It preserves predicted hourly rush hour demand, actual measured footfall, and resulting MAPE (Mean Absolute Percentage Error) scores.

| Field Name | Description | Field Type | Field Size | Type of Key |
| :--- | :--- | :--- | :--- | :--- |
| `prediction_id` | Unique prediction record identifier | Integer | 11 | Primary Key |
| `prediction_target` | Target metric predicted (e.g., Hourly Rush Hour Demand) | Varchar | 50 | None |
| `predicted_value` | Projected footfall or rush hour index | Varchar | 100 | None |
| `actual_value` | Actual observed customer footfall | Varchar | 100 | None |
| `mape_score` | Mean Absolute Percentage Error score | Decimal | 5, 2 | None |
| `logged_at` | Timestamp when prediction was recorded | Timestamp | — | None |

---

### Table 10. Audit Logs Table (`tbl_audit_logs`)
Table 10 illustrates the immutable security audit trail that records all privileged administrative actions, configuration adjustments, and order state overrides.

| Field Name | Description | Field Type | Field Size | Type of Key |
| :--- | :--- | :--- | :--- | :--- |
| `log_id` | Unique audit log identifier | Integer | 11 | Primary Key |
| `user_id` | Identifier of the user performing the action | Integer | 11 | Foreign Key |
| `user_name` | Name of the user | Varchar | 100 | None |
| `user_email` | Email address of the user | Varchar | 100 | None |
| `user_role` | Role of the user (`Manager`, `Staff`, `Super Admin`) | Varchar | 30 | None |
| `action` | Action descriptor (e.g., Override Payment Status, Edit Settings) | Varchar | 80 | None |
| `entity_type` | Targeted entity (e.g., Appointment, Machine, Settings) | Varchar | 50 | None |
| `entity_id` | Identifier of affected record | Varchar | 50 | None |
| `details` | Granular description of modification | Varchar | 500 | None |
| `ip_address` | Client IP address of requesting host | Varchar | 45 | None |
| `created_at` | Timestamp when action occurred | Timestamp | — | None |
