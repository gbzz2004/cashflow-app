import streamlit as st
from database import init_db
from auth import login_user, register_user
from styles import load_css

st.set_page_config(
    page_title="CashFlow",
    page_icon="💰",
    layout="wide"
)

st.markdown(load_css(), unsafe_allow_html=True)

init_db()

# ── Define all pages ──────────────────────────────────────────────────────────
login_page      = st.Page("pages/login.py",           title="Admin Login",  icon="🏢", default=True)
customer_portal = st.Page("pages/customer_portal.py", title="My Bookings",  icon="👤")
booking_page    = st.Page("pages/0_Book_Now.py",      title="↳ Book Now",   icon="🗓️")
dashboard       = st.Page("pages/1_Dashboard.py",     title="Dashboard",    icon="📊")
bookings        = st.Page("pages/2_Bookings.py",      title="Bookings",     icon="📅")
products        = st.Page("pages/3_Products.py",      title="Products",     icon="🛍️")
teams_page      = st.Page("pages/6_Teams.py",         title="Teams",        icon="👥")
predictions     = st.Page("pages/4_Predictions.py",   title="Predictions",  icon="🔮")
reports         = st.Page("pages/5_Reports.py",       title="Reports",      icon="📄")

# ── Route based on login state ────────────────────────────────────────────────
if st.session_state.get("user"):
    on_bookings = st.session_state.get("current_page") == "bookings"

    if on_bookings:
        pg = st.navigation(
            {
                "Admin": [dashboard, bookings, booking_page, products, teams_page, predictions, reports],
            },
            expanded=True
        )
    else:
        pg = st.navigation(
            {
                "Admin": [dashboard, bookings, products, teams_page, predictions, reports],
            },
            expanded=True
        )

elif st.session_state.get("customer"):
    pg = st.navigation(
        {
            "My Account": [customer_portal, booking_page],
        },
        expanded=True
    )
else:
    pg = st.navigation(
        {
            "": [customer_portal, login_page],
        },
        expanded=True
    )

pg.run()