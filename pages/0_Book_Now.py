import streamlit as st
from datetime import datetime, date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import func
from database import SessionLocal, Booking, Product, User, Team

# ── Pick which business to book with ─────────────────────────────────────────
db = SessionLocal()
businesses = db.query(User).filter(User.role == "admin").all()

if not businesses:
    st.error("No businesses are registered yet.")
    db.close()
    st.stop()

st.title("🗓️ Book an Appointment")
st.caption("Fill in the form below to reserve your slot.")

if len(businesses) == 1:
    selected_business = businesses[0]
else:
    biz_choice = st.selectbox(
        "Select business",
        options=businesses,
        format_func=lambda u: u.business_name
    )
    selected_business = biz_choice

products = db.query(Product).filter(Product.owner_id == selected_business.id).all()

# ── Get team count and fully booked dates ─────────────────────────────────────
total_teams = db.query(Team).filter(Team.owner_id == selected_business.id).count()

booked_counts = db.query(
    func.date(Booking.booking_date),
    func.count(Booking.id)
).filter(
    Booking.owner_id == selected_business.id,
    Booking.status != "cancelled"
).group_by(func.date(Booking.booking_date)).all()

db.close()

fully_booked_dates = set()
if total_teams > 0:
    for booking_date_val, count in booked_counts:
        if count >= total_teams:
            fully_booked_dates.add(str(booking_date_val))

if not products:
    st.warning(f"{selected_business.business_name} has no services listed yet. Check back soon!")
    st.stop()

st.markdown(f"### {selected_business.business_name}")

# ── Show team capacity info ───────────────────────────────────────────────────
if total_teams > 0:
    st.info(f"📅 This business has **{total_teams} team(s)** available — maximum **{total_teams} booking(s) per day**.")
else:
    st.warning("⚠️ No teams have been set up yet. Bookings are currently unlimited.")

st.divider()

customer = st.session_state.get("customer", None)
if customer:
    st.success(f"👤 Booking as **{customer['full_name']}** — your booking will be saved to your account!")

# ── Confirmation Dialog ───────────────────────────────────────────────────────
@st.dialog("Confirm Your Booking")
def confirm_booking_dialog():
    b = st.session_state.get("pending_booking")
    if not b:
        return

    notes_line    = f"📝 <strong>Notes:</strong> {b['notes']}<br>" if b['notes'] else ""
    payment_label = "Pay on the day 🕐" if b['pay_option'] == "I'll pay on the day (no payment now)" else "Paid ✅"

    st.markdown("### 📋 Booking Summary")
    st.markdown(f"""
    <div style="background:#1A1D2E;border:1px solid #2A2D3E;border-radius:14px;padding:20px;margin-bottom:16px;">
        <div style="font-size:0.9rem;line-height:2.2;color:#E8EAF6;">
            👤 <strong>Name:</strong> {b['customer_name']}<br>
            🎯 <strong>Service:</strong> {b['product'].name}<br>
            💰 <strong>Amount:</strong> ₱{b['product'].price:,.2f}<br>
            📅 <strong>Date:</strong> {b['booking_date'].strftime('%B %d, %Y')}<br>
            💳 <strong>Payment:</strong> {payment_label}<br>
            {notes_line}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("Please review your booking details before confirming.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm", use_container_width=True, type="primary"):
            status    = "completed" if b["pay_option"] == "Mark as paid" else "pending"
            note_text = b["notes"]
            if b["customer_contact"]:
                contact_note = f"Contact: {b['customer_contact']}"
                note_text    = f"{contact_note}\n{note_text}" if note_text else contact_note

            customer_id = st.session_state.get("customer", {}).get("id", None)

            db2 = SessionLocal()
            booking = Booking(
                owner_id=b["business"].id,
                product_id=b["product"].id,
                customer_id=customer_id,
                customer_name=b["customer_name"],
                amount=b["product"].price,
                status=status,
                booking_date=datetime.combine(b["booking_date"], datetime.min.time()),
                notes=note_text or None
            )
            db2.add(booking)
            db2.commit()
            db2.close()

            if st.session_state.get("customer"):
                st.session_state["last_booking"] = {
                    "service": b["product"].name,
                    "date":    b["booking_date"].strftime("%B %d, %Y"),
                    "amount":  b["product"].price,
                    "status":  status
                }

            del st.session_state["pending_booking"]
            st.session_state["show_confirm"]    = False
            st.session_state["booking_success"] = True
            st.rerun()

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            del st.session_state["pending_booking"]
            st.session_state["show_confirm"] = False
            st.rerun()

# ── Trigger dialog ────────────────────────────────────────────────────────────
if st.session_state.get("show_confirm"):
    confirm_booking_dialog()

# ── Success message ───────────────────────────────────────────────────────────
if st.session_state.get("booking_success"):
    st.success("✅ Booking confirmed successfully!")
    if customer:
        st.info("👤 This booking has been saved to your account. View it in **My Bookings**!")
    st.session_state["booking_success"] = False

# ── Booking Form ──────────────────────────────────────────────────────────────
with st.form("client_booking_form", clear_on_submit=True):
    customer_name = st.text_input(
        "Your Name *",
        value=customer["full_name"] if customer else ""
    )
    customer_contact = st.text_input("Contact Number or Email (optional)")

    product_choice = st.selectbox(
        "Service *",
        options=products,
        format_func=lambda p: f"{p.name}  —  ₱{p.price:,.2f}"
    )

    if product_choice and product_choice.description:
        st.caption(f"ℹ️ {product_choice.description}")

    booking_date = st.date_input(
        "Preferred Date *",
        value=date.today(),
        min_value=date.today()
    )

    # ← Show warning inside form if date is fully booked
    is_fully_booked = str(booking_date) in fully_booked_dates
    if is_fully_booked:
        st.error(f"❌ Sorry! **{booking_date.strftime('%B %d, %Y')}** is fully booked ({total_teams}/{total_teams} teams occupied). Please choose another date.")

    notes = st.text_area("Special requests or notes (optional)", height=80)

    pay_option = st.radio(
        "Payment",
        ["I'll pay on the day (no payment now)", "Mark as paid"],
        horizontal=True
    )

    st.divider()
    submitted = st.form_submit_button(
        "✅ Confirm Booking",
        use_container_width=True,
        disabled=is_fully_booked  # ← disable button if fully booked
    )

    if submitted:
        if not customer_name.strip():
            st.error("Please enter your name.")
        elif is_fully_booked:
            st.error("❌ This date is fully booked. Please choose another date.")
        else:
            st.session_state["pending_booking"] = {
                "customer_name":    customer_name.strip(),
                "customer_contact": customer_contact.strip(),
                "product":          product_choice,
                "booking_date":     booking_date,
                "notes":            notes.strip(),
                "pay_option":       pay_option,
                "business":         selected_business,
            }
            st.session_state["show_confirm"] = True
            st.rerun()

st.divider()
st.caption("To manage your bookings, please contact the business directly.")