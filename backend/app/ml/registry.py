"""Loads trained models once and retrains them if they're missing or were
pickled by an incompatible scikit-learn version."""
import json
import logging
import os
import threading
import warnings

import joblib

log = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
_lock = threading.Lock()
_models = {}


def _trainer(name):
    if name == "phishing":
        from ml_training.train_phishing import train
    else:
        from ml_training.train_forecaster import train
    return train


def _try_load(path):
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # turn sklearn version warnings into failures
        return joblib.load(path)


def get(name):
    """name: 'phishing' or 'forecaster'"""
    if name in _models:
        return _models[name]
    with _lock:
        if name in _models:
            return _models[name]
        path = os.path.join(MODEL_DIR, f"{name}.joblib")
        bundle = None
        if os.path.exists(path):
            try:
                bundle = _try_load(path)
            except Exception as exc:  # noqa: BLE001
                log.warning("Could not load %s (%s) - retraining", name, exc)
        if bundle is None:
            log.info("Training %s model, this takes a few seconds the first time...", name)
            _trainer(name)(verbose=False)
            bundle = joblib.load(path)
        model = bundle["model"]
        if hasattr(model, "n_jobs"):
            # single-row predictions are faster without spinning up a worker pool
            model.n_jobs = 1
        _models[name] = bundle
        return bundle


def metrics(name):
    path = os.path.join(MODEL_DIR, f"{name}_metrics.json")
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return json.load(fh)


def warm_up():
    for name in ("phishing", "forecaster"):
        get(name)
