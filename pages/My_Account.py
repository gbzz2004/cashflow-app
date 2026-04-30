import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import SessionLocal, User
from auth import hash_password, verify_password

# ── Styles (matching admin UI) ────────────────────────────────────────────────
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Playfair Display', serif !important; }
.block-container { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
.stCaption { opacity: 0.7; }
</style>''', unsafe_allow_html=True)

# ── Auth Check ────────────────────────────────────────────────────────────────
customer = st.session_state.get("customer")
if not customer:
    st.warning("Please sign in to access your account settings.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown(f"👤 **{customer['full_name']}**")
    st.caption(f"@{customer['username']}")
    if st.button("🚪 Sign Out", use_container_width=True, key="account_signout_btn"):
        st.session_state["confirm_account_logout"] = True
        st.rerun()
    st.markdown("---")

# ── Logout dialog ─────────────────────────────────────────────────────────────
@st.dialog("Confirm Sign Out")
def logout_dialog():
    st.warning("⚠️ Are you sure you want to sign out?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Sign Out", use_container_width=True, type="primary"):
            del st.session_state["customer"]
            st.rerun()
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state["confirm_account_logout"] = False
            st.rerun()

if st.session_state.get("confirm_account_logout"):
    st.session_state["confirm_account_logout"] = False
    logout_dialog()

# ── Confirm Name Change Dialog ────────────────────────────────────────────────
@st.dialog("Confirm Name Change")
def confirm_name_dialog():
    pending = st.session_state.get("pending_name_change")
    if not pending:
        return
    st.markdown(f"""
    <div style="background:#1A1D2E;border:1px solid #2A2D3E;border-radius:14px;padding:20px;margin:12px 0;">
        <div style="font-size:0.9rem;line-height:2.2;color:#E8EAF6;">
            👤 <strong>Current name:</strong> {pending['old_name']}<br>
            ✏️ <strong>New name:</strong> {pending['new_name']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Are you sure you want to update your full name?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Update", use_container_width=True, type="primary"):
            db  = SessionLocal()
            row = db.query(User).filter(User.id == customer["id"]).first()
            if row:
                row.business_name = pending["new_name"]
                db.commit()
                st.session_state["customer"]["full_name"] = pending["new_name"]
            db.close()
            st.session_state.pop("pending_name_change", None)
            st.session_state["account_success"] = f"Name updated to '{pending['new_name']}'."
            st.rerun()
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.pop("pending_name_change", None)
            st.rerun()

# ── Confirm Password Change Dialog ────────────────────────────────────────────
@st.dialog("Confirm Password Change")
def confirm_password_dialog():
    if not st.session_state.get("pending_password_change"):
        return
    st.warning("⚠️ Are you sure you want to update your password? You will need to use the new password on your next sign in.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Update", use_container_width=True, type="primary"):
            pending = st.session_state["pending_password_change"]
            db  = SessionLocal()
            row = db.query(User).filter(User.id == customer["id"]).first()
            if row:
                row.hashed_password = hash_password(pending["new_pw"])
                db.commit()
            db.close()
            st.session_state.pop("pending_password_change", None)
            st.session_state["account_success"] = "Password updated successfully."
            st.rerun()
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.pop("pending_password_change", None)
            st.rerun()

# ── Trigger dialogs ───────────────────────────────────────────────────────────
if st.session_state.get("pending_name_change"):
    confirm_name_dialog()

if st.session_state.get("pending_password_change"):
    confirm_password_dialog()

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown(
    '<div style="border-left:4px solid #7F77DD;padding-left:16px;margin-bottom:4px;">'
    '<span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;'
    'color:#7F77DD;font-weight:600;">Account</span>'
    '<h2 style="margin:4px 0 0;font-family:Playfair Display,serif;'
    'color:var(--text-color, #1a1a2e);">My Account</h2>'
    '</div>',
    unsafe_allow_html=True
)
st.caption("Manage your profile and security settings.")
st.divider()

# ── Success message ───────────────────────────────────────────────────────────
if st.session_state.get("account_success"):
    st.success("✅ " + st.session_state.pop("account_success"))

# ── Current info ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:var(--background-color,#fff);border:1px solid rgba(127,119,221,0.2);
            border-radius:12px;padding:18px 22px;margin-bottom:24px;">
    <div style="font-size:0.75rem;color:#7F77DD;text-transform:uppercase;
                letter-spacing:0.08em;font-weight:600;margin-bottom:10px;">Current Profile</div>
    <div style="font-size:0.95rem;line-height:2;color:var(--text-color,#333);">
        👤 <strong>Full Name:</strong> {customer['full_name']}<br>
        🔑 <strong>Username:</strong> @{customer['username']}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Change Full Name ──────────────────────────────────────────────────────────
with st.expander("✏️ Change Full Name", expanded=False):
    with st.form("change_name_form"):
        new_name = st.text_input(
            "New Full Name",
            value=customer["full_name"],
            placeholder="Enter your new full name"
        )
        if st.form_submit_button("Save Name", use_container_width=True):
            if not new_name.strip():
                st.error("❌ Name cannot be empty.")
            elif new_name.strip() == customer["full_name"]:
                st.warning("⚠️ That's already your current name.")
            else:
                st.session_state["pending_name_change"] = {
                    "old_name": customer["full_name"],
                    "new_name": new_name.strip()
                }
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── Change Password ───────────────────────────────────────────────────────────
with st.expander("🔒 Change Password", expanded=False):
    with st.form("change_password_form"):
        current_pw = st.text_input(
            "Current Password", type="password",
            placeholder="Enter your current password"
        )
        new_pw = st.text_input(
            "New Password", type="password",
            placeholder="Min. 6 characters"
        )
        confirm_pw = st.text_input(
            "Confirm New Password", type="password",
            placeholder="Repeat new password"
        )
        if st.form_submit_button("Update Password", use_container_width=True):
            if not all([current_pw, new_pw, confirm_pw]):
                st.error("❌ All fields are required.")
            elif len(new_pw) < 6:
                st.error("❌ New password must be at least 6 characters.")
            elif new_pw != confirm_pw:
                st.error("❌ New passwords do not match.")
            else:
                db  = SessionLocal()
                row = db.query(User).filter(User.id == customer["id"]).first()
                if not row or not verify_password(current_pw, row.hashed_password):
                    st.error("❌ Current password is incorrect.")
                    db.close()
                else:
                    db.close()
                    st.session_state["pending_password_change"] = {"new_pw": new_pw}
                    st.rerun()