import streamlit as st
import pandas as pd
import datetime
from .db import get_connection
from .email_utils import send_email

# DB table creation
CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS prasad_seva (
    id SERIAL PRIMARY KEY,
    seva_type VARCHAR(20),
    names TEXT,
    item_name VARCHAR(100),
    num_people INT,
    apartment VARCHAR(20),
    seva_date DATE,
    pooja_time VARCHAR(20),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(10) DEFAULT 'active'
);
'''

def prasad_seva_tab():
    st.session_state['active_tab'] = 'Prasad Seva'
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()

    st.markdown("<h1 style='text-align: center; color: #8D6E63;'>Prasad Seva</h1>", unsafe_allow_html=True)

    # Display table first
    st.markdown("### Prasad Seva List")
    cursor.execute("SELECT id, seva_type, names, item_name, num_people, apartment, seva_date, pooja_time, created_by, status FROM prasad_seva WHERE status='active' ORDER BY seva_date, pooja_time, id")
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Type", "Names", "Item Name", "How many people are you bringing item for", "Apartemnt Number", "Date", "Pooja Time", "Created By", "Status"])
        if "Status" in df.columns:
            df = df.drop(columns=["Status"])
        # Remove Created By column
        df_display = df.drop(columns=["ID", "Created By"])
        # Bold 'How many people are you bringing item for' column
        df_display["How many people are you bringing item for"] = df_display["How many people are you bringing item for"].apply(lambda x: f"<b>{x}</b>")
        # Sort by Date and Pooja Time
        df_display = df_display.sort_values(by=["Date", "Pooja Time"])
        df_display.index = range(1, len(df_display) + 1)
        st.markdown(df_display.to_html(escape=False, index=True), unsafe_allow_html=True)
        # Show Send Email button only for admin, directly below table
        if st.session_state.get('admin_logged_in', False):
            if st.button("Send Prasad Seva Details to Email"):
                cursor.execute("SELECT email FROM notification_emails")
                notification_emails = [row[0] for row in cursor.fetchall() if row[0]]
                html_table = df.drop(columns=["ID", "Created By"]).to_html(index=False, border=1, justify='center')
                send_email(
                    "Prasad Seva List",
                    f"<b>Current Prasad Seva List</b><br><br>{html_table}",
                    notification_emails
                )
                st.success("✅ Email sent!")
    else:
        st.info("No Prasad Seva entries yet.")

    st.markdown("---")
    # Form for adding Prasad Seva
    st.markdown("### ➕ Add Prasad Seva")
    seva_type = st.radio("Type", ["Group", "Individual"], horizontal=True)
    names = []
    item_names = []
    if seva_type == "Group":
        names_str = st.text_area("Enter Names (comma separated)", key="prasad_group_names", placeholder="e.g. FullName1, FullName2, FullName3")
        names = [n.strip() for n in names_str.split(',') if n.strip()]
        items_str = st.text_area("Enter Item Names (comma separated)", key="prasad_group_items", placeholder="e.g. Pulihora, Kheer/Payasam, Modak, Puran Poli")
        item_names = [i.strip() for i in items_str.split(',') if i.strip()]
        apartment = st.text_input("Apartment Number", key="prasad_group_apartment", placeholder="e.g. 323")
    else:
        name = st.text_input("Name", key="prasad_individual_name", placeholder="e.g. Hanuman")
        names = [name.strip()] if name.strip() else []
        item_name = st.text_input("Item Name", placeholder="e.g. Modak")
        item_names = [item_name.strip()] if item_name.strip() else []
        apartment = st.text_input("Apartment Number", key="prasad_individual_apartment", placeholder="e.g. 1203")

    num_people = st.number_input("How many people are you bringing item for?", min_value=1, value=1)
    # Date picker, restrict to 26th to 30th August 2025
    min_date = datetime.date(2025, 8, 26)
    max_date = datetime.date(2025, 8, 30)
    seva_date = st.date_input("Date", value=min_date, min_value=min_date, max_value=max_date)
    pooja_time = st.radio("Pooja Time", ["Morning Pooja", "Evening Pooja"], horizontal=True)

    # Add Prasad Seva
    if st.button("✅ Add Prasad Seva"):
        if not names:
            st.error("Please enter at least one name.")
        elif not item_names:
            st.error("Please enter at least one item name.")
        elif not apartment.strip():
            st.error("Apartment Number is required.")
        elif not num_people:
            st.error("Number of people is required.")
        elif not seva_date:
            st.error("Date is required.")
        elif not pooja_time:
            st.error("Pooja Time is required.")
        else:
            for item in item_names:
                cursor.execute(
                    "INSERT INTO prasad_seva (seva_type, names, item_name, num_people, apartment, seva_date, pooja_time, created_by, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (seva_type, ', '.join(names), item, num_people, apartment, seva_date, pooja_time, st.session_state.get('admin_full_name', 'User'), 'active')
                )
            conn.commit()
            st.success("✅ Prasad Seva added!")
            st.rerun()

    # Edit/Delete Prasad Seva (now for all users)
    if rows:
        st.markdown("#### Edit/Delete Prasad Seva")
        selected_id = st.selectbox("Select Entry to Edit/Delete", df["ID"].tolist(), format_func=lambda x: f"{df[df['ID']==x]['Names'].values[0]}")
        entry = df[df["ID"]==selected_id].iloc[0]
        edit_tab, delete_tab = st.tabs(["Edit", "Delete"])
        with edit_tab:
            new_type = st.radio("Type", ["Group", "Individual"], index=0 if entry["Type"]=="Group" else 1)
            new_names = st.text_area("Names (comma separated)", value=entry["Names"])
            new_item = st.text_input("Item Name", value=entry["Item Name"])
            new_num = st.number_input("How many people are you bringing item for?", min_value=1, value=int(entry["How many people are you bringing item for"]))
            new_apartment = st.text_input("Apartment Number", value=entry["Apartemnt Number"])
            min_date = datetime.date(2025, 8, 26)
            max_date = datetime.date(2025, 8, 30)
            current_date = pd.to_datetime(entry["Date"]).date() if pd.notna(entry["Date"]) else min_date
            new_date = st.date_input("Date", value=current_date, min_value=min_date, max_value=max_date, key=f"edit_prasad_date_{selected_id}")
            new_pooja_time = st.radio("Pooja Time", ["Morning Pooja", "Evening Pooja"], index=0 if entry["Pooja Time"]=="Morning Pooja" else 1, key=f"edit_prasad_time_{selected_id}")
            if st.button("Update Prasad Seva"):
                cursor.execute("UPDATE prasad_seva SET seva_type=%s, names=%s, item_name=%s, num_people=%s, apartment=%s, seva_date=%s, pooja_time=%s, status=%s WHERE id=%s", (new_type, new_names, new_item, new_num, new_apartment, new_date, new_pooja_time, 'active', selected_id))
                conn.commit()
                st.success("✅ Updated!")
                st.rerun()
        with delete_tab:
            entered_name = st.text_input(f"Type the name to confirm deletion ({entry['Names']})", key=f"delete_name_{selected_id}")
            confirm_message = f"Type <b>{entry['Names']}</b> above and click Delete to confirm."
            st.markdown(confirm_message, unsafe_allow_html=True)
            if st.button("Delete Prasad Seva", key=f"delete_prasad_{selected_id}"):
                if entered_name.strip() == entry['Names']:
                    cursor.execute("UPDATE prasad_seva SET status='inactive' WHERE id=%s", (selected_id,))
                    conn.commit()
                    st.success("🗑️ Deleted!")
                    st.rerun()
                else:
                    st.warning(f"Please type the exact name '{entry['Names']}' to confirm deletion.")
