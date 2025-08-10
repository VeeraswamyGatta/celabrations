from .db import get_connection

def get_notification_emails():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT email FROM notification_emails")
        emails = [row[0] for row in cursor.fetchall()]
    conn.close()
    return emails
