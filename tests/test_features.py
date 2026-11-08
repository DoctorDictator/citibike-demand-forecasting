import pandas as pd
from urbanflow.features.time_features import add_calendar_features, add_lag_features


def test_calendar_and_lags():
    df = pd.DataFrame({
        "station_id": ["A"] * 30,
        "timestamp": pd.date_range("2026-01-01", periods=30, freq="h"),
        "departures": list(range(30)),
    })
    out = add_calendar_features(df)
    out = add_lag_features(out, "departures", lags=[1, 24], windows=[3])
    assert out.loc[1, "departures_lag_1"] == 0
    assert out.loc[24, "departures_lag_24"] == 0
    assert {"hour_sin", "hour_cos", "departures_roll_mean_3"}.issubset(out.columns)
