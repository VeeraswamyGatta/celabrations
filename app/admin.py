import streamlit as st
TABLE_HEADER_STYLE = "background-color:#6A1B9A;color:#fff;text-transform:capitalize;"

# Custom button styles for admin section
st.markdown('''
    <style>
    .stButton > button {
        background-color: #6A1B9A !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        margin-bottom: 0.5em;
    }
    .stButton > button:hover {
        background-color: #8e24aa !important;
        color: #fff !important;
    }
    </style>
''', unsafe_allow_html=True)
import pandas as pd
from .db import get_connection
from .email_utils import send_email

def admin_tab(menu="Sponsorship Items"):
    st.session_state['active_tab'] = 'Admin'
    conn = get_connection()
    cursor = conn.cursor()
    if menu == "Payment Details":
        st.markdown("<h2 style='color: #6A1B9A;'>💳 Payment Details</h2>", unsafe_allow_html=True)
        # Fetch sponsor names and their total sponsored+donated amount
        @st.cache_data(show_spinner=False)
        def get_sponsor_df():
            df = pd.read_sql("SELECT name, SUM(COALESCE(donation,0)) AS donation_sum FROM sponsors GROUP BY name", conn)
            cursor2 = conn.cursor()
            # Calculate per-sponsor amount by dividing item amount by sponsor_limit
            cursor2.execute("""
                SELECT s.name, SUM(COALESCE(si.amount,0) / NULLIF(si.sponsor_limit,0))
                FROM sponsors s
                JOIN sponsorship_items si ON si.item = s.sponsorship
                GROUP BY s.name
            """)
            sponsor_amt = {row[0]: float(row[1]) for row in cursor2.fetchall()}
            df["sponsorship_sum"] = df["name"].map(sponsor_amt).fillna(0).astype(float)
            df["donation_sum"] = df["donation_sum"].astype(float)
            df["total_amount"] = df["donation_sum"] + df["sponsorship_sum"]
            return df
        sponsor_df = get_sponsor_df()
        sponsor_names = sorted(sponsor_df["name"].tolist())
        # Tabs for Received and Not Received
        tab1, tab2 = st.tabs(["Received", "Not Received"])

        with tab1:
            # Received: Payment details table
            df_pay = pd.read_sql("SELECT id, name, amount, date, comments, payment_type FROM payment_details ORDER BY date DESC, id DESC", conn)
            if not df_pay.empty:
                display_df = df_pay.drop(columns=["id"])
                display_df = display_df.sort_values(by=["name"])  # Sort by Name
                st.dataframe(display_df, use_container_width=True)
                total_amount = display_df["amount"].sum()
                st.markdown(f"<div style='text-align:right; font-size:1.1em; margin-top:0.5em;'><b>Total Amount:</b> <span style='color:#6A1B9A;'>${total_amount:,.2f}</span></div>", unsafe_allow_html=True)
                csv = display_df.to_csv(index=False)
                st.download_button("Export as CSV", csv, file_name="payment_details.csv", mime="text/csv")
            else:
                st.info("No payment details found.")

        with tab2:
            # Not Received: Names/Amounts not in payment_details
            df_pay = pd.read_sql("SELECT name FROM payment_details", conn)
            paid_names = set(df_pay["name"].tolist())
            not_received_df = sponsor_df[~sponsor_df["name"].isin(paid_names)][["name", "total_amount"]]
            not_received_df = not_received_df.rename(columns={"name": "Name", "total_amount": "Amount"})
            not_received_df = not_received_df.sort_values(by=["Name"])  # Sort by Name
            st.dataframe(not_received_df, use_container_width=True)
            st.markdown(f"<div style='text-align:right; font-size:1.1em; margin-top:0.5em;'><b>Total Not Received:</b> <span style='color:#6A1B9A;'>${not_received_df['Amount'].sum():,.2f}</span></div>", unsafe_allow_html=True)

        # Add Payment Detail section next
        st.markdown("<h3 style='color: #6A1B9A;'>➕ Add Payment Detail</h3>", unsafe_allow_html=True)
        if 'add_pay_selected_name' not in st.session_state:
            st.session_state['add_pay_selected_name'] = sponsor_names[0] if sponsor_names else ''
        if 'add_pay_payment_type' not in st.session_state:
            st.session_state['add_pay_payment_type'] = 'PayPal'
        def update_amount():
            name = st.session_state['add_pay_selected_name']
            amt = float(sponsor_df[sponsor_df["name"] == name]["total_amount"].values[0]) if name in sponsor_names else 0.0
            st.session_state['add_pay_amount'] = amt
        name = st.selectbox("Name", sponsor_names, key="add_pay_selected_name", on_change=update_amount)
        payment_type = st.selectbox("Payment Type", ["PayPal", "Zelle"], key="add_pay_payment_type")
        if 'add_pay_amount' not in st.session_state or st.session_state['add_pay_selected_name'] != name:
            update_amount()
        amount = st.session_state.get('add_pay_amount', 0.0)
        st.write(f"Amount: **${amount:,.2f}**")
        with st.form("add_payment_detail_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Name: **{name}**")
                st.write(f"Amount: **${amount:,.2f}**")
                st.write(f"Payment Type: **{payment_type}**")
            with col2:
                date = st.date_input("Date", key="add_pay_date")
                comments = st.text_input("Comments", key="add_pay_comments")
            if st.form_submit_button("Add Payment Detail"):
                try:
                    cursor.execute(
                        "INSERT INTO payment_details (name, amount, date, comments, payment_type) VALUES (%s, %s, %s, %s, %s)",
                        (name, amount, date, comments, payment_type)
                    )
                    conn.commit()
                    st.success("✅ Payment detail added!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add payment detail: {e}")

        # Delete Payment Detail section last
        df_pay = pd.read_sql("SELECT id, name, amount, date, comments FROM payment_details ORDER BY date DESC, id DESC", conn)
        if not df_pay.empty:
            st.markdown("<h3 style='color: #6A1B9A;'>🗑️ Delete Payment Detail</h3>", unsafe_allow_html=True)
            pay_names = df_pay["name"].tolist()
            selected_name = st.selectbox("Select Payment Record (by Name)", pay_names)
            pay_row = df_pay[df_pay.name == selected_name].iloc[0]
            pay_id = int(pay_row["id"])
            # Display details in readable format
            st.markdown(f"""
<div style='border:1px solid #ccc; border-radius:8px; padding:1em; margin-bottom:1em;'>
<b>Name:</b> {pay_row['name']}<br>
<b>Amount:</b> ${pay_row['amount']:,.2f}<br>
<b>Date:</b> {pay_row['date']}<br>
<b>Comments:</b> {pay_row['comments'] or ''}
</div>
""", unsafe_allow_html=True)
            if st.button("Delete Payment Detail"):
                try:
                    cursor.execute("DELETE FROM payment_details WHERE id=%s", (pay_id,))
                    conn.commit()
                    st.success("🗑️ Payment detail deleted!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to delete payment detail: {e}")
        return

    if menu == "Sponsorship Items":
        st.markdown("<h2 style='color: #6A1B9A;'>Sponsorship Items Overview</h2>", unsafe_allow_html=True)
        df = pd.read_sql("SELECT * FROM sponsorship_items ORDER BY id", conn)
        st.dataframe(df)

        st.markdown("<h3 style='color: #6A1B9A;'>✏️ Edit Existing Item</h3>", unsafe_allow_html=True)
        item_id = st.selectbox("Select Item ID", df["id"].tolist())
        item_row = df[df.id == item_id].iloc[0]
        new_item_name = st.text_input("Item Name", value=item_row["item"])
        st.write(f"Amount: ${float(item_row['amount']):,.2f}")
        st.write(f"Limit: {int(item_row['sponsor_limit'])}")

        if st.button("Update Item"):
            try:
                cursor.execute("UPDATE sponsorship_items SET item=%s WHERE id=%s",
                               (new_item_name, item_id))
                conn.commit()
                st.success("✅ Item updated successfully!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Failed to update: {e}")

        st.markdown("<h3 style='color: #6A1B9A;'>➕ Add New Sponsorship Item</h3>", unsafe_allow_html=True)
        with st.form("add_item_form"):
            new_name = st.text_input("New Item Name")
            new_amt = st.number_input("Amount", min_value=0)
            new_lim = st.number_input("Limit", min_value=1, value=3)
            if st.form_submit_button("Add Item"):
                try:
                    cursor.execute("INSERT INTO sponsorship_items (item, amount, sponsor_limit) VALUES (%s, %s, %s)",
                                   (new_name, new_amt, new_lim))
                    conn.commit()
                    st.success("✅ New item added!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add item: {e}")

    elif menu == "Sponsorship Record":
        st.markdown("<h2 style='color: #6A1B9A;'>✏️ Edit Sponsorship Record</h2>", unsafe_allow_html=True)
        df_sponsors = pd.read_sql("SELECT * FROM sponsors ORDER BY id", conn)
        if not df_sponsors.empty:
            # Add Type column
            display_df = df_sponsors.copy()
            def get_type(row):
                if row['sponsorship'] and str(row['sponsorship']).strip():
                    return 'Sponsorship'
                elif row['donation'] and float(row['donation']) > 0:
                    return 'Donation'
                else:
                    return ''
            display_df['Type'] = display_df.apply(get_type, axis=1)
            # Pre-fetch sponsorship item amounts into a dict
            cursor.execute("SELECT item, amount, sponsor_limit FROM sponsorship_items")
            item_amounts = {}
            for row in cursor.fetchall():
                item, amount, sponsor_limit = row
                try:
                    per_sponsor = float(amount) / int(sponsor_limit) if sponsor_limit else float(amount)
                except Exception:
                    per_sponsor = float(amount)
                item_amounts[item] = per_sponsor
            # Compute a single amount column
            def get_amount(row):
                if row['Type'] == 'Sponsorship':
                    item = row['sponsorship']
                    return item_amounts.get(item, 0.0) if item else 0.0
                elif row['Type'] == 'Donation':
                    try:
                        return float(row['donation']) if row['donation'] not in (None, '', 0, '0') else 0.0
                    except:
                        return 0.0
                return 0.0
            display_df['Donation/Sponsorship Amount'] = display_df.apply(get_amount, axis=1)
            # Remove original 'sponsorship', 'donation', and 'id' columns
            display_df = display_df.drop(columns=['sponsorship', 'donation', 'id'])
            # Reorder columns
            col_order = ['name', 'email', 'mobile', 'apartment', 'gothram', 'Type', 'Donation/Sponsorship Amount']
            display_df = display_df[[c for c in col_order if c in display_df.columns]]
            display_df = display_df.rename(columns={col: col.replace('_', ' ').title() for col in display_df.columns})
            st.dataframe(display_df, use_container_width=True)
            sponsor_names = df_sponsors["name"].tolist()
            selected_name = st.selectbox("Select Sponsorship Record (by Name)", sponsor_names)
            sponsor_row = df_sponsors[df_sponsors.name == selected_name].iloc[0]
            sponsor_id = int(sponsor_row["id"])
            # Read-only mandatory and requested fields in plain text
            st.write(f"Name: {sponsor_row['name']}")
            st.write(f"Apartment Number: {sponsor_row['apartment']}")
            st.write(f"Sponsorship Item: {sponsor_row['sponsorship'] if sponsor_row['sponsorship'] else 'N/A'}")
            st.write(f"Donation: ${float(sponsor_row['donation'] or 0):,.2f}")
            # Editable optional fields
            edit_email = st.text_input("Email Address (optional)", value=sponsor_row["email"] or "", help="Enter Email to Subscribe the notifications to Your Email")
            edit_gothram = st.text_input("Gothram (optional)", value=sponsor_row["gothram"] if "gothram" in sponsor_row and sponsor_row["gothram"] is not None else "", key=f"edit_gothram_{sponsor_id}")
            edit_mobile = st.text_input("Mobile (optional, US format)", value=sponsor_row["mobile"] or "")
            if st.button("Update Sponsorship Record"):
                errors = []
                # Email validation
                if edit_email.strip():
                    if '@' not in edit_email or not edit_email.strip().lower().endswith('.com'):
                        errors.append("Please enter a valid email address (must contain '@' and end with .com)")
                # Mobile validation (optional, US format)
                import re
                def validate_us_phone(phone):
                    digits = re.sub(r'\D', '', phone)
                    if len(digits) == 10:
                        return True, f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                    return False, phone
                phone_valid, phone_fmt = True, edit_mobile
                if edit_mobile.strip():
                    phone_valid, phone_fmt = validate_us_phone(edit_mobile)
                    if not phone_valid:
                        errors.append("Please enter a valid 10-digit US phone number.")
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    try:
                        cursor.execute(
                            "UPDATE sponsors SET email=%s, mobile=%s, gothram=%s WHERE id=%s",
                            (edit_email, phone_fmt.strip(), edit_gothram, sponsor_id)
                        )
                        conn.commit()
                        st.success("✅ Sponsorship record updated!")
                        # Send to all unique sponsor emails
                        cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                        sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                        send_email(
                            "Ganesh Chaturthi Celebrations Sponsorship Program in Austin Texas",
                            f"""
<b>Sponsorship Record Updated</b><br><br>
<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
        <tr><th style='{TABLE_HEADER_STYLE}'>Name</th><td>{sponsor_row['name']}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Email</th><td>{edit_email}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Gothram</th><td>{edit_gothram}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Mobile</th><td>{phone_fmt.strip()}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Apartment</th><td>{sponsor_row['apartment']}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Sponsorship Item</th><td>{sponsor_row['sponsorship'] if sponsor_row['sponsorship'] else 'N/A'}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Donation</th><td>${float(sponsor_row['donation'] or 0):,.2f}</td></tr>
</table>
""",
                            sponsor_emails
                        )
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to update sponsorship: {e}")
        else:
            st.info("No sponsorship records found.")
    elif menu == "Manage Notification Emails":
        st.markdown("<h2 style='color: #6A1B9A;'>✉️ Manage Notification Emails</h2>", unsafe_allow_html=True)
        df_emails = pd.read_sql("SELECT * FROM notification_emails ORDER BY id", conn)
        if not df_emails.empty:
            display_emails = df_emails.drop(columns=["id"])
            st.dataframe(display_emails, use_container_width=True)
            email_list = df_emails["email"].tolist()
            selected_email = st.selectbox("Select Email to Edit/Delete", email_list)
            email_row = df_emails[df_emails.email == selected_email].iloc[0]
            email_id = int(email_row["id"])
            edit_email_val = st.text_input("Edit Email", value=email_row["email"], key="edit_notification_email")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Notification Email"):
                    try:
                        cursor.execute("UPDATE notification_emails SET email=%s WHERE id=%s", (edit_email_val.strip(), email_id))
                        conn.commit()
                        st.success("✅ Notification email updated!")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to update notification email: {e}")
            with col2:
                if st.button("Delete Notification Email"):
                    try:
                        cursor.execute("DELETE FROM notification_emails WHERE id=%s", (email_id,))
                        conn.commit()
                        st.success("🗑️ Notification email deleted!")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to delete notification email: {e}")
        else:
            st.info("No notification emails found.")
        st.markdown("<h3 style='color: #6A1B9A;'>➕ Add Notification Email</h3>", unsafe_allow_html=True)
        with st.form("add_notification_email_form"):
            new_email_val = st.text_input("New Notification Email")
            if st.form_submit_button("Add Notification Email"):
                try:
                    cursor.execute("INSERT INTO notification_emails (email) VALUES (%s)", (new_email_val.strip(),))
                    conn.commit()
                    st.success("✅ New notification email added!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add notification email: {e}")

