"""Feature builder shared by the forecaster's training script and runtime."""
import math

import numpy as np

FEATURE_NAMES = [
    "lag_1", "lag_2", "lag_3", "lag_24", "lag_48", "mean_6", "mean_24", "mean_72",
    "max_24", "hour_sin", "hour_cos", "is_weekend", "log_age_hours",
]


def row(history, hour, dow, age_hours):
    """Features for predicting the *next* hour given the hourly `history` so far.

    Counts go through log1p so a link doing 3 clicks/hr and one doing 3000
    look structurally similar to the trees.
    """
    h = np.asarray(history, dtype=float)

    def lag(k):
        return math.log1p(h[-k]) if len(h) >= k else 0.0

    def window(k, fn):
        seg = h[-k:] if len(h) else np.zeros(1)
        return math.log1p(fn(seg))

    return [
        lag(1), lag(2), lag(3), lag(24), lag(48),
        window(6, np.mean), window(24, np.mean), window(72, np.mean), window(24, np.max),
        math.sin(2 * math.pi * hour / 24), math.cos(2 * math.pi * hour / 24),
        1.0 if dow >= 5 else 0.0,
        math.log1p(age_hours),
    ]
