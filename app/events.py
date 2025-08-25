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
    st.markdown("""
    <div style='text-align:center;margin-bottom:18px;'>
        <span style='font-size:2.6em;vertical-align:middle;'>🪔</span>
        <span style='font-size:2.2em;font-weight:700;color:#2E7D32;letter-spacing:1px;'>Ganesh Chaturthi Events</span>
        <div style='font-size:1.1em;color:#388e3c;margin-top:6px;'>Celebrating joy, devotion, and togetherness</div>
    </div>
    """, unsafe_allow_html=True)

    # Admin credentials for add/edit/delete
    ADMIN_USERNAME = st.secrets["admin_user"]
    ADMIN_PASSWORD_BASE = st.secrets["admin_pass"]
    def get_admin_password():
        today_day = datetime.date.today().strftime('%d')
        return f"{ADMIN_PASSWORD_BASE}{today_day}"

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        # Show only the event table to non-admins first
        cursor.execute("SELECT id, title, event_date, event_time, link, description FROM events ORDER BY event_date, event_time")
        events = cursor.fetchall()
        if events:
            df_events = pd.DataFrame(events, columns=["ID", "Event Name", "Date", "Time", "Link", "Description"])
            display_df = df_events.drop(columns=["ID", "Link"])
            import pytz
            cst = pytz.timezone('US/Central')
            today_cst = datetime.datetime.now(cst).date()
            display_df['Date_obj'] = pd.to_datetime(display_df['Date'], errors='coerce').dt.date
            upcoming_df = display_df[display_df['Date_obj'] >= today_cst]
            past_df = display_df[display_df['Date_obj'] < today_cst]
            tab1, tab2 = st.tabs(["Active Events", "Past Events"])
            with tab1:
                if not upcoming_df.empty:
                    st.markdown("""
                    <style>
                    .event-card-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                        gap: 24px;
                        margin-top: 12px;
                    }
                    .event-card {
                        background: linear-gradient(120deg,#fffde7 60%,#e3f2fd 100%);
                        border-radius: 18px;
                        box-shadow: 0 4px 18px #e0e0e0;
                        padding: 24px 22px 18px 22px;
                        border: 2px solid #90caf9;
                        position: relative;
                        transition: box-shadow 0.2s;
                    }
                    .event-card:hover {
                        box-shadow: 0 8px 32px #90caf9;
                        border-color: #388e3c;
                    }
                    .event-title {
                        font-size: 1.35em;
                        font-weight: 700;
                        color: #1976d2;
                        margin-bottom: 6px;
                        letter-spacing: 0.5px;
                    }
                    .event-date {
                        font-size: 1.08em;
                        color: #388e3c;
                        font-weight: 600;
                        margin-bottom: 2px;
                    }
                    .event-time {
                        font-size: 1em;
                        color: #1565c0;
                        margin-bottom: 8px;
                    }
                    .event-desc {
                        font-size: 1em;
                        color: #333;
                        margin-bottom: 0;
                    }
                    </style>
                    <div class='event-card-grid'>
                    """, unsafe_allow_html=True)
                    for _, row in upcoming_df.iterrows():
                        st.markdown(f"""
                        <div class='event-card'>
                            <div class='event-title'>{row['Event Name']}</div>
                            <div class='event-date'>📅 {row['Date']}</div>
                            <div class='event-time'>⏰ {row['Time']}</div>
                            <div class='event-desc'>{row['Description']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No active events.")
            with tab2:
                if not past_df.empty:
                    st.markdown("""
                    <style>
                    .event-card-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                        gap: 24px;
                        margin-top: 12px;
                    }
                    .event-card {
                        background: linear-gradient(120deg,#fffde7 60%,#e3f2fd 100%);
                        border-radius: 18px;
                        box-shadow: 0 4px 18px #e0e0e0;
                        padding: 24px 22px 18px 22px;
                        border: 2px solid #90caf9;
                        position: relative;
                        transition: box-shadow 0.2s;
                        opacity:0.85;
                    }
                    .event-card:hover {
                        box-shadow: 0 8px 32px #90caf9;
                        border-color: #388e3c;
                    }
                    .event-title {
                        font-size: 1.35em;
                        font-weight: 700;
                        color: #1976d2;
                        margin-bottom: 6px;
                        letter-spacing: 0.5px;
                    }
                    .event-date {
                        font-size: 1.08em;
                        color: #388e3c;
                        font-weight: 600;
                        margin-bottom: 2px;
                    }
                    .event-time {
                        font-size: 1em;
                        color: #1565c0;
                        margin-bottom: 8px;
                    }
                    .event-desc {
                        font-size: 1em;
                        color: #333;
                        margin-bottom: 0;
                    }
                    </style>
                    <div class='event-card-grid'>
                    """, unsafe_allow_html=True)
                    for _, row in past_df.iterrows():
                        st.markdown(f"""
                        <div class='event-card'>
                            <div class='event-title'>{row['Event Name']}</div>
                            <div class='event-date'>📅 {row['Date']}</div>
                            <div class='event-time'>⏰ {row['Time']}</div>
                            <div class='event-desc'>{row['Description']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No past events.")
        else:
            st.info("No events added yet.")
    # Only show admin login prompt if not logged in as user

    # Admin is logged in: show full add/edit/delete UI
    if st.session_state.get('admin_logged_in', False):
        if "events" not in st.session_state or st.session_state.get("refresh_events", True):
            cursor.execute("SELECT id, title, event_date, event_time, link, description FROM events ORDER BY event_date, event_time")
            events = cursor.fetchall()
            st.session_state.events = events
            st.session_state.refresh_events = False
        else:
            events = st.session_state.events

        if events:
            df_events = pd.DataFrame(events, columns=["ID", "Event Name", "Date", "Time", "Link", "Description"])
            display_df = df_events.drop(columns=["ID", "Link"])
            st.markdown("""
            <style>
            .event-card-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 24px;
                margin-top: 12px;
            }
            .event-card {
                background: linear-gradient(120deg,#fffde7 60%,#e3f2fd 100%);
                border-radius: 18px;
                box-shadow: 0 4px 18px #e0e0e0;
                padding: 24px 22px 18px 22px;
                border: 2px solid #90caf9;
                position: relative;
                transition: box-shadow 0.2s;
            }
            .event-card:hover {
                box-shadow: 0 8px 32px #90caf9;
                border-color: #388e3c;
            }
            .event-title {
                font-size: 1.35em;
                font-weight: 700;
                color: #1976d2;
                margin-bottom: 6px;
                letter-spacing: 0.5px;
            }
            .event-date {
                font-size: 1.08em;
                color: #388e3c;
                font-weight: 600;
                margin-bottom: 2px;
            }
            .event-time {
                font-size: 1em;
                color: #1565c0;
                margin-bottom: 8px;
            }
            .event-desc {
                font-size: 1em;
                color: #333;
                margin-bottom: 0;
            }
            </style>
            <div class='event-card-grid'>
            """, unsafe_allow_html=True)
            for _, row in display_df.iterrows():
                st.markdown(f"""
                <div class='event-card'>
                    <div class='event-title'>{row['Event Name']}</div>
                    <div class='event-date'>📅 {row['Date']}</div>
                    <div class='event-time'>⏰ {row['Time']}</div>
                    <div class='event-desc'>{row['Description']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            # Send button to email the event table
            if st.button("Send Event Table by Email"):
                cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                html_table = display_df.to_html(index=False, border=1, justify='center')
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
            new_description = st.text_area("Description (optional)")
            submitted = st.form_submit_button("Add Event")
            if submitted:
                if not new_title.strip():
                    st.error("Event title is required.")
                else:
                    try:
                        if hasattr(cursor, 'execute') and hasattr(cursor.connection, 'account'):
                            cursor.execute(
                                "INSERT INTO events (id, title, event_date, event_time, link, description) VALUES (events_id_seq.NEXTVAL, %s, %s, %s, %s, %s)",
                                (new_title, new_date, new_time, None, new_description)
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO events (title, event_date, event_time, link, description) VALUES (%s, %s, %s, %s, %s)",
                                (new_title, new_date, new_time, None, new_description)
                            )
                        conn.commit()
                        st.success("✅ Event added successfully!")
                        # Get admin full name for audit trail
                        admin_full_name = st.session_state.get('admin_full_name', 'Unknown')
                        # Send to notification_emails only
                        cursor.execute("SELECT email FROM notification_emails")
                        notification_emails = [row[0] for row in cursor.fetchall() if row[0]]
                        html_table = f"""
                        <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
                          <tr><th>Title</th><td>{new_title}</td></tr>
                          <tr><th>Date</th><td>{new_date}</td></tr>
                          <tr><th>Time</th><td>{new_time}</td></tr>
                          <tr><th>Description</th><td>{new_description}</td></tr>
                        </table>
                        <br><b>Modified By:</b> {admin_full_name}
                        """
                        if notification_emails:
                            send_email(
                                "New Ganesh Chaturthi Event Added",
                                f"<b>New Event Added:</b><br><br>{html_table}",
                                notification_emails
                            )
                        st.session_state.refresh_events = True
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to add event: {e}")

        if st.session_state.get('admin_logged_in', False):
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
                        if pd.notna(event_row["Time"]):
                            if isinstance(event_row["Time"], datetime.time):
                                default_time = event_row["Time"]
                            else:
                                default_time = pd.to_datetime(event_row["Time"]).time()
                        else:
                            default_time = datetime.time(0,0)
                        edited_time = st.time_input("Edit Event Time", value=default_time, key="edit_event_time_bottom")
                        edited_description = st.text_area("Edit Description (optional)", value=event_row["Description"] if pd.notna(event_row["Description"]) else "", key="edit_event_description_bottom")
                        if st.button("Update Event", key="update_event_bottom"):
                            if not edited_title.strip():
                                st.error("Event title is required.")
                            else:
                                try:
                                    cursor.execute(
                                        "UPDATE events SET title=%s, event_date=%s, event_time=%s, link=%s, description=%s WHERE id=%s",
                                        (edited_title, edited_date, edited_time, None, edited_description, selected_event_id)
                                    )
                                    conn.commit()
                                    st.success("✅ Event updated successfully!")
                                    admin_full_name = st.session_state.get('admin_full_name', 'Unknown')
                                    cursor.execute("SELECT email FROM notification_emails")
                                    notification_emails = [row[0] for row in cursor.fetchall() if row[0]]
                                    html_table = f"""
                                    <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
                                      <tr><th>Title</th><td>{edited_title}</td></tr>
                                      <tr><th>Date</th><td>{edited_date}</td></tr>
                                      <tr><th>Time</th><td>{edited_time}</td></tr>
                                      <tr><th>Description</th><td>{edited_description}</td></tr>
                                    </table>
                                    <br><b>Modified By:</b> {admin_full_name}
                                    """
                                    if notification_emails:
                                        send_email(
                                            "Ganesh Chaturthi Event Updated",
                                            f"<b>Event Updated:</b><br><br>{html_table}",
                                            notification_emails
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
                        st.markdown(f"**Description:** {event_row['Description']}")
                        if st.button("Delete Event", key="delete_event_bottom"):
                            try:
                                cursor.execute("DELETE FROM events WHERE id=%s", (selected_event_id,))
                                conn.commit()
                                st.success("🗑️ Event deleted successfully!")
                                admin_full_name = st.session_state.get('admin_full_name', 'Unknown')
                                cursor.execute("SELECT email FROM notification_emails")
                                notification_emails = [row[0] for row in cursor.fetchall() if row[0]]
                                html_table = f"""
                                <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>
                                  <tr><th>Title</th><td>{event_row['Event Name']}</td></tr>
                                  <tr><th>Date</th><td>{event_row['Date']}</td></tr>
                                  <tr><th>Description</th><td>{event_row['Description']}</td></tr>
                                </table>
                                <br><b>Modified By:</b> {admin_full_name}
                                """
                                if notification_emails:
                                    send_email(
                                        "Ganesh Chaturthi Event Deleted",
                                        f"<b>Event deleted:</b><br><br>{html_table}",
                                        notification_emails
                                    )
                                st.session_state.refresh_events = True
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"❌ Failed to delete event: {e}")
            else:
                st.info("No events available to edit or delete.")
