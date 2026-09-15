# 🌍 YATRA360 — AI-Enabled Smart Tourism Platform

YATRA360 gives travelers personalized destination recommendations, detects overcrowding, suggests better alternatives, surfaces safety info, generates itineraries, and promotes lesser-known destinations and local businesses.

Instead of just warning users about crowded or unsafe spots, YATRA360 ranks and recommends better alternatives — balancing crowd levels, safety, cost, distance, weather, and preferences — so tourism value spreads more evenly across destinations and communities.

> 🚧 **Status:** Prototype / Foundation phase. This repo has the full-stack skeleton (backend API, database layer, frontend SPA, health checks, tests) that upcoming modules (scoring, recommendations, maps, auth) will build on.

---

## ✨ Features

**Planned**
- 🎯 **Personalized Recommendations** — based on interests, budget, travel type & accessibility needs
- 📊 **Dynamic Destination Scoring** — a transparent weighted model:
  `Score = 0.25×Preference + 0.20×Safety + 0.20×Crowd + 0.15×Accessibility + 0.10×Cost + 0.10×Weather`
- 🧭 **Overcrowding Detection & Alternatives** — ranks better nearby options instead of just warning
- 🛡️ **Safety Dashboard** — indicators, alerts & nearby emergency info (decision support, not a guarantee)
- 🗓️ **Smart Itinerary Planner** — day-wise plans from time, budget & interests
- 🏘️ **Local Business Discovery** — visibility for guides, artisans, homestays & restaurants
- 🗺️ **Map Integration** — destinations, routes & nearby services
- 📈 **Admin & Analytics Dashboard** — manage data, view crowd & recommendation trends
- 🔐 **Auth & Role-Based Access** — JWT/OAuth for tourists, businesses, guides & admins

**Already Built (Foundation Phase)**
- ⚙️ FastAPI backend with versioned routing (`/api/v1`) & CORS setup
- ❤️ Resilient health probe (`/api/v1/health`) — boots in `degraded` mode if the DB is offline
- 🗄️ SQLAlchemy ORM + Alembic migrations for PostgreSQL
- ⚛️ React (Vite) frontend with a decoupled API layer & live health dashboard
- ✅ Automated pytest suite

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js (Vite), HTML, CSS, JS |
| Backend | Python, FastAPI |
| AI / ML | scikit-learn, Pandas, NumPy |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| Maps | OpenStreetMap / Mapbox / Google Maps |
| Weather | Weather API |
| Visualization | Plotly / Chart.js |
| Auth | JWT / OAuth |
| Testing | Pytest |
| Deployment | Render / Railway / Vercel |

*Open datasets and simulated data are used for the prototype where live sources aren't available yet.*

---

## 🚀 Setup Instructions

**Prerequisites:** Python 3.10+, Node.js 18+, PostgreSQL 14+ (optional — backend runs `degraded` without it)

**1. Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
python run.py
```
Runs at `http://127.0.0.1:8000` · Docs: `/api/v1/docs` · Health: `/api/v1/health`

**2. Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Runs at `http://localhost:5173`

**3. Check it works** — open the frontend, confirm the **System Health** card shows `HEALTHY` (or `DEGRADED` without Postgres).

**Migrations** (once Postgres is running):
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

**Run tests:**
```bash
cd backend && pytest tests -v
```

---

## ☁️ Deployment

Built for lightweight prototype hosting, not production-scale infra yet.

| Component | Suggested Platform |
|---|---|
| Backend | Render, Railway, or Fly.io |
| Frontend | Vercel or Netlify |
| Database | Managed PostgreSQL (Render, Supabase, Neon) |

**Flow:** provision Postgres → set `DATABASE_URL` → deploy backend → run `alembic upgrade head` → build & deploy frontend (`npm run build`) pointed at the backend URL → lock down CORS to your deployed domain.

---

## 🔒 Security and Safety

**App Security**
- 🔑 JWT-based auth with role-based access control
- 🙈 Secrets live in `.env` (never committed); `.env.example` documents required vars
- 🌐 CORS restricted to known frontend origins in production
- ✅ Pydantic validation on all requests/responses
- 📦 Pinned/locked dependencies (`requirements.txt`, `package-lock.json`)
- 🗄️ ORM-only DB access to reduce injection risk

**Tourism Safety**
- ⚠️ Safety scores are **informational decision support**, not an official safety guarantee
- 🏷️ Data sources are labeled; simulated/prototype data is clearly distinguished from verified data
- 🔭 Roadmap includes verified government/official safety sources & real-time emergency alerts
- 🔐 User preferences and trip data are treated as personal data — minimize and secure before real-world use

Found a vulnerability? Please report it privately (e.g. via GitHub Security Advisories) instead of a public issue.

---

## 🗺️ Roadmap

- [ ] Auth & role-based access control
- [ ] Destination database & seeding
- [ ] Destination scoring engine
- [ ] Overcrowding & alternative recommender
- [ ] Itinerary planner
- [ ] Local business discovery
- [ ] Map integration
- [ ] Admin & analytics dashboard
- [ ] Deployment pipeline

**Future:** real-time crowd sensing, government data integration, multilingual voice assistant, mobile apps, booking integrations, sustainable-travel scoring.