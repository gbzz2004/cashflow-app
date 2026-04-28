import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sidebar import show_sidebar_logout
show_sidebar_logout()
from sqlalchemy.orm import joinedload
from auth import require_login
from database import SessionLocal, Booking
from ml_predict import predict_revenue
# Reset current page tracker
if st.session_state.get("current_page") != "":
    st.session_state["current_page"] = ""
    st.rerun()

st.set_page_config(page_title="Predictions", page_icon="🔮", layout="wide")

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
    border-left: 3px solid #EF9F27;
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

st.markdown('<div style="border-left:4px solid #EF9F27;padding-left:16px;margin-bottom:4px;"><span style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;color:#EF9F27;font-weight:600;">Machine Learning</span><h2 style="margin:4px 0 0;font-family:Playfair Display,serif;">Revenue Prediction</h2></div>', unsafe_allow_html=True)
st.caption("Polynomial regression on your historical booking data, powered by scikit-learn.")
st.divider()

db = SessionLocal()
bookings = db.query(Booking).options(joinedload(Booking.product)).filter(Booking.owner_id == user["id"]).all()
db.close()

# ── Controls ──────────────────────────────────────────────────────────────────
col1, col2, _ = st.columns([1, 1, 2])
with col1:
    days_ahead = st.selectbox("Forecast period", [30, 60, 90], format_func=lambda d: f"{d} days")
with col2:
    granularity = st.selectbox("View by", ["Daily", "Monthly", "Yearly"])

result = predict_revenue(bookings, days_ahead=days_ahead)

if not result["enough_data"]:
    st.warning(result.get("message", "Not enough data yet."))
    st.info("Add at least 7 days of completed bookings to unlock predictions.")
    st.stop()

s = result["summary"]

# ── KPIs ──────────────────────────────────────────────────────────────────────
section_title("Forecast Summary")
c1, c2, c3, c4 = st.columns(4)
for col, label, val in [
    (c1, f"Forecast Total ({days_ahead}d)", f"₱{s['total_forecast']:,.2f}"),
    (c2, "Predicted Daily Avg",             f"₱{s['forecast_daily_avg']:,.2f}"),
    (c3, "Historical Daily Avg",            f"₱{s['historical_daily_avg']:,.2f}"),
    (c4, "Growth Trend",                    f"{s['growth_pct']:+.1f}%"),
]:
    col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div></div>',
                 unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

# ── Prepare data ──────────────────────────────────────────────────────────────
hist = result["historical"].copy()
hist["date"] = pd.to_datetime(hist["date"])
fore = result["forecast"].copy()
fore["date"] = pd.to_datetime(fore["date"])

def group_by_granularity(df, value_col, granularity):
    df = df.copy()
    if granularity == "Daily":
        df["label"] = df["date"].dt.strftime("%b %d, %Y")
    elif granularity == "Monthly":
        df["label"] = df["date"].dt.strftime("%b %Y")
    else:
        df["label"] = df["date"].dt.strftime("%Y")
    return df.groupby("label", sort=False)[value_col].sum().reset_index()

hist_grouped = group_by_granularity(hist, "revenue",           granularity)
fore_grouped = group_by_granularity(fore, "predicted_revenue", granularity)

# ── Main forecast bar chart ───────────────────────────────────────────────────
section_title(f"Historical vs {days_ahead}-Day Forecast — {granularity}")

fig = go.Figure()
fig.add_trace(go.Bar(
    x=hist_grouped["label"],
    y=hist_grouped["revenue"],
    name="Historical",
    marker_color="#7F77DD",
    marker_line_width=0,
))
fig.add_trace(go.Bar(
    x=fore_grouped["label"],
    y=fore_grouped["predicted_revenue"],
    name=f"{days_ahead}-day Forecast",
    marker_color="#EF9F27",
    marker_line_width=0,
))
fig.update_layout(
    height=400,
    margin=dict(t=10, b=10, l=0, r=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", y=1.15, font=dict(size=12)),
    xaxis=dict(showgrid=False, type="category"),
    yaxis=dict(showgrid=True, gridcolor="#f5f5f5", title="₱"),
    barmode="group",
    hovermode="x unified",
    font=dict(size=12),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Predicted monthly breakdown ───────────────────────────────────────────────
section_title("Predicted Monthly Breakdown")

fore["month"] = fore["date"].dt.strftime("%Y-%m")
monthly_fore  = fore.groupby("month")["predicted_revenue"].sum().reset_index().sort_values("month")

fig2 = go.Figure(go.Bar(
    x=monthly_fore["month"].tolist(),
    y=monthly_fore["predicted_revenue"].tolist(),
    marker_color="#EF9F27",
    marker_line_width=0,
))
fig2.update_layout(
    height=300, margin=dict(t=10, b=10, l=0, r=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, type="category"),
    yaxis=dict(showgrid=True, gridcolor="#f5f5f5", title="₱"),
    font=dict(size=12), showlegend=False
)
st.plotly_chart(fig2, use_container_width=True)

# ── Forecast table ────────────────────────────────────────────────────────────
with st.expander("📋 Full forecast table"):
    display = fore[["date", "predicted_revenue"]].copy()
    display.columns = ["Date", "Predicted Revenue (₱)"]
    display["Date"] = display["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display, use_container_width=True, hide_index=True)

with st.expander("ℹ️ How the prediction works"):
    st.markdown(f"""
**Model:** Polynomial Regression (degree 2) — scikit-learn

**Training data:** {s['days_of_history']} days of completed booking history

1. Completed bookings are grouped by day into a daily revenue time series
2. Each day is encoded as a number so the model can learn the trend
3. A polynomial curve is fitted — capturing growth or decline patterns
4. The curve is extrapolated {days_ahead} days forward; negative values are clipped to ₱0

**Note:** This model assumes your current trend continues. One-time spikes or seasonal events won't be predicted unless they've happened before in your history.
""")