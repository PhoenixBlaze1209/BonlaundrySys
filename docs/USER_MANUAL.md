# Bon Laundry Station — User Guide & Standard Operating Procedures
**Role-by-Role Practical Guide & Step-by-Step Workflows**  
*Urban Deca Homes Ortigas Branch*

---

## Quick Navigation Index

1. [Customer User Guide & Step-by-Step Instructions](#1-customer-user-guide--step-by-step-instructions)
   * 1.1 How to Sign In via Google Single Sign-On (SSO)
   * 1.2 How to Book a Laundry Service Online (4-Step Wizard)
   * 1.3 How to Track Live Orders & Lifecycle Milestones
   * 1.4 How to View Service Rates & Official Price Tariffs
   * 1.5 How to Inspect Live Machine Fleet Availability
   * 1.6 How to Cancel a Pending Order with OTP Verification
2. [Staff Operations Guide & Step-by-Step Instructions](#2-staff-operations-guide--step-by-step-instructions)
   * 2.1 Front-Desk Operations Console Overview
   * 2.2 How to Verify and Check In Customer Orders at the Counter
   * 2.3 How to Process Walk-In POS Job Orders
   * 2.4 How to Manage Online Bookings & Condo Doorstep Pickups
   * 2.5 How to Advance Orders on the Live Queue Board
   * 2.6 How to Operate Machine Timers & Maintenance Mode
   * 2.7 How to Handle Late Garment Retrieval Penalties
3. [Manager Supervisory Guide & Step-by-Step Instructions](#3-manager-supervisory-guide--step-by-step-instructions)
   * 3.1 Supervisory Console Overview
   * 3.2 How to Interpret Machine Learning Peak Hour Demand Forecasts
   * 3.3 How to Allocate Habitual VIP "Ghost Slots"
   * 3.4 How to Reconcile the Daily Sales Ledger, Tally Cash & Export CSV
   * 3.5 How to Review the Chronological Security Audit Trail
4. [Super Admin Administration Guide & Step-by-Step Instructions](#4-super-admin-administration-guide--step-by-step-instructions)
   * 4.1 How to Use the Dynamic Role Perspective Switcher
   * 4.2 How to Pre-Register Staff & Manager Accounts for Google SSO
   * 4.3 How to Promote, Demote, or Reassign User Roles
   * 4.4 How to Configure Store Tariffs, Grace Periods & Late Multa Penalties
   * 4.5 How to Configure the Machine Hardware Fleet Matrix
5. [Role Navigation & Route Reference Table](#5-role-navigation--route-reference-table)

---

## 1. Customer User Guide & Step-by-Step Instructions

The Customer Portal provides self-service laundry booking, live order tracking, transparent rate cards, and machine fleet telemetry for Urban Deca Homes Ortigas residents.

---

### 1.1 How to Sign In via Google Single Sign-On (SSO)

1. Open your web browser and go to `/login`.
2. Click **Continue with Google**.
3. Select your Google account.
4. You will be automatically redirected to your personal customer portal at `/customer/dashboard`.

> [!NOTE]
> No manual password creation is required. Your name, email, and Google profile picture are automatically synced to your account.

---

### 1.2 How to Book a Laundry Service Online (4-Step Wizard)

![Figure 1: Customer Online Booking Wizard](file:///c:/Users/genes/bon-laundry/docs/screenshots/booking.jpeg)

#### Step-by-Step Procedure:
1. From the portal header or top navigation bar, click the **Book Appointment** tab (`#tab-content-book` or `/book`).
2. **Step 1 — Service Tier, Loads & Mode**:
   * Select your desired service tier:
     * **Wash, Dry & Fold**: Complete full-service package.
     * **Wash Only**: Self-drying or line-drying.
     * **Dry Only**: For pre-washed garments.
     * **Bulky Comforter / Blanket**: Specialized large-drum cycle.
   * Select the number of loads: click **1 Load** (up to 8.0 kg), **2 Loads** (up to 16.0 kg), or **3 Loads**.
   * Choose your service mode:
     * **Drop-Off at Station**: Personal counter drop-off.
     * **Self-Service**: On-site assisted machine use.
     * **Condo Doorstep Pickup & Delivery**: Station staff collects and returns laundry to your condo unit.
   * Click **Next Step: Schedule**.
3. **Step 2 — Schedule & Time Slot**:
   * Pick your preferred date using the calendar input.
   * Select an available 2-hour window (e.g., `08:00 AM - 10:00 AM`, `10:00 AM - 12:00 PM`, or `02:00 PM - 04:00 PM`).
   * *If Condo Pickup is selected*: Enter your **Building Number** (e.g., `Bldg 12`) and **Unit Number** (e.g., `Unit 304`).
   * Click **Next Step: Contact & Pay**.
4. **Step 3 — Contact Details & Payment Method**:
   * Confirm your contact details (Full Name and Mobile Phone Number).
   * Select your payment channel:
     * **Cash on Drop-Off / COD**: Pay upon physical handover.
     * **Pay Online Now via PayMongo**: Direct digital payment via GCash, Maya, GrabPay, or Credit/Debit Card.
   * Click **Next Step: Review**.
5. **Step 4 — Review, Liability Waiver & Confirmation**:
   * Review the itemized cost breakdown (base loads, detergent add-ons, and delivery fees).
   * Check the **Customer Equipment Liability Policy** checkbox, certifying that all pockets have been emptied of coins, pens, and sharp objects.
   * Click **Confirm Booking**.
   * Your unique **Order Reference Code** (e.g., `ORD-84920`) is issued, and an SMS confirmation is sent to your phone.

---

### 1.3 How to Track Live Orders & Lifecycle Milestones

![Figure 2: Customer Live Order Tracking & Queue Status](file:///c:/Users/genes/bon-laundry/docs/screenshots/orders_tracking.jpeg)

#### Step-by-Step Procedure:
1. In the customer portal, click the **My Orders** tab (`#tab-content-orders`).
2. Locate your active order card, or enter your Order Reference Code (e.g., `ORD-84920`) in the search box.
3. Observe the live 4-step progress tracker:
   * **Step 1: Order Received**: Booking registered in the system; awaiting drop-off or doorstep pickup.
   * **Step 2: In Queue**: Staff verified your laundry at the counter; weight entered; ticket `Q-XXX` issued.
   * **Step 3: In Progress**: Garments loaded into the washer or dryer; active cycle running with a live timer.
   * **Step 4: Ready for Pick-Up**: Cycle complete; laundry folded and bagged; ready for collection or delivery.
4. Check the **Assigned Machine** badge (e.g., `Washer 04`) and estimated turnaround time to know when your laundry will be finished.

---

### 1.4 How to View Service Rates & Official Price Tariffs

![Figure 3: Services & Official Store Rate Card](file:///c:/Users/genes/bon-laundry/docs/screenshots/services_rate.jpeg)

#### Step-by-Step Procedure:
1. Click the **Services & Rates** tab (`#tab-content-services`).
2. Review the transparent store rate card:
   * **Regular Wash (Washer)**: Up to 8.0 kg — **₱145.00** flat cycle fee (₱65.00/kg base tariff).
   * **Titan Dry (Dryer)**: Up to 13.0 kg — **₱145.00** flat cycle fee.
   * **Wash, Dry & Fold Bundle**: 1 Load (8.0 kg) — **₱290.00** (24-hour turnaround SLA).
   * **Express Same-Day Rush**: **+₱100.00** surcharge (4–6 hour turnaround SLA).
   * **Bulky Comforter / Heavy Blanket**: **₱200.00** flat fee.
   * **Detergent & Fabric Softener Add-ons**: Ariel/Tide (₱20.00/sachet), Downy (₱15.00/sachet).
   * **Condo Delivery**: Free or ₱30.00 promotional rate for Urban Deca Homes Ortigas residents.

---

### 1.5 How to Inspect Live Machine Fleet Availability

![Figure 4: Live Machine Fleet Lobby Telemetry](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig1_fleet_lobby.jpg)

#### Step-by-Step Procedure:
1. Click the **Live Lobby** tab (`#tab-content-lobby`).
2. Inspect the telemetry grid of all 19 shop machines (14 Washers and 5 Dryers).
3. Review the status indicators:
   * 🟢 **Available**: Ready for immediate assignment.
   * 🟡 **In-Use (Walk-In)**: Active walk-in cycle running with live countdown timer.
   * 🔵 **In-Use (Online Order)**: Active cycle assigned to a scheduled online customer.
   * 🔴 **Maintenance**: Offline for servicing or drum sanitation.
4. Check the **Estimated Waiting Time (EWT)** banner to plan your visit during low-traffic periods.

---

### 1.6 How to Cancel a Pending Order with OTP Verification

1. Navigate to **My Orders** (`#tab-content-orders`).
2. Locate the active order card (must be in `Pending` or `In Queue` status).
3. Click the **Cancel Order** button.
4. The system sends a 6-digit One-Time Password (OTP) to your registered email and mobile phone.
5. In the cancellation dialog, enter the 6-digit OTP and select your reason for cancellation.
6. Click **Confirm Cancellation**. The order is cancelled, your reserved slot is released, and confirmation is displayed.

> [!WARNING]
> Orders that have already entered the active washing or drying cycle (`In Progress`) cannot be cancelled online. Please contact the front desk directly.

---

## 2. Staff Operations Guide & Step-by-Step Instructions

The Staff Console is designed for countertop operators handling physical intake, digital scale weighing, machine allocation, queue progression, and customer handovers.

![Figure 5: Staff Front-Desk Operations Dashboard](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig21_staff_dashboard.jpg)

---

### 2.1 Front-Desk Operations Console Overview
* **Sign In**: Navigate to `/login` and sign in with your pre-registered Google account. You will automatically land on `/staff/dashboard`.
* **Sidebar Navigation**:
  * **Dashboard**: High-level telemetry, active queue counts, and live activity feed.
  * **Verify Order**: Counter intake and digital scale weighing terminal.
  * **Appointments**: Incoming online bookings and condo pickup requests.
  * **Queue Order**: Live queue board with cycle progression controls.
  * **Machine Fleet**: Status controls and manual timer overrides for all 19 machines.

---

### 2.2 How to Verify and Check In Customer Orders at the Counter

![Figure 6: Counter Order Verification & Digital Scale Terminal](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig22_staff_verify.jpg)

#### Step-by-Step Procedure:
1. Click the **Verify Order** tab on the sidebar (or open `/staff/verify-order`).
2. **Order Lookup**:
   * Request the customer's Order Code (e.g., `ORD-84920` or digits only like `84920`) or mobile phone number.
   * Enter the code or number in the search field and press **Enter** (or click **Look Up**). The system automatically resolves numeric-only inputs (e.g., `84920` → `ORD-84920`).
   * Verify customer name, service package, and delivery preference.
3. **Physical Scale Weighing**:
   * Place the laundry bag on the digital countertop scale.
   * Enter the exact scale weight in kilograms (e.g., `7.4 kg`) in the **Physical Scale Weight** field.
   * *If the weight exceeds the 8.0 kg limit*: The system alerts you to split the laundry into two loads.
4. **Machine Recommendation**:
   * Review the machine unit recommended by the system (e.g., `Regular Washer 03`).
   * Accept the recommended machine or select an alternate available unit.
5. **Equipment Liability Verification**:
   * Ask the customer: *"Have you checked all pockets for coins, pens, or metal objects?"*
   * Verify the liability check displayed on screen.
6. **Payment Collection**:
   * If payment status is `Pending`, collect cash or confirm PayMongo online payment.
   * Click **Mark as Paid**.
7. **Confirm Check-In**:
   * Click **Confirm & Dispatch to Queue**.
   * The system assigns a physical queue ticket (e.g., `Q-014`), updates the order to `In Queue`, and dispatches an arrival confirmation SMS to the customer.

---

### 2.3 How to Process Walk-In POS Job Orders

1. On the operations header or sidebar, click **Walk-in Booking** (or visit `/book`).
2. Select the customer's requested service tier (e.g., *Wash, Dry & Fold*).
3. Set the load count based on laundry volume.
4. Enter the customer's Name and Mobile Phone Number.
5. Click **Submit Walk-In Order** to generate an instant Order Code.
6. Return to the **Verify Order** terminal (`/staff/verify-order`) and follow the check-in steps in Section 2.2 to weigh, assign a machine, collect payment, and issue a queue ticket.

---

### 2.4 How to Manage Online Bookings & Condo Doorstep Pickups

![Figure 7: Online Appointments & Condo Pickup Intake](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig23_staff_appointments.jpg)

#### Step-by-Step Procedure:
1. Click the **Appointments** tab (`#view-appointment`).
2. Filter the table by clicking **Pending** or **Confirmed**.
3. For Condo Doorstep Pickups:
   * Review the scheduled time window, customer name, and Building/Unit number (e.g., `Bldg 14, Unit 512`).
   * Dispatch floor staff to collect the laundry bag from the resident's door.
4. When the laundry arrives at the counter, click the **Check-In** button on the table row.
5. The order loads directly into the Verification Terminal for weighing and queue assignment.

---

### 2.5 How to Advance Orders on the Live Queue Board

![Figure 8: Live Queue Order Board & Floor Dispatch](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig24_staff_queue.jpg)

#### Step-by-Step Procedure:
1. Click the **Queue Order** tab (`#view-queue`).
2. Review the sequence of tickets arranged by priority and ticket number (`Q-001`, `Q-002`, etc.).
3. **To Start a Wash or Dry Cycle**:
   * Carry the laundry bag to the assigned machine (e.g., `Washer 04`).
   * Load the garments, add detergent/softener, close the door, and start the physical machine.
   * On the Queue Board card, click **Start Wash** (or **Start Dry**).
   * Status transitions from `Waiting` to `Processing`. The synchronized 39m or 40m countdown timer begins.
4. **To Complete a Cycle**:
   * When the timer reaches `00:00`, unload the drum immediately.
   * Transport garments to the folding table; fold, pack, and attach the order tag.
   * On the Queue Board card, click **Complete Cycle**.
   * Status transitions to `Done`. An automated SMS notifies the resident that their laundry is ready for pickup.
   * The 10-minute retrieval grace period begins.
5. **To Release Garments to Customer**:
   * When the customer arrives, verify their ticket number or order code.
   * Hand over the clean, bagged laundry.
   * Click **Release Garments**. The ticket is archived, and the machine returns to `Available`.

---

### 2.6 How to Operate Machine Timers & Maintenance Mode

![Figure 9: Machine Fleet Status & Cycle Timers](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig25_staff_fleet.jpg)

#### Step-by-Step Procedure:
1. Click the **Machine Fleet** tab (`#view-machines`).
2. View all 19 machines (Washers 01–14, Dryers 01–05).
3. **Manual Cycle Start (Walk-In Self-Service)**:
   * Click **Start Cycle** on the target machine card.
   * Select cycle duration (`39 mins Wash` or `40 mins Dry`).
   * The unit locks and begins counting down.
4. **Toggle Maintenance Mode**:
   * If a machine requires drum cleaning, filter clearing, or servicing, click **Toggle Maintenance**.
   * The machine is immediately marked offline (red badge), preventing the booking wizard and recommendation engine from assigning jobs to it.
   * Once servicing is complete, click **Toggle Maintenance** again to return it to `Available`.

---

### 2.7 How to Handle Late Garment Retrieval Penalties

1. When a cycle is completed, the system begins a **10-minute grace period**.
2. If the customer does not retrieve their laundry within 10 minutes:
   * The Queue Board displays an amber alert: `Grace Period Expired — Penalty Applicable`.
3. When the customer arrives to collect their laundry:
   * The terminal displays the standard **₱100.00 Late Multa** surcharge.
   * Explain the policy to the customer and collect the ₱100 penalty fee.
   * Record the penalty collection in the drawer and click **Release Garments**.

---

## 3. Manager Supervisory Guide & Step-by-Step Instructions

The Manager Console provides oversight of store operations, demand forecasting, financial drawer reconciliation, and security audit logs.

---

### 3.1 Supervisory Console Overview
* **Sign In**: Navigate to `/login` with your pre-registered Manager Google account. You will automatically land on `/manager/dashboard`.
* **Supervisory Features**:
  * Inherits all Staff floor operations tabs.
  * Unlocks the **Machine Learning Demand Forecast** engine.
  * Unlocks the **Sales Ledger & Tally** tab.
  * Unlocks the **Audit Trail & Prediction Logs** tab.

---

### 3.2 How to Interpret Machine Learning Peak Hour Demand Forecasts

1. On the **Dashboard** overview tab (`#view-dashboard`), locate the **Predictive Operations & Rush Forecast** card.
2. Review the core metrics:
   * **Predicted Peak Rush**: Identifies projected high-volume hours (e.g., *Peak Rush Expected: 3:00 PM – 6:00 PM with 18+ incoming loads*).
   * **MAPE Accuracy Score**: Displays model accuracy (e.g., `MAPE: 8.4%`, indicating high statistical reliability).
   * **Staffing Recommendation**: Advises whether to deploy an additional floor operator or clear folding tables in advance.
3. Use this forecast during morning briefings to schedule shift handovers and plan machine availability.

---

### 3.3 How to Allocate Habitual VIP "Ghost Slots"

1. In the **Dashboard** tab, locate the **Habitual Ghost Slots Matrix** card.
2. The engine identifies residents who regularly wash on specific days/times (3+ previous visits).
3. Review the identified habitual customer slots for the day.
4. When a regular resident contacts the shop, click **Assign Ghost Slot** next to their profile.
5. The system pre-reserves their preferred machine and turnaround tier, ensuring fast service without double-booking walk-in clients.

---

### 3.4 How to Reconcile the Daily Sales Ledger, Tally Cash & Export CSV

![Figure 10: Sales Ledger, Cash Tally & Revenue Reconciliation](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig27_manager_sales.jpg)

#### Step-by-Step Procedure:
1. Click the **Sales & Tally** tab (`#view-sales`).
2. **Select Date Filter**: Click `Today`, `Yesterday`, `Last 7 Days`, `This Month`, or specify a custom date range.
3. **Reconcile Financial Cards**:
   * **Gross Revenue**: Total collected sales.
   * **Cash Drawer Tally**: Verify that physical cash in the counter register matches this figure.
   * **Digital PayMongo Tally**: Confirms funds deposited via GCash, Maya, and cards.
   * **Pending Receivables**: Review orders currently in progress that have not yet been settled.
4. **Audit Transactions**: Review individual records in the transaction table (Order Code, Customer, Weight, Machine ID, Amount, Payment Method).
5. **Export Financial Records**:
   * Click the **Export CSV** button in the top right corner.
   * The system downloads a complete `.csv` spreadsheet (`/sales/export`) for store accounting, Excel reconciliation, or tax filings.

---

### 3.5 How to Review the Chronological Security Audit Trail

![Figure 11: Operational Security Audit Trail & ML Logs](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig26_manager_audit.jpg)

#### Step-by-Step Procedure:
1. Click the **Audit Trail** tab (`#view-audit`).
2. Review chronological system activity:
   * User sign-ins and session role switches.
   * Order counter check-ins and manual price overrides.
   * Machine maintenance toggles.
   * Appointment cancellations and OTP submissions.
   * Account provisioning and role adjustments.
3. Check the **Actor**, **Action**, **IP Address**, and **Timestamp** columns to investigate operational discrepancies.
4. Scroll to the **Prediction Logs** section to review historical forecast accuracy against actual customer traffic.

---

## 4. Super Admin Administration Guide & Step-by-Step Instructions

The Super Admin possesses executive control over store policies, pricing structures, hardware settings, and employee system access.

---

### 4.1 How to Use the Dynamic Role Perspective Switcher

![Figure 12: Dynamic Role Perspective Switcher](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig28_superadmin_switch_role.jpg)

#### Step-by-Step Procedure:
1. Click the user profile button in the top-right header (marked with a gold star `★ Super Admin`).
2. The **Switch View Mode** dropdown opens, displaying all four system perspectives:
   * 👑 **Super Admin**: Master governance, audit trail, user provisioning, and tariffs.
   * 👔 **Manager**: Operations overview, sales ledger, ML forecasts, and ghost slots.
   * 🛠️ **Staff**: Counter verification terminal, live queue board, and machine controls.
   * 👤 **Customer Portal**: End-user booking wizard, live orders, and fleet lobby.
3. Click your target perspective.
4. The workspace re-renders immediately under that role's interface rules without requiring you to log out.
5. To return to administrative mode, open the dropdown and select **Super Admin**.

---

### 4.2 How to Pre-Register Staff & Manager Accounts for Google SSO

![Figure 13: Staff Google SSO Account Provisioning & Role Management](file:///c:/Users/genes/bon-laundry/docs/screenshots/fig29_superadmin_account_mgmt.jpg)

#### Step-by-Step Procedure:
1. Click the **System Settings** tab (`#view-settings` or `switchTab('settings')`).
2. Scroll to the **Account Provisioning & Staff Onboarding** card.
3. Fill in the employee onboarding fields:
   * **Full Name**: e.g., `Maria Santos`.
   * **Gmail Address**: e.g., `maria.santos@gmail.com` (must be their official Google account).
   * **Assigned Role**: Select `Staff` (or `Manager`).
4. Click **Pre-Register Account**.
5. Inform the employee to open `/login` on their workstation and click **Continue with Google**.
6. The system links their Google identity and routes them directly to their assigned operational workspace.

---

### 4.3 How to Promote, Demote, or Reassign User Roles

1. In the **System Settings** tab, scroll to the **Registered Users Directory** table.
2. Locate the user you wish to modify.
3. Click the **Role Selector** dropdown in their row.
4. Select the updated role: `Customer`, `Staff`, `Manager`, or `Super Admin`.
5. The permission change takes effect immediately.

> [!NOTE]
> Only a Super Admin can promote a user to the Super Admin role or modify existing Super Admin accounts.

---

### 4.4 How to Configure Store Tariffs, Grace Periods & Late Multa Penalties

1. In the **System Settings** tab, locate the **Store Operating Rules & Pricing Parameters** card.
2. Update the master store values:
   * **Base Price per Kilogram**: e.g., `₱65.00` per kg.
   * **Maximum Weight Limit per Regular Load**: e.g., `8.0 kg`.
   * **Standard Washer Cycle Duration**: e.g., `39 minutes`.
   * **Standard Dryer Cycle Duration**: e.g., `40 minutes`.
   * **Late Retrieval Grace Period**: e.g., `10 minutes`.
   * **Late Retrieval Penalty Surcharge (Multa)**: e.g., `₱100.00`.
3. Click **Save Settings**. The updated rules apply immediately across the booking wizard, verification terminal, and queue timers.

---

### 4.5 How to Configure the Machine Hardware Fleet Matrix

1. In the **System Settings** tab, locate the **Machine Hardware Matrix** table.
2. For each of the 19 fleet machines (Washers 01–14, Dryers 01–05), you can customize:
   * **Machine Name**: e.g., `Titan Dryer 01`.
   * **Capacity (kg)**: e.g., `8 kg` for Washers, `13 kg` for Dryers.
   * **Per-Cycle Fee (₱)**: e.g., `₱145.00`.
   * **Operational Status**: Toggle between `Available` and `Maintenance`.
3. Click **Save Hardware Configuration**. Updated cycle fees reflect immediately across counter POS calculations and customer online bookings.

---

## 5. Role Navigation & Route Reference Table

| Workspace / Module | Permitted Roles | Direct URL / Selector | Primary Purpose |
| :--- | :---: | :---: | :--- |
| **Public Landing Page** | Public | `/` | Store amenities, machine preview, community info, and chatbot. |
| **Google Sign-In** | Public | `/login` | Secure OAuth 2.0 authentication entry point. |
| **Customer Portal** | Customer | `/customer/dashboard` | Central customer portal for bookings, live orders, rates, and lobby. |
| **Online Booking Wizard** | Customer | `/book` | 4-step self-service appointment booking wizard. |
| **Live Machine Lobby** | Customer | `#tab-content-lobby` | Telemetry grid showing real-time status of all 19 machines. |
| **Staff Dashboard** | Staff, Mgr, Admin | `/staff/dashboard` | Real-time queue counters, ready units, and recent jobs feed. |
| **Order Verification Terminal** | Staff, Mgr, Admin | `/staff/verify-order` | Counter check-in: digital scale weight entry, liability, and machine dispatch. |
| **Online Appointments Queue** | Staff, Mgr, Admin | `#view-appointment` | Scheduled bookings and condo doorstep pickup management. |
| **Live Queue Order Board** | Staff, Mgr, Admin | `#view-queue` | Cycle progression board: Start Wash/Dry, Complete Cycle, Release Garments. |
| **Machine Fleet Control** | Staff, Mgr, Admin | `#view-machines` | Individual countdown timers, walk-in cycle start, and maintenance toggles. |
| **Manager Dashboard** | Manager, Admin | `/manager/dashboard` | Supervisory console with ML rush forecasts and ghost slot optimization. |
| **Sales Ledger & Tally** | Manager, Admin | `#view-sales` | Financial reconciliation: Cash drawer, PayMongo digital sales, CSV export. |
| **CSV Sales Data Export** | Manager, Admin | `/sales/export` | One-click spreadsheet download of all store transactions. |
| **Audit Trail & Prediction Logs**| Manager, Admin | `#view-audit` | Chronological security activity log and ML model validation records. |
| **Role Perspective Switcher** | Super Admin | Top Bar Dropdown | Dynamic switching between Admin, Manager, Staff, and Customer viewports. |
| **User Account Provisioning** | Super Admin | `#view-settings` | Pre-registering Staff/Manager Gmail accounts and reassigning roles. |
| **Master Tariffs & Rules** | Super Admin | `#view-settings` | Master pricing per kg, cycle durations, grace periods, and late penalty fees. |
| **Hardware Fleet Matrix** | Super Admin | `#view-settings` | Per-machine capacity (8kg/13kg) and cycle tariff configurations. |

---

*Bon Laundry Station User Guide & Standard Operating Procedures — Document End*
