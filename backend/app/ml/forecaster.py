from datetime import timedelta

import numpy as np

from app.ml import forecast_features as ff
from app.ml import registry


def forecast_next_hours(hourly_counts, last_hour_start, age_hours, horizon=24):
    """Roll the one-step model forward `horizon` hours.

    hourly_counts   list of click counts, oldest first, one per hour, ending at `last_hour_start`
    last_hour_start aware datetime of the final bucket in `hourly_counts`
    """
    model = registry.get("forecaster")["model"]
    history = list(hourly_counts)
    out = []
    for step in range(1, horizon + 1):
        ts = last_hour_start + timedelta(hours=step)
        x = np.array([ff.row(history, ts.hour, ts.weekday(), age_hours + step)])
        pred = max(0.0, float(np.expm1(model.predict(x)[0])))
        history.append(pred)
        out.append({"hour": ts.isoformat(), "predicted": round(pred, 2)})
    return out


def summarize(hourly_counts, forecast):
    last_24 = float(np.sum(hourly_counts[-24:])) if hourly_counts else 0.0
    next_24 = float(sum(p["predicted"] for p in forecast))
    if sum(hourly_counts) < 10:
        # too little history for a percentage change to mean anything
        trend = "warming_up" if next_24 >= 0.5 else "quiet"
        change = 0.0
    else:
        change = (next_24 - last_24) / max(last_24, 1.0) * 100
        trend = "rising" if change > 15 else "falling" if change < -15 else "steady"
    peak = max(forecast, key=lambda p: p["predicted"]) if forecast else None
    return {
        "last_24h": int(last_24),
        "predicted_next_24h": round(next_24, 1),
        "change_pct": round(change, 1),
        "trend": trend,
        "predicted_peak_hour": peak["hour"] if peak and peak["predicted"] > 0.2 else None,
    }
