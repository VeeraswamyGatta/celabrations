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
    st.markdown("<h1 style='text-align: center; color: #E65100;'>Ganesh Chaturthi Sponsorship 2025</h1>", unsafe_allow_html=True)
    st.markdown("### 🙏 Choose one or more items to sponsor, or donate an amount of your choice.")

    import re
    name = st.text_input("👤 Full Name")
    apartment = st.text_input("🏢 Apartment Number")
    email = st.text_input("📧 Email Address (optional)", help="Enter Email to Subscribe the notifications to Your Email")
    mobile = st.text_input("📱 Mobile Number (Optional, US format)")

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

    def validate_us_phone(phone):
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return True, f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return False, phone

    def format_name(name):
        return ' '.join(word.capitalize() for word in name.strip().split())

    if st.button("✅ Submit"):
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
                st.success("🎉 Thank you for your contribution!")
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
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Submission failed: {e}")
