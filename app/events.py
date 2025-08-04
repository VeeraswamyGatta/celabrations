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
        cursor.execute("SELECT id, title, event_date, link FROM events ORDER BY event_date")
        events = cursor.fetchall()
        st.session_state.events = events
        st.session_state.refresh_events = False
    else:
        events = st.session_state.events

    if events:
        df_events = pd.DataFrame(events, columns=["ID", "Event Name", "Date", "Link"])

        def make_clickable(link):
            if link and link.strip() not in ("", "*"):
                return f"[Link]({link.strip()})"
            return ""

        df_events["Link"] = df_events["Link"].apply(make_clickable)
        display_df = df_events.drop(columns=["ID"])
        st.dataframe(display_df, use_container_width=True)

        selected_event_id = st.selectbox(
            "Select Event to Edit/Delete",
            df_events["ID"].tolist(),
            format_func=lambda x: df_events[df_events["ID"] == x]["Event Name"].values[0]
        )

        if selected_event_id:
            event_row = df_events[df_events["ID"] == selected_event_id].iloc[0]

            edited_title = st.text_input("Edit Event Title", value=event_row["Event Name"])
            edited_date = st.date_input(
                "Edit Event Date",
                value=pd.to_datetime(event_row["Date"]).date() if pd.notna(event_row["Date"]) else datetime.date.today()
            )
            current_link = event_row["Link"]
            if current_link.startswith("[Link](") and current_link.endswith(")"):
                current_link = current_link[6:-1]
            edited_link = st.text_input("Edit Event Link", value=current_link)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Event"):
                    if not edited_title.strip():
                        st.error("Event title is required.")
                    else:
                        link_to_store = None if edited_link.strip() in ("", "*") else edited_link.strip()
                        try:
                            cursor.execute(
                                "UPDATE events SET title=%s, event_date=%s, link=%s WHERE id=%s",
                                (edited_title, edited_date, link_to_store, selected_event_id)
                            )
                            conn.commit()
                            st.success("✅ Event updated successfully!")
                            # Send to all unique sponsor emails
                            cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                            sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                            send_email(
                                "Ganesh Chaturthi Event Updated",
                                f"Event updated:\nTitle: {edited_title}\nDate: {edited_date}\nLink: {edited_link if edited_link else 'N/A'}",
                                sponsor_emails
                            )
                            st.session_state.refresh_events = True
                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ Failed to update event: {e}")

            with col2:
                if st.button("Delete Event"):
                    try:
                        cursor.execute("DELETE FROM events WHERE id=%s", (selected_event_id,))
                        conn.commit()
                        st.success("🗑️ Event deleted successfully!")
                        cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                        sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                        send_email(
                            "Ganesh Chaturthi Event Deleted",
                            f"Event deleted:\nTitle: {event_row['Event Name']}\nDate: {event_row['Date']}\nLink: {event_row['Link']}",
                            sponsor_emails
                        )
                        st.session_state.refresh_events = True
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Failed to delete event: {e}")
    else:
        st.info("No events added yet.")

    st.markdown("---")
    st.markdown("### ➕ Add New Event")
    with st.form("add_event_form"):
        new_title = st.text_input("Event Title")
        new_date = st.date_input("Event Date", value=datetime.date.today())
        new_link = st.text_input("Event Link (optional)")
        submitted = st.form_submit_button("Add Event")
        if submitted:
            if not new_title.strip():
                st.error("Event title is required.")
            else:
                link_to_store = None if new_link.strip() in ("", "*") else new_link.strip()
                try:
                    cursor.execute(
                        "INSERT INTO events (title, event_date, link) VALUES (%s, %s, %s)",
                        (new_title, new_date, link_to_store)
                    )
                    conn.commit()
                    st.success("✅ Event added successfully!")
                    cursor.execute("SELECT DISTINCT email FROM sponsors WHERE email IS NOT NULL AND email != ''")
                    sponsor_emails = [row[0].strip() for row in cursor.fetchall() if row[0]]
                    send_email(
                        "New Ganesh Chaturthi Event Added",
                        f"Event Title: {new_title}\nEvent Date: {new_date}\nEvent Link: {new_link if new_link else 'N/A'}",
                        sponsor_emails
                    )
                    st.session_state.refresh_events = True
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Failed to add event: {e}")
