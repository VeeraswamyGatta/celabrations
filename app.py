import streamlit as st

st.set_page_config(page_title="Ganesh Chaturthi 2025", layout="wide")

st.title("🎉 Ganesh Chaturthi 2025 Sponsorship")
st.markdown("📅 **Dates:** August 26 – 30, 2025  \n📍 **Venue:** 3C Garage (Thanks to Raghava!)")

st.header("🙏 Sponsorship Categories")
st.markdown("Please select the item(s) you'd like to sponsor:")

sponsorship_options = {
    "Ganesh Idol": 300,
    "Priest Donation (2 days)": 200,
    "Pooja Items (Patri, Flowers, Coconuts)": "125–200",
    "Garlands": 150,
    "Fruits": 50,
    "Tamala Leaves": 10,
    "Pooja Essentials (Karpooram, etc.)": 100,
    "Decoration (Flowers, Backdrop, etc.)": 200,
    "Nimarjanam Logistics": 200,
    "Bowls, Bottles, Napkins, etc.": 400,
    "Miscellaneous": 500,
}

selected = st.multiselect("Choose item(s) to sponsor:", options=list(sponsorship_options.keys()))

if selected:
    st.subheader("💰 Estimated Contribution")
    total = 0
    for item in selected:
        cost = sponsorship_options[item]
        if isinstance(cost, int):
            st.write(f"- {item}: ${cost}")
            total += cost
        else:
            st.write(f"- {item}: ${cost}")
    st.success(f"Estimated Total: ~${total}" if isinstance(total, int) else "Multiple ranges selected")

st.divider()
st.header("📝 Share Your Interest")
with st.form("sponsorship_form"):
    name = st.text_input("Your Name")
    email = st.text_input("Email Address")
    phone = st.text_input("Phone Number (optional)")
    custom_note = st.text_area("Any comments or custom amount you'd like to contribute?")
    submitted = st.form_submit_button("Submit")

    if submitted:
        st.success("Thank you! We'll reach out to you soon.")
