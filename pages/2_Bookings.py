import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import joinedload
from sidebar import show_sidebar_logout
from auth import require_login
from database import SessionLocal, Booking, Product

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Playfair Display', serif !important; }
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
.rec-card { border-radius:14px; padding:18px 20px; margin-bottom:10px; }
[data-testid="stDataFrame"] { border-radius: 10px; }
.stCaption { opacity: 0.7; }
</style>''', unsafe_allow_html=True)

# ── UI label mapping (DB value → display label) ───────────────────────────────
STATUS_DISPLAY = {
    "completed": "Approved",
    "pending":   "Pending",
    "cancelled": "Cancelled"
}
STATUS_DB = {v: k for k, v in STATUS_DISPLAY.items()}  # reverse: display → DB
STATUS_OPTIONS_UI = ["Pending", "Approved", "Cancelled"]  # shown in dropdowns
STATUS_ICON = {"completed": "🟢", "pending": "🟡", "cancelled": "🔴"}

user = require_login()
show_sidebar_logout()
if not user:
    st.warning("Please log in first.")
    st.stop()

st.markdown('<div style="border-left:4px solid #7F77DD;padding-left:16px;margin-bottom:4px;"><span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;color:#7F77DD;font-weight:600;">Management</span><h2 style="margin:4px 0 0;font-family:Playfair Display,serif;color:var(--text-color, #1a1a2e);">Bookings</h2></div>', unsafe_allow_html=True)
st.caption("Manage and track all your customer bookings.")
st.divider()

db = SessionLocal()
products = db.query(Product).filter(Product.owner_id == user["id"]).all()

# ── Add New Booking ────────────────────────────────────────────────────────────
with st.expander("➕ Add New Booking", expanded=False):
    if not products:
        st.warning("You have no products yet. Go to **Products** to add one first.")
    else:
        with st.form("add_booking"):
            col1, col2 = st.columns(2)
            with col1:
                customer_name  = st.text_input("Customer Name")
                product_choice = st.selectbox("Product / Service", options=products,
                                              format_func=lambda p: f"{p.name} (₱{p.price:,.2f})")
                amount         = st.number_input("Amount (₱)", min_value=0.0,
                                                 value=float(product_choice.price) if product_choice else 0.0,
                                                 step=10.0)
            with col2:
                booking_date  = st.date_input("Booking Date", value=datetime.today())
                status_ui     = st.selectbox("Status", STATUS_OPTIONS_UI)  # ← shows Approved
                notes         = st.text_area("Notes (optional)", height=100)

            if st.form_submit_button("Save Booking", use_container_width=True):
                if not customer_name.strip():
                    st.error("Customer name is required.")
                else:
                    db.add(Booking(
                        owner_id=user["id"],
                        product_id=product_choice.id,
                        customer_name=customer_name.strip(),
                        amount=amount,
                        status=STATUS_DB[status_ui],  # ← saves "completed" to DB
                        booking_date=datetime.combine(booking_date, datetime.min.time()),
                        notes=notes.strip() or None
                    ))
                    db.commit()
                    st.success(f"Booking saved for {customer_name.strip()}!")
                    st.rerun()

st.divider()

# ── Filters ────────────────────────────────────────────────────────────────────
st.markdown("**All Bookings**")
f1, f2, f3 = st.columns(3)
with f1: filter_status  = st.selectbox("Status",  ["All"] + STATUS_OPTIONS_UI)  # ← shows Approved
with f2: filter_product = st.selectbox("Service", ["All"] + [p.name for p in products])
with f3: sort_by        = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Amount (high)", "Amount (low)"])

bookings = db.query(Booking).options(joinedload(Booking.product)).filter(Booking.owner_id == user["id"]).all()

filtered = bookings
if filter_status != "All":
    filter_db = STATUS_DB[filter_status]  # ← convert display label to DB value
    filtered = [b for b in filtered if b.status == filter_db]
if filter_product != "All":
    filtered = [b for b in filtered if b.product and b.product.name == filter_product]

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
    # ← Shows "Approved" in the summary caption
    st.caption(f"Showing **{len(filtered)}** booking(s) — Approved: **₱{completed_total:,.2f}** | Pending: **₱{pending_total:,.2f}**")
    st.markdown("<br>", unsafe_allow_html=True)

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
            current_ui = STATUS_DISPLAY.get(b.status, b.status.capitalize())  # ← shows Approved
            new_status_ui = st.selectbox(
                "Status",
                STATUS_OPTIONS_UI,
                index=STATUS_OPTIONS_UI.index(current_ui) if current_ui in STATUS_OPTIONS_UI else 0,
                key=f"stat_{b.id}"
            )
            if new_status_ui != current_ui:
                db2 = SessionLocal()
                row = db2.query(Booking).filter(Booking.id == b.id).first()
                if row:
                    row.status = STATUS_DB[new_status_ui]  # ← saves correct DB value
                    db2.commit()
                db2.close()
                st.rerun()

        st.markdown('<hr style="border:none;border-top:1px solid #f5f5f5;margin:6px 0 10px;">', unsafe_allow_html=True)

db.close()