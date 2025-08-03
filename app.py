import streamlit as st
import pandas as pd
import psycopg2
import os
from psycopg2.extras import RealDictCursor

st.set_page_config(page_title="Ganesh Chaturthi 2025", layout="wide")

# ---------- Constants ----------
BG_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/8/89/Lord_Ganesha_art.png"

sponsorship_items = {
    "Ganesh Idol": 300,
    "Priest Donation (2 days)": 200,
    "Pooja Items (Patri, Flowers, Coconuts)": 150,
    "Garlands": 150,
    "Fruits": 50,
    "Tamala Leaves": 10,
    "Pooja Essentials (Karpooram, etc.)": 100,
    "Decoration (Marigold, Backdrop, etc.)": 200,
    "Nimarjanam Logistics": 200,
    "Serving Items (Bowls, Water, Napkins)": 400,
    "Miscellaneous Items": 500
}

def calculate_limit(cost):
    return int(cost // 50) if cost >= 50 else 3

sponsor_limits = {item: calculate_limit(cost) for item, cost in sponsorship_items.items()}

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
tabs = st.tabs(["🎉 Sponsorship & Donation", "📅 Events"])

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

    selected_items = []
    for item, cost in sponsorship_items.items():
        limit = sponsor_limits[item]
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

    events = {
        "Day 1: Ganapathi Sthapana": "https://example.com/day1",
        "Day 2: Visesha Alankaram": "https://example.com/day2",
        "Day 3: Cultural Programs": "https://example.com/day3",
        "Day 4: Annadanam": "https://example.com/day4",
        "Day 5: Nimajjanam": "https://example.com/day5"
    }

    for event, link in events.items():
        st.markdown(f"- [{event}]({link})")
