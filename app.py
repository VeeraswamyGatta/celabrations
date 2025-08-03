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
st.markdown("""
    <style>
        .block-container {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            border-radius: 10px;
        }
        label > div[data-testid="stMarkdownContainer"] > p:first-child:before {
            content: "* ";
            color: red;
        }
    </style>
""", unsafe_allow_html=True)

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
                send_email("New Sponsorship Submission", f"Name: {name}\nEmail: {email}\nPhone: {mobile}\nItems: {', '.join(selected_items)}\nDonation: ${donation}")
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
                    send_email("New Ganesh Event Added", f"Event: {new_title}\nDate: {new_date}\nLink: {new_link}")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add event: {e}")

# ---------- Tab 3: Statistics (Protected) ----------
with tabs[2]:
    if "auth" not in st.session_state:
        st.session_state.auth = False

    if not st.session_state.auth:
        st.subheader("🔐 Admin Login Required")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.auth = True
            else:
                st.error("Invalid credentials.")
    else:
        st.markdown("## 📊 Sponsorship Overview")

        cursor.execute("SELECT sponsorship, COUNT(*), SUM(donation) FROM sponsors GROUP BY sponsorship")
        rows = cursor.fetchall()
        stats_df = pd.DataFrame(rows, columns=["Item", "Sponsors", "Total Donation"])
        st.dataframe(stats_df, use_container_width=True)

        chart = alt.Chart(stats_df).mark_bar().encode(
            x='Item',
            y='Sponsors',
            color='Item',
            tooltip=['Item', 'Sponsors', 'Total Donation']
        ).properties(width=700)

        st.altair_chart(chart, use_container_width=True)

# ---------- Tab 4: Admin Emails ----------
with tabs[3]:
    st.markdown("### ✉️ Configure Notification Emails")
    new_email = st.text_input("Add Notification Email")
    if st.button("Add Email"):
        if new_email:
            try:
                cursor.execute("INSERT INTO notification_emails (email) VALUES (%s) ON CONFLICT DO NOTHING", (new_email,))
                conn.commit()
                st.success("Email added successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

    cursor.execute("SELECT email FROM notification_emails")
    emails = cursor.fetchall()
    if emails:
        df = pd.DataFrame(emails, columns=["Configured Notification Emails"])
        st.dataframe(df, use_container_width=True)
