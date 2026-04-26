# CashFlow & Revenue Predictor
**Online Booking System — Cashflow and Revenue Prediction (Admin Side)**

A Streamlit web app that helps small business owners manage bookings, track income, and forecast future revenue using scikit-learn machine learning.

## Features
- Secure login and registration per business
- Add and manage products/services
- Record bookings with customer name, amount, date, and status
- Dashboard with KPIs, revenue charts, and booking stats
- ML-powered revenue prediction (30 / 60 / 90 days)
- CSV export for reports

## Tech Stack
- **Frontend + Backend:** Python + Streamlit
- **ML:** scikit-learn (Polynomial Regression)
- **Database:** SQLite (local) / PostgreSQL (Render)
- **ORM:** SQLAlchemy
- **Charts:** Plotly

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Render
1. Push this repo to GitHub
2. Sign up at render.com
3. New → Blueprint → connect your repo
4. Render reads `render.yaml` and deploys automatically

## Project Structure
```
cashflow-app/
├── app.py              # Entry point (login/register)
├── database.py         # SQLAlchemy models
├── auth.py             # Password hashing, session helpers
├── ml_predict.py       # scikit-learn prediction engine
├── requirements.txt
├── render.yaml
└── pages/
    ├── 1_Dashboard.py
    ├── 2_Bookings.py
    ├── 3_Products.py
    ├── 4_Predictions.py
    └── 5_Reports.py
```
