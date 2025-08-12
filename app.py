
import streamlit as st
from streamlit_option_menu import option_menu
import datetime
from app.db import get_connection, create_tables
from app.sponsorship import sponsorship_tab
from app.events import events_tab
from app.statistics import statistics_tab
from app.admin import admin_tab


st.set_page_config(page_title="Terrazzo Ganesh Celebrations 2025", page_icon="🙏", layout="wide")
# Add Ganesh image to the top-right corner
# Show Ganesh image in the top-right corner using st.image and CSS
from PIL import Image
ganesh_img = Image.open("ganesh.png")
st.markdown(
    """
    <style>
    .ganesh-corner-st {
        position: fixed;
        top: 18px;
        right: 24px;
        z-index: 9999;
        width: 70px;
        height: 70px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        background: #fff;
        padding: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    <div class="ganesh-corner-st" id="ganesh-corner-st"></div>
    <script>
    const img = window.parent.document.createElement('img');
    img.src = '/app/static/ganesh.png';
    img.alt = 'Ganesh';
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.borderRadius = '12px';
    document.getElementById('ganesh-corner-st').appendChild(img);
    </script>
    """,
    unsafe_allow_html=True
)
# Fallback for environments where JS injection doesn't work (e.g., Streamlit Cloud)
st.image(ganesh_img, width=70)

# ---------- Constants ----------

ADMIN_USERNAME = st.secrets["admin_user"]
ADMIN_PASSWORD_BASE = st.secrets["admin_pass"]
def get_admin_password():
    today_day = datetime.date.today().strftime('%d')
    return f"{ADMIN_PASSWORD_BASE}{today_day}"

# ---------- DB Setup ----------

conn = get_connection()
create_tables(conn)
from app.db import create_transfers_table
create_transfers_table(conn)


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
    if 'admin_full_name' not in st.session_state or not st.session_state['admin_full_name']:
        st.session_state['admin_full_name'] = ''
    events_tab()
elif main_menu == "📊 Statistics":
    if not st.session_state.admin_logged_in:
        st.markdown("<h1 style='text-align: center; color: #6A1B9A;'>Admin Login Required</h1>", unsafe_allow_html=True)
        with st.form("admin_login_stats"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            full_name = st.text_input("Your Full Name (for audit trail) *", key="stats_login_full_name", placeholder="Enter your full name")
            login = st.form_submit_button("Login")
        if login:
            if not user.strip():
                st.error("Username is required.")
            elif not pwd.strip():
                st.error("Password is required.")
            elif not full_name.strip():
                st.error("Your Full Name is required for audit trail.")
            elif user == ADMIN_USERNAME and pwd == get_admin_password():
                st.session_state.admin_logged_in = True
                st.session_state.admin_full_name = full_name.strip()
                st.success("✅ Admin access granted!")
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials")
    else:
        if 'admin_full_name' not in st.session_state or not st.session_state['admin_full_name']:
            st.session_state['admin_full_name'] = ''
            st.warning("Your Full Name (for audit trail) is required. Please log out and log in again.")
        else:
            statistics_tab()
elif main_menu == "🔐 Admin":
    if not st.session_state.admin_logged_in:
        with st.form("admin_login_admin"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            full_name = st.text_input("Your Full Name (for audit trail) *", key="admin_login_full_name", placeholder="Enter your full name")
            login = st.form_submit_button("Login")
        if login:
            if not user.strip():
                st.error("Username is required.")
            elif not pwd.strip():
                st.error("Password is required.")
            elif not full_name.strip():
                st.error("Your Full Name is required for audit trail.")
            elif user == ADMIN_USERNAME and pwd == get_admin_password():
                st.session_state.admin_logged_in = True
                st.session_state.admin_full_name = full_name.strip()
                st.success("✅ Admin access granted!")
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials")
    else:
        # Admin submenu
        if 'admin_full_name' not in st.session_state:
            st.session_state.admin_full_name = ''
        admin_menu = option_menu(
            "Admin Sections",
            [
                "Sponsorship Items",
                "Sponsorship Record",
                "Manage Notification Emails",
                "Payment Details"
            ],
            icons=["list-task", "pencil-square", "envelope-fill", "credit-card"],
            menu_icon="gear",
            default_index=0,
            orientation="vertical"
        )
        admin_tab(menu=admin_menu)
