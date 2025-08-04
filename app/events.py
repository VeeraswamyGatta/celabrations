import streamlit as st

# Custom button styles for events section
st.markdown('''
    <style>
    .stButton > button {
        background-color: #2E7D32 !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        margin-bottom: 0.5em;
    }
    .stButton > button:hover {
        background-color: #388e3c !important;
        color: #fff !important;
    }
    </style>
''', unsafe_allow_html=True)
import pandas as pd
import datetime
from .db import get_connection
from .email_utils import send_email

def events_tab():
    st.session_state['active_tab'] = 'Events'
    conn = get_connection()
    cursor = conn.cursor()
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>Ganesh Chaturthi Events</h1>", unsafe_allow_html=True)

    if "events" not in st.session_state or st.session_state.get("refresh_events", True):
        cursor.execute("SELECT id, title, event_date, event_time, link, description FROM events ORDER BY event_date, event_time")
        events = cursor.fetchall()
        st.session_state.events = events
        st.session_state.refresh_events = False
    else:
        events = st.session_state.events

    if events:
        df_events = pd.DataFrame(events, columns=["ID", "Event Name", "Date", "Time", "Link", "Description"])

        def make_clickable(link):
            if link and link.strip() not in ("", "*"):
                url = link.strip()
                return f'<a href="{url}" target="_blank">{url}</a>'
            return ""

        df_events["Link"] = df_events["Link"].apply(make_clickable)
        display_df = df_events.drop(columns=["ID"])
        st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Send button to email the event table
        if st.button("Send Event Table by Email"):
            cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
            sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
            # Format table as HTML
            html_table = df_events.drop(columns=["ID"]).to_html(index=False, border=1, justify='center')
            send_email(
                "Ganesh Chaturthi Events Table",
                f"<b>Current Events Table</b><br><br>{html_table}",
                sponsor_emails
            )
            st.success("✅ Event table sent by email!")

    else:
        st.info("No events added yet.")

    st.markdown("---")
    st.markdown("### ➕ Add New Event")
    with st.form("add_event_form"):
        new_title = st.text_input("Event Title")
        new_date = st.date_input("Event Date", value=datetime.date.today())
        new_time = st.time_input("Event Time", value=datetime.time(0,0))
        new_link = st.text_input("Event Link (optional)")
        new_description = st.text_area("Description (optional)")
        submitted = st.form_submit_button("Add Event")
        if submitted:
            if not new_title.strip():
                st.error("Event title is required.")
            else:
                link_to_store = None if new_link.strip() in ("", "*") else new_link.strip()
                try:
                    cursor.execute(
                        "INSERT INTO events (title, event_date, event_time, link, description) VALUES (%s, %s, %s, %s, %s)",
                        (new_title, new_date, new_time, link_to_store, new_description)
                    )
                    conn.commit()
                    st.success("✅ Event added successfully!")
                    cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                    sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                    # Format as table
                    html_table = f"""
                    <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
                      <tr><th>Title</th><td>{new_title}</td></tr>
                      <tr><th>Date</th><td>{new_date}</td></tr>
                      <tr><th>Time</th><td>{new_time}</td></tr>
                      <tr><th>Link</th><td>{new_link if new_link else 'N/A'}</td></tr>
                      <tr><th>Description</th><td>{new_description}</td></tr>
                    </table>
                    """
                    send_email(
                        "New Ganesh Chaturthi Event Added",
                        f"<b>New Event Added:</b><br><br>{html_table}",
                        sponsor_emails
                    )
                    st.session_state.refresh_events = True
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add event: {e}")

    # Only show edit/delete section if there are events
    if events:
        selected_event_id = st.selectbox(
            "Select Event to Edit/Delete",
            df_events["ID"].tolist(),
            format_func=lambda x: df_events[df_events["ID"] == x]["Event Name"].values[0],
            key="select_event_edit_delete_bottom"
        )

        if selected_event_id:
            event_row = df_events[df_events["ID"] == selected_event_id].iloc[0]
            tab1, tab2 = st.tabs(["Edit Event", "Delete Event"])

            with tab1:
                edited_title = st.text_input("Edit Event Title", value=event_row["Event Name"], key="edit_event_title_bottom")
                edited_date = st.date_input(
                    "Edit Event Date",
                    value=pd.to_datetime(event_row["Date"]).date() if pd.notna(event_row["Date"]) else datetime.date.today(),
                    key="edit_event_date_bottom"
                )
                # Handle if event_row['Time'] is already a datetime.time object
                if pd.notna(event_row["Time"]):
                    if isinstance(event_row["Time"], datetime.time):
                        default_time = event_row["Time"]
                    else:
                        default_time = pd.to_datetime(event_row["Time"]).time()
                else:
                    default_time = datetime.time(0,0)
                edited_time = st.time_input("Edit Event Time", value=default_time, key="edit_event_time_bottom")
                current_link = event_row["Link"]
                # If current_link is an HTML anchor tag, extract the URL
                if current_link and current_link.startswith('<a href="'):
                    # Extract URL between the first double quote after <a href=" and the next double quote
                    start = current_link.find('"') + 1
                    end = current_link.find('"', start)
                    current_link = current_link[start:end]
                elif current_link and current_link.startswith("[Link](") and current_link.endswith(")"):
                    current_link = current_link[6:-1]
                edited_link = st.text_input("Edit Event Link (optional)", value=current_link, key="edit_event_link_bottom")
                edited_description = st.text_area("Edit Description (optional)", value=event_row["Description"] if pd.notna(event_row["Description"]) else "", key="edit_event_description_bottom")
                if st.button("Update Event", key="update_event_bottom"):
                    if not edited_title.strip():
                        st.error("Event title is required.")
                    else:
                        link_to_store = None if edited_link.strip() in ("", "*") else edited_link.strip()
                        try:
                            cursor.execute(
                                "UPDATE events SET title=%s, event_date=%s, event_time=%s, link=%s, description=%s WHERE id=%s",
                                (edited_title, edited_date, edited_time, link_to_store, edited_description, selected_event_id)
                            )
                            conn.commit()
                            st.success("✅ Event updated successfully!")
                            # Send to all unique sponsor emails
                            cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                            sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                            # Format as table
                            html_table = f"""
                            <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
                              <tr><th>Title</th><td>{edited_title}</td></tr>
                              <tr><th>Date</th><td>{edited_date}</td></tr>
                              <tr><th>Time</th><td>{edited_time}</td></tr>
                              <tr><th>Link</th><td>{edited_link if edited_link else 'N/A'}</td></tr>
                              <tr><th>Description</th><td>{edited_description}</td></tr>
                            </table>
                            """
                            send_email(
                                "Ganesh Chaturthi Event Updated",
                                f"<b>Event updated:</b><br><br>{html_table}",
                                sponsor_emails
                            )
                            st.session_state.refresh_events = True
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ Failed to update event: {e}")

            with tab2:
                st.markdown("#### Delete this event?")
                st.markdown(f"**Title:** {event_row['Event Name']}")
                st.markdown(f"**Date:** {event_row['Date']}")
                st.markdown(f"**Time:** {event_row['Time']}")
                # Show link as plain URL if stored as anchor tag
                link_display = event_row['Link']
                if link_display and link_display.startswith('<a href="'):
                    start = link_display.find('"') + 1
                    end = link_display.find('"', start)
                    link_display = link_display[start:end]
                elif link_display and link_display.startswith("[Link](") and link_display.endswith(")"):
                    link_display = link_display[6:-1]
                st.markdown(f"**Link:** {link_display if link_display else 'N/A'}")
                st.markdown(f"**Description:** {event_row['Description']}")
                if st.button("Delete Event", key="delete_event_bottom"):
                    try:
                        cursor.execute("DELETE FROM events WHERE id=%s", (selected_event_id,))
                        conn.commit()
                        st.success("🗑️ Event deleted successfully!")
                        cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                        sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                        html_table = f"""
                        <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
                          <tr><th>Title</th><td>{event_row['Event Name']}</td></tr>
                          <tr><th>Date</th><td>{event_row['Date']}</td></tr>
                          <tr><th>Time</th><td>{event_row['Time']}</td></tr>
                          <tr><th>Link</th><td>{event_row['Link'] if event_row['Link'] else 'N/A'}</td></tr>
                          <tr><th>Description</th><td>{event_row['Description']}</td></tr>
                        </table>
                        """
                        send_email(
                            "Ganesh Chaturthi Event Deleted",
                            f"<b>Event deleted:</b><br><br>{html_table}",
                            sponsor_emails
                        )
                        st.session_state.refresh_events = True
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to delete event: {e}")
    else:
        st.info("No events available to edit or delete.")
