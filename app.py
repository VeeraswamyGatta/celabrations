import streamlit as st
import pandas as pd
import psycopg2
import os
from io import BytesIO
from psycopg2.extras import RealDictCursor
import altair as alt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from PIL import Image

st.set_page_config(page_title="Ganesh Chaturthi 2025", layout="wide")

# ---------- Constants ----------
BG_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/8/89/Lord_Ganesha_art.png"
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

# ---------- Notification Email Table ----------
cursor.execute("""
    CREATE TABLE IF NOT EXISTS notification_emails (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL
    );
""")
conn.commit()

# ---------- Email Sender Function ----------
def send_email(subject, body):
    cursor.execute("SELECT email FROM notification_emails")
    recipients = [row[0] for row in cursor.fetchall()]

    if not recipients:
        return

    for recipient in recipients:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
        except Exception as e:
            print(f"Email failed to {recipient}: {e}")

# ---------- Background Styling ----------
st.markdown(f"""
    <style>
        .stApp {{
            background-image: url('{BG_IMAGE_URL}');
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        .block-container {{
            background-color: rgba(255, 255, 255, 0.90);
            padding: 2rem;
            border-radius: 10px;
        }}
        label > div[data-testid="stMarkdownContainer"] > p:first-child:before {{
            content: "* ";
            color: red;
        }}
    </style>
""", unsafe_allow_html=True)

# ---------- Ganesh Image Display ----------
try:
    image = Image.open("ganesh.png")
    width, height = image.size
    aspect_ratio = width / height
    new_height = 350  # half the height of typical screen section
    new_width = int(new_height * aspect_ratio)
    resized_img = image.resize((new_width, new_height))
    st.image(resized_img, use_container_width=True)
except Exception as e:
    st.warning("Ganesh image not found or failed to load.")

# ---------- Tabs ----------
tabs = st.tabs(["🎉 Sponsorship & Donation", "📅 Events", "📊 Statistics", "🔐 Admin"])

# ---------- Tab 1: Sponsorship ----------
with tabs[0]:
    st.markdown("<h1 style='text-align: center; color: #E65100;'>Ganesh Chaturthi Sponsorship 2025</h1>", unsafe_allow_html=True)
    st.markdown("### 🙏 Choose one or more items to sponsor, or donate an amount of your choice.")

    name = st.text_input("👤 Full Name")
    email = st.text_input("📧 Email Address")
    apartment = st.text_input("🏢 Apartment Number")
    mobile = st.text_input("📱 Mobile Number (Optional)")

    st.markdown("---")
    st.markdown("### 🛕 Sponsorship Items")

    cursor.execute("SELECT sponsorship, COUNT(*) FROM sponsors GROUP BY sponsorship")
    counts = dict(cursor.fetchall())

    cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items")
    rows = cursor.fetchall()

    selected_items = []
    for row in rows:
        item, cost, limit = row
        count = counts.get(item, 0)
        remaining = limit - count
        st.markdown(f"**{item}** — :orange[${cost}] | Total: {limit}, Remaining: {remaining}")

        if count < limit:
            if st.checkbox(f"Sponsor {item}", key=item):
                selected_items.append(item)
        else:
            st.markdown(f"🚫 Fully Sponsored")
        st.markdown("---")

    st.markdown("### 💰 Donation")
    donation = st.number_input("Enter donation amount (optional)", min_value=0, value=0)

    if st.button("✅ Submit"):
        if not name or not email or not apartment:
            st.error("Name, Email and Apartment Number are mandatory.")
        elif not selected_items and donation == 0:
            st.warning("Please sponsor at least one item or donate an amount.")
        else:
            try:
                for item in selected_items or [None]:
                    cursor.execute("""
                        INSERT INTO sponsors (name, email, mobile, apartment, sponsorship, donation)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (name, email, mobile, apartment, item, donation if item == selected_items[0] else 0))
                conn.commit()
                st.success("🎉 Thank you for your contribution!")
                send_email("New Sponsorship Submission", f"Name: {name}\nEmail: {email}\nItems: {', '.join(selected_items)}\nDonation: ${donation}")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Submission failed: {e}")

# ---------- Tab 2: Events ----------
with tabs[1]:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>Ganesh Chaturthi Events</h1>", unsafe_allow_html=True)
    st.markdown("### 📅 List of Events")

    cursor.execute("SELECT id, title, link, event_date FROM events ORDER BY event_date")
    fetched_events = cursor.fetchall()

    if fetched_events:
        event_df = pd.DataFrame(fetched_events, columns=["ID", "Event Name", "Link", "Date"])
        event_df["Edit"] = "✏️ Edit"
        event_df["Delete"] = "🗑️ Delete"
        st.dataframe(event_df, use_container_width=True)

    st.markdown("---")
    st.markdown("### ➕ Add New Event")
    with st.form("add_event_form"):
        new_title = st.text_input("Event Title")
        new_link = st.text_input("Event Link (optional)")
        new_date = st.date_input("Event Date")
        submitted = st.form_submit_button("Add Event")
        if submitted:
            if not new_title:
                st.error("Event title is required.")
            else:
                try:
                    cursor.execute("INSERT INTO events (title, link, event_date) VALUES (%s, %s, %s)", (new_title, new_link, new_date))
                    conn.commit()
                    st.success("✅ Event added successfully!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add event: {e}")
