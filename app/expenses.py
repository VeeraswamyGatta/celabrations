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
    cursor.execute("SELECT id, category, sub_category, amount, date, spent_by, comments FROM expenses WHERE status='active' ORDER BY category, sub_category")
    rows = cursor.fetchall()
    tabs = ["Expenses List"]
    is_admin = st.session_state.get("admin_logged_in", False)
    if is_admin:
        tabs.append("Expense Summary by Person")
    tabs = st.tabs(tabs)
    with tabs[0]:
        if rows:
            columns = ["ID", "Category", "Sub Category", "Amount", "Date", "Spent By", "Comments"] if is_admin else ["ID", "Category", "Sub Category", "Amount", "Date", "Comments"]
            df = pd.DataFrame(rows, columns=["ID", "Category", "Sub Category", "Amount", "Date", "Spent By", "Comments"])
            # Icon mapping for each column
            category_icons = {
                "Decoration": "🎉",
                "Snacks": "🍪",
                "Flowers": "🌸",
                "Prasad": "🍛",
                "Other": "🛒"
            }
            def get_category_icon(cat):
                return category_icons.get(cat, "🛒")
            def get_subcat_icon(subcat):
                if "food" in subcat.lower():
                    return "🍽️"
                elif "drink" in subcat.lower():
                    return "🥤"
                elif "flower" in subcat.lower():
                    return "🌼"
                elif "decoration" in subcat.lower():
                    return "🎊"
                else:
                    return "🔖"
            def get_amount_icon(amount):
                return "💸" if amount > 0 else ""
            def get_date_icon(date):
                return "📅"
            def format_comments(comments):
                if not comments:
                    return ""
                lines = [line.strip() for line in comments.split("\n") if line.strip()]
                html_lines = []
                for line in lines:
                    parts = line.split("\t")
                    html_lines.append("<span style='display:inline-block;margin-bottom:2px;'>📝 " + " &nbsp;|&nbsp; ".join(parts) + "</span>")
                return "<br>".join(html_lines)
            # Apply icons
            df["Category"] = df["Category"].apply(lambda x: f"{get_category_icon(x)} {x}")
            df["Sub Category"] = df["Sub Category"].apply(lambda x: f"{get_subcat_icon(x)} {x}")
            df["Amount"] = df["Amount"].apply(lambda x: f"{get_amount_icon(x)} {x:.2f}")
            df["Date"] = df["Date"].apply(lambda x: f"{get_date_icon(x)} {x}")
            df["Comments"] = df["Comments"].apply(format_comments)
            if not is_admin:
                df_display = df.drop(columns=["ID", "Spent By"])
            else:
                df_display = df.drop(columns=["ID"])
            df_display.index = range(1, len(df_display) + 1)
            st.markdown(df_display.to_html(escape=False, index=True), unsafe_allow_html=True)
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
        category = st.selectbox("Category", categories, key="add_expense_category")
        sub_category = st.text_input("Sub Category", placeholder="e.g. Decoration, Snacks", key="add_expense_subcat")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="add_expense_amount")
        date = st.date_input("Date", value=datetime.date.today(), key="add_expense_date")
        spent_by = st.text_input("Spent By", placeholder="e.g. Name", key="add_expense_spentby")
        comments = st.text_area("Comments", placeholder="Any additional details", key="add_expense_comments")
        if st.button("Add Expense", key="add_expense_btn"):
            if not category:
                st.error("Category is required.")
            elif not sub_category.strip():
                st.error("Sub Category is required.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            elif not spent_by.strip():
                st.error("Spent By is required.")
            else:
                cursor.execute("INSERT INTO expenses (category, sub_category, amount, date, spent_by, comments, status) VALUES (%s, %s, %s, %s, %s, %s, 'active')", (category, sub_category, amount, date, spent_by, comments))
                conn.commit()
                st.success("✅ Expense added!")
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
                    # Add newline before each item if not present
                    # This will add a newline before each item that starts with a word and ends with a dollar amount
                    plain_comments = re.sub(r"(\$[0-9,.]+)", r"\1\n", plain_comments)
                    # Remove extra spaces and ensure each item is on its own line
                    plain_comments = re.sub(r"\n\s*", "\n", plain_comments)
                    plain_comments = plain_comments.strip()
                    new_comments = st.text_area("Comments", value=plain_comments)
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
    # If no expenses recorded yet
    if not rows:
        st.info("No expenses recorded yet.")

