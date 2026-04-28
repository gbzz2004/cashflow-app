import streamlit as st


@st.dialog("Confirm Logout")
def logout_dialog():
    st.warning("⚠️ Are you sure you want to log out?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Log Out", use_container_width=True, type="primary"):
            del st.session_state["user"]
            st.rerun()
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()


def show_sidebar_logout():
    """Shows user info and logout button in sidebar."""
    user = st.session_state.get("user")
    if not user:
        return

    with st.sidebar:
        st.markdown("---")

        # ── User info + logout ────────────────────────────────────────────────
        st.markdown(f"👤 **{user['business_name']}**")
        st.caption(f"@{user['username']}")
        if st.button("🚪 Log Out", use_container_width=True, key="nav_logout"):
            st.session_state["confirm_logout"] = True

        if st.session_state.get("confirm_logout"):
            st.session_state["confirm_logout"] = False
            logout_dialog()

        st.markdown("---")