# YATRA360 — AI-Enabled Smart Tourism Platform (Prototype)

YATRA360 is an AI-enabled smart tourism web platform designed to provide personalized destination recommendations, detect overcrowding, suggest suitable alternative destinations, provide safety information, generate itineraries, and promote lesser-known destinations and local businesses.

---

## Current Phase: Foundation & Architecture

This repository contains the foundational full-stack skeleton with:
- **Backend API**: Python FastAPI with modular API v1 routing and CORS configuration.
- **Database & Migrations**: SQLAlchemy ORM with Alembic migrations support for PostgreSQL.
- **Frontend SPA**: Minimal and functional React.js client (bootstrapped via Vite) with decoupled API services.
- **Resilient Health Probe**: Health check endpoint (`/api/v1/health`) that checks both server status and PostgreSQL connectivity without breaking the app if the database is offline.
- **Automated Tests**: Pytest suite verifying root and health endpoints.

---

## Directory Structure

```text
YATRA360/
├── backend/
│   ├── alembic/                 # Alembic database migration scripts & environment
│   │   ├── versions/            # Migration version files
│   │   └── env.py               # Configured to load app settings & metadata
│   ├── app/
│   │   ├── api/                 # API routes
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py # GET /api/v1/health endpoint
│   │   │       └── router.py    # Aggregated v1 router
│   │   ├── core/                # Application configuration & DB engine
│   │   │   ├── config.py        # Pydantic Settings (.env loader)
│   │   │   └── database.py      # SQLAlchemy engine, session maker, and DB probe
│   │   ├── models/              # SQLAlchemy ORM models (placeholder for future models)
│   │   ├── schemas/             # Pydantic request/response validation schemas
│   │   │   └── health.py        # Health response schema
│   │   ├── services/            # Business logic, scoring, and external API stubs
│   │   └── main.py              # FastAPI app initialization, middleware & routes
│   ├── tests/
│   │   └── test_health.py       # Pytest tests for API health
│   ├── .env.example             # Backend environment template
│   ├── alembic.ini              # Alembic migration configuration
│   ├── requirements.txt         # Pinned backend dependencies
│   └── run.py                   # Development server runner (port 8000)
├── frontend/
│   ├── src/
│   │   ├── api/                 # Decoupled network layer (no business logic in UI)
│   │   │   ├── apiClient.js     # Configured fetch wrapper
│   │   │   └── healthService.js # Health service calls
│   │   ├── components/
│   │   │   └── Header.jsx       # Header & navigation component
│   │   ├── pages/
│   │   │   └── Home.jsx         # Status dashboard & architecture overview
│   │   ├── styles/
│   │   │   ├── App.css          # Minimal, clean responsive styles
│   │   │   └── index.css        # Base reset
│   │   ├── App.jsx              # Main app view
│   │   └── main.jsx             # React entry point
│   ├── .env.example             # Frontend environment template
│   ├── index.html               # HTML document template
│   ├── package.json             # NPM dependencies & scripts
│   └── vite.config.js           # Vite dev & build configuration
├── alembic.ini                  # Root Alembic configuration wrapper
└── README.md                    # Project documentation & run guide
```

---

## Prerequisites

- **Python**: 3.10 or newer (tested on Python 3.14)
- **Node.js**: 18.x or newer (tested on Node v24.x)
- **PostgreSQL**: 14+ (optional for testing the skeleton; the backend will boot in `degraded` health status if PostgreSQL is not yet running)

---

## Setup & Running the Application

### 1. Backend Setup

Open a terminal in the project root:

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create a virtual environment (if not already created)
python -m venv venv

# 3. Activate virtual environment:
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# 4. Install backend dependencies
pip install -r requirements.txt

# 5. Configure environment variables
# Copy .env.example to .env
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS

# 6. Start the FastAPI development server
python run.py
```

The backend will be live at `http://127.0.0.1:8000`.

- Interactive API Docs (Swagger UI): [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
- Alternative API Docs (ReDoc): [http://127.0.0.1:8000/api/v1/redoc](http://127.0.0.1:8000/api/v1/redoc)
- Health Check Endpoint: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

#### Database Migrations (Alembic)

When your PostgreSQL instance is running and models are defined:

```bash
# Generate a migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

---

### 2. Frontend Setup

Open a separate terminal in the project root:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment variables (defaults to http://127.0.0.1:8000/api/v1)
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS

# 4. Start the Vite development server
npm run dev
```

The frontend will start at `http://localhost:5173`.

---

## How to Test

### Automated Backend Tests

Run pytest from the backend virtual environment:

```bash
cd backend
pytest tests -v
```

This will run:
- `test_root_endpoint`: Confirms root route returns 200 and API paths.
- `test_health_endpoint`: Confirms `/api/v1/health` returns status code 200, valid schema, and reports database connectivity.

### Manual End-to-End Verification

1. Start the backend: `cd backend && python run.py`.
2. Start the frontend: `cd frontend && npm run dev`.
3. Open `http://localhost:5173` in your browser.
4. Check the **System Health & Connectivity** card:
   - If the backend is running, the card displays **HEALTHY** or **DEGRADED** (if PostgreSQL service is offline).
   - Click **Refresh Status** to verify dynamic polling.
   - Click **API Docs ↗** in the top navigation to view the Swagger interactive API explorer.

---

## Architecture Rules & Next Modules

1. **Separation of Concerns**:
   - UI components in `frontend/src/pages/` and `components/` never make raw HTTP calls or contain business logic.
   - All external communication goes through `frontend/src/api/`.
2. **Upcoming Modules**:
   - User Registration, JWT Authentication & Role-Based Access Control.
   - Destination Database schema & initial seeding.
   - Transparent Multi-Factor Destination Scoring Engine.
   - Overcrowding Detection & Alternative Destination Recommender.
   - Leaflet / OpenStreetMap visual integration.
