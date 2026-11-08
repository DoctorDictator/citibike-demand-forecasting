from __future__ import annotations

from pathlib import Path
import pandas as pd

from urbanflow.features.time_features import add_calendar_features, add_lag_features
from urbanflow.data.noaa import load_daily_weather
from urbanflow.data.nyc_events import events_by_date


def build_feature_table(
    station_hourly: pd.DataFrame,
    weather_path: Path | None = None,
    events_path: Path | None = None,
    lags: list[int] | None = None,
    windows: list[int] | None = None,
) -> pd.DataFrame:
    df = add_calendar_features(station_hourly)
    if weather_path and weather_path.exists():
        weather = load_daily_weather(weather_path)
        df = df.merge(weather, on="date", how="left")
    if events_path and events_path.exists():
        events = events_by_date(events_path)
        df = df.merge(events, on="date", how="left")
        for c in ["event_count", "event_types", "event_today"]:
            if c in df.columns:
                df[c] = df[c].fillna(0)
    df = add_lag_features(
        df, target="departures", lags=lags or [1, 2, 3, 24, 48, 168],
        windows=windows or [3, 6, 24, 168]
    )
    return df
