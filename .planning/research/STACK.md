# Technology Stack: React + FastAPI Layer

**Project:** Gaucho Course Optimizer — Web Frontend + API Layer
**Researched:** 2026-03-30
**Overall confidence:** HIGH (all major decisions verified against official docs and current sources)

---

## Context

This milestone adds a React SPA + FastAPI REST layer on top of an existing Python 3.12 / SQLAlchemy / PostgreSQL backend. The existing ETL pipeline, APScheduler jobs, and database schema are **not touched**. FastAPI replaces only the Streamlit query layer; React replaces the Streamlit UI.

**Deployment target:** Vercel (React) + Render (FastAPI) — free tier both.

---

## Recommended Stack

### Backend — FastAPI Layer

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI | 0.115.x | REST API framework | Latest stable (0.135.x exists but 0.115.x is battle-tested LTS-equivalent; either works). Native async, automatic OpenAPI docs, first-class Pydantic v2 integration. Matches existing Python 3.12 runtime. |
| Pydantic v2 | 2.x (bundled with FastAPI) | Request validation, response serialization | Already bundled; 5-10x faster than Pydantic v1. Use for all response schemas — keeps API contract explicit. |
| pydantic-settings | 2.x | Environment variable management | Replaces raw `os.environ.get()` scattered through existing code. BaseSettings + `SettingsConfigDict(env_file=".env")` gives type-safe config with validation at startup. |
| uvicorn | 0.32.x | ASGI server | Required runtime for FastAPI. On Render free tier: single worker, `uvicorn main:app --host 0.0.0.0 --port $PORT`. Gunicorn multi-worker is NOT beneficial on free tier's 0.1 CPU — it adds overhead without throughput gain. |
| python-multipart | 0.0.9+ | Form data parsing | Required if any form inputs needed (search box POST). FastAPI dependency. |

**What NOT to use on the backend:**
- **Gunicorn + multiple workers on Render free tier** — Render free tier has 0.1 CPU and 512 MB RAM. Multiple Gunicorn workers will OOM-kill each other. Use single `uvicorn` directly.
- **Async SQLAlchemy migration** — The existing code uses sync SQLAlchemy 2.x. Migrating to `asyncpg` + async sessions is a significant rewrite with high risk and marginal benefit for this traffic level. Keep sync; use FastAPI's `run_in_executor` pattern if you hit blocking issues.
- **SQLModel** — Adds another abstraction layer over existing SQLAlchemy models. Don't use; map existing models to Pydantic response schemas manually.
- **FastAPI background tasks for ETL** — APScheduler already handles this. Don't duplicate scheduling in FastAPI.

### Database — PostgreSQL Hosting (Critical Decision)

| Option | Free Tier | Expiry | Recommendation |
|--------|-----------|--------|----------------|
| **Neon** | 0.5 GB storage, 100 CU-hrs/month, scale-to-zero | **Never expires** | **USE THIS** |
| Render PostgreSQL | 1 GB | **Expires in 30 days** (reduced from 90 days as of May 2024) | Do not use as primary |
| Supabase | 500 MB | Never expires (pauses after 1 week inactivity) | Second choice |

**Use Neon.** Render's free PostgreSQL now expires after 30 days — your database gets deleted. You would need to recreate it monthly and re-run the full ETL pipeline. Neon is a persistent, serverless PostgreSQL with a standard connection string compatible with the existing `psycopg2-binary` driver. No code changes required other than `DATABASE_URL`.

**Neon connection note:** Neon scales to zero after inactivity. First connection after idle may take 1-2 seconds. This is acceptable for a student tool. The FastAPI app will handle connection pool reconnect automatically via SQLAlchemy's `pool_pre_ping=True`.

### Frontend — React SPA

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| React | 19.x | UI framework | Stable as of Dec 2024; React 19 concurrent features (useTransition, Suspense) are beneficial for search UX. `@types/react@^19` required. |
| TypeScript | 5.7.x | Type safety | Standard for any non-trivial React app in 2025. Catches API contract mismatches at compile time — critical since FastAPI schemas can change. |
| Vite | 8.x | Build tool | Current stable (8.0.2, March 2026). Rolldown-based, 10-30x faster builds than Vite 5. Use `npm create vite@latest -- --template react-ts`. |
| TanStack Query (React Query) | v5.x | Server state management | The correct choice for a read-heavy SPA hitting a REST API. Handles caching, background refetch, stale-while-revalidate, loading/error states. Replaces manual `useEffect` + `useState` fetch patterns entirely. Use `@tanstack/react-query@^5`. |
| Axios | 1.7.x | HTTP client | Pair with TanStack Query as the fetch function. Axios provides an instance with `baseURL` configured once, interceptors for error handling, and cleaner TypeScript types than raw `fetch`. Define one `api.ts` file with `axios.create({ baseURL: import.meta.env.VITE_API_URL })`. |
| React Router | 6.x (v6.28+) | Client-side routing | Needed for `/course/:id` professor detail pages. v6 with `createBrowserRouter` is the current pattern. |
| Tailwind CSS | 4.x | Utility CSS | Tailwind v4 ships with a new CSS-first config (no `tailwind.config.js` required). Faster PostCSS pipeline. |
| shadcn/ui | latest | Component library | Copy-paste components built on Radix UI + Tailwind. Not a dependency — components live in your repo. Use for: Command (search autocomplete), Card (professor cards), Badge (score badges), Skeleton (loading states). Zero bundle bloat for unused components. |

**What NOT to use on the frontend:**
- **Next.js** — SSR/SSG adds complexity and a Node.js server process, which you don't need and Vercel would count as serverless function invocations. This is a pure SPA hitting a FastAPI backend. Plain React + Vite is correct.
- **Redux or Zustand for server state** — TanStack Query IS the state manager for server data. Don't add Redux. Zustand is only needed if you add complex local UI state (weight sliders synced across many components); defer that decision.
- **Material UI or Ant Design** — Large bundle sizes, opinionated styling that fights Tailwind. shadcn/ui is the correct pairing.
- **React Query v4** — v5 has breaking API changes. Start on v5. The `useQuery` API simplification (single object arg) is v5 standard.

### Charts — Grade Distribution

**Use Recharts 2.x.**

| Library | Bundle size | Histograms | React integration | Verdict |
|---------|-------------|------------|-------------------|---------|
| **Recharts** | ~230 KB | BarChart with custom bins | Native React components | **USE THIS** |
| Nivo | ~400 KB+ | Good, but heavy | Wrapper-based | Too heavy for a free-tier SPA |
| Chart.js + react-chartjs-2 | ~200 KB | Good | Imperative, less React-native | Worse DX |
| Victory | ~400 KB+ | Good | React-native | Oversized |

Recharts uses SVG, is composed entirely of React components, and has a `<BarChart>` that directly renders grade distribution data (A/B/C/D/F counts as categories). The existing Plotly charts in the Python backend provide the data shape; map those directly to Recharts `data={[{grade: 'A', count: 42}, ...]}`.

Install: `npm install recharts`

---

## CORS Configuration

This is the most common production failure point for React + FastAPI on separate domains.

**FastAPI side (`main.py`):**

```python
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "https://gaucho-course-optimizer.vercel.app",  # production Vercel URL
    "http://localhost:5173",                         # Vite dev server
]

# Add VITE_FRONTEND_URL from env for dynamic Vercel preview URLs
import os
if os.environ.get("FRONTEND_URL"):
    origins.append(os.environ["FRONTEND_URL"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,   # No auth cookies — keep False
    allow_methods=["GET"],     # Read-only API — restrict to GET only
    allow_headers=["*"],
)
```

**Critical:** Do NOT use `allow_origins=["*"]` in production. List your exact Vercel domain. Vercel preview deployments get random URLs (e.g., `gaucho-course-optimizer-abc123.vercel.app`) — you either need to add them manually or use an env var. For a student project, adding the stable production URL plus localhost is sufficient.

---

## Environment Variables

### FastAPI (Render)

Set these in Render dashboard under "Environment":

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | Neon connection string | Format: `postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require` — note `?sslmode=require` required for Neon |
| `RMP_AUTH_TOKEN` | RMP GraphQL token | Existing variable, move out of `.env` |
| `FRONTEND_URL` | `https://gaucho-course-optimizer.vercel.app` | For dynamic CORS origin addition |
| `ENVIRONMENT` | `production` | Gate debug behavior |

**pydantic-settings pattern (`config.py`):**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    rmp_auth_token: str = ""
    frontend_url: str = "http://localhost:5173"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### React (Vercel)

Vercel env vars must be prefixed with `VITE_` to be exposed to the browser bundle.

| Variable | Value | Where to set |
|----------|-------|--------------|
| `VITE_API_URL` | `https://your-app.onrender.com` | Vercel dashboard → Settings → Environment Variables |

**`api.ts`:**
```typescript
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 15000,  // 15s — accounts for Render cold start
})
```

**Vercel SPA routing (`vercel.json` in repo root):**
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```
This is required for React Router deep links to work. Without it, refreshing `/course/CS111` returns a 404.

---

## Deployment Configuration

### Render (FastAPI)

**Service type:** Web Service
**Language:** Python 3
**Build command:** `pip install -r requirements.txt`
**Start command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

Adjust `api.main:app` to match your module path.

**`render.yaml` (optional, for IaC):**
```yaml
services:
  - type: web
    name: gaucho-course-optimizer-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: RMP_AUTH_TOKEN
        sync: false
      - key: FRONTEND_URL
        value: https://gaucho-course-optimizer.vercel.app
    plan: free
```

**Cold start mitigation:** Render free tier spins down after 15 minutes of inactivity. First request after idle takes 30-60 seconds. Mitigations:

1. Add a `/health` endpoint that returns `{"status": "ok"}` (lightweight, no DB query)
2. Use UptimeRobot (free) to ping `/health` every 5 minutes — keeps the service awake, stays within 750 hr/month free limit (5-min pings = 8,928 requests/month, negligible)
3. In `api.ts` on the frontend, set `timeout: 15000` to survive the cold start on the rare case a user hits a freshly-spun-down instance

### Vercel (React)

**Framework preset:** Vite (auto-detected)
**Build command:** `npm run build` (auto-detected)
**Output directory:** `dist` (auto-detected by Vite preset)
**Install command:** `npm install`

No additional config needed beyond the `vercel.json` rewrite rule above.

Free tier: 100 GB bandwidth/month, unlimited deployments. Sufficient for a student tool.

---

## FastAPI Project Structure

```
api/
├── main.py          # FastAPI app, lifespan, middleware
├── config.py        # pydantic-settings Settings class
├── dependencies.py  # DB session dependency (wraps existing db/connection.py)
├── routers/
│   ├── courses.py   # GET /courses/search?q=...
│   └── professors.py # GET /courses/{dept}/{num}/professors
└── schemas/
    ├── course.py    # Pydantic response models
    └── professor.py # Pydantic response models
```

The `dependencies.py` wraps the **existing** `db/connection.py` session factory — do not rewrite it. Expose it as a FastAPI `Depends()` injectable:

```python
# dependencies.py
from db.connection import SessionLocal
from typing import Generator

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This preserves the existing sync SQLAlchemy session without any migration risk.

---

## Installation

### FastAPI additions to `requirements.txt`

```
fastapi>=0.115.0,<1.0
uvicorn>=0.32.0,<1.0
pydantic-settings>=2.5.0,<3.0
python-multipart>=0.0.9
```

### React frontend (new directory, e.g. `frontend/`)

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install

# Data fetching
npm install @tanstack/react-query axios

# Routing
npm install react-router-dom

# Charts
npm install recharts

# UI — Tailwind v4
npm install -D tailwindcss @tailwindcss/vite

# shadcn/ui (CLI-based, adds components to src/components/ui/)
npx shadcn@latest init
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| API framework | FastAPI | Django REST Framework | DRF is heavier, less aligned with existing non-Django codebase |
| API framework | FastAPI | Flask | No automatic OpenAPI docs, less type-safe, manual validation |
| Frontend framework | React + Vite | Next.js | SSR adds Node.js server cost; this is a read-only SPA, no SEO required |
| State management | TanStack Query | SWR | SWR is simpler but has fewer features (no mutations, less cache control). TanStack Query v5 is the ecosystem standard. |
| HTTP client | Axios | native fetch | fetch requires manual error handling and has no instance/interceptor pattern. Axios is better for a multi-endpoint app. |
| Charts | Recharts | Nivo | Nivo bundle is ~2x larger. Recharts is sufficient for bar charts. |
| Charts | Recharts | Plotly.js (React) | Plotly React wrapper is 3 MB+. Unacceptable for a free-tier SPA. |
| DB hosting | Neon | Render PostgreSQL | Render free DB expires every 30 days since May 2024. |
| Component library | shadcn/ui | MUI / Ant Design | Both are large bundle dependencies. shadcn copies components into your codebase — zero runtime overhead for unused parts. |

---

## Sources

- FastAPI release notes: https://fastapi.tiangolo.com/release-notes/
- FastAPI CORS docs: https://fastapi.tiangolo.com/tutorial/cors/
- FastAPI lifespan events: https://fastapi.tiangolo.com/advanced/events/
- FastAPI deploy on Render: https://render.com/docs/deploy-fastapi
- FastAPI production best practices (Render): https://render.com/articles/fastapi-production-deployment-best-practices
- Render free PostgreSQL 30-day expiry changelog: https://render.com/changelog/free-postgresql-instances-now-expire-after-30-days-previously-90
- Neon free tier details: https://neon.com/docs/introduction/plans
- TanStack Query v5 announcement: https://tanstack.com/blog/announcing-tanstack-query-v5
- TanStack Query docs: https://tanstack.com/query/latest
- Vite 8.0 announcement: https://vite.dev/blog/announcing-vite8
- shadcn/ui Vite setup: https://ui.shadcn.com/docs/installation/vite
- Render cold start mitigation: https://medium.com/@saveriomazza/how-to-keep-your-fastapi-server-active-on-renders-free-tier-93767b70365c
- Vercel SPA routing: https://medium.com/today-i-solved/deploy-spa-with-react-router-to-vercel-d10a6b2bfde8
- LogRocket React chart libraries 2025: https://blog.logrocket.com/best-react-chart-libraries-2025/
- pydantic-settings docs: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

*Researched: 2026-03-30*
