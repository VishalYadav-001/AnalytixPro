# AnalytixPro

AI-powered automated data analytics platform.

## Project Structure

```
AnalytixPro/
├── analytixpro-backend/     # Django REST API
│   ├── analytics/           # Main app (models, views, serializers, services)
│   ├── core/                # Django project settings and URLs
│   ├── media/               # Uploaded files (datasets, exports)
│   ├── venv/                # Python virtual environment
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env                 # Local secrets (not committed)
│   └── .env.example         # Template — copy to .env and fill in values
│
├── analytixpro-frontend/    # Vue 3 + Vite + Tailwind CSS SPA
│   ├── src/
│   │   ├── pages/           # Route-level components
│   │   ├── components/      # Shared layout and UI components
│   │   ├── stores/          # Pinia state (auth)
│   │   ├── services/        # Axios API client
│   │   └── router/          # Vue Router
│   ├── .env                 # Local env vars (not committed)
│   └── .env.example         # Template — copy to .env
│
└── datasets/                # Raw sample datasets (xlsx/csv)
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue 3, Vite, Tailwind CSS, Pinia, Axios |
| Backend | Django 6, Django REST Framework, SimpleJWT |
| Database | PostgreSQL (SQLite for quick dev) |
| Data/ML | Pandas, NumPy, Scikit-learn, Plotly |
| AI | Google Gemini API |

## Quick Start

### 1. Backend

```bash
cd analytixpro-backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set SECRET_KEY, DB credentials, GEMINI_API_KEY

# Run migrations and start server
python manage.py migrate
python manage.py runserver
```

Backend runs at `http://localhost:8000`

### 2. Frontend

```bash
cd analytixpro-frontend

# Configure environment
cp .env.example .env

# Install dependencies and start dev server
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

## API Overview

All endpoints are under `/api/`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login, returns JWT tokens |
| GET/PATCH | `/api/auth/me/` | Current user profile |
| GET/POST | `/api/datasets/` | List / upload datasets |
| POST | `/api/datasets/{id}/run-analysis/` | Trigger EDA on a dataset |
| GET/POST | `/api/chat-sessions/` | List / create chat sessions |
| POST | `/api/chat-sessions/{id}/send-message/` | Send message to AI |
| GET | `/api/analyses/` | List analyses |
| POST | `/api/dashboards/generate/` | Generate dashboard from analysis |
| POST | `/api/dashboards/{id}/export/` | Export dashboard (PDF/notebook/script) |

## Features

- **JWT Auth** — Login/register with access + refresh tokens; auto-refresh on 401
- **Dataset Upload** — CSV/Excel; server validates type, size, extracts metadata
- **Automated EDA** — Summary stats, missing values, correlations, categorical insights, KPIs
- **Dashboard Generator** — Chart config generated automatically from EDA results
- **Export Engine** — PDF report, Jupyter Notebook, or Python script
- **AI Chat** — Guided analysis setup via Gemini-powered chatbot
