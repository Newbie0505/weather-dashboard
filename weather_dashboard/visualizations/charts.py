"""
visualizations/charts.py
─────────────────────────
All Plotly charts used by the dashboard.
"""

from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ── Design tokens ─────────────────────────────────────────────────────────────

PALETTE = {
    "blue":    "#3B82F6",
    "red":     "#EF4444",
    "green":   "#10B981",
    "amber":   "#F59E0B",
    "purple":  "#8B5CF6",
    "cyan":    "#06B6D4",
    "pink":    "#EC4899",
    "white":   "#F8FAFC",
    "dim":     "rgba(255,255,255,0.35)",
    "grid":    "rgba(255,255,255,0.06)",
    "surface": "rgba(0,0,0,0)",
}

FONT = dict(family="'DM Sans', 'Inter', sans-serif", color=PALETTE["white"])

LAYOUT_BASE = dict(
    paper_bgcolor = PALETTE["surface"],
    plot_bgcolor  = PALETTE["surface"],
    font          = FONT,
    margin        = dict(l=24, r=24, t=52, b=24),
    xaxis         = dict(gridcolor=PALETTE["grid"], zeroline=False,
                         tickfont=dict(color=PALETTE["dim"])),
    yaxis         = dict(gridcolor=PALETTE["grid"], zeroline=False,
                         tickfont=dict(color=PALETTE["dim"])),
    legend        = dict(orientation="h", yanchor="bottom", y=1.02,
                         font=dict(size=11, color=PALETTE["dim"])),
)

BAR_COLORS = [
    PALETTE["blue"], PALETTE["red"], PALETTE["green"],
    PALETTE["amber"], PALETTE["purple"], PALETTE["cyan"],
]


class WeatherCharts:

    # ── Temperature trend ─────────────────────────────────────────────────────

    def temperature_trend_chart(
        self,
        df: pd.DataFrame,
        forecast_df: Optional[pd.DataFrame] = None,
    ) -> go.Figure:
        fig = go.Figure()

        if not df.empty:
            df = df.sort_values("timestamp")

            if "temp_max" in df.columns and "temp_min" in df.columns:
                fig.add_trace(go.Scatter(
                    x=list(df["timestamp"]) + list(df["timestamp"][::-1]),
                    y=list(df["temp_max"])  + list(df["temp_min"][::-1]),
                    fill="toself",
                    fillcolor="rgba(59,130,246,0.12)",
                    line=dict(width=0),
                    hoverinfo="skip",
                    showlegend=False,
                ))

            fig.add_trace(go.Scatter(
                x=df["timestamp"],
                y=df["temperature"],
                name="Temperature",
                mode="lines+markers",
                line=dict(color=PALETTE["blue"], width=2.5),
                marker=dict(size=4, color=PALETTE["blue"]),
            ))

        if forecast_df is not None and not forecast_df.empty:
            fig.add_trace(go.Scatter(
                x=forecast_df["timestamp"],
                y=forecast_df["predicted_temp"],
                name="ML Forecast",
                mode="lines",
                line=dict(color=PALETTE["amber"], width=2, dash="dash"),
            ))

        fig.update_layout(
            **LAYOUT_BASE,
            title="🌡️ Temperature Trend & Forecast",
            yaxis_title="°C",
        )
        return fig

    # ── Multi-city comparison ─────────────────────────────────────────────────

    def multi_city_comparison(self, city_data: List[Dict]) -> go.Figure:
        cities     = [d["city"]        for d in city_data]
        temps      = [d["temperature"] for d in city_data]
        humidities = [d["humidity"]    for d in city_data]
        colors     = (BAR_COLORS * (len(cities) // len(BAR_COLORS) + 1))[:len(cities)]

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Temperature (°C)", "Humidity (%)"),
        )

        fig.add_trace(go.Bar(
            x=cities, y=temps,
            marker_color=colors,
            text=[f"{t:.1f}°C" for t in temps],
            textposition="auto",
            name="Temp",
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            x=cities, y=humidities,
            marker_color=colors,
            text=[f"{h}%" for h in humidities],
            textposition="auto",
            name="Humidity",
        ), row=1, col=2)

        fig.update_layout(**LAYOUT_BASE,
            title="🏙️ Multi-City Comparison",
            showlegend=False,
        )
        return fig

    # ── Gauges ────────────────────────────────────────────────────────────────

    def humidity_gauge(self, humidity: float) -> go.Figure:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=humidity,
            number={"suffix": "%", "font": {"size": 34, "color": PALETTE["white"]}},
            title={"text": "💧 Humidity", "font": {"size": 14, "color": PALETTE["dim"]}},
            gauge={
                "axis":  {"range": [0, 100], "tickcolor": PALETTE["dim"]},
                "bar":   {"color": PALETTE["blue"]},
                "bgcolor": "rgba(255,255,255,0.04)",
                "steps": [
                    {"range": [0,  30], "color": "rgba(239,68,68,0.2)"},
                    {"range": [30, 60], "color": "rgba(16,185,129,0.2)"},
                    {"range": [60, 100], "color": "rgba(59,130,246,0.2)"},
                ],
                "threshold": {
                    "line": {"color": PALETTE["amber"], "width": 3},
                    "thickness": 0.8,
                    "value": 80,
                },
            },
        ))
        fig.update_layout(paper_bgcolor=PALETTE["surface"],
                          font=FONT, height=220,
                          margin=dict(l=20, r=20, t=30, b=10))
        return fig

    def pressure_gauge(self, pressure: float) -> go.Figure:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pressure,
            number={"suffix": " hPa", "font": {"size": 28, "color": PALETTE["white"]}},
            title={"text": "📊 Pressure", "font": {"size": 14, "color": PALETTE["dim"]}},
            gauge={
                "axis":  {"range": [950, 1050], "tickcolor": PALETTE["dim"]},
                "bar":   {"color": PALETTE["purple"]},
                "bgcolor": "rgba(255,255,255,0.04)",
                "steps": [
                    {"range": [950,  990], "color": "rgba(239,68,68,0.2)"},
                    {"range": [990, 1020], "color": "rgba(16,185,129,0.2)"},
                    {"range": [1020, 1050], "color": "rgba(59,130,246,0.2)"},
                ],
            },
        ))
        fig.update_layout(paper_bgcolor=PALETTE["surface"],
                          font=FONT, height=220,
                          margin=dict(l=20, r=20, t=30, b=10))
        return fig

    # ── Wind rose ─────────────────────────────────────────────────────────────

    def wind_rose(self, df: pd.DataFrame) -> go.Figure:
        if df.empty or "wind_deg" not in df.columns:
            return go.Figure().update_layout(**LAYOUT_BASE, title="🌬️ Wind Rose (no data)")

        labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        bins   = [0, 45, 90, 135, 180, 225, 270, 315, 360]
        df     = df.copy()
        df["dir_bin"] = pd.cut(
            df["wind_deg"], bins=bins,
            labels=labels, right=False, include_lowest=True,
        )
        rose = df.groupby("dir_bin", observed=True)["wind_speed"].mean().reindex(labels, fill_value=0)

        fig = go.Figure(go.Barpolar(
            r=rose.values,
            theta=rose.index,
            marker_color=PALETTE["blue"],
            marker_line_color="rgba(255,255,255,0.1)",
            marker_line_width=1,
            opacity=0.85,
        ))
        fig.update_layout(
            **LAYOUT_BASE,
            title="🌬️ Wind Rose",
            polar=dict(
                bgcolor=PALETTE["surface"],
                radialaxis=dict(
                    visible=True,
                    range=[0, max(rose.values) + 2 if rose.values.any() else 10],
                    gridcolor=PALETTE["grid"],
                    tickfont=dict(color=PALETTE["dim"]),
                ),
                angularaxis=dict(
                    gridcolor=PALETTE["grid"],
                    tickfont=dict(color=PALETTE["dim"]),
                ),
            ),
        )
        return fig

    # ── Heatmap ───────────────────────────────────────────────────────────────

    def temperature_heatmap(self, df: pd.DataFrame) -> go.Figure:
        if df.empty:
            return go.Figure().update_layout(**LAYOUT_BASE, title="🔥 Heatmap (no data)")

        df = df.copy()
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        pivot = df.pivot_table(
            values="temperature", index="date", columns="hour", aggfunc="mean"
        )
        fig = px.imshow(
            pivot,
            color_continuous_scale="RdYlBu_r",
            labels=dict(x="Hour", y="Date", color="°C"),
            title="🔥 Temperature Heatmap (Hour × Day)",
        )
        fig.update_layout(**LAYOUT_BASE)
        return fig

    # ── Correlation heatmap ───────────────────────────────────────────────────

    def correlation_heatmap(self, corr: pd.DataFrame) -> go.Figure:
        fig = go.Figure(go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.columns.tolist(),
            colorscale="RdBu",
            zmid=0, zmin=-1, zmax=1,
            text=corr.round(2).values,
            texttemplate="%{text}",
            textfont=dict(size=11),
            colorbar=dict(tickfont=dict(color=PALETTE["dim"])),
        ))
        fig.update_layout(**LAYOUT_BASE, title="📊 Correlation Matrix")
        return fig

    # ── Daily summary ─────────────────────────────────────────────────────────

    def daily_summary_chart(self, daily: pd.DataFrame) -> go.Figure:
        if daily.empty:
            return go.Figure().update_layout(**LAYOUT_BASE, title="📅 Daily Summary (no data)")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(daily["date"]) + list(daily["date"][::-1]),
            y=list(daily["max_temp"]) + list(daily["min_temp"][::-1]),
            fill="toself",
            fillcolor="rgba(59,130,246,0.10)",
            line=dict(width=0),
            name="Range",
            hoverinfo="skip",
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=daily["date"], y=daily["avg_temp"],
            mode="lines+markers",
            name="Avg Temp",
            line=dict(color=PALETTE["blue"], width=2.5),
            marker=dict(size=7),
        ))
        fig.update_layout(**LAYOUT_BASE,
            title="📅 Daily Temperature Summary",
            yaxis_title="°C",
        )
        return fig

    # ── Forecast area chart ───────────────────────────────────────────────────

    def forecast_area_chart(self, forecast_df: pd.DataFrame) -> go.Figure:
        if forecast_df.empty:
            return go.Figure().update_layout(**LAYOUT_BASE, title="🔮 Forecast (no data)")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=forecast_df["timestamp"],
            y=forecast_df["temperature"],
            mode="lines+markers",
            name="Forecast Temp",
            line=dict(color=PALETTE["cyan"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(6,182,212,0.12)",
            marker=dict(size=4),
        ))
        fig.update_layout(**LAYOUT_BASE,
            title="🔮 5-Day Temperature Forecast",
            yaxis_title="°C",
        )
        return fig