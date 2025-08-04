import streamlit as st
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

    df = pd.read_sql("SELECT name, email, mobile, sponsorship, donation FROM sponsors ORDER BY id", conn)
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
            "Total Slots": limit,
            "Remaining Slots": remaining
        })
    df_available = pd.DataFrame(available_data)
    st.markdown("### 📋 Available Sponsorship Items")
    st.dataframe(df_available)

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

    st.markdown("### 📊 Bar Chart of Sponsorships")
    chart_data = df["sponsorship"].value_counts().reset_index()
    chart_data.columns = ["Sponsorship", "Count"]

    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("Sponsorship", sort="-y"),
        y="Count",
        tooltip=["Sponsorship", "Count"]
    ).properties(width=700)

    st.altair_chart(chart, use_container_width=True)
