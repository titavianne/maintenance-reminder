# 🔧 Maintenance Reminder Automation System

An automated maintenance reminder system built with Python that reads customer data from Google Sheets, calculates 6-month maintenance schedules, and sends email notifications via SendGrid.

## Overview

This system ensures that every customer in the dataset receives a timely maintenance reminder based on their scheduled date. It runs daily via Windows Task Scheduler, checks which customers are due for maintenance **today**, and sends a professional email notification to the administrator — enabling proactive customer outreach.

## Features

- **Google Sheets Integration** — Reads customer data live from a shared Google Sheet, so updates are instant without redeploying code.
- **6-Month Cycle Calculation** — Uses calendar-based date arithmetic (not fixed day counts) to accurately compute recurring maintenance dates.
- **Automated Email Delivery** — Sends professional HTML-formatted reminder emails through SendGrid's API.
- **Duplicate Prevention** — Logs every sent reminder to `sent_log.csv`, ensuring no customer receives the same reminder twice.
- **Data Validation** — Skips and logs invalid or incomplete entries without crashing the system.
- **Comprehensive Logging** — Records all activity to both CSV (for tracking) and a log file (for debugging).
- **Idempotent & Deterministic** — Safe to run multiple times per day; produces consistent results.
- **Daily Scheduling** — Configured via Windows Task Scheduler for fully hands-off operation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   WINDOWS TASK SCHEDULER                    │
│                  (Trigger: Daily at 03:00)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ Executes
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     run_reminder.bat                        │
│              (Activates venv + runs script)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │ Launches
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       reminder.py                           │
│                                                             │
│  1. Validate config (.env)                                  │
│  2. Read customer data (Google Sheets API)                  │
│  3. For each customer:                                      │
│     ├─ Parse & validate start_date                          │
│     ├─ Calculate next maintenance (start_date + 6mo cycle)  │
│     ├─ Check: is next_maintenance == today?                 │
│     ├─ Check: already sent? (sent_log.csv)                  │
│     └─ If due & not sent → Send email via SendGrid          │
│  4. Log results                                             │
│  5. Print summary                                           │
└──────┬──────────────────────┬───────────────────┬───────────┘
       │                      │                   │
       ▼                      ▼                   ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
│ Google Sheets│   │    SendGrid API  │   │  logs/       │
│     API      │   │                  │   │              │
│              │   │  Sends HTML      │   │ sent_log.csv │
│ Reads data   │   │  email to admin  │   │ reminder.log │
│ via service  │   │  inbox           │   │              │
│ account      │   │                  │   │              │
└──────────────┘   └──────────────────┘   └──────────────┘
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.12 | Core automation logic |
| Data Source | Google Sheets API | Live customer database |
| Email Service | SendGrid API | Reliable email delivery |
| Auth | Google Service Account | Secure API authentication |
| Scheduler | Windows Task Scheduler | Daily automated execution |
| Config | python-dotenv | Environment variable management |
| Date Math | python-dateutil | Accurate 6-month calculations |

## Project Structure

```
maintenance-reminder/
├── reminder.py            # Main automation script
├── run_reminder.bat       # Windows batch file for Task Scheduler
├── test_connection.py     # Google Sheets connection test
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not tracked)
├── .env.example           # Template for .env setup
├── credentials.json       # Google service account key (not tracked)
├── .gitignore             # Git ignore rules
└── logs/
    ├── sent_log.csv       # Email delivery tracking log
    └── reminder.log       # Detailed execution log
```

## Prerequisites

- Python 3.9+
- Google Cloud Platform account (with Sheets & Drive API enabled)
- SendGrid account (free tier: 100 emails/day)
- Windows OS (for Task Scheduler)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/maintenance-reminder.git
cd maintenance-reminder
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Google Sheets API

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Google Sheets API** and **Google Drive API**
3. Create a **Service Account** and download the JSON key
4. Rename the key to `credentials.json` and place it in the project root
5. Share your Google Sheet with the service account email (Viewer access)

### 5. Configure SendGrid

1. Create a free account at [sendgrid.com](https://sendgrid.com)
2. Complete **Single Sender Verification**
3. Generate an **API Key** with Mail Send permissions

### 6. Set Up Environment Variables

Copy the example file and fill in your values:

```bash
copy .env.example .env
```

```env
SENDGRID_API_KEY=SG.your_api_key_here
SENDER_EMAIL=your_verified_sender@email.com
RECIPIENT_EMAIL=your_inbox@email.com
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_CREDS_FILE=credentials.json
SHEET_TAB_NAME=Sheet1
```

### 7. Prepare Google Sheet

Create a Google Sheet with the following columns in Row 1:

| Column A | Column B | Column C |
|----------|----------|----------|
| name | email | start_date |

- `name` — Customer identifier (e.g., "134107 BYD Atto 1")
- `email` — Customer email address
- `start_date` — Maintenance schedule date in `YYYY-MM-DD` format

## Usage

### Manual Run

```bash
python reminder.py
```

### Test Google Sheets Connection

```bash
python test_connection.py
```

### Automated Daily Execution (Windows)

Double-click `run_reminder.bat` or configure Windows Task Scheduler:

1. Open **Task Scheduler** → **Create Basic Task**
2. Set trigger: **Daily** at your preferred time
3. Set action: **Start a program** → select `run_reminder.bat`
4. In task Properties → Settings: enable **"Run task as soon as possible after a scheduled start is missed"**

## How the Date Calculation Works

The system uses a rolling 6-month cycle from each customer's `start_date`:

```
start_date: 2026-06-03

Reminder schedule:
  → 2026-06-03  (first reminder)
  → 2026-12-03  (6 months later)
  → 2027-06-03  (12 months later)
  → ...          (continues indefinitely)
```

On each daily run, the script checks: **"Does any customer's next maintenance date fall on today?"** If yes, it sends the reminder. If not, it does nothing.

## Sample Email Output

When a reminder is triggered, the admin receives an email like:

> **Subject:** Maintenance Reminder - 134107 BYD Atto 1 (03 June 2026)
>
> 🔧 **Maintenance Reminder**
>
> This is a reminder that the following customer is due for maintenance:
>
> **Customer:** 134107 BYD Atto 1
> **Maintenance Date:** 03 June 2026
>
> **Action needed:** Please contact the customer to schedule their maintenance appointment.

## Logging

All activity is recorded in the `logs/` directory:

- **`sent_log.csv`** — Tracks every email: timestamp, customer, date, status (sent/failed/skipped)
- **`reminder.log`** — Detailed execution log with timestamps for debugging

## License

This project is for personal/small-business use.

---

Built with Python • Google Sheets API • SendGrid
