import streamlit as st
from streamlit_option_menu import option_menu
import datetime
from app.db import get_connection
from app.sponsorship import sponsorship_tab
from app.events import events_tab
from app.statistics import statistics_tab
from app.admin import admin_tab


st.set_page_config(page_title="Terrazzo Ganesh Celebrations 2025", page_icon="🙏", layout="wide")
from PIL import Image
ganesh_img = Image.open("ganesh.png")


# ---------- Constants ----------

ADMIN_USERNAME = st.secrets["admin_user"]
ADMIN_PASSWORD_BASE = st.secrets["admin_pass"]
import pytz
def get_admin_password():
    cst = pytz.timezone('US/Central')
    now_utc = datetime.datetime.now(pytz.utc)
    now_cst = now_utc.astimezone(cst)
    today_day = now_cst.strftime('%d')
    return f"{ADMIN_PASSWORD_BASE}{today_day}"

# ---------- DB Setup ----------

conn = get_connection()


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




# ---------- User Login on Landing Page ----------
USER_USERNAME = st.secrets["user_username"]
USER_PASSWORD = st.secrets["user_password"]

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

show_login_form = False
# Only show the initial menu if not logged in
if not st.session_state.user_logged_in and not st.session_state.admin_logged_in:
    # Show only Prasad Seva, Events, Login
    initial_menu = option_menu(
        "Menu",
        ["Prasad Seva", "Events", "Login"],
        icons=["award", "calendar-event", "box-arrow-in-right"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )
    if initial_menu == "Prasad Seva":
        from app.prasad_seva import prasad_seva_tab
        prasad_seva_tab()
    elif initial_menu == "Events":
        from app.events import events_tab
        events_tab()
    elif initial_menu == "Login":
        show_login_form = True
else:
    show_login_form = False
if show_login_form:
    role = st.selectbox("Login as", ["User", "Admin"], index=0)
    if role == "User":
        with st.form("user_login_form"):
            user = st.text_input("👤 Username", key="user_login_username")
            pwd = st.text_input("🔒 Password", type="password", key="user_login_password")
            login = st.form_submit_button("Login", help="Login as User", use_container_width=True)
        if login:
            user = user.strip().lower()
            pwd = pwd.strip().lower()
            errors = []
            if not user:
                errors.append("Username is required.")
            if not pwd:
                errors.append("Password is required.")
            apartment = None
            base_pwd = USER_PASSWORD
            apt_num = None
            if pwd.startswith(base_pwd) and len(pwd) > len(base_pwd):
                apt_str = pwd[len(base_pwd):]
                if apt_str.isdigit():
                    apt_num = int(apt_str)
                    if not (100 <= apt_num <= 1600):
                        pass
                    else:
                        apartment = apt_str
                else:
                    errors.append("Apartment Number must be numeric and follow the password.")
            elif pwd == base_pwd:
                apartment = None
            else:
                errors.append("Username or password is incorrect.")
            if user != USER_USERNAME:
                errors.append("Invalid username.")
            if errors:
                st.markdown("""
                <div style='background:#ffebee;border-radius:10px;padding:16px 18px;margin-bottom:12px;border:1px solid #e57373;'>
                    <span style='color:#d32f2f;font-size:1.1em;font-weight:bold;'>⚠️ Login Error</span>
                    <ul style='color:#d32f2f;margin-top:8px;'>
                        {} 
                    </ul>
                </div>
                """.format("".join([f"<li>{err}</li>" for err in errors])), unsafe_allow_html=True)
                st.info("For login issues, please reach out in the Ganesh Chaturthi celebrations 2025 WhatsApp group.")
            else:
                st.session_state.user_logged_in = True
                st.session_state.user_apartment = apartment if apartment else ""
                st.success("✅ User login successful!")
                st.rerun()
    else:
        with st.form("admin_login_form"):
            user = st.text_input("👤 Admin Username", key="admin_login_username")
            pwd = st.text_input("🔒 Admin Password", type="password", key="admin_login_password")
            full_name = st.text_input("📝 Your Full Name (for audit trail) *", key="admin_login_full_name", placeholder="Enter your full name")
            login = st.form_submit_button("Login", help="Login as Admin", use_container_width=True)
        if login:
            user = user.strip().lower()
            pwd = pwd.strip().lower()
            full_name = full_name.strip()
            errors = []
            if not user:
                errors.append("Username is required.")
            if not pwd:
                errors.append("Password is required.")
            if not full_name:
                errors.append("Your Full Name is required for audit trail.")
            if user == ADMIN_USERNAME and pwd == get_admin_password() and not errors:
                st.session_state.admin_logged_in = True
                st.session_state.admin_full_name = full_name
                st.success("✅ Admin access granted!")
                st.rerun()
            else:
                if not (user == ADMIN_USERNAME and pwd == get_admin_password()) and not errors:
                    errors.append("❌ Invalid admin credentials")
                if errors:
                    st.markdown("""
                    <div style='background:#ffebee;border-radius:10px;padding:16px 18px;margin-bottom:12px;border:1px solid #e57373;'>
                        <span style='color:#d32f2f;font-size:1.1em;font-weight:bold;'>⚠️ Login Error</span>
                        <ul style='color:#d32f2f;margin-top:8px;'>
                            {} 
                        </ul>
                    </div>
                    """.format("".join([f"<li>{err}</li>" for err in errors])), unsafe_allow_html=True)
else:
    # Add Ganesh image to the top-right corner (after login)
    st.markdown(
        """
        <style>
        .ganesh-corner-st {
            position: fixed;
            top: 40px;
            right: 24px;
            z-index: 9999;
            width: 80px;
            height: 90px;
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
    # (Removed: do not show Ganesh image at the bottom)
    # Show menu based on role after successful login
    if st.session_state.admin_logged_in:
        menu_items = ["Contributions", "Events", "Prasad Seva", "Statistics", "Expenses", "Admin"]
        menu_icons = ["gift", "calendar-event", "award", "bar-chart", "cash-coin", "lock"]
    elif st.session_state.user_logged_in:
        menu_items = ["Contributions", "Events", "Prasad Seva", "Statistics", "Expenses"]
        menu_icons = ["gift", "calendar-event", "award", "bar-chart", "cash-coin"]
    else:
        menu_items = []
        menu_icons = []
    if menu_items:
        main_menu = option_menu(
            "Menu",
            menu_items,
            icons=menu_icons,
            menu_icon="cast",
            default_index=0,
            orientation="horizontal"
        )

        if main_menu == "Contributions":
            sponsorship_tab()
        elif main_menu == "Events":
            if 'admin_full_name' not in st.session_state or not st.session_state['admin_full_name']:
                st.session_state['admin_full_name'] = ''
            events_tab()
        elif main_menu == "Prasad Seva":
            from app.prasad_seva import prasad_seva_tab
            prasad_seva_tab()
        elif main_menu == "Statistics":
            # Set is_admin flag for statistics
            st.session_state['is_admin'] = st.session_state.admin_logged_in
            statistics_tab()
        elif main_menu == "Expenses":
            from app.expenses import expenses_tab
            expenses_tab()
        elif st.session_state.admin_logged_in and main_menu == "Admin":
            if 'admin_full_name' not in st.session_state:
                st.session_state.admin_full_name = ''
            admin_menu = option_menu(
                "Admin Sections",
                [
                    "Payment Details",
                    "Sponsorship Record",
                    "Sponsorship Items",
                    "Manage Notification Emails"
                ],
                icons=["credit-card", "pencil-square", "list-task", "envelope-fill"],
                menu_icon="gear",
                default_index=0,
                orientation="vertical"
            )
            admin_tab(menu=admin_menu)
