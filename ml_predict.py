import pandas as pd
import numpy as np
from datetime import timedelta

# ── Prophet import with graceful fallback ─────────────────────────────────────
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

# ── Fallback: simple linear regression if Prophet not installed ───────────────
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline


def prepare_time_series(bookings: list) -> pd.DataFrame:
    """Convert booking records into a daily revenue time series."""
    if not bookings:
        return pd.DataFrame(columns=["date", "revenue"])

    df = pd.DataFrame([{
        "date": b.booking_date.date(),
        "amount": b.amount
    } for b in bookings if b.status and b.status.lower() == "completed"])

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


def _forecast_with_prophet(df: pd.DataFrame, days_ahead: int):
    """Run Prophet forecast. Returns forecast_df and predictions array."""
    import logging
    logging.getLogger("prophet").setLevel(logging.WARNING)
    logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

    # Prophet expects columns: ds (date), y (value)
    prophet_df = df.rename(columns={"date": "ds", "revenue": "y"})
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative" if prophet_df["y"].mean() > 0 else "additive",
        changepoint_prior_scale=0.05,  # less sensitive to noise
        interval_width=0.80,           # 80% confidence interval
    )

    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=days_ahead, freq="D")
    forecast = model.predict(future)

    # Split into historical fitted values and future forecast
    hist_len = len(df)
    future_fc = forecast.iloc[hist_len:][["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    future_fc["yhat"]       = future_fc["yhat"].clip(lower=0).round(2)
    future_fc["yhat_lower"] = future_fc["yhat_lower"].clip(lower=0).round(2)
    future_fc["yhat_upper"] = future_fc["yhat_upper"].clip(lower=0).round(2)

    forecast_df = pd.DataFrame({
        "date":              future_fc["ds"].values,
        "predicted_revenue": future_fc["yhat"].values,
        "lower_bound":       future_fc["yhat_lower"].values,
        "upper_bound":       future_fc["yhat_upper"].values,
    })

    predictions = future_fc["yhat"].values
    return forecast_df, predictions


def _forecast_with_polynomial(df: pd.DataFrame, days_ahead: int):
    """Fallback polynomial regression forecast."""
    df = df.copy()
    df["day_num"] = (pd.to_datetime(df["date"]) - pd.to_datetime(df["date"].min())).dt.days
    X = df[["day_num"]].values
    y = df["revenue"].values

    degree = 2 if len(df) >= 14 else 1
    model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
    model.fit(X, y)

    last_day = df["day_num"].max()
    future_days = np.arange(last_day + 1, last_day + days_ahead + 1).reshape(-1, 1)
    future_dates = [
        pd.to_datetime(df["date"].max()) + timedelta(days=int(i))
        for i in range(1, days_ahead + 1)
    ]

    predictions = np.clip(model.predict(future_days), 0, None)

    forecast_df = pd.DataFrame({
        "date":              future_dates,
        "predicted_revenue": predictions.round(2),
        "lower_bound":       predictions.round(2),
        "upper_bound":       predictions.round(2),
    })
    return forecast_df, predictions


def predict_revenue(bookings: list, days_ahead: int = 30) -> dict:
    """
    Forecast daily revenue using Prophet (or polynomial regression as fallback).
    Drop-in replacement — same function signature and return structure.
    """
    df = prepare_time_series(bookings)

    result = {
        "historical":  df,
        "forecast":    pd.DataFrame(),
        "summary":     {},
        "enough_data": False,
        "model_used":  "prophet" if PROPHET_AVAILABLE else "polynomial",
    }

    if len(df) < 7:
        result["message"] = "Need at least 7 days of booking history to generate a forecast."
        return result

    result["enough_data"] = True

    try:
        if PROPHET_AVAILABLE:
            forecast_df, predictions = _forecast_with_prophet(df, days_ahead)
        else:
            forecast_df, predictions = _forecast_with_polynomial(df, days_ahead)
    except Exception as e:
        # If Prophet fails for any reason, silently fall back to polynomial
        forecast_df, predictions = _forecast_with_polynomial(df, days_ahead)
        result["model_used"]      = "polynomial"
        result["fallback_reason"] = str(e)

    historical_avg = float(df["revenue"].mean())
    forecast_avg   = float(predictions.mean())
    total_forecast = float(predictions.sum())
    growth_pct     = ((forecast_avg - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0

    result["forecast"] = forecast_df
    result["summary"]  = {
        "historical_daily_avg": round(historical_avg, 2),
        "forecast_daily_avg":   round(forecast_avg, 2),
        "total_forecast":       round(total_forecast, 2),
        "growth_pct":           round(growth_pct, 1),
        "days_of_history":      len(df),
        "days_forecasted":      days_ahead,
    }

    return result


def get_monthly_summary(bookings: list) -> pd.DataFrame:
    """Aggregate completed bookings by month for the revenue chart."""
    if not bookings:
        return pd.DataFrame(columns=["month", "revenue", "count"])

    df = pd.DataFrame([{
        "month":  b.booking_date.strftime("%Y-%m"),
        "amount": b.amount,
        "status": b.status
    } for b in bookings])

    completed = df[df["status"].str.lower() == "completed"]
    if completed.empty:
        return pd.DataFrame(columns=["month", "revenue", "count"])

    monthly = completed.groupby("month").agg(
        revenue=("amount", "sum"),
        count=("amount", "count")
    ).reset_index()

    return monthly.sort_values("month")