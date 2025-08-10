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
    if menu == "PayPal Payment Details":
        st.markdown("<h2 style='color: #6A1B9A;'>💳 PayPal Payment Details</h2>", unsafe_allow_html=True)
        # Display table
        df_pay = pd.read_sql("SELECT id, name, amount, date, comments FROM payment_details ORDER BY date DESC, id DESC", conn)
        if not df_pay.empty:
            display_df = df_pay.drop(columns=["id"])
            st.dataframe(display_df, use_container_width=True)
            # Show total amount below the table
            total_amount = display_df["amount"].sum()
            st.markdown(f"<div style='text-align:right; font-size:1.1em; margin-top:0.5em;'><b>Total Amount:</b> <span style='color:#6A1B9A;'>${total_amount:,.2f}</span></div>", unsafe_allow_html=True)
            csv = display_df.to_csv(index=False)
            st.download_button("Export as CSV", csv, file_name="payment_details.csv", mime="text/csv")
            # Edit/Delete section
            st.markdown("<h3 style='color: #6A1B9A;'>✏️ Edit or Delete Payment Detail</h3>", unsafe_allow_html=True)
            pay_names = df_pay["name"].tolist()
            selected_name = st.selectbox("Select Payment Record (by Name)", pay_names)
            pay_row = df_pay[df_pay.name == selected_name].iloc[0]
            pay_id = int(pay_row["id"])
            col1, col2 = st.columns(2)
            with col1:
                edit_name = st.text_input("Name", value=pay_row["name"])
                edit_amount = st.number_input("Amount", min_value=0.0, value=float(pay_row["amount"]), format="%.2f")
            with col2:
                edit_date = st.date_input("Date", value=pay_row["date"])
                edit_comments = st.text_input("Comments", value=pay_row["comments"] or "")
            col3, col4 = st.columns(2)
            with col3:
                if st.button("Update Payment Detail"):
                    try:
                        cursor.execute(
                            "UPDATE payment_details SET name=%s, amount=%s, date=%s, comments=%s WHERE id=%s",
                            (edit_name, edit_amount, edit_date, edit_comments, pay_id)
                        )
                        conn.commit()
                        st.success("✅ Payment detail updated!")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to update payment detail: {e}")
            with col4:
                if st.button("Delete Payment Detail"):
                    try:
                        cursor.execute("DELETE FROM payment_details WHERE id=%s", (pay_id,))
                        conn.commit()
                        st.success("🗑️ Payment detail deleted!")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to delete payment detail: {e}")
        else:
            st.info("No payment details found.")
        # Add new payment detail
        st.markdown("<h3 style='color: #6A1B9A;'>➕ Add Payment Detail</h3>", unsafe_allow_html=True)
        with st.form("add_payment_detail_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name", key="add_pay_name")
                amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="add_pay_amount")
            with col2:
                date = st.date_input("Date", key="add_pay_date")
                comments = st.text_input("Comments", key="add_pay_comments")
            if st.form_submit_button("Add Payment Detail"):
                try:
                    cursor.execute(
                        "INSERT INTO payment_details (name, amount, date, comments) VALUES (%s, %s, %s, %s)",
                        (name, amount, date, comments)
                    )
                    conn.commit()
                    st.success("✅ Payment detail added!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add payment detail: {e}")
        return

    if menu == "Sponsorship Items":
        st.markdown("<h2 style='color: #6A1B9A;'>Sponsorship Items Overview</h2>", unsafe_allow_html=True)
        df = pd.read_sql("SELECT * FROM sponsorship_items ORDER BY id", conn)
        st.dataframe(df)

        st.markdown("<h3 style='color: #6A1B9A;'>✏️ Edit Existing Item</h3>", unsafe_allow_html=True)
        item_id = st.selectbox("Select Item ID", df["id"].tolist())
        item_row = df[df.id == item_id].iloc[0]
        new_item_name = st.text_input("Item Name", value=item_row["item"])
        new_amount = st.number_input("Amount", value=float(item_row["amount"]))
        new_limit = st.number_input("Limit", value=int(item_row["sponsor_limit"]))

        if st.button("Update Item"):
            try:
                cursor.execute("UPDATE sponsorship_items SET item=%s, amount=%s, sponsor_limit=%s WHERE id=%s",
                               (new_item_name, new_amount, new_limit, item_id))
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

        st.markdown("<h3 style='color: #6A1B9A;'>🗑️ Delete Item</h3>", unsafe_allow_html=True)
        del_item = st.selectbox("Select Item to Delete", df["item"].tolist())
        if st.button("Delete Item"):
            try:
                cursor.execute("DELETE FROM sponsors WHERE sponsorship = %s", (del_item,))
                cursor.execute("DELETE FROM sponsorship_items WHERE item = %s", (del_item,))
                conn.commit()
                st.success("✅ Item and related sponsorships deleted!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Failed to delete item: {e}")

    elif menu == "Edit/Delete Sponsorship Record":
        st.markdown("<h2 style='color: #6A1B9A;'>✏️ Edit or Delete Sponsorship Record</h2>", unsafe_allow_html=True)
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
            # Show total amount
            total_amt = display_df['Donation/Sponsorship Amount'].sum()
            # Total display removed as requested
            sponsor_names = df_sponsors["name"].tolist()
            selected_name = st.selectbox("Select Sponsorship Record (by Name)", sponsor_names)
            sponsor_row = df_sponsors[df_sponsors.name == selected_name].iloc[0]
            sponsor_id = int(sponsor_row["id"])
            edit_name = st.text_input("Name", value=sponsor_row["name"])
            edit_apartment = st.text_input("Apartment Number (100-1600)", value=sponsor_row["apartment"])
            edit_email = st.text_input("Email Address (optional)", value=sponsor_row["email"] or "", help="Enter Email to Subscribe the notifications to Your Email")
            edit_gothram = st.text_input("Gothram (optional)", value=sponsor_row["gothram"] if "gothram" in sponsor_row and sponsor_row["gothram"] is not None else "", key=f"edit_gothram_{sponsor_id}")
            edit_mobile = st.text_input("Mobile (optional, US format)", value=sponsor_row["mobile"] or "")
            cursor.execute("SELECT item FROM sponsorship_items ORDER BY id")
            sponsorship_options = [row[0] for row in cursor.fetchall()]
            sponsorship_options = [None] + sponsorship_options
            edit_sponsorship = st.selectbox("Sponsorship Item (optional)", sponsorship_options, index=sponsorship_options.index(sponsor_row["sponsorship"]) if sponsor_row["sponsorship"] in sponsorship_options else 0)
            edit_donation = st.number_input("Donation (optional)", min_value=0.0, value=float(sponsor_row["donation"] or 0))
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Sponsorship Record"):
                    errors = []
                    # Apartment validation
                    if not edit_apartment.strip():
                        errors.append("Apartment Number is required.")
                    else:
                        try:
                            apt_num = int(edit_apartment.strip())
                            if not (100 <= apt_num <= 1600):
                                errors.append("Apartment Number must be between 100 and 1600.")
                        except ValueError:
                            errors.append("Apartment Number must be a number between 100 and 1600.")
                    # Email validation
                    if edit_email.strip():
                        if '@' not in edit_email or not edit_email.strip().lower().endswith('.com'):
                            errors.append("Please enter a valid email address (must contain '@' and end with .com)")
                    # Donation/item validation
                    if (not edit_sponsorship or edit_sponsorship is None) and (edit_donation is None or edit_donation == 0.0):
                        errors.append("Please select at least one Sponsorship Item or enter a Donation amount.")
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
                                "UPDATE sponsors SET name=%s, email=%s, mobile=%s, apartment=%s, gothram=%s, sponsorship=%s, donation=%s WHERE id=%s",
                                (edit_name, edit_email, phone_fmt.strip(), edit_apartment, edit_gothram, edit_sponsorship, edit_donation, sponsor_id)
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
        <tr><th style='{TABLE_HEADER_STYLE}'>Name</th><td>{edit_name}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Email</th><td>{edit_email}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Gothram</th><td>{edit_gothram}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Mobile</th><td>{phone_fmt.strip()}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Apartment</th><td>{edit_apartment}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Sponsorship Item</th><td>{edit_sponsorship if edit_sponsorship else 'N/A'}</td></tr>
        <tr><th style='{TABLE_HEADER_STYLE}'>Donation</th><td>${edit_donation}</td></tr>
</table>
""",
                                sponsor_emails
                            )
                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ Failed to update sponsorship: {e}")
            with col2:
                if st.button("Delete Sponsorship Record"):
                    try:
                        cursor.execute("DELETE FROM sponsors WHERE id=%s", (sponsor_id,))
                        conn.commit()
                        st.success("🗑️ Sponsorship record deleted!")
                        cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                        sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                        send_email(
                            "Ganesh Chaturthi Celebrations Sponsorship Program in Austin Texas",
                            f"""
<b>Sponsorship Record Deleted</b><br><br>
<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
  <tr><th style='{TABLE_HEADER_STYLE}'>Name</th><td>{sponsor_row['name']}</td></tr>
  <tr><th style='{TABLE_HEADER_STYLE}'>Email</th><td>{sponsor_row['email']}</td></tr>
  <tr><th style='{TABLE_HEADER_STYLE}'>Mobile</th><td>{sponsor_row['mobile']}</td></tr>
  <tr><th style='{TABLE_HEADER_STYLE}'>Apartment</th><td>{sponsor_row['apartment']}</td></tr>
  <tr><th style='{TABLE_HEADER_STYLE}'>Sponsorship Item</th><td>{sponsor_row['sponsorship'] if sponsor_row['sponsorship'] else 'N/A'}</td></tr>
  <tr><th style='{TABLE_HEADER_STYLE}'>Donation</th><td>${sponsor_row['donation']}</td></tr>
</table>
""",
                            sponsor_emails
                        )
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to delete sponsorship: {e}")
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

