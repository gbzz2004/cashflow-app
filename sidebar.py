import streamlit as st


def show_sidebar_logout():
    """Call this at the top of every page to show user info + logout in sidebar."""
    user = st.session_state.get("user")
    if user:
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"👤 **{user['business_name']}**")
            st.caption(f"@{user['username']}")
            if st.button("🚪 Log Out", use_container_width=True):
                del st.session_state["user"]
                st.rerun()
            st.markdown("---")
