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
    conn = get_connection()
    cursor = conn.cursor()
    st.markdown("<h1 style='text-align: center; color: #1565C0;'>Sponsorship Statistics</h1>", unsafe_allow_html=True)

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
    st.dataframe(df)
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
        # Add total row
        df_csv_out = df_csv.copy()
        if not df_csv_out.empty:
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

    def send_csv_email(subject, body, df_csv, filename):
        import io
        cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
        recipients = list({row[0].strip() for row in cursor.fetchall() if row[0]})
        if not recipients:
            st.warning("No sponsor emails found.")
            return
        EMAIL_SENDER = st.secrets["email_sender"]
        EMAIL_PASSWORD = st.secrets["email_password"]
        SMTP_SERVER = st.secrets["smtp_server"]
        SMTP_PORT = st.secrets["smtp_port"]
        for recipient in recipients:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_SENDER
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            csv_buffer = io.StringIO()
            df_csv.to_csv(csv_buffer, index=False)
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

    if st.button("Send Sponsored Records Report (CSV)"):
        body = f"""
<b>Sponsored Records Report (CSV attached)</b><br><br>
Total records: {len(df)}<br>
Date: {datetime.date.today()}<br>
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

    # Bar chart for item total and remaining slots
    st.markdown("### 📊 Sponsorship Item Slot Distribution")
    if not df_available.empty:
        bar_data = pd.melt(
            df_available,
            id_vars=["Item"],
            value_vars=["Total Slot", "Remaining Slot Available"],
            var_name="Slot Type",
            value_name="Count"
        )
        bar_chart = alt.Chart(bar_data).mark_bar().encode(
            x=alt.X('Item:N', title='Sponsorship Item'),
            y=alt.Y('Count:Q', title='Slots'),
            color=alt.Color('Slot Type:N', title='Slot Type'),
            column=alt.Column('Slot Type:N', title=None, header=alt.Header(labelOrient='bottom')),
            tooltip=['Item', 'Slot Type', 'Count']
        ).properties(width=120, height=300)
        st.altair_chart(bar_chart, use_container_width=True)

    # Bar chart for total donation per person
    st.markdown("### 💵 Total Donation by Person")
    donation_df = raw_df.groupby("name", as_index=False)["donation"].sum()
    donation_df = donation_df[donation_df["donation"] > 0]
    if not donation_df.empty:
        donation_chart = alt.Chart(donation_df).mark_bar().encode(
            x=alt.X("name:N", title="Name", sort="-y"),
            y=alt.Y("donation:Q", title="Total Donation ($)"),
            color=alt.Color("name:N", legend=None),
            tooltip=["name", "donation"]
        ).properties(width=700)
        st.altair_chart(donation_chart, use_container_width=True)
    else:
        st.info("No donations recorded yet.")

    if st.button("Send Available Items Report (CSV)"):
        body = f"""
<b>Available Sponsorship Items Report (CSV attached)</b><br><br>
Date: {datetime.date.today()}<br>
"""
        send_csv_email(
            "Ganesh Chaturthi Sponsorship - Available Items CSV Report",
            body,
            df_available,
            f"available_items_{datetime.date.today()}.csv"
        )
        st.success("Available items report sent!")

    # Removed Bar Chart of Sponsorships as requested
