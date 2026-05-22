# ⚡ Imperion Automation Platform

A **multi-tenant, production-grade AI automation & integration platform** for SMBs.
Connects lead capture → workflow automation → CRM sync → scheduling → notifications,
with a visual workflow builder, retries, audit logs, analytics, and AI-assisted workflow generation.

> Built as the Round-2 technical assessment for the AI Automation & Integration
> Internship at **Imperion Data Systems Pvt. Ltd.**

---

## 🚀 One-command Quickstart

```bash
git clone <this-repo>
cd imperion-automation
chmod +x start.sh
./start.sh
```

Then open:

| Service        | URL                              |
|----------------|----------------------------------|
| **Frontend**   | http://localhost:5173            |
| **Backend**    | http://localhost:8000            |
| **API Docs**   | http://localhost:8000/docs       |

### Demo credentials (seeded automatically)

| Workspace | Email                  | Password    |
|-----------|------------------------|-------------|
| Acme      | `admin@acme.com`       | password123 |
| Globex    | `admin@globex.com`     | password123 |

---

## ✅ Mandatory requirements — coverage map

| Requirement | Where it lives |
|-------------|----------------|
| **Multi-tenant workspaces** (separate settings/workflows/dashboards per client) | `models/models.py` → `Workspace`; every table has `workspace_id`; auth scopes JWT to a workspace |
| **≥ 4 real integrations** | `integrations/` — Email/Gmail (SMTP), Slack (webhook), Telegram (Bot API), Google Sheets (gspread), WhatsApp Cloud API, Google Calendar, generic Webhook, built-in CRM — **8 providers total** |
| **Trigger → Condition → Action → Follow-up builder** | `workflows/engine.py` (graph executor) + UI editor at `/workflows/:id` |
| **Automation engine** with retries, scheduling, queue, failure handling | Celery + Redis (`workers/tasks.py`), APScheduler (`workers/scheduler.py`), exponential backoff in `engine._execute_action_with_retry` |
| **Analytics dashboard** (leads, runs, conversions, latency, failures) | `/api/v1/analytics` + `frontend/pages/Dashboard.jsx` (charts) |
| **Admin panel** (logs, configs, trigger history) | `/admin` page — audit logs + webhook events with replay |
| **Reliability layer** (monitoring, audit, safe rollback) | `services/audit.py`, loguru file logs, `POST /workflows/:id/rollback`, `previous_graph` column |
| **Frontend + backend + DB deployment-ready** | `docker-compose.yml` brings up Postgres + Redis + FastAPI + Celery worker + React (nginx) |

## 🌟 Bonus features delivered

- ✅ **Node-chained workflow editor** (n8n-style graph) with JSON + visual preview
- ✅ **Webhook replay & retry queue** — `/admin` Webhook Events tab, plus durable storage
- ✅ **Lead scoring** (0-100 deterministic score) + **human-handoff flag**
- ✅ **AI-assisted workflow generation** (OpenAI if key set, else heuristic generator)
- ✅ **Slack / Telegram / WhatsApp alerts** as first-class integrations
- ✅ **Safe rollback** of workflow versions (previous_graph stored on every update)

---

## 🧱 Architecture

```
┌─────────────────┐      ┌──────────────────┐
│  React + Vite   │ ───► │   FastAPI App    │
│  (nginx, :5173) │ JWT  │     (:8000)      │
└─────────────────┘      └────────┬─────────┘
                                  │
              ┌───────────────────┼────────────────────┐
              ▼                   ▼                    ▼
        ┌──────────┐        ┌───────────┐       ┌────────────┐
        │ Postgres │        │   Redis   │       │APScheduler │
        │  (data)  │        │ (broker)  │       │ (in-proc)  │
        └──────────┘        └─────┬─────┘       └─────┬──────┘
                                  │                   │
                              ┌───▼─────────┐         │
                              │   Celery    │◄────────┘
                              │   Workers   │
                              └───┬─────────┘
                                  │
              ┌───────────────────┼───────────────────────────┐
              ▼                   ▼                           ▼
        ┌──────────┐        ┌──────────┐                ┌─────────┐
        │ Workflow │        │  Audit   │                │External │
        │  Engine  │───────►│   Log    │                │ APIs    │
        └──────────┘        └──────────┘                │(Slack..)│
                                                        └─────────┘
```

### Components

- **FastAPI backend** — REST API, JWT auth, multi-tenant isolation per request.
- **PostgreSQL** — workspaces, users, workflows, runs, leads, integrations, audit logs, webhook events, scheduled jobs.
- **Redis + Celery** — durable queue for async workflow execution with automatic retries.
- **APScheduler** — in-process scheduler that polls `scheduled_jobs` every 30 s and enqueues due workflows.
- **WorkflowEngine** (`app/workflows/engine.py`) — walks the workflow graph node-by-node, handles condition branching, per-node retries with exponential backoff, on-failure routes, context templating (`{{var}}`), and step-by-step logging.
- **Integrations layer** — pluggable `BaseIntegration` interface; each provider implements `execute(action, config, payload)`. New providers added by dropping a file in `app/integrations/` and registering in `__init__.py`.
- **React frontend** — Vite + Tailwind + Recharts. JWT auth context, axios with interceptor, polling dashboard.

---

## 🗂️ Project layout

```
imperion-automation/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routers (auth, workflows, leads, ...)
│   │   ├── core/            # config, db, security, logger
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── integrations/    # Email, Slack, Telegram, WhatsApp, Sheets, CRM, ...
│   │   ├── workflows/       # Workflow execution engine
│   │   ├── workers/         # Celery tasks + APScheduler
│   │   ├── services/        # audit, lead-scoring, ai-workflow
│   │   ├── main.py          # FastAPI entrypoint
│   │   └── seed.py          # Demo data seeder
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/           # Dashboard, Workflows, Leads, Integrations, Admin
│   │   ├── components/      # Layout (sidebar)
│   │   ├── context/         # AuthContext
│   │   └── services/api.js  # axios client
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── start.sh
└── README.md
```

---

## 🔌 API quick reference

All endpoints (except auth + public webhook) require `Authorization: Bearer <token>`.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/auth/signup` | Create workspace + admin user |
| POST | `/api/v1/auth/login` | Login → JWT |
| GET  | `/api/v1/workspace/me` | Current workspace info |
| GET  | `/api/v1/integrations` | List workspace integrations |
| POST | `/api/v1/integrations` | Add integration |
| POST | `/api/v1/integrations/{id}/test` | Send a test message |
| GET/POST | `/api/v1/workflows` | List / create workflows |
| PUT  | `/api/v1/workflows/{id}` | Update (bumps version, stores previous) |
| POST | `/api/v1/workflows/{id}/rollback` | Roll back to previous version |
| POST | `/api/v1/workflows/{id}/run` | Manually trigger a run |
| GET  | `/api/v1/workflows/{id}/runs` | Run history with step logs |
| GET/POST | `/api/v1/leads` | List / capture leads (auto-scored, auto-triggers workflows) |
| POST | `/api/v1/ai/generate-workflow` | AI-generate a workflow from English |
| POST | `/api/v1/webhooks/{slug}/{wf_id}` | **Public** webhook receiver |
| POST | `/api/v1/webhooks/events/{id}/replay` | Replay a stored event |
| GET  | `/api/v1/analytics` | Dashboard analytics |
| GET  | `/api/v1/analytics/audit-logs` | Audit trail |

Full interactive docs at <http://localhost:8000/docs>.

---

## 🎯 How a workflow runs (end-to-end)

1. Lead is captured (`POST /leads` or via the webhook URL).
2. The lead is scored and stored; any workflow with `trigger_type=lead_created` for that workspace is queued.
3. `execute_workflow_run` Celery task picks it up.
4. `WorkflowEngine` walks the graph node-by-node, accumulating context.
5. Each action node calls the matching integration with config (with `{{var}}` templating).
6. Failures are retried with exponential backoff (`base ^ attempt` seconds, up to `MAX_RETRIES`).
7. Step-by-step status and duration are persisted on the `WorkflowRun` row.
8. Dashboard polls `/analytics` and reflects the new data in ~10 s.

---

## 🛠️ Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# (Point DATABASE_URL/REDIS_URL to local Postgres/Redis or use SQLite by changing config)
uvicorn app.main:app --reload
# In another shell:
celery -A app.workers.celery_app.celery_app worker --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

---

## 📋 Environment variables

See `backend/.env.example`. All external integrations have **simulation fallback**:
if no API key is configured for Slack/Telegram/WhatsApp/Sheets/Calendar, the call is logged and reported as `simulated: true`. This means the platform is **fully demoable with zero external accounts**, while remaining production-ready when keys are supplied.

---

## 🎬 Demo video script (5-7 minutes)

A suggested flow for the demo video lives in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

## 📐 Architecture deep-dive

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 📜 License

Built for the Imperion Data Systems Round 2 technical assessment.
