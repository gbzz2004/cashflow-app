import streamlit as st
from database import init_db
from auth import login_user, register_user
from styles import load_css

# ✅ set_page_config MUST be first
st.set_page_config(
    page_title="CashFlow",
    page_icon="💰",
    layout="centered"
)

st.markdown(load_css(), unsafe_allow_html=True)

init_db()

# ── Define all pages ──────────────────────────────────────────────────────────
# ✅ Fixed
login_page      = st.Page("pages/login.py",           title="Admin Login",  icon="🏢")
customer_portal = st.Page("pages/customer_portal.py", title="My Bookings",  icon="👤", default=True)
booking_page    = st.Page("pages/0_Book_Now.py",      title="Book Now",     icon="🗓️")
dashboard       = st.Page("pages/1_Dashboard.py",     title="Dashboard",    icon="📊")
bookings        = st.Page("pages/2_Bookings.py",      title="Bookings",     icon="📅")
products        = st.Page("pages/3_Products.py",      title="Products",     icon="🛍️")
predictions     = st.Page("pages/4_Predictions.py",   title="Predictions",  icon="🔮")
reports         = st.Page("pages/5_Reports.py",       title="Reports",      icon="📄")

# ── Route based on login state ────────────────────────────────────────────────
if st.session_state.get("user"):
    # Admin logged in
    pg = st.navigation(
        {
            "Public":  [booking_page],
            "Admin":   [dashboard, bookings, products, predictions, reports],
        },
        expanded=True
    )
elif st.session_state.get("customer"):
    # Customer logged in
    pg = st.navigation(
        {
            "":           [booking_page],
            "My Account": [customer_portal],
        },
        expanded=True
    )
else:
    # Not logged in — show login only
    pg = st.navigation(
        {
            "": [login_page, customer_portal],
        },
        expanded=True
    )

pg.run()