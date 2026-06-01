"""
Maintenance Reminder System
============================
Reads customer data from Google Sheets, calculates 6-month maintenance
schedules, sends email reminders via SendGrid, and logs all activity.

Run daily via Windows Task Scheduler.
"""

import os
import csv
import logging
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from dateutil.relativedelta import relativedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL     = os.getenv("SENDER_EMAIL")
RECIPIENT_EMAIL  = os.getenv("RECIPIENT_EMAIL")
GOOGLE_SHEET_ID  = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDS     = os.getenv("GOOGLE_CREDS_FILE", "credentials.json")
SHEET_TAB_NAME   = os.getenv("SHEET_TAB_NAME", "Sheet1")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

# Paths
BASE_DIR  = Path(__file__).resolve().parent
LOG_DIR   = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
SENT_LOG  = LOG_DIR / "sent_log.csv"

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "reminder.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def validate_config():
    """Make sure all required environment variables are set."""
    missing = []
    if not SENDGRID_API_KEY:
        missing.append("SENDGRID_API_KEY")
    if not SENDER_EMAIL:
        missing.append("SENDER_EMAIL")
    if not RECIPIENT_EMAIL:
        missing.append("RECIPIENT_EMAIL")
    if not GOOGLE_SHEET_ID:
        missing.append("GOOGLE_SHEET_ID")
    if missing:
        logger.error("Missing environment variables: %s", ", ".join(missing))
        logger.error("Please check your .env file.")
        return False
    if not Path(GOOGLE_CREDS).exists():
        logger.error("Credentials file not found: %s", GOOGLE_CREDS)
        return False
    return True


def read_google_sheet():
    """Fetch all rows from the Google Sheet and return as list of dicts."""
    creds  = Credentials.from_service_account_file(GOOGLE_CREDS, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(GOOGLE_SHEET_ID).worksheet(SHEET_TAB_NAME)
    return sheet.get_all_records()


def parse_date(date_string):
    """
    Parse a date string in YYYY-MM-DD format.
    Returns a date object or None if invalid.
    """
    if not date_string or str(date_string).strip() == "":
        return None
    try:
        return datetime.strptime(str(date_string).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def calculate_next_maintenance(start_date, today=None):
    """
    Starting from start_date, keep adding 6 months until we reach a date
    that is >= today. Returns that next maintenance date.
    """
    if today is None:
        today = date.today()

    next_date = start_date
    while next_date < today:
        next_date += relativedelta(months=6)

    return next_date


def was_already_sent(customer_name, scheduled_date):
    """
    Check the sent_log.csv to see if we already sent a reminder
    for this customer on this scheduled date. Prevents duplicates.
    """
    if not SENT_LOG.exists():
        return False

    target_name = str(customer_name).strip()
    target_date = str(scheduled_date)

    with open(SENT_LOG, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("customer_name", "").strip() == target_name
                    and row.get("scheduled_date") == target_date
                    and row.get("status") == "sent"):
                return True
    return False


def log_sent(customer_name, email, scheduled_date, status):
    """Append a record to sent_log.csv."""
    file_exists = SENT_LOG.exists()

    with open(SENT_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "customer_name", "email", "scheduled_date", "status",
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer_name":  customer_name,
            "email":          email,
            "scheduled_date": str(scheduled_date),
            "status":         status,
        })


def build_email_body(customer_name, maintenance_date):
    """Build a professional HTML email body."""
    display_name = customer_name if customer_name else "Customer"
    formatted_date = maintenance_date.strftime("%d %B %Y")

    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">🔧 Maintenance Reminder</h2>
        <p>Hi,</p>
        <p>This is a reminder that the following customer is due for maintenance:</p>

        <div style="background-color: #f8f9fa; border-left: 4px solid #3498db;
                    padding: 15px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Customer:</strong> {display_name}</p>
            <p style="margin: 5px 0;"><strong>Maintenance Date:</strong> {formatted_date}</p>
        </div>

        <p><strong>Action needed:</strong> Please contact the customer to schedule
        their maintenance appointment.</p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">
            This is an automated reminder from your Maintenance Reminder System.
        </p>
    </div>
    """


def send_email(customer_name, maintenance_date):
    """Send a maintenance reminder email via SendGrid."""
    display_name = customer_name if customer_name else "Customer"
    formatted_date = maintenance_date.strftime("%d %B %Y")

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=RECIPIENT_EMAIL,
        subject=f"Maintenance Reminder - {display_name} ({formatted_date})",
        html_content=build_email_body(customer_name, maintenance_date),
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            logger.info("  ✅ Email sent successfully (status %s)", response.status_code)
            return True
        else:
            logger.warning("  ⚠️  Email returned status %s", response.status_code)
            return False

    except Exception as e:
        logger.error("  ❌ Failed to send email: %s", e)
        return False


# ---------------------------------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------------------------------

def run():
    """Main entry point — run once per day."""
    logger.info("=" * 60)
    logger.info("Maintenance Reminder System — Starting")
    logger.info("=" * 60)

    # Step 1: Validate configuration
    if not validate_config():
        return

    today = date.today()
    logger.info("Today's date: %s", today)

    # Step 2: Read data from Google Sheets
    try:
        data = read_google_sheet()
        logger.info("Loaded %d customers from Google Sheets", len(data))
    except Exception as e:
        logger.error("Failed to read Google Sheet: %s", e)
        return

    # Step 3: Process each customer
    reminders_sent = 0
    skipped        = 0
    errors         = 0
    not_due        = 0

    for i, row in enumerate(data, 1):
        customer_name = str(row.get("name", "")).strip()
        email         = str(row.get("email", "")).strip()
        start_date_str = str(row.get("start_date", "")).strip()

        # Validate required fields
        if not email:
            logger.warning("Row %d: Missing email — skipped", i)
            log_sent(customer_name, "", "", "skipped_no_email")
            skipped += 1
            continue

        if not start_date_str:
            logger.warning("Row %d (%s): Missing start date — skipped", i, customer_name)
            log_sent(customer_name, email, "", "skipped_no_date")
            skipped += 1
            continue

        # Parse the date
        start_date = parse_date(start_date_str)
        if start_date is None:
            logger.warning("Row %d (%s): Invalid date '%s' — skipped",
                           i, customer_name, start_date_str)
            log_sent(customer_name, email, start_date_str, "skipped_invalid_date")
            skipped += 1
            continue

        # Calculate next maintenance date
        next_maintenance = calculate_next_maintenance(start_date, today)

        # Check if today is the day
        if next_maintenance != today:
            not_due += 1
            continue

        # Check for duplicate sends
        if was_already_sent(customer_name, next_maintenance):
            logger.info("Row %d (%s): Already sent for %s — skipping",
                        i, customer_name, next_maintenance)
            not_due += 1
            continue

        # Send the reminder!
        logger.info("Row %d (%s): Maintenance due TODAY (%s) — sending reminder...",
                     i, customer_name, next_maintenance)

        success = send_email(customer_name, next_maintenance)

        if success:
            log_sent(customer_name, email, next_maintenance, "sent")
            reminders_sent += 1
        else:
            log_sent(customer_name, email, next_maintenance, "failed")
            errors += 1

    # Step 4: Summary
    logger.info("-" * 60)
    logger.info("SUMMARY")
    logger.info("  Total customers : %d", len(data))
    logger.info("  Reminders sent  : %d", reminders_sent)
    logger.info("  Not due today   : %d", not_due)
    logger.info("  Skipped (invalid): %d", skipped)
    logger.info("  Errors          : %d", errors)
    logger.info("=" * 60)
    logger.info("Done!\n")


if __name__ == "__main__":
    run()