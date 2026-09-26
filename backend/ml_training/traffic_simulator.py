"""Simulates hourly click series for links so the forecaster has history to learn from.

Each simulated link gets:
  * a base popularity (log-normal, so most links are small and a few are big)
  * a daily cycle that peaks in the evening (IST-ish browsing pattern)
  * a weekday / weekend effect
  * a launch spike that decays over a few days (people share a link, then it cools off)
  * the odd random viral burst
and counts are Poisson sampled on top of that.
"""
import math

import numpy as np


def hourly_profile(hour):
    # low at night, bump at lunch, peak around 8-9 PM
    return 0.35 + 0.45 * math.exp(-((hour - 13) ** 2) / 8) + 0.9 * math.exp(-((hour - 20.5) ** 2) / 6)


def simulate_link(rng, hours=24 * 21):
    base = rng.lognormal(mean=0.0, sigma=1.3)
    launch = rng.uniform(2, 25)
    decay = rng.uniform(12, 96)
    weekend_boost = rng.uniform(0.7, 1.4)
    start_dow = rng.integers(0, 7)
    start_hour = rng.integers(0, 24)

    series = np.zeros(hours, dtype=float)
    burst_left = 0
    burst_size = 0.0
    for t in range(hours):
        hour = (start_hour + t) % 24
        dow = (start_dow + (start_hour + t) // 24) % 7
        rate = base * hourly_profile(hour)
        if dow >= 5:
            rate *= weekend_boost
        rate *= 1 + launch * math.exp(-t / decay)
        if burst_left == 0 and rng.random() < 0.004:
            burst_left = rng.integers(2, 8)
            burst_size = rng.uniform(3, 12)
        if burst_left:
            rate *= burst_size
            burst_left -= 1
        series[t] = rng.poisson(rate)
    return series, int(start_hour), int(start_dow)


def simulate(n_links=400, seed=7):
    rng = np.random.default_rng(seed)
    return [simulate_link(rng) for _ in range(n_links)]
