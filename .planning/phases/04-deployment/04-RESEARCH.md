# Phase 4: Deployment - Research

**Researched:** 2026-04-01
**Domain:** Vercel (SPA hosting), Render (Python/FastAPI free-tier), CORS configuration, UptimeRobot cold-start mitigation
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEPLOY-01 | Student can access the React SPA at a public Vercel URL with React Router deep links working (via `vercel.json` rewrite rule) | vercel.json SPA rewrite is already present in `frontend/`; Vercel root directory must be set to `frontend/` at import time |
| DEPLOY-02 | Student's browser can make API calls to the Render service without CORS errors — `allow_origins` set to exact Vercel production URL + `http://localhost:5173` | CORS middleware already added in `api/main.py`; needs production origin added via `ALLOWED_ORIGINS` env var read from pydantic-settings |
| DEPLOY-03 | Render API service stays warm during UCSB registration hours — UptimeRobot pings `GET /health` every 10 minutes to prevent cold starts | `/health` endpoint exists with no DB query; Render spins down after 15 min; UptimeRobot free tier supports 5-min intervals |
</phase_requirements>

---

## Summary

Phase 4 deploys two already-built services: the Vite/React SPA to Vercel and the FastAPI backend to Render's free web service tier. The infrastructure is almost entirely click-through dashboard work plus a small amount of code changes — specifically updating the CORS configuration to read allowed origins from an environment variable so the production Vercel URL can be added without hardcoding it.

The most important pre-work is updating `api/main.py` and `api/config.py` so `allow_origins` is driven by an `ALLOWED_ORIGINS` env var (comma-separated string, parsed via a `field_validator`). The current code hardcodes only localhost origins — adding the Vercel production URL in code before deploy is the wrong pattern; it must come from an env var.

Render's free web service tier spins down after 15 minutes of inactivity and takes ~60 seconds to wake up. UptimeRobot's free plan pings every 5 minutes, which is well within the 15-minute threshold. The `/health` endpoint is already correctly implemented (no DB dependency), making it a perfect keep-warm target.

**Primary recommendation:** Update CORS config to env-var-driven before deploying; set Render root directory to the repo root (not a subdirectory) since `api/` imports from `db/` and `etl/` which live at the repo root; set Vercel root directory to `frontend/`.

---

## Standard Stack

### Core

| Service | Version/Tier | Purpose | Why Standard |
|---------|-------------|---------|--------------|
| Vercel | Free Hobby tier | SPA static hosting + CDN | Zero-config Vite detection, automatic `vercel.json` SPA rewrites, GitHub auto-deploy |
| Render | Free Web Service | FastAPI ASGI hosting | Free Python runtime, auto-deploy from GitHub, `$PORT` injection, uvicorn support |
| UptimeRobot | Free tier (50 monitors) | Cold-start prevention | Free HTTP monitoring, 5-min ping interval beats Render's 15-min spin-down threshold |
| Neon PostgreSQL | Free tier (already set up) | Persistent data | Already seeded and configured — no changes needed in this phase |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| pydantic-settings `field_validator` | Parse comma-separated `ALLOWED_ORIGINS` env var into `list[str]` | Needed to make CORS origins env-configurable without a JSON list |
| Render Dashboard env vars | Store `DATABASE_URL`, `ALLOWED_ORIGINS`, `RMP_AUTH_TOKEN` secrets | Never commit secrets; add via dashboard "Add Environment Variable" |
| Vercel Dashboard env vars | Store `VITE_API_URL` (production Render URL) | Baked into static bundle at build time — must be set before first deploy |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Render free web service | Railway, Fly.io | Both require credit card or paid plan for always-on; Render free matches the project constraint |
| UptimeRobot | Cron-job.org, GitHub Actions scheduled ping | UptimeRobot has dedicated UI and alerting; simpler setup for this use case |
| Vercel | Netlify | Both are equivalent for Vite SPAs; Vercel auto-detects Vite framework, slightly simpler |

---

## Architecture Patterns

### Deployment Topology

```
GitHub repo (monorepo)
├── frontend/          → Vercel Web Service
│   └── Root Dir: frontend/
│   └── Build: npm run build
│   └── Output: dist/
│   └── vercel.json: SPA rewrite (already present)
│
└── (repo root)        → Render Web Service
    └── Root Dir: (repo root — NOT api/)
    └── Build: pip install -r requirements.txt
    └── Start: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Pattern 1: Vercel SPA Deployment with Subdirectory Root

**What:** Import GitHub repo into Vercel, set Root Directory to `frontend/` during import wizard. Vercel runs `npm run build` and serves `dist/`. The `vercel.json` rewrite rule already present handles SPA deep links.

**When to use:** Any time the frontend lives in a subdirectory of a monorepo.

**Critical:** `VITE_API_URL` must be added to Vercel's Environment Variables dashboard (Settings → Environment Variables → Production) BEFORE the first production deployment, because Vite bakes env vars into the static bundle at build time. Changing this after the first deploy requires a redeploy.

```json
// frontend/vercel.json — already present, no changes needed
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```
Source: [Vite on Vercel docs](https://vercel.com/docs/frameworks/frontend/vite)

### Pattern 2: Render Web Service with Repo-Root Start Command

**What:** Create a Render Web Service pointing at the GitHub repo. Set Root Directory to empty (repo root). This is critical because `api/main.py` imports `api.routers` which import `db.connection` and `etl.scoring` — those modules live at the repo root. Setting root directory to `api/` would break all cross-package imports.

**Start command:**
```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

Note: The module path is `api.main:app` (dot-separated package path from repo root), not `main:app`.

**Build command:**
```bash
pip install -r requirements.txt
```

Source: [Render deploy-fastapi docs](https://render.com/docs/deploy-fastapi), [Render monorepo docs](https://render.com/docs/monorepo-support)

### Pattern 3: CORS Origins from Environment Variable

**What:** Update `api/config.py` to add an `allowed_origins` field with a `field_validator` that parses a comma-separated string into a list. Update `api/main.py` to read `settings.allowed_origins` instead of a hardcoded list.

**When to use:** Any production deployment where the allowed origin (Vercel URL) is not known at code-write time.

```python
# api/config.py — updated
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    database_url: str = "postgresql://gco:gco@localhost:5432/gco"
    rmp_auth_token: str = ""
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v
```

```python
# api/main.py — updated middleware block
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

On Render, set environment variable:
```
ALLOWED_ORIGINS=https://gaucho-course-optimizer.vercel.app,http://localhost:5173
```

Source: [FastAPI Settings docs](https://fastapi.tiangolo.com/advanced/settings/), pydantic-settings field_validator pattern

### Pattern 4: UptimeRobot HTTP Monitor Setup

**What:** Create a free UptimeRobot account, add an HTTP(s) monitor pointing at `https://<render-service>.onrender.com/health`, set interval to 5 minutes.

**Why 5 minutes works:** Render spins down after 15 minutes of inactivity. A 5-minute ping interval means the service never reaches 15 minutes idle — it receives a request every 5 minutes. UptimeRobot free plan supports exactly 5-minute intervals (minimum on free tier).

**The requirement says 10-minute interval** — this also works (10 < 15 minutes) and is a valid conservative choice. 5 minutes provides more margin.

Steps:
1. Sign up at uptimerobot.com (free, no credit card)
2. Click "+ Add New Monitor"
3. Monitor Type: HTTP(s)
4. Friendly Name: "Gaucho Course Optimizer API"
5. URL: `https://<your-render-service>.onrender.com/health`
6. Monitoring Interval: 5 minutes (or 10 minutes per DEPLOY-03)
7. Click "Create Monitor"

Source: [UptimeRobot setup guide](https://help.uptimerobot.com/en/articles/11358364-how-to-create-your-first-monitor-on-uptimerobot-quick-setup-guide)

### Anti-Patterns to Avoid

- **Hardcoding the Vercel production URL in `api/main.py`:** The URL is not known until after Vercel deployment. Read it from `ALLOWED_ORIGINS` env var instead.
- **Setting Render root directory to `api/`:** Breaks cross-package imports (`db/`, `etl/`). Keep root at repo root.
- **Using `allow_origins=["*"]` in production:** Browsers reject wildcard origins when `allow_credentials=True`. Even without credentials, it violates DEPLOY-02's "no wildcard origins" requirement.
- **Setting `VITE_API_URL` after the first Vercel deploy without rebuilding:** Vite bakes env vars at build time. The value must be present before running `npm run build`. Vercel must be told to redeploy after the variable is added.
- **Forgetting `allow_methods=["GET"]`:** All production endpoints are GET-only. Restricting methods tightens the CORS policy.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Uptime monitoring / keep-warm pings | Custom cron script or GitHub Actions scheduled workflow | UptimeRobot free HTTP monitor | GH Actions has cold-start issues itself; UptimeRobot is purpose-built, has alerting, and is free |
| SPA deep link routing on Vercel | Custom server or redirect rules | `vercel.json` `rewrites` (already present) | The rewrite is one JSON line; hand-rolling misses edge cases |
| Environment variable parsing (list from string) | `os.environ.get(...).split(",")` in `main.py` | pydantic-settings `field_validator` | Centralizes config, handles `.env` file for local dev, validates types |

**Key insight:** All three deployment requirements have free-tier, purpose-built solutions that require configuration, not code. The only real code change is the CORS origins env-var migration in `api/config.py`.

---

## Common Pitfalls

### Pitfall 1: Render Start Command Module Path
**What goes wrong:** Using `uvicorn main:app` instead of `uvicorn api.main:app` — the FastAPI app is in `api/main.py`, not `main.py`. With repo root as the working directory, the module reference must use dot notation.
**Why it happens:** Render's own FastAPI example assumes a flat repo where `main.py` is at root.
**How to avoid:** Always use `api.main:app` in the start command when root directory is the repo root.
**Warning signs:** Render deploy log shows `ModuleNotFoundError: No module named 'api'` or `Could not find module 'main'`.

### Pitfall 2: VITE_API_URL Baked at Build Time
**What goes wrong:** Student opens the Vercel URL and all API calls go to `undefined` or `localhost` because `VITE_API_URL` was not set in Vercel's dashboard before the build ran.
**Why it happens:** Vite replaces `import.meta.env.VITE_*` values statically during the build. If the variable is missing at build time, it resolves to `undefined` in the bundle.
**How to avoid:** Add `VITE_API_URL` to Vercel Environment Variables (Production environment) BEFORE deploying, or trigger a redeploy after adding it.
**Warning signs:** Browser console shows `fetch('undefined/courses/search?q=...')` or CORS errors to `localhost:8000`.

### Pitfall 3: Render Free Tier 750 Hour Monthly Limit
**What goes wrong:** Service goes down mid-registration period because it exceeded 750 instance-hours for the month (~31 days * 24 hours = 744 hours, which means always-on is just within the limit).
**Why it happens:** Keeping the service alive 24/7 via UptimeRobot consumes ~720 hours/month (30 days), which is within the 750-hour cap. However, heavy use or multiple services on the same account can exhaust hours.
**How to avoid:** Run UptimeRobot only during UCSB registration periods (not 24/7) if monthly hour budget is a concern. For a single service, 720 hours/month is within the 750-hour cap.
**Warning signs:** Render dashboard shows "Service suspended — monthly hours limit reached."

### Pitfall 4: CORS Origin Must Match Exactly (Including Protocol and No Trailing Slash)
**What goes wrong:** CORS error in browser even though the origin looks correct — e.g., `https://gaucho-course-optimizer.vercel.app/` (trailing slash) vs `https://gaucho-course-optimizer.vercel.app` (no slash).
**Why it happens:** The `Origin` header browsers send does not include a trailing slash. The CORS middleware does exact string matching.
**How to avoid:** Set `ALLOWED_ORIGINS` without a trailing slash. Verify with browser DevTools → Network → request headers → `Origin` value.
**Warning signs:** Browser console: "has been blocked by CORS policy: The 'Access-Control-Allow-Origin' header has a value '...' that is not equal to the supplied origin."

### Pitfall 5: Render First Deploy Takes 5-10 Minutes
**What goes wrong:** After clicking "Deploy," the dashboard shows "In Progress" for longer than expected. Developers assume it failed and click deploy again, creating a queue.
**Why it happens:** First deploy installs all Python dependencies (sqlalchemy, pandas, scikit-learn, etc.) — a large dependency tree. Subsequent deploys are faster due to caching.
**How to avoid:** Wait for the deploy log to show "==> Your service is live" before testing the URL. Normal first-deploy time is 5-10 minutes.

---

## Code Examples

### Updated api/config.py (CORS origins from env var)

```python
# Source: pydantic-settings field_validator pattern
# https://fastapi.tiangolo.com/advanced/settings/
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    database_url: str = "postgresql://gco:gco@localhost:5432/gco"
    rmp_auth_token: str = ""
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()
```

### Updated api/main.py (use settings.allowed_origins)

```python
# Source: FastAPI CORS docs + project pattern
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import health, courses, professors
from api.config import settings

app = FastAPI(
    title="Gaucho Course Optimizer API",
    description="REST API exposing UCSB professor rankings by Gaucho Score",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(professors.router, prefix="/professors", tags=["professors"])
```

### Render render.yaml (optional IaC, placed at repo root)

```yaml
# Source: https://render.com/docs/blueprint-spec
# Place at repo root if using Render Blueprint (optional — dashboard config is sufficient)
services:
  - name: gaucho-course-optimizer-api
    type: web
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false        # Set manually in Render dashboard (secret)
      - key: ALLOWED_ORIGINS
        sync: false        # Set manually after Vercel URL is known
      - key: RMP_AUTH_TOKEN
        sync: false        # Set manually in Render dashboard (secret)
```

### Local .env additions for development

```bash
# .env (already gitignored)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | `npm run build` (Vercel) | ✓ (local) | v20.9.0 | Vercel provides Node in cloud |
| npm | Frontend install | ✓ (local) | 10.1.0 | Vercel provides npm in cloud |
| Git | GitHub push to trigger deploys | ✓ | 2.44.0 | — |
| Vercel account | Frontend hosting | External service | Free Hobby | — |
| Render account | Backend hosting | External service | Free tier | — |
| UptimeRobot account | Cold-start prevention | External service | Free plan | cron-job.org as fallback |
| GitHub repo (public or Vercel-connected) | Auto-deploy trigger | Assumed present | — | Manual CLI deploy |

**Missing dependencies with no fallback:** None — all required tools are either already available or are external services with free tiers.

**Missing dependencies with fallback:**
- UptimeRobot: If unavailable, use cron-job.org (free, 1-minute minimum interval) as HTTP ping alternative.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (backend) + Vitest (frontend) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` / `frontend/vitest.config.ts` |
| Quick run command (backend) | `pytest tests/test_api/ -x -q` |
| Quick run command (frontend) | `cd frontend && npm test` |
| Full suite command | `pytest -x -q && cd frontend && npm test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEPLOY-01 | SPA deep links return 200 (not 404) at `/course/:id` via vercel.json rewrite | smoke (manual, Vercel preview URL) | Manual browser check — cannot automate pre-deploy | N/A — post-deploy check |
| DEPLOY-02 | CORS headers present on API responses from production origin | smoke (manual curl/browser DevTools) | `curl -H "Origin: https://<vercel-url>" https://<render-url>/health -v` | N/A — post-deploy check |
| DEPLOY-02 | `settings.allowed_origins` correctly parses comma-separated env var | unit | `pytest tests/test_config.py::test_allowed_origins_parsing -x` | ❌ Wave 0 |
| DEPLOY-03 | `/health` endpoint returns `{"status": "ok"}` without DB | unit (already covered) | `pytest tests/test_api/ -k health -x` | ✅ (existing test_courses_router.py / test suite) |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q -k "not integration"` (backend unit tests)
- **Per wave merge:** `pytest tests/ -x -q && cd frontend && npm test`
- **Phase gate:** Full suite green + manual smoke test of live Vercel and Render URLs before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_config.py` — unit test for `Settings.parse_origins` field_validator: verifies comma-separated string parses correctly, single origin works, default localhost list preserved when env var absent
- [ ] No other gaps — existing `/health` test covers DEPLOY-03 unit behavior; DEPLOY-01 and DEPLOY-02 are inherently post-deploy smoke tests

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Heroku free tier (dynos) | Render free web services | Heroku killed free tier Nov 2022 | Render is the de-facto replacement for free Python hosting |
| `allow_origins=["*"]` for "quick" dev | Explicit origin list from env var | CORS security best practice (always) | Wildcard breaks with `allow_credentials=True`; explicit list required for production |
| `process.env.REACT_APP_*` (CRA) | `import.meta.env.VITE_*` (Vite) | Vite became standard ~2021 | Must use `VITE_` prefix or variables are invisible to the app |

**Deprecated/outdated:**
- `port=80` in start command: Render injects `$PORT` (default 10000) — hardcoding 80 causes the service to never receive traffic. Always use `--port $PORT`.
- `allow_credentials=True` with wildcard origins: Browsers reject this combination per spec. Not applicable here (no auth), but worth noting.

---

## Open Questions

1. **Final Vercel production URL is not known until first deploy**
   - What we know: Vercel assigns `<project-name>.vercel.app` by default, but the slug may vary.
   - What's unclear: The exact URL cannot be pre-set in `ALLOWED_ORIGINS` on Render before the first Vercel deploy.
   - Recommendation: Deploy Vercel first (CORS errors are acceptable on first deploy — no backend calls yet), then copy the production URL, add it to Render's `ALLOWED_ORIGINS` env var, and redeploy Render. Alternatively, use a `*.vercel.app` wildcard ONLY during the brief setup window then tighten it.

2. **UCSB registration hours for targeted UptimeRobot scheduling**
   - What we know: UCSB pass times are Pacific time, staggered across students, typically morning/afternoon during registration week.
   - What's unclear: Exact hours vary each quarter. No fixed 9am-5pm schedule found in public docs.
   - Recommendation: Run UptimeRobot 24/7 (always-on uses ~720 hrs/month, within the 750-hour free cap for a single service). No time-scheduling needed; simpler and stays within budget.

3. **Python version specification on Render**
   - What we know: `pyproject.toml` requires `python >= 3.12`. Render's default Python version may differ.
   - What's unclear: Whether Render auto-detects `pyproject.toml` or requires a `.python-version` file.
   - Recommendation: Add a `.python-version` file containing `3.12.0` at the repo root as a precaution. This is universally recognized by Render, pyenv, and other tools.

---

## Sources

### Primary (HIGH confidence)
- [Vercel — Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite) — SPA rewrite config, env var handling, VITE_ prefix requirement
- [Render — Deploy FastAPI](https://render.com/docs/deploy-fastapi) — uvicorn start command, `$PORT` variable, build command
- [Render — Free tier limits](https://render.com/docs/free) — 15-minute spin-down, ~60 second wake-up, 750 hours/month cap
- [Render — Monorepo Support](https://render.com/docs/monorepo-support) — root directory configuration, relative command paths
- [Render — Environment Variables](https://render.com/docs/configure-environment-variables) — secret values via dashboard, `sync: false` pattern
- [FastAPI — Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/) — pydantic-settings pattern for config

### Secondary (MEDIUM confidence)
- [UptimeRobot — Create Your First Monitor](https://help.uptimerobot.com/en/articles/11358364-how-to-create-your-first-monitor-on-uptimerobot-quick-setup-guide) — free tier supports 5-minute ping interval, 50 monitors
- [render-examples/fastapi render.yaml](https://github.com/render-examples/fastapi/blob/main/render.yaml) — official Render example confirms `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Multiple community sources confirming Render 15-minute inactivity → spin-down behavior

### Tertiary (LOW confidence)
- None — all critical claims verified via official documentation.

---

## Metadata

**Confidence breakdown:**
- Vercel SPA deployment: HIGH — verified via official Vite-on-Vercel docs; vercel.json rewrite already present in codebase
- Render FastAPI deployment: HIGH — verified via official Render deploy-fastapi docs and render-examples template
- CORS env-var pattern: HIGH — verified via FastAPI official settings docs + pydantic-settings field_validator
- UptimeRobot setup: MEDIUM — verified via official UptimeRobot help center; 5-min interval confirmed as free-tier minimum
- Render cold-start behavior: HIGH — verified via official Render free tier docs (15 min inactivity, ~60 sec wake-up)

**Research date:** 2026-04-01
**Valid until:** 2026-07-01 (90 days — Render/Vercel free tier terms are stable; check if Render changes free tier policy)
