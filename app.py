"""
app.py
──────
Environmental Intelligence Dashboard — Streamlit entry point.

Run with:
    streamlit run app.py
"""

import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from api.weather_api import WeatherAPI, WeatherAPIError
from database.storage import WeatherStorage
from services.analytics import WeatherAnalytics
from visualizations.charts import WeatherCharts
from utils.helpers import get_weather_emoji, get_wind_direction

load_dotenv()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Environmental Intelligence Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ─── KPI Card ─────────────────────────────────────── */
.kpi-card {
    background: linear-gradient(145deg, rgba(30,41,59,0.85), rgba(15,23,42,0.9));
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    backdrop-filter: blur(8px);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.45); }
.kpi-label  { font-size: 0.7rem; font-weight: 600; letter-spacing: 1.2px;
              color: rgba(255,255,255,0.4); text-transform: uppercase; margin-bottom: 6px; }
.kpi-value  { font-size: 1.9rem; font-weight: 700; color: #F8FAFC; line-height: 1; }
.kpi-unit   { font-size: 0.8rem; color: rgba(255,255,255,0.35); margin-top: 3px; }

/* ─── Insight badge ────────────────────────────────── */
.insight {
    background: rgba(59,130,246,0.10);
    border-left: 3px solid #3B82F6;
    border-radius: 6px;
    padding: 0.45rem 0.8rem;
    margin: 0.3rem 0;
    font-size: 0.85rem;
    color: #E2E8F0;
}

/* ─── Section header ───────────────────────────────── */
.section-hdr {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.35);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding-bottom: 6px;
    margin-bottom: 14px;
}

/* ─── City header ──────────────────────────────────── */
.city-title { font-size: 2.4rem; font-weight: 700; line-height: 1; margin: 0; }
.city-sub   { font-size: 0.9rem; color: rgba(255,255,255,0.45); margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


# ── Service initialisation (cached for the session) ───────────────────────────
@st.cache_resource
def init_services():
    api       = WeatherAPI()
    db        = WeatherStorage("data/weather.db")
    analytics = WeatherAnalytics()
    charts    = WeatherCharts()
    return api, db, analytics, charts

try:
    api, db, analytics, charts = init_services()
except WeatherAPIError as exc:
    st.error(f"⚠️ Cannot start dashboard: {exc}")
    st.info("Add your `OPENWEATHER_API_KEY` to a `.env` file and restart.")
    st.stop()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌍 EnvIntel Dashboard")
    st.caption("Real-time Environmental Analytics")
    st.markdown("---")

    st.markdown("### 📍 Primary City")
    primary_city = st.text_input("City", value="Amsterdam", placeholder="e.g. Tokyo")

    st.markdown("### 🏙️ Comparison Cities")
    compare_raw  = st.text_area("One city per line", value="London\nParis\nNew York\nTokyo", height=110)
    compare_cities = [c.strip() for c in compare_raw.strip().splitlines() if c.strip()]

    st.markdown("### ⚙️ Settings")
    history_days  = st.slider("History window (days)",    1, 30,  7)
    forecast_hrs  = st.slider("ML forecast horizon (h)", 6, 48, 24, step=6)
    unit          = st.radio("Temperature unit", ["°C", "°F"], horizontal=True)

    st.markdown("---")
    if st.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption(f"Last refresh: {datetime.now():%H:%M:%S}")
    st.caption("Data: OpenWeatherMap · Storage: SQLite")


# ── Data fetching (cached 5 min) ───────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_current(city: str) -> dict:
    raw    = api.get_current_weather(city)
    parsed = api.parse_current_weather(raw)
    db.save_weather(parsed)
    return parsed

@st.cache_data(ttl=300)
def load_forecast(city: str) -> list:
    raw = api.get_forecast(city)
    return api.parse_forecast(raw)

@st.cache_data(ttl=300)
def load_comparison(cities: tuple) -> list:
    results = []
    for city in cities:
        try:
            raw    = api.get_current_weather(city)
            parsed = api.parse_current_weather(raw)
            results.append(parsed)
        except WeatherAPIError:
            pass
    return results

def to_display_temp(c: float) -> str:
    if unit == "°F":
        return f"{c * 9/5 + 32:.1f}°F"
    return f"{c:.1f}°C"


# ── Fetch primary city data ───────────────────────────────────────────────────
try:
    current = load_current(primary_city)
except WeatherAPIError as exc:
    st.error(f"❌ {exc}")
    st.stop()


# ═══════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════
emoji = get_weather_emoji(current.get("weather_main", ""))
col_h, col_temp = st.columns([3, 1])
with col_h:
    st.markdown(
        f"<p class='city-title'>{emoji} {current['city']}, {current['country']}</p>"
        f"<p class='city-sub'>"
        f"{current['timestamp']:%A %d %B %Y · %H:%M} &nbsp;·&nbsp; "
        f"{current.get('weather_desc','').title()}"
        f"</p>",
        unsafe_allow_html=True,
    )
with col_temp:
    st.metric(
        "Temperature",
        to_display_temp(current["temperature"]),
        delta=f"Feels {to_display_temp(current['feels_like'])}",
    )

st.markdown("---")


# ═══════════════════════════════════════════════════════════════
#  KPI CARDS
# ═══════════════════════════════════════════════════════════════
def kpi(label: str, value: str, unit: str = "") -> str:
    return (
        f"<div class='kpi-card'>"
        f"  <div class='kpi-label'>{label}</div>"
        f"  <div class='kpi-value'>{value}</div>"
        f"  <div class='kpi-unit'>{unit}</div>"
        f"</div>"
    )

kpis = [
    ("🌡️ Temp",        to_display_temp(current["temperature"]),                ""),
    ("💧 Humidity",    str(current["humidity"]),                               "%"),
    ("🌬️ Wind",        f"{current['wind_speed']:.1f}",                         "m/s"),
    ("📊 Pressure",    str(current["pressure"]),                               "hPa"),
    ("👁️ Visibility",  f"{current['visibility']:.1f}",                         "km"),
    ("☁️ Cloudiness",  str(current["cloudiness"]),                             "%"),
]
cols = st.columns(6)
for col, (lbl, val, u) in zip(cols, kpis):
    with col:
        st.markdown(kpi(lbl, val, u), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════════
tab_temp, tab_compare, tab_analytics, tab_forecast, tab_history = st.tabs([
    "📈 Temperature",
    "🏙️ City Comparison",
    "📊 Analytics",
    "🔮 Forecast",
    "💾 History",
])


# ── Tab 1: Temperature ────────────────────────────────────────────────────────
with tab_temp:
    history_df = db.get_history(primary_city, history_days)
    pred_df    = analytics.forecast_temperature(history_df, forecast_hrs) if not history_df.empty else None

    c1, c2 = st.columns([2, 1])
    with c1:
        st.plotly_chart(
            charts.temperature_trend_chart(history_df, pred_df),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(charts.humidity_gauge(current["humidity"]),  use_container_width=True)
        st.plotly_chart(charts.pressure_gauge(current["pressure"]), use_container_width=True)

    i1, i2, i3 = st.columns(3)
    i1.info(f"🌅 Sunrise  {current['sunrise']:%H:%M}")
    i2.info(f"🌇 Sunset   {current['sunset']:%H:%M}")
    i3.info(f"🌬️ Wind dir  {get_wind_direction(current.get('wind_deg', 0))} "
            f"({current.get('wind_deg', 0):.0f}°)")


# ── Tab 2: City Comparison ────────────────────────────────────────────────────
with tab_compare:
    compare_data = load_comparison(tuple(compare_cities))
    if compare_data:
        st.plotly_chart(charts.multi_city_comparison(compare_data), use_container_width=True)

        df_tbl = pd.DataFrame([{
            "City":        d["city"],
            "Country":     d["country"],
            "Temp (°C)":   round(d["temperature"], 1),
            "Humidity (%)": d["humidity"],
            "Wind (m/s)":  round(d["wind_speed"], 1),
            "Pressure":    d["pressure"],
            "Condition":   d["weather_desc"].title(),
        } for d in compare_data])
        st.dataframe(df_tbl, use_container_width=True, hide_index=True)
    else:
        st.warning("Could not load comparison data. Check the city names in the sidebar.")


# ── Tab 3: Analytics ──────────────────────────────────────────────────────────
with tab_analytics:
    history_df = db.get_history(primary_city, history_days)

    col_ins, col_corr = st.columns(2)

    with col_ins:
        st.markdown("<div class='section-hdr'>💡 AI Insights</div>", unsafe_allow_html=True)
        for insight in analytics.get_insights(current, history_df):
            st.markdown(f"<div class='insight'>{insight}</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-hdr'>📊 Period Statistics</div>", unsafe_allow_html=True)
        stats = db.get_stats(primary_city, history_days)
        if stats:
            s1, s2 = st.columns(2)
            s1.metric("Avg Temp",     to_display_temp(stats["avg_temp"]))
            s2.metric("Max Temp",     to_display_temp(stats["max_temp"]))
            s1.metric("Min Temp",     to_display_temp(stats["min_temp"]))
            s2.metric("Avg Humidity", f"{stats['avg_humidity']}%")
            s1.metric("Avg Wind",     f"{stats['avg_wind']} m/s")
            s2.metric("Records",      stats["record_count"])
        else:
            st.info("No historical data yet — use the dashboard regularly to build it up.")

    with col_corr:
        if not history_df.empty:
            corr = analytics.correlation_matrix(history_df)
            st.plotly_chart(charts.correlation_heatmap(corr), use_container_width=True)
        else:
            st.info("Correlation analysis requires stored history.")

    if not history_df.empty:
        st.plotly_chart(charts.temperature_heatmap(history_df), use_container_width=True)

        # Anomaly detection
        st.markdown("<div class='section-hdr'>🔍 Anomaly Detection</div>", unsafe_allow_html=True)
        anomaly_df = analytics.detect_anomalies(history_df)
        found      = anomaly_df[anomaly_df["is_anomaly"] == True]
        if not found.empty:
            st.warning(f"⚠️ {len(found)} anomalous reading(s) detected in the last {history_days} days.")
            cols_show = [c for c in ["timestamp", "temperature", "humidity", "pressure", "wind_speed"]
                         if c in found.columns]
            st.dataframe(found[cols_show].head(10), use_container_width=True, hide_index=True)
        else:
            st.success("✅ No anomalies detected in the selected window.")


# ── Tab 4: Forecast ────────────────────────────────────────────────────────────
with tab_forecast:
    forecast_records = load_forecast(primary_city)
    if forecast_records:
        fc_df = pd.DataFrame(forecast_records)

        st.plotly_chart(charts.forecast_area_chart(fc_df), use_container_width=True)

        daily = analytics.daily_summary(fc_df)
        if not daily.empty:
            st.plotly_chart(charts.daily_summary_chart(daily), use_container_width=True)

            st.markdown("<div class='section-hdr'>📋 Daily Breakdown</div>", unsafe_allow_html=True)
            st.dataframe(
                daily.rename(columns={
                    "date": "Date", "avg_temp": "Avg °C", "max_temp": "Max °C",
                    "min_temp": "Min °C", "avg_humidity": "Humidity %",
                    "avg_wind": "Wind m/s", "avg_pressure": "Pressure hPa",
                }),
                use_container_width=True, hide_index=True,
            )
    else:
        st.info("Forecast data unavailable.")


# ── Tab 5: History ────────────────────────────────────────────────────────────
with tab_history:
    history_df = db.get_history(primary_city, history_days)

    hdr, export_col = st.columns([3, 1])
    with hdr:
        st.markdown(
            f"<div class='section-hdr'>"
            f"Records for {primary_city} — last {history_days} days"
            f"</div>",
            unsafe_allow_html=True,
        )
    with export_col:
        if not history_df.empty:
            csv = history_df.to_csv(index=False)
            st.download_button(
                "⬇️ Export CSV",
                data=csv,
                file_name=f"{primary_city}_weather_{datetime.now().date()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    if not history_df.empty:
        st.plotly_chart(charts.wind_rose(history_df), use_container_width=True)

        show_cols = [c for c in
                     ["timestamp", "temperature", "feels_like", "humidity",
                      "pressure", "wind_speed", "wind_deg", "cloudiness",
                      "weather_desc"]
                     if c in history_df.columns]
        st.dataframe(
            history_df[show_cols].sort_values("timestamp", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            f"No history stored for **{primary_city}** yet. "
            "Every time you open the dashboard a new record is saved automatically."
        )
