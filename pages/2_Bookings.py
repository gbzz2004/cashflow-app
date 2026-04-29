import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import joinedload
from sidebar import show_sidebar_logout
from auth import require_login
from database import SessionLocal, Booking, Product, Team

# Tell app.py we're on the bookings page
if st.session_state.get("current_page") != "bookings":
    st.session_state["current_page"] = "bookings"
    st.rerun()

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
.rec-card { border-radius:14px; padding:18px 20px; margin-bottom:10px; }
[data-testid="stDataFrame"] { border-radius: 10px; }
.stCaption { opacity: 0.7; }
.block-container {
    max-width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
</style>''', unsafe_allow_html=True)

# ── UI label mapping ──────────────────────────────────────────────────────────
STATUS_DISPLAY    = {"completed": "Approved", "pending": "Pending", "cancelled": "Cancelled"}
STATUS_DB         = {v: k for k, v in STATUS_DISPLAY.items()}
STATUS_OPTIONS_UI = ["Pending", "Approved", "Cancelled"]
STATUS_ICON       = {"completed": "🟢", "pending": "🟡", "cancelled": "🔴"}

user = require_login()
show_sidebar_logout()
if not user:
    st.warning("Please log in first.")
    st.stop()

st.markdown('<div style="border-left:4px solid #7F77DD;padding-left:16px;margin-bottom:4px;"><span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;color:#7F77DD;font-weight:600;">Management</span><h2 style="margin:4px 0 0;font-family:Playfair Display,serif;color:var(--text-color, #1a1a2e);">Bookings</h2></div>', unsafe_allow_html=True)
st.caption("Manage and track all your customer bookings.")
st.divider()

# ── Auto-settle remaining balance when booking date has passed ────────────────
today = date.today()
db_settle = SessionLocal()
overdue = db_settle.query(Booking).filter(
    Booking.owner_id == user["id"],
    Booking.status == "completed",
    Booking.remaining_balance > 0,
).all()
for b in overdue:
    if b.booking_date.date() <= today:
        b.remaining_balance = 0.0
db_settle.commit()
db_settle.close()

# ── Downpayment / Approve dialog ──────────────────────────────────────────────
@st.dialog("Set Downpayment")
def downpayment_dialog(booking_id: int, total_amount: float):
    st.markdown(f"**Total service price:** ₱{total_amount:,.2f}")
    st.caption("Enter the downpayment amount the customer will pay now. The remaining balance will be collected on the day of the booking.")

    dp = st.number_input(
        "Downpayment Amount (₱)",
        min_value=0.0,
        max_value=float(total_amount),
        value=min(total_amount * 0.5, total_amount),
        step=50.0,
        key="dp_input"
    )
    remaining = total_amount - dp
    st.info(f"💰 Downpayment: **₱{dp:,.2f}** — Remaining balance on booking day: **₱{remaining:,.2f}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm Approval", use_container_width=True, type="primary"):
            db2 = SessionLocal()
            row = db2.query(Booking).filter(Booking.id == booking_id).first()
            if row:
                row.status            = "completed"
                row.downpayment       = dp
                row.remaining_balance = remaining
                row.downpayment_paid  = False
            db2.commit()
            db2.close()
            st.session_state.pop("pending_approval_id", None)
            st.session_state.pop("pending_approval_amount", None)
            st.rerun()
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.pop("pending_approval_id", None)
            st.session_state.pop("pending_approval_amount", None)
            st.rerun()

# ── Cancel confirmation dialog ────────────────────────────────────────────────
@st.dialog("Confirm Cancellation")
def cancel_dialog(booking_id: int, customer_name: str, service: str, amount: float, booking_date):
    st.warning("⚠️ Are you sure you want to cancel this booking?")
    st.markdown(f"""
    <div style="border:1px solid #f5f5f5;border-radius:10px;padding:14px 18px;margin:10px 0;">
        <div style="font-size:0.9rem;line-height:2;">
            👤 <strong>Customer:</strong> {customer_name}<br>
            🎯 <strong>Service:</strong> {service}<br>
            📅 <strong>Date:</strong> {booking_date.strftime('%B %d, %Y')}<br>
            💰 <strong>Amount:</strong> ₱{amount:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("This action cannot be undone.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔴 Yes, Cancel Booking", use_container_width=True, type="primary"):
            db2 = SessionLocal()
            row = db2.query(Booking).filter(Booking.id == booking_id).first()
            if row:
                row.status            = "cancelled"
                row.downpayment       = None
                row.remaining_balance = None
                row.downpayment_paid  = False
            db2.commit()
            db2.close()
            st.session_state.pop("pending_cancel_id", None)
            st.rerun()
    with col2:
        if st.button("← Go Back", use_container_width=True):
            st.session_state.pop("pending_cancel_id", None)
            st.rerun()

# ── Mark as Paid confirmation dialog ─────────────────────────────────────────
@st.dialog("Confirm Downpayment Receipt")
def mark_paid_dialog(booking_id: int, customer_name: str, downpayment: float):
    st.success(f"Confirm that you have received the downpayment from **{customer_name}**.")
    st.markdown(f"""
    <div style="background:#f0fdf4;border:1.5px solid #86efac;border-radius:12px;
                padding:16px 20px;margin:10px 0;text-align:center;">
        <div style="font-size:0.8rem;color:#166534;font-weight:600;
                    text-transform:uppercase;letter-spacing:0.08em;">Downpayment Received</div>
        <div style="font-size:2rem;font-weight:700;color:#166534;margin:6px 0;">
            ₱{downpayment:,.2f}
        </div>
        <div style="font-size:0.82rem;color:#166534;">
            This will be counted in your revenue immediately.<br>
            The remaining balance will be added on the booking day.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Mark as Paid", use_container_width=True, type="primary"):
            db2 = SessionLocal()
            row = db2.query(Booking).filter(Booking.id == booking_id).first()
            if row:
                row.downpayment_paid = True
            db2.commit()
            db2.close()
            st.session_state.pop("pending_mark_paid_id", None)
            st.rerun()
    with col2:
        if st.button("← Go Back", use_container_width=True):
            st.session_state.pop("pending_mark_paid_id", None)
            st.rerun()

# ── Trigger dialogs if queued ─────────────────────────────────────────────────
if "pending_approval_id" in st.session_state:
    downpayment_dialog(
        st.session_state["pending_approval_id"],
        st.session_state["pending_approval_amount"]
    )

if "pending_cancel_id" in st.session_state:
    info = st.session_state["pending_cancel_id"]
    cancel_dialog(
        info["id"], info["customer_name"], info["service"],
        info["amount"], info["booking_date"]
    )

if "pending_mark_paid_id" in st.session_state:
    info = st.session_state["pending_mark_paid_id"]
    mark_paid_dialog(info["id"], info["customer_name"], info["downpayment"])

db = SessionLocal()
products = db.query(Product).filter(Product.owner_id == user["id"]).all()

# ── Filters ────────────────────────────────────────────────────────────────────
st.markdown("**All Bookings**")
f1, f2, f3 = st.columns(3)
with f1: filter_status  = st.selectbox("Status",  ["All"] + STATUS_OPTIONS_UI)
with f2: filter_product = st.selectbox("Service", ["All"] + [p.name for p in products])
with f3: sort_by        = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Amount (high)", "Amount (low)"])

bookings = db.query(Booking).options(
    joinedload(Booking.product),
    joinedload(Booking.team)
).filter(Booking.owner_id == user["id"]).all()

filtered = bookings
if filter_status != "All":
    filter_db = STATUS_DB[filter_status]
    filtered  = [b for b in filtered if b.status == filter_db]
if filter_product != "All":
    filtered  = [b for b in filtered if b.product and b.product.name == filter_product]

sort_map = {
    "Date (newest)": (lambda b: b.booking_date, True),
    "Date (oldest)": (lambda b: b.booking_date, False),
    "Amount (high)": (lambda b: b.amount, True),
    "Amount (low)":  (lambda b: b.amount, False)
}
key_fn, rev = sort_map[sort_by]
filtered    = sorted(filtered, key=key_fn, reverse=rev)

if not filtered:
    st.info("No bookings found for the selected filters.")
else:
    approved_income = sum(
        (b.downpayment if b.downpayment is not None else b.amount)
        for b in filtered if b.status == "completed" and b.downpayment_paid
    )
    pending_dp = sum(
        b.downpayment for b in filtered
        if b.status == "completed" and b.downpayment is not None and not b.downpayment_paid
    )
    pending_total = sum(b.amount for b in filtered if b.status == "pending")
    st.caption(
        f"Showing **{len(filtered)}** booking(s) — "
        f"Confirmed revenue: **₱{approved_income:,.2f}** | "
        f"Awaiting DP: **₱{pending_dp:,.2f}** | "
        f"Pending: **₱{pending_total:,.2f}**"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    for b in filtered:
        col_info, col_status = st.columns([5, 2])

        with col_info:
            team_label = f"  🎬 {b.team.name}" if b.team else ""
            st.markdown(f"**#{b.id} — {b.customer_name}**{team_label}")

            # Build payment line
            if b.status == "completed" and b.downpayment is not None:
                bal = b.remaining_balance or 0.0
                dp_paid = b.downpayment_paid or False

                if dp_paid:
                    dp_tag = f"💳 DP: ₱{b.downpayment:,.2f} ✅"
                else:
                    dp_tag = f"💳 DP: ₱{b.downpayment:,.2f} ⏳ awaiting payment"

                if bal > 0:
                    pay_info = f"  |  {dp_tag}  |  Balance on day: ₱{bal:,.2f}"
                else:
                    pay_info = f"  |  {dp_tag}  |  ✅ Fully settled"
            else:
                pay_info = f"  |  ₱{b.amount:,.2f}"

            st.caption(
                f"{b.product.name if b.product else '—'}"
                f"{pay_info}  |  "
                f"{b.booking_date.strftime('%b %d, %Y')}"
                + (f"  |  📝 {b.notes}" if b.notes else "")
            )

        with col_status:
            current_ui    = STATUS_DISPLAY.get(b.status, b.status.capitalize())
            status_locked = b.status in ("completed", "cancelled")

            if status_locked:
                badge_color = {"completed": "#2e7d32", "cancelled": "#c62828"}.get(b.status, "#555")
                st.markdown(
                    f'<div style="border:1px solid {badge_color};border-radius:8px;padding:6px 12px;'
                    f'color:{badge_color};font-weight:600;font-size:0.85rem;text-align:center;">'
                    f'{STATUS_ICON.get(b.status, "")} {current_ui}'
                    f'<br><span style="font-size:0.68rem;opacity:0.6;font-weight:400;">locked</span></div>',
                    unsafe_allow_html=True
                )
            else:
                new_status_ui = st.selectbox(
                    "Status",
                    STATUS_OPTIONS_UI,
                    index=STATUS_OPTIONS_UI.index(current_ui) if current_ui in STATUS_OPTIONS_UI else 0,
                    key=f"stat_{b.id}"
                )

                if new_status_ui != current_ui:
                    if new_status_ui == "Approved":
                        st.session_state["pending_approval_id"]     = b.id
                        st.session_state["pending_approval_amount"] = b.amount
                        st.rerun()
                    elif new_status_ui == "Cancelled":
                        st.session_state["pending_cancel_id"] = {
                            "id":            b.id,
                            "customer_name": b.customer_name,
                            "service":       b.product.name if b.product else "—",
                            "amount":        b.amount,
                            "booking_date":  b.booking_date,
                        }
                        st.rerun()

            # ── Mark as Paid button (approved, has DP, not yet paid) ──────
            if (b.status == "completed"
                    and b.downpayment is not None
                    and not (b.downpayment_paid or False)):
                st.markdown("<div style='margin-top:6px;'>", unsafe_allow_html=True)
                if st.button("💰 Mark DP as Paid", key=f"paid_{b.id}", use_container_width=True):
                    st.session_state["pending_mark_paid_id"] = {
                        "id":            b.id,
                        "customer_name": b.customer_name,
                        "downpayment":   b.downpayment,
                    }
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            elif (b.status == "completed"
                    and b.downpayment is not None
                    and (b.downpayment_paid or False)):
                st.markdown(
                    '<div style="margin-top:6px;font-size:0.8rem;color:#2e7d32;'
                    'font-weight:600;text-align:center;">💰 DP Received ✅</div>',
                    unsafe_allow_html=True
                )

            # ── Team assignment (only when Approved) ──────────────────────
            if b.status == "completed":
                db3   = SessionLocal()
                teams = db3.query(Team).filter(Team.owner_id == user["id"]).all()
                db3.close()

                if teams:
                    team_options = {t.name: t.id for t in teams}
                    current_team = b.team.name if b.team else None

                    if current_team:
                        st.markdown(
                            f'<div style="border:1px solid #7F77DD;border-radius:8px;padding:6px 12px;'
                            f'color:#7F77DD;font-weight:600;font-size:0.85rem;text-align:center;margin-top:6px;">'
                            f'🎬 {current_team}'
                            f'<br><span style="font-size:0.68rem;opacity:0.6;font-weight:400;">team locked</span></div>',
                            unsafe_allow_html=True
                        )
                    else:
                        booking_date_only = b.booking_date.date() if hasattr(b.booking_date, 'date') else b.booking_date
                        db5 = SessionLocal()
                        same_day_bookings = db5.query(Booking).filter(
                            Booking.owner_id == user["id"],
                            Booking.id != b.id,
                            Booking.team_id != None,
                        ).all()
                        db5.close()

                        booked_team_ids = {
                            sb.team_id for sb in same_day_bookings
                            if (sb.booking_date.date() if hasattr(sb.booking_date, 'date') else sb.booking_date) == booking_date_only
                        }

                        available_teams = {
                            name: tid for name, tid in team_options.items()
                            if tid not in booked_team_ids
                        }

                        if not available_teams:
                            st.caption("⚠️ All teams are already assigned on this date.")
                        else:
                            selected_team = st.selectbox(
                                "Assign Team",
                                ["-- Select Team --"] + list(available_teams.keys()),
                                index=0,
                                key=f"team_{b.id}"
                            )
                            if selected_team != "-- Select Team --":
                                db4 = SessionLocal()
                                row = db4.query(Booking).filter(Booking.id == b.id).first()
                                if row:
                                    row.team_id = available_teams[selected_team]
                                    db4.commit()
                                db4.close()
                                st.rerun()
                else:
                    st.caption("⚠️ No teams yet. Add teams in the Teams page.")

        st.markdown('<hr style="border:none;border-top:1px solid #f5f5f5;margin:6px 0 10px;">', unsafe_allow_html=True)

db.close()