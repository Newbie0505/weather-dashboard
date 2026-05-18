"""
utils/helpers.py
────────────────
Shared utility functions: logging, formatting, safe data access.
"""

import logging
from datetime import datetime
from typing import Any, Optional


# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)


# ── Data helpers ─────────────────────────────────────────────────────────────

def safe_get(data: Any, *keys, default: Any = None) -> Any:
    """Safely traverse a nested dict/list structure."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        elif isinstance(data, (list, tuple)) and isinstance(key, int):
            try:
                data = data[key]
            except IndexError:
                return default
        else:
            return default
    return data


# ── Unit conversions ─────────────────────────────────────────────────────────

def celsius_to_fahrenheit(c: float) -> float:
    return (c * 9 / 5) + 32

def kelvin_to_celsius(k: float) -> float:
    return k - 273.15

def ms_to_kmh(ms: float) -> float:
    return ms * 3.6


# ── Formatting ───────────────────────────────────────────────────────────────

def format_temperature(temp: float, unit: str = "C") -> str:
    if unit == "F":
        return f"{celsius_to_fahrenheit(temp):.1f}°F"
    return f"{temp:.1f}°C"

def format_wind_speed(speed: float) -> str:
    return f"{speed:.1f} m/s  ({ms_to_kmh(speed):.0f} km/h)"

def unix_to_datetime(unix_ts: int) -> datetime:
    return datetime.fromtimestamp(unix_ts)


# ── Weather helpers ───────────────────────────────────────────────────────────

WIND_DIRECTIONS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]

def get_wind_direction(degrees: float) -> str:
    """Convert wind angle (0–360) to compass label."""
    idx = round(degrees / 22.5) % 16
    return WIND_DIRECTIONS[idx]


EMOJI_MAP = {
    "clear":        "☀️",
    "clouds":       "☁️",
    "rain":         "🌧️",
    "drizzle":      "🌦️",
    "thunderstorm": "⛈️",
    "snow":         "❄️",
    "mist":         "🌫️",
    "fog":          "🌫️",
    "haze":         "🌫️",
    "smoke":        "🌫️",
    "dust":         "🌪️",
    "sand":         "🌪️",
    "tornado":      "🌪️",
}

def get_weather_emoji(condition: str) -> str:
    """Return an emoji for a weather condition string."""
    condition = condition.lower()
    for key, emoji in EMOJI_MAP.items():
        if key in condition:
            return emoji
    return "🌡️"