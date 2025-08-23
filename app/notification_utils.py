from .db import get_connection

def get_notification_emails():
    from app import switch_db_type as global_db_type
    conn = get_connection(global_db_type)
    with conn.cursor() as cursor:
        cursor.execute("SELECT email FROM notification_emails")
        emails = [row[0] for row in cursor.fetchall()]
    conn.close()
    return emails
