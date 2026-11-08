from __future__ import annotations

from pathlib import Path
import requests
import pandas as pd


def download_daily_weather(
    base_url: str,
    station_id: str,
    start_date: str,
    end_date: str,
    destination: Path,
) -> Path:
    """Download NOAA/NCEI daily summaries for the configured NYC station.

    This starter deliberately uses the documented NCEI Access Data Service and
    a stable Central Park station ID. The downstream pipeline joins daily weather
    onto hourly trips by local date. Hourly weather can be added later without
    changing the trip pipeline.
    """
    params = {
        "dataset": "daily-summaries",
        "stations": station_id,
        "startDate": start_date,
        "endDate": end_date,
        "format": "csv",
        "units": "metric",
        "includeStationName": "true",
        "includeStationLocation": "true",
    }
    r = requests.get(base_url, params=params, timeout=120, headers={"User-Agent": "UrbanFlowAI/0.1"})
    r.raise_for_status()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(r.content)
    return destination


def load_daily_weather(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    if "DATE" not in df.columns:
        raise ValueError("NOAA daily summary CSV must contain DATE")
    df["date"] = pd.to_datetime(df["DATE"], errors="coerce").dt.date
    keep = [c for c in ["date", "TAVG", "TMIN", "TMAX", "PRCP", "SNOW", "AWND"] if c in df.columns]
    out = df[keep].copy()
    rename = {"TAVG": "temp_avg_c", "TMIN": "temp_min_c", "TMAX": "temp_max_c",
              "PRCP": "precip_mm", "SNOW": "snow_mm", "AWND": "wind_avg"}
    return out.rename(columns=rename)
