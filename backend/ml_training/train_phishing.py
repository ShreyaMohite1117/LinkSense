"""Train the phishing URL classifier.

    python -m ml_training.train_phishing

Compares a couple of models, keeps the best one (by F1 on a held-out split)
and writes it to app/ml/models/phishing.joblib with its metrics.
"""
import csv
import json
import os
import time

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.ml import url_features
from ml_training import phishing_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, "..", "app", "ml", "models")
CUSTOM_DATA = os.path.join(HERE, "data", "urls.csv")


def load_rows():
    if os.path.exists(CUSTOM_DATA):
        with open(CUSTOM_DATA, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = [(r["url"], int(r["label"])) for r in reader if r.get("url")]
        print(f"Using custom dataset: {len(rows)} rows")
        return rows, "custom"
    return phishing_dataset.build(), "generated"


def train(verbose=True):
    started = time.time()
    rows, source = load_rows()
    X = np.array([url_features.vector(u) for u, _ in rows], dtype=float)
    y = np.array([label for _, label in rows])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    candidates = {
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=18, min_samples_leaf=2, n_jobs=-1, random_state=42
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
    }

    results = {}
    best_name, best_model, best_f1 = None, None, -1
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        pred = (proba >= 0.5).astype(int)
        scores = {
            "accuracy": round(accuracy_score(y_test, pred), 4),
            "precision": round(precision_score(y_test, pred), 4),
            "recall": round(recall_score(y_test, pred), 4),
            "f1": round(f1_score(y_test, pred), 4),
            "roc_auc": round(roc_auc_score(y_test, proba), 4),
        }
        results[name] = scores
        if verbose:
            print(f"{name:22s} {scores}")
        if scores["f1"] > best_f1:
            best_name, best_model, best_f1 = name, model, scores["f1"]

    importances = {}
    if hasattr(best_model, "feature_importances_"):
        ranked = sorted(
            zip(url_features.FEATURE_NAMES, best_model.feature_importances_), key=lambda kv: kv[1], reverse=True
        )
        importances = {k: round(float(v), 4) for k, v in ranked}

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": best_model, "features": url_features.FEATURE_NAMES}, os.path.join(MODEL_DIR, "phishing.joblib"))
    meta = {
        "chosen_model": best_name,
        "dataset": source,
        "samples": len(rows),
        "test_metrics": results[best_name],
        "all_models": results,
        "feature_importance": importances,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "train_seconds": round(time.time() - started, 1),
    }
    with open(os.path.join(MODEL_DIR, "phishing_metrics.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    if verbose:
        print(f"Saved {best_name} (F1={best_f1})")
    return meta


if __name__ == "__main__":
    train()
