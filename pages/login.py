import streamlit as st
from auth import login_user, register_user


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0F1117;
    color: #E8EAF6;
}

/* Hide Streamlit default header */
#MainMenu, footer, header { visibility: hidden; }

/* Center the whole page */
.block-container {
    max-width: 460px !important;
    padding-top: 60px !important;
}

/* Logo + Title */
.login-header {
    text-align: center;
    margin-bottom: 32px;
}
.login-logo {
    font-size: 3rem;
    margin-bottom: 8px;
}
.login-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
}
.login-subtitle {
    font-size: 0.85rem;
    color: #6B7280;
    margin-top: 4px;
}

/* Card container */
.login-card {
    background: linear-gradient(135deg, #1A1D2E 0%, #1E2235 100%);
    border: 1px solid #2A2D3E;
    border-radius: 20px;
    padding: 36px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0F1117 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid #2A2D3E !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #6B7280 !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 8px 20px !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4F8EF7, #3B6FD4) !important;
    color: white !important;
}

/* Input fields */
.stTextInput > div > div > input {
    background-color: #0F1117 !important;
    border: 1px solid #2A2D3E !important;
    border-radius: 10px !important;
    color: #E8EAF6 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4F8EF7 !important;
    box-shadow: 0 0 0 3px rgba(79,142,247,0.15) !important;
}
.stTextInput label {
    color: #9EA3C0 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}

/* Buttons */
.stButton > button, .stFormSubmitButton > button {
    background: linear-gradient(135deg, #4F8EF7 0%, #3B6FD4 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(79,142,247,0.3) !important;
    margin-top: 8px !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(79,142,247,0.5) !important;
}

/* Alerts */
.stAlert {
    border-radius: 10px !important;
    border: none !important;
    font-size: 0.85rem !important;
}
</style>

<div class="login-header">
    <div class="login-logo">💰</div>
    <div class="login-title">CashFlow</div>
    <div class="login-subtitle">Revenue management for small businesses</div>
</div>
""", unsafe_allow_html=True)

# ── Already logged in ──────────────────────────────────────────────────────────
if st.session_state.get("user"):
    user = st.session_state["user"]
    st.success(f"✅ Logged in as **{user['business_name']}**")
    if st.button("Log out", use_container_width=True):
        del st.session_state["user"]
        st.rerun()
    st.info("Use the sidebar to navigate to your admin pages.")
    st.stop()

# ── Login / Register Tabs ──────────────────────────────────────────────────────
tab_login, tab_register = st.tabs(["  🔑  Login  ", "  ✏️  Create Account  "])

with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Log In →", use_container_width=True)
        if submitted:
            user = login_user(username, password)
            if user:
                st.session_state["user"] = user
                st.success(f"Welcome back, {user['business_name']}! 👋")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

with tab_register:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("register_form"):
        new_business = st.text_input("Business Name", placeholder="e.g. Juan's Photography")
        new_username = st.text_input("Username", placeholder="Choose a username")
        new_password = st.text_input("Password", type="password", placeholder="Min. 6 characters")
        new_confirm  = st.text_input("Confirm Password", type="password", placeholder="Repeat your password")
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Create Account →", use_container_width=True)
        if submitted:
            if not all([new_business, new_username, new_password]):
                st.error("❌ All fields are required.")
            elif new_password != new_confirm:
                st.error("❌ Passwords do not match.")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters.")
            else:
                ok, msg = register_user(new_username, new_password, new_business)
                if ok:
                    st.success("✅ " + msg + " Please log in.")
                else:
                    st.error("❌ " + msg)