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

# ✅ CSS loads after
st.markdown(load_css(), unsafe_allow_html=True)

init_db()

# ── Define all pages ──────────────────────────────────────────────────────────
login_page       = st.Page("pages/login.py",              title="Admin",        icon="🏢")
booking_page     = st.Page("pages/0_Book_Now.py",         title="Book Now",     icon="🗓️", default=True)
customer_portal  = st.Page("pages/customer_portal.py",    title="My Bookings",  icon="👤")
dashboard        = st.Page("pages/1_Dashboard.py",        title="Dashboard",    icon="📊")
bookings         = st.Page("pages/2_Bookings.py",         title="Bookings",     icon="📅")
products         = st.Page("pages/3_Products.py",         title="Products",     icon="🛍️")
predictions      = st.Page("pages/4_Predictions.py",      title="Predictions",  icon="🔮")
reports          = st.Page("pages/5_Reports.py",          title="Reports",      icon="📄")

# ── Route based on login state ────────────────────────────────────────────────
if st.session_state.get("user"):
    # Admin is logged in
    pg = st.navigation(
        {
            "Public":   [booking_page],
            "Admin":    [dashboard, bookings, products, predictions, reports],
        },
        expanded=True
    )
elif st.session_state.get("customer"):
    # Customer is logged in
    pg = st.navigation(
        {
            "":          [booking_page],
            "My Account": [customer_portal],
        },
        expanded=True
    )
else:
    # Not logged in
    pg = st.navigation(
        {
            "":          [booking_page],
            "Customer":  [customer_portal],
            "Admin":     [login_page],
        },
        expanded=True
    )

pg.run()