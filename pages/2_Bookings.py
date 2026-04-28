import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sidebar import show_sidebar_logout
show_sidebar_logout()
from sqlalchemy.orm import joinedload
from auth import require_login
from database import SessionLocal, Booking, Product
# Tell app.py we're on the bookings page
if st.session_state.get("current_page") != "bookings":
    st.session_state["current_page"] = "bookings"
    st.rerun()

st.set_page_config(page_title="Bookings", page_icon="📅", layout="wide")

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Playfair Display', serif !important; }

/* Force card backgrounds to use theme-aware colors */
.kpi {
    background: var(--background-color, #fff) !important;
    border: 1px solid rgba(127,119,221,0.25) !important;
    border-radius: 14px;
    padding: 24px 26px;
}
.kpi-label { font-size:0.75rem; color:#7F77DD; text-transform:uppercase; letter-spacing:0.08em; font-weight:600; }
.kpi-value { font-size:1.5rem; font-weight:700; color: var(--text-color, #1a1a2e); margin:4px 0 2px; }
.sec { font-family:'Playfair Display',serif; font-size:1.05rem; font-weight:600;
       color: var(--text-color, #1a1a2e); margin-bottom:12px; }

/* Page header accent bar */
.page-header-label { font-size:0.78rem; text-transform:uppercase; letter-spacing:0.12em; font-weight:600; }
.page-header-title { margin:4px 0 0; font-family:'Playfair Display',serif;
                     color: var(--text-color, #1a1a2e); font-size:1.8rem; }

/* Recommendation cards — use semi-transparent backgrounds so they work in dark mode */
.rec-card { border-radius:14px; padding:18px 20px; margin-bottom:10px; }

/* Make Streamlit dataframes readable in dark mode */
[data-testid="stDataFrame"] { border-radius: 10px; }

/* Caption color */
.stCaption { opacity: 0.7; }
</style>''', unsafe_allow_html=True)

user = require_login()
if not user:
    st.warning("Please log in first.")
    st.stop()

st.markdown('<div style="border-left:4px solid #7F77DD;padding-left:16px;margin-bottom:4px;"><span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;color:#7F77DD;font-weight:600;">Management</span><h2 style="margin:4px 0 0;font-family:Playfair Display,serif;color:var(--text-color, #1a1a2e);">Bookings</h2></div>', unsafe_allow_html=True)
st.caption("Manage and track all your customer bookings.")
st.divider()

db = SessionLocal()
products = db.query(Product).filter(Product.owner_id == user["id"]).all()


# ── Filters ────────────────────────────────────────────────────────────────────
st.markdown("**All Bookings**")
f1, f2, f3 = st.columns(3)
with f1: filter_status  = st.selectbox("Status",  ["All", "completed", "pending", "cancelled"])
with f2: filter_product = st.selectbox("Service", ["All"] + [p.name for p in products])
with f3: sort_by        = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Amount (high)", "Amount (low)"])

bookings = db.query(Booking).options(joinedload(Booking.product)).filter(Booking.owner_id == user["id"]).all()

filtered = bookings
if filter_status  != "All": filtered = [b for b in filtered if b.status == filter_status]
if filter_product != "All": filtered = [b for b in filtered if b.product and b.product.name == filter_product]

sort_map = {"Date (newest)": (lambda b: b.booking_date, True),
            "Date (oldest)": (lambda b: b.booking_date, False),
            "Amount (high)": (lambda b: b.amount, True),
            "Amount (low)":  (lambda b: b.amount, False)}
key_fn, rev = sort_map[sort_by]
filtered    = sorted(filtered, key=key_fn, reverse=rev)

if not filtered:
    st.info("No bookings found for the selected filters.")
else:
    completed_total = sum(b.amount for b in filtered if b.status == "completed")
    pending_total   = sum(b.amount for b in filtered if b.status == "pending")
    st.caption(f"Showing **{len(filtered)}** booking(s) — Completed: **₱{completed_total:,.2f}** | Pending: **₱{pending_total:,.2f}**")
    st.markdown("<br>", unsafe_allow_html=True)

    status_icon = {"completed": "🟢", "pending": "🟡", "cancelled": "🔴"}

    for b in filtered:
        col_info, col_status = st.columns([5, 2])

        with col_info:
            st.markdown(f"**#{b.id} — {b.customer_name}**")
            st.caption(
                f"{b.product.name if b.product else '—'}  |  "
                f"₱{b.amount:,.2f}  |  "
                f"{b.booking_date.strftime('%b %d, %Y')}"
                + (f"  |  📝 {b.notes}" if b.notes else "")
            )

        with col_status:
            new_status = st.selectbox(
                "Status",
                ["pending", "completed", "cancelled"],
                index=["pending", "completed", "cancelled"].index(b.status),
                key=f"stat_{b.id}"
            )
            if new_status != b.status:
                db2 = SessionLocal()
                row = db2.query(Booking).filter(Booking.id == b.id).first()
                if row:
                    row.status = new_status
                    db2.commit()
                db2.close()
                st.rerun()

        st.markdown('<hr style="border:none;border-top:1px solid #f5f5f5;margin:6px 0 10px;">', unsafe_allow_html=True)

db.close()
