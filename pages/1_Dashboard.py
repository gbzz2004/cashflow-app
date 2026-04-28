import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import joinedload
from auth import require_login
from database import SessionLocal, Booking, Product
from ml_predict import get_monthly_summary, predict_revenue

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Playfair Display', serif !important; }

/* Force card backgrounds to use theme-aware colors */
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

/* Page header accent bar */
.page-header-label { font-size:0.78rem; text-transform:uppercase; letter-spacing:0.12em; font-weight:600; }
.page-header-title { margin:4px 0 0; font-family:'Playfair Display',serif;
                     color: var(--text-color, #1a1a2e); font-size:1.8rem; }

/* Recommendation cards — use semi-transparent backgrounds so they work in dark mode */
.rec-card { border-radius:14px; padding:18px 20px; margin-bottom:10px; }

/* Make Streamlit dataframes readable in dark mode */
[data-testid="stDataFrame"] { border-radius: 10px; }

/* Caption color */
.stCaption { opacity: 0.7; }
</style>''', unsafe_allow_html=True)

user = require_login()
if not user:
    st.warning("Please log in first.")
    st.stop()

db = SessionLocal()
bookings = db.query(Booking).options(joinedload(Booking.product)).filter(Booking.owner_id == user["id"]).all()
products = db.query(Product).filter(Product.owner_id == user["id"]).all()
db.close()

st.markdown(f'<div style="border-left:4px solid #7F77DD;padding-left:16px;margin-bottom:4px;"><span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;color:#7F77DD;font-weight:600;">Dashboard</span><h2 style="margin:4px 0 0;font-family:Playfair Display,serif;color:var(--text-color, #1a1a2e);">{user["business_name"]}</h2></div>', unsafe_allow_html=True)
st.caption("Welcome back. Here's your business at a glance.")
st.divider()

# ── KPIs ───────────────────────────────────────────────────────────────────────
completed  = [b for b in bookings if b.status == "completed"]
pending    = [b for b in bookings if b.status == "pending"]
cancelled  = [b for b in bookings if b.status == "cancelled"]
this_month = datetime.now().replace(day=1)
month_completed = [b for b in completed if b.booking_date >= this_month]

c1, c2, c3, c4 = st.columns(4)
for col, label, value, sub in [
    (c1, "Total Revenue",      f"₱{sum(b.amount for b in completed):,.2f}", "completed bookings"),
    (c2, "This Month",         f"₱{sum(b.amount for b in month_completed):,.2f}", "completed this month"),
    (c3, "Completed Bookings", str(len(completed)), "all time"),
    (c4, "Pending Bookings",   str(len(pending)),   "awaiting completion"),
]:
    col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
monthly = get_monthly_summary(bookings)
cl, cr = st.columns([3, 2])

with cl:
    st.markdown('<div class="sec">Monthly Revenue</div>', unsafe_allow_html=True)
    if not monthly.empty:
        fig = px.bar(monthly, x="month", y="revenue", color_discrete_sequence=["#7F77DD"],
                     labels={"month": "", "revenue": "₱"})
        fig.update_layout(height=320, margin=dict(t=10,b=10,l=0,r=0),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#f5f5f5"),
                          font=dict(size=12), showlegend=False)
        fig.update_traces(marker_cornerradius=4, marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No completed bookings yet.")

with cr:
    st.markdown('<div class="sec">Booking Status</div>', unsafe_allow_html=True)
    status_df = pd.DataFrame([
        {"Status": "Completed", "Count": len(completed)},
        {"Status": "Pending",   "Count": len(pending)},
        {"Status": "Cancelled", "Count": len([b for b in bookings if b.status == "cancelled"])},
    ])
    fig2 = px.pie(status_df, names="Status", values="Count", hole=0.58,
                  color_discrete_sequence=["#7F77DD", "#EF9F27", "#E24B4A"])
    fig2.update_layout(height=320, margin=dict(t=10,b=10,l=0,r=0),
                       paper_bgcolor="rgba(0,0,0,0)",
                       legend=dict(orientation="h", y=-0.15, font=dict(size=12)))
    fig2.update_traces(textinfo="percent", textfont_size=11)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Forecast ───────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">30-Day Forecast</div>', unsafe_allow_html=True)
result = predict_revenue(bookings, days_ahead=30)

if result["enough_data"]:
    s = result["summary"]
    f1, f2, f3 = st.columns(3)
    for col, label, val in [
        (f1, "Forecast Total",      f"₱{s['total_forecast']:,.2f}"),
        (f2, "Predicted Daily Avg", f"₱{s['forecast_daily_avg']:,.2f}"),
        (f3, "Growth vs History",   f"{s['growth_pct']:+.1f}%"),
    ]:
        col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value" style="font-size:1.3rem;">{val}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    hist = result["historical"].copy(); hist["date"] = pd.to_datetime(hist["date"])
    fore = result["forecast"].copy();   fore["date"] = pd.to_datetime(fore["date"])
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=hist["date"], y=hist["revenue"], name="Historical",
                              line=dict(color="#7F77DD", width=2)))
    fig3.add_trace(go.Scatter(x=fore["date"], y=fore["predicted_revenue"], name="Forecast",
                              line=dict(color="#EF9F27", width=2, dash="dash")))
    fig3.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                       legend=dict(orientation="h", y=1.2, font=dict(size=12)),
                       xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#f5f5f5"),
                       hovermode="x unified")
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("See **Predictions** for 30/60/90-day full forecasts.")
else:
    st.info(result.get("message", "Add more bookings to unlock predictions."))

st.divider()

# ── Recent Bookings ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Recent Bookings</div>', unsafe_allow_html=True)
if bookings:
    recent = sorted(bookings, key=lambda b: b.booking_date, reverse=True)[:8]
    rows = [{
        "Date":    b.booking_date.strftime("%b %d, %Y"),
        "Customer":b.customer_name,
        "Service": b.product.name if b.product else "—",
        "Amount":  f"₱{b.amount:,.2f}",
        "Status":  b.status.capitalize(),
        
    } for b in recent]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No bookings yet. Go to **Bookings** to add your first one.")
