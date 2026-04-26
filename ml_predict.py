import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from datetime import datetime, timedelta


def prepare_time_series(bookings: list) -> pd.DataFrame:
    """Convert booking records into a daily revenue time series."""
    if not bookings:
        return pd.DataFrame(columns=["date", "revenue"])

    df = pd.DataFrame([{
        "date": b.booking_date.date(),
        "amount": b.amount
    } for b in bookings if b.status == "completed"])

    if df.empty:
        return pd.DataFrame(columns=["date", "revenue"])

    daily = df.groupby("date")["amount"].sum().reset_index()
    daily.columns = ["date", "revenue"]
    daily = daily.sort_values("date")

    # Fill missing dates with 0
    full_range = pd.date_range(daily["date"].min(), daily["date"].max())
    daily = daily.set_index("date").reindex(full_range, fill_value=0).reset_index()
    daily.columns = ["date", "revenue"]
    return daily


def predict_revenue(bookings: list, days_ahead: int = 30) -> dict:
    """
    Fit a polynomial regression on historical daily revenue
    and return forecast for the next N days.
    """
    df = prepare_time_series(bookings)

    result = {
        "historical": df,
        "forecast": pd.DataFrame(),
        "summary": {},
        "enough_data": False
    }

    if len(df) < 7:
        result["message"] = "Need at least 7 days of booking history to generate a forecast."
        return result

    result["enough_data"] = True

    # Encode dates as integers (days since start)
    df["day_num"] = (pd.to_datetime(df["date"]) - pd.to_datetime(df["date"].min())).dt.days
    X = df[["day_num"]].values
    y = df["revenue"].values

    # Polynomial degree 2 handles slight curves in growth
    degree = 2 if len(df) >= 14 else 1
    model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
    model.fit(X, y)

    # Generate future dates
    last_day = df["day_num"].max()
    future_days = np.arange(last_day + 1, last_day + days_ahead + 1).reshape(-1, 1)
    future_dates = [
        pd.to_datetime(df["date"].max()) + timedelta(days=int(i))
        for i in range(1, days_ahead + 1)
    ]

    predictions = model.predict(future_days)
    predictions = np.clip(predictions, 0, None)  # No negative revenue

    forecast_df = pd.DataFrame({
        "date": future_dates,
        "predicted_revenue": predictions.round(2)
    })

    # Summary stats
    historical_avg = float(df["revenue"].mean())
    forecast_avg = float(predictions.mean())
    total_forecast = float(predictions.sum())
    growth_pct = ((forecast_avg - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0

    result["forecast"] = forecast_df
    result["summary"] = {
        "historical_daily_avg": round(historical_avg, 2),
        "forecast_daily_avg": round(forecast_avg, 2),
        "total_forecast": round(total_forecast, 2),
        "growth_pct": round(growth_pct, 1),
        "days_of_history": len(df),
        "days_forecasted": days_ahead,
    }

    return result


def get_monthly_summary(bookings: list) -> pd.DataFrame:
    """Aggregate completed bookings by month for the revenue chart."""
    if not bookings:
        return pd.DataFrame(columns=["month", "revenue", "count"])

    df = pd.DataFrame([{
        "month": b.booking_date.strftime("%Y-%m"),
        "amount": b.amount,
        "status": b.status
    } for b in bookings])

    completed = df[df["status"] == "completed"]
    if completed.empty:
        return pd.DataFrame(columns=["month", "revenue", "count"])

    monthly = completed.groupby("month").agg(
        revenue=("amount", "sum"),
        count=("amount", "count")
    ).reset_index()

    return monthly.sort_values("month")
