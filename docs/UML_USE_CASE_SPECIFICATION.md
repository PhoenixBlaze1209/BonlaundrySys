# UML 2.5 Use Case Diagram Specification — Bon Laundry Station

## 1. Executive Summary & Overview
This document specifies the official **UML 2.5 Use Case Diagram** for the **Bon Laundry Station Management System with Predictive Analytics** (Urban Deca Homes Ortigas). 

In accordance with current operational requirements and architectural decisions:
* **Telegram Bot Excluded**: All legacy bot-driven interactions have been removed from the system boundary. Real-time notifications and operations rely on the responsive customer portal, optical QR codes, counter check-ins, and direct SMS cycle alerts (PhilSMS).
* **Four Dedicated Human Actors**: The system distinguishes between **Customer (Resident)**, **Staff (Cashier & Floor Operator)**, **Manager (Store Supervisor)**, and **Super Admin (Business Owner)**.
* **Hierarchical Role Generalization**: 
  $$\text{Super Admin} \xrightarrow{\text{inherits}} \text{Manager} \xrightarrow{\text{inherits}} \text{Staff}$$
  This reflects that higher-tier managerial and executive roles retain full operational permissions over floor activities, queue management, and POS intake.

---

## 2. Actors Definition & Permissions Hierarchy

| Actor | Category | Description & Operational Scope |
| :--- | :--- | :--- |
| **Customer** | Primary (Human) | Residential clients residing in Urban Deca Homes Ortigas. Interacts with the public web portal without mandatory account registration (guest model). Initiates booking appointments, inspects real-time fleet telemetry, tracks multi-step milestones, and processes payments. |
| **Staff** | Primary (Human) | Counter cashiers and floor laundry operators. Authenticates via Google SSO or internal credentials. Manages physical garment intake, QR code validation, walk-in POS job orders, queue progression, machine timer cycles, and final order release. |
| **Manager** | Secondary / Supervisor (Human) | Store supervisor in charge of operational oversight. **Inherits all Staff privileges**. Monitors sales history and reconciles daily drawer tallies, audits chronological staff actions, inspects machine learning peak-demand forecasts, and manages habitual predictive time slots. |
| **Super Admin** | Secondary / Executive (Human) | Business owner and top-level administrator. **Inherits all Manager and Staff privileges**. Controls business settings, pricing tariffs, service add-on fees, pre-registers Google SSO staff accounts, and utilizes the dynamic role perspective switcher. |

---

## 3. Use Case Inventory by Subsystem

### 3.1 Customer Subsystem (Self-Service Portal)
1. **Book Laundry Service / Online Appointment**:
   * Enables residents to select wash/dry tiers, separate loads across multiple machines (e.g. customized detergent and fabric softener per load), choose between doorstep pickup/delivery or station drop-off, and book a specific time slot.
   * `«include»` **Calculate Service Price & Queue EWT Slot**: Automatically evaluates load tariffs, delivery surcharges, and current queue load to project Estimated Waiting Time (EWT).
   * `«include»` **Pay for Order**: Forwards the generated booking total to the payment subsystem.
2. **Track Live Order & Queue**:
   * Provides real-time visibility into order status through a 4-step live milestone tracker (*Order Received* $\rightarrow$ *In Queue* $\rightarrow$ *In Progress [Washing/Drying]* $\rightarrow$ *Ready for Pickup/Delivery*).
   * Extended by `«extend»` **Request Order Cancellation**: Allows customers to submit a self-service cancellation before washing/drying operations commence.
3. **Request Order Cancellation**:
   * Self-service cancellation request triggered directly from the tracking view. Only active during *Order Received* or *In Queue* states.
4. **View Machine Fleet Lobby & Traffic Indicator**:
   * Displays live telemetry across the shop's 19 machines (14 washers and 5 dryers), showing real-time countdown timers, cycle statuses, and current traffic rush hours.

### 3.2 Payment Processing Subsystem
5. **Pay for Order** *(Abstract Base Use Case)*:
   * Serves as the generalized transaction interface invoked by online appointments and counter POS job orders.
   * Specialization (Generalization $\triangle$):
     * **Pay Online (GCash / Maya / Debit & Credit Card)**: Digital payment settlement routed via PayMongo secure hosted checkout.
     * **Pay Cash on Counter / COD**: In-person cash collection at the counter or cash-on-delivery during doorstep condo handover.

### 3.3 Staff Operations Subsystem (Floor & POS)
6. **Verify Order QR Code & Counter Check-In**:
   * Optical scanning of customer appointment QR code or order number intake in $<15$ seconds, verifying bag count and shifting order status from scheduled to arrived.
7. **Process Walk-in POS Job Order**:
   * Direct front-desk counter intake for walk-in residents without prior appointments.
   * `«include»` **Validate Garment Weight & Calculate Load Fee / Add-ons**: Computes load brackets, overweight charges, and optional detergent/softener add-ons.
   * `«include»` **Pay for Order**: Collects customer payment immediately at the POS counter.
8. **Validate Garment Weight & Calculate Load Fee / Add-ons**:
   * Included computation logic for POS pricing and laundry load validation.
9. **Manage & Intake Online Appointments**:
   * Operational dashboard queue displaying incoming condo doorstep pickup requests and scheduled station drop-offs.
10. **Manage Live Queue Order & Floor Fleet Dispatch**:
    * Queue dispatch interface allowing operators to assign specific laundry loads to available washer or dryer units.
11. **Operate Machine Cycle & Monitor Live Timers**:
    * Physical start of washer/dryer cycles and initialization of synchronized system countdown timers.
12. **Complete Laundry Order & Release for Pickup / Delivery**:
    * Final operational step marking garments as washed, dried, folded, and bagged, shifting status to *Ready for Pickup / Delivery* and notifying the resident.
13. **Update Machine Fleet Status**:
    * Manual operational toggle to flag individual machines as *Available*, *In-Use*, or *Under Maintenance*.

### 3.4 Manager Subsystem (Supervisory & Machine Learning)
14. **Access Store Operations Dashboard & ML Rush Forecast**:
    * High-level operational telemetry paired with Machine Learning store rush predictions generated via **2nd-Degree Polynomial Regression** and validated using Mean Absolute Percentage Error (**MAPE**).
15. **Manage Habitual Predictive Slots**:
    * Analyzes resident recurring laundry patterns to identify habitual booking routines and generate recommended priority slots.
16. **Monitor Sales History & Daily Tally**:
    * End-of-day cash drawer reconciliation, breakdown between counter cash and digital transactions, and CSV export for financial records.
17. **Monitor Operational Audit Trail**:
    * Chronological audit log tracking operator timestamps, queue re-orderings, manual machine overrides, and status transitions.

### 3.5 Super Admin Subsystem (Business Owner & System Admin)
18. **Switch View Mode Perspective**:
    * Dynamic role switcher allowing immediate viewport transitions between *Super Admin*, *Manager*, *Staff*, and *Customer* without repeated authentication, facilitating system inspection and floor quality assurance.
19. **Manage Staff & User Accounts**:
    * Pre-registers authorized staff emails for Google Single Sign-On (SSO), provisions and reassigns user roles (*Staff*, *Manager*, *Super Admin*), and deactivates inactive personnel.
20. **Configure Pricing, Tariffs & Fleet Settings**:
    * Master configuration panel for wash/dry cycle tariffs, detergent and fabric softener pricing, condo delivery surcharges, and fleet hardware specifications.

---

## 4. Diagram Artifacts

* **High-Resolution PNG Image**: [use_case_diagram.png](file:///c:/Users/genes/bon-laundry/docs/diagrams/use_case_diagram.png)
* **Editable Draw.io Source**: [use_case_diagram.drawio](file:///c:/Users/genes/bon-laundry/docs/diagrams/use_case_diagram.drawio)
* **Interactive SVG/HTML Canvas**: [diagram.html](file:///c:/Users/genes/bon-laundry/scratch/diagram.html)
