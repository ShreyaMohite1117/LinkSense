# LinkSense - ML-Powered URL Shortener

A full-stack URL shortener that uses machine learning to block phishing links, predict clicks and detect bot traffic.

## Tech Stack

| Category | Technologies |
|---|---|
| **Frontend** | React, Vite, Recharts |
| **Backend** | Python, Flask, REST APIs |
| **Database** | MongoDB |
| **Caching** | Redis |
| **Machine Learning** | Scikit-learn (Gradient Boosting, Random Forest, Isolation Forest) |
| **Authentication** | JWT (access and refresh tokens) |
| **DevOps** | Docker, GitHub Actions |

---

## Screenshots

| Login | Dashboard |
|---|---|
| ![Login](<img width="1365" height="690" alt="login_page" src="https://github.com/user-attachments/assets/1e5313a2-ee13-463f-8822-eb80e786b14d" />
) | ![Dashboard](<img width="1365" height="670" alt="dashboard_1" src="https://github.com/user-attachments/assets/153fdba9-b325-4161-aba8-f431f6393eec" />
)(<img width="1362" height="668" alt="dashboard_2" src="https://github.com/user-attachments/assets/7fdb2f91-eb0b-4e8f-bb3c-9801ac8d77f9" />)
|

| Create Link | Short Link Created |
|---|---|
| ![Create Link](docs/screenshots/create-link.png) | ![Link Created](docs/screenshots/link-created.png) |

| My Links | Recent Links |
|---|---|
| ![My Links](docs/screenshots/my-links.png) | ![Recent Links](docs/screenshots/recent-links.png) |

| URL Scanner | ML Model Metrics |
|---|---|
| ![URL Scanner](docs/screenshots/url-scanner.png) | ![ML Models](docs/screenshots/ml-models.png) |

---

## Features

**Link Management**
- Short links with random codes or custom aliases
- Password protection, expiry dates and click limits
- QR code for every link
- Bulk shortening and CSV export

**Machine Learning**
- **Phishing Detection:** checks every URL before it is shortened and blocks dangerous links
- **Click Prediction:** a Random Forest model predicts the next 24 hours of clicks
- **Bot Detection:** an Isolation Forest model flags bot traffic and unusual click patterns

**Analytics**
- Clicks over time, unique visitors and bot clicks
- Country, device, browser and referrer breakdowns
- AI-generated insights for each link

**Security & Performance**
- JWT login with access and refresh tokens
- Rate limiting to prevent abuse
- Redis caching for faster redirects
- Light and dark mode

---

## ML Model Results

| Model | Result |
|---|---|
| Phishing Detection (Gradient Boosting) | 97.7% accuracy, 97.6% precision, 97.8% recall |
| Click Prediction (Random Forest) | 54.7% lower error than a simple baseline |
| Bot Detection (Isolation Forest) | Flags unusual clicks for each link |

**How phishing detection works**

- **Model accuracy (97.7%)** is the overall result. The model was tested on 2,400 URLs it had never seen and classified 97.7% of them correctly.
- **Risk score** is different for every URL:

| Score | Result |
|---|---|
| Below 50% | Safe |
| 50% – 80% | Warning shown |
| Above 80% | Link blocked |

*The model is trained on 12,000 URLs built from common phishing patterns and real websites.*

---

## How to Run

**Requirements:** Python 3.10+ and Node.js 18+
MongoDB and Redis are optional. Without them, the app runs with a built-in demo database.

**1. Clone the project**
```bash
git clone https://github.com/shreyamohite1117/linksense.git
cd linksense
```

**2. Start the backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```
The first start takes about 40 seconds while the ML models are trained.

**3. Start the frontend** (in a new terminal)
```bash
cd frontend
npm install
npm run dev
```

**4. Open the app**
Go to **http://localhost:5173** and log in with the demo account:
- Email: `demo@linksense.dev`
- Password: `Demo@1234`

**Run with Docker (optional)**
```bash
docker compose up --build
```

---

## Run Tests
```bash
cd backend
pytest
```

---

## Project Structure
```
linksense/
├── backend/     Flask API, ML models, tests
├── frontend/    React app
└── docker-compose.yml
```

---

## Author

**Shreya Mohite**
GitHub: [shreyamohite1117](https://github.com/shreyamohite1117)
