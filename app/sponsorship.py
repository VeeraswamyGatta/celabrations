import streamlit as st
import pandas as pd
import datetime
from .db import get_connection
from .email_utils import send_email
import altair as alt

# Place all sponsorship and donation logic here

def sponsorship_tab():
    st.session_state['active_tab'] = 'Sponsorship'
    conn = get_connection()
    cursor = conn.cursor()

    st.markdown(
        f"""
        <h1 style='text-align: center; color: #E65100;'>Ganesh Chaturthi Sponsorship 2025</h1>
        <div style='text-align: center; font-size: 1.1em; color: #444; margin-bottom: 0.5em;'>
            <span style='margin-right: 18px;'>
                <span style='font-size:1.2em; vertical-align:middle;'>📅</span>
                <b>26th August 2025 to 30th August 2025 (5 days)</b>
            </span><br/>
            <span>
                <span style='font-size:1.2em; vertical-align:middle;'>📍</span>
                <b>3C Garagge</b> <span style='font-size:1.2em;vertical-align:middle;'>🙏</span> <span style='font-size:0.95em;'>(Raghava)</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("""
<span style='font-size:1.15em; font-weight:bold;'>
We warmly invite you to be part of this celebration by sponsoring any of the items listed below based on the slots available or contributing an amount of your choice as a donation.<br>
<br>
The total estimated cost for this year’s celebrations is approximately <span style='color:#d32f2f;'>$2,800–$3,000</span> (based on last year’s event expenses)<br>
<br>
Your generous support will help make this year’s festivities vibrant and memorable for our entire community.
</span>
""", unsafe_allow_html=True)


    st.markdown("""
<br>
<div style='font-size:1.08em; color:#2E7D32; margin-bottom: 0.5em;'>
Please fill in your details below to participate in the Ganesh Chaturthi celebrations. Your information helps us coordinate and keep you updated!
</div>
""", unsafe_allow_html=True)

    import re
    # Post-submit page logic
    if 'show_submission' not in st.session_state:
        st.session_state['show_submission'] = False
    if 'submitted_data' not in st.session_state:
        st.session_state['submitted_data'] = None

    if st.session_state['show_submission'] and st.session_state['submitted_data']:
        st.success("🎉 Thank you for your contribution!")
        st.markdown("### Submitted Details")
        df = pd.DataFrame([st.session_state['submitted_data']])
        st.table(df)
        if st.button("Home"):
            st.session_state['show_submission'] = False
            st.session_state['submitted_data'] = None
            st.rerun()
        return

    name = st.text_input("👤 Your Full Name", placeholder="Enter your full name")
    apartment = st.text_input("🏢 Your Apartment Number", help="Apartment number must be between 100 and 1600", placeholder="E.g., 305")
    email = st.text_input("📧 Email Address (optional)", help="Get notifications and receipts to your email", placeholder="your@email.com")
    mobile = st.text_input("📱 Mobile Number (optional)", help="10-digit US phone number (no country code)", placeholder="E.g., 5121234567")

    st.markdown("---")

    st.markdown("""
<div style='font-size:1.08em; color:#2E7D32; margin-bottom: 0.5em;'>🙏 Sponsor items or donate an amount of your choice.</div>
""", unsafe_allow_html=True)
    tab1, tab2 = st.tabs([
        "🛕 Sponsorship Items",
        "💰 Donation"
    ])
    selected_items = []
    with tab1:
        st.markdown("<span style='font-size:1.08em; font-weight:bold; color:#2E7D32;'>🛕 Sponsorship Items</span>", unsafe_allow_html=True)
        cursor.execute("SELECT sponsorship, COUNT(*) FROM sponsors GROUP BY sponsorship")
        counts = dict(cursor.fetchall())
        cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items ORDER BY id")
        rows = cursor.fetchall()
        for row in rows:
            item, cost, limit = row
            count = counts.get(item, 0)
            remaining = limit - count
            # Fetch sponsor names for this item
            cursor.execute("SELECT name FROM sponsors WHERE sponsorship = %s", (item,))
            sponsor_names = [n[0] for n in cursor.fetchall()]
            if remaining > 0:
                remaining_str = f"<span class='blink' style='color:#d32f2f;font-weight:bold'>{remaining}</span>"
            else:
                remaining_str = f"{remaining}"
            st.markdown(
                """
                <style>
                .blink {
                    animation: blinker 1s linear infinite;
                }
                @keyframes blinker {
                    50% { opacity: 0; }
                }
                </style>
                """ + f"**{item}** — :orange[${cost} Approx.] | Total Slots: {limit}, Remaining Slots Available: {remaining_str}",
                unsafe_allow_html=True
            )
            if sponsor_names:
                st.markdown(
                    f"<span style='font-size: 0.95em;'>Sponsored Names: <span style='font-size:1.1em;vertical-align:middle;'>🙏</span> "
                    + ", ".join([f"<span style='color:#388e3c;font-weight:bold'>{n}</span>" for n in sponsor_names])
                    + "</span>",
                    unsafe_allow_html=True
                )
            if remaining > 0:
                if st.checkbox(f"Sponsor {item}", key=item):
                    selected_items.append(item)
                st.markdown("---")
            else:
                st.markdown(
                    f"<span style='color:#d32f2f;font-weight:bold;'>Slots are not available. This item is fully sponsored! <span style='font-size:1.1em;vertical-align:middle;'>🙏</span></span>",
                    unsafe_allow_html=True
                )
                st.markdown("---")

    with tab2:
        st.markdown("<span style='font-size:1.08em; font-weight:bold; color:#1565c0;'>💰 Donation</span>", unsafe_allow_html=True)
        donation = st.number_input("Enter donation amount (optional)", min_value=0, value=0)

    def validate_us_phone(phone):
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return True, f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return False, phone

    def format_name(name):
        return ' '.join(word.capitalize() for word in name.strip().split())

    if st.button("✅ Submit", key="sponsorship_submit"):
        errors = []
        name_val = format_name(name)
        if not name_val:
            errors.append("Name is required.")
        if not apartment.strip():
            errors.append("Apartment Number is required.")
        else:
            try:
                apt_num = int(apartment.strip())
                if not (100 <= apt_num <= 1600):
                    errors.append("Apartment Number must be between 100 and 1600.")
            except ValueError:
                errors.append("Apartment Number must be a number between 100 and 1600.")
        if not selected_items and donation == 0:
            errors.append("Please sponsor at least one item or donate an amount.")
        # Basic email validation
        if email.strip():
            if '@' not in email or not email.strip().lower().endswith('.com'):
                errors.append("Please enter a valid email address (must contain '@' and end with .com)")

        phone_valid, phone_fmt = True, mobile
        if mobile.strip():
            phone_valid, phone_fmt = validate_us_phone(mobile)
            if not phone_valid:
                errors.append("Please enter a valid 10-digit US phone number.")
        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                for idx, item in enumerate(selected_items):
                    d = donation if idx == 0 else 0
                    cursor.execute("""
                        INSERT INTO sponsors (name, email, mobile, apartment, sponsorship, donation)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (name_val, email, phone_fmt.strip(), apartment, item, d))
                if not selected_items and donation > 0:
                    cursor.execute("""
                        INSERT INTO sponsors (name, email, mobile, apartment, sponsorship, donation)
                        VALUES (%s, %s, %s, %s, NULL, %s)
                    """, (name_val, email, phone_fmt.strip(), apartment, donation))
                conn.commit()
                # Prepare submitted data for display
                st.session_state['submitted_data'] = {
                    "Name": name_val,
                    "Email": email,
                    "Mobile": phone_fmt.strip(),
                    "Apartment": apartment,
                    "Sponsorship Items": ', '.join(selected_items) if selected_items else 'N/A',
                    "Donation": f"${donation}"
                }
                st.session_state['show_submission'] = True
                # Send email to the submitter (if provided) and all unique sponsor emails
                recipients = []
                if email.strip():
                    recipients.append(email.strip())
                cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                # Avoid duplicate emails
                recipients = list({e for e in recipients + sponsor_emails})
                send_email(
                    "Ganesh Chaturthi Celebrations Sponsorship Program in Austin Texas",
                    f"""
<b>New Sponsorship Submission</b><br><br>
<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
  <tr><th>Name</th><td>{name_val}</td></tr>
  <tr><th>Email</th><td>{email}</td></tr>
  <tr><th>Mobile</th><td>{phone_fmt.strip()}</td></tr>
  <tr><th>Apartment</th><td>{apartment}</td></tr>
  <tr><th>Sponsorship Items</th><td>{', '.join(selected_items) if selected_items else 'N/A'}</td></tr>
  <tr><th>Donation</th><td>${donation}</td></tr>
</table>
""",
                    recipients
                )
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Submission failed: {e}")
