# European Macro Analyzer — Streamlit Edition 🇪🇺

This directory contains the complete Python + Streamlit version of the European Macro Analyzer, ready for immediate deployment to **Streamlit Community Cloud** (`share.streamlit.io`).

---

## 📁 Files Included
- `app.py`: The complete Streamlit dashboard script containing Model 1 (Consensus Surprises), Model 2 (Trend Momentum), MiFID II/COT positioning, Technicals, and live Google Sheets synchronization.
- `requirements.txt`: Python package dependencies (`streamlit`, `pandas`, `plotly`, `requests`).
- `eu_cot_data.csv`: Historical European Commitment of Traders (COT) positioning data.
- `macro_forecasts_template.csv`: The complete 48-indicator macro consensus forecast template.

---

## 🚀 How to Deploy to Streamlit Cloud in 3 Steps:

1. **Create a New Repository on GitHub**:
   - Go to [github.com/new](https://github.com/new) and name it (e.g., `european-macro-analyzer-streamlit`).
   - Push or upload the 4 files in this `streamlit/` folder to the root of your new repository.

2. **Connect to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.
   - Click **New app**.

3. **Deploy**:
   - Select your new repository.
   - Set **Main file path** to `app.py`.
   - Click **Deploy**!

Within ~60 seconds, Streamlit Cloud will give you a permanent public URL (e.g. `https://your-name-macro.streamlit.app`) accessible from any phone, tablet, or PC!

---

## 💻 Running Locally (Optional):
```bash
pip install -r requirements.txt
streamlit run app.py
```
