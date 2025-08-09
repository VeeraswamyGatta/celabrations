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
    st.session_state['active_tab'] = 'Statistics'
    conn = get_connection()
    cursor = conn.cursor()
    st.markdown("<h1 style='text-align: center; color: #1565C0;'>Sponsorship Statistics</h1>", unsafe_allow_html=True)

    # Build sponsorship records with type and split item/donation
    raw_df = pd.read_sql("SELECT name, email, mobile, sponsorship, donation FROM sponsors ORDER BY id", conn)
    records = []
    for _, row in raw_df.iterrows():
        if row['sponsorship']:
            records.append({
                'Name': row['name'],
                'Email': row['email'],
                'Mobile': row['mobile'],
                'Sponsorship Type': 'Item',
                'Item/Donation': row['sponsorship'],
                'Amount': ''
            })
        if row['donation'] and row['donation'] > 0:
            records.append({
                'Name': row['name'],
                'Email': row['email'],
                'Mobile': row['mobile'],
                'Sponsorship Type': 'Donation',
                'Item/Donation': 'General Donation',
                'Amount': f"${row['donation']}"
            })
    df = pd.DataFrame(records)
    st.markdown("### 📋 Sponsorship Records")
    st.dataframe(df)

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
