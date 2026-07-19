# 🍃 Tea Leaves Weighing & Smart Records System

A lightweight Flask + MySQL web application that helps small tea collection
centres in Sri Lanka **digitise daily collection** and **catch entry errors
automatically** — built for non-technical rural operators.

> **Module:** IT304040 — Python Programming, Final Group Project
> **University of Vocational Technology** · B.Tech in Software and Intelligent Systems (2024/2025)
> **Group 09** ·

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Getting Started](#getting-started)
6. [Configuration](#configuration)
7. [Running the App](#running-the-app)
8. [Running the Tests](#running-the-tests)
9. [Deployment](#deployment)
10. [Team & Responsibilities](#team--responsibilities)
11. [License](#license)

---

## Overview

The system keeps a solid CRUD weighing ledger as its foundation and adds two
smart, **rule-based** features that give real logic depth without the cost and
risk of machine learning:

- **Automatic error / anomaly check** on every weight entry.
- **Simple trend estimate** (moving average) of each farmer's supply.

These directly answer the project's pain points: manual entry causes errors,
payments are disputed, and existing tools are too costly or too basic.

## Key Features

| Feature | Description |
|---------|-------------|
| Farmer registry | Add, edit and manage farmers |
| Daily weight entry | Record weights against the correct farmer |
| Auto error check | Warns on zero/negative, far-too-high/low, or likely double entries (§5.2) |
| Trend estimate | Moving-average "up/down" hint + rough next-day estimate (§5.3) |
| Payments & wages | Farmer payment and plucker wage; excludes flagged rows (§5.4) |
| Attendance | Mark plucker attendance for wage calculation |
| Reports | Daily and farmer-wise reports, optional charts |
| Operator login | Session-based authentication, hashed passwords |
| AI assistant | In-app chatbot with RAG over a built-in manual + read-only data tools; also exposed to MCP clients (see [docs/chatbot_rag_mcp_guide.md](docs/chatbot_rag_mcp_guide.md)) |

## Tech Stack

- **Backend:** Python 3, Flask 3.0.2 (application factory + blueprints)
- **Database:** MySQL (`mysql-connector-python`)
- **Frontend:** Bootstrap 5, Jinja2 templates
- **Config:** `python-dotenv`
- **Deployment:** gunicorn on Render / Railway

## Project Structure

```
tea_weighing/
├── src/
│   ├── app.py          # Flask app factory, routing, integration  (Sagara)
│   ├── auth.py         # operator login / sessions                (Sagara)
│   ├── config.py       # environment configuration                (Sagara)
│   ├── db.py           # MySQL connection helpers                  (Sagara)
│   ├── models.py       # MySQL schema                              (Dissanayaka)
│   ├── farmers.py      # farmer CRUD                               (Dissanayaka)
│   ├── weights.py      # weight entry (calls error check)          (Ravishan)
│   ├── checks.py       # error/anomaly + trend logic               (Ravishan/Dharmarathna)
│   ├── payments.py     # payment & wage engine                     (Dissanayaka)
│   ├── attendance.py   # plucker attendance                        (Disanayaka)
│   ├── reports.py      # reports + simple charts                   (Dharmarathna)
│   ├── templates/      # Jinja2 + Bootstrap views
│   └── static/         # CSS / assets
├── tests/              # pytest suite
├── data/               # seed scripts / sample data
├── docs/               # architecture, test log
├── requirements.txt    # pinned dependencies
├── wsgi.py             # production entry point
├── Procfile            # process definition (cloud)
├── render.yaml         # Render deployment blueprint
├── .env.example        # configuration template
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL 8.x (running locally or a managed instance)
- `pip` and `venv`

### Install

```bash
git clone <repository-url>
cd tea_weighing
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy the template and fill in your values:

```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS/Linux
```

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Flask session signing key |
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | MySQL connection |
| `DEFAULT_OPERATOR_USERNAME` / `DEFAULT_OPERATOR_PASSWORD` | Operator seeded on first run |
| `GROQ_API_KEY` / `CHATBOT_MODEL` | Free Groq API key for the AI assistant (optional — without it the chatbot answers from the built-in manual) |

`.env` is git-ignored — **never commit real credentials.**

## Running the App

```bash
cd tea_weighing
python -m src.app
```

Open <http://localhost:5000> and log in with the default operator
(`admin` / `admin123` unless changed in `.env`).

> The app boots even if MySQL is not yet available — the dashboard simply shows
> a "Database offline" badge — so development is never blocked on the database.

## Running the Tests

```bash
cd tea_weighing
python -m pytest
```

The integration smoke tests verify the app factory builds, every blueprint is
registered, protected routes redirect to login, and `/healthz` responds. The
full feature test suite is owned by QA (D.M.N.K. Disanayaka).

## Deployment

The repo is ready for a one-click deploy on **Render** (or Railway). See
[`docs/architecture_and_deployment.md`](docs/architecture_and_deployment.md)
for full steps. In short:

1. Push to GitHub (public repository).
2. Render → **New → Blueprint** → select the repo (`render.yaml` does the rest).
3. Add a managed MySQL instance and set the `DB_*` / `SECRET_KEY` env vars.
4. Visit the live URL and `/healthz`, then share the URL with the lecturer.

## Team & Responsibilities

| Member | Role |
|--------|------|
| H.G.P.C. Sagara | Project Manager & Integration Dev — app factory, auth, DB layer, deployment, README |
| K.G.C. Ravishan | Lead Dev — Weights & Smart Checks |
| D.M.N.D. Dissanayaka | Lead Dev — Database & Payments |
| P.A.K.N. Dharmarathna | Domain Researcher & Reports/Trend Dev |
| D.M.N.K. Disanayaka | QA, Testing & Attendance Dev |

## License

Academic project — © 2026 Group 09, University of Vocational Technology.
For educational use.
