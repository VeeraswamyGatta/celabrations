import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import altair as alt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime

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

# ---------- Create Tables if not exist ----------
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

# ---------- Styling ----------
st.markdown("""
<style>
    .block-container {
        padding: 2rem;
        border-radius: 10px;
    }
    label > div[data-testid="stMarkdownContainer"] > p:first-child:before {
        content: "* ";
        color: red;
    }
</style>
""", unsafe_allow_html=True)

# Initialize admin login state if not set
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

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
                    f"Name: {name}\nEmail: {email}\nItems: {', '.join(selected_items) if selected_items else 'None'}\nDonation: ${donation}"
                )
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Submission failed: {e}")

# ---------- Tab 2: Events ----------
with tabs[1]:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>Ganesh Chaturthi Events</h1>", unsafe_allow_html=True)

    if "events" not in st.session_state or st.session_state.get("refresh_events", True):
        cursor.execute("SELECT id, title, event_date, link FROM events ORDER BY event_date")
        events = cursor.fetchall()
        st.session_state.events = events
        st.session_state.refresh_events = False
    else:
        events = st.session_state.events

    if events:
        df_events = pd.DataFrame(events, columns=["ID", "Event Name", "Date", "Link"])

        def make_clickable(link):
            if link and link.strip() not in ("", "*"):
                return f"[Link]({link.strip()})"
            return ""

        df_events["Link"] = df_events["Link"].apply(make_clickable)
        display_df = df_events.drop(columns=["ID"])
        st.dataframe(display_df, use_container_width=True)

        selected_event_id = st.selectbox(
            "Select Event to Edit/Delete",
            df_events["ID"].tolist(),
            format_func=lambda x: df_events[df_events["ID"] == x]["Event Name"].values[0]
        )

        if selected_event_id:
            event_row = df_events[df_events["ID"] == selected_event_id].iloc[0]

            edited_title = st.text_input("Edit Event Title", value=event_row["Event Name"])
            edited_date = st.date_input(
                "Edit Event Date",
                value=pd.to_datetime(event_row["Date"]).date() if pd.notna(event_row["Date"]) else datetime.date.today()
            )
            current_link = event_row["Link"]
            if current_link.startswith("[Link](") and current_link.endswith(")"):
                current_link = current_link[6:-1]
            edited_link = st.text_input("Edit Event Link", value=current_link)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Event"):
                    if not edited_title.strip():
                        st.error("Event title is required.")
                    else:
                        link_to_store = None if edited_link.strip() in ("", "*") else edited_link.strip()
                        try:
                            cursor.execute(
                                "UPDATE events SET title=%s, event_date=%s, link=%s WHERE id=%s",
                                (edited_title, edited_date, link_to_store, selected_event_id)
                            )
                            conn.commit()
                            st.success("✅ Event updated successfully!")
                            send_email(
                                "Ganesh Chaturthi Event Updated",
                                f"Event updated:\nTitle: {edited_title}\nDate: {edited_date}\nLink: {edited_link if edited_link else 'N/A'}"
                            )
                            st.session_state.refresh_events = True
                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ Failed to update event: {e}")

            with col2:
                if st.button("Delete Event"):
                    try:
                        cursor.execute("DELETE FROM events WHERE id=%s", (selected_event_id,))
                        conn.commit()
                        st.success("🗑️ Event deleted successfully!")
                        send_email(
                            "Ganesh Chaturthi Event Deleted",
                            f"Event deleted:\nTitle: {event_row['Event Name']}\nDate: {event_row['Date']}\nLink: {event_row['Link']}"
                        )
                        st.session_state.refresh_events = True
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to delete event: {e}")
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
                    send_email(
                        "New Ganesh Chaturthi Event Added",
                        f"Event Title: {new_title}\nEvent Date: {new_date}\nEvent Link: {new_link if new_link else 'N/A'}"
                    )
                    st.session_state.refresh_events = True
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add event: {e}")

# ---------- Tab 3: Statistics (with admin authentication) ----------
with tabs[2]:
    if not st.session_state.admin_logged_in:
        st.markdown("<h1 style='text-align: center; color: #6A1B9A;'>Admin Login Required</h1>", unsafe_allow_html=True)
        with st.form("admin_login_stats"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            login = st.form_submit_button("Login")

        if login:
            if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("✅ Admin access granted!")
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials")
    else:
        st.markdown("<h1 style='text-align: center; color: #1565C0;'>Sponsorship Statistics</h1>", unsafe_allow_html=True)

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
    st.markdown("<h1 style='text-align: center; color: #6A1B9A;'>Admin Panel</h1>", unsafe_allow_html=True)

    if not st.session_state.admin_logged_in:
        with st.form("admin_login_admin"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            login = st.form_submit_button("Login")

        if login:
            if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("✅ Admin access granted!")
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials")
    else:
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
        df = pd.read_sql("SELECT * FROM sponsorship_items ORDER BY id", conn)
        st.dataframe(df)

        st.markdown("### ✏️ Edit Existing Item")
        item_id = st.selectbox("Select Item ID", df["id"].tolist())
        item_row = df[df.id == item_id].iloc[0]
        new_item_name = st.text_input("Item Name", value=item_row["item"])
        new_amount = st.number_input("Amount", value=float(item_row["amount"]))
        new_limit = st.number_input("Limit", value=int(item_row["sponsor_limit"]))

        if st.button("Update Item"):
            try:
                cursor.execute("UPDATE sponsorship_items SET item=%s, amount=%s, sponsor_limit=%s WHERE id=%s",
                               (new_item_name, new_amount, new_limit, item_id))
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
                    cursor.execute("INSERT INTO sponsorship_items (item, amount, sponsor_limit) VALUES (%s, %s, %s)",
                                   (new_name, new_amt, new_lim))
                    conn.commit()
                    st.success("✅ New item added!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add item: {e}")

        st.markdown("### 🗑️ Delete Item")
        del_item = st.selectbox("Select Item to Delete", df["item"].tolist())
        if st.button("Delete Item"):
            try:
                cursor.execute("DELETE FROM sponsors WHERE sponsorship = %s", (del_item,))
                cursor.execute("DELETE FROM sponsorship_items WHERE item = %s", (del_item,))
                conn.commit()
                st.success("✅ Item and related sponsorships deleted!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Failed to delete item: {e}")
