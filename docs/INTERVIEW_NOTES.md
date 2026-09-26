# LinkSense - talking points

Notes for explaining the design decisions behind the project.

## Why cache-aside for redirects?
Redirects are ~99% reads on a small set of hot links. On first hit the link is read from MongoDB and stored in Redis (`link:<code>`) with a TTL capped at the link's expiry time. Edits and deletes delete the key. Click counters are *not* cached because they change on every click; links with a click limit re-read the counter from Mongo. Unknown codes are negatively cached for 60s so junk traffic doesn't hit the DB. The `X-Cache` header on redirects shows HIT/MISS.

## Why pre-bucketed `day` and `hour_key` fields on clicks?
Time-series grouping becomes a simple `$group` on a string field instead of date math inside the pipeline, and the compound index `(link_id, ts)` covers the range filters.

## Rate limiting
Fixed window counters in Redis (`INCR` + `EXPIRE` on the first hit). Keyed by user id when logged in, otherwise by IP. Separate buckets for auth, shortening, scanning and password unlocks (the last one stops brute-forcing link passwords).

## Phishing model
- Lexical features only, so scoring takes microseconds and needs no network calls (no WHOIS, no page fetch).
- Compared Logistic Regression, Random Forest and Gradient Boosting; picked by F1 on a stratified 80/20 split.
- A trusted-domain allowlist caps the score for sites like google.com so "login" in a URL doesn't cause false positives.
- Two thresholds: warn at 0.5, block at 0.8. Blocked attempts are logged.
- Honest limitation: the training data is generated from known phishing patterns. The script accepts a real labelled CSV to retrain.

## Click forecaster
- One-step-ahead `RandomForestRegressor` on log1p counts (lags 1/2/3/24/48, rolling means, rolling max, hour as sin/cos, weekend flag, link age).
- Recursive 24-step forecast: each prediction becomes the next step's lag.
- Log transform keeps a link with 3 clicks/hour and one with 3,000 structurally similar.
- Split by *link* (not by time row) for evaluation so the test set is links the model never saw. Reports MAE vs. a "same hour yesterday" baseline.

## Isolation Forest
- Unsupervised, so no labelled fraud data is needed.
- Fitted per link on its own clicks, so "normal" is relative to that link's audience.
- Falls back to rules below 25 clicks, where a forest isn't meaningful.
- Output is cached per (link, click count) for 5 minutes.

## Security
- Passwords hashed with Werkzeug (PBKDF2/scrypt), JWT access (60 min) + refresh (7 days) tokens with a `type` claim so one can't be used as the other.
- IPs are salted-hashed; only a masked `49.36.x.x` form is stored for display.
- Only http/https destinations are accepted (no `javascript:` URLs); reserved paths can't be used as aliases.
- Destination of a password-protected link is never sent to the browser until the password is verified.

## What I'd do next at scale
- Push click logging onto a queue so redirect latency is independent of DB writes.
- Counter sharding or Redis `INCR` + periodic flush for very hot links.
- Base62 codes from a distributed ID generator instead of random + collision check.
