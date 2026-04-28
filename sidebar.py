import streamlit as st


# Map each page file to its display label and icon
NAV_PAGES = {
    "dashboard":    ("pages/1_Dashboard.py",    "🏠", "Dashboard"),
    "bookings":     ("pages/2_Bookings.py",     "📋", "Bookings"),
    "book_now":     ("pages/3_Book_Now.py",     "➕", "Book Now"),       # submenu of Bookings
    "products":     ("pages/4_Products.py",     "📦", "Products"),
    "predictions":  ("pages/5_Predictions.py",  "📈", "Predictions"),
    "reports":      ("pages/6_Reports.py",      "📄", "Reports"),
}


def show_sidebar_logout():
    """Shows navigation menu, user info, and logout button in sidebar."""
    user = st.session_state.get("user")
    if not user:
        return

    with st.sidebar:
        # ── Brand ─────────────────────────────────────────────────────────────
        st.markdown(
            '<div style="padding:10px 0 6px;">'
            '<span style="font-size:1.3rem;font-weight:700;letter-spacing:0.02em;">💰 CashFlow</span>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown("---")

        # ── Navigation ────────────────────────────────────────────────────────
        st.markdown(
            '<p style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;'
            'color:#888;margin:0 0 6px 4px;font-weight:600;">Menu</p>',
            unsafe_allow_html=True
        )

        # Dashboard
        if st.button("🏠  Dashboard", use_container_width=True, key="nav_dashboard"):
            st.switch_page("pages/1_Dashboard.py")

        # Bookings (parent)
        if st.button("📋  Bookings", use_container_width=True, key="nav_bookings"):
            st.switch_page("pages/2_Bookings.py")

        # Book Now (submenu — indented)
        st.markdown(
            '<div style="padding-left:18px;">',
            unsafe_allow_html=True
        )
        if st.button("➕  Book Now", use_container_width=True, key="nav_book_now"):
            st.switch_page("pages/3_Book_Now.py")
        st.markdown("</div>", unsafe_allow_html=True)

        # Products
        if st.button("📦  Products", use_container_width=True, key="nav_products"):
            st.switch_page("pages/4_Products.py")

        # Predictions
        if st.button("📈  Predictions", use_container_width=True, key="nav_predictions"):
            st.switch_page("pages/5_Predictions.py")

        # Reports
        if st.button("📄  Reports", use_container_width=True, key="nav_reports"):
            st.switch_page("pages/6_Reports.py")

        st.markdown("---")

        # ── User info + logout ─────────────────────────────────────────────────
        st.markdown(f"👤 **{user['business_name']}**")
        st.caption(f"@{user['username']}")
        if st.button("🚪 Log Out", use_container_width=True, key="nav_logout"):
            del st.session_state["user"]
            st.switch_page("app.py")

        st.markdown("---")