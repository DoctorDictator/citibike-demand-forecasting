from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class ClassificationResult:
    model_name: str
    f1: float
    roc_auc: float | None
    model: object


def _preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    return ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical),
    ], remainder="drop")


def train_binary_models(X_train, y_train, X_test, y_test) -> list[ClassificationResult]:
    models = {
        "logistic": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "lda": LinearDiscriminantAnalysis(),
        "qda": QuadraticDiscriminantAnalysis(reg_param=0.05),
    }
    results = []
    for name, estimator in models.items():
        pipe = Pipeline([("prep", _preprocessor(X_train)), ("model", estimator)])
        try:
            pipe.fit(X_train, y_train)
            pred = pipe.predict(X_test)
            proba = pipe.predict_proba(X_test)[:, 1] if hasattr(pipe, "predict_proba") else None
            auc = roc_auc_score(y_test, proba) if proba is not None and len(set(y_test)) > 1 else None
            results.append(ClassificationResult(name, f1_score(y_test, pred), auc, pipe))
        except Exception as exc:
            print(f"warning: {name} skipped: {exc}")
    return results
