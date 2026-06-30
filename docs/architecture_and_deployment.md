# Architecture & Deployment

**Report section owner:** H.G.P.C. Sagara (Project Manager & Integration Dev)
**Project:** Tea Leaves Weighing & Smart Records System — Group 09

---

## 1. Architecture Overview

The system keeps the proposal's **three-layer architecture**. The logic for the
two smart features lives in the domain layer, so the interface and persistence
layers stay thin and testable.

```
┌─────────────────────────────────────────────────────────┐
│  Interface Layer                                          │
│  Flask routes (blueprints) + Bootstrap templates         │
│  app.py · auth.py · farmers · weights · payments ·       │
│  attendance · reports                                    │
├─────────────────────────────────────────────────────────┤
│  Domain Layer                                            │
│  Validation · error/anomaly check · trend estimate ·     │
│  payment & wage rules · reports         (checks.py …)    │
├─────────────────────────────────────────────────────────┤
│  Persistence Layer                                       │
│  MySQL via db.py helpers (parameterised, try/except)     │
│  Tables: farmer, weight_record, payment, plucker,        │
│  attendance, price_config, operator                      │
└─────────────────────────────────────────────────────────┘
```

### Module → Blueprint → Owner

| File            | Blueprint / role         | Owner                  |
|-----------------|--------------------------|------------------------|
| `app.py`        | app factory, core routes | H.G.P.C. Sagara        |
| `auth.py`       | `auth` — login/sessions  | H.G.P.C. Sagara        |
| `config.py`     | environment config       | H.G.P.C. Sagara        |
| `db.py`         | MySQL connection layer   | H.G.P.C. Sagara        |
| `models.py`     | schema                   | D.M.N.D. Dissanayaka   |
| `farmers.py`    | `farmers`                | D.M.N.D. Dissanayaka   |
| `weights.py`    | `weights`                | K.G.C. Ravishan        |
| `checks.py`     | error check + trend      | Ravishan / Dharmarathna|
| `payments.py`   | `payments`               | D.M.N.D. Dissanayaka   |
| `attendance.py` | `attendance`             | D.M.N.K. Disanayaka    |
| `reports.py`    | `reports`                | P.A.K.N. Dharmarathna  |

### How integration works

`create_app()` in `app.py` is the single wiring point. Each teammate's module
exposes a Flask `bp` blueprint; the factory registers them all under clean URL
prefixes (`/farmers`, `/weights`, …), installs the database teardown handler,
registers authentication, and adds the error handlers. Because every module
depends only on the shared `db.py` helpers and the `login_required` decorator,
teammates can work on separate branches without colliding.

## 2. Request Flow (example: recording a weight)

1. Operator logs in → `auth.login` sets the session.
2. Operator opens `/weights` (protected by `login_required`).
3. `weights.py` calls `checks.check(farmer_id, weight)` (domain layer, §5.2).
4. `db.execute(...)` saves the row through the parameterised helper.
5. A warning flash is shown on screen if the entry was flagged.

## 3. Configuration & Secrets

All environment-specific values are read once in `config.py`:

- `SECRET_KEY`, `FLASK_ENV`
- `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD`
  (or a single `DATABASE_URL` that the host injects)
- `DEFAULT_OPERATOR_USERNAME` / `DEFAULT_OPERATOR_PASSWORD`

Locally these come from a `.env` file (see `.env.example`). Secrets are **never
committed** — `.env` is in `.gitignore`. In the cloud they are set in the host
dashboard.

## 4. Error Handling (guideline §5.5)

- Every DB call in `db.py` is wrapped in `try/except` and raises a
  `DatabaseError` carrying a short, user-safe message.
- Routes turn failures into friendly flash messages or the 404/500 pages.
- A real stack trace is **never** shown to the operator; the full error is
  written to the server log only.

## 5. Deployment (Render / Railway)

The app ships with everything needed for a one-click deploy:

| File              | Purpose                                       |
|-------------------|-----------------------------------------------|
| `requirements.txt`| Pinned dependencies (incl. `gunicorn`)        |
| `wsgi.py`         | WSGI entry — `gunicorn wsgi:app`              |
| `Procfile`        | Process definition for the web dyno           |
| `render.yaml`     | Render blueprint: web service + env vars      |
| `/healthz`        | Health-check endpoint for uptime monitoring   |

### Deploy steps

1. Push the repository to GitHub (public, per the submission checklist).
2. On Render: **New → Blueprint**, select the repo. `render.yaml` provisions
   the web service automatically (root dir `tea_weighing`).
3. Create a managed MySQL instance and set `DB_*` (or `DATABASE_URL`),
   `SECRET_KEY`, and the default operator variables in the dashboard.
4. First boot runs `ensure_operator_table()`, which creates the `operator`
   table and seeds the default operator.
5. Verify the live URL and `/healthz`, then share the URL with the lecturer.

## 6. Local Development

```bash
cd tea_weighing
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env        # then edit DB credentials
python -m src.app             # http://localhost:5000
```

The app boots even if MySQL is not yet running — the dashboard shows a
"Database offline" badge instead of crashing — so front-end work is never
blocked on the database being ready.
