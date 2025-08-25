import streamlit as st
import pandas as pd
import datetime
from .db import get_connection
import io


def expenses_tab():
    # --- Clear Add Expense form fields if needed ---
    if st.session_state.get("clear_expense_form", False):
        st.session_state["add_expense_category"] = ""
        st.session_state["add_expense_subcat"] = ""
        st.session_state["add_expense_amount"] = 0.0
        st.session_state["add_expense_date"] = datetime.date.today()
        st.session_state["add_expense_spentby"] = ""
        st.session_state["add_expense_comments"] = ""
    # File uploader cannot be cleared programmatically; do not show info to user
        st.session_state["clear_expense_form"] = False
        st.rerun()
    conn = get_connection()
    cursor = conn.cursor()
    # Calculate wallet and expenses totals
    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payment_details")
    total_payments = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE status='active'")
    total_expenses = cursor.fetchone()[0]
    wallet_amount = total_payments - total_expenses
    blink_color = 'red' if wallet_amount < 500 else 'green'
    st.markdown(f"""
    <div style='font-size:1.3em; font-weight:bold; margin-bottom:10px;'>
        Available Amount in Wallet (Total Received Amount - Total Expense Amount): {total_payments:.2f} - {total_expenses:.2f} = <span style='background: {blink_color}; color: white; padding: 4px 12px; border-radius: 8px; animation: blink 1s linear infinite;'>{wallet_amount:.2f}</span>
    </div>
    <style>
    @keyframes blink {{
      0% {{ opacity: 1; }}
      50% {{ opacity: 0.2; }}
      100% {{ opacity: 1; }}
    }}
    span[style*='animation: blink'] {{ animation: blink 1s linear infinite; }}
    </style>
    """, unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #6D4C41;'>Expenses</h1>", unsafe_allow_html=True)

    # Fetch expenses data
    st.markdown("### Expenses")
    cursor.execute("SELECT id, category, sub_category, amount, date, spent_by, comments, receipt_path, receipt_blob FROM expenses WHERE status='active' ORDER BY category, sub_category")
    rows = cursor.fetchall()
    columns = ["ID", "Category", "Sub Category", "Amount", "Date", "Spent By", "Comments", "Receipt", "Receipt Blob"]
    df = pd.DataFrame(rows, columns=columns)
    def format_comments(comments):
        if not comments:
            return ""
        import re
        # Split comments by newlines or pipes, keep each line separate
        lines = re.split(r'[\n|]+', comments)
        return lines
    df["Comments"] = df["Comments"].apply(format_comments)

    # Tabs for Expenses List, Receipts, and Expense Summary
    # Determine tabs to show based on user role
    is_admin = st.session_state.get("admin_logged_in", False)
    if is_admin:
        tabs = ["Add Expense", "Expenses List", "Receipts", "Expense Summary by Person", "Edit/Delete Expense"]
    else:
        tabs = ["Expenses List", "Receipts"]
    tab_objects = st.tabs(tabs)

    tab_idx = 0
    if is_admin:
        # Add Expense Tab
        with tab_objects[tab_idx]:
            cursor.execute("SELECT item FROM sponsorship_items")
            categories = [row[0] for row in cursor.fetchall()]
            if "Miscellaneous" not in categories:
                categories.append("Miscellaneous")
            MAX_RECEIPT_SIZE_MB = 10
            MAX_RECEIPT_SIZE_BYTES = MAX_RECEIPT_SIZE_MB * 1024 * 1024
            uploaded_receipt = st.file_uploader(f"Upload Receipt (JPG/PNG, max {MAX_RECEIPT_SIZE_MB}MB)", type=["jpg", "jpeg", "png"], key="add_expense_receipt")
            receipt_path = None
            receipt_bytes = None
            receipt_filename = None
            if uploaded_receipt is not None:
                if uploaded_receipt.size > MAX_RECEIPT_SIZE_BYTES:
                    st.error(f"Receipt file size should not exceed {MAX_RECEIPT_SIZE_MB} MB.")
                elif uploaded_receipt.type not in ["image/jpeg", "image/png"]:
                    st.error("Only JPG and PNG files are allowed.")
                else:
                    import uuid
                    ext = uploaded_receipt.name.split('.')[-1]
                    receipt_filename = f"receipt_{uuid.uuid4().hex}.{ext}"
                    receipt_bytes = uploaded_receipt.read()
                    receipt_path = receipt_filename
            category = st.selectbox("Category", categories, key="add_expense_category")
            sub_category = st.text_input("Sub Category", placeholder="e.g. Decoration, Snacks", key="add_expense_subcat")
            amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="add_expense_amount")
            date = st.date_input("Date", value=datetime.date.today(), key="add_expense_date")
            spent_by = st.text_input("Spent By", placeholder="e.g. Name", key="add_expense_spentby")
            comments = st.text_area("Comments", value="", placeholder="Any additional details", key="add_expense_comments")
            if st.button("Add Expense", key="add_expense_btn"):
                if not category:
                    st.error("Category is required.")
                elif not sub_category.strip():
                    st.error("Sub Category is required.")
                elif amount <= 0:
                    st.error("Amount must be greater than 0.")
                elif not spent_by.strip():
                    st.error("Spent By is required.")
                elif uploaded_receipt is not None and (uploaded_receipt.size > 10 * 1024 * 1024 or uploaded_receipt.type not in ["image/jpeg", "image/png"]):
                    st.error("Invalid receipt file. Only JPG/PNG under 10MB allowed.")
                else:
                    if hasattr(cursor, 'execute') and hasattr(cursor.connection, 'account'):  # crude check for Snowflake
                        cursor.execute("INSERT INTO expenses (id, category, sub_category, amount, date, spent_by, comments, receipt_path, receipt_blob, status) VALUES (expenses_id_seq.NEXTVAL, %s, %s, %s, %s, %s, %s, %s, %s, 'active')", (category, sub_category, amount, date, spent_by, comments, receipt_path, receipt_bytes))
                    else:
                        cursor.execute("INSERT INTO expenses (category, sub_category, amount, date, spent_by, comments, receipt_path, receipt_blob, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')", (category, sub_category, amount, date, spent_by, comments, receipt_path, receipt_bytes))
                    conn.commit()
                    # Fetch notification email recipients
                    cursor.execute("SELECT email FROM notification_emails")
                    recipients = [row[0] for row in cursor.fetchall()]
                    # Prepare email subject and body
                    subject = f"New Expense Added: {category} - {sub_category}"
                    body = f"""
<h3>New Expense Added</h3>
<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
    <tr><th align='left'>Category</th><td>{category}</td></tr>
    <tr><th align='left'>Sub Category</th><td>{sub_category}</td></tr>
    <tr><th align='left'>Amount</th><td>{amount:.2f}</td></tr>
    <tr><th align='left'>Date</th><td>{date}</td></tr>
    <tr><th align='left'>Spent By</th><td>{spent_by}</td></tr>
    <tr><th align='left'>Comments</th><td>{comments}</td></tr>
</table>
"""
                    # Send email with receipt attached if present
                    st.session_state["expense_submission_in_progress"] = True
                    st.info("Add expense record is in progress...")
                    from app.email_utils import send_email, send_email_with_attachment
                    if receipt_bytes:
                        mime_type = "image/jpeg" if receipt_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
                        for recipient in recipients:
                            send_email_with_attachment(subject, body, recipient, receipt_bytes, receipt_path, mime_type)
                    else:
                        send_email(subject, body, recipients)
                    st.session_state["expense_submission_in_progress"] = False
                    st.success("✅ Expense added and notification email sent!")
                    # Set flag to clear input fields on next run
                    st.session_state["clear_expense_form"] = True
                    st.rerun()
        tab_idx += 1

    # Expenses List Tab
    with tab_objects[tab_idx]:
        # Category filter (for all)
        category_options = ["All"] + sorted(df["Category"].dropna().unique().tolist())
        selected_category = st.selectbox("Filter by Category", category_options, key="filter_category")
        filtered_df = df.copy()
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df["Category"] == selected_category]

        # Spent By filter (admin only)
        if is_admin:
            spent_by_options = ["All"] + sorted(filtered_df["Spent By"].dropna().unique().tolist())
            selected_spent_by = st.selectbox("Filter by Spent By", spent_by_options, key="filter_spent_by")
            if selected_spent_by != "All":
                filtered_df = filtered_df[filtered_df["Spent By"] == selected_spent_by]

        drop_cols = ["Receipt Blob", "Receipt"]
        if not is_admin and "Spent By" in filtered_df.columns:
            drop_cols.append("Spent By")
        show_df = filtered_df.drop(drop_cols, axis=1)
        if "ID" in show_df.columns:
            show_df = show_df.sort_values(by="ID").reset_index(drop=True)
            show_df = show_df[["ID"] + [c for c in show_df.columns if c != "ID"]]
        show_df["Comments"] = show_df["Comments"].apply(lambda x: "  \n".join([str(line) for line in x if str(line).strip()]) if isinstance(x, list) else str(x))
        show_df.index = show_df.index + 1
        st.dataframe(show_df, use_container_width=True)
        st.markdown(f"<div style='font-size:1.1em; font-weight:bold; margin-top:10px; text-align:right;'>Total Expenses: <span style='color:#6D4C41'>{filtered_df['Amount'].sum():.2f}</span></div>", unsafe_allow_html=True)
        if not len(filtered_df):
                st.info("No expenses recorded yet.")
        # Show category summary (category and total amount) below the table
        if not filtered_df.empty:
                cat_summary = filtered_df.groupby("Category")['Amount'].sum().reset_index()
                cat_summary = cat_summary.sort_values(by="Amount", ascending=False)
                # Modern card design for summary
                table_rows = "".join([
                        f"<tr>"
                        f"<td style='padding:8px 18px;font-weight:500;color:#4E342E;font-size:1.08em;'>🗂️ {row['Category']}</td>"
                        f"<td style='padding:8px 18px;text-align:right;font-weight:bold;color:#388E3C;background:#FFFDE7;border-radius:8px;font-size:1.08em;'>{row['Amount']:.2f}</td>"
                        f"</tr>"
                        for _, row in cat_summary.iterrows()
                ])
                card_html = f"""
    <div style='max-width:480px;margin:28px auto 0 auto;padding:0;'>
    <div style='background:linear-gradient(90deg,#6D4C41 60%,#A1887F 100%);color:#fff;padding:12px 22px 10px 22px;border-top-left-radius:14px;border-top-right-radius:14px;font-size:1.18em;font-weight:bold;letter-spacing:0.5px;box-shadow:0 2px 8px #d7ccc8;'>
    <span style='vertical-align:middle;'>📊 Category Summary</span>
    </div>
    <div style='background:#fff;padding:16px 22px 22px 22px;border-bottom-left-radius:14px;border-bottom-right-radius:14px;box-shadow:0 2px 12px #d7ccc8;'>
    <table style='width:100%;border-collapse:separate;border-spacing:0;'>
    <thead>
        <tr style='background:#F5F5F5;'>
            <th style='text-align:left;padding:8px 18px;color:#6D4C41;font-size:1.08em;'>Category</th>
            <th style='text-align:right;padding:8px 18px;color:#6D4C41;font-size:1.08em;'>Amount</th>
        </tr>
    </thead>
    <tbody>
        {table_rows}
    </tbody>
    </table>
    </div>
    </div>
    """
                st.markdown(card_html, unsafe_allow_html=True)
    tab_idx += 1

    # Receipts Tab
    with tab_objects[tab_idx]:
        receipts_df = df.sort_values(by="ID")
        for idx, row in receipts_df.iterrows():
            receipt_name = row["Receipt"]
            receipt_blob = row["Receipt Blob"]
            is_admin = st.session_state.get("admin_logged_in", False)
            if isinstance(receipt_name, str) and receipt_name.strip() and receipt_blob:
                data = receipt_blob
                if isinstance(data, memoryview):
                    data = data.tobytes()
                elif isinstance(data, bytearray):
                    data = bytes(data)
                label_text = f"View Receipt: ID {row['ID']} | Amount {row['Amount']} | Date {row['Date']}"
                if is_admin and "Spent By" in row:
                    label_text += f" | Spent By {row['Spent By']}"
                if st.button(label_text, key=f"view_receipt_{row['ID']}"):
                    import base64
                    img_type = "jpeg" if receipt_name.lower().endswith((".jpg", ".jpeg")) else "png"
                    img_base64 = base64.b64encode(data).decode("utf-8")
                    st.markdown(f"<div style='margin-bottom:18px;'><img src='data:image/{img_type};base64,{img_base64}' style='max-width:320px;max-height:320px;border-radius:12px;border:2px solid #eee;box-shadow:0 2px 8px #ccc;margin-top:8px;'/></div>", unsafe_allow_html=True)
            else:
                label_text = f"No Receipt for ID {row['ID']} | Amount {row['Amount']} | Date {row['Date']}"
                if is_admin and "Spent By" in row:
                    label_text += f" | Spent By {row['Spent By']}"
                st.markdown(f"<span style='color:#888;'>{label_text}</span>", unsafe_allow_html=True)
    tab_idx += 1

    # Expense Summary by Person Tab (admin only)
    if is_admin:
        with tab_objects[tab_idx]:
            cursor.execute("SELECT spent_by, SUM(amount) FROM expenses WHERE status='active' GROUP BY spent_by ORDER BY SUM(amount) DESC")
            summary_rows = cursor.fetchall()
            if summary_rows:
                summary_df = pd.DataFrame(summary_rows, columns=["Name", "Total Amount"])
                total_summary_amount = sum([row[1] for row in summary_rows if row[1] is not None])
                summary_df["Total Amount"] = summary_df["Total Amount"].apply(lambda x: f"<span style='background-color:#FFECB3;color:#6D4C41;padding:4px 12px;border-radius:16px;font-weight:bold;'>{x:.2f}</span>")
                st.markdown(summary_df.to_html(escape=False, index=False, justify='center'), unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:1.1em; font-weight:bold; margin-top:10px; text-align:right;'>Total Amount: <span style='color:#6D4C41'>{total_summary_amount:.2f}</span></div>", unsafe_allow_html=True)
            else:
                st.info("No expense summary available yet.")
        tab_idx += 1

    # Edit/Delete Expense Tab (admin only)
    if is_admin:
        with tab_objects[tab_idx]:
            if rows:
                categories = []
                cursor.execute("SELECT item FROM sponsorship_items")
                categories = [row[0] for row in cursor.fetchall()]
                if "Miscellaneous" not in categories:
                    categories.append("Miscellaneous")
                expense_options = ["Choose an item"] + [f"{df[df['ID']==x]['Category'].values[0]} - {df[df['ID']==x]['Sub Category'].values[0]}" for x in df["ID"].tolist()]
                selected_idx = st.selectbox("Select Expense to Edit/Delete", range(len(expense_options)), format_func=lambda i: expense_options[i])
                if selected_idx == 0:
                    st.info("Please choose an expense to edit or delete.")
                else:
                    selected_id = df["ID"].tolist()[selected_idx-1]
                    entry = df[df["ID"]==selected_id].iloc[0].copy()
                    import re
                    amount_str = str(entry["Amount"])
                    amount_val = float(re.sub(r"[^0-9.]+", "", amount_str))
                    date_str = str(entry["Date"])
                    date_val = re.sub(r"[^0-9\-]", "", date_str)
                    try:
                        date_obj = pd.to_datetime(date_val).date()
                    except Exception:
                        date_obj = datetime.date.today()
                    edit_tab, delete_tab = st.tabs(["Edit", "Delete"])
                    with edit_tab:
                        new_category = st.selectbox("Category", categories, index=categories.index(entry["Category"]) if entry["Category"] in categories else 0, key=f"edit_category_{selected_id}")
                        new_sub_category = st.text_input("Sub Category", value=entry["Sub Category"])
                        new_amount = st.number_input("Amount", min_value=0.0, value=amount_val, format="%.2f")
                        new_date = st.date_input("Date", value=date_obj)
                        new_spent_by = st.text_input("Spent By", value=entry["Spent By"])
                        plain_comments = entry["Comments"]
                        if isinstance(plain_comments, list):
                            plain_comments = "\n".join([str(line) for line in plain_comments if str(line).strip()])
                        plain_comments = re.sub(r"<[^>]+>", "", plain_comments)
                        plain_comments = plain_comments.replace("📝 ", "")
                        plain_comments = plain_comments.replace("&nbsp;|&nbsp;", " | ")
                        plain_comments = plain_comments.replace("&nbsp;", " ")
                        plain_comments = re.sub(r"(\$[0-9,.]+)", r"\1\n", plain_comments)
                        plain_comments = re.sub(r"\n\s*", "\n", plain_comments)
                        plain_comments = plain_comments.strip()
                        new_comments = st.text_area("Comments", value=plain_comments)
                        receipt_name = entry["Receipt"]
                        receipt_blob = entry["Receipt Blob"]
                        receipt_deleted = False
                        new_receipt_bytes = None
                        new_receipt_path = None
                        if isinstance(receipt_name, str) and receipt_name.strip() and receipt_blob:
                            st.markdown("<b>Current Receipt:</b>", unsafe_allow_html=True)
                            data = receipt_blob
                            if isinstance(data, memoryview):
                                data = data.tobytes()
                            elif isinstance(data, bytearray):
                                data = bytes(data)
                            st.download_button(
                                label="Download Receipt",
                                data=data,
                                file_name=receipt_name,
                                mime="image/jpeg" if receipt_name.lower().endswith((".jpg", ".jpeg")) else "image/png",
                                key=f"edit_download_{selected_id}"
                            )
                            if st.button("Delete Receipt", key=f"delete_receipt_{selected_id}"):
                                cursor.execute("UPDATE expenses SET receipt_path=NULL, receipt_blob=NULL WHERE id=%s", (selected_id,))
                                conn.commit()
                                st.success("Receipt deleted. You can upload a new one below.")
                                receipt_deleted = True
                                st.rerun()
                        else:
                            st.info("No receipt uploaded yet. You can upload one below.")
                        uploaded_new_receipt = st.file_uploader(f"Upload New Receipt (JPG/PNG, max {MAX_RECEIPT_SIZE_MB}MB)", type=["jpg", "jpeg", "png"], key=f"edit_upload_receipt_{selected_id}")
                        if uploaded_new_receipt is not None:
                            if uploaded_new_receipt.size > MAX_RECEIPT_SIZE_BYTES:
                                st.error(f"Receipt file size should not exceed {MAX_RECEIPT_SIZE_MB} MB.")
                            elif uploaded_new_receipt.type not in ["image/jpeg", "image/png"]:
                                st.error("Only JPG and PNG files are allowed.")
                            else:
                                import uuid
                                ext = uploaded_new_receipt.name.split('.')[-1]
                                new_receipt_path = f"receipt_{uuid.uuid4().hex}.{ext}"
                                new_receipt_bytes = uploaded_new_receipt.read()
                        if st.button("Update Expense"):
                            if new_receipt_bytes and new_receipt_path:
                                cursor.execute("UPDATE expenses SET category=%s, sub_category=%s, amount=%s, date=%s, spent_by=%s, comments=%s, receipt_path=%s, receipt_blob=%s, status='active' WHERE id=%s", (new_category, new_sub_category, new_amount, new_date, new_spent_by, new_comments, new_receipt_path, new_receipt_bytes, selected_id))
                            else:
                                cursor.execute("UPDATE expenses SET category=%s, sub_category=%s, amount=%s, date=%s, spent_by=%s, comments=%s, status='active' WHERE id=%s", (new_category, new_sub_category, new_amount, new_date, new_spent_by, new_comments, selected_id))
                            conn.commit()
                            subject = f"Expense Edited: {new_category} - {new_sub_category}"
                            body = f"""
                            <b>Expense Edited</b><br><br>
                            <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
                            <tr><th align='left'>Category</th><td>{new_category}</td></tr>
                            <tr><th align='left'>Sub Category</th><td>{new_sub_category}</td></tr>
                            <tr><th align='left'>Amount</th><td>{new_amount:.2f}</td></tr>
                            <tr><th align='left'>Date</th><td>{new_date}</td></tr>
                            <tr><th align='left'>Spent By</th><td>{new_spent_by}</td></tr>
                            <tr><th align='left'>Comments</th><td>{new_comments}</td></tr>
                            </table>
                            """
                            recipients = [st.secrets.get("admin_email", "")]
                            if new_receipt_bytes and new_receipt_path:
                                mime_type = "image/jpeg" if new_receipt_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
                                from app.email_utils import send_email_with_attachment
                                send_email_with_attachment(subject, body, recipients[0], new_receipt_bytes, new_receipt_path, mime_type)
                            else:
                                from app.email_utils import send_email
                                send_email(subject, body, recipients)
                            st.success("✅ Updated and notification email sent!")
                            st.rerun()
                    with delete_tab:
                        entered_cat = st.text_input(f"Type the Category to confirm deletion ({entry['Category']})", key=f"delete_cat_{selected_id}")
                        entered_subcat = st.text_input(f"Type the Sub Category to confirm deletion ({entry['Sub Category']})", key=f"delete_subcat_{selected_id}")
                        confirm_message = f"Type <b>{entry['Category']}</b> and <b>{entry['Sub Category']}</b> above and click Delete to confirm."
                        st.markdown(confirm_message, unsafe_allow_html=True)
                        if st.button("Delete Expense", key=f"delete_expense_{selected_id}"):
                            if entered_cat.strip() == entry['Category'] and entered_subcat.strip() == entry['Sub Category']:
                                cursor.execute("UPDATE expenses SET status='inactive' WHERE id=%s", (selected_id,))
                                conn.commit()
                                subject = f"Expense Deleted: {entry['Category']} - {entry['Sub Category']}"
                                body = f"""
                                <b>Expense Deleted</b><br><br>
                                <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
                                <tr><th align='left'>Category</th><td>{entry['Category']}</td></tr>
                                <tr><th align='left'>Sub Category</th><td>{entry['Sub Category']}</td></tr>
                                <tr><th align='left'>Amount</th><td>{entry['Amount']:.2f}</td></tr>
                                <tr><th align='left'>Date</th><td>{entry['Date']}</td></tr>
                                <tr><th align='left'>Spent By</th><td>{entry['Spent By']}</td></tr>
                                <tr><th align='left'>Comments</th><td>{entry['Comments']}</td></tr>
                                </table>
                                """
                                cursor.execute("SELECT email FROM notification_emails")
                                recipients = [row[0] for row in cursor.fetchall()]
                                from app.email_utils import send_email
                                send_email(subject, body, recipients)
                                st.success("🗑️ Deleted and notification email sent!")
                                st.rerun()
                            else:
                                st.warning(f"Please type the exact Category '{entry['Category']}' and Sub Category '{entry['Sub Category']}' to confirm deletion.")
            else:
                st.info("No expenses recorded yet.")

