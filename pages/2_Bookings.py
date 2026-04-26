import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import joinedload
from sidebar import show_sidebar_logout
from auth import require_login
from database import SessionLocal, Booking, Product

st.set_page_config(page_title="Bookings", page_icon="📅", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Playfair Display', serif !important; }
.sec { font-family:'Playfair Display',serif; font-size:1.05rem; font-weight:600; color:#1a1a2e; margin-bottom:12px; }
</style>
""", unsafe_allow_html=True)

user = require_login()
show_sidebar_logout()
if not user:
    st.warning("Please log in first.")
    st.stop()

st.markdown("## 📅 Bookings")
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
                booking_date = st.date_input("Booking Date", value=datetime.today())
                status       = st.selectbox("Status", ["pending", "completed", "cancelled"])
                notes        = st.text_area("Notes (optional)", height=100)

            if st.form_submit_button("Save Booking", use_container_width=True):
                if not customer_name.strip():
                    st.error("Customer name is required.")
                else:
                    db.add(Booking(
                        owner_id=user["id"],
                        product_id=product_choice.id,
                        customer_name=customer_name.strip(),
                        amount=amount,
                        status=status,
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
