import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import joinedload
from auth import require_login
from database import SessionLocal, Booking
from sidebar import show_sidebar_logout
show_sidebar_logout()
if st.session_state.get("current_page") != "":
    st.session_state["current_page"] = ""
    st.rerun()
st.set_page_config(page_title="Reports", page_icon="📄", layout="wide")

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

/* Section titles — color:inherit lets Streamlit's theme control visibility */
.sec-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 12px;
    padding-left: 10px;
    border-left: 3px solid #7F77DD;
    color: inherit;
}

.rec-card { border-radius:14px; padding:18px 20px; margin-bottom:10px; }
[data-testid="stDataFrame"] { border-radius: 10px; }
.stCaption { opacity: 0.7; }
</style>''', unsafe_allow_html=True)

def section_title(text):
    st.markdown(f'<p class="sec-title">{text}</p>', unsafe_allow_html=True)

user = require_login()
if not user:
    st.warning("Please log in first.")
    st.stop()

st.markdown('<div style="border-left:4px solid #7F77DD;padding-left:16px;margin-bottom:4px;"><span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;color:#7F77DD;font-weight:600;">Analytics</span><h2 style="margin:4px 0 0;font-family:Playfair Display,serif;">Reports & Export</h2></div>', unsafe_allow_html=True)
st.caption("Review your booking history, export data, and get AI-powered financial recommendations.")
st.divider()

db = SessionLocal()
bookings = db.query(Booking).options(joinedload(Booking.product)).filter(Booking.owner_id == user["id"]).all()
db.close()

if not bookings:
    st.info("No bookings yet. Add some bookings first.")
    st.stop()

# ── Filters ────────────────────────────────────────────────────────────────────
f1, f2, f3 = st.columns(3)
dates = [b.booking_date for b in bookings]
with f1: start_date    = st.date_input("From", value=min(dates).date())
with f2: end_date      = st.date_input("To",   value=max(dates).date())
with f3: status_filter = st.selectbox("Status", ["All", "completed", "pending", "cancelled"])

filtered = [b for b in bookings
            if start_date <= b.booking_date.date() <= end_date
            and (status_filter == "All" or b.status == status_filter)]

st.divider()

# ── Summary KPIs ───────────────────────────────────────────────────────────────
paid_f = [b for b in filtered if b.status == "completed"]
avg    = sum(b.amount for b in paid_f) / len(paid_f) if paid_f else 0

c1, c2, c3, c4 = st.columns(4)
for col, label, val in [
    (c1, "Total Revenue",   f"₱{sum(b.amount for b in paid_f):,.2f}"),
    (c2, "Total Bookings",  str(len(filtered))),
    (c3, "Completed",       str(len(paid_f))),
    (c4, "Avg per Booking", f"₱{avg:,.2f}"),
]:
    col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div></div>',
                 unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# ── Two-column layout: Left = Reports | Right = AI Recommendations ────────────
# ══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 1], gap="large")

# ── LEFT: Revenue by Service + Booking Detail + Export ────────────────────────
with col_left:
    section_title("Revenue by Service")
    if paid_f:
        by_product = {}
        for b in paid_f:
            pname = b.product.name if b.product else "Unknown"
            by_product[pname] = by_product.get(pname, 0) + b.amount
        prod_df = pd.DataFrame(list(by_product.items()), columns=["Product", "Revenue"]).sort_values("Revenue", ascending=False)
        fig = px.bar(prod_df, x="Product", y="Revenue", color_discrete_sequence=["#7F77DD"],
                     labels={"Product": "", "Revenue": "₱"})
        fig.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#f5f5f5"),
                          font=dict(size=12), showlegend=False)
        fig.update_traces(marker_cornerradius=4, marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No completed bookings in this date range.")

    st.divider()
    section_title("Booking Detail")
    if filtered:
        rows = [{
            "Date":       b.booking_date.strftime("%b %d, %Y"),
            "Customer":   b.customer_name,
            "Service":    b.product.name if b.product else "—",
            "Amount (₱)": round(b.amount, 2),
            "Status":     b.status.capitalize(),
            "Notes":      b.notes or ""
        } for b in sorted(filtered, key=lambda b: b.booking_date, reverse=True)]

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        section_title("Export")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV Report", data=csv,
                           file_name=f"cashflow_report_{start_date}_{end_date}.csv",
                           mime="text/csv", use_container_width=True)
        st.caption("Open in Excel or Google Sheets for further analysis.")
    else:
        st.info("No bookings match the selected filters.")

# ── RIGHT: AI Business Recommendations ────────────────────────────────────────
with col_right:
    st.markdown('<div style="border-left:4px solid #EF9F27;padding-left:16px;margin-bottom:16px;"><span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;color:#EF9F27;font-weight:600;">AI Powered</span><h3 style="margin:4px 0 0;font-family:Playfair Display,serif;">Business Recommendations</h3></div>', unsafe_allow_html=True)
    st.caption("Analyzes your revenue trends, booking patterns, and product performance.")

    all_completed = [b for b in bookings if b.status == "completed"]

    if len(all_completed) < 3:
        st.info("Add at least 3 completed bookings to unlock AI recommendations.")
    else:
        import numpy as np
        from sklearn.linear_model import LinearRegression
        from collections import defaultdict

        all_amounts  = [b.amount for b in all_completed]
        total_income = sum(all_amounts)
        avg_booking  = total_income / len(all_completed)

        monthly = defaultdict(float)
        for b in all_completed:
            monthly[b.booking_date.strftime("%Y-%m")] += b.amount
        sorted_months    = sorted(monthly.keys())
        monthly_revenues = [monthly[m] for m in sorted_months]
        num_months       = len(sorted_months)

        if num_months >= 2:
            X_m = np.arange(num_months).reshape(-1, 1)
            lr  = LinearRegression().fit(X_m, np.array(monthly_revenues))
            trend_slope     = lr.coef_[0]
            next_month_pred = max(0, float(lr.predict([[num_months]])[0]))
        else:
            trend_slope     = 0
            next_month_pred = monthly_revenues[0] if monthly_revenues else 0

        product_revenue = defaultdict(float)
        product_count   = defaultdict(int)
        for b in all_completed:
            pname = b.product.name if b.product else "Unknown"
            product_revenue[pname] += b.amount
            product_count[pname]   += 1

        best_product  = max(product_revenue, key=product_revenue.get)
        worst_product = min(product_revenue, key=product_revenue.get)
        num_products  = len(product_revenue)

        volatility     = float(np.std(monthly_revenues)) if num_months > 1 else 0
        monthly_avg    = total_income / max(num_months, 1)
        volatility_pct = (volatility / monthly_avg * 100) if monthly_avg > 0 else 0

        recommended_savings   = total_income * 0.20
        recommended_opex      = total_income * 0.40
        recommended_marketing = total_income * 0.10
        emergency_fund        = monthly_avg * 3
        estimated_profit      = total_income * 0.60
        reinvestment          = estimated_profit * 0.30

        # Trend banner
        if trend_slope > 0:
            t_label, t_bg, t_br = "📈 Growing", "#dcfce7", "#86efac"
            t_text = f"Revenue trending <strong>upward</strong> by ₱{trend_slope:,.2f}/month."
        elif trend_slope < 0:
            t_label, t_bg, t_br = "📉 Declining", "#fef2f2", "#fca5a5"
            t_text = f"Revenue <strong>declining</strong> by ₱{abs(trend_slope):,.2f}/month. Consider promotions or new services."
        else:
            t_label, t_bg, t_br = "➡️ Stable", "#fefce8", "#fde68a"
            t_text = "Revenue is stable. Good time to plan growth."

        st.markdown(f"""
        <div style="background:{t_bg};border:1.5px solid {t_br};border-radius:12px;padding:16px 18px;margin-bottom:14px;">
            <div style="font-weight:700;font-size:0.95rem;margin-bottom:4px;color:#1a1a2e;">{t_label} — Revenue Trend</div>
            <div style="font-size:0.87rem;color:#1a1a2e;">{t_text}</div>
            <div style="margin-top:6px;font-size:0.82rem;color:#555;">Next month estimate: <strong>₱{next_month_pred:,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)

        # KPI strip
        k1, k2 = st.columns(2)
        k1.markdown(f'<div class="kpi"><div class="kpi-label">💰 Savings</div><div class="kpi-value" style="font-size:1.1rem;">₱{recommended_savings:,.2f}</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi"><div class="kpi-label">📊 Est. Profit</div><div class="kpi-value" style="font-size:1.1rem;">₱{estimated_profit:,.2f}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Advice cards
        growth_tip = (f"Only {num_products} product(s) — add more to grow."
                      if num_products < 3 else "Good variety — focus on top performers.")
        st.markdown(f"""
        <div class="rec-card" style="background:#f0f9ff;border:1px solid #bae6fd;">
            <div style="font-weight:700;font-size:0.9rem;margin-bottom:6px;color:#1a1a2e;">🏦 Savings & Emergency Fund</div>
            <div style="font-size:0.85rem;line-height:1.75;color:#1a1a2e;">
                • Save <strong>₱{recommended_savings:,.2f}</strong> (20% of income)<br>
                • Emergency fund: <strong>₱{emergency_fund:,.2f}</strong> (3-month reserve)<br>
                • Save before calculating spending budget
            </div>
        </div>
        <div class="rec-card" style="background:#fdf4ff;border:1px solid #e9d5ff;">
            <div style="font-weight:700;font-size:0.9rem;margin-bottom:6px;color:#1a1a2e;">📣 Marketing & Growth</div>
            <div style="font-size:0.85rem;line-height:1.75;color:#1a1a2e;">
                • Marketing: <strong>₱{recommended_marketing:,.2f}</strong> (10% of income)<br>
                • Best: <strong>{best_product}</strong><br>
                • Weakest: <strong>{worst_product}</strong> — reprice or phase out<br>
                • {growth_tip}
            </div>
        </div>
        <div class="rec-card" style="background:#fff7ed;border:1px solid #fed7aa;">
            <div style="font-weight:700;font-size:0.9rem;margin-bottom:6px;color:#1a1a2e;">⚙️ Operating Expenses</div>
            <div style="font-size:0.85rem;line-height:1.75;color:#1a1a2e;">
                • OPEX ceiling: <strong>₱{recommended_opex:,.2f}</strong> (40% of income)<br>
                • Reinvestment: <strong>₱{reinvestment:,.2f}</strong> (30% of profit)<br>
                • Avg booking: <strong>₱{avg_booking:,.2f}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Volatility card
        vol_label = "Low ✅" if volatility_pct < 30 else ("Moderate ⚠️" if volatility_pct < 60 else "High 🚨")
        v_bg  = "#f0fdf4" if volatility_pct < 30 else ("#fefce8" if volatility_pct < 60 else "#fef2f2")
        v_br  = "#86efac" if volatility_pct < 30 else ("#fde68a" if volatility_pct < 60 else "#fca5a5")
        v_advice = ("Stable income — good for fixed expense planning." if volatility_pct < 30
                    else ("Variable income — avoid large fixed commitments." if volatility_pct < 60
                    else "High swings — build a larger emergency fund."))
        st.markdown(f"""
        <div class="rec-card" style="background:{v_bg};border:1px solid {v_br};">
            <div style="font-weight:700;font-size:0.9rem;margin-bottom:6px;color:#1a1a2e;">📉 Income Volatility: {vol_label}</div>
            <div style="font-size:0.85rem;line-height:1.75;color:#1a1a2e;">
                • Score: <strong>{volatility_pct:.1f}%</strong> | Std dev: <strong>₱{volatility:,.2f}</strong><br>
                • Monthly avg: <strong>₱{monthly_avg:,.2f}</strong><br>
                • {v_advice}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Budget pie
        section_title("Budget Allocation")
        buffer = max(0, total_income - recommended_savings - recommended_opex - recommended_marketing - reinvestment)
        alloc_df = pd.DataFrame([
            {"Category": "💰 Savings",      "Amount": recommended_savings},
            {"Category": "⚙️ Operations",   "Amount": recommended_opex},
            {"Category": "📣 Marketing",    "Amount": recommended_marketing},
            {"Category": "🔁 Reinvestment", "Amount": reinvestment},
            {"Category": "🧾 Buffer",       "Amount": buffer},
        ])
        fig_a = px.pie(alloc_df, names="Category", values="Amount", hole=0.52,
                       color_discrete_sequence=["#7F77DD","#EF9F27","#60a5fa","#34d399","#f87171"])
        fig_a.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                            paper_bgcolor="rgba(0,0,0,0)",
                            legend=dict(orientation="h", y=-0.2, font=dict(size=11)))
        fig_a.update_traces(textinfo="percent", textfont_size=11)
        st.plotly_chart(fig_a, use_container_width=True)
        st.caption("⚠️ ML-generated estimates. Consult a financial advisor for major decisions.")