def load_css():
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0F1117;
    color: #E8EAF6;
}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #ffffff !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A1D2E 0%, #0F1117 100%) !important;
    border-right: 1px solid #2A2D3E !important;
}

section[data-testid="stSidebar"] .stMarkdown p {
    color: #9EA3C0 !important;
}

/* Sidebar nav links */
section[data-testid="stSidebar"] a {
    color: #9EA3C0 !important;
    text-decoration: none;
    font-size: 0.9rem;
    padding: 8px 12px;
    border-radius: 8px;
    transition: all 0.2s;
}

section[data-testid="stSidebar"] a:hover {
    color: #4F8EF7 !important;
    background: rgba(79, 142, 247, 0.1) !important;
}

/* Sidebar logo/title area */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #4F8EF7 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #4F8EF7 0%, #3B6FD4 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(79, 142, 247, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(79, 142, 247, 0.5) !important;
}

.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── Input Fields ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea {
    background-color: #1A1D2E !important;
    border: 1px solid #2A2D3E !important;
    border-radius: 10px !important;
    color: #E8EAF6 !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #4F8EF7 !important;
    box-shadow: 0 0 0 2px rgba(79, 142, 247, 0.2) !important;
}

/* ── KPI Cards ── */
.kpi-card {
    background: linear-gradient(135deg, #1A1D2E 0%, #1E2235 100%);
    border: 1px solid #2A2D3E;
    border-radius: 16px;
    padding: 24px;
    transition: transform 0.2s;
}

.kpi-card:hover {
    transform: translateY(-3px);
    border-color: #4F8EF7;
}

.kpi-label {
    font-size: 0.72rem;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 500;
}

.kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #ffffff;
    margin: 6px 0 2px;
    font-family: 'Space Grotesk', sans-serif;
}

.kpi-sub {
    font-size: 0.78rem;
    color: #4F8EF7;
}

/* ── Divider ── */
hr {
    border-color: #2A2D3E !important;
}

/* ── Tables/Dataframes ── */
.stDataFrame {
    border: 1px solid #2A2D3E !important;
    border-radius: 12px !important;
    overflow: hidden;
}

/* ── Alerts ── */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background: #1A1D2E;
    border: 1px solid #2A2D3E;
    border-radius: 14px;
    padding: 16px;
}

[data-testid="stMetricValue"] {
    color: #4F8EF7 !important;
}
</style>
"""