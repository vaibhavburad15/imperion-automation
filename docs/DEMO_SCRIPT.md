# 5-7 Minute Demo Video Script

Total target: **~6 minutes**.

## 0:00–0:30 Intro
"Hi, I'm building Imperion — a multi-tenant automation platform for SMBs.
It connects lead capture, workflow automation, CRM, scheduling, and
notifications, all in one. Let me give you a tour."

Show the architecture diagram from `docs/ARCHITECTURE.md`.

## 0:30–1:15 Multi-tenant login
- Open http://localhost:5173 → login as `admin@acme.com / password123`.
- Show the dashboard: leads, runs, conversion, charts.
- Logout, login as `admin@globex.com / password123` — show that
  Globex sees its own (empty) data. **No leakage**, no shared state.

## 1:15–2:30 Workflow Editor & Engine
- Back to Acme. Open **Workflows → New Lead Onboarding**.
- Walk through the JSON graph: trigger → CRM → condition (requires_human?)
  → email / slack → follow-up.
- Show the visual preview (color-coded nodes with arrows).
- Hit **Run** with a demo payload. Switch to the Dashboard — point at the
  new "success" run appearing within seconds, with duration in ms and
  step logs.

## 2:30–3:30 Lead capture + scoring + handoff
- Go to **Leads → Capture Lead**.
- Fill name, email (use a business domain like `cfo@example-inc.com`),
  source = `referral`, click Save.
- Show the **score bar** (high because of business domain + referral) and
  the **human-handoff flag** (orange icon) appear.
- Switch to Dashboard → another workflow run fires automatically.

## 3:30–4:30 Integrations + reliability
- Open **Integrations**. Show the seeded providers (email, slack, sheets,
  CRM, telegram). Click **Test** on Slack — it returns simulated success.
- Add a new **Webhook** integration with a URL like `https://httpbin.org/post`.
- Go to **Admin → Audit Logs** — show every action timestamped & traceable.
- Go to **Admin → Webhook Events** — show inbound events (run a curl to
  the public webhook URL `curl -X POST http://localhost:8000/api/v1/webhooks/acme/1 -H "Content-Type: application/json" -d '{"name":"Live demo","email":"x@y.com"}'`).
- Click **Replay** on that event — shows our durable retry pipeline.

## 4:30–5:30 AI workflow generation + rollback
- **Workflows → AI Generate** → "When a new lead arrives, save to CRM,
  send a WhatsApp message, notify Slack and book a calendar intro call."
- Show the generated graph appearing in the list. Open it → preview the
  visual chain.
- Open the existing onboarding workflow → edit something → save (version bumps).
- Click **Rollback** → version bumps again, content reverts. Highlight
  this is our safe-rollback feature.

## 5:30–6:00 Wrap-up
- Recap: multi-tenant, 8 integrations, retry+queue+scheduler, AI
  generation, audit logs, rollback, dockerized one-command deploy.
- Show the `start.sh` quickstart and the `/docs` interactive API.
- "Thanks for watching!"
