from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error


def fit_count_models(train: pd.DataFrame, test: pd.DataFrame, target: str, features: list[str]) -> dict:
    X_train = train[features].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    X_test = test[features].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    y_train = pd.to_numeric(train[target], errors="coerce").fillna(0.0)
    y_test = pd.to_numeric(test[target], errors="coerce").fillna(0.0)
    X_train = sm.add_constant(X_train, has_constant="add")
    X_test = sm.add_constant(X_test, has_constant="add")
    fitted = {
        "poisson": sm.GLM(y_train, X_train, family=sm.families.Poisson()).fit(),
        "negative_binomial": sm.GLM(y_train, X_train, family=sm.families.NegativeBinomial(alpha=1.0)).fit(),
    }
    out = {}
    for name, model in fitted.items():
        pred = np.clip(model.predict(X_test), 0, None)
        out[name] = {
            "model": model,
            "mae": mean_absolute_error(y_test, pred),
            "rmse": mean_squared_error(y_test, pred) ** 0.5,
        }
    return out
