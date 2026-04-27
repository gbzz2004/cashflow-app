import streamlit as st
from auth import login_user

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0F1117;
    color: #E8EAF6;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    max-width: 460px !important;
    padding-top: 60px !important;
}

.login-header { text-align: center; margin-bottom: 32px; }
.login-logo { font-size: 3rem; margin-bottom: 8px; }
.login-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
}
.login-subtitle { font-size: 0.85rem; color: #6B7280; margin-top: 4px; }

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

.stButton > button, .stFormSubmitButton > button {
    background: linear-gradient(135deg, #4F8EF7 0%, #3B6FD4 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
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

.stAlert {
    border-radius: 10px !important;
    border: none !important;
    font-size: 0.85rem !important;
}
</style>

<div class="login-header">
    <div class="login-logo">💰</div>
    <div class="login-title">CashFlow</div>
    <div class="login-subtitle">Admin access only</div>
</div>
""", unsafe_allow_html=True)

# ── Already logged in ─────────────────────────────────────────────────────────
if st.session_state.get("user"):
    user = st.session_state["user"]
    st.success(f"✅ Logged in as **{user['business_name']}**")
    if st.button("Log out", use_container_width=True):
        del st.session_state["user"]
        st.rerun()
    st.info("Use the sidebar to navigate to your admin pages.")
    st.stop()

# ── Admin Login Form ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.form("login_form"):
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("Sign In →", use_container_width=True)
    if submitted:
        user = login_user(username, password)
        if user:
            st.session_state["user"] = user
            st.success(f"Welcome back, {user['business_name']}! 👋")
            st.rerun()
        else:
            st.error("❌ Invalid username or password.")