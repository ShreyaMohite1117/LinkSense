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

| Login | 
<img width="1365" height="690" alt="login_page" src="https://github.com/user-attachments/assets/a938959b-39f4-4e57-885f-cc0b1c23b73d" />

| Dashboard |

<img width="1365" height="670" alt="dashboard_1" src="https://github.com/user-attachments/assets/44cb8c71-f774-4bbb-8ca9-4146eaf80baa" />
<img width="1362" height="668" alt="dashboard_2" src="https://github.com/user-attachments/assets/09e0da72-b16a-4b55-941e-855b79ca7b17" />

| Short Link Created |
<img width="1365" height="668" alt="link_short_url1" src="https://github.com/user-attachments/assets/d7628e51-9c93-4d4b-b3e7-1489cb406e1c" />

| My Links | 

<img width="1365" height="669" alt="my_links_page" src="https://github.com/user-attachments/assets/a78d039a-8519-4e2c-9efe-4a0e433a4245" />

| URL Scanner |
<img width="1361" height="682" alt="url_scanner1" src="https://github.com/user-attachments/assets/fe9ceebb-b958-4312-be44-adf9a8ac0b66" />
<img width="1365" height="668" alt="url_scanner_2" src="https://github.com/user-attachments/assets/db392879-6b0e-4f90-9737-402bda223ee0" />

| Theme Changing |

<img width="1364" height="681" alt="dark_theme_dashboard" src="https://github.com/user-attachments/assets/d10fdcd6-268b-4d60-866a-cda36bf33b2a" />


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
