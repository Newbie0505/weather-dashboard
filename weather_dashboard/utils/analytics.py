"""
services/analytics.py
──────────────────────
Analytics, ML forecasting, and anomaly detection.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression

from utils.helpers import get_logger

logger = get_logger(__name__)


class WeatherAnalytics:

    # ── Comfort index ─────────────────────────────────────────────────────────

    @staticmethod
    def heat_index(temp_c: float, humidity: float) -> float:
        T = temp_c * 9 / 5 + 32
        R = humidity
        HI = (
            -42.379
            + 2.04901523 * T
            + 10.14333127 * R
            - 0.22475541 * T * R
            - 0.00683783 * T ** 2
            - 0.05481717 * R ** 2
            + 0.00122874 * T ** 2 * R
            + 0.00085282 * T * R ** 2
            - 0.00000199 * T ** 2 * R ** 2
        )
        return (HI - 32) * 5 / 9

    def comfort_level(self, temp: float, humidity: float) -> str:
        hi = self.heat_index(temp, humidity)
        if hi < 0:   return "❄️ Very Cold"
        if hi < 10:  return "🥶 Cold"
        if hi < 18:  return "😐 Cool"
        if hi < 24:  return "😊 Comfortable"
        if hi < 30:  return "😅 Warm"
        if hi < 38:  return "🥵 Hot"
        return "🔥 Dangerously Hot"

    # ── Trend analysis ────────────────────────────────────────────────────────

    @staticmethod
    def temperature_trend(df: pd.DataFrame, window: int = 6) -> str:
        if len(df) < 3:
            return "➡️ Insufficient data"
        recent = df.sort_values("timestamp").tail(window)["temperature"].values
        slope  = float(np.polyfit(range(len(recent)), recent, 1)[0])
        if slope > 0.3:  return "📈 Rising"
        if slope < -0.3: return "📉 Falling"
        return "➡️ Stable"

    # ── ML forecasting ────────────────────────────────────────────────────────

    def forecast_temperature(
        self,
        df: pd.DataFrame,
        hours_ahead: int = 24,
    ) -> Optional[pd.DataFrame]:
        if len(df) < 5:
            logger.warning("Too few records for forecasting (%d < 5)", len(df))
            return None

        df = df.sort_values("timestamp").copy()
        df["idx"] = range(len(df))

        model = LinearRegression()
        model.fit(df[["idx"]], df["temperature"])

        steps       = max(1, hours_ahead // 3)
        future_idxs = np.arange(len(df), len(df) + steps).reshape(-1, 1)
        preds       = model.predict(future_idxs)

        last_ts   = df["timestamp"].iloc[-1]
        future_ts = pd.date_range(last_ts, periods=steps, freq="3h")[0:steps]

        return pd.DataFrame({"timestamp": future_ts, "predicted_temp": preds})

    # ── Anomaly detection ─────────────────────────────────────────────────────

    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < 10:
            return df.assign(is_anomaly=False)

        features  = ["temperature", "humidity", "pressure", "wind_speed"]
        available = [f for f in features if f in df.columns]
        X         = df[available].fillna(df[available].median())

        clf    = IsolationForest(contamination=0.1, random_state=42)
        labels = clf.fit_predict(X)

        result = df.copy()
        result["is_anomaly"] = labels == -1
        n = result["is_anomaly"].sum()
        if n:
            logger.info("Anomaly detection: %d outliers found", n)
        return result

    # ── Aggregations ──────────────────────────────────────────────────────────

    @staticmethod
    def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
        cols      = ["temperature", "humidity", "pressure", "wind_speed", "cloudiness"]
        available = [c for c in cols if c in df.columns]
        return df[available].corr()

    @staticmethod
    def daily_summary(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        out = df.copy()
        out["date"] = pd.to_datetime(out["timestamp"]).dt.date
        return (
            out.groupby("date")
            .agg(
                avg_temp     = ("temperature", "mean"),
                max_temp     = ("temperature", "max"),
                min_temp     = ("temperature", "min"),
                avg_humidity = ("humidity",    "mean"),
                avg_wind     = ("wind_speed",  "mean"),
                avg_pressure = ("pressure",    "mean"),
            )
            .round(1)
            .reset_index()
        )

    # ── Insights ──────────────────────────────────────────────────────────────

    def get_insights(self, current: Dict, history_df: pd.DataFrame) -> List[str]:
        insights: List[str] = []

        temp     = current.get("temperature", 20)
        humidity = current.get("humidity",     50)
        wind     = current.get("wind_speed",   0)
        pressure = current.get("pressure",     1013)

        insights.append(f"Comfort level: {self.comfort_level(temp, humidity)}")

        if humidity > 80:
            insights.append("⚠️ High humidity — expect muggy conditions")
        elif humidity < 30:
            insights.append("💧 Low humidity — stay hydrated")

        if wind > 10:
            insights.append("🌬️ Strong winds — be cautious outdoors")
        elif wind < 1:
            insights.append("🍃 Calm air — minimal wind chill")

        if pressure < 990:
            insights.append("🌩️ Low pressure — stormy weather likely")
        elif pressure > 1025:
            insights.append("🌤️ High pressure — clear skies expected")

        if not history_df.empty:
            trend = self.temperature_trend(history_df)
            insights.append(f"Temperature trend: {trend}")

        return insights