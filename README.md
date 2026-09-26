# LinkSense - ML-Powered URL Shortener

A full-stack URL shortener with three machine learning models built in: **phishing URL detection**, **Random Forest click forecasting** and **Isolation Forest anomaly detection** on click traffic.

**Stack:** React 18 (Vite) · Flask 3 · MongoDB · Redis · scikit-learn · JWT · Docker · GitHub Actions

---

## Features

**Links**
- Shorten any URL with a random code or a custom alias (with live availability check)
- Smart alias suggestions generated from the destination URL
- Password-protected links, expiry dates and click limits
- Pause / resume, edit the destination without changing the short link
- Bulk shortening (paste a list or upload a CSV), CSV export
- QR code for every link, with colour options and PNG download

**Machine learning**
- **Phishing detection** - 25 lexical/host features (IP hosts, brand look-alikes, suspicious TLDs, keyword counts, entropy...). Three models are trained and compared (Logistic Regression, Random Forest, Gradient Boosting); the best F1 wins. High-risk URLs are refused, medium-risk ones get a warning.
- **Click forecasting** - a `RandomForestRegressor` trained on lag + seasonality features predicts the next hour, then rolls forward to a 24-hour forecast. Evaluated against a "same hour yesterday" baseline.
- **Anomaly detection** - an `IsolationForest` is fitted on each link's own clicks (burst size, repeat-click gap, IP share, bot user-agent, referrer, time of day) and flags scrapers and click fraud.
- **AI insights** - plain-English summary of each link's traffic, forecast and anomalies.

**Platform**
- JWT auth with access + refresh tokens (auto-refresh in the frontend)
- API keys for programmatic access (`X-API-Key` header)
- Redis cache-aside for redirects, with an in-memory fallback if Redis isn't running
- Fixed-window rate limiting on login, signup, shortening, scanning and password unlocks
- Privacy: IPs are hashed with a secret salt and only a masked version is shown
- Light / dark theme toggle, responsive layout

---

## Architecture

```
 React (Vite)  ──/api──►  Flask REST API  ──►  MongoDB  (users, links, clicks)
      │                        │
      │                        ├──►  Redis  (redirect cache, rate limits)
      │                        │
      │                        └──►  scikit-learn models
      │                               ├─ phishing classifier   (on create / scan)
      │                               ├─ RF click forecaster   (on analytics view)
      │                               └─ Isolation Forest      (on analytics view)
      │
 Visitor ──► GET /<code> ──► cache lookup ──► status checks ──► log click ──► 302 redirect
```

---

## Running locally (VS Code)

### Prerequisites
- **Python 3.10+** and **Node.js 18+**
- **MongoDB** (optional) - [MongoDB Community](https://www.mongodb.com/try/download/community) or a free [Atlas](https://www.mongodb.com/atlas) cluster
- **Redis** (optional) - the app falls back to an in-memory cache without it

> No MongoDB? No problem. With `USE_MOCK_DB=auto` (the default) the backend uses MongoDB if it's running and otherwise switches to an in-memory database pre-loaded with demo data. Data resets on restart in that mode.

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env      # Windows   (macOS/Linux: cp .env.example .env)
python run.py
```

The API runs at http://localhost:5000. Check http://localhost:5000/api/health.

**First start takes about 40 seconds** because the ML models are trained and saved to `app/ml/models/`. After that the server starts in a couple of seconds. (If you upgrade scikit-learn later, the models retrain themselves automatically.)

### 2. Frontend (second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### 3. Log in

Use the demo account (**demo@linksense.dev / Demo@1234**) or sign up.
When running on a real MongoDB, load the demo data with:

```bash
cd backend
python -m scripts.seed_demo
```

### Or run everything with Docker

```bash
docker compose up --build
```

Frontend: http://localhost:3000 · API: http://localhost:5000 · MongoDB and Redis are included.

---

## Tests

```bash
cd backend
pytest -q
```

23 tests cover auth, link creation, redirects, password/expiry/click-limit rules, cache invalidation, ownership checks, QR generation and all three ML components. CI runs them plus a frontend build on every push.

---

## Retraining the models

```bash
cd backend
python -m ml_training.train_all        # both models
python -m ml_training.train_phishing   # just the classifier
```

Metrics are saved next to the models (`*_metrics.json`) and shown on the **URL Scanner** page.

The phishing model trains on a generated dataset built from real phishing patterns (brand-in-subdomain, IP hosts, typosquats, `@` tricks, free-hosting drops...) plus legitimate URLs from popular sites, with 2% label noise. To train on a real dataset (e.g. Kaggle "Malicious URLs" or PhiUSIIL), save it as `backend/ml_training/data/urls.csv` with `url,label` columns (1 = phishing) and rerun the script.

The forecaster trains on simulated hourly traffic (daily cycle, weekend effect, launch spike with decay, random viral bursts). At runtime it predicts from each link's real click history.

---

## API overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/signup` | Create account |
| POST | `/api/auth/login` | Log in, returns access + refresh tokens |
| POST | `/api/auth/refresh` | New access token |
| GET / PATCH | `/api/auth/me` | Current user / update name |
| POST | `/api/auth/change-password` | Change password |
| POST / DELETE | `/api/auth/api-key` | Generate / revoke API key |
| POST | `/api/links` | Create short link (phishing check runs here) |
| POST | `/api/links/bulk` | Create up to 50 links |
| GET | `/api/links` | List with search, status filter, sort, pagination |
| GET / PATCH / DELETE | `/api/links/:id` | Read / update / delete a link |
| GET | `/api/links/suggest-alias?url=` | Smart alias ideas |
| GET | `/api/links/check-alias?alias=` | Alias availability |
| GET | `/api/links/export` | CSV of all links |
| GET | `/api/analytics/overview` | Dashboard totals |
| GET | `/api/analytics/links/:id` | Stats, forecast, anomalies, insights |
| GET | `/api/analytics/links/:id/export` | CSV of clicks |
| POST | `/api/scan` | Phishing score for any URL (no login needed) |
| GET | `/api/ml/models` | Model metrics |
| GET | `/api/qr/:code` | QR code PNG |
| GET | `/:code` | Redirect |
| POST | `/api/r/:code/unlock` | Unlock a password-protected link |
| GET | `/api/health` | DB / cache / model status |

Example with an API key:

```bash
curl -X POST http://localhost:5000/api/links \
  -H "X-API-Key: lsk_..." -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/long/path", "alias": "example", "expires_in_days": 7}'
```

---

## Project structure

```
linksense/
├── backend/
│   ├── app/
│   │   ├── routes/        auth, links, analytics, scanner, redirect, health
│   │   ├── services/      cache (Redis + fallback), rate limiter, click tracker, analytics
│   │   ├── ml/            features, phishing, forecaster, anomaly, alias, model registry
│   │   ├── utils/         JWT helpers, validators, serializers, short codes
│   │   ├── config.py
│   │   └── extensions.py  MongoDB (with auto in-memory fallback)
│   ├── ml_training/       dataset builder, traffic simulator, training scripts
│   ├── scripts/seed_demo.py
│   ├── tests/
│   ├── run.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/           axios client with token refresh
│       ├── context/       auth + theme
│       ├── components/    navbar, link rows, modals, charts helpers
│       └── pages/         landing, login, signup, dashboard, links, analytics, scanner, settings
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## Environment variables (backend/.env)

| Variable | Default | Notes |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017/linksense` | Local, Docker or Atlas |
| `USE_MOCK_DB` | `auto` | `auto`, `true` (always in-memory), `false` (MongoDB only) |
| `REDIS_URL` | `redis://localhost:6379/0` | Optional |
| `SECRET_KEY`, `JWT_SECRET` | - | Change these in production |
| `BASE_URL` | `http://localhost:5000` | Used to build short links |
| `FRONTEND_URL` | `http://localhost:5173` | Where password / expired pages live |
| `PHISHING_WARN_THRESHOLD` / `PHISHING_BLOCK_THRESHOLD` | `0.5` / `0.8` | Model score cut-offs |
| `RATE_LIMIT_AUTH`, `RATE_LIMIT_SHORTEN` | `10/minute`, `30/minute` | Per IP or per user |

---

## Ideas for later
- Move click logging to a queue (Celery / RQ) so redirects never wait on a DB write
- GeoIP lookups with MaxMind GeoLite2 for non-CDN deployments
- Custom domains per user
- Retrain the forecaster on real traffic once there's enough of it
