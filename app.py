import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import altair as alt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from PIL import Image

st.set_page_config(page_title="Ganesh Chaturthi 2025", layout="wide")

# ---------- Constants ----------
ADMIN_USERNAME = st.secrets["admin_user"]
ADMIN_PASSWORD = st.secrets["admin_pass"]
EMAIL_SENDER = st.secrets["email_sender"]
EMAIL_PASSWORD = st.secrets["email_password"]
SMTP_SERVER = st.secrets["smtp_server"]
SMTP_PORT = st.secrets["smtp_port"]

# ---------- DB Connection ----------
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=st.secrets["postgres_host"],
        port=st.secrets["postgres_port"],
        dbname=st.secrets["postgres_dbname"],
        user=st.secrets["postgres_user"],
        password=st.secrets["postgres_password"]
    )

conn = get_connection()
cursor = conn.cursor()

# ---------- Create Tables ----------
cursor.execute("""CREATE TABLE IF NOT EXISTS sponsorship_items (
    id SERIAL PRIMARY KEY,
    item TEXT UNIQUE NOT NULL,
    amount NUMERIC NOT NULL,
    sponsor_limit INTEGER NOT NULL
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS sponsors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    mobile TEXT,
    apartment TEXT NOT NULL,
    sponsorship TEXT,
    donation NUMERIC DEFAULT 0
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    event_date DATE,
    link TEXT
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS notification_emails (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL
);""")

conn.commit()

# ---------- Send Email ----------
def send_email(subject, body):
    cursor.execute("SELECT email FROM notification_emails")
    recipients = [row[0] for row in cursor.fetchall()]
    if not recipients:
        return
    for recipient in recipients:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
        except Exception as e:
            print(f"Failed to send email to {recipient}: {e}")

# ---------- Styles ----------
st.markdown("""
<style>
    .stApp {
        background-attachment: fixed;
        background-size: cover;
    }
    .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Display Image at Top ----------
ganesh_img = Image.open("ganesh.png")
# Resize to reduce height by ~50%
width, height = ganesh_img.size
resized_img = ganesh_img.resize((width, height // 2))
st.image(resized_img, use_container_width=True)

# ---------- Tabs ----------
tabs = st.tabs(["🎉 Sponsorship & Donation", "📅 Events", "📊 Statistics", "🔐 Admin"])

# ---------- Continue with your tab logic... ----------
# NOTE: Your existing logic inside tabs[0], tabs[1], tabs[2], tabs[3]
# remains unchanged — copy/paste from your current code after image section.
