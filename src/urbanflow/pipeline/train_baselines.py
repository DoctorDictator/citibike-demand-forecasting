from __future__ import annotations

from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


def chronological_split(df: pd.DataFrame, test_fraction: float = 0.2):
    times = sorted(pd.to_datetime(df["timestamp"]).dropna().unique())
    cut = max(1, int(len(times) * (1 - test_fraction)))
    cutoff = times[min(cut, len(times) - 1)]
    return df[pd.to_datetime(df["timestamp"]) < cutoff], df[pd.to_datetime(df["timestamp"]) >= cutoff]


def run(feature_path: Path, model_dir: Path, test_fraction: float = 0.2) -> dict:
    df = pd.read_parquet(feature_path).sort_values("timestamp")
    lag_cols = [c for c in df.columns if c.startswith("departures_lag_") or c.startswith("departures_roll_")]
    extra = [c for c in ["hour_sin", "hour_cos", "dow_sin", "dow_cos", "is_weekend", "temp_avg_c", "precip_mm", "event_today"] if c in df.columns]
    features = lag_cols + extra
    usable = df.dropna(subset=["departures"])
    train, test = chronological_split(usable, test_fraction)
    if train.empty or test.empty:
        raise ValueError("Not enough data after chronological split")
    X_train, X_test = train[features], test[features]
    y_train, y_test = train["departures"], test["departures"]
    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model", HistGradientBoostingRegressor(random_state=42, loss="poisson")),
    ])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test).clip(min=0)
    metrics = {
        "mae": float(mean_absolute_error(y_test, pred)),
        "rmse": float(mean_squared_error(y_test, pred) ** 0.5),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "features": features,
    }
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_dir / "departure_baseline.joblib")
    (model_dir / "departure_baseline_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics
