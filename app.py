import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Ganesh Chaturthi 2025 Sponsorship", layout="wide")

# --- File to store data ---
DATA_FILE = "sponsors.csv"

# --- Sponsorship Items and Costs ---
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

# --- Calculate sponsor limits based on cost ---
def calculate_limit(cost):
    return int(cost // 50) if cost >= 50 else 3

sponsor_limits = {item: calculate_limit(cost) for item, cost in sponsorship_items.items()}

# --- Load existing data ---
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["name", "email", "item"])

# --- Grouped sponsor data ---
current_counts = df["item"].value_counts().to_dict()
current_sponsors = df.groupby("item")["name"].apply(list).to_dict()

# --- Page Header ---
st.markdown("<h1 style='text-align: center; color: #E65100;'>🙏 Ganesh Chaturthi 2025 Sponsorship Portal</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>📅 August 26 – 30, 2025 &nbsp;&nbsp; | &nbsp;&nbsp; 📍 3C Garage (Thanks to Raghava)</h4>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("### 💡 Please review the items below and select what you'd like to sponsor. Each item has a limited number of sponsorship slots.")

name = st.text_input("👤 Your Full Name")
email = st.text_input("📧 Your Email Address")

st.markdown("---")

sponsored_items = []

# --- Display each item ---
for item, cost in sponsorship_items.items():
    limit = sponsor_limits[item]
    count = current_counts.get(item, 0)
    sponsors = current_sponsors.get(item, [])

    with st.container():
        st.markdown(f"<h5 style='color:#2E7D32'>{item} — <span style='color:#D84315;'>${cost}</span></h5>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:gray;'>Limit: {limit} | Sponsored: {count}</span>", unsafe_allow_html=True)
        
        if count < limit:
            selected = st.checkbox("✅ I want to sponsor this", key=item)
            if selected:
                sponsored_items.append(item)
        else:
            st.markdown("<div style='color:#EF6C00; font-weight:bold;'>⚠️ Fully Sponsored!</div>", unsafe_allow_html=True)
            if sponsors:
                st.markdown("👥 Sponsored by: " + ", ".join(f"<b>{s}</b>" for s in sponsors), unsafe_allow_html=True)

        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)

# --- Submit section ---
if st.button("🎉 Submit Sponsorship"):
    if not name or not email:
        st.error("Please enter your name and email.")
    elif not sponsored_items:
        st.warning("Please select at least one item to sponsor.")
    else:
        new_entries = pd.DataFrame({
            "name": [name] * len(sponsored_items),
            "email": [email] * len(sponsored_items),
            "item": sponsored_items
        })
        updated_df = pd.concat([df, new_entries], ignore_index=True)
        updated_df.to_csv(DATA_FILE, index=False)
        st.success("✅ Thank you for your sponsorship! We will contact you soon.")
