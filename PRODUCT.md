# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Customers**: Walk-in and online clients booking laundry appointments, tracking order progress in real-time, checking machine availability, and viewing history.
- **Staff**: Front-desk operators processing laundry intake, weighing loads, assigning machines, handling queue transitions, and recording payments.
- **Managers / Owners**: Business administrators monitoring operational KPIs, revenue forecasts, machine fleet telemetry/maintenance, pricing, and turnaround metrics.

## Product Purpose
Bon Laundry Station provides an end-to-end commercial laundromat operating system and customer portal. It streamlines front-counter laundry drop-offs, online bookings, live queue management, fleet tracking for 19 machines (14 washers, 5 dryers), and analytics-driven business oversight.

## Positioning
An integrated, real-time laundromat ecosystem combining transparent customer self-service (live machine lobby & order tracking without friction) with granular operational POS, queue orchestrations, and predictive revenue/turnaround analytics.

## Operating Context
- Countertop POS and staff workstations in high-traffic laundry shop environments.
- Mobile and desktop customer access for online appointment bookings and remote laundry cycle tracking.
- Manager dashboard for performance auditing, forecasting, and machine health telemetry.

## Capabilities and Constraints
- **Fleet Management**: 19-machine inventory (14 Regular 8kg washers, 5 Titan 13kg dryers) with state tracking (`Available`, `In-Use`, `Maintenance`), cycle timers, and usage counts.
- **Appointment & Tracking**: Unique order tracking codes, pickup scheduling, service tier selections, and automated status notifications.
- **POS & Billing**: Weight-based pricing calculations (`price_per_kg`, default ₱65/kg), cycle flat fees, and payment status verification.
- **Queue Automation**: Live queue numbering, estimated wait-time calculation, and machine dispatching.
- **Analytics & Forecasting**: Predictive engine with MAPE tracking for demand and revenue forecasting.

## Brand Commitments
- **Name**: Bon Laundry Station
- **Tone**: Clean, reliable, approachable, trustworthy, and efficient.
- **Visual Assets**: Official logo (`/logo.webp`), aquatic/fresh ocean palette accents (azure/sky/slate).

## Evidence on Hand
- Full database schema with models for users, appointments, machine status, transactions, queues, settings, and prediction logs in `models/schemas.py`.
- Flask routes and blueprints in `routes/` (auth, dashboard, pos, appointments, machines).
- Operational analytics and queue engines in `services/`.
- Working customer landing page, customer dashboard, and manager analytics console in `templates/`.

## Product Principles
1. **Zero-Guesswork Transparency**: Customers must always know the precise status of their garments and waiting times.
2. **Frictionless Counter Intake**: Staff POS workflows must prioritize speed, accuracy in weight entry, and fast machine assignment.
3. **Operational Clarity**: Managers should receive immediate signal on fleet bottlenecks, utilization rates, and revenue trajectories.
4. **Resilient Data Integrity**: Clear audit trails across appointments, transactions, and machine state transitions.
