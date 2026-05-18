"""
database/storage.py
───────────────────
SQLite persistence layer using SQLAlchemy ORM.

Responsibilities
----------------
• Save parsed weather dicts as WeatherRecord rows
• Query history for a city across N days
• Return aggregated statistics
• Export data to CSV
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import (
    Column, DateTime, Float, Integer, String,
    create_engine, text,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from utils.helpers import get_logger

logger = get_logger(__name__)


# ── ORM model ────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class WeatherRecord(Base):
    """One weather observation for one city at one point in time."""
    __tablename__ = "weather_records"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    city        = Column(String,  nullable=False, index=True)
    country     = Column(String)
    timestamp   = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float)
    feels_like  = Column(Float)
    temp_min    = Column(Float)
    temp_max    = Column(Float)
    humidity    = Column(Float)
    pressure    = Column(Float)
    wind_speed  = Column(Float)
    wind_deg    = Column(Float)
    cloudiness  = Column(Float)
    visibility  = Column(Float)
    weather_main = Column(String)
    weather_desc = Column(String)


# ── Storage class ─────────────────────────────────────────────────────────────

class WeatherStorage:
    """
    Thin repository over a local SQLite database.

    Parameters
    ----------
    db_path : str
        Path to the SQLite file (created automatically if absent).
    """

    _RECORD_COLUMNS = {c.key for c in WeatherRecord.__table__.columns}

    def __init__(self, db_path: str = "data/weather.db") -> None:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self._Session = sessionmaker(bind=self.engine)
        logger.info("Database ready at %s", db_path)

    # ── Write ──────────────────────────────────────────────────────────────────

    def save_weather(self, parsed: Dict) -> bool:
        """
        Persist a parsed weather dict.  Unknown keys are silently dropped.
        Returns True on success.
        """
        try:
            payload = {k: v for k, v in parsed.items() if k in self._RECORD_COLUMNS}
            with self._Session() as session:
                session.add(WeatherRecord(**payload))
                session.commit()
            logger.info("Saved record — %s @ %s", parsed.get("city"), parsed.get("timestamp"))
            return True
        except Exception as exc:
            logger.error("Save failed: %s", exc)
            return False

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_history(self, city: str, days: int = 7) -> pd.DataFrame:
        """
        Return all records for *city* within the last *days* days
        as a Pandas DataFrame (empty DataFrame if none found).
        """
        cutoff = datetime.now() - timedelta(days=days)
        sql = text("""
            SELECT * FROM weather_records
            WHERE city = :city
              AND timestamp >= :cutoff
            ORDER BY timestamp DESC
        """)
        try:
            with self.engine.connect() as conn:
                return pd.read_sql(sql, conn, params={"city": city, "cutoff": cutoff})
        except Exception as exc:
            logger.error("History query failed: %s", exc)
            return pd.DataFrame()

    def get_all_cities(self) -> List[str]:
        """Return a sorted list of distinct city names in the database."""
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT DISTINCT city FROM weather_records ORDER BY city")
                )
                return [r[0] for r in rows]
        except Exception as exc:
            logger.error("City list query failed: %s", exc)
            return []

    # ── Aggregates ────────────────────────────────────────────────────────────

    def get_stats(self, city: str, days: int = 7) -> Dict:
        """
        Return a summary dict with avg/min/max statistics for *city*.
        Returns an empty dict if there is no data.
        """
        df = self.get_history(city, days)
        if df.empty:
            return {}
        return {
            "avg_temp":     round(df["temperature"].mean(), 1),
            "max_temp":     round(df["temperature"].max(), 1),
            "min_temp":     round(df["temperature"].min(), 1),
            "avg_humidity": round(df["humidity"].mean(), 1),
            "avg_wind":     round(df["wind_speed"].mean(), 1),
            "avg_pressure": round(df["pressure"].mean(), 1),
            "record_count": len(df),
        }

    # ── Export ────────────────────────────────────────────────────────────────

    def export_csv(self, city: str, days: int = 30) -> str:
        """Write history to CSV and return the file path."""
        df = self.get_history(city, days)
        path = f"data/{city.replace(' ', '_')}_weather_export.csv"
        df.to_csv(path, index=False)
        logger.info("Exported %d rows → %s", len(df), path)
        return path
