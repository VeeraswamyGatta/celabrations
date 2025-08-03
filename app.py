import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Ganesh Chaturthi Sponsorship", layout="centered")

# File to store sponsor data
DATA_FILE = "sponsors.csv"

# Sponsorship items and their costs
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

# Function to determine limit
def calculate_limit(cost):
    return int(cost // 50) if cost >= 50 else 3

# Compute sponsor limits
sponsor_limits = {item: calculate_limit(cost) for item, cost in sponsorship_items.items()}

# Load sponsor data
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["name", "email", "item"])

# Calculate current sponsor counts
current_counts = df["item"].value_counts().to_dict()
current_sponsors = df.groupby("item")["name"].apply(list).to_dict()

# --- UI Begins ---
st.title("🎉 Ganesh Chaturthi 2025 Sponsorship Portal")
st.markdown("📅 **Date:** Aug 26–30, 2025  \n📍 **Venue:** 3C Garage (Thanks to Raghava!)")

st.subheader("🙏 Sponsorship Options")

name = st.text_input("Your Full Name")
email = st.text_input("Your Email")

st.markdown("---")

sponsored_items = []

# Display each item with availability
for item, cost in sponsorship_items.items():
    limit = sponsor_limits[item]
    count = current_counts.get(item, 0)
    sponsors = current_sponsors.get(item, [])

    with st.container():
        st.write(f"### {item} — ${cost}")
        st.caption(f"Limit: {limit} | Sponsored: {count}")
        if count < limit:
            selected = st.checkbox(f"I want to sponsor this item", key=item)
            if selected:
                sponsored_items.append(item)
        else:
            st.warning("Fully Sponsored!")
            st.info("Sponsored by: " + ", ".join(sponsors))

        st.markdown("---")

# Submit section
if st.button("✅ Submit Sponsorship"):
    if not name or not email:
        st.error("Please enter your name and email.")
    elif not sponsored_items:
        st.error("Please select at least one item to sponsor.")
    else:
        new_entries = pd.DataFrame({
            "name": [name] * len(sponsored_items),
            "email": [email] * len(sponsored_items),
            "item": sponsored_items
        })
        updated_df = pd.concat([df, new_entries], ignore_index=True)
        updated_df.to_csv(DATA_FILE, index=False)
        st.success("🎉 Thank you for your sponsorship! We'll contact you shortly.")
