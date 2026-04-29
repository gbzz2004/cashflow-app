import streamlit as st
from datetime import datetime, date
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import joinedload
from database import SessionLocal, Booking, Product, User
from auth import login_customer, register_customer
import qrcode
from io import BytesIO

# ── ⚙️ CONFIG — replace with your actual GCash details ───────────────────────
GCASH_NUMBER = "09755434084"   # <-- your GCash number
GCASH_NAME   = "BRAINARD GABRIEL IZON"  # <-- your GCash account name

def make_gcash_qr(amount: float) -> BytesIO:
    qr_data = f"GCash Payment\nPay to: {GCASH_NAME}\nNumber: {GCASH_NUMBER}\nAmount: PHP {amount:,.2f}"
    img = qrcode.QRCode(version=2, box_size=8, border=3,
                        error_correction=qrcode.constants.ERROR_CORRECT_M)
    img.add_data(qr_data)
    img.make(fit=True)
    qr_img = img.make_image(fill_color="#0033A0", back_color="white")
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)
    return buf

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

# ── Logout Confirmation Dialog ────────────────────────────────────────────────
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
            st.rerun()

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
                💰 <strong>Total Price:</strong> ₱{b.amount:,.2f}
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

# ── Payment Method Dialog ─────────────────────────────────────────────────────
@st.dialog("💳 Choose Payment Method", width="small")
def payment_dialog():
    booking_id = st.session_state.get("pay_booking_id")
    amount     = st.session_state.get("pay_amount", 0.0)
    if not booking_id:
        return

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:1rem;color:#555;">Downpayment due</div>
        <div style="font-size:2rem;font-weight:700;color:#0033A0;">₱{amount:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    method = st.radio(
        "Select how you'd like to pay:",
        ["💙 Online — GCash QR", "🚶 Walk-in — Pay on appointment day"],
        index=0,
        key="payment_method_choice"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if method == "💙 Online — GCash QR":
        # ── GCash QR ─────────────────────────────────────────────────────
        qr_buf = make_gcash_qr(amount)
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.image(qr_buf, width=190)

        st.markdown(f"""
        <div style="background:#f0f4ff;border:1.5px solid #0033A0;border-radius:12px;
                    padding:14px 18px;margin:10px 0;text-align:center;">
            <div style="font-size:0.8rem;color:#0033A0;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.08em;">Send payment to</div>
            <div style="font-size:1.1rem;font-weight:700;color:#0033A0;margin:4px 0;">
                📱 {GCASH_NUMBER}
            </div>
            <div style="font-size:0.85rem;color:#333;">👤 {GCASH_NAME}</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Open GCash → Scan QR or send to number → Enter amount → Confirm. "
                   "Screenshot your receipt and send it to the admin.")

        if st.button("✅ Done — I've Paid", use_container_width=True, type="primary"):
            st.session_state.pop("pay_booking_id", None)
            st.session_state.pop("pay_amount", None)
            st.session_state["pay_success"] = "gcash"
            st.rerun()

    else:
        # ── Walk-in ───────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:#f0fdf4;border:1.5px solid #86efac;border-radius:12px;
                    padding:16px 18px;margin:10px 0;text-align:center;">
            <div style="font-size:1.5rem;margin-bottom:6px;">🚶</div>
            <div style="font-weight:700;color:#166534;font-size:0.95rem;">Pay on Appointment Day</div>
            <div style="font-size:0.85rem;color:#166534;margin-top:6px;line-height:1.6;">
                Bring <strong>₱{amount:,.2f}</strong> in cash on your appointment day.<br>
                Please arrive on time.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("⚠️ Walk-in payment must be settled at the start of your appointment.")

        if st.button("✅ Got it", use_container_width=True, type="primary"):
            st.session_state.pop("pay_booking_id", None)
            st.session_state.pop("pay_amount", None)
            st.session_state["pay_success"] = "walkin"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back", use_container_width=True):
        st.session_state.pop("pay_booking_id", None)
        st.session_state.pop("pay_amount", None)
        st.rerun()

# ── Trigger dialogs ───────────────────────────────────────────────────────────
if st.session_state.get("confirm_customer_logout"):
    st.session_state["confirm_customer_logout"] = False
    logout_dialog()

if st.session_state.get("cancel_booking_id"):
    cancel_booking_dialog()

if st.session_state.get("pay_booking_id"):
    payment_dialog()

# ── Header ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"## 👋 Welcome, {customer['full_name']}!")
    st.caption("Manage your bookings below.")
with col2:
    if st.button("Sign Out", use_container_width=True):
        st.session_state["confirm_customer_logout"] = True
        st.rerun()

st.divider()

# ── Success messages ──────────────────────────────────────────────────────────
if st.session_state.get("cancel_success"):
    st.success("✅ Booking has been cancelled.")
    st.session_state["cancel_success"] = False

if st.session_state.get("pay_success") == "gcash":
    st.success("💙 GCash payment noted! Please send your receipt to the admin.")
    st.session_state.pop("pay_success", None)
elif st.session_state.get("pay_success") == "walkin":
    st.success("🚶 Walk-in payment selected. Please bring the exact amount on your appointment day.")
    st.session_state.pop("pay_success", None)

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
        today = date.today()
        for b in my_bookings:
            status_color = {"completed": "🟢", "pending": "🟡", "cancelled": "🔴"}.get(b.status, "⚪")
            status_label = "Approved ✅" if b.status == "completed" else b.status.capitalize()
            booking_day  = b.booking_date.date()
            is_past      = booking_day <= today

            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])

                with c1:
                    st.markdown(f"**{b.product.name if b.product else 'Unknown Service'}**")
                    st.caption(f"📅 {b.booking_date.strftime('%B %d, %Y')}")

                with c2:
                    if b.status == "completed" and b.downpayment is not None:
                        remaining = b.remaining_balance or 0.0
                        st.markdown(f"💳 Downpayment: **₱{b.downpayment:,.2f}**")
                        if remaining > 0:
                            if is_past:
                                st.caption("✅ Remaining balance settled on appointment day")
                            else:
                                st.markdown(
                                    f"<span style='color:#f59e0b;font-weight:600;'>"
                                    f"⏳ Balance due on day: ₱{remaining:,.2f}</span>",
                                    unsafe_allow_html=True
                                )
                        else:
                            st.caption("✅ Fully settled")
                    elif b.status == "pending":
                        st.markdown(f"₱{b.amount:,.2f}")
                        st.caption("🕐 Awaiting approval — downpayment TBD")
                    else:
                        st.markdown(f"₱{b.amount:,.2f}")

                    st.caption(f"{status_color} {status_label}")

                with c3:
                    if b.status == "pending":
                        if st.button("Cancel", key=f"cancel_{b.id}", type="secondary"):
                            st.session_state["cancel_booking_id"] = b.id
                            st.rerun()

                    # Pay button — approved, has downpayment, not yet past
                    if (b.status == "completed"
                            and b.downpayment is not None
                            and (b.remaining_balance or 0) > 0
                            and not is_past):
                        if st.button("💳 Pay", key=f"pay_{b.id}", type="primary"):
                            st.session_state["pay_booking_id"] = b.id
                            st.session_state["pay_amount"]     = b.downpayment
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
        options = {
            f"{b.product.name if b.product else 'Unknown'} — ₱{b.amount:,.2f} ({b.booking_date.strftime('%b %d, %Y')})": b
            for b in past_bookings
        }
        choice   = st.selectbox("Select booking to rebook", list(options.keys()))
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
                downpayment=None,
                remaining_balance=None,
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
        st.success("✅ Booking Request Submitted!")
        st.markdown(f"""
        <div style="background:#1A1D2E;border:1px solid #2A2D3E;border-radius:16px;padding:28px;max-width:400px;">
            <div style="font-size:1.1rem;font-weight:700;color:#ffffff;margin-bottom:16px;">📋 Booking Summary</div>
            <div style="color:#9EA3C0;font-size:0.9rem;line-height:2;">
                🎯 <strong style="color:#ffffff;">Service:</strong> {b['service']}<br>
                📅 <strong style="color:#ffffff;">Date:</strong> {b['date']}<br>
                💰 <strong style="color:#ffffff;">Total Price:</strong> ₱{b['amount']:,.2f}<br>
                🕐 <strong style="color:#ffffff;">Status:</strong> Pending approval<br>
                💳 <strong style="color:#ffffff;">Payment:</strong> Downpayment will be set once approved
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Check the **My Bookings** tab after approval to see your downpayment and remaining balance.")
    else:
        st.info("No recent booking confirmation. Book or rebook a service first!")