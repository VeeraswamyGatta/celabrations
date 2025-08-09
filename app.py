
import streamlit as st
from streamlit_option_menu import option_menu
import datetime
from app.db import get_connection, create_tables
from app.sponsorship import sponsorship_tab
from app.events import events_tab
from app.statistics import statistics_tab
from app.admin import admin_tab


st.set_page_config(page_title="Ganesh Chaturthi 2025", page_icon="🙏", layout="wide")

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



# ---------- Sidebar Navigation with Option Menu ----------
with st.sidebar:
    main_menu = option_menu(
        "Menu",
        ["🎉 Sponsorship & Donation", "📅 Events", "📊 Statistics", "🔐 Admin"],
        icons=["gift", "calendar-event", "bar-chart", "lock"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

if main_menu == "🎉 Sponsorship & Donation":
    sponsorship_tab()
elif main_menu == "📅 Events":
    events_tab()
elif main_menu == "📊 Statistics":
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
elif main_menu == "🔐 Admin":
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
        # Admin submenu
        admin_menu = option_menu(
            "Admin Sections",
            ["Sponsorship Items", "Edit/Delete Sponsorship Record"],
            icons=["list-task", "pencil-square"],
            menu_icon="gear",
            default_index=0,
            orientation="vertical"
        )
        admin_tab(menu=admin_menu)
