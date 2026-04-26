import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sidebar import show_sidebar_logout
from auth import require_login
from database import SessionLocal, Product

st.set_page_config(page_title="Products", page_icon="🛍️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Playfair Display', serif !important; }
.sec { font-family:'Playfair Display',serif; font-size:1.05rem; font-weight:600; color:#1a1a2e; margin-bottom:12px; }
.product-card {
    background:#fafafa; border:1px solid #ececec; border-radius:14px;
    padding:18px 22px; margin-bottom:10px;
    display:flex; align-items:center; justify-content:space-between;
}
.product-name { font-weight:600; font-size:1rem; color:#1a1a2e; }
.product-desc { font-size:0.83rem; color:#aaa; margin-top:3px; }
.product-price { font-size:1.1rem; font-weight:700; color:#7F77DD; }
.product-stat  { font-size:0.82rem; color:#999; margin-top:2px; }
</style>
""", unsafe_allow_html=True)

user = require_login()
show_sidebar_logout()
if not user:
    st.warning("Please log in first.")
    st.stop()

st.markdown("## 🛍️ Products & Services")
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
                db.delete(p)
                db.commit()
                st.rerun()

        st.markdown('<hr style="border:none;border-top:1px solid #f0f0f0;margin:4px 0 12px;">', unsafe_allow_html=True)
else:
    st.info("No products yet. Add your first product or service above.")

db.close()
