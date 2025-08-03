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

# ---------- Create tables if not exist ----------
cursor.execute("""
CREATE TABLE IF NOT EXISTS sponsorship_items (
    id SERIAL PRIMARY KEY,
    item TEXT UNIQUE NOT NULL,
    amount NUMERIC NOT NULL,
    sponsor_limit INTEGER NOT NULL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS sponsors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    mobile TEXT,
    apartment TEXT NOT NULL,
    sponsorship TEXT,
    donation NUMERIC DEFAULT 0
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    event_date DATE,
    link TEXT
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS notification_emails (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL
);
""")
conn.commit()

# ---------- Email Sending Function ----------
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
            print(f"Failed to send email to {recipient}: {e}")

# ---------- Background Styling ----------
st.markdown("""
    <style>
        .stApp {
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }
        .block-container {
            background-color: rgba(255, 255, 255, 0.90);
            padding: 2rem;
            border-radius: 10px;
        }
        label > div[data-testid="stMarkdownContainer"] > p:first-child:before {
            content: "* ";
            color: red;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Ganesh Image Display at the top ----------
with st.container():
    try:
        image = Image.open("ganesh.png")
        width, height = image.size
        aspect_ratio = width / height
        new_height = 350
        new_width = int(new_height * aspect_ratio)
        resized_img = image.resize((new_width, new_height))
        st.image(resized_img, use_container_width=True)
    except Exception:
        st.warning("Ganesh image not found or failed to load.")

# ---------- Tabs ----------
tabs = st.tabs(["🎉 Sponsorship & Donation", "📅 Events", "📊 Statistics", "🔐 Admin"])

# ---------- Tab 1: Sponsorship & Donation ----------
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

    cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items ORDER BY id")
    rows = cursor.fetchall()

    selected_items = []
    for row in rows:
        item, cost, limit = row
        count = counts.get(item, 0)
        remaining = limit - count
        st.markdown(f"**{item}** — :orange[${cost}] | Total: {limit}, Remaining: {remaining}")

        if remaining > 0:
            if st.checkbox(f"Sponsor {item}", key=item):
                selected_items.append(item)
        else:
            st.markdown(f"🚫 Fully Sponsored")
        st.markdown("---")

    st.markdown("### 💰 Donation")
    donation = st.number_input("Enter donation amount (optional)", min_value=0, value=0)

    if st.button("✅ Submit"):
        if not name.strip() or not email.strip() or not apartment.strip():
            st.error("Name, Email and Apartment Number are mandatory.")
        elif not selected_items and donation == 0:
            st.warning("Please sponsor at least one item or donate an amount.")
        else:
            try:
                for idx, item in enumerate(selected_items):
                    d = donation if idx == 0 else 0
                    cursor.execute("""
                        INSERT INTO sponsors (name, email, mobile, apartment, sponsorship, donation)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (name, email, mobile, apartment, item, d))
                if not selected_items and donation > 0:
                    cursor.execute("""
                        INSERT INTO sponsors (name, email, mobile, apartment, sponsorship, donation)
                        VALUES (%s, %s, %s, %s, NULL, %s)
                    """, (name, email, mobile, apartment, donation))
                conn.commit()
                st.success("🎉 Thank you for your contribution!")
                send_email(
                    "New Sponsorship Submission",
                    f"Name: {name}\nEmail: {email}\nItems: {', '.join(selected_items)}\nDonation: ${donation}"
                )
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Submission failed: {e}")

# ---------- Tab 2: Events ----------
with tabs[1]:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>Ganesh Chaturthi Events</h1>")

    cursor.execute("SELECT id, title, event_date, link FROM events ORDER BY event_date")
    events = cursor.fetchall()

    if events:
        df_events = pd.DataFrame(events, columns=["ID", "Event Name", "Date", "Link"])

        def make_clickable(link):
            if link and link.strip() not in ("", "*"):
                return f"[Link]({link.strip()})"
            return ""

        df_events["Link"] = df_events["Link"].apply(make_clickable)
        display_df = df_events.drop(columns=["ID"])
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No events added yet.")

    st.markdown("---")
    st.markdown("### ➕ Add New Event")
    with st.form("add_event_form"):
        new_title = st.text_input("Event Title")
        new_date = st.date_input("Event Date", value=datetime.date.today())
        new_link = st.text_input("Event Link (optional)")
        submitted = st.form_submit_button("Add Event")
        if submitted:
            if not new_title.strip():
                st.error("Event title is required.")
            else:
                link_to_store = None if new_link.strip() in ("", "*") else new_link.strip()
                try:
                    cursor.execute(
                        "INSERT INTO events (title, event_date, link) VALUES (%s, %s, %s)",
                        (new_title, new_date, link_to_store)
                    )
                    conn.commit()
                    st.success("✅ Event added successfully!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add event: {e}")

# ---------- Tab 3: Statistics ----------
with tabs[2]:
    st.markdown("<h1 style='text-align: center; color: #1565C0;'>Sponsorship Statistics</h1>")
    df = pd.read_sql("SELECT name, email, mobile, sponsorship, donation FROM sponsors ORDER BY id", conn)
    st.markdown("### 📋 Sponsorship Records")
    st.dataframe(df)

    st.markdown("### 📊 Bar Chart of Sponsorships")
    chart_data = df["sponsorship"].value_counts().reset_index()
    chart_data.columns = ["Sponsorship", "Count"]

    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("Sponsorship", sort="-y"),
        y="Count",
        tooltip=["Sponsorship", "Count"]
    ).properties(width=700)

    st.altair_chart(chart, use_container_width=True)

# ---------- Tab 4: Admin ----------
with tabs[3]:
    st.markdown("<h1 style='text-align: center; color: #6A1B9A;'>Admin Panel</h1>")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            login = st.form_submit_button("Login")

        if login:
            if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("✅ Admin access granted!")
            else:
                st.error("❌ Invalid admin credentials")

    if st.session_state.admin_logged_in:
        st.markdown("### 📩 Notification Email Configuration")
        with st.form("add_email_form"):
            new_email = st.text_input("Add Notification Email")
            submit_email = st.form_submit_button("Add Email")
        if submit_email and new_email:
            try:
                cursor.execute("INSERT INTO notification_emails (email) VALUES (%s) ON CONFLICT DO NOTHING", (new_email,))
                conn.commit()
                st.success("✅ Email added")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Failed to add email: {e}")

        cursor.execute("SELECT id, email FROM notification_emails ORDER BY id")
        emails = cursor.fetchall()
        if emails:
            df_emails = pd.DataFrame(emails, columns=["ID", "Email"])
            st.markdown("### 📧 Configured Notification Emails")
            st.dataframe(df_emails, use_container_width=True)
        else:
            st.info("No notification emails configured yet.")

        st.markdown("### 📊 Sponsorship Items Overview")
        df_items = pd.read_sql("SELECT * FROM sponsorship_items ORDER BY id", conn)
        st.dataframe(df_items)

        st.markdown("### ✏️ Edit Existing Item")
        item_id = st.selectbox("Select Item ID", df_items["id"].tolist())
        item_row = df_items[df_items["id"] == item_id].iloc[0]
        new_item_name = st.text_input("Item Name", value=item_row["item"])
        new_amount = st.number_input("Amount", value=float(item_row["amount"]))
        new_limit = st.number_input("Limit", value=int(item_row["sponsor_limit"]))

        if st.button("Update Item"):
            try:
                cursor.execute(
                    "UPDATE sponsorship_items SET item=%s, amount=%s, sponsor_limit=%s WHERE id=%s",
                    (new_item_name, new_amount, new_limit, item_id)
                )
                conn.commit()
                st.success("✅ Item updated successfully!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Failed to update: {e}")

        st.markdown("### ➕ Add New Sponsorship Item")
        with st.form("add_item_form"):
            new_name = st.text_input("New Item Name")
            new_amt = st.number_input("Amount", min_value=0)
            new_lim = st.number_input("Limit", min_value=1, value=3)
            if st.form_submit_button("Add Item"):
                try:
                    cursor.execute(
                        "INSERT INTO sponsorship_items (item, amount, sponsor_limit) VALUES (%s, %s, %s)",
                        (new_name, new_amt, new_lim)
                    )
                    conn.commit()
                    st.success("✅ New item added!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add item: {e}")

        st.markdown("### 🗑️ Delete Item")
        del_item = st.selectbox("Select Item to Delete", df_items["item"].tolist())
        if st.button("Delete Item"):
            try:
                cursor.execute("DELETE FROM sponsors WHERE sponsorship = %s", (del_item,))
                cursor.execute("DELETE FROM sponsorship_items WHERE item = %s", (del_item,))
                conn.commit()
                st.success("✅ Item and related sponsorships deleted!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Failed to delete item: {e}")
