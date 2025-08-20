import streamlit as st
from streamlit_option_menu import option_menu
import datetime
from app.db import get_connection, create_tables
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




# ---------- User Login on Landing Page ----------
USER_USERNAME = st.secrets["user_username"]
USER_PASSWORD = st.secrets["user_password"]

if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

if not st.session_state.user_logged_in and not st.session_state.admin_logged_in:
    st.markdown("""
    <style>
    .stImage > img {
        margin-top: 24px;
        max-width: 90px;
        height: auto;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    @media (max-width: 600px) {
        .stImage > img {
            margin-top: 36px !important;
            max-width: 70px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    st.image(ganesh_img, width=90)
    st.markdown("""
    <style>
    .login-card {
        max-width: 400px;
        margin: 10px auto 0 auto;
        background: #fff;
        border-radius: 16px;
        box-shadow: 0 2px 16px rgba(21,101,192,0.12);
        padding: 32px 28px 24px 28px;
        text-align: center;
    }
    .login-title {
        color: #1565C0;
        font-size: 2em;
        font-weight: bold;
        margin-bottom: 12px;
    }
    .login-input {
        margin-bottom: 18px;
    }
    .login-btn {
        background: #1565C0;
        color: #fff;
        border-radius: 8px;
        font-size: 1.1em;
        padding: 8px 32px;
        border: none;
        margin-top: 10px;
        cursor: pointer;
    }
    .login-btn:hover {
        background: #0d47a1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Removed empty login card div that caused extra box
    st.markdown("<div class='login-title'>Login</div>", unsafe_allow_html=True)
    role = st.selectbox("Login as", ["User", "Admin"], index=0)
    if role == "User":
        with st.form("user_login_form"):
            user = st.text_input("👤 Username", key="user_login_username")
            pwd = st.text_input("🔒 Password", type="password", key="user_login_password")
            login = st.form_submit_button("Login", help="Login as User", use_container_width=True)
        if login:
            errors = []
            if not user.strip():
                errors.append("Username is required.")
            if not pwd.strip():
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
            errors = []
            if not user.strip():
                errors.append("Username is required.")
            if not pwd.strip():
                errors.append("Password is required.")
            if not full_name.strip():
                errors.append("Your Full Name is required for audit trail.")
            if user == ADMIN_USERNAME and pwd == get_admin_password() and not errors:
                st.session_state.admin_logged_in = True
                st.session_state.admin_full_name = full_name.strip()
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
    # Removed closing div for login card
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
    st.image(ganesh_img, width=70)
    # Show contributions page after successful login
    if st.session_state.admin_logged_in:
        menu_items = ["Contributions", "Events", "Prasad Seva", "Statistics", "Expenses", "Admin"]
        menu_icons = ["gift", "calendar-event", "award", "bar-chart", "cash-coin", "lock"]
    else:
        menu_items = ["Contributions", "Events", "Prasad Seva", "Statistics", "Expenses"]
        menu_icons = ["gift", "calendar-event", "award", "bar-chart", "cash-coin"]
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
