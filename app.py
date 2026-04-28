import streamlit as st
from database import init_db
from auth import login_user, register_user

init_db()

st.set_page_config(
    page_title="CashFlow Admin",
    page_icon="💰",
    layout="wide"
)

# ── Auth check — redirect to dashboard if already logged in ───────────────────
if st.session_state.get("user"):
    dashboard = st.Page("pages/1_Dashboard.py",    label="Dashboard",         icon="📊")
    bookings  = st.Page("pages/2_Bookings.py",     label="Bookings",          icon="📅")
    book_now  = st.Page("pages/6_Book_Now.py",     label="↳ Book Now",        icon="📆")
    products  = st.Page("pages/3_Products.py",     label="Products",          icon="🛍️")
    predict   = st.Page("pages/4_Predictions.py",  label="Predictions",       icon="🔮")
    reports   = st.Page("pages/5_Reports.py",      label="Reports",           icon="📄")

    pg = st.navigation({
        "Main": [dashboard],
        "Bookings": [bookings, book_now],
        "Business": [products, predict, reports],
    })
    pg.run()
    st.stop()

# ── Login / Register UI ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Playfair Display', serif !important; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1.2, 1])
with col2:
    st.markdown("""
    <div style="text-align:center;padding:40px 0 24px;">
        <div style="font-size:2.8rem;">💰</div>
        <h2 style="margin:8px 0 4px;font-family:Playfair Display,serif;">CashFlow</h2>
        <p style="color:#7F77DD;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">Revenue Predictor</p>
        <p style="color:#999;font-size:0.85rem;margin-top:4px;">Admin system for small business owners</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["Log In", "Create Account"])

    with tab_login:
        with st.form("login_form"):
            username  = st.text_input("Username")
            password  = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", use_container_width=True)
            if submitted:
                user = login_user(username, password)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab_register:
        with st.form("register_form"):
            new_business = st.text_input("Business Name")
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_confirm  = st.text_input("Confirm Password", type="password")
            submitted    = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                if not all([new_business, new_username, new_password]):
                    st.error("All fields are required.")
                elif new_password != new_confirm:
                    st.error("Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    ok, msg = register_user(new_username, new_password, new_business)
                    if ok:
                        st.success(msg + " Please log in.")
                    else:
                        st.error(msg)
