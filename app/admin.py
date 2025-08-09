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
            # Hide 'id' column in display
            display_df = df_sponsors.drop(columns=["id"])
            display_df = display_df.rename(columns={col: col.replace('_', ' ').title() for col in display_df.columns})
            st.dataframe(display_df, use_container_width=True)
            sponsor_names = df_sponsors["name"].tolist()
            selected_name = st.selectbox("Select Sponsorship Record (by Name)", sponsor_names)
            sponsor_row = df_sponsors[df_sponsors.name == selected_name].iloc[0]
            sponsor_id = int(sponsor_row["id"])
            edit_name = st.text_input("Name", value=sponsor_row["name"])
            edit_apartment = st.text_input("Apartment Number (100-1600)", value=sponsor_row["apartment"])
            edit_email = st.text_input("Email Address (optional)", value=sponsor_row["email"] or "", help="Enter Email to Subscribe the notifications to Your Email")
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
                                "UPDATE sponsors SET name=%s, email=%s, mobile=%s, apartment=%s, sponsorship=%s, donation=%s WHERE id=%s",
                                (edit_name, edit_email, phone_fmt.strip(), edit_apartment, edit_sponsorship, edit_donation, sponsor_id)
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
    elif menu == "Edit/Delete Transfer Accounts":
        st.markdown("<h2 style='color: #6A1B9A;'>✏️ Edit or Delete Transfer Account</h2>", unsafe_allow_html=True)
        df_transfers = pd.read_sql("SELECT * FROM transfers ORDER BY id", conn)
        if not df_transfers.empty:
            display_df = df_transfers.drop(columns=["id"])
            display_df = display_df.rename(columns={col: col.replace('_', ' ').title() for col in display_df.columns})
            st.dataframe(display_df, use_container_width=True)
            transfer_names = df_transfers["name"].tolist()
            selected_name = st.selectbox("Select Transfer Account (by Name)", transfer_names)
            transfer_row = df_transfers[df_transfers.name == selected_name].iloc[0]
            transfer_id = int(transfer_row["id"])
            edit_name = st.text_input("Name", value=transfer_row["name"])
            edit_phone = st.text_input("Phone", value=transfer_row["phone"] or "")
            edit_email = st.text_input("Email", value=transfer_row["email"] or "")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Transfer Account"):
                    try:
                        cursor.execute(
                            "UPDATE transfers SET name=%s, phone=%s, email=%s WHERE id=%s",
                            (edit_name, edit_phone, edit_email, transfer_id)
                        )
                        conn.commit()
                        st.success("✅ Transfer account updated!")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to update transfer account: {e}")
            with col2:
                if st.button("Delete Transfer Account"):
                    try:
                        cursor.execute("DELETE FROM transfers WHERE id=%s", (transfer_id,))
                        conn.commit()
                        st.success("🗑️ Transfer account deleted!")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to delete transfer account: {e}")
        else:
            st.info("No transfer accounts found.")
        st.markdown("<h3 style='color: #6A1B9A;'>➕ Add New Transfer Account</h3>", unsafe_allow_html=True)
        with st.form("add_transfer_admin_form"):
            new_name = st.text_input("New Name")
            new_phone = st.text_input("New Phone Number")
            new_email = st.text_input("New Email")
            if st.form_submit_button("Add Transfer Account"):
                try:
                    cursor.execute("INSERT INTO transfers (name, phone, email) VALUES (%s, %s, %s)", (new_name.strip(), new_phone.strip(), new_email.strip()))
                    conn.commit()
                    st.success("✅ New transfer account added!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add transfer account: {e}")

