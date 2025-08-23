import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from .db import get_connection

def send_email(subject, body, recipients):
    if not recipients:
        return
    EMAIL_SENDER = st.secrets["email_sender"]
    EMAIL_PASSWORD = st.secrets["email_password"]
    SMTP_SERVER = st.secrets["smtp_server"]
    SMTP_PORT = st.secrets["smtp_port"]
    # Optionally support attachments
    def send_with_attachment(recipient, subject, body, attachment=None, filename=None, mime_type=None):
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        if attachment and filename:
            from email.mime.base import MIMEBase
            from email import encoders
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            if mime_type:
                part.add_header('Content-Type', mime_type)
            msg.attach(part)
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
        except Exception as e:
            print(f"Failed to send email to {recipient}: {e}")
    return send_with_attachment
