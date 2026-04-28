import streamlit as st
from datetime import datetime, date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import joinedload
from database import SessionLocal, Booking, Product, User
from auth import login_customer, register_customer

# ── Auth Check ────────────────────────────────────────────────────────────────
if "customer" not in st.session_state:
    st.markdown("""
    <style>
    .block-container { max-width: 460px !important; padding-top: 40px !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 👤 Customer Portal")
    st.caption("Sign in to view and manage your bookings.")
    st.divider()

    tab_login, tab_register = st.tabs(["  🔑  Sign In  ", "  ✏️  Register  "])

    with tab_login:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("customer_login"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Sign In →", use_container_width=True):
                customer = login_customer(username, password)
                if customer:
                    st.session_state["customer"] = customer
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")

    with tab_register:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("customer_register"):
            full_name = st.text_input("Full Name", placeholder="e.g. Juan Dela Cruz")
            username  = st.text_input("Username", placeholder="Choose a username")
            password  = st.text_input("Password", type="password", placeholder="Min. 6 characters")
            confirm   = st.text_input("Confirm Password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Create Account →", use_container_width=True):
                if not all([full_name, username, password]):
                    st.error("❌ All fields are required.")
                elif password != confirm:
                    st.error("❌ Passwords do not match.")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters.")
                else:
                    ok, msg = register_customer(username, password, full_name)
                    if ok:
                        st.success("✅ " + msg + " Please sign in.")
                    else:
                        st.error("❌ " + msg)
    st.stop()

# ── Customer is logged in ─────────────────────────────────────────────────────
customer = st.session_state["customer"]

# ── Cancel Confirmation Dialog ────────────────────────────────────────────────
@st.dialog("Cancel Booking")
def cancel_booking_dialog():
    booking_id = st.session_state.get("cancel_booking_id")
    if not booking_id:
        return

    st.warning("⚠️ Are you sure you want to cancel this booking?")

    db = SessionLocal()
    b = db.query(Booking).options(joinedload(Booking.product)).filter(
        Booking.id == booking_id
    ).first()

    if b:
        st.markdown(f"""
        <div style="background:#1A1D2E;border:1px solid #2A2D3E;border-radius:14px;padding:20px;margin:12px 0;">
            <div style="font-size:0.9rem;line-height:2.2;color:#E8EAF6;">
                🎯 <strong>Service:</strong> {b.product.name if b.product else 'Unknown'}<br>
                📅 <strong>Date:</strong> {b.booking_date.strftime('%B %d, %Y')}<br>
                💰 <strong>Amount:</strong> ₱{b.amount:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    db.close()

    st.caption("This action cannot be undone.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Cancel", use_container_width=True, type="primary"):
            db2 = SessionLocal()
            row = db2.query(Booking).filter(Booking.id == booking_id).first()
            if row:
                row.status = "cancelled"
                db2.commit()
            db2.close()
            del st.session_state["cancel_booking_id"]
            st.session_state["cancel_success"] = True
            st.rerun()
    with col2:
        if st.button("❌ No, Go Back", use_container_width=True):
            del st.session_state["cancel_booking_id"]
            st.rerun()

# ── Trigger cancel dialog ─────────────────────────────────────────────────────
if st.session_state.get("cancel_booking_id"):
    cancel_booking_dialog()

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"## 👋 Welcome, {customer['full_name']}!")
    st.caption("Manage your bookings below.")
with col2:
    if st.button("Sign Out", use_container_width=True):
        del st.session_state["customer"]
        st.rerun()

st.divider()

# ── Cancel success message ────────────────────────────────────────────────────
if st.session_state.get("cancel_success"):
    st.success("✅ Booking has been cancelled.")
    st.session_state["cancel_success"] = False

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 My Bookings", "🔁 Rebook", "✅ Confirmation"])

# ── Tab 1: My Bookings ────────────────────────────────────────────────────────
with tab1:
    db = SessionLocal()
    my_bookings = db.query(Booking).options(joinedload(Booking.product)).filter(
        Booking.customer_id == customer["id"]
    ).order_by(Booking.booking_date.desc()).all()

    if not my_bookings:
        st.info("You have no bookings yet. Book an appointment first!")
    else:
        for b in my_bookings:
            status_color = {"completed": "🟢", "pending": "🟡", "cancelled": "🔴"}.get(b.status, "⚪")
            status_label = "Approved ✅" if b.status == "completed" else b.status.capitalize()
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.markdown(f"**{b.product.name if b.product else 'Unknown Service'}**")
                    st.caption(f"📅 {b.booking_date.strftime('%B %d, %Y')}")
                with c2:
                    st.markdown(f"₱{b.amount:,.2f}")
                    st.caption(f"{status_color} {status_label}")
                with c3:
                    if b.status == "pending":
                        if st.button("Cancel", key=f"cancel_{b.id}", type="secondary"):
                            st.session_state["cancel_booking_id"] = b.id
                            st.rerun()
    db.close()

# ── Tab 2: Rebook ─────────────────────────────────────────────────────────────
with tab2:
    db = SessionLocal()
    past_bookings = db.query(Booking).options(joinedload(Booking.product)).filter(
        Booking.customer_id == customer["id"],
        Booking.status != "cancelled"
    ).order_by(Booking.booking_date.desc()).all()

    if not past_bookings:
        st.info("No past bookings to rebook from.")
    else:
        st.caption("Select a past booking to rebook the same service.")
        options = {f"{b.product.name if b.product else 'Unknown'} — ₱{b.amount:,.2f} ({b.booking_date.strftime('%b %d, %Y')})": b
                   for b in past_bookings}
        choice  = st.selectbox("Select booking to rebook", list(options.keys()))
        selected = options[choice]

        new_date = st.date_input("New Date", value=date.today(), min_value=date.today())
        notes    = st.text_area("Special requests (optional)", height=80)

        if st.button("✅ Confirm Rebook", use_container_width=True):
            new_booking = Booking(
                owner_id=selected.owner_id,
                product_id=selected.product_id,
                customer_id=customer["id"],
                customer_name=customer["full_name"],
                amount=selected.amount,
                status="pending",
                booking_date=datetime.combine(new_date, datetime.min.time()),
                notes=notes or None
            )
            db.add(new_booking)
            db.commit()
            st.session_state["last_booking"] = {
                "service": selected.product.name if selected.product else "Unknown",
                "date":    new_date.strftime("%B %d, %Y"),
                "amount":  selected.amount
            }
            st.success("✅ Rebooked successfully!")
            st.rerun()
    db.close()

# ── Tab 3: Confirmation ───────────────────────────────────────────────────────
with tab3:
    if "last_booking" in st.session_state:
        b = st.session_state["last_booking"]
        st.success("✅ Booking Confirmed!")
        st.markdown(f"""
        <div style="background:#1A1D2E;border:1px solid #2A2D3E;border-radius:16px;padding:28px;max-width:400px;">
            <div style="font-size:1.1rem;font-weight:700;color:#ffffff;margin-bottom:16px;">📋 Booking Summary</div>
            <div style="color:#9EA3C0;font-size:0.9rem;line-height:2;">
                🎯 <strong style="color:#ffffff;">Service:</strong> {b['service']}<br>
                📅 <strong style="color:#ffffff;">Date:</strong> {b['date']}<br>
                💰 <strong style="color:#ffffff;">Amount:</strong> ₱{b['amount']:,.2f}<br>
                🕐 <strong style="color:#ffffff;">Status:</strong> Pending — Pay on the day
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No recent booking confirmation. Book or rebook a service first!")