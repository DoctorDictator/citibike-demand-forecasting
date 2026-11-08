from __future__ import annotations

import numpy as np
import pandas as pd


def add_calendar_features(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    out = df.copy()
    ts = pd.to_datetime(out[timestamp_col])
    out["hour"] = ts.dt.hour
    out["day_of_week"] = ts.dt.dayofweek
    out["month"] = ts.dt.month
    out["is_weekend"] = (ts.dt.dayofweek >= 5).astype(int)
    out["hour_sin"] = np.sin(2 * np.pi * out["hour"] / 24)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"] / 24)
    out["dow_sin"] = np.sin(2 * np.pi * out["day_of_week"] / 7)
    out["dow_cos"] = np.cos(2 * np.pi * out["day_of_week"] / 7)
    out["date"] = ts.dt.date
    return out


def add_lag_features(
    df: pd.DataFrame,
    target: str,
    group_col: str = "station_id",
    timestamp_col: str = "timestamp",
    lags: list[int] | tuple[int, ...] = (1, 24, 168),
    windows: list[int] | tuple[int, ...] = (3, 24, 168),
) -> pd.DataFrame:
    out = df.sort_values([group_col, timestamp_col]).copy()
    grouped = out.groupby(group_col, sort=False)[target]
    for lag in lags:
        out[f"{target}_lag_{lag}"] = grouped.shift(lag)
    for w in windows:
        shifted = grouped.shift(1)
        out[f"{target}_roll_mean_{w}"] = shifted.groupby(out[group_col]).transform(
            lambda s: s.rolling(w, min_periods=max(1, min(3, w))).mean()
        )
        out[f"{target}_roll_std_{w}"] = shifted.groupby(out[group_col]).transform(
            lambda s: s.rolling(w, min_periods=max(2, min(3, w))).std()
        )
    return out
