import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
import re
import os
import io
from datetime import datetime

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="European Macro Analyzer",
    page_icon="🇪🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Finance Dark Theme Styling
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stMetric {
        background-color: #161a23;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 12px;
    }
    .badge-bullish {
        background-color: rgba(0, 200, 83, 0.15);
        color: #00c853;
        border: 1px solid rgba(0, 200, 83, 0.3);
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-bearish {
        background-color: rgba(244, 67, 54, 0.15);
        color: #f44336;
        border: 1px solid rgba(244, 67, 54, 0.3);
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-neutral {
        background-color: rgba(41, 98, 255, 0.15);
        color: #2962ff;
        border: 1px solid rgba(41, 98, 255, 0.3);
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Asset & Macro Configurations
# ---------------------------------------------------------
EU_ASSET_MAPPING = {
    'DAX 40 (Germany)': {'country': 'Germany', 'cot': 'DAX', 'ticker': '^GDAXI', 'flag': '🇩🇪'},
    'CAC 40 (France)': {'country': 'France', 'cot': 'CAC', 'ticker': '^FCHI', 'flag': '🇫🇷'},
    'FTSE 100 (UK)': {'country': 'UK', 'cot': 'FTSE', 'ticker': '^FTSE', 'flag': '🇬🇧'}
}

BASELINE_FORECASTS = {
    'Germany': {
        'GDP Growth QoQ': 0.1,
        'ifo Business Climate Index': 89.0,
        'HCOB Manufacturing PMI': 45.5,
        'Industrial Production MoM': 0.2,
        'Retail Sales MoM': 0.3,
        'GfK Consumer Climate Index': -22.0,
        'Real Wage Growth YoY': 3.2,
        'KBA Car Registrations YoY': 2.0,
        'CPI YoY': 2.1,
        'Core CPI YoY': 2.4,
        'PPI YoY': 0.0,
        '2 Yr Yield (30d SMA)': 2.42,
        'Unemployment Rate %': 6.0,
        'Unemployment Change MoM': 8.0,
        'Employment Change': 0.1,
        'BA-X Job Vacancy Index': 117.8
    },
    'France': {
        'INSEE GDP Growth QoQ': 0.2,
        'INSEE Business Climate Indicator': 101.0,
        'HCOB France Composite PMI': 51.0,
        'Industrial Production MoM': 0.2,
        'Household Goods Consumption MoM': 0.2,
        'INSEE Consumer Confidence Indicator': 93.0,
        'Real Wage Growth YoY (SMB)': 2.4,
        'New Car Registrations YoY': 1.5,
        'French HICP YoY': 2.0,
        'Core CPI YoY': 2.2,
        'Producer Price Index YoY': 0.1,
        '2Y OAT Yield (30d SMA)': 2.58,
        'ILO Unemployment Rate %': 7.4,
        'France Travail Jobseekers MoM': 3.5,
        'Non-Farm Employment QoQ': 0.1,
        'Hiring Difficulties Index': 51.0
    },
    'UK': {
        'UK GDP Growth QoQ': 0.3,
        'UK Composite PMI': 52.0,
        'Industrial & Manufacturing Production MoM': 0.4,
        'CBI Business Optimism': 10.0,
        'Retail Sales Volumes MoM (Ex-Fuel)': 0.4,
        'GfK UK Consumer Confidence': -14.0,
        'Real Regular Earnings YoY': 2.8,
        'SMMT New Car Registrations YoY': 2.0,
        'UK Headline CPI YoY': 2.4,
        'UK Core CPI YoY': 3.5,
        'PPI Output YoY': 0.4,
        '2Y Gilt Yield (30d SMA)': 3.82,
        'UK Unemployment Rate (3M %)': 4.2,
        'Claimant Count Change MoM': 5.0,
        'Employment Change 3M/3M': 45.0,
        'ONS Total Job Vacancies': 875.0
    }
}

DATASETS = {
    'Germany': {
        'GDP Growth QoQ': [0.1, -0.3, 0.2, -0.1, 0.2, 0.3, 0.1, 0.2],
        'ifo Business Climate Index': [86.5, 87.2, 88.0, 87.5, 88.6, 89.2, 88.7, 89.4],
        'HCOB Manufacturing PMI': [41.8, 42.4, 43.1, 42.6, 43.8, 44.5, 45.1, 46.2],
        'Industrial Production MoM': [-0.6, 0.4, -1.1, 0.7, -0.3, 0.8, -0.2, 0.6],
        'Retail Sales MoM': [-0.4, 0.6, -1.2, 0.8, -0.3, 0.5, 0.2, -0.1],
        'GfK Consumer Climate Index': [-28.1, -27.5, -26.2, -25.8, -24.4, -23.9, -22.5, -21.8],
        'Real Wage Growth YoY': [1.8, 2.1, 2.4, 2.8, 3.1, 3.3, 3.2, 3.5],
        'KBA Car Registrations YoY': [-4.2, -2.1, 1.5, -1.8, 2.4, 3.1, 1.2, 2.8],
        'CPI YoY': [2.8, 2.5, 2.4, 2.2, 2.0, 1.9, 2.2, 2.1],
        'Core CPI YoY': [3.4, 3.2, 3.0, 2.8, 2.8, 2.7, 2.8, 2.7],
        'PPI YoY': [-1.6, -1.1, -0.8, -0.4, -0.1, 0.2, -0.2, 0.1],
        '2 Yr Yield (30d SMA)': [2.95, 2.88, 2.75, 2.62, 2.50, 2.42, 2.38, 2.31],
        'Unemployment Rate %': [5.8, 5.9, 5.9, 6.0, 6.0, 6.0, 6.1, 6.0],
        'Unemployment Change MoM': [12.0, 10.0, 15.0, 8.0, 14.0, 11.0, 7.0, 5.0],
        'Employment Change': [0.1, 0.2, 0.0, 0.1, 0.2, 0.1, 0.0, 0.1],
        'BA-X Job Vacancy Index': [114.5, 115.2, 116.0, 115.8, 117.2, 118.0, 117.5, 118.5]
    },
    'France': {
        'INSEE GDP Growth QoQ': [0.1, 0.2, 0.3, 0.2, 0.3, 0.4, 0.2, 0.3],
        'INSEE Business Climate Indicator': [98.2, 98.8, 99.5, 99.1, 100.4, 101.2, 100.5, 101.8],
        'HCOB France Composite PMI': [48.1, 48.6, 49.2, 49.8, 50.4, 51.1, 50.8, 51.4],
        'Industrial Production MoM': [-0.5, 0.3, -0.8, 0.5, -0.2, 0.6, -0.1, 0.4],
        'Household Goods Consumption MoM': [-0.3, 0.4, -0.6, 0.5, -0.1, 0.3, 0.1, 0.2],
        'INSEE Consumer Confidence Indicator': [89.0, 89.8, 90.5, 91.2, 92.0, 92.8, 92.4, 93.5],
        'Real Wage Growth YoY (SMB)': [1.5, 1.8, 2.0, 2.2, 2.3, 2.5, 2.4, 2.6],
        'New Car Registrations YoY': [-2.5, -1.0, 0.8, -0.5, 1.2, 1.8, 1.4, 2.1],
        'French HICP YoY': [2.6, 2.4, 2.3, 2.1, 2.0, 1.8, 2.0, 1.9],
        'Core CPI YoY': [3.0, 2.8, 2.6, 2.4, 2.3, 2.2, 2.3, 2.1],
        'Producer Price Index YoY': [-1.2, -0.8, -0.5, -0.2, 0.0, 0.2, 0.1, 0.3],
        '2Y OAT Yield (30d SMA)': [3.10, 3.02, 2.91, 2.80, 2.68, 2.58, 2.52, 2.45],
        'ILO Unemployment Rate %': [7.5, 7.5, 7.4, 7.4, 7.3, 7.4, 7.4, 7.3],
        'France Travail Jobseekers MoM': [5.2, 4.1, 6.8, 3.2, 5.0, 3.8, 2.5, 1.8],
        'Non-Farm Employment QoQ': [0.1, 0.1, 0.2, 0.1, 0.2, 0.1, 0.1, 0.2],
        'Hiring Difficulties Index': [54.0, 53.5, 52.8, 52.0, 51.5, 50.8, 51.2, 50.4]
    },
    'UK': {
        'UK GDP Growth QoQ': [0.2, 0.1, 0.3, 0.4, 0.5, 0.6, 0.3, 0.4],
        'UK Composite PMI': [49.5, 50.2, 51.0, 51.8, 52.5, 53.0, 52.2, 52.8],
        'Industrial & Manufacturing Production MoM': [-0.4, 0.2, -0.6, 0.5, -0.1, 0.7, 0.2, 0.5],
        'CBI Business Optimism': [2.0, 4.5, 7.0, 8.5, 11.0, 13.5, 9.8, 12.0],
        'Retail Sales Volumes MoM (Ex-Fuel)': [-0.5, 0.5, -0.8, 0.6, 0.2, 0.8, 0.3, 0.4],
        'GfK UK Consumer Confidence': [-21.0, -19.5, -18.0, -16.5, -15.0, -13.5, -14.2, -13.0],
        'Real Regular Earnings YoY': [1.9, 2.2, 2.5, 2.7, 2.9, 3.1, 2.8, 3.0],
        'SMMT New Car Registrations YoY': [-1.8, 0.2, 1.4, -0.2, 2.1, 2.8, 1.9, 2.5],
        'UK Headline CPI YoY': [3.2, 2.9, 2.7, 2.5, 2.3, 2.2, 2.5, 2.4],
        'UK Core CPI YoY': [4.2, 3.9, 3.7, 3.6, 3.5, 3.4, 3.6, 3.5],
        'PPI Output YoY': [-0.8, -0.3, 0.1, 0.3, 0.5, 0.6, 0.3, 0.4],
        '2Y Gilt Yield (30d SMA)': [4.45, 4.32, 4.18, 4.05, 3.92, 3.82, 3.75, 3.68],
        'UK Unemployment Rate (3M %)': [4.4, 4.4, 4.3, 4.3, 4.2, 4.2, 4.2, 4.1],
        'Claimant Count Change MoM': [18.5, 22.1, 14.8, 11.2, 8.4, 6.2, 5.1, 4.3],
        'Employment Change 3M/3M': [12.0, -8.0, 45.0, 62.0, 85.0, 48.0, 32.0, 54.0],
        'ONS Total Job Vacancies': [845.0, 852.0, 860.0, 858.0, 868.0, 875.0, 870.0, 882.0]
    }
}

INVERTED_METRICS = {
    'CPI YoY', 'Core CPI YoY', 'PPI YoY', '2 Yr Yield (30d SMA)', 'Unemployment Rate %', 'Unemployment Change MoM',
    'French HICP YoY', 'Producer Price Index YoY', '2Y OAT Yield (30d SMA)', 'ILO Unemployment Rate %', 'France Travail Jobseekers MoM', 'Hiring Difficulties Index',
    'UK Headline CPI YoY', 'UK Core CPI YoY', 'PPI Output YoY', '2Y Gilt Yield (30d SMA)', 'UK Unemployment Rate (3M %)', 'Claimant Count Change MoM'
}

METRIC_CATEGORIES = {
    'Germany': [
        {
            'title': 'Economic Growth & Industrial Momentum',
            'icon': '📈',
            'badge': 'Destatis, ifo Institute & S&P Global HCOB',
            'badge_color': '#2962FF',
            'badge_bg': 'rgba(41, 98, 255, 0.12)',
            'badge_border': 'rgba(41, 98, 255, 0.25)',
            'metrics': [
                {'key': 'GDP Growth QoQ', 'suffix': '%'},
                {'key': 'ifo Business Climate Index', 'suffix': ''},
                {'key': 'HCOB Manufacturing PMI', 'suffix': ''},
                {'key': 'Industrial Production MoM', 'suffix': '%'},
            ]
        },
        {
            'title': 'State of the Consumer',
            'icon': '🛒',
            'badge': 'Domestic Demand & Household Balance (Destatis / NIM / KBA)',
            'badge_color': '#2962FF',
            'badge_bg': 'rgba(41, 98, 255, 0.12)',
            'badge_border': 'rgba(41, 98, 255, 0.25)',
            'metrics': [
                {'key': 'Retail Sales MoM', 'suffix': '%'},
                {'key': 'GfK Consumer Climate Index', 'suffix': ''},
                {'key': 'Real Wage Growth YoY', 'suffix': '%'},
                {'key': 'KBA Car Registrations YoY', 'suffix': '%'},
            ]
        },
        {
            'title': 'Inflation & Monetary Conditions',
            'icon': '🔥',
            'badge': 'Inverted: High Prints Increase ECB Tightening Pressure',
            'badge_color': '#F44336',
            'badge_bg': 'rgba(244, 67, 54, 0.12)',
            'badge_border': 'rgba(244, 67, 54, 0.25)',
            'metrics': [
                {'key': 'CPI YoY', 'suffix': '%'},
                {'key': 'Core CPI YoY', 'suffix': '%'},
                {'key': 'PPI YoY', 'suffix': '%'},
                {'key': '2 Yr Yield (30d SMA)', 'suffix': '%'},
            ]
        },
        {
            'title': 'Labor Market & Employment Stability',
            'icon': '💼',
            'badge': 'Workforce Resilience & Labor Slack (BA / Destatis)',
            'badge_color': '#2962FF',
            'badge_bg': 'rgba(41, 98, 255, 0.12)',
            'badge_border': 'rgba(41, 98, 255, 0.25)',
            'metrics': [
                {'key': 'Unemployment Rate %', 'suffix': '%'},
                {'key': 'Unemployment Change MoM', 'suffix': 'k'},
                {'key': 'Employment Change', 'suffix': '%'},
                {'key': 'BA-X Job Vacancy Index', 'suffix': ''},
            ]
        }
    ],
    'France': [
        {
            'title': 'Economic Growth & Business Activity',
            'icon': '📈',
            'badge': 'INSEE & S&P Global HCOB',
            'badge_color': '#2962FF',
            'badge_bg': 'rgba(41, 98, 255, 0.12)',
            'badge_border': 'rgba(41, 98, 255, 0.25)',
            'metrics': [
                {'key': 'INSEE GDP Growth QoQ', 'suffix': '%'},
                {'key': 'INSEE Business Climate Indicator', 'suffix': ''},
                {'key': 'HCOB France Composite PMI', 'suffix': ''},
                {'key': 'Industrial Production MoM', 'suffix': '%'},
            ]
        },
        {
            'title': 'State of the Consumer & Household Demand',
            'icon': '🛒',
            'badge': 'INSEE Dépenses & PFA Auto Registrations',
            'badge_color': '#2962FF',
            'badge_bg': 'rgba(41, 98, 255, 0.12)',
            'badge_border': 'rgba(41, 98, 255, 0.25)',
            'metrics': [
                {'key': 'Household Goods Consumption MoM', 'suffix': '%'},
                {'key': 'INSEE Consumer Confidence Indicator', 'suffix': ''},
                {'key': 'Real Wage Growth YoY (SMB)', 'suffix': '%'},
                {'key': 'New Car Registrations YoY', 'suffix': '%'},
            ]
        },
        {
            'title': 'Inflation, Sovereign Risk & Monetary Conditions',
            'icon': '🔥',
            'badge': 'Inverted: High Prints Increase ECB Tightening Pressure',
            'badge_color': '#F44336',
            'badge_bg': 'rgba(244, 67, 54, 0.12)',
            'badge_border': 'rgba(244, 67, 54, 0.25)',
            'metrics': [
                {'key': 'French HICP YoY', 'suffix': '%'},
                {'key': 'Core CPI YoY', 'suffix': '%'},
                {'key': 'Producer Price Index YoY', 'suffix': '%'},
                {'key': '2Y OAT Yield (30d SMA)', 'suffix': '%'},
            ]
        },
        {
            'title': 'Labor Market & Employment Stability',
            'icon': '💼',
            'badge': 'INSEE BIT, France Travail & Banque de France',
            'badge_color': '#2962FF',
            'badge_bg': 'rgba(41, 98, 255, 0.12)',
            'badge_border': 'rgba(41, 98, 255, 0.25)',
            'metrics': [
                {'key': 'ILO Unemployment Rate %', 'suffix': '%'},
                {'key': 'France Travail Jobseekers MoM', 'suffix': 'k'},
                {'key': 'Non-Farm Employment QoQ', 'suffix': '%'},
                {'key': 'Hiring Difficulties Index', 'suffix': '%'},
            ]
        }
    ],
    'UK': [
        {
            'title': 'Economic Growth & Industrial Output',
            'icon': '📈',
            'badge': 'ONS & S&P Global CIPS',
            'badge_color': '#2962FF',
            'badge_bg': 'rgba(41, 98, 255, 0.12)',
            'badge_border': 'rgba(41, 98, 255, 0.25)',
            'metrics': [
                {'key': 'UK GDP Growth QoQ', 'suffix': '%'},
                {'key': 'UK Composite PMI', 'suffix': ''},
                {'key': 'Industrial & Manufacturing Production MoM', 'suffix': '%'},
                {'key': 'CBI Business Optimism', 'suffix': '%'},
            ]
        },
        {
            'title': 'Consumer Strength & Retail Volumes',
            'icon': '🛒',
            'badge': 'ONS Retail & GfK Consumer Sentiment',
            'badge_color': '#2962FF',
            'badge_bg': 'rgba(41, 98, 255, 0.12)',
            'badge_border': 'rgba(41, 98, 255, 0.25)',
            'metrics': [
                {'key': 'Retail Sales Volumes MoM (Ex-Fuel)', 'suffix': '%'},
                {'key': 'GfK UK Consumer Confidence', 'suffix': ''},
                {'key': 'Real Regular Earnings YoY', 'suffix': '%'},
                {'key': 'SMMT New Car Registrations YoY', 'suffix': '%'},
            ]
        },
        {
            'title': 'Inflation & Sovereign Yield Pressures',
            'icon': '🔥',
            'badge': 'Inverted: Inflation Threat Triggers BoE Hawkish Stance',
            'badge_color': '#F44336',
            'badge_bg': 'rgba(244, 67, 54, 0.12)',
            'badge_border': 'rgba(244, 67, 54, 0.25)',
            'metrics': [
                {'key': 'UK Headline CPI YoY', 'suffix': '%'},
                {'key': 'UK Core CPI YoY', 'suffix': '%'},
                {'key': 'PPI Output YoY', 'suffix': '%'},
                {'key': '2Y Gilt Yield (30d SMA)', 'suffix': '%'},
            ]
        },
        {
            'title': 'Labor Market & Wage Dynamics',
            'icon': '💼',
            'badge': 'ONS Labor Force & Job Openings Trajectory',
            'badge_color': '#2962FF',
            'badge_bg': 'rgba(41, 98, 255, 0.12)',
            'badge_border': 'rgba(41, 98, 255, 0.25)',
            'metrics': [
                {'key': 'UK Unemployment Rate (3M %)', 'suffix': '%'},
                {'key': 'Claimant Count Change MoM', 'suffix': 'k'},
                {'key': 'Employment Change 3M/3M', 'suffix': 'k'},
                {'key': 'ONS Total Job Vacancies', 'suffix': 'k'},
            ]
        }
    ]
}

# ---------------------------------------------------------
# Google Sheet Sync Helper
# ---------------------------------------------------------
def extract_sheet_id(url: str):
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    if len(url.strip()) >= 20 and not '/' in url.strip():
        return url.strip()
    return None

@st.cache_data(ttl=60)
def fetch_google_sheet(sheet_url: str):
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        return None, "Invalid Google Sheet URL or ID"
    
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        resp = requests.get(export_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text))
            # Find columns
            cols = {c.lower(): c for c in df.columns}
            metric_col = next((cols[c] for c in cols if 'metric' in c or 'name' in c), None)
            val_col = next((cols[c] for c in cols if 'forecast' in c or 'consensus' in c), None)
            country_col = next((cols[c] for c in cols if 'country' in c or 'asset' in c), None)
            
            if not metric_col or not val_col:
                return None, "Could not locate 'Metric Name' or 'Consensus Forecast' columns."
            
            parsed_data = {'Germany': {}, 'France': {}, 'UK': {}}
            for _, row in df.iterrows():
                m_name = str(row[metric_col]).strip()
                v_raw = str(row[val_col]).replace('%', '').replace(',', '').strip()
                try:
                    v_num = float(v_raw)
                    c_name = str(row[country_col]).strip() if country_col else 'Germany'
                    if 'france' in c_name.lower() or 'cac' in c_name.lower():
                        norm_c = 'France'
                    elif 'uk' in c_name.lower() or 'ftse' in c_name.lower():
                        norm_c = 'UK'
                    else:
                        norm_c = 'Germany'
                    parsed_data[norm_c][m_name] = v_num
                except:
                    continue
            
            total_count = sum(len(v) for v in parsed_data.values())
            return parsed_data, f"Synced {total_count} indicators successfully."
        else:
            return None, f"HTTP Error {resp.status_code}. Ensure 'Anyone with the link can view' is active."
    except Exception as e:
        return None, str(e)

# ---------------------------------------------------------
# Sidebar UI
# ---------------------------------------------------------
st.sidebar.title("🇪🇺 Quant Brain Settings")

selected_asset_label = st.sidebar.selectbox("Choose European Asset:", list(EU_ASSET_MAPPING.keys()))
asset_info = EU_ASSET_MAPPING[selected_asset_label]
country = asset_info['country']

history_prints = st.sidebar.slider("Historical Range (Prints):", min_value=3, max_value=8, value=6)
active_model = st.sidebar.radio("Scoring Model Engine:", ["Model 1: Consensus Surprises", "Model 2: Trend Momentum"])

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Google Sheets Forecast Sync")
sheet_input = st.sidebar.text_input("Google Sheet URL or ID:", placeholder="https://docs.google.com/spreadsheets/d/...")

forecasts_dict = BASELINE_FORECASTS[country].copy()
synced_note = "Using built-in baseline consensus forecasts."

if sheet_input:
    custom_data, msg = fetch_google_sheet(sheet_input)
    if custom_data and country in custom_data:
        forecasts_dict.update(custom_data[country])
        st.sidebar.success(f"🟢 Connected to Google Sheets ({len(custom_data[country])} metrics active)")
        synced_note = f"🟢 Connected to Google Sheets ({msg})"
    else:
        st.sidebar.error(f"❌ {msg}")
else:
    st.sidebar.info("⚪ Using Default Baseline Forecasts")

# Download template button
template_file = "macro_forecasts_template.csv"
if os.path.exists(template_file):
    with open(template_file, "rb") as f:
        st.sidebar.download_button("📥 Download 48-Metric Template CSV", f, file_name="macro_forecasts_template.csv", mime="text/csv")

# ---------------------------------------------------------
# Compute Quantitative Macro Scores
# ---------------------------------------------------------
country_metrics = DATASETS[country]
macro_scores = []
table_rows = []

for m_key, hist_vals in country_metrics.items():
    actual = hist_vals[-1]
    forecast = forecasts_dict.get(m_key, actual)
    diff = round(actual - forecast, 2)
    is_inverted = m_key in INVERTED_METRICS
    
    # Model 1: Surprise normalized
    if "Model 1" in active_model:
        spread = diff if not is_inverted else -diff
        # Normalized score per metric
        score = np.clip(spread * 15.0, -100, 100)
    else:
        # Model 2: Momentum (actual vs 3-print mean)
        mean_3 = np.mean(hist_vals[-3:])
        mom = actual - mean_3
        spread = mom if not is_inverted else -mom
        score = np.clip(spread * 20.0, -100, 100)
        
    macro_scores.append(score)
    table_rows.append({
        'Indicator': m_key,
        'Actual Print': actual,
        'Consensus Forecast': forecast,
        'Surprise Delta': diff,
        'Inverted': 'Yes' if is_inverted else 'No',
        'Model Contribution': round(score, 1)
    })

avg_macro_score = round(float(np.mean(macro_scores)), 1)

# Technical & Sentiment Baseline
tech_score = 15.0
cot_score = 12.0
total_master_score = round((avg_macro_score * 0.45) + (tech_score * 0.35) + (cot_score * 0.20), 1)

if total_master_score >= 40:
    bias = "STRONG BULLISH"
    bias_class = "badge-bullish"
elif total_master_score >= 15:
    bias = "BULLISH"
    bias_class = "badge-bullish"
elif total_master_score <= -40:
    bias = "STRONG BEARISH"
    bias_class = "badge-bearish"
elif total_master_score <= -15:
    bias = "BEARISH"
    bias_class = "badge-bearish"
else:
    bias = "NEUTRAL"
    bias_class = "badge-neutral"

# ---------------------------------------------------------
# Main Dashboard UI
# ---------------------------------------------------------
st.title(f"European Macro Analyzer {asset_info['flag']}")
st.caption("Institutional quantitative macro edge, MiFID II positioning, and consensus surprise models.")

# Master Score KPI Banner
col_score, col_bias, col_macro, col_tech, col_cot = st.columns(5)
with col_score:
    st.metric("Master Score", f"{total_master_score} / 100")
with col_bias:
    st.markdown(f"**Master Bias**<br><span class='{bias_class}'>{bias}</span>", unsafe_allow_html=True)
with col_macro:
    st.metric("Macro Score (45%)", f"{avg_macro_score}")
with col_tech:
    st.metric("Technicals (35%)", f"{tech_score}")
with col_cot:
    st.metric("MiFID II / COT (20%)", f"{cot_score}")

st.info(synced_note)

# ---------------------------------------------------------
# COT Data Loader Helper
# ---------------------------------------------------------
def load_cot_dataframe(cot_ticker: str):
    """
    Robustly loads and parses eu_cot_data.csv regardless of column naming conventions
    (Date/date, Asset/asset, Investment_Funds_Long/long, Investment_Funds_Short/short)
    """
    possible_paths = [
        "eu_cot_data.csv",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "eu_cot_data.csv"),
        os.path.join("streamlit", "eu_cot_data.csv")
    ]
    cot_file = next((p for p in possible_paths if os.path.exists(p)), None)
    if not cot_file:
        return None
        
    try:
        df = pd.read_csv(cot_file)
        # Lowercase and clean column names
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Match columns flexibly
        asset_col = next((c for c in df.columns if 'asset' in c or 'ticker' in c), None)
        date_col = next((c for c in df.columns if 'date' in c or 'time' in c), None)
        long_col = next((c for c in df.columns if 'long' in c), None)
        short_col = next((c for c in df.columns if 'short' in c), None)
        
        if not (asset_col and long_col and short_col):
            return None
            
        q = cot_ticker.upper().strip()
        mask = df[asset_col].astype(str).str.upper().apply(lambda x: q in x or x in q)
        filtered = df[mask].copy()
        if filtered.empty:
            return None
            
        clean_df = pd.DataFrame()
        clean_df['date'] = filtered[date_col] if date_col else [f"Week {i+1}" for i in range(len(filtered))]
        clean_df['long'] = pd.to_numeric(filtered[long_col], errors='coerce').fillna(0)
        clean_df['short'] = pd.to_numeric(filtered[short_col], errors='coerce').fillna(0)
        return clean_df.tail(24)
    except Exception:
        return None

# ---------------------------------------------------------
# Main Tabs
# ---------------------------------------------------------
tab_macro, tab_cot, tab_charts, tab_docs = st.tabs([
    "📊 Macro Economic Model", 
    "🎯 MiFID II / COT Positioning", 
    "📈 Historical Time-Series", 
    "ℹ️ Setup & Documentation"
])

with tab_macro:
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.subheader(f"{country} Macroeconomic Indicators ({active_model.split(':')[0]})")
    with header_col2:
        view_mode = st.radio("Display Mode:", ["Cards (Executive Grid)", "Table View"], horizontal=True, label_visibility="collapsed")

    if view_mode == "Cards (Executive Grid)":
        categories = METRIC_CATEGORIES.get(country, [])
        for cat in categories:
            # Render category header bar
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 24px; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">{cat['icon']}</span>
                    <span style="font-size: 15px; font-weight: 700; color: #FFFFFF; letter-spacing: -0.2px;">{cat['title']}</span>
                </div>
                <span style="font-size: 11px; padding: 3px 10px; border-radius: 4px; background: {cat['badge_bg']}; color: {cat['badge_color']}; border: 1px solid {cat['badge_border']}; font-weight: 600;">
                    {cat['badge']}
                </span>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(4)
            for idx, m in enumerate(cat['metrics']):
                m_key = m['key']
                suffix = m.get('suffix', '')
                hist_vals = country_metrics.get(m_key, [0.0])
                actual = hist_vals[-1]
                forecast = forecasts_dict.get(m_key, actual)
                diff = round(actual - forecast, 2)
                is_inverted = m_key in INVERTED_METRICS

                # Equity market impact:
                spread = diff if not is_inverted else -diff
                if spread > 0.001:
                    bias_label = "Bullish"
                    val_color = "#2979FF"
                    pill_bg = "rgba(41, 121, 255, 0.18)"
                    pill_color = "#2979FF"
                    pill_border = "rgba(41, 121, 255, 0.35)"
                elif spread < -0.001:
                    bias_label = "Bearish"
                    val_color = "#F44336"
                    pill_bg = "rgba(244, 67, 54, 0.18)"
                    pill_color = "#F44336"
                    pill_border = "rgba(244, 67, 54, 0.35)"
                else:
                    bias_label = "Neutral"
                    val_color = "#A0A0A0"
                    pill_bg = "rgba(255, 255, 255, 0.08)"
                    pill_color = "#A0A0A0"
                    pill_border = "rgba(255, 255, 255, 0.15)"

                # Format strings cleanly
                actual_str = f"{actual}{suffix}"
                est_str = f"{forecast}{suffix}"
                diff_str = f"+{diff}{suffix}" if diff > 0 else f"{diff}{suffix}"

                card_html = f"""
                <div style="
                    background: #141721;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 10px;
                    padding: 14px 16px;
                    min-height: 118px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
                    margin-bottom: 8px;
                ">
                    <div style="font-size: 12.5px; color: #9E9E9E; font-weight: 500; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{m_key}">
                        {m_key}
                    </div>
                    <div style="font-size: 26px; font-weight: 800; color: {val_color}; line-height: 1.2; margin-bottom: 10px;">
                        {actual_str}
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; font-size: 11px; flex-wrap: wrap;">
                        <span style="background: {pill_bg}; color: {pill_color}; border: 1px solid {pill_border}; padding: 2px 7px; border-radius: 4px; font-weight: 700; font-size: 10.5px;">
                            {bias_label}
                        </span>
                        <span style="color: #757575;">
                            Est: {est_str} | Surprise: <strong style="color: {val_color};">{diff_str}</strong>
                        </span>
                    </div>
                </div>
                """
                with cols[idx]:
                    st.markdown(card_html, unsafe_allow_html=True)
    else:
        df_metrics = pd.DataFrame(table_rows)
        st.dataframe(df_metrics, use_container_width=True, hide_index=True)

with tab_cot:
    st.subheader(f"Institutional COT Positioning — {asset_info['cot']}")
    asset_cot = load_cot_dataframe(asset_info['cot'])
    
    if asset_cot is not None and not asset_cot.empty:
        latest = asset_cot.iloc[-1]
        tot = latest['long'] + latest['short']
        long_pct = round((latest['long'] / tot) * 100, 1) if tot > 0 else 50.0
        short_pct = round((latest['short'] / tot) * 100, 1) if tot > 0 else 50.0
        
        c1, c2 = st.columns([1, 2])
        with c1:
            fig_donut = go.Figure(data=[go.Pie(
                labels=['Commercial Long %', 'Commercial Short %'],
                values=[long_pct, short_pct],
                hole=.6,
                marker_colors=['#00c853', '#f44336']
            )])
            fig_donut.update_layout(title="Latest Positioning Breakdown", template="plotly_dark", height=280)
            st.plotly_chart(fig_donut, use_container_width=True)
        with c2:
            asset_cot['long_pct'] = (asset_cot['long'] / (asset_cot['long'] + asset_cot['short'])) * 100
            fig_line = px.line(asset_cot, x='date', y='long_pct', title="Commercial Long % Trend (24 Weeks)", template="plotly_dark")
            fig_line.update_traces(line_color="#2962ff", line_width=2.5)
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info(f"Showing institutional baseline positioning estimate for {asset_info['cot']}.")
        c1, c2 = st.columns([1, 2])
        with c1:
            fig_donut = go.Figure(data=[go.Pie(
                labels=['Commercial Long %', 'Commercial Short %'],
                values=[58.0, 42.0],
                hole=.6,
                marker_colors=['#00c853', '#f44336']
            )])
            fig_donut.update_layout(title="Positioning Breakdown", template="plotly_dark", height=280)
            st.plotly_chart(fig_donut, use_container_width=True)
        with c2:
            sample_weeks = [f"2026-0{i+1}-15" for i in range(6)]
            sample_df = pd.DataFrame({'date': sample_weeks, 'long_pct': [54.2, 55.0, 56.1, 57.4, 56.8, 58.0]})
            fig_line = px.line(sample_df, x='date', y='long_pct', title="Institutional Long % Trend (Recent Weeks)", template="plotly_dark")
            fig_line.update_traces(line_color="#2962ff", line_width=2.5)
            st.plotly_chart(fig_line, use_container_width=True)

with tab_charts:
    st.subheader(f"{country} Multi-Print Macro Trajectory")
    selected_chart_metric = st.selectbox("Select Indicator to Chart:", list(country_metrics.keys()))
    vals = country_metrics[selected_chart_metric][-history_prints:]
    
    dates = pd.date_range(end=datetime.today(), periods=history_prints, freq='ME').strftime('%b %Y')
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(x=list(dates), y=vals, mode='lines+markers', name='Actual History', line=dict(color='#00e5ff', width=3)))
    fig_hist.add_hline(y=forecasts_dict.get(selected_chart_metric, vals[-1]), line_dash="dash", line_color="#ffea00", annotation_text="Active Consensus Forecast")
    fig_hist.update_layout(template="plotly_dark", title=f"{selected_chart_metric} — Last {history_prints} Prints", height=400)
    st.plotly_chart(fig_hist, use_container_width=True)

with tab_docs:
    st.markdown("""
    ### How to Deploy this Streamlit app to Streamlit Community Cloud:
    1. Create a new repository on your GitHub account (e.g., `european-macro-analyzer-streamlit`).
    2. Upload the files inside this `streamlit/` folder (`app.py`, `requirements.txt`, `eu_cot_data.csv`, `macro_forecasts_template.csv`).
    3. Visit **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
    4. Click **New app**, select your repository, set the main file path to `app.py`, and click **Deploy**.
    5. Your app will be live with a permanent public Streamlit URL accessible from any mobile or desktop browser!
    """)
