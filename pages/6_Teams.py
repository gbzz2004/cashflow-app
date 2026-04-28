import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sidebar import show_sidebar_logout
from auth import require_login
from database import SessionLocal, Team

user = require_login()
show_sidebar_logout()
if not user:
    st.warning("Please log in first.")
    st.stop()

if st.session_state.get("current_page") != "":
    st.session_state["current_page"] = ""
    st.rerun()

# ── Initialize delete confirmation state ──────────────────────────────────────
if "confirm_delete_team_id" not in st.session_state:
    st.session_state["confirm_delete_team_id"] = None

st.markdown('<div style="border-left:4px solid #4F8EF7;padding-left:16px;margin-bottom:4px;"><span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;color:#4F8EF7;font-weight:600;">Management</span><h2 style="margin:4px 0 0;font-family:Playfair Display,serif;color:var(--text-color,#1a1a2e);">Teams</h2></div>', unsafe_allow_html=True)
st.caption("Manage your shoot teams. The number of teams = max bookings per day.")
st.divider()

db = SessionLocal()
teams = db.query(Team).filter(Team.owner_id == user["id"]).all()

# ── Team Count Banner ─────────────────────────────────────────────────────────
total_teams = len(teams)
st.markdown(f"""
<div style="background:#1A1D2E;border:1px solid #4F8EF7;border-radius:14px;padding:20px;margin-bottom:20px;">
    <div style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.1em;color:#4F8EF7;font-weight:600;">Max Bookings Per Day</div>
    <div style="font-size:2rem;font-weight:700;color:#ffffff;margin:4px 0;">{total_teams}</div>
    <div style="font-size:0.82rem;color:#9EA3C0;">Based on number of active teams</div>
</div>
""", unsafe_allow_html=True)

# ── Add New Team ──────────────────────────────────────────────────────────────
with st.expander("➕ Add New Team", expanded=False):
    with st.form("add_team"):
        team_name = st.text_input("Team Name *", placeholder="e.g. Team Alpha")
        team_desc = st.text_area("Description (optional)", placeholder="e.g. Lead videographer + 2 assistants", height=80)
        if st.form_submit_button("Save Team", use_container_width=True):
            if not team_name.strip():
                st.error("Team name is required.")
            else:
                db.add(Team(
                    owner_id=user["id"],
                    name=team_name.strip(),
                    description=team_desc.strip() or None
                ))
                db.commit()
                st.success(f"✅ Team '{team_name}' added!")
                st.rerun()

st.divider()

# ── Team List ─────────────────────────────────────────────────────────────────
if not teams:
    st.info("No teams yet. Add your first team above!")
else:
    st.markdown(f"**{total_teams} Team(s)**")
    st.markdown("<br>", unsafe_allow_html=True)
    for t in teams:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**🎬 {t.name}**")
                if t.description:
                    st.caption(t.description)
            with c2:
                # ── If this team is pending confirmation ──────────────────────
                if st.session_state["confirm_delete_team_id"] == t.id:
                    st.warning("Are you sure?")
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✅ Yes", key=f"confirm_yes_{t.id}", type="primary", use_container_width=True):
                            db.delete(t)
                            db.commit()
                            st.session_state["confirm_delete_team_id"] = None
                            st.success(f"Team '{t.name}' deleted.")
                            st.rerun()
                    with btn_col2:
                        if st.button("❌ No", key=f"confirm_no_{t.id}", use_container_width=True):
                            st.session_state["confirm_delete_team_id"] = None
                            st.rerun()
                else:
                    if st.button("🗑️ Delete", key=f"del_team_{t.id}", type="secondary", use_container_width=True):
                        st.session_state["confirm_delete_team_id"] = t.id
                        st.rerun()

db.close()