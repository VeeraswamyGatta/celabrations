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
