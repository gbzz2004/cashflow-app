import streamlit as st
from auth import login_user, register_user

st.title("💰 CashFlow & Revenue Predictor")
st.caption("Admin system for small business owners")

# Already logged in
if st.session_state.get("user"):
    user = st.session_state["user"]
    st.success(f"You are logged in as **{user['business_name']}**")
    if st.button("Log out", use_container_width=True):
        del st.session_state["user"]
        st.rerun()
    st.info("Use the sidebar to navigate to your admin pages.")
    st.stop()

tab_login, tab_register = st.tabs(["Log In", "Create Account"])

with tab_login:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In", use_container_width=True)
        if submitted:
            user = login_user(username, password)
            if user:
                st.session_state["user"] = user
                st.success(f"Welcome back, {user['business_name']}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

with tab_register:
    with st.form("register_form"):
        new_business = st.text_input("Business Name")
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        new_confirm  = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)
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
