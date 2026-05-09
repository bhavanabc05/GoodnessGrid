# 🌟 Goodness Grid — A Network of Good Deeds

A full-stack community donation management platform that connects **Donors**, **NGOs/Receivers**, **Volunteers**, and **Admins** to streamline the donation lifecycle — from posting to delivery.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Database Schema](#database-schema)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Role-Based Access](#role-based-access)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)

---

## Overview

Goodness Grid is a web application that bridges the gap between surplus and need. Donors list items they want to give away, NGOs browse and claim them, volunteers handle pickup and delivery, and admins oversee the entire platform.

---

## Features

### 🔐 Authentication & Security
- Role-based registration: Donor, NGO/Receiver, Volunteer, Admin
- Email verification via tokenized links (itsdangerous)
- Password hashing with Werkzeug
- Flask session management

### 🎁 Donor Features
- Post donations with image upload (food, clothes, books, medicine, electronics, etc.)
- Track donation status: Available → Claimed → Completed
- Gamification: Donor levels, badges, and monthly streak tracking
- View feedback and star ratings from receivers

### 🏥 NGO / Receiver Features
- Browse and claim available donations
- Smart donation matching based on NGO type (food NGO sees food donations first)
- Self-pickup option if no volunteer is assigned within 24 hours
- Submit star ratings and feedback for completed donations

### 🚚 Volunteer Features
- View and accept pending pickup tasks
- Mark deliveries as completed
- Track active and completed task history

### 🛠️ Admin Features
- User management with NGO verification
- Platform analytics with Chart.js (donation trends, type distribution, completion rates, user growth)
- Export data to CSV: Users, Donations, Transactions, Summary Report
- Database consistency check and auto-fix tool

### 📧 Email Notifications
- Email verification on registration
- Notification when a donation is claimed
- Pickup assignment notification for volunteers
- Delivery completion notification for both donor and NGO

---

## Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Backend      | Python, Flask 2.3                   |
| Database     | MySQL with mysql-connector-python   |
| Frontend     | Jinja2 Templates, Bootstrap 5.3, Bootstrap Icons |
| Auth         | Werkzeug (password hashing), itsdangerous (tokens) |
| Email        | Flask-Mail (Gmail SMTP)             |
| File Upload  | Werkzeug secure_filename            |
| Charts       | Chart.js 4.4                        |
| Deployment   | Gunicorn (Procfile for cloud deploy)|
| Config       | python-dotenv (.env)                |

---

## System Architecture

```
Client (Browser)
      │
      ▼
Flask App (app.py)
      │
  ┌───┴───────────────────┐
  │   Routes & Views       │
  │   (Role-based access)  │
  └───┬───────────────────┘
      │
  ┌───┴──────────────────┐
  │  database.py          │
  │  (All DB operations)  │
  └───┬──────────────────┘
      │
  ┌───┴──────────────────┐
  │     MySQL Database    │
  │  Users, Donations,    │
  │  Transactions,        │
  │  Feedback             │
  └──────────────────────┘
```

---

## Database Schema

### Users
```sql
user_id, name, email, password, phone, address, role,
donor_type, ngo_type, availability, vehicle_details,
verified, email_verified, created_at
```

### Donations
```sql
donation_id, donor_id, type, description, quantity,
pickup_address, pickup_time, expiry_date, status,
image_path, created_at
```

### Transactions
```sql
transaction_id, donation_id, ngo_id, volunteer_id,
status, self_pickup_allowed, created_at, completed_at
```

### Feedback
```sql
feedback_id, donation_id, donor_id, receiver_id,
rating, comments, created_at
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- Gmail account (for email notifications)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/bhavanabc05/goodnessgrid.git
cd goodnessgrid

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up the database
# Create a MySQL database named 'goodnessgrid'
# Run the SQL schema file to create all tables

# 5. Configure environment variables (see below)
cp .env.example .env
# Fill in your values

# 6. Run the application
python app.py
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=goodnessgrid

FLASK_SECRET_KEY=your_secret_key_here

MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com

BASE_URL=http://127.0.0.1:5000
```

> **Note:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

---

## Running the Application

```bash
# Development
python app.py

# Production (with Gunicorn)
gunicorn app:app
```

Visit `http://127.0.0.1:5000` in your browser.

---

## Project Structure

```
goodnessgrid/
│
├── app.py                  # Main Flask application, all routes
├── database.py             # All MySQL database helper functions
├── config.py               # Configuration loaded from .env
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn deployment config
├── .gitignore
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── uploads/
│       └── donations/      # Uploaded donation images
│
└── templates/
    ├── base.html           # Base layout with navbar & footer
    ├── home.html
    ├── login.html
    ├── register.html
    ├── dashboard.html      # Role-specific dashboard
    ├── post_donation.html
    ├── view_donations.html
    ├── my_donations.html
    ├── my_claims.html
    ├── volunteer_pickups.html
    ├── profile.html
    ├── edit_profile.html
    ├── change_password.html
    ├── admin_users.html
    ├── admin_transactions.html
    ├── admin_analytics.html
    ├── admin_sync_check.html
    ├── about.html
    ├── 404.html
    └── 500.html
```

---

## Role-Based Access

| Feature                     | Donor | NGO/Receiver | Volunteer | Admin |
|-----------------------------|-------|--------------|-----------|-------|
| Post Donations              | ✅    | ❌           | ❌        | ❌    |
| Browse Donations            | ✅    | ✅           | ✅        | ✅    |
| Claim Donations             | ❌    | ✅           | ❌        | ❌    |
| Accept Pickup Tasks         | ❌    | ❌           | ✅        | ❌    |
| Mark Delivery Complete      | ❌    | ❌           | ✅        | ❌    |
| Give Feedback               | ❌    | ✅           | ❌        | ❌    |
| View Analytics              | ❌    | ❌           | ❌        | ✅    |
| Manage Users                | ❌    | ❌           | ❌        | ✅    |
| Export CSV Reports          | ❌    | ❌           | ❌        | ✅    |
| Self Pickup (24hr timeout)  | ❌    | ✅           | ❌        | ❌    |

---

## Future Improvements

- [ ] Real-time notifications using WebSockets
- [ ] Google Maps integration for pickup route optimization
- [ ] Mobile app (React Native / Flutter)
- [ ] SMS notifications via Twilio/Textbee
- [ ] AI-based donation-to-NGO matching
- [ ] Multi-language support
- [ ] Docker containerization

---

## License

This project is built for academic and community purposes.

---

*Made with ❤️ by Team Goodness Grid*
