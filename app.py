
import streamlit as st
import datetime
from app.db import get_connection, create_tables
from app.sponsorship import sponsorship_tab
from app.events import events_tab
from app.statistics import statistics_tab
from app.admin import admin_tab


st.set_page_config(page_title="Ganesh Chaturthi 2025", layout="wide")

# ---------- Constants ----------

ADMIN_USERNAME = st.secrets["admin_user"]
ADMIN_PASSWORD_BASE = st.secrets["admin_pass"]
def get_admin_password():
    today_day = datetime.date.today().strftime('%d')
    return f"{ADMIN_PASSWORD_BASE}{today_day}"

# ---------- DB Setup ----------
conn = get_connection()
create_tables(conn)


# ---------- Styling ----------
st.markdown("""
<style>
    .block-container {
        padding: 2rem;
        border-radius: 10px;
    }
    label > div[data-testid="stMarkdownContainer"] > p:first-child:before {
        content: "* ";
        color: red;
    }
</style>
""", unsafe_allow_html=True)


# Initialize admin login state if not set
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ---------- Tabs ----------
tabs = st.tabs(["🎉 Sponsorship & Donation", "📅 Events", "📊 Statistics", "🔐 Admin"])

# ---------- Tab 1: Sponsorship ----------
with tabs[0]:
    sponsorship_tab()

# ---------- Tab 2: Events ----------
with tabs[1]:
    events_tab()

# ---------- Tab 3: Statistics (with admin authentication) ----------
with tabs[2]:
    if not st.session_state.admin_logged_in:
        st.markdown("<h1 style='text-align: center; color: #6A1B9A;'>Admin Login Required</h1>", unsafe_allow_html=True)
        with st.form("admin_login_stats"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            login = st.form_submit_button("Login")

        if login:
            if user == ADMIN_USERNAME and pwd == get_admin_password():
                st.session_state.admin_logged_in = True
                st.success("✅ Admin access granted!")
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials")
    else:
        statistics_tab()

# ---------- Tab 4: Admin ----------
with tabs[3]:
    if not st.session_state.admin_logged_in:
        with st.form("admin_login_admin"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            login = st.form_submit_button("Login")

        if login:
            if user == ADMIN_USERNAME and pwd == get_admin_password():
                st.session_state.admin_logged_in = True
                st.success("✅ Admin access granted!")
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials")
    else:
        admin_tab()
