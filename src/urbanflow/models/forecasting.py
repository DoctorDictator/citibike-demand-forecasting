from __future__ import annotations

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX


def aggregate_city_hourly(df: pd.DataFrame, target: str = "departures") -> pd.Series:
    series = df.groupby("timestamp")[target].sum().sort_index()
    series.index = pd.DatetimeIndex(series.index)
    return series.asfreq("h", fill_value=0)


def holdout_forecast(series: pd.Series, horizon: int = 168) -> dict:
    if len(series) <= horizon + 48:
        raise ValueError("Need more observations than the forecast horizon")
    train, test = series.iloc[:-horizon], series.iloc[-horizon:]
    results = {}

    hw = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=24, initialization_method="estimated").fit()
    hw_pred = hw.forecast(horizon)
    results["holt_winters"] = {
        "model": hw,
        "forecast": hw_pred,
        "mae": mean_absolute_error(test, hw_pred),
        "rmse": mean_squared_error(test, hw_pred) ** 0.5,
    }

    sarima = SARIMAX(train, order=(1, 1, 1), seasonal_order=(1, 0, 1, 24),
                     enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    sarima_pred = sarima.forecast(horizon)
    results["sarima"] = {
        "model": sarima,
        "forecast": sarima_pred,
        "mae": mean_absolute_error(test, sarima_pred),
        "rmse": mean_squared_error(test, sarima_pred) ** 0.5,
    }
    results["test"] = test
    return results
