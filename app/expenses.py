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
    st.markdown("<h1 style='text-align: center; color: #6D4C41;'>Expenses</h1>", unsafe_allow_html=True)

    # Fetch sponsorship items for category dropdown
    cursor.execute("SELECT item FROM sponsorship_items")
    categories = [row[0] for row in cursor.fetchall()]

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
            st.success("✅ Expense added!")
            st.rerun()

    # Display Expenses Table
    st.markdown("### Expenses List")
    cursor.execute("SELECT id, category, sub_category, amount, date, spent_by, comments FROM expenses WHERE status='active' ORDER BY category, sub_category")
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Category", "Sub Category", "Amount", "Date", "Spent By", "Comments"])
        df_display = df.drop(columns=["ID"])
        df_display.index = range(1, len(df_display) + 1)
        st.markdown(df_display.to_html(escape=False, index=True), unsafe_allow_html=True)
        # Edit/Delete options
        st.markdown("#### Edit/Delete Expense")
        selected_id = st.selectbox("Select Expense to Edit/Delete", df["ID"].tolist(), format_func=lambda x: f"{df[df['ID']==x]['Category'].values[0]} - {df[df['ID']==x]['Sub Category'].values[0]}")
        entry = df[df["ID"]==selected_id].iloc[0]
        edit_tab, delete_tab = st.tabs(["Edit", "Delete"])
        with edit_tab:
            new_category = st.selectbox("Category", categories, index=categories.index(entry["Category"]))
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
