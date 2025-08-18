import streamlit as st

# Custom button styles for statistics section
st.markdown('''
    <style>
    .stButton > button {
        background-color: #1565C0 !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        margin-bottom: 0.5em;
    }
    .stButton > button:hover {
        background-color: #1976d2 !important;
        color: #fff !important;
    }
    </style>
''', unsafe_allow_html=True)
import pandas as pd
import datetime
from .db import get_connection
from .email_utils import send_email
import altair as alt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def statistics_tab():
    # --- Combined PayPal + Zelle Total ---    
    st.session_state['active_tab'] = 'Statistics'
    is_admin = st.session_state.get('is_admin', False)
    # --- Audit trail: Your Full Name ---
    st.markdown("<h1 style='text-align: center; color: #1565C0;'>Sponsorship Statistics</h1>", unsafe_allow_html=True)
    # Removed audit trail full name requirement as requested
    # (Removed duplicate display of audit name in statistics page)
    conn = get_connection()
    cursor = conn.cursor()

    # Build sponsorship records with type and split item/donation, and show correct sponsored amount
    raw_df = pd.read_sql("SELECT name, email, mobile, sponsorship, donation FROM sponsors ORDER BY id", conn)
    # Get sponsorship item amounts and limits for per-slot calculation
    cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items")
    item_amt_map = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    records = []
    for _, row in raw_df.iterrows():
        if row['sponsorship']:
            amt, limit = item_amt_map.get(row['sponsorship'], (0, 1))
            per_item_amt = round(amt / limit, 2) if limit else amt
            records.append({
                'Name': row['name'],
                'Email': row['email'],
                'Mobile': row['mobile'],
                'Type': 'Sponsored',
                'Item/Donation': row['sponsorship'],
                'Amount': per_item_amt
            })
        if row['donation'] and row['donation'] > 0:
            records.append({
                'Name': row['name'],
                'Email': row['email'],
                'Mobile': row['mobile'],
                'Type': 'Donation',
                'Item/Donation': 'General Donation',
                'Amount': row['donation']
            })
    df = pd.DataFrame(records)
    st.markdown("### 📋 Sponsorship Records")
    df_display = df.copy()
    if not is_admin:
        # Hide email and mobile columns for users
        df_display = df_display.drop(columns=[col for col in ['Email', 'Mobile'] if col in df_display.columns])
    if 'Name' in df_display.columns:
        df_display = df_display.sort_values(by=["Name"]).reset_index(drop=True)
    df_display.index = range(1, len(df_display) + 1)
    st.dataframe(df_display)
    # Add total row at the bottom
    if not df.empty:
        df_amt = df.copy()
        df_amt['Amount'] = df_amt['Amount'].apply(lambda x: float(x))
        total_amt = df_amt['Amount'].sum()
        st.markdown(f"<div style='font-size:1.1em; color:#1565C0; font-weight:bold; margin-top:0.5em;'>Total Amount (All Records): <span style='color:#2E7D32;'>{total_amt:,.2f}</span></div>", unsafe_allow_html=True)

    # Add total row to CSV export
    def send_csv_email(subject, body, df_csv, filename):
        import io
        cursor.execute("SELECT email FROM notification_emails WHERE email IS NOT NULL AND email != ''")
        recipients = list({row[0].strip() for row in cursor.fetchall() if row[0]})
        if not recipients:
            st.warning("No notification emails found.")
            return
        EMAIL_SENDER = st.secrets["email_sender"]
        EMAIL_PASSWORD = st.secrets["email_password"]
        SMTP_SERVER = st.secrets["smtp_server"]
        SMTP_PORT = st.secrets["smtp_port"]
        # Add total row and sort by Name
        df_csv_out = df_csv.copy()
        if not df_csv_out.empty:
            if 'Name' in df_csv_out.columns:
                df_csv_out = df_csv_out.sort_values(by=["Name"]).reset_index(drop=True)
            df_csv_out['Amount'] = df_csv_out['Amount'].apply(lambda x: float(x))
            total_amt = df_csv_out['Amount'].sum()
            total_row = {col: '' for col in df_csv_out.columns}
            total_row['Name'] = 'TOTAL'
            total_row['Amount'] = total_amt
            df_csv_out = pd.concat([df_csv_out, pd.DataFrame([total_row])], ignore_index=True)
        for recipient in recipients:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_SENDER
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            csv_buffer = io.StringIO()
            df_csv_out.to_csv(csv_buffer, index=False)
            part = MIMEText(csv_buffer.getvalue(), 'csv')
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
            try:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                    server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
            except Exception as e:
                st.error(f"Failed to send email to {recipient}: {e}")

    if is_admin:
        if st.button("Send Sponsored Records Report (CSV)"):
            audit_name = st.session_state.get('admin_full_name', '')
            body = f"""
    <b>Sponsored Records Report (CSV attached)</b><br><br>
    Total records: {len(df)}<br>
    Date: {datetime.date.today()}<br>
    Triggered Report by: <b>{audit_name}</b><br>
    """
            send_csv_email(
                "Ganesh Chaturthi Sponsorship - Sponsored Records CSV Report",
                body,
                df,
                f"sponsored_records_{datetime.date.today()}.csv"
            )
            st.success("Sponsored records report sent!")

    # Available items report
    cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items ORDER BY id")
    items = cursor.fetchall()
    cursor.execute("SELECT sponsorship, COUNT(*) FROM sponsors GROUP BY sponsorship")
    counts = dict(cursor.fetchall())
    available_data = []
    for item, amount, limit in items:
        count = counts.get(item, 0)
        remaining = limit - count
        available_data.append({
            "Item": item,
            "Amount": amount,
            "Total Slot": limit,
            "Remaining Slot Available": remaining
        })
    df_available = pd.DataFrame(available_data)

    st.markdown("### 📋 Available Sponsorship Items")
    st.dataframe(df_available)

    # Move the CSV export button here
    if is_admin:
        if st.button("Send Available Items Report (CSV)", key="available_items_csv_btn"):
            audit_name = st.session_state.get('admin_full_name', '')
            body = f"""
    <b>Available Sponsorship Items Report (CSV attached)</b><br><br>
    Date: {datetime.date.today()}<br>
    Triggered Report by: <b>{audit_name}</b><br>
    """
            send_csv_email(
                "Ganesh Chaturthi Sponsorship - Available Items CSV Report",
                body,
                df_available,
                f"available_items_{datetime.date.today()}.csv"
            )
            st.success("Available items report sent!")


    # Bar chart for total contribution per person (sponsorship + donation)
    st.markdown("### 📊 Total Contribution by Person")
    # Prepare grouped data for sponsorship and donation
    contrib_data = {}
    for _, row in raw_df.iterrows():
        name = row['name']
        # Sponsorship amount (apply limit calculation)
        spon_amt = 0
        if row['sponsorship']:
            amt, limit = item_amt_map.get(row['sponsorship'], (0, 1))
            spon_amt = round(amt / limit, 2) if limit else amt
        # Donation amount
        don_amt = row['donation'] if row['donation'] else 0
        if name not in contrib_data:
            contrib_data[name] = {'Sponsorship Amount': 0, 'Donation Amount': 0}
        contrib_data[name]['Sponsorship Amount'] += spon_amt
        contrib_data[name]['Donation Amount'] += don_amt
    # Build DataFrame for chart
    contrib_df = pd.DataFrame([
        {
            'Name': name,
            'Sponsorship Amount': float(v['Sponsorship Amount']),
            'Donation Amount': float(v['Donation Amount']),
            'Total Contribution': float(v['Sponsorship Amount']) + float(v['Donation Amount'])
        }
        for name, v in contrib_data.items()
    ])
    if not contrib_df.empty:
        chart_df = contrib_df.melt(id_vars=['Name'], value_vars=['Sponsorship Amount', 'Donation Amount'], var_name='Type', value_name='Amount')
        # Set y-axis to have a step of 10 for amount range
        min_amt = chart_df['Amount'].min() if not chart_df['Amount'].empty else 0
        max_amt = chart_df['Amount'].max() if not chart_df['Amount'].empty else 10
        # Responsive chart width for mobile
        chart_width = 700
        # If running on mobile, reduce chart width (pseudo-code, Streamlit does not provide direct device detection)
        # You may use st.container() or st.columns for better mobile layout if needed
        # chart_width = 350 if is_mobile else 700
        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X('Name:N', title='Name', sort='-y'),
            y=alt.Y('Amount:Q', title='Amount ($)', scale=alt.Scale(domain=[min_amt, max_amt], nice=True)),
            color=alt.Color('Type:N', title='Type'),
            tooltip=['Name', 'Type', 'Amount']
        ).properties(width=chart_width)
        chart = chart.configure_axis(
            grid=True,
            tickCount=round((max_amt-min_amt)/5) if max_amt > min_amt else 5
        )
        st.altair_chart(chart, use_container_width=True)

        # Calculate unique contributors for sponsors and donations
        sponsor_names = set(raw_df[raw_df['sponsorship'].notnull()]['name'])
        donation_names = set(raw_df[(raw_df['donation'] > 0) & raw_df['donation'].notnull()]['name'])
        total_sponsors = len(sponsor_names)
        total_donors = len(donation_names)
        total_contributors = len(sponsor_names.union(donation_names))

        st.markdown(f"<div style='font-size:1em; color:#1565C0; font-weight:bold; margin-top:0.5em;'>Total Contributors (Sponsors + Donations) = {total_sponsors} + {total_donors} = <span style='color:#2E7D32;'>{total_contributors}</span></div>", unsafe_allow_html=True)
    else:
        st.info("No contributions recorded yet.")



    # Removed Bar Chart of Sponsorships as requested
