# Architecture Deep Dive

## 1. Multi-tenancy model

Every domain table (`workflows`, `leads`, `integrations`, `workflow_runs`,
`audit_logs`, `webhook_events`, `scheduled_jobs`) has a `workspace_id` FK
to `workspaces`. The JWT issued at login carries the user's `workspace_id`,
and `app/api/deps.py:get_current_user` extracts the user; every router
scopes its query with `.filter(Table.workspace_id == user.workspace_id)`.

Result: a complete row-level tenant isolation — workspaces are never able
to read each other's data, and adding new workspaces is just a row insert.

## 2. Workflow representation

A workflow's `graph` is a JSON document:

```json
{
  "nodes": [
    { "id": "t1", "type": "trigger", "label": "Lead Created", "next": "a1" },
    { "id": "a1", "type": "action",  "label": "Save to CRM",
      "config": { "provider": "crm", "action": "upsert_lead" },
      "next": "c1" },
    { "id": "c1", "type": "condition", "label": "Needs human?",
      "config": { "field": "requires_human", "op": "eq", "value": true },
      "branches": { "true": "slack1", "false": "email1" } },
    ...
  ]
}
```

Each node has:
- `id`        — unique within the workflow
- `type`      — `trigger | condition | action | follow_up | delay`
- `config`    — provider-specific options
- `next`      — id of next node (for linear flow)
- `branches`  — `{true: id, false: id}` for conditions
- `on_failure` — id to jump to on error (optional)

## 3. Engine guarantees

- **Per-node retries** with exponential backoff (`RETRY_BACKOFF_BASE^attempt`).
- **Loop detection** — visited set per run.
- **Context accumulation** — each action's output is merged into context,
  available as `{{key}}` to downstream nodes.
- **Failure isolation** — `on_failure` lets a workflow gracefully degrade
  (e.g. fall back from WhatsApp to email).
- **Step logs** — every node's status, output and timestamp persisted on
  the `WorkflowRun` row → full forensics & auditability.

## 4. Async execution pipeline

```
HTTP / webhook / lead.create / scheduler tick
        │
        ▼
  WorkflowRun row (status=pending)
        │
        ▼  Celery .delay()
  execute_workflow_run task
        │
        ▼
  WorkflowEngine.execute()
        │  (per-node retries)
        ▼
  Integration.execute()  →  external service
```

If a task itself crashes (not just a node), Celery retries up to 3× with
10s delay — providing two layers of resilience.

## 5. Scheduling

`scheduled_jobs.next_run_at` is checked every 30s by APScheduler. When due:
- a new `WorkflowRun(status=pending)` is created;
- the task is `.delay()`-ed onto Celery;
- `next_run_at` is bumped by the parsed interval (`every:N` seconds).

## 6. Webhook reliability

Every inbound webhook is **persisted first** (`webhook_events`), then a run
is enqueued. This gives us:
- **At-least-once processing** (we always have the payload to replay).
- **Replay API** — `POST /webhooks/events/{id}/replay` re-enqueues the run
  with the original payload.
- **Idempotency hook** — payload + headers stored, ready for de-dupe by
  signature/id in future.

## 7. Safe rollback

On every workflow update we copy the current `graph` into `previous_graph`
and bump `version`. `POST /workflows/{id}/rollback` swaps them — so even a
broken edit can be reverted instantly without consulting backups.

## 8. Audit & observability

- `audit_logs` row for every state-changing API call (create/update/delete
  on workflow / integration / lead, plus run trigger and rollback).
- Loguru structured logs to stdout + `logs/app.log` (10MB rotation).
- `/health` endpoint for liveness probes.
- All run durations and retry counts are stored → SLO dashboards possible.

## 9. Integration extensibility

Add a new provider in 3 steps:
1. Create `app/integrations/myprovider_integration.py` extending `BaseIntegration`.
2. Register in `app/integrations/__init__.py:REGISTRY`.
3. Use it from any workflow node: `{"provider": "myprovider", "action": "do_thing"}`.

No engine changes needed — the dispatcher already routes by provider name.

## 10. Production hardening checklist

- [x] Multi-tenant isolation
- [x] JWT auth + password hashing (bcrypt)
- [x] Async queue with retries
- [x] Audit trail
- [x] Health endpoint
- [x] Docker-compose for one-command setup
- [ ] HTTPS termination (add Caddy/Traefik in production compose)
- [ ] Webhook signature verification (stub already in `webhooks.py`)
- [ ] Per-workspace rate limiting (add middleware)
- [ ] Encrypted credential storage (currently plain JSON — wrap with Fernet)
- [ ] Horizontal scale: add more Celery workers behind shared Redis
