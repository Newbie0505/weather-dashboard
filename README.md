# 🌍 Environmental Intelligence Dashboard

A **production-style** real-time weather analytics platform built with Python,
Streamlit, and OpenWeatherMap.  
Designed as an internship portfolio project demonstrating clean architecture,
API integration, data persistence, ML forecasting, and professional UI design.

---

## ✨ Features

| Category | What's included |
|---|---|
| **Live weather** | Temperature, humidity, pressure, wind, visibility, cloudiness |
| **Multi-city** | Side-by-side comparison of up to 6 cities |
| **Visualizations** | Line charts, gauges, wind rose, heatmap, correlation matrix |
| **ML Forecast** | Linear-regression temperature extrapolation (up to 48 h) |
| **Anomaly detection** | Isolation Forest flags unusual readings |
| **History** | SQLite storage — auto-grows every visit; CSV export |
| **Insights** | Heat-index comfort level, pressure trend, wind advisory |
| **Dark-glass UI** | Custom CSS, DM Sans font, responsive Streamlit layout |

---

## 🗂️ Project Structure

```
weather_dashboard/
├── app.py                   ← Streamlit entry point (dashboard UI)
├── api/
│   └── weather_api.py       ← OpenWeatherMap client + response caching
├── services/
│   └── analytics.py         ← ML forecasting, anomaly detection, insights
├── visualizations/
│   └── charts.py            ← All Plotly figures
├── database/
│   └── storage.py           ← SQLAlchemy ORM + SQLite persistence
├── utils/
│   └── helpers.py           ← Logging, formatting, safe dict access
├── data/                    ← Auto-created: weather.db, CSV exports
├── .env.example             ← Copy to .env and add your API key
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1 — Get a free API key

1. Register at <https://openweathermap.org/api>
2. Copy your key from the **API keys** tab  
   *(new keys take ~2 hours to activate)*

### 2 — Clone and set up the environment

```bash
# Clone or unzip the project
cd weather_dashboard

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3 — Configure your API key

```bash
cp .env.example .env
# Open .env and replace  your_api_key_here  with your real key
```

### 4 — Run the dashboard

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `OPENWEATHER_API_KEY` | Your OpenWeatherMap API key (**required**) |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Interactive web dashboard framework |
| `plotly` | Interactive charts and gauges |
| `pandas` | Data processing and aggregation |
| `sqlalchemy` | ORM and SQLite interface |
| `scikit-learn` | Linear regression forecast + Isolation Forest |
| `requests` | HTTP client for the weather API |
| `python-dotenv` | Load environment variables from `.env` |
| `apscheduler` | (Available for scheduled data ingestion) |

---

## 🎓 Internship Evaluation Checklist

- [x] Clean UI with dark-glass aesthetic
- [x] Modular architecture (api / services / visualizations / database / utils)
- [x] Real-world API integration with error handling and caching
- [x] Professional Plotly visualizations (7+ chart types)
- [x] Code is documented with docstrings
- [x] Environment variables for secrets — no hard-coded keys
- [x] SQLite persistence with SQLAlchemy ORM
- [x] ML forecasting (Linear Regression) + Anomaly Detection (Isolation Forest)
- [x] CSV export
- [x] README with clear setup instructions

---

## 🛠️ Next Steps (Phase 8 – 10)

- [ ] APScheduler: background job that ingests data every 30 min automatically
- [ ] Docker deployment (`Dockerfile` + `docker-compose.yml`)
- [ ] Unit tests with `pytest`
- [ ] Add an air-quality endpoint (OpenWeatherMap `/air_pollution`)
- [ ] Deploy to Streamlit Cloud or AWS Lightsail
