"""Train the Random Forest click forecaster.

    python -m ml_training.train_forecaster

The model predicts log1p(clicks) for the next hour from recent history. At
runtime we roll it forward hour by hour to get a 24h forecast.
"""
import json
import math
import os
import time

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from app.ml import forecast_features as ff
from ml_training import traffic_simulator

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, "..", "app", "ml", "models")


def build_xy(series_list, min_history=6):
    X, y, groups = [], [], []
    for idx, (series, start_hour, start_dow) in enumerate(series_list):
        for t in range(min_history, len(series)):
            abs_hour = start_hour + t
            hour = abs_hour % 24
            dow = (start_dow + abs_hour // 24) % 7
            X.append(ff.row(series[:t], hour, dow, t))
            y.append(math.log1p(series[t]))
            groups.append(idx)
    return np.array(X), np.array(y), np.array(groups)


def train(verbose=True):
    started = time.time()
    links = traffic_simulator.simulate()
    X, y, groups = build_xy(links)

    # split by link so the test set is links the model has never seen
    test_mask = groups % 5 == 0
    X_train, y_train = X[~test_mask], y[~test_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    model = RandomForestRegressor(
        n_estimators=120, max_depth=14, min_samples_leaf=5, n_jobs=-1, random_state=42
    )
    model.fit(X_train, y_train)

    pred = np.expm1(model.predict(X_test)).clip(min=0)
    actual = np.expm1(y_test)
    # naive baseline: "next hour looks like the same hour yesterday"
    naive = np.expm1(X_test[:, ff.FEATURE_NAMES.index("lag_24")])

    mae = mean_absolute_error(actual, pred)
    naive_mae = mean_absolute_error(actual, naive)
    metrics = {
        "model": "RandomForestRegressor",
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "mae_clicks_per_hour": round(float(mae), 3),
        "naive_mae_clicks_per_hour": round(float(naive_mae), 3),
        "improvement_over_naive_pct": round(float((naive_mae - mae) / naive_mae * 100), 1),
        "feature_importance": {
            k: round(float(v), 4)
            for k, v in sorted(zip(ff.FEATURE_NAMES, model.feature_importances_), key=lambda kv: -kv[1])
        },
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "train_seconds": round(time.time() - started, 1),
    }

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": model, "features": ff.FEATURE_NAMES}, os.path.join(MODEL_DIR, "forecaster.joblib"))
    with open(os.path.join(MODEL_DIR, "forecaster_metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=2)
    if verbose:
        print(json.dumps({k: v for k, v in metrics.items() if k != "feature_importance"}, indent=2))
    return metrics


if __name__ == "__main__":
    train()
