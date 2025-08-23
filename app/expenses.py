import streamlit as st
import pandas as pd
import datetime
from .db import get_connection
import io


def expenses_tab():
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

    # Display Expenses Table
    st.markdown("### Expenses List")
    cursor.execute("SELECT id, category, sub_category, amount, date, spent_by, comments, receipt_path, receipt_blob FROM expenses WHERE status='active' ORDER BY category, sub_category")
    rows = cursor.fetchall()
    tabs = ["Expenses List"]
    is_admin = st.session_state.get("admin_logged_in", False)
    if is_admin:
        tabs.append("Expense Summary by Person")
    tabs = st.tabs(tabs)
    with tabs[0]:
        if rows:
            columns = ["ID", "Category", "Sub Category", "Amount", "Date", "Spent By", "Comments", "Receipt", "Receipt Blob"]
            df = pd.DataFrame(rows, columns=columns)
            # Remove all icon logic and use plain text for table columns
            def format_comments(comments):
                if not comments:
                    return ""
                # Split by newline or pipe, keep each as a separate line
                import re
                lines = re.split(r'[\n|]+', comments)
                html_lines = [f"<span style='display:block;margin-bottom:2px;'>{line.strip()}</span>" for line in lines if line.strip()]
                return "<div style='line-height:1.5;'>" + "".join(html_lines) + "</div>"
            df["Comments"] = df["Comments"].apply(format_comments)
            # Display each expense row with details and download button in Receipt column
            st.markdown("""
                <style>
                .expense-table-container {
                    background: #fff;
                    border-radius: 16px;
                    box-shadow: 0 4px 24px rgba(109,76,65,0.10);
                    padding: 24px 16px 16px 16px;
                    margin-bottom: 24px;
                }
                .expense-header {
                    background: linear-gradient(90deg, #FFECB3 0%, #FFE0B2 100%);
                    border-bottom: 2px solid #6D4C41;
                    font-weight: bold;
                    color: #6D4C41;
                    padding: 12px 0;
                    border-radius: 8px 8px 0 0;
                    font-size: 1.08em;
                    letter-spacing: 0.5px;
                }
                .expense-row {
                    border-bottom: 1px solid #e0e0e0;
                    padding: 12px 0;
                    border-radius: 0 0 8px 8px;
                    box-shadow: 0 2px 8px rgba(109,76,65,0.04);
                    transition: background 0.2s;
                }
                .expense-row.alt {
                    background: #FFF8E1;
                }
                .expense-row:hover {
                    background: #FFE0B2;
                }
                .expense-cell {
                    padding: 12px 0;
                    font-size: 1.01em;
                }
                </style>
            """, unsafe_allow_html=True)
            # Removed empty expense-table-container div to eliminate extra space before table
            # Removed duplicate Expenses Table heading
            # Responsive HTML table for expenses
            table_html = """
<style>
@media (max-width: 600px) {
  .expense-table th, .expense-table td { font-size: 0.95em; padding: 8px 4px; }
  .expense-table { font-size: 0.95em; }
}
.expense-table-container { background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(109,76,65,0.10); padding: 24px 8px 16px 8px; margin-bottom: 24px; }
.expense-table { width: 100%; border-collapse: collapse; }
.expense-table th { background: linear-gradient(90deg, #FFECB3 0%, #FFE0B2 100%); border-bottom: 2px solid #6D4C41; color: #6D4C41; font-weight: bold; padding: 12px 6px; }
.expense-table td { border-bottom: 1px solid #e0e0e0; padding: 12px 6px; }
.expense-table tr:nth-child(even) { background: #FFF8E1; }
.expense-table tr:hover { background: #FFE0B2; }
</style>
<div class='expense-table-container'>
<h3 style='color:#6D4C41;margin-bottom:0.5em;'>Expenses Table</h3>
<table class='expense-table'>
  <thead>
    <tr>
      <th>Category</th>
      <th>Sub Category</th>
      <th>Amount</th>
      <th>Date</th>
      <th>Comments</th>
      <th>Receipt</th>
    </tr>
  </thead>
  <tbody>
"""
            for idx, row in df.iterrows():
                table_html += "<tr>"
                for col in ["Category", "Sub Category", "Amount", "Date", "Comments"]:
                    val = row[col]
                    if col == "Comments":
                        table_html += f"<td>{val}</td>"
                    else:
                        table_html += f"<td>{val}</td>"
                # Receipt column
                receipt_name = row["Receipt"]
                receipt_blob = row["Receipt Blob"]
                if isinstance(receipt_name, str) and receipt_name.strip() and receipt_blob:
                    data = receipt_blob
                    if isinstance(data, memoryview):
                        data = data.tobytes()
                    # Generate a download link using Streamlit's download_button outside the table
                    # Instead, use a placeholder and add download_button after rendering table
                    table_html += f"<td><span id='download_{idx}'></span></td>"
                else:
                    table_html += "<td>No Receipt</td>"
                table_html += "</tr>"
            table_html += "</tbody></table></div>"
            st.markdown(table_html, unsafe_allow_html=True)
            # Add download buttons for receipts after table rendering
            for idx, row in df.iterrows():
                receipt_name = row["Receipt"]
                receipt_blob = row["Receipt Blob"]
                if isinstance(receipt_name, str) and receipt_name.strip() and receipt_blob:
                    data = receipt_blob
                    if isinstance(data, memoryview):
                        data = data.tobytes()
                    st.download_button(
                        label="Download Receipt",
                        data=data,
                        file_name=receipt_name,
                        mime="image/jpeg" if receipt_name.lower().endswith((".jpg", ".jpeg")) else "image/png",
                        key=f"download_{idx}"
                    )
            st.markdown(f"<div style='font-size:1.1em; font-weight:bold; margin-top:10px; text-align:right;'>Total Expenses: <span style='color:#6D4C41'>{total_expenses:.2f}</span></div>", unsafe_allow_html=True)
        else:
            st.info("No expenses recorded yet.")
    if is_admin and len(tabs) > 1:
        with tabs[1]:
            # Expense summary by person
            cursor.execute("SELECT spent_by, SUM(amount) FROM expenses WHERE status='active' GROUP BY spent_by ORDER BY SUM(amount) DESC")
            summary_rows = cursor.fetchall()
            if summary_rows:
                summary_df = pd.DataFrame(summary_rows, columns=["Name", "Total Amount"])
                # Calculate total from raw summary_rows
                total_summary_amount = sum([row[1] for row in summary_rows if row[1] is not None])
                summary_df["Total Amount"] = summary_df["Total Amount"].apply(lambda x: f"<span style='background-color:#FFECB3;color:#6D4C41;padding:4px 12px;border-radius:16px;font-weight:bold;'>{x:.2f}</span>")
                st.markdown("<h4 style='color:#6D4C41;'>Expense Summary by Person</h4>", unsafe_allow_html=True)
                st.markdown(summary_df.to_html(escape=False, index=False, justify='center'), unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:1.1em; font-weight:bold; margin-top:10px; text-align:right;'>Total Amount: <span style='color:#6D4C41'>{total_summary_amount:.2f}</span></div>", unsafe_allow_html=True)
            else:
                st.info("No expense summary available yet.")

    # Add Expense Form (admin only)
    if is_admin:
        st.markdown("### ➕ Add Expense")
        cursor.execute("SELECT item FROM sponsorship_items")
        categories = [row[0] for row in cursor.fetchall()]
        uploaded_receipt = st.file_uploader("Upload Receipt (JPG/PNG, max 1MB)", type=["jpg", "jpeg", "png"], key="add_expense_receipt")
        receipt_path = None
        receipt_bytes = None
        receipt_filename = None
        if uploaded_receipt is not None:
            if uploaded_receipt.size > 1 * 1024 * 1024:
                st.error("Receipt file size should not exceed 1 MB.")
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
            elif uploaded_receipt is not None and (uploaded_receipt.size > 1 * 1024 * 1024 or uploaded_receipt.type not in ["image/jpeg", "image/png"]):
                st.error("Invalid receipt file. Only JPG/PNG under 1MB allowed.")
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
                from app.email_utils import send_email
                send_with_attachment = send_email(subject, body, recipients)
                if receipt_bytes:
                    mime_type = "image/jpeg" if receipt_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
                    for recipient in recipients:
                        send_with_attachment(recipient, subject, body, receipt_bytes, receipt_path, mime_type)
                else:
                    for recipient in recipients:
                        send_with_attachment(recipient, subject, body)
                st.success("✅ Expense added and notification email sent!")
                st.rerun()

        # Move Edit/Delete Expense section after Add Expense
        if rows:
            st.markdown("#### Edit/Delete Expense")
            categories = []
            cursor.execute("SELECT item FROM sponsorship_items")
            categories = [row[0] for row in cursor.fetchall()]
            expense_options = ["Choose an item"] + [f"{df[df['ID']==x]['Category'].values[0]} - {df[df['ID']==x]['Sub Category'].values[0]}" for x in df["ID"].tolist()]
            selected_idx = st.selectbox("Select Expense to Edit/Delete", range(len(expense_options)), format_func=lambda i: expense_options[i])
            if selected_idx == 0:
                st.info("Please choose an expense to edit or delete.")
            else:
                selected_id = df["ID"].tolist()[selected_idx-1]
                entry = df[df["ID"]==selected_id].iloc[0].copy()
                # Remove icon from Amount for editing
                import re
                amount_str = str(entry["Amount"])
                amount_val = float(re.sub(r"[^0-9.]+", "", amount_str))
                # Remove icon from Date for editing
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
                    # Show plain text comments in edit form
                    import re
                    plain_comments = entry["Comments"]
                    plain_comments = re.sub(r"<[^>]+>", "", plain_comments)
                    plain_comments = plain_comments.replace("📝 ", "")
                    plain_comments = plain_comments.replace("&nbsp;|&nbsp;", " | ")
                    plain_comments = plain_comments.replace("&nbsp;", " ")
                    plain_comments = re.sub(r"(\$[0-9,.]+)", r"\1\n", plain_comments)
                    plain_comments = re.sub(r"\n\s*", "\n", plain_comments)
                    plain_comments = plain_comments.strip()
                    new_comments = st.text_area("Comments", value=plain_comments)

                    # Receipt management
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

                    # Allow uploading new receipt if none exists or after deletion
                    uploaded_new_receipt = st.file_uploader("Upload New Receipt (JPG/PNG, max 1MB)", type=["jpg", "jpeg", "png"], key=f"edit_upload_receipt_{selected_id}")
                    if uploaded_new_receipt is not None:
                        if uploaded_new_receipt.size > 1 * 1024 * 1024:
                            st.error("Receipt file size should not exceed 1 MB.")
                        elif uploaded_new_receipt.type not in ["image/jpeg", "image/png"]:
                            st.error("Only JPG and PNG files are allowed.")
                        else:
                            import uuid
                            ext = uploaded_new_receipt.name.split('.')[-1]
                            new_receipt_path = f"receipt_{uuid.uuid4().hex}.{ext}"
                            new_receipt_bytes = uploaded_new_receipt.read()

                    if st.button("Update Expense"):
                        # Update expense with or without new receipt
                        if new_receipt_bytes and new_receipt_path:
                            cursor.execute("UPDATE expenses SET category=%s, sub_category=%s, amount=%s, date=%s, spent_by=%s, comments=%s, receipt_path=%s, receipt_blob=%s, status='active' WHERE id=%s", (new_category, new_sub_category, new_amount, new_date, new_spent_by, new_comments, new_receipt_path, new_receipt_bytes, selected_id))
                        else:
                            cursor.execute("UPDATE expenses SET category=%s, sub_category=%s, amount=%s, date=%s, spent_by=%s, comments=%s, status='active' WHERE id=%s", (new_category, new_sub_category, new_amount, new_date, new_spent_by, new_comments, selected_id))
                        conn.commit()
                        st.success("✅ Updated!")
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
                            st.success("🗑️ Deleted!")
                            st.rerun()
                        else:
                            st.warning(f"Please type the exact Category '{entry['Category']}' and Sub Category '{entry['Sub Category']}' to confirm deletion.")
    # If no expenses recorded yet
    if not rows:
        st.info("No expenses recorded yet.")

