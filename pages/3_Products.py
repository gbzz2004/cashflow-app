import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sidebar import show_sidebar_logout
show_sidebar_logout()
from auth import require_login
from database import SessionLocal, Product
if st.session_state.get("current_page") != "":
    st.session_state["current_page"] = ""
    st.rerun()

st.set_page_config(page_title="Products", page_icon="🛍️", layout="wide")

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

.page-header-label { font-size:0.78rem; text-transform:uppercase; letter-spacing:0.12em; font-weight:600; }
.page-header-title { margin:4px 0 0; font-family:'Playfair Display',serif;
                     color: var(--text-color, #1a1a2e); font-size:1.8rem; }

.rec-card { border-radius:14px; padding:18px 20px; margin-bottom:10px; }
[data-testid="stDataFrame"] { border-radius: 10px; }
.stCaption { opacity: 0.7; }

/* ── Floating modal overlay ───────────────────────────────────────────────── */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(3px);
    z-index: 9998;
}
.modal-box {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--background-color, #ffffff);
    border: 1px solid rgba(127,119,221,0.35);
    border-radius: 18px;
    padding: 36px 40px 28px;
    z-index: 9999;
    width: 380px;
    box-shadow: 0 24px 60px rgba(0,0,0,0.25);
    text-align: center;
}
.modal-icon { font-size: 2.4rem; margin-bottom: 10px; }
.modal-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-color, #1a1a2e);
    margin-bottom: 6px;
}
.modal-subtitle {
    font-size: 0.875rem;
    color: #9EA3C0;
    margin-bottom: 24px;
    line-height: 1.5;
}
</style>''', unsafe_allow_html=True)

user = require_login()
if not user:
    st.warning("Please log in first.")
    st.stop()

# ── Init delete state ─────────────────────────────────────────────────────────
if "confirm_delete_product_id" not in st.session_state:
    st.session_state["confirm_delete_product_id"] = None
if "confirm_delete_product_name" not in st.session_state:
    st.session_state["confirm_delete_product_name"] = None

# ── Floating confirmation modal ───────────────────────────────────────────────
if st.session_state["confirm_delete_product_id"] is not None:
    product_name = st.session_state["confirm_delete_product_name"]

    st.markdown(f"""
    <div class="modal-overlay"></div>
    <div class="modal-box">
        <div class="modal-icon">🗑️</div>
        <div class="modal-title">Delete Product?</div>
        <div class="modal-subtitle">
            You're about to delete <strong>{product_name}</strong>.<br>
            This action cannot be undone.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render buttons inside the visual modal using empty columns trick
    spacer_l, btn_col1, btn_col2, spacer_r = st.columns([2.2, 1, 1, 2.2])
    with btn_col1:
        if st.button("✅ Yes, Delete", key="modal_confirm_yes", type="primary", use_container_width=True):
            db = SessionLocal()
            product = db.query(Product).filter(Product.id == st.session_state["confirm_delete_product_id"]).first()
            if product:
                db.delete(product)
                db.commit()
            db.close()
            st.session_state["confirm_delete_product_id"] = None
            st.session_state["confirm_delete_product_name"] = None
            st.rerun()
    with btn_col2:
        if st.button("❌ Cancel", key="modal_confirm_no", use_container_width=True):
            st.session_state["confirm_delete_product_id"] = None
            st.session_state["confirm_delete_product_name"] = None
            st.rerun()

st.markdown('<div style="border-left:4px solid #7F77DD;padding-left:16px;margin-bottom:4px;"><span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;color:#7F77DD;font-weight:600;">Catalog</span><h2 style="margin:4px 0 0;font-family:Playfair Display,serif;color:var(--text-color, #1a1a2e);">Products & Services</h2></div>', unsafe_allow_html=True)
st.caption("Manage your offerings and track what earns the most.")
st.divider()

db = SessionLocal()

# ── Add Product ───────────────────────────────────────────────────────────────
with st.expander("➕ Add New Product / Service", expanded=False):
    with st.form("add_product"):
        col1, col2 = st.columns(2)
        with col1:
            name  = st.text_input("Name")
            price = st.number_input("Price (₱)", min_value=0.0, step=10.0)
        with col2:
            description = st.text_area("Description (optional)", height=120)

        if st.form_submit_button("Save Product", use_container_width=True):
            if not name.strip():
                st.error("Product name is required.")
            elif db.query(Product).filter(Product.owner_id == user["id"], Product.name == name.strip()).first():
                st.error("A product with that name already exists.")
            else:
                db.add(Product(owner_id=user["id"], name=name.strip(), price=price,
                               description=description.strip() or None))
                db.commit()
                st.success(f"'{name.strip()}' added!")
                st.rerun()

st.divider()
st.markdown('<div class="sec">Your Products</div>', unsafe_allow_html=True)

products = db.query(Product).filter(Product.owner_id == user["id"]).all()

if products:
    for p in products:
        booking_count = len(p.bookings)
        total_earned  = sum(b.amount for b in p.bookings if b.status == "completed")

        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        with c1:
            st.markdown(f"""
            <div style="padding:18px 0;">
                <div class="product-name">{p.name}</div>
                <div class="product-desc">{p.description or 'No description'}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.metric("Price", f"₱{p.price:,.2f}")
        with c3:
            st.metric("Total Earned", f"₱{total_earned:,.2f}", f"{booking_count} bookings")
        with c4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{p.id}", help="Delete product"):
                st.session_state["confirm_delete_product_id"] = p.id
                st.session_state["confirm_delete_product_name"] = p.name
                st.rerun()

        st.markdown('<hr style="border:none;border-top:1px solid #f0f0f0;margin:4px 0 12px;">', unsafe_allow_html=True)
else:
    st.info("No products yet. Add your first product or service above.")

db.close()