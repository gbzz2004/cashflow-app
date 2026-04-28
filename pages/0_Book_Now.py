import streamlit as st
from datetime import datetime, date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import SessionLocal, Booking, Product, User
# Reset current page tracker
st.session_state["current_page"] = ""

# ── Pick which business to book with ─────────────────────────────────────────
db = SessionLocal()

# Only show admin businesses, not customer accounts
businesses = db.query(User).filter(User.role == "admin").all()

if not businesses:
    st.error("No businesses are registered yet.")
    db.close()
    st.stop()

st.title("🗓️ Book an Appointment")
st.caption("Fill in the form below to reserve your slot.")

# If only one business exists, skip the selector
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

if not products:
    st.warning(f"{selected_business.business_name} has no services listed yet. Check back soon!")
    db.close()
    st.stop()

st.markdown(f"### {selected_business.business_name}")
st.divider()

# ── Check if customer is logged in ───────────────────────────────────────────
customer = st.session_state.get("customer", None)
if customer:
    st.success(f"👤 Booking as **{customer['full_name']}** — your booking will be saved to your account!")

# ── Booking Form ──────────────────────────────────────────────────────────────
with st.form("client_booking_form", clear_on_submit=True):

    # Pre-fill name if customer is logged in
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

    notes = st.text_area("Special requests or notes (optional)", height=80)

    pay_option = st.radio(
        "Payment",
        ["I'll pay on the day (no payment now)", "Mark as paid"],
        horizontal=True
    )

    st.divider()
    submitted = st.form_submit_button("✅ Confirm Booking", use_container_width=True)

    if submitted:
        if not customer_name.strip():
            st.error("Please enter your name.")
        else:
            status = "completed" if pay_option == "Mark as paid" else "pending"
            note_text = notes.strip()
            if customer_contact.strip():
                contact_note = f"Contact: {customer_contact.strip()}"
                note_text = f"{contact_note}\n{note_text}" if note_text else contact_note

            # ← Link to customer account if logged in
            customer_id = customer["id"] if customer else None

            booking = Booking(
                owner_id=selected_business.id,
                product_id=product_choice.id,
                customer_id=customer_id,
                customer_name=customer_name.strip(),
                amount=product_choice.price,
                status=status,
                booking_date=datetime.combine(booking_date, datetime.min.time()),
                notes=note_text or None
            )
            db.add(booking)
            db.commit()

            # Save confirmation to session for customer portal
            if customer:
                st.session_state["last_booking"] = {
                    "service": product_choice.name,
                    "date": booking_date.strftime("%B %d, %Y"),
                    "amount": product_choice.price,
                    "status": status
                }

            st.success(f"✅ Booking confirmed for **{customer_name}**!")
            st.info(
                f"📋 **Summary**\n\n"
                f"- **Service:** {product_choice.name}\n"
                f"- **Date:** {booking_date.strftime('%B %d, %Y')}\n"
                f"- **Amount:** ₱{product_choice.price:,.2f}\n"
                f"- **Payment:** {'Paid ✅' if status == 'completed' else 'Pay on the day 🕐'}"
            )
            if customer:
                st.info("👤 This booking has been saved to your account. View it in **My Bookings**!")

db.close()

st.divider()
st.caption("To manage your bookings, please contact the business directly.")