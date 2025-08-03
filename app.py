import streamlit as st
import pandas as pd
import psycopg2
import os
from psycopg2.extras import RealDictCursor

st.set_page_config(page_title="Ganesh Chaturthi 2025", layout="wide")

# ---------- Constants ----------
BG_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/8/89/Lord_Ganesha_art.png"
ADMIN_USERNAME = st.secrets["admin_user"]
ADMIN_PASSWORD = st.secrets["admin_pass"]

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

# ---------- Table Setup ----------
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sponsors (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            mobile TEXT,
            apartment TEXT NOT NULL,
            sponsorship TEXT,
            donation NUMERIC
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            link TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sponsorship_items (
            id SERIAL PRIMARY KEY,
            item TEXT UNIQUE,
            amount NUMERIC,
            limit INTEGER
        );
    """)
    conn.commit()
except Exception as e:
    conn.rollback()
    st.error(f"❌ Database table creation failed: {e}")

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
    </style>
""", unsafe_allow_html=True)

# ---------- Tabs ----------
tabs = st.tabs(["🎉 Sponsorship & Donation", "📅 Events", "🔐 Admin"])

# ---------- Tab 1: Sponsorship ----------
with tabs[0]:
    st.markdown("<h1 style='text-align: center; color: #E65100;'>Ganesh Chaturthi Sponsorship 2025</h1>", unsafe_allow_html=True)
    st.markdown("### 🙏 Choose one or more items to sponsor, or donate an amount of your choice.")

    name = st.text_input("👤 Full Name")
    email = st.text_input("📧 Email Address")
    apartment = st.text_input("🏢 Apartment Number (Required)")
    mobile = st.text_input("📱 Mobile Number (Optional)")

    st.markdown("---")
    st.markdown("### 🛕 Sponsorship Items")

    cursor.execute("SELECT sponsorship, COUNT(*) FROM sponsors GROUP BY sponsorship")
    counts = dict(cursor.fetchall())

    cursor.execute("SELECT item, amount, limit FROM sponsorship_items")
    rows = cursor.fetchall()

    selected_items = []
    for row in rows:
        item, cost, limit = row
        count = counts.get(item, 0)

        st.markdown(f"**{item}** — :orange[${cost}] | Limit: {limit}, Sponsored: {count}")

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
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Submission failed: {e}")

# ---------- Tab 2: Events ----------
with tabs[1]:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>Ganesh Chaturthi Events</h1>", unsafe_allow_html=True)
    st.markdown("### 📅 List of Events")

    cursor.execute("SELECT title, link FROM events")
    fetched_events = cursor.fetchall()

    for event in fetched_events:
        title, link = event
        st.markdown(f"- [{title}]({link})")

    st.markdown("---")
    st.markdown("### ➕ Add New Event")
    with st.form("add_event_form"):
        new_title = st.text_input("Event Title")
        new_link = st.text_input("Event Link (optional)")
        submitted = st.form_submit_button("Add Event")
        if submitted:
            if not new_title:
                st.error("Event title is required.")
            else:
                try:
                    cursor.execute("INSERT INTO events (title, link) VALUES (%s, %s)", (new_title, new_link))
                    conn.commit()
                    st.success("✅ Event added successfully!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add event: {e}")

# ---------- Tab 3: Admin ----------
with tabs[2]:
    st.markdown("<h1 style='text-align: center; color: #6A1B9A;'>Admin Panel</h1>", unsafe_allow_html=True)
    with st.form("admin_login"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        login = st.form_submit_button("Login")

    if login:
        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            st.success("✅ Admin access granted!")

            st.markdown("### 📊 Sponsorship Items Overview")
            df = pd.read_sql("SELECT * FROM sponsorship_items ORDER BY id", conn)
            st.dataframe(df)

            st.markdown("### ✏️ Edit Existing Item")
            item_id = st.selectbox("Select Item ID", df["id"].tolist())
            item_row = df[df.id == item_id].iloc[0]
            new_item_name = st.text_input("Item Name", value=item_row["item"])
            new_amount = st.number_input("Amount", value=float(item_row["amount"]))
            new_limit = st.number_input("Limit", value=int(item_row["limit"]))

            if st.button("Update Item"):
                try:
                    cursor.execute("UPDATE sponsorship_items SET item=%s, amount=%s, limit=%s WHERE id=%s", (new_item_name, new_amount, new_limit, item_id))
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
                        cursor.execute("INSERT INTO sponsorship_items (item, amount, limit) VALUES (%s, %s, %s)", (new_name, new_amt, new_lim))
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
        else:
            st.error("❌ Invalid admin credentials")
