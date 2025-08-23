import streamlit as st
import pandas as pd
import datetime
from .db import get_connection
from .email_utils import send_email

# DB table creation
CREATE_TABLE_SQL_POSTGRES = '''
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

CREATE_TABLE_SQL_SNOWFLAKE = '''
CREATE TABLE IF NOT EXISTS prasad_seva (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
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

def prasad_seva_tab(switch_db_type="postgres"):
    st.session_state['active_tab'] = 'Prasad Seva'
    from app import switch_db_type as global_db_type
    conn = get_connection(global_db_type)
    cursor = conn.cursor()
    db_type = global_db_type
    if db_type == "snowflake":
        cursor.execute(CREATE_TABLE_SQL_SNOWFLAKE)
    else:
        cursor.execute(CREATE_TABLE_SQL_POSTGRES)
    conn.commit()

    # Removed repeated Prasad Seva heading for cleaner UI

    # Metrics: Date-wise sum of 'How many people are you bringing item for'
    cursor.execute("SELECT seva_date, pooja_time, SUM(num_people) FROM prasad_seva WHERE status='active' GROUP BY seva_date, pooja_time ORDER BY seva_date, pooja_time")
    metrics = cursor.fetchall()
    min_date = datetime.date(2025, 8, 26)
    max_date = datetime.date(2025, 8, 30)
    date_range = pd.date_range(min_date, max_date)
    pooja_times = ["Morning Pooja", "Evening Pooja"]
    # Build metrics dict {(date, pooja_time): total}
    metrics_dict = {(pd.to_datetime(row[0]).date(), row[1]): row[2] for row in metrics} if metrics else {}
    metrics_data = []
    for d in date_range:
        for pt in pooja_times:
            # Skip Morning Pooja for 26th Aug
            if d.date() == datetime.date(2025, 8, 26) and pt == "Morning Pooja":
                continue
            metrics_data.append((d.date(), pt, metrics_dict.get((d.date(), pt), 0)))
    metrics_df = pd.DataFrame(metrics_data, columns=["Date", "Pooja Time", "Total People Served"])
    # Format date and number for better visualization
    metrics_df["Date"] = metrics_df["Date"].apply(lambda d: f"<span style='font-size:16px;'>&#128197;</span> <b>{pd.to_datetime(d).strftime('%d-%b-%Y')}</b>")
    metrics_df["Pooja Time"] = metrics_df["Pooja Time"].apply(lambda pt: f"<span style='font-size:18px;'>{'🌅' if pt=='Morning Pooja' else '🌇'}</span> <b>{pt.replace('Pooja','')}</b>")
    metrics_df["Total People Served"] = metrics_df["Total People Served"].apply(lambda x: f"<span style='background-color:#FFECB3;color:#6D4C41;padding:4px 12px;border-radius:16px;font-weight:bold;display:inline-block;text-align:center;'>{x}</span>")
    # Center align columns and render as HTML
    tabs = st.tabs(["Prasad Seva Summary", "Prasad Seva Sponsors List"])
    with tabs[0]:
        # Calculate total sponsored count for all days
        cursor.execute("SELECT SUM(num_people) FROM prasad_seva WHERE status='active'")
        total_sponsored = cursor.fetchone()[0] or 0
    with tabs[0]:
        st.markdown(f"<h4 style='text-align:center;color:#388E3C;background:#C8E6C9;padding:7px;border-radius:10px;margin-bottom:0.5em;font-size:1.1em;'>🎉 Total People Served Count (All Days): <span style='color:#1B5E20;'>{total_sponsored}</span></h4>", unsafe_allow_html=True)
        st.markdown(metrics_df.to_html(escape=False, index=False, justify='center'), unsafe_allow_html=True)
        # Download button for summary table
        # Prepare raw summary data for download (no HTML tags)
        raw_metrics_df = pd.DataFrame(metrics_data, columns=["Date", "Pooja Time", "Total People Served"])
        csv_summary = raw_metrics_df.to_csv(index=False)
        st.download_button(label="📥", data=csv_summary, file_name="prasad_seva_summary.csv", mime="text/csv")

    with tabs[1]:
        # --- Filters ---
        st.markdown("<h5 style='margin-bottom:0.2em;'>🔎 Filter Prasad Seva Entries</h5>", unsafe_allow_html=True)
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_date = st.date_input("Filter by Date", value=None, min_value=min_date, max_value=max_date, key="prasad_filter_date")
        with filter_col2:
            filter_name = st.text_input("Filter by Name", value="", key="prasad_filter_name")

        query = "SELECT id, seva_type, names, item_name, num_people, apartment, seva_date, pooja_time, created_by, status FROM prasad_seva WHERE status='active'"
        filters = []
        params = []
        if filter_date:
            filters.append("seva_date = %s")
            params.append(filter_date)
        if filter_name:
            filters.append("names ILIKE %s")
            params.append(f"%{filter_name}%")
        if filters:
            query += " AND " + " AND ".join(filters)
        query += " ORDER BY seva_date, pooja_time, id"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            df = pd.DataFrame(rows, columns=["ID", "Type", "Names", "Item Name", "How many people are you bringing item for", "Apartemnt Number", "Date", "Pooja Time", "Created By", "Status"])
            if "Status" in df.columns:
                df = df.drop(columns=["Status"])
            # Remove Created By column
            df_display = df.drop(columns=["ID", "Created By"])
            # Format date, number, pooja time, and type columns for visualization
            df_display["Date"] = df_display["Date"].apply(lambda d: f"<span style='font-size:16px;'>&#128197;</span> <b>{pd.to_datetime(d).strftime('%d-%b-%Y')}</b>")
            # Hide Morning Pooja for 26th Aug in table
            def pooja_time_display(row):
                if row["Date"].startswith("<span") and "26-Aug-2025" in row["Date"] and row["Pooja Time"].find("Morning") != -1:
                    return ""
                return f"<span style='font-size:18px;'>{'🌅' if row['Pooja Time']=='Morning Pooja' else '🌇'}</span> <b>{row['Pooja Time'].replace('Pooja','')}</b>"
            df_display["Pooja Time"] = df_display.apply(pooja_time_display, axis=1)
            df_display["Type"] = df_display["Type"].apply(lambda t: f"<span style='background-color:{'#B2DFDB' if t=='Group' else '#FFCCBC'};color:#4E342E;padding:4px 10px;border-radius:12px;font-weight:bold;'>{'👥 Group' if t=='Group' else '🧑 Individual'}</span>")
            df_display["Apartemnt Number"] = df_display["Apartemnt Number"].apply(lambda apt: f"<span style='font-size:16px;'>&#127968;</span> <b>{apt}</b>" if apt else "")
            df_display["Names"] = df_display["Names"].apply(lambda n: f"<span style='font-size:16px;'>&#128100;</span> <b>{n}</b>" if n else "")
            df_display["Item Name"] = df_display["Item Name"].apply(lambda item: f"<span style='font-size:16px;'>&#127858;</span> <b>{item}</b>" if item else "")
            df_display["How many people are you bringing item for"] = df_display["How many people are you bringing item for"].apply(lambda x: f"<span style='background-color:#FFECB3;color:#6D4C41;padding:4px 12px;border-radius:16px;font-weight:bold;display:inline-block;text-align:center;'>{x}</span>")
            # Sort by Date and Pooja Time
            df_display = df_display.sort_values(by=["Date", "Pooja Time"])
            df_display.index = range(1, len(df_display) + 1)
            st.markdown(df_display.to_html(escape=False, index=True, justify='center'), unsafe_allow_html=True)
            # Download button for sponsors list table
            # Prepare raw sponsors list data for download (no HTML tags)
            raw_sponsors_df = df.drop(columns=["ID", "Created By"])
            csv_sponsors = raw_sponsors_df.to_csv(index=False)
            st.download_button(label="📥", data=csv_sponsors, file_name="prasad_seva_sponsors_list.csv", mime="text/csv")
            # Show Send Email button only for admin, directly below table
            if st.session_state.get('admin_logged_in', False):
                if st.button("Send Prasad Seva Details to Email"):
                    cursor.execute("SELECT email FROM notification_emails")
                    notification_emails = [row[0] for row in cursor.fetchall() if row[0]]
                    html_table = df.drop(columns=["ID", "Created By"]).to_html(index=False, border=1, justify='center')
                    send_email(
                        "Prasad Seva Sponsors List",
                        f"<b>Current Prasad Seva List</b><br><br>{html_table}",
                        notification_emails
                    )
                    st.success("✅ Email sent!")
        else:
            st.info("No Prasad Seva entries yet.")
    # ...existing code...

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
        name = st.text_input("Name", key="prasad_individual_name", placeholder="e.g. Full Name")
        names = [name.strip()] if name.strip() else []
        item_name = st.text_input("Item Name", placeholder="e.g. Modak")
        item_names = [item_name.strip()] if item_name.strip() else []
        apartment = st.text_input("Apartment Number", key="prasad_individual_apartment", placeholder="e.g. 1203")

    num_people = st.number_input("How many people are you bringing item for?", min_value=1, value=1)
    # Date picker, restrict to 26th to 30th August 2025
    min_date = datetime.date(2025, 8, 26)
    max_date = datetime.date(2025, 8, 30)
    seva_date = st.date_input("Date", value=min_date, min_value=min_date, max_value=max_date)
    # Only enable Morning Pooja if date is not 26th Aug
    pooja_options = ["Morning Pooja", "Evening Pooja"]
    if seva_date == datetime.date(2025, 8, 26):
        pooja_options = ["Evening Pooja"]
    pooja_time = st.radio("Pooja Time", pooja_options, horizontal=True)

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
        st.markdown("<h5 style='text-align:center;color:#4E342E;background:#FFF8E1;padding:8px;border-radius:10px;margin-bottom:0.5em;'>✏️🗑️ Edit/Delete Prasad Seva Entry</h5>", unsafe_allow_html=True)
        options = ["Select an option"] + [
            f"{df[df['ID']==x]['Names'].values[0]} | {pd.to_datetime(df[df['ID']==x]['Date'].values[0]).strftime('%d-%b-%Y')} | {df[df['ID']==x]['Pooja Time'].values[0]}"
            for x in df["ID"].tolist()
        ]
        selected_idx = st.selectbox("Choose an entry to Edit/Delete", range(len(options)), format_func=lambda i: options[i])
        entry = None
        if selected_idx != 0:
            selected_id = df["ID"].tolist()[selected_idx-1]
            entry = df[df["ID"]==selected_id].iloc[0]
        if entry is not None:
            edit_tab, delete_tab = st.tabs(["Edit", "Delete"])
            with edit_tab:
                # Type is not editable
                st.markdown(f"<b>Type:</b> " + (f"<span style='background-color:#B2DFDB;color:#4E342E;padding:4px 10px;border-radius:12px;font-weight:bold;'>👥 Group</span>" if entry['Type']=='Group' else f"<span style='background-color:#FFCCBC;color:#4E342E;padding:4px 10px;border-radius:12px;font-weight:bold;'>🧑 Individual</span>"), unsafe_allow_html=True)
                # Names and Apartment Number are not editable
                st.markdown(f"<b>Names:</b> <span style='font-size:16px;'>&#128100;</span> <b>{entry['Names']}</b>", unsafe_allow_html=True)
                new_item = st.text_input("Item Name", value=entry["Item Name"])
                new_num = st.number_input(
                    "How many people are you bringing item for?",
                    min_value=1,
                    value=int(entry["How many people are you bringing item for"]),
                    key=f"edit_num_people_{selected_id}"
                )
                st.markdown(f"<b>Apartment Number:</b> <span style='font-size:16px;'>&#127968;</span> <b>{entry['Apartemnt Number']}</b>", unsafe_allow_html=True)
                min_date = datetime.date(2025, 8, 26)
                max_date = datetime.date(2025, 8, 30)
                current_date = pd.to_datetime(entry["Date"]).date() if pd.notna(entry["Date"]) else min_date
                new_date = st.date_input("Date", value=current_date, min_value=min_date, max_value=max_date, key=f"edit_prasad_date_{selected_id}")
                pooja_options = ["Morning Pooja", "Evening Pooja"]
                if new_date == datetime.date(2025, 8, 26):
                    pooja_options = ["Evening Pooja"]
                pooja_index = 0 if entry["Pooja Time"]=="Morning Pooja" and "Morning Pooja" in pooja_options else 0
                new_pooja_time = st.radio("Pooja Time", pooja_options, index=pooja_index, key=f"edit_prasad_time_{selected_id}")
                if st.button("Update Prasad Seva"):
                    cursor.execute(
                        "UPDATE prasad_seva SET seva_type=%s, names=%s, item_name=%s, num_people=%s, apartment=%s, seva_date=%s, pooja_time=%s, status=%s WHERE id=%s",
                        (entry["Type"], entry["Names"], new_item, new_num, entry["Apartemnt Number"], new_date, new_pooja_time, 'active', selected_id)
                    )
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
