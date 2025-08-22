import streamlit as st
import pandas as pd
import datetime
from .db import get_connection
from .email_utils import send_email
from .notification_utils import get_notification_emails
import altair as alt

# Place all sponsorship and donation logic here

def sponsorship_tab():
    # Helper to get total approved expense amount
    def get_total_expense_amount(conn):
        try:
            df = pd.read_sql("SELECT amount FROM expenses WHERE status = 'active'", conn)
            if not df.empty:
                return df["amount"].astype(float).sum()
        except Exception:
            pass
        return 0.0
    st.session_state['active_tab'] = 'Sponsorship'
    conn = get_connection()
    cursor = conn.cursor()

    # --- Combined PayPal + Zelle Total ---
    # Get PayPal and Zelle totals from payment_details table
    paypal_amount = 0.0
    zelle_amount = 0.0
    try:
        paypal_df = pd.read_sql("SELECT amount FROM payment_details WHERE payment_type = 'PayPal'", conn)
        if not paypal_df.empty:
            paypal_amount = paypal_df["amount"].astype(float).sum()
    except Exception:
        paypal_amount = 0.0
    try:
        zelle_df = pd.read_sql("SELECT amount FROM payment_details WHERE payment_type = 'Zelle'", conn)
        if not zelle_df.empty:
            zelle_amount = zelle_df["amount"].astype(float).sum()
    except Exception:
        zelle_amount = 0.0
    combined_total = paypal_amount + zelle_amount

    
    st.markdown("""
    <div style='background:linear-gradient(90deg,#fffde7 60%,#e3f2fd 100%); border-radius:14px; box-shadow:0 2px 12px #e0e0e0; padding:22px 28px; margin-bottom:22px; border:2px solid #ffe082;'>
        <div style='font-size:1.18em; font-family: Times New Roman, Calibri, Verdana, serif; color:#1565c0; font-weight:bold; margin-bottom:8px; text-align:center;'>
            🙏 Welcome to Terrazzo Ganesh Celebrations 2025!
        </div>
        <div style='font-size:1.13em; color: #E65100; margin-bottom:6px; text-align:center;'>
            <span style='font-size:1.08em; color:#444;'>📅 26th Aug 2025 to 30th Aug 2025 <span style='color:#388e3c;'>(5 days)</span></span><br>
            <span style='font-size:1.08em; color:#1565c0;'>📍 3C Garagge <span style='font-size:1.15em;vertical-align:middle;'>🙏</span> <span style='font-size:0.98em; color:#444;'>(Raghava)</span></span>
        </div>
        <div style='font-size:1.08em; color:#333; margin-bottom:6px;'>
            We warmly welcome you to join this year’s celebration by sponsoring any of the major items listed below. The cost for each item will be shared among the selected sponsors based on available slots. You may also contribute any amount of your choice as a donation.
        </div>
        <div style='font-size:1.08em; color:#388e3c; font-weight:500;'>
            Your generous support will help us make this year’s festivities vibrant and memorable for our entire community.
        </div>
    </div>
   """, unsafe_allow_html=True)





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
<div style='max-width:600px; margin:1.5em auto 1em auto; border-radius:18px; box-shadow:0 2px 16px rgba(21,101,192,0.10); background:#fff; padding:2em 2.2em 1.5em 2.2em;'>
    <div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:1.2em;'>
        <div style='font-size:1.25em; color:#6A1B9A; font-weight:bold;'>🎉 Sponsorship and Donation Summary</div>
        <div style='font-size:1.5em;'>🛕</div>
    </div>
    <div style='display:flex; flex-wrap:wrap; gap:1.2em;'>
        <div style='flex:1; min-width:220px;'>
            <span style='font-size:1.1em; color:#1565c0;'>Slots</span><br>
            <span style='font-size:1.5em; color:#2E7D32; font-weight:bold;'>{slots_html}</span> / <span style='color:#1565c0;'>{total_slots}</span>
            <span style='font-size:1.2em; margin-left:8px;'>🪔</span>
        </div>
        <div style='flex:1; min-width:220px;'>
            <span style='font-size:1.1em; color:#1565c0;'>Total Sponsored & Donated</span><br>
            <span style='font-size:1.2em; color:#2E7D32; font-weight:bold;'>${total_sponsored:,.2f}</span> + <span style='font-size:1.2em; color:#388E3C; font-weight:bold;'>${total_donated:,.2f}</span> = <span style='font-size:1.2em; color:#1565c0; font-weight:bold;'>${total_combined:,.2f}</span>
            <span style='font-size:1.2em; margin-left:8px;'>💰</span>
        </div>
        <div style='flex:1; min-width:220px;'>
            <span style='font-size:1.1em; color:#1565c0;'>Total Received & Pending</span><br>
            <span style='font-size:1.2em; color:#2E7D32; font-weight:bold;'>${float(combined_total):,.2f}</span> + <span style='font-size:1.2em; color:#d32f2f; font-weight:bold;'>{float(total_combined) - float(combined_total):,.2f}</span> = <span style='font-size:1.2em; color:#1565c0; font-weight:bold;'>${float(total_combined):,.2f}</span>
            <span style='font-size:1.2em; margin-left:8px;'>📥</span>
        </div>
        <div style='flex:1; min-width:220px;'>
            <span style='font-size:1.1em; color:#1565c0;'>Available Wallet</span><br>
            <span style='font-size:1.2em; color:#388e3c; font-weight:bold;'>${float(combined_total) - float(get_total_expense_amount(conn)):,.2f}</span>
            <span style='font-size:1.2em; margin-left:8px;'>👛</span>
        </div>
    </div>
    <hr style='margin:1.5em 0 1em 0; border:0; border-top:1.5px solid #eee;'>
    <div style='font-size:1.05em; color:#1565c0; margin-bottom:0.5em;'>
        <span style='margin-right:18px;'>📊 <b>Expenses:</b> See <b style='color:#d32f2f;'>Expenses</b> tab above.</span><br>
        <span style='margin-right:18px;'>📅 <b>Events:</b> See <b style='color:#FF9800;'>Events</b> tab above.</span><br>
        <span>📈 <b>Summary:</b> See <b style='color:#FF9800;'>Statistics</b> tab above.</span>
    </div>
</div>
""", unsafe_allow_html=True)

    # --- Custom logic for user login and sponsorship limit ---
    show_submission_inputs = True
    sponsorship_limit = st.secrets.get("sponsorship_amount_limit", 0)
    # Only apply for user login, not admin
    if st.session_state.get("user_logged_in") and not st.session_state.get("admin_logged_in"):
        if sponsorship_limit and sponsorship_limit < total_combined:
            st.markdown("""
<div style='
    max-width: 520px;
    margin: 2em auto 1.5em auto;
    background: linear-gradient(90deg, #ffe0e0 0%, #fff3f3 100%);
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(211,47,47,0.08);
    padding: 1.7em 1.5em 1.2em 1.5em;
    border: 2px solid #d32f2f;
    text-align: center;
'>
    <div style='font-size:2em; color:#d32f2f; font-weight:bold; margin-bottom:0.3em;'>🎉 Sponsorship Goal Reached!</div>
    <div style='font-size:1.15em; color:#333; margin-bottom:0.7em;'>
        Thanks for reaching the sponsorship goal for the Ganesh Chaturthi celebration.<br>
        <span style='color:#d32f2f; font-weight:bold;'>We are sorry, direct submissions are now closed.</span>
    </div>
    <div style='font-size:1.08em; color:#1565c0; margin-bottom:0.5em;'>
        Please reach out in the <b>Ganesh Chaturthi celebrations 2025 WhatsApp group</b> to participate.<br>
        The team will collect your information and submit it for you.
    </div>
</div>
""", unsafe_allow_html=True)
            show_submission_inputs = False

    # Only show the info message if not on the submission thank you page and submission is allowed
    if not (st.session_state.get('show_submission') and st.session_state.get('submitted_data')) and show_submission_inputs:
        st.markdown("""
<br>
<div style='font-size:1.08em; color:#d32f2f; margin-bottom: 0.5em;'>
Please fill in your details below to participate in the Ganesh Chaturthi celebrations. Your information helps us coordinate and keep you updated!
</div>
""", unsafe_allow_html=True)

    # Show submitted details if just submitted
    if st.session_state.get('show_submission') and st.session_state.get('submitted_data'):
        st.success('Thank you for your submission! Here are your submitted details:')
        submitted_data = st.session_state['submitted_data']
        for k, v in submitted_data.items():
            if isinstance(v, list):
                st.markdown(f"**{k}:** {', '.join(str(i) for i in v)}")
            else:
                st.markdown(f"**{k}:** {v}")
        if st.button('🏠 Home', key='home_button'):
            st.session_state['show_submission'] = False
            st.session_state['submitted_data'] = None
            st.rerun()
        return

    # Only show submission inputs if allowed
    if show_submission_inputs:
        name = st.text_input("👤 Your Name", help="Please enter your full name", placeholder="E.g., Raghava Rao")
        apartment = st.text_input("🏢 Your Apartment Number", help="Apartment number must be between 100 and 1600", placeholder="E.g., 305")
        email = st.text_input("📧 Email Address (optional)", help="Get notifications and receipts to your email", placeholder="your@email.com")
        gothram = st.text_input("🪔 Gothram (optional)", help="Enter your family Gothram (optional)", placeholder="E.g., Bharadwaja, Kashyapa, etc.")
        mobile = st.text_input("📱 Mobile Number (optional)", help="10-digit US phone number (no country code)", placeholder="E.g., 5121234567")
    else:
        name = apartment = email = gothram = mobile = ""

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
            per_slot = cost / limit if limit else cost
            def fmt_amt(val):
                return str(int(val)) if val == int(val) else str(val)
            # Modern card for fully sponsored items
            if remaining > 0:
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
                    """ +
                    f"<b>{item}</b> — <span style='color:#1565c0;'>${fmt_amt(cost)} / {limit} = ${fmt_amt(per_slot)}$ per slot</span> | Total Slots: {limit}, Available Slots: {remaining_str}",
                    unsafe_allow_html=True
                )
                if sponsor_names:
                    st.markdown(
                        f"<span style='font-size: 0.95em;'>Sponsored Names: <span style='font-size:1.1em;vertical-align:middle;'>🙏</span> "
                        + ", ".join([f"<span style='color:#388e3c;font-weight:bold'>{n}</span>" for n in sponsor_names])
                        + "</span>",
                        unsafe_allow_html=True
                    )
                # Only show sponsor checkbox if slots are available
                if remaining > 0:
                    if st.checkbox(f"Sponsor {item}", key=item):
                        selected_items.append(item)
                st.markdown("---")
            else:
                st.markdown(
                    f"""
                    <div style='background:linear-gradient(90deg,#ffe0b2 60%,#fffde7 100%); border-radius:14px; box-shadow:0 2px 12px #e0e0e0; padding:22px 28px; margin-bottom:22px; border:2px solid #ffb74d;'>
                        <div style='display:flex; align-items:center; justify-content:space-between;'>
                            <div style='font-size:1.15em; font-weight:bold; color:#d84315;'>{item}</div>
                            <div style='font-size:1.1em; color:#1565c0; font-weight:bold;'>${fmt_amt(cost)}</div>
                        </div>
                        <div style='margin:10px 0 6px 0; font-size:1.05em;'>
                            <span style='color:#388E3C;'>${fmt_amt(cost)}</span> / <span style='color:#1565c0;'>{limit}</span> = <span style='color:#388E3C;'>{fmt_amt(per_slot)}</span> per slot
                            &nbsp;|&nbsp; <span style='color:#1565c0;'>Total Slots: {limit}</span>
                            &nbsp;|&nbsp; <span style='color:#2E7D32;'>Available Slots: 0</span>
                        </div>
                        <div style='margin:10px 0 0 0; font-size:1em; color:#333;'>
                            <span style='font-weight:500;'>Sponsored Names:</span> <span style='font-size:1.1em;vertical-align:middle;'>🙏</span> {', '.join([f"<span style='color:#388e3c;font-weight:bold'>{n}</span>" for n in sponsor_names])}
                        </div>
                        <div style='margin-top:14px; padding:10px 0; background:#ffe0b2; border-radius:8px; font-size:1.08em; color:#d84315; font-weight:bold; text-align:center; box-shadow:0 1px 4px #ffe0b2;'>
                            <span style='font-size:1.12em;'>Slots are not available. This item is fully sponsored! <span style='font-size:1.1em;vertical-align:middle;'>🙏</span></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown("---")

    with tab2:
        # Show donor table before donation field
        cursor.execute("SELECT name, donation FROM sponsors WHERE donation IS NOT NULL AND donation > 0 ORDER BY donation DESC")
        donor_rows = cursor.fetchall()
        # Only show donors with donation >= 5
        donor_rows_filtered = [row for row in donor_rows if row[1] >= 5]
        if donor_rows_filtered:
            donor_table_html = f"""
<div style='background:linear-gradient(90deg,#e3f2fd 60%,#fffde7 100%); border-radius:14px; box-shadow:0 2px 12px #e0e0e0; padding:18px 24px; margin-bottom:18px; border:2px solid #90caf9;'>
    <div style='font-size:1.15em; font-weight:bold; color:#1976d2; margin-bottom:10px;'>🙏 Donors</div>
    <table style='width:100%; border-collapse:collapse; font-size:1.05em;'>
        <thead>
            <tr style='background:#bbdefb;'>
                <th style='padding:8px 12px; color:#1976d2; font-weight:600; border-bottom:2px solid #90caf9;'>Donor Name</th>
                <th style='padding:8px 12px; color:#1976d2; font-weight:600; border-bottom:2px solid #90caf9;'>Amount</th>
            </tr>
        </thead>
        <tbody>
            {''.join([f"<tr><td style='padding:8px 12px; border-bottom:1px solid #e3f2fd;'>{row[0]}</td><td style='padding:8px 12px; border-bottom:1px solid #e3f2fd; color:#388e3c; font-weight:bold;'>${row[1]}</td></tr>" for row in donor_rows_filtered])}
        </tbody>
    </table>
</div>
"""
            st.markdown(donor_table_html, unsafe_allow_html=True)
        # Only show donation input if there are available slots in any item and not in donors tab
        if 'Donors' not in st.session_state.get('active_tab', ''):
            if any((row[2] - sum([1 for s in sponsor_names if s == row[0]]) > 0) for row in items):
                donation = st.number_input("Enter donation amount (optional)", min_value=0, value=0)

    def validate_us_phone(phone):
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return True, f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return False, phone

    def format_name(name):
        return ' '.join(word.capitalize() for word in name.strip().split())

    submit_disabled = st.session_state.get('show_submission', False)
    if show_submission_inputs:
        if st.button("✅ Submit", key="sponsorship_submit", disabled=submit_disabled):
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
                        submitted_data["Contributed Amount"] = f"${contributed_amount}"
                    st.session_state['submitted_data'] = submitted_data
                    st.session_state['show_submission'] = True
                    notification_emails = get_notification_emails()
                    recipients = list(notification_emails)
                    if email.strip():
                        recipients.append(email.strip())
                    recipients = list(set(recipients))
                    email_rows = f"""
  <tr><th>Name</th><td>{name_val}</td></tr>
  <tr><th>Email</th><td>{email}</td></tr>
  <tr><th>Gothram</th><td>{gothram}</td></tr>
  <tr><th>Mobile</th><td>{phone_fmt.strip()}</td></tr>
  <tr><th>Apartment</th><td>{apartment}</td></tr>
"""
                    if selected_items:
                        format_strings = ','.join(['%s'] * len(selected_items))
                        cursor.execute(f"SELECT item, amount, sponsor_limit FROM sponsorship_items WHERE item IN ({format_strings})", tuple(selected_items))
                        item_amounts = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
                        for item in selected_items:
                            amt, limit = item_amounts.get(item, (0, 1))
                            per_item_amt = round(amt / limit, 2) if limit else amt
                            email_rows += f"  <tr><th>Sponsorship Item</th><td>{item}</td><td><b>${per_item_amt}</b></td></tr>\n"
                    if donation > 0:
                        email_rows += f"  <tr><th>Donation</th><td>General Donation</td><td><b>${donation}</b></td></tr>\n"
                    if contributed_amount:
                        email_rows += f"  <tr><th colspan='2'>Total Contributed Amount</th><td><b>${contributed_amount}</b></td></tr>\n"
                    paypal_link = st.secrets.get("paypal_link", "")
                    paypal_icon = "<img src='https://www.paypalobjects.com/webstatic/icon/pp258.png' alt='PayPal' style='height:32px;vertical-align:middle;margin-right:8px;'/>"
                    paypal_html = "<br><b>To pay your sponsorship or donation, please use the PayPal link below:</b><br>"
                    if paypal_link:
                        paypal_html += f"<a href='{paypal_link}' target='_blank'>{paypal_icon}<b>Pay via PayPal</b></a>"
                    else:
                        paypal_html += "<span style='color:#d32f2f;'>PayPal link not available.</span>"
                    paypal_html += "<br><b>For Zelle payment, pay money to any one of these persons: <span style='color:#1565C0;'>Purna Magum / Ganesh Thamma</span></b>"
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
