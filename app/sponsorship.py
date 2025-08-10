import streamlit as st
import pandas as pd
import datetime
from .db import get_connection
from .email_utils import send_email
from .notification_utils import get_notification_emails
import altair as alt

# Place all sponsorship and donation logic here

def sponsorship_tab():
    st.session_state['active_tab'] = 'Sponsorship'
    conn = get_connection()
    cursor = conn.cursor()

    st.markdown(
        f"""
        <div style='text-align: center; margin-top: -1.2em; margin-bottom: -0.7em;'>
            <h1 style='color: #E65100; margin: 0 0 0.04em 0; font-size: 2.1em; line-height: 1.05;'>Terrazzo Ganesh Celebrations 2025</h1>
            <div style='font-size: 1.08em; color: #444; margin: 0;'>
                <span style='margin-right: 18px;'>
                    <span style='font-size:1.2em; vertical-align:middle;'>📅</span>
                    <b>26th Aug 2025 to 30th Aug 2025 (5 days)</b>
                </span><br/>
                <span>
                    <span style='font-size:1.2em; vertical-align:middle;'>📍</span>
                    <b>3C Garagge</b> <span style='font-size:1.2em;vertical-align:middle;'>🙏</span> <span style='font-size:0.95em;'>(Raghava)</span>
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("""
<span style='font-size:1.13em; font-family: Times New Roman, Calibri, Verdana, serif;'>
We warmly welcome you to join this year’s celebration by sponsoring any of the major items listed below. The cost for each item will be shared among the selected sponsors based on available slots. You may also contribute any amount of your choice as a donation.<br>
<br>
This year’s celebration is estimated to cost approximately <span style='color:#d32f2f; font-weight:bold;'>$2,800–$3,000</span>, based on last year’s expenses.<br>
<br>
Your generous support will help us make this year’s festivities vibrant and memorable for our entire community.<br>
</span>
""", unsafe_allow_html=True)




    # Only show info message if not on submitted details page
    if not (st.session_state.get('show_submission') and st.session_state.get('submitted_data')):
        # --- High-level statistics ---
        cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items")
        items = cursor.fetchall()
        total_slots = sum([row[2] for row in items])
        cursor.execute("SELECT sponsorship, donation FROM sponsors")
        sponsor_rows = cursor.fetchall()
        slots_filled = {}
        for s, _ in sponsor_rows:
            if s:
                slots_filled[s] = slots_filled.get(s, 0) + 1
        remaining_slots = sum([row[2] - slots_filled.get(row[0], 0) for row in items])
        total_donated = sum([row[1] for row in sponsor_rows if row[1]])
        cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items")
        sponsorship_items = cursor.fetchall()
        cursor.execute("SELECT sponsorship FROM sponsors")
        sponsored_counts = {}
        for row in cursor.fetchall():
            s = row[0]
            if s:
                sponsored_counts[s] = sponsored_counts.get(s, 0) + 1
        total_sponsored = 0
        for item, amount, limit in sponsorship_items:
            count = sponsored_counts.get(item, 0)
            if count > 0 and limit:
                total_sponsored += (amount / limit) * count
        total_sponsored = round(total_sponsored, 2)
        total_donated = round(total_donated, 2)
        total_combined = round(total_sponsored + total_donated, 2)
        import requests
        from bs4 import BeautifulSoup
        paypal_link = st.secrets.get("paypal_link", "")
        total_paypal_received = "(fetching...)"
        if paypal_link:
            try:
                resp = requests.get(paypal_link, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    amt_tag = soup.find(class_="poolProgressBar-amount-raised")
                    if amt_tag and amt_tag.text.strip():
                        total_paypal_received = amt_tag.text.strip()
                    else:
                        import re
                        match = re.search(r'\$[0-9,.]+', resp.text)
                        if match:
                            total_paypal_received = match.group(0)
                        else:
                            total_paypal_received = "(not found)"
                else:
                    total_paypal_received = f"(error: {resp.status_code})"
            except Exception as e:
                total_paypal_received = f"(error)"
        blink_style = """
<style>
.blink-red {
    color: #d32f2f;
    font-weight: bold;
    animation: blinker 1s linear infinite;
}
@keyframes blinker {
    50% { opacity: 0; }
}
</style>
"""
        if remaining_slots > 0:
            slots_html = f"<span class='blink-red'>{remaining_slots}</span>"
            style_html = blink_style
        else:
            slots_html = f"<span style='color:#d32f2f;font-weight:bold'>{remaining_slots}</span>"
            style_html = ""
        st.markdown(f"""
{style_html}
<div style='font-size:1.08em; color:#1565c0; margin-bottom: 0.5em;'>
<b>Slots</b> (Total Number of Remaining Slots / Total Number of Slots): {slots_html} / <span style='color:#2E7D32;'>{total_slots}</span><br>
<b>Total Donated Amount Submitted:</b> <span style='color:#2E7D32;'>${total_donated}</span><br>
<b>Total Sponsored Amount Submitted:</b> <span style='color:#2E7D32;'>${total_sponsored}</span><br>
<b>Total Sponsored + Donation Amount Submitted:</b> <span style='color:#2E7D32;'>${total_combined}</span><br>
<b>Total Amount Received in PayPal Account:</b> <span style='color:#2E7D32;'>{total_paypal_received}</span>
</div>
""", unsafe_allow_html=True)
        st.markdown("""
<br>
<div style='font-size:1.08em; color:#d32f2f; margin-bottom: 0.5em;'>
Please fill in your details below to participate in the Ganesh Chaturthi celebrations. Your information helps us coordinate and keep you updated!
</div>
""", unsafe_allow_html=True)
    apartment = st.text_input("🏢 Your Apartment Number", help="Apartment number must be between 100 and 1600", placeholder="E.g., 305")
    email = st.text_input("📧 Email Address (optional)", help="Get notifications and receipts to your email", placeholder="your@email.com")
    gothram = st.text_input("🪔 Gothram (optional)", help="Enter your family Gothram (optional)", placeholder="E.g., Bharadwaja, Kashyapa, etc.")
    mobile = st.text_input("📱 Mobile Number (optional)", help="10-digit US phone number (no country code)", placeholder="E.g., 5121234567")

    # --- High-level statistics ---
    # Get all sponsorship items
    cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items")
    items = cursor.fetchall()
    total_slots = sum([row[2] for row in items])
    # Get all sponsors
    cursor.execute("SELECT sponsorship, donation FROM sponsors")
    sponsor_rows = cursor.fetchall()
    # Calculate remaining slots
    slots_filled = {}
    for s, _ in sponsor_rows:
        if s:
            slots_filled[s] = slots_filled.get(s, 0) + 1
    remaining_slots = sum([row[2] - slots_filled.get(row[0], 0) for row in items])
    # Calculate totals
    total_donated = sum([row[1] for row in sponsor_rows if row[1]])
    # Calculate total sponsored amount (sum of all sponsorships)
    cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items")
    sponsorship_items = cursor.fetchall()
    cursor.execute("SELECT sponsorship FROM sponsors")
    sponsored_counts = {}
    for row in cursor.fetchall():
        s = row[0]
        if s:
            sponsored_counts[s] = sponsored_counts.get(s, 0) + 1
    total_sponsored = 0
    for item, amount, limit in sponsorship_items:
        count = sponsored_counts.get(item, 0)
        if count > 0 and limit:
            total_sponsored += (amount / limit) * count
    total_sponsored = round(total_sponsored, 2)
    total_donated = round(total_donated, 2)
    total_combined = round(total_sponsored + total_donated, 2)
    # Fetch PayPal pool amount from the public page
    import requests
    from bs4 import BeautifulSoup
    paypal_link = st.secrets.get("paypal_link", "")
    total_paypal_received = "(fetching...)"
    if paypal_link:
        try:
            resp = requests.get(paypal_link, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Try to find the amount in the page (PayPal pool pages show a progress bar with amount)
                # Look for something like: <span class="poolProgressBar-amount-raised">$123.45</span>
                amt_tag = soup.find(class_="poolProgressBar-amount-raised")
                if amt_tag and amt_tag.text.strip():
                    total_paypal_received = amt_tag.text.strip()
                else:
                    # Fallback: look for any $ amount in the page
                    import re
                    match = re.search(r'\$[0-9,.]+', resp.text)
                    if match:
                        total_paypal_received = match.group(0)
                    else:
                        total_paypal_received = "(not found)"
            else:
                total_paypal_received = f"(error: {resp.status_code})"
        except Exception as e:
            total_paypal_received = f"(error)"
    # ...existing code...

    tab1, tab2 = st.tabs([
        "🛕 Sponsorship Items",
        "💰 Donation"
    ])
    selected_items = []
    with tab1:
        st.markdown("<div style='font-size:1.08em; color:#1565c0; margin-bottom: 0.5em;'><b>Major Sponsorship items are listed below</b></div>", unsafe_allow_html=True)
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
        # Show donor table before donation field
        cursor.execute("SELECT name, donation FROM sponsors WHERE donation IS NOT NULL AND donation > 0 ORDER BY donation DESC")
        donor_rows = cursor.fetchall()
        if donor_rows:
            donor_df = pd.DataFrame(donor_rows, columns=["Donor Name", "Amount"])
            donor_df["Amount"] = donor_df["Amount"].apply(lambda x: f"${x}")
            st.markdown("<b>🙏 Donors</b>", unsafe_allow_html=True)
            st.table(donor_df)
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
                # Calculate sponsorship item total as (amount / sponsor_limit) for each selected item
                sponsorship_total = 0
                if selected_items:
                    format_strings = ','.join(['%s'] * len(selected_items))
                    cursor.execute(f"SELECT amount, sponsor_limit FROM sponsorship_items WHERE item IN ({format_strings})", tuple(selected_items))
                    sponsorship_total = sum([row[0] / row[1] if row[1] else 0 for row in cursor.fetchall()])
                contributed_amount = sponsorship_total + (donation if donation else 0)
                # Format to 2 decimal places for display and email
                contributed_amount = round(contributed_amount, 2)
                for idx, item in enumerate(selected_items):
                    d = donation if idx == 0 else 0
                    cursor.execute("""
                        INSERT INTO sponsors (name, email, gothram, mobile, apartment, sponsorship, donation)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (name_val, email, gothram, phone_fmt.strip(), apartment, item, d))
                if not selected_items and donation > 0:
                    cursor.execute("""
                        INSERT INTO sponsors (name, email, gothram, mobile, apartment, sponsorship, donation)
                        VALUES (%s, %s, %s, %s, %s, NULL, %s)
                    """, (name_val, email, gothram, phone_fmt.strip(), apartment, donation))
                conn.commit()
                # Prepare submitted data for display
                submitted_data = {
                    "Name": name_val,
                    "Email": email,
                    "Gothram": gothram,
                    "Mobile": phone_fmt.strip(),
                    "Apartment": apartment
                }
                if selected_items:
                    submitted_data["Sponsorship Items"] = selected_items.copy()
                if donation > 0:
                    submitted_data["Donation"] = f"${donation}"
                if (selected_items or donation > 0) and contributed_amount:
                    submitted_data["Contributed Amount (Approx)"] = f"${contributed_amount}"
                st.session_state['submitted_data'] = submitted_data
                st.session_state['show_submission'] = True
                # Send email to notification_emails and the submitter (if provided)
                notification_emails = get_notification_emails()
                recipients = list(notification_emails)
                if email.strip():
                    recipients.append(email.strip())
                recipients = list(set(recipients))
                # Build email table rows in detailed format
                email_rows = f"""
  <tr><th>Name</th><td>{name_val}</td></tr>
  <tr><th>Email</th><td>{email}</td></tr>
  <tr><th>Gothram</th><td>{gothram}</td></tr>
  <tr><th>Mobile</th><td>{phone_fmt.strip()}</td></tr>
  <tr><th>Apartment</th><td>{apartment}</td></tr>
"""
                # Add each sponsored item as a row with amount
                if selected_items:
                    format_strings = ','.join(['%s'] * len(selected_items))
                    cursor.execute(f"SELECT item, amount, sponsor_limit FROM sponsorship_items WHERE item IN ({format_strings})", tuple(selected_items))
                    item_amounts = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
                    for item in selected_items:
                        amt, limit = item_amounts.get(item, (0, 1))
                        per_item_amt = round(amt / limit, 2) if limit else amt
                        email_rows += f"  <tr><th>Sponsorship Item</th><td>{item}</td><td><b>${per_item_amt}</b></td></tr>\n"
                # Add donation as a row if present
                if donation > 0:
                    email_rows += f"  <tr><th>Donation</th><td>General Donation</td><td><b>${donation}</b></td></tr>\n"
                # Add total contributed amount
                if contributed_amount:
                    email_rows += f"  <tr><th colspan='2'>Total Contributed Amount</th><td><b>${contributed_amount}</b></td></tr>\n"
                # Build PayPal payment section for the email
                paypal_link = st.secrets.get("paypal_link", "")
                paypal_icon = "<img src='https://www.paypalobjects.com/webstatic/icon/pp258.png' alt='PayPal' style='height:32px;vertical-align:middle;margin-right:8px;'/>"
                paypal_html = "<br><b>To pay your sponsorship or donation, please use the PayPal link below:</b><br>"
                if paypal_link:
                    paypal_html += f"<a href='{paypal_link}' target='_blank'>{paypal_icon}<b>Pay via PayPal</b></a>"
                else:
                    paypal_html += "<span style='color:#d32f2f;'>PayPal link not available.</span>"
                send_email(
                    "Ganesh Chaturthi Celebrations Sponsorship Program in Austin Texas",
                    f"""
<b>New Sponsorship Submission</b><br><br>
<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
{email_rows}
</table>
{paypal_html}
""",
                    recipients
                )
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Submission failed: {e}")
