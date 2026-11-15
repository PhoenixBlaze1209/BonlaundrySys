# Bon Laundry Station

Bon Laundry Station is a web-based laundromat management system and customer portal for online bookings, walk-in intake, live queue and machine tracking, payments, and operational analytics. It supports Customers, Staff, Managers, and Super Administrators through role-based dashboards designed to make day-to-day laundry operations faster and more transparent.

## Group Members & Roles

**Leader:** Genesis D. Samson

**Members:**
- Erika P. Cardana
- Mary Lloyd E. Firma


- **Genesis D. Samson** – Project Manager / Lead Developer / Documentation Lead
- **Genesis D. Samson** – Frontend / UI/UX Developer
- **Genesis D. Samson** – Backend / Database Administrator

- **Erika P. Cardana** – Documentation Lead
- **Mary Lloyd E. Firma** – Documentation Assistant



## Key Features

- Online laundry booking and order tracking
- Walk-in point-of-sale and counter verification
- Live queue numbers and estimated waiting times
- Real-time status and cycle tracking for a 19-machine fleet
- Cash and PayMongo-assisted payment workflows
- Customer, Staff, Manager, and Super Admin dashboards
- Sales reports, audit logs, and demand/revenue analytics
- Optional Google Sign-In, email, and SMS notifications

## Tech Stack

- **Frontend:** HTML5, CSS3, JavaScript, and Jinja templates
- **Backend:** Python 3.11 and Flask
- **Database:** MySQL with SQLAlchemy ORM and PyMySQL
- **Analytics:** pandas and NumPy
- **Tools & version control:** Git, GitHub, VS Code, and optional n8n workflows

## System Requirements

Install the following before setting up the project:

- Git
- Python 3.11 or later
- MySQL Server or XAMPP with MySQL
- A modern web browser

Optional third-party accounts are required only when enabling Google Sign-In, PayMongo payments, Gmail notifications, or SMS delivery.

## Installation and Setup

### 1. Clone the repository

```powershell
git clone https://github.com/PhoenixBlaze1209/BonlaundrySys.git
cd BonlaundrySys
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux, use `cp .env.example .env` instead. Update `.env` with your local database credentials and any optional service credentials. Never commit real API keys or passwords.

## Database Setup

1. Start MySQL using MySQL Server or XAMPP.
2. Create the application database:

   ```sql
   CREATE DATABASE bon_laundry_db
     CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
   ```

3. Set `DATABASE_URL` in `.env`. The repository's local default uses MySQL port `3307`:

   ```env
   DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3307/bon_laundry_db
   ```

   If your MySQL server uses the standard port, change `3307` to `3306`. Add the password after `root:` when the database user has one.

4. No SQL import is required for a fresh installation. When the application starts, SQLAlchemy creates the required tables and applies the included additive schema updates automatically.

5. Optional: populate sample customer, transaction, appointment, and prediction data after the tables have been created:

   ```powershell
   python seed_analytics_data.py
   ```

   The seed script adds demonstration records and should not be run against production data.

## Running the Application

Start the Flask development server:

```powershell
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in a browser. To verify the database connection, visit [http://localhost:5000/test-db](http://localhost:5000/test-db).

The built-in server runs in debug mode and is intended for local development only.

## Authentication and Accounts

The current user interface authenticates users through Google OAuth; it does not expose a local email/password login form. New Google users are registered as Customers automatically, while Staff and Manager email addresses must be provisioned by an authorized administrator before their first sign-in.

No universal default administrator password is included. Configure the Google OAuth variables in `.env`, then use an appropriately provisioned account. The optional analytics seed script creates sample Customer records for demonstration data, but these are not administrative credentials.

For local OAuth, register this callback URL in the Google Cloud Console:

```text
http://localhost:5000/auth/google/callback
```

## Optional Integrations

The application can run locally without every integration configured, although the related features will be limited.

- **Google OAuth:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- **Gmail SMTP:** `MAIL_HOST`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_FROM`, `MAIL_APP_PASSWORD`
- **SMS:** PhilSMS or Semaphore API credentials
- **PayMongo:** public, secret, and webhook keys

