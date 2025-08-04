import psycopg2
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Load secrets from environment or a config file
EMAIL_SENDER = os.environ.get('EMAIL_SENDER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
SMTP_SERVER = os.environ.get('SMTP_SERVER')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))

DB_CONFIG = {
    'host': os.environ.get('POSTGRES_HOST'),
    'port': os.environ.get('POSTGRES_PORT'),
    'dbname': os.environ.get('POSTGRES_DBNAME'),
    'user': os.environ.get('POSTGRES_USER'),
    'password': os.environ.get('POSTGRES_PASSWORD'),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_notification_emails(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT email FROM notification_emails")
        return [row[0] for row in cursor.fetchall()]

def send_email(subject, body, recipients):
    for recipient in recipients:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
        except Exception as e:
            print(f"Failed to send email to {recipient}: {e}")

def report_sponsored_records(conn, recipients):
    df = pd.read_sql("SELECT name, email, mobile, apartment, sponsorship, donation FROM sponsors ORDER BY id", conn)
    html = """
    <b>Daily Sponsored Records Report - {date}</b><br><br>
    <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
      <tr><th>Name</th><th>Email</th><th>Mobile</th><th>Apartment</th><th>Sponsorship</th><th>Donation</th></tr>
    """.format(date=datetime.date.today())
    for _, row in df.iterrows():
        html += f"<tr><td>{row['name']}</td><td>{row['email']}</td><td>{row['mobile'] or ''}</td><td>{row['apartment']}</td><td>{row['sponsorship'] or 'N/A'}</td><td>${row['donation']}</td></tr>"
    html += "</table>"
    send_email(
        "Ganesh Chaturthi Sponsorship - Daily Sponsored Records Report",
        html,
        recipients
    )

def report_available_items(conn, recipients):
    with conn.cursor() as cursor:
        cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items ORDER BY id")
        items = cursor.fetchall()
        cursor.execute("SELECT sponsorship, COUNT(*) FROM sponsors GROUP BY sponsorship")
        counts = dict(cursor.fetchall())
    html = """
    <b>Daily Available Sponsorship Items Report - {date}</b><br><br>
    <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
      <tr><th>Item</th><th>Amount</th><th>Total Slots</th><th>Remaining Slots</th></tr>
    """.format(date=datetime.date.today())
    for item, amount, limit in items:
        count = counts.get(item, 0)
        remaining = limit - count
        html += f"<tr><td>{item}</td><td>${amount}</td><td>{limit}</td><td>{remaining}</td></tr>"
    html += "</table>"
    send_email(
        "Ganesh Chaturthi Sponsorship - Daily Available Items Report",
        html,
        recipients
    )

def main():
    today = datetime.date.today()
    # Only send reports until August 31st, 2025
    if today <= datetime.date(2025, 8, 31):
        conn = get_connection()
        recipients = get_notification_emails(conn)
        if recipients:
            report_sponsored_records(conn, recipients)
            report_available_items(conn, recipients)
        conn.close()
    else:
        print("Daily reports are only sent until August 31st, 2025.")

if __name__ == "__main__":
    main()
