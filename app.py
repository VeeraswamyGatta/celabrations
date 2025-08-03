import streamlit as st
import pandas as pd
import psycopg2
import os

# --- Streamlit page settings ---
st.set_page_config(page_title="Ganesh Chaturthi Sponsorship", layout="wide")

# --- Sponsorship data ---
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
    "Serving Items (Water, Napkins)": 400,
    "Miscellaneous": 500
}

def calculate_limit(cost):
    return int(cost // 50) if cost >= 50 else 3

sponsor_limits = {item: calculate_limit(cost) for item, cost in sponsorship_items.items()}

# --- Connect to PostgreSQL ---
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        dbname=st.secrets["postgres"]["dbname"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"]
    )

conn = get_connection()
cur = conn.cursor()

# --- Create Tables ---
cur.execute("""
CREATE TABLE IF NOT EXISTS sponsors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    UNIQUE(email)
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS sponsorships (
    id SERIAL PRIMARY KEY,
    sponsor_id INTEGER REFERENCES sponsors(id),
    item TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# --- UI Header ---
st.markdown("<h1 style='text-align:center;color:#E65100;'>Ganesh Chaturthi 2025 Sponsorship Portal</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;'>📍 3C Garage | 📅 Aug 26–30</h4>", unsafe_allow_html=True)
st.markdown("---")

name = st.text_input("👤 Your Full Name")
email = st.text_input("📧 Your Email")

st.markdown("### 🙏 Sponsorship Options")
selected_items = []

# Get current sponsorship counts
cur.execute("SELECT item, COUNT(*) FROM sponsorships GROUP BY item;")
counts = dict(cur.fetchall())

# Get sponsor names for full items
cur.execute("""
SELECT s.name, sp.item
FROM sponsors s
JOIN sponsorships sp ON s.id = sp.sponsor_id
""")
sponsor_map = {}
for name_, item_ in cur.fetchall():
    sponsor_map.setdefault(item_, []).append(name_)

for item, cost in sponsorship_items.items():
    limit = sponsor_limits[item]
    current = counts.get(item, 0)
    sponsors = sponsor_map.get(item, [])

    st.markdown(f"**{item} – ${cost}** (Limit: {limit}, Sponsored: {current})")

    if current < limit:
        if st.checkbox(f"I want to sponsor '{item}'", key=item):
            selected_items.append(item)
    else:
        st.markdown(f"<span style='color:red;'>Fully Sponsored by: {', '.join(sponsors)}</span>", unsafe_allow_html=True)

st.markdown("---")

if st.button("✅ Submit Sponsorship"):
    if not name or not email or not selected_items:
        st.warning("Please enter all details and select items.")
    else:
        try:
            # Insert sponsor (deduplicated by email)
            cur.execute("INSERT INTO sponsors (name, email) VALUES (%s, %s) ON CONFLICT(email) DO NOTHING RETURNING id;", (name, email))
            sponsor_id = cur.fetchone()
            if sponsor_id is None:
                cur.execute("SELECT id FROM sponsors WHERE email = %s", (email,))
                sponsor_id = cur.fetchone()
            sponsor_id = sponsor_id[0]

            # Insert sponsorships
            for item in selected_items:
                cur.execute("INSERT INTO sponsorships (sponsor_id, item) VALUES (%s, %s)", (sponsor_id, item))

            conn.commit()
            st.success("Thank you for sponsoring!")
        except Exception as e:
            conn.rollback()
            st.error(f"Error: {e}")

# --- STATS ---
st.markdown("## 📊 Sponsorship Statistics")

stats = []
for item, cost in sponsorship_items.items():
    limit = sponsor_limits[item]
    count = counts.get(item, 0)
    remaining = max(limit - count, 0)
    stats.append({"Item": item, "Sponsored": count, "Remaining": remaining, "Limit": limit})

df_stats = pd.DataFrame(stats)

st.dataframe(df_stats, use_container_width=True)

st.bar_chart(df_stats.set_index("Item")[["Sponsored", "Remaining"]])
