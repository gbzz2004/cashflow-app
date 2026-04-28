import streamlit as st


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
            del st.session_state["user"]
            st.rerun()

        st.markdown("---")