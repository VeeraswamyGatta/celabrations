import streamlit as st
import pandas as pd
import datetime
from .db import get_connection

def create_expenses_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            category TEXT NOT NULL,
            sub_category TEXT NOT NULL,
            amount NUMERIC(10,2) NOT NULL,
            date DATE NOT NULL,
            spent_by TEXT NOT NULL,
            comments TEXT,
            status VARCHAR(10) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

create_expenses_table()

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
            Available Amount in Wallet: <span style='background: {blink_color}; color: white; padding: 4px 12px; border-radius: 8px; animation: blink 1s linear infinite;'>{wallet_amount:.2f}</span>
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

        # Fetch sponsorship items for category dropdown
        cursor.execute("SELECT item FROM sponsorship_items")
        categories = [row[0] for row in cursor.fetchall()]

        # Display Expenses Table
        st.markdown("### Expenses List")
        cursor.execute("SELECT id, category, sub_category, amount, date, spent_by, comments FROM expenses WHERE status='active' ORDER BY category, sub_category")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=["ID", "Category", "Sub Category", "Amount", "Date", "Spent By", "Comments"])
            df_display = df.drop(columns=["ID"])
            df_display.index = range(1, len(df_display) + 1)
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(df_display.to_html(escape=False, index=True), unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='font-size:1.1em; font-weight:bold; margin-top:10px; text-align:right;'>Total Expenses: <span style='color:#6D4C41'>{total_expenses:.2f}</span></div>", unsafe_allow_html=True)
            # Edit/Delete options
            st.markdown("#### Edit/Delete Expense")
            selected_id = st.selectbox("Select Expense to Edit/Delete", df["ID"].tolist(), format_func=lambda x: f"{df[df['ID']==x]['Category'].values[0]} - {df[df['ID']==x]['Sub Category'].values[0]}")
            entry = df[df["ID"]==selected_id].iloc[0]
            edit_tab, delete_tab = st.tabs(["Edit", "Delete"])
            with edit_tab:
                new_category = st.selectbox("Category", categories, index=categories.index(entry["Category"]), key=f"edit_category_{selected_id}")
                new_sub_category = st.text_input("Sub Category", value=entry["Sub Category"])
                new_amount = st.number_input("Amount", min_value=0.0, value=float(entry["Amount"]), format="%.2f")
                new_date = st.date_input("Date", value=pd.to_datetime(entry["Date"]).date())
                new_spent_by = st.text_input("Spent By", value=entry["Spent By"])
                new_comments = st.text_area("Comments", value=entry["Comments"])
                if st.button("Update Expense"):
                    cursor.execute("UPDATE expenses SET category=%s, sub_category=%s, amount=%s, date=%s, spent_by=%s, comments=%s, status='active' WHERE id=%s", (new_category, new_sub_category, new_amount, new_date, new_spent_by, new_comments, selected_id))
                    conn.commit()
                    st.success("✅ Updated!")
                    st.rerun()
            with delete_tab:
                entered_cat = st.text_input(f"Type the Category to confirm deletion (e.g. {entry['Category']})", key=f"delete_cat_{selected_id}")
                entered_subcat = st.text_input(f"Type the Sub Category to confirm deletion (e.g. {entry['Sub Category']})", key=f"delete_subcat_{selected_id}")
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
        else:
            st.info("No expenses recorded yet.")

        # Add Expense Form
        st.markdown("### ➕ Add Expense")
        category = st.selectbox("Category", categories)
        sub_category = st.text_input("Sub Category", placeholder="e.g. Decoration, Snacks")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        date = st.date_input("Date", value=datetime.date.today())
        spent_by = st.text_input("Spent By", placeholder="e.g. Name")
        comments = st.text_area("Comments", placeholder="Any additional details")
        if st.button("Add Expense"):
            if not category:
                st.error("Category is required.")
            elif not sub_category.strip():
                st.error("Sub Category is required.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            elif not spent_by.strip():
                st.error("Spent By is required.")
            else:
                cursor.execute(
                    "INSERT INTO expenses (category, sub_category, amount, date, spent_by, comments, status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (category, sub_category, amount, date, spent_by, comments, 'active')
                )
                conn.commit()
                # Send notification email
                from .email_utils import send_email
                # Get notification emails
                cursor.execute("SELECT email FROM notification_emails")
                notification_emails = [row[0] for row in cursor.fetchall() if row[0]]
                # Get wallet amount after adding expense
                cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payment_details")
                total_payments = cursor.fetchone()[0]
                cursor.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE status='active'")
                total_expenses = cursor.fetchone()[0]
                wallet_amount = total_payments - total_expenses
                # Newly added expense info as table
                new_expense_df = pd.DataFrame([[category, sub_category, amount, date, spent_by, comments]], columns=["Category", "Sub Category", "Amount", "Date", "Spent By", "Comments"])
                new_expense_html = new_expense_df.to_html(index=False, border=1, justify='center')
                # All expenses table
                cursor.execute("SELECT category, sub_category, amount, date, spent_by, comments FROM expenses WHERE status='active' ORDER BY category, sub_category")
                all_rows = cursor.fetchall()
                all_expenses_df = pd.DataFrame(all_rows, columns=["Category", "Sub Category", "Amount", "Date", "Spent By", "Comments"])
                all_expenses_html = all_expenses_df.to_html(index=False, border=1, justify='center')
                subject = f"Available Amount in Wallet: {wallet_amount:.2f}"
                body = f"<b>New Expense Added:</b><br>{new_expense_html}<br><br><b>All Expenses:</b><br>{all_expenses_html}"
                send_email(subject, body, notification_emails)
                st.success("✅ Expense added and notification email sent!")
                st.rerun()
