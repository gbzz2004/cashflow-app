import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import requests
import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth import require_login
from database import SessionLocal, Booking, Product
from ml_predict import predict_revenue, get_monthly_summary

st.set_page_config(page_title="Finance Advisor", page_icon="🧠", layout="wide")

user = require_login()
if not user:
    st.warning("Please log in first.")
    st.stop()

# ── Pull all business data ────────────────────────────────────────────────────
db = SessionLocal()
bookings  = db.query(Booking).filter(Booking.owner_id == user["id"]).all()
products  = db.query(Product).filter(Product.owner_id == user["id"]).all()
db.close()

completed  = [b for b in bookings if b.status == "completed"]
pending    = [b for b in bookings if b.status == "pending"]
cancelled  = [b for b in bookings if b.status == "cancelled"]

# ── Compute financial metrics ─────────────────────────────────────────────────
def get_financial_snapshot(bookings_completed, bookings_pending, products_list):
    if not bookings_completed:
        return None

    now        = datetime.now()
    this_month = now.replace(day=1)
    last_month_start = (this_month.replace(day=1) - pd.Timedelta(days=1)).replace(day=1)
    last_month_end   = this_month

    monthly   = get_monthly_summary(bookings_completed)
    month_rev = sum(b.amount for b in bookings_completed if b.booking_date >= this_month)
    last_rev  = sum(b.amount for b in bookings_completed
                   if last_month_start <= b.booking_date < last_month_end)
    total_rev = sum(b.amount for b in bookings_completed)
    pending_val = sum(b.amount for b in bookings_pending)

    # Revenue per product
    product_revenue = {}
    for b in bookings_completed:
        pname = b.product.name if b.product else "Unknown"
        product_revenue[pname] = product_revenue.get(pname, 0) + b.amount

    top_product   = max(product_revenue, key=product_revenue.get) if product_revenue else "N/A"
    lowest_product = min(product_revenue, key=product_revenue.get) if product_revenue else "N/A"

    # Monthly growth trend
    if len(monthly) >= 2:
        last_two   = monthly.tail(2)["revenue"].tolist()
        mom_growth = ((last_two[1] - last_two[0]) / last_two[0] * 100) if last_two[0] > 0 else 0
    else:
        mom_growth = 0

    avg_monthly = monthly["revenue"].mean() if not monthly.empty else 0
    best_month  = monthly.loc[monthly["revenue"].idxmax()]["month"] if not monthly.empty else "N/A"

    return {
        "business_name":    user["business_name"],
        "total_revenue":    round(total_rev, 2),
        "this_month":       round(month_rev, 2),
        "last_month":       round(last_rev, 2),
        "mom_growth_pct":   round(mom_growth, 1),
        "avg_monthly":      round(float(avg_monthly), 2),
        "pending_payments": round(pending_val, 2),
        "total_bookings":   len(bookings_completed),
        "num_products":     len(products_list),
        "top_product":      top_product,
        "lowest_product":   lowest_product,
        "product_revenue":  {k: round(v, 2) for k, v in product_revenue.items()},
        "best_month":       best_month,
    }


def get_forecast_snapshot(bookings_all, days=90):
    result = predict_revenue(bookings_all, days_ahead=days)
    if not result["enough_data"]:
        return None
    s = result["summary"]
    return {
        "forecast_total_90d":  s["total_forecast"],
        "forecast_daily_avg":  s["forecast_daily_avg"],
        "historical_daily_avg": s["historical_daily_avg"],
        "growth_trend_pct":    s["growth_pct"],
        "days_of_history":     s["days_of_history"],
    }


# ── Build prompt for Claude ───────────────────────────────────────────────────
def build_prompt(snapshot, forecast, advice_focus):
    product_lines = "\n".join(
        f"  - {k}: ₱{v:,.2f}" for k, v in snapshot["product_revenue"].items()
    )
    forecast_section = ""
    if forecast:
        forecast_section = f"""
ML REVENUE FORECAST (90 days):
- Predicted total (next 90 days): ₱{forecast['forecast_total_90d']:,.2f}
- Predicted daily average: ₱{forecast['forecast_daily_avg']:,.2f}
- Historical daily average: ₱{forecast['historical_daily_avg']:,.2f}
- Growth trend: {forecast['growth_trend_pct']:+.1f}%
- Days of booking history used: {forecast['days_of_history']}
"""

    return f"""You are a practical financial advisor for small Filipino businesses. Your job is to give clear, honest, actionable advice based on real cashflow data.

BUSINESS PROFILE:
- Business name: {snapshot['business_name']}
- Total revenue (all time): ₱{snapshot['total_revenue']:,.2f}
- This month's revenue: ₱{snapshot['this_month']:,.2f}
- Last month's revenue: ₱{snapshot['last_month']:,.2f}
- Month-over-month growth: {snapshot['mom_growth_pct']:+.1f}%
- Average monthly revenue: ₱{snapshot['avg_monthly']:,.2f}
- Pending (unpaid) bookings: ₱{snapshot['pending_payments']:,.2f}
- Total completed bookings: {snapshot['total_bookings']}
- Number of services/products: {snapshot['num_products']}
- Best performing service: {snapshot['top_product']}
- Lowest performing service: {snapshot['lowest_product']}
- Best revenue month: {snapshot['best_month']}

REVENUE BY SERVICE:
{product_lines}
{forecast_section}

ADVICE FOCUS REQUESTED BY OWNER: {advice_focus}

Based on this real data, give specific, honest financial advice. Structure your response with these exact sections:

## 💰 Cashflow Health Summary
A 2-3 sentence honest assessment of the business's current financial health. Be direct.

## 📊 How to Allocate This Month's Revenue
Give a specific percentage-based breakdown of how ₱{snapshot['this_month']:,.2f} should be allocated. Use real peso amounts. Example categories: operating costs, emergency fund, reinvestment, owner's pay. Base percentages on the business's growth stage.

## ⚠️ What NOT to Spend On Right Now
List 3-5 specific things this business should avoid spending on given their current numbers. Be blunt and specific — not generic advice.

## 🚀 Top 3 Investment Priorities
Based on the revenue data and forecast, what are the 3 best things to invest in to grow this business? Give concrete, affordable suggestions relevant to a small Filipino business.

## 🎯 30-Day Action Plan
Give 3 specific, actionable steps the owner can do in the next 30 days to improve cashflow. Each step should be realistic and tied to their actual numbers.

Keep the tone friendly but direct — like advice from a trusted business mentor, not a textbook. Use Philippine context where relevant (e.g. mention emergency funds in peso amounts, consider local business realities). Always refer to their actual numbers."""


# ── Call Anthropic API ────────────────────────────────────────────────────────
def call_advisor(prompt: str) -> str:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"Content-Type": "application/json"},
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    data = response.json()
    if "content" in data and data["content"]:
        return data["content"][0]["text"]
    elif "error" in data:
        return f"⚠️ API error: {data['error'].get('message', 'Unknown error')}"
    return "⚠️ Could not generate advice. Please try again."


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

st.title("🧠 Finance Advisor")
st.caption("AI-powered cashflow analysis and investment advice based on your real business data.")

if not completed:
    st.warning("You need at least a few completed bookings before the advisor can analyse your cashflow.")
    st.stop()

snapshot = get_financial_snapshot(completed, pending, products)
forecast = get_forecast_snapshot(bookings, days=90)

# ── Quick metrics strip ───────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("This Month",      f"₱{snapshot['this_month']:,.2f}",
          f"{snapshot['mom_growth_pct']:+.1f}% vs last month")
c2.metric("Avg Monthly",     f"₱{snapshot['avg_monthly']:,.2f}")
c3.metric("Pending Payments",f"₱{snapshot['pending_payments']:,.2f}",
          help="Bookings not yet marked as paid")
if forecast:
    c4.metric("90-Day Forecast", f"₱{forecast['forecast_total_90d']:,.2f}",
              f"{forecast['growth_trend_pct']:+.1f}% growth trend")
else:
    c4.metric("90-Day Forecast", "Need more data")

st.divider()

# ── Revenue breakdown chart ───────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Revenue by Service")
    if snapshot["product_revenue"]:
        prod_df = pd.DataFrame(
            list(snapshot["product_revenue"].items()),
            columns=["Service", "Revenue"]
        ).sort_values("Revenue", ascending=True)
        fig = px.bar(prod_df, x="Revenue", y="Service", orientation="h",
                     color_discrete_sequence=["#7F77DD"])
        fig.update_layout(height=220, margin=dict(t=10, b=10, l=0))
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Allocation Preview")
    if snapshot["this_month"] > 0:
        rev = snapshot["this_month"]
        # Smart allocation based on growth stage
        if snapshot["mom_growth_pct"] > 10:
            alloc = {"Operating Costs": 0.40, "Reinvestment": 0.25,
                     "Emergency Fund": 0.20, "Owner's Pay": 0.15}
        elif snapshot["mom_growth_pct"] > 0:
            alloc = {"Operating Costs": 0.45, "Reinvestment": 0.20,
                     "Emergency Fund": 0.20, "Owner's Pay": 0.15}
        else:
            alloc = {"Operating Costs": 0.50, "Reinvestment": 0.10,
                     "Emergency Fund": 0.25, "Owner's Pay": 0.15}

        alloc_df = pd.DataFrame([
            {"Category": k, "Amount": round(rev * v, 2)}
            for k, v in alloc.items()
        ])
        fig2 = px.pie(alloc_df, names="Category", values="Amount", hole=0.45,
                      color_discrete_sequence=["#7F77DD","#1D9E75","#EF9F27","#E24B4A"])
        fig2.update_layout(height=220, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Suggested split — full breakdown below after AI analysis.")

st.divider()

# ── Advice focus selector ─────────────────────────────────────────────────────
st.subheader("Get Your Personalized Advice")

advice_focus = st.selectbox(
    "What do you need help with most right now?",
    [
        "General cashflow management and spending advice",
        "How to reinvest to grow my business",
        "I'm spending too much — help me cut costs",
        "Planning for slow season / low income months",
        "I want to hire staff — is it the right time?",
        "I want to expand my services or products",
        "Building an emergency fund while keeping operations running",
    ]
)

custom_context = st.text_area(
    "Any additional context? (optional)",
    placeholder="e.g. I have monthly rent of ₱8,000, I'm planning to buy equipment worth ₱15,000…",
    height=80
)

if custom_context.strip():
    advice_focus = f"{advice_focus}. Additional context from owner: {custom_context.strip()}"

# ── Generate advice ───────────────────────────────────────────────────────────
if st.button("🧠 Generate Financial Advice", use_container_width=True, type="primary"):
    with st.spinner("Analysing your cashflow and generating advice…"):
        prompt  = build_prompt(snapshot, forecast, advice_focus)
        advice  = call_advisor(prompt)

    st.divider()
    st.subheader("Your Personalised Financial Advice")
    st.markdown(advice)

    st.divider()
    st.caption(
        "⚠️ This advice is generated by AI based on your booking data. "
        "It is meant as a planning guide, not a substitute for a licensed financial advisor. "
        "Always consider your full business expenses before making financial decisions."
    )