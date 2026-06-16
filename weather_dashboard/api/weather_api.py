"""
api/weather_api.py
──────────────────
OpenWeatherMap API client with caching and error handling.
"""

import os
import time
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from utils.helpers import get_logger, safe_get

load_dotenv()
logger = get_logger(__name__)

BASE_URL = "https://api.openweathermap.org/data/2.5"


# ── Exceptions ────────────────────────────────────────────────────────────────

class WeatherAPIError(Exception):
    """Raised for any problem communicating with OpenWeatherMap."""


# ── Client ────────────────────────────────────────────────────────────────────

class WeatherAPI:

    def __init__(self, cache_ttl: int = 300) -> None:
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        if not self.api_key:
            raise WeatherAPIError(
                "OPENWEATHER_API_KEY is not set. "
                "Add your key to the .env file."
            )
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = cache_ttl
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "WeatherDashboard/1.0"})

    # ── Cache helpers ─────────────────────────────────────────────────────────

    def _cache_valid(self, key: str) -> bool:
        entry = self._cache.get(key)
        return bool(entry and time.time() - entry["ts"] < self._cache_ttl)

    def _from_cache(self, key: str) -> Optional[Any]:
        if self._cache_valid(key):
            logger.debug("Cache hit: %s", key)
            return self._cache[key]["data"]
        return None

    def _to_cache(self, key: str, data: Any) -> None:
        self._cache[key] = {"data": data, "ts": time.time()}

    # ── HTTP helper ───────────────────────────────────────────────────────────

    def _get(self, endpoint: str, params: Dict) -> Dict:
        params = {**params, "appid": self.api_key, "units": "metric"}
        url = f"{BASE_URL}/{endpoint}"
        try:
            resp = self._session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError:
            code = resp.status_code
            if code == 401:
                raise WeatherAPIError("Invalid API key.")
            if code == 404:
                raise WeatherAPIError("City not found.")
            if code == 429:
                raise WeatherAPIError("Rate limit hit. Wait and retry.")
            raise WeatherAPIError(f"HTTP {code}: {resp.text[:120]}")
        except requests.ConnectionError:
            raise WeatherAPIError("No internet connection.")
        except requests.Timeout:
            raise WeatherAPIError("Request timed out.")

    # ── Public API ────────────────────────────────────────────────────────────

    def get_current_weather(self, city: str) -> Dict:
        key = f"cur:{city.lower()}"
        cached = self._from_cache(key)
        if cached:
            return cached
        data = self._get("weather", {"q": city})
        self._to_cache(key, data)
        logger.info("Fetched current weather — %s", city)
        return data

    def get_forecast(self, city: str, days: int = 5) -> Dict:
        key = f"fc:{city.lower()}:{days}"
        cached = self._from_cache(key)
        if cached:
            return cached
        data = self._get("forecast", {"q": city, "cnt": days * 8})
        self._to_cache(key, data)
        logger.info("Fetched %d-day forecast — %s", days, city)
        return data

    def get_multiple_cities(self, cities: List[str]) -> List[Dict]:
        results = []
        for city in cities:
            try:
                results.append(self.get_current_weather(city))
            except WeatherAPIError as exc:
                logger.warning("Skipping %s: %s", city, exc)
        return results

    # ── Parsers ───────────────────────────────────────────────────────────────

    def parse_current_weather(self, raw: Dict) -> Dict:
        return {
            "city":         raw.get("name"),
            "country":      safe_get(raw, "sys", "country"),
            "timestamp":    datetime.fromtimestamp(raw.get("dt", 0)),
            "temperature":  safe_get(raw, "main", "temp"),
            "feels_like":   safe_get(raw, "main", "feels_like"),
            "temp_min":     safe_get(raw, "main", "temp_min"),
            "temp_max":     safe_get(raw, "main", "temp_max"),
            "humidity":     safe_get(raw, "main", "humidity"),
            "pressure":     safe_get(raw, "main", "pressure"),
            "visibility":   raw.get("visibility", 0) / 1000,
            "wind_speed":   safe_get(raw, "wind", "speed"),
            "wind_deg":     safe_get(raw, "wind", "deg", default=0),
            "cloudiness":   safe_get(raw, "clouds", "all"),
            "weather_main": safe_get(raw, "weather", 0, "main"),
            "weather_desc": safe_get(raw, "weather", 0, "description"),
            "sunrise":      datetime.fromtimestamp(safe_get(raw, "sys", "sunrise", default=0)),
            "sunset":       datetime.fromtimestamp(safe_get(raw, "sys", "sunset", default=0)),
        }

    def parse_forecast(self, raw: Dict) -> List[Dict]:
        records = []
        for item in raw.get("list", []):
            records.append({
                "timestamp":    datetime.fromtimestamp(item.get("dt", 0)),
                "temperature":  safe_get(item, "main", "temp"),
                "feels_like":   safe_get(item, "main", "feels_like"),
                "humidity":     safe_get(item, "main", "humidity"),
                "pressure":     safe_get(item, "main", "pressure"),
                "wind_speed":   safe_get(item, "wind", "speed"),
                "cloudiness":   safe_get(item, "clouds", "all"),
                "weather_main": safe_get(item, "weather", 0, "main"),
                "weather_desc": safe_get(item, "weather", 0, "description"),
                "rain_3h":      safe_get(item, "rain", "3h", default=0.0),
            })
        return records