# 🔍 Services Monitor

> A **deterministic** website auditing & monitoring platform. It crawls a site, runs structured technical audits (health, SEO, accessibility, security), produces transparent and reproducible scores, and can layer an optional, fully-auditable AI explanation on top.

The guiding principle of the whole project: **every report, score, comparison, and recommendation must be traceable, explainable, reproducible, and derived from verifiable data.** No hidden business logic, no opaque scoring.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [API Surface](#-api-surface)
- [Prerequisites (WSL)](#-prerequisites-wsl)
- [Local Setup & Run on WSL](#-local-setup--run-on-wsl)
- [Configuration](#-configuration)
- [Running with Docker](#-running-with-docker)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)

---

## 🧭 Overview

Services Monitor turns an arbitrary public website into a structured, auditable quality report through a multi-stage workflow:

```
User Input → Validation → Discovery Crawl → URL Selection → Final Audit → Scoring → Report (+ optional AI summary)
```

1. **Validation** — the root URL and email are validated and sanitized (HTTPS-only, no localhost / private IPs, SSRF-protected).
2. **Discovery** — a bounded crawl maps the site structure, respects `robots.txt`, reads `sitemap.xml`, groups similar URLs, and estimates crawl risk/budget.
3. **Selection** — the user picks which sections to audit (include-based scope, capped at safe limits).
4. **Audit** — selected pages are checked across the enabled categories.
5. **Scoring** — each category gets a transparent `0–100` score; an overall score and grade are computed as a simple average of completed categories.
6. **Report** — results are returned inline (JSON), with PDF/CSV/JSON export formats defined.
7. **AI Summary (optional)** — an LLM turns the deterministic data into prose. The audit data remains the source of truth; the AI never invents scores.

The current MVP is **stateless**: every audit runs from scratch with no stored history or cache.

---

## ✨ Features

| Category | What it checks |
|---|---|
| ❤️ **Health** | Availability, redirect loops, reachability |
| 🔎 **SEO** | On-page SEO signals and metadata |
| ♿ **Accessibility** | Accessibility analysis of rendered pages |
| 🔐 **Security** | TLS, security headers, cookies, DNS, dependencies, frontend & best-practice checks |
| 🧮 **Scoring** | Deterministic per-category `0–100` scores → overall score + grade |
| 🕸️ **Discovery** | robots.txt + sitemap aware crawl, URL grouping, runaway-crawl protection, crawl-budget estimation |
| 🤖 **AI Summary** | Optional, auditable explanation layer; **bring-your-own API key** |
| 🌍 **i18n** | English & Polish output for the AI explanation layer |
| 📤 **Exports** | JSON (inline today), with PDF & CSV formats defined |
| 📡 **Streaming** | Server-streamed progress for discovery and audit (`/stream` endpoints) |

### 🔒 Safety by design
- **SSRF protection** — the crawler never reaches localhost, private networks, or internal infrastructure.
- **robots.txt is always respected** — for discovery, the audit, and the selection UI.
- **Hard crawl limits** — URL count, depth, request count, and duration caps protect both the target and the infrastructure.
- **Security headers** on every API response (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).
- **No server-side LLM key** — the AI provider key is supplied per request via the `X-LLM-Api-Key` header and lives only in the user's browser; it is never logged or persisted.

---

## 🧱 Tech Stack

### Backend — `apps/api`
- **Python 3.11+**
- **FastAPI** + **Uvicorn** (async I/O)
- **Pydantic v2** / **pydantic-settings** (validation & typed config)
- **httpx** (async HTTP client)
- **BeautifulSoup4** + **lxml** (HTML parsing)
- **truststore**, **email-validator**
- **pytest** / **pytest-asyncio** / **ruff**

### Frontend — `frontend`
- **Next.js 16** (App Router) + **React 19**
- **TypeScript**
- **TailwindCSS v4**
- **Zod** + **react-hook-form** (typed forms & API contracts)

### AI providers (bring-your-own key)
- **OpenAI**, **Google Gemini**, **Anthropic**, **OpenRouter**

---

## 🏗 Architecture

The backend follows a **vertical slice architecture** — each domain owns its own router, schemas, service logic, and tests, with no cross-slice coupling.

```
apps/api/slices/
├── input_validation/   # URL/email/report-name validation + sanitization
├── discovery/          # robots/sitemap-aware crawl, URL classification & grouping
├── health_check/       # availability & redirect-loop detection
├── seo/                # SEO analysis
├── accessibility/      # accessibility analysis
├── security/           # TLS, headers, cookies, DNS, dependencies, frontend, best-practices
├── scoring/            # deterministic per-category scores → overall + grade
├── audit/              # orchestrates checks across selected pages
├── reporting/          # report assembly + export formats (json/pdf/csv)
└── ai_summary/         # optional, auditable LLM explanation layer
```

Cross-cutting concerns live in `apps/api/core/` (config, HTTP client, SSRF guard, logging, exceptions).

---

## 🌐 API Surface

All feature endpoints are served under the `/api/v1` prefix.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/validate` | Validate audit input (URL, email, report name) |
| `POST` | `/api/v1/discovery` | Run a discovery crawl |
| `POST` | `/api/v1/discovery/stream` | Streamed discovery progress |
| `POST` | `/api/v1/health-check` | Single-URL health check |
| `POST` | `/api/v1/seo` | SEO analysis for a URL |
| `POST` | `/api/v1/audit` | Run a full audit, return report inline |
| `POST` | `/api/v1/audit/stream` | Streamed audit progress + final report |
| `POST` | `/api/v1/ai/validate-key` | Validate a user-supplied LLM API key |
| `GET`  | `/healthz` | Liveness probe (used by Docker healthcheck) |
| `GET`  | `/` | Basic server status |

> Interactive API docs are available at **`http://localhost:8000/docs`** (Swagger UI) once the API is running.

---

## 🐧 Prerequisites (WSL)

These steps assume **WSL2** with a Debian/Ubuntu distribution. From your WSL shell:

```bash
# 1. Python 3.11+ (the system default may be older — install 3.11 explicitly)
sudo apt update
sudo apt install -y python3.11 python3.11-venv

# 2. Node.js 22+ and npm  (nvm is the easiest way on WSL)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# restart the shell, then:
nvm install 22

# 3. (Optional) GNU Make — used for the convenience commands below
sudo apt install -y make
```

Verify:

```bash
python3.11 --version   # >= 3.11
node --version         # >= 22
npm --version
```

> 💡 **WSL tip:** clone and work on the project **inside** the Linux filesystem (e.g. `~/projects/...`), not under `/mnt/c/...`. Filesystem watching, install speed, and hot-reload are dramatically better.

---

## 🚀 Local Setup & Run on WSL

### Option A — Makefile (recommended)

From the repository root:

```bash
# 1. Create the backend virtual environment (uses python3 — see note below)
make venv

# 2. Install backend + frontend dependencies
make install

# 3. Configure the backend (see Configuration section)
cp apps/api/.env.example apps/api/.env

# 4. Run the API and frontend together (hot-reload)
make dev
```

- API → http://localhost:8000  (docs at `/docs`)
- Web → http://localhost:3000

> ⚠️ **Python version note:** `make venv` runs `python3 -m venv`. If your default `python3` is older than 3.11, create the venv with 3.11 explicitly instead:
> ```bash
> python3.11 -m venv apps/api/.venv
> make install
> ```

Other Make targets:

```bash
make api        # backend only (uvicorn --reload)
make frontend   # frontend only (next dev)
make help       # list all targets
```

### Option B — Manual

**Backend**

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # add -r requirements-dev.txt for tests/lint
cp .env.example .env
uvicorn main:app --reload                 # http://localhost:8000
```

**Frontend** (in a second terminal)

```bash
cd frontend
npm install
# point the browser-side client at the API:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev                                # http://localhost:3000
```

---

## ⚙️ Configuration

### Backend — `apps/api/.env`

Copy `apps/api/.env.example` and adjust. Key variables:

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Services Monitor API` | Application title |
| `DEBUG` | `false` | FastAPI debug mode |
| `CORS_ALLOWED_ORIGINS` | _(empty)_ | Comma-separated browser origins allowed to call the API. Empty = no cross-origin |
| `LOG_DIR` | _(empty)_ | Directory for the rotating log file. Empty = stdout only |
| `HTTP_TIMEOUT` | `30.0` | Outbound HTTP timeout (seconds) |
| `HTTP_MAX_REDIRECTS` | `10` | Max redirects to follow |
| `USER_AGENT` | `ServiceMonitorBot/1.0 …` | Crawler user-agent |
| `DISCOVERY_MAX_URLS` | `500` | Discovery hard caps … |
| `DISCOVERY_MAX_DEPTH` | `3` | |
| `DISCOVERY_MAX_DURATION_SECONDS` | `120` | |
| `DISCOVERY_MAX_REQUESTS` | `1000` | |
| `AUDIT_MAX_DURATION_SECONDS` | `240` | Audit time cap |
| `AUDIT_MAX_PAGES` | `50` | Max pages per audit |
| `AUDIT_DEFAULT_PAGES` | `15` | Default pages per audit |
| `AI_SUMMARY_ENABLED` | `true` | Server-wide kill switch for AI summaries |
| `AI_SUMMARY_TIMEOUT_SECONDS` | `45.0` | LLM request timeout |
| `AI_SUMMARY_MAX_TOKENS` | `8192` | Max tokens per summary |
| `AI_SUMMARY_MAX_TOOL_ITERATIONS` | `4` | Max tool-use iterations |

> 🔑 The **LLM API key is never configured on the server.** It is supplied per request via the `X-LLM-Api-Key` header and stored only in the user's browser.

### Frontend — `frontend/.env.local`

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API origin reachable from the **browser**. Inlined at build time — must be set before `npm run build` |

---

## 🐳 Running with Docker

A `docker-compose.yml` is provided for a one-command stack:

```bash
# Optional: configure the backend first
cp apps/api/.env.example apps/api/.env

# Build & start both services
docker compose up --build
```

- API → http://localhost:8000 (with a `HEALTHCHECK` on `/healthz`)
- Web → http://localhost:3000 (waits for the API to become healthy)

To point the frontend at a non-default API origin (it is inlined at build time):

```bash
NEXT_PUBLIC_API_URL=https://api.example.com docker compose up --build
```

Both images run as **non-root** users.

---

## 🧪 Testing

Backend tests use **pytest** (`asyncio_mode=auto`) and live next to each slice under `slices/<slice>/tests/`.

```bash
cd apps/api
source .venv/bin/activate
pip install -r requirements-dev.txt    # pytest, pytest-asyncio, ruff
pytest                                  # run the full suite
ruff check .                            # lint
```

Frontend correctness is currently verified via the TypeScript compiler and ESLint:

```bash
cd frontend
npx tsc --noEmit
npm run lint
```

---

## 🗂 Project Structure

```
services-monitor/
├── apps/
│   └── api/                # FastAPI backend (vertical slices)
│       ├── core/           # config, http client, SSRF guard, logging, exceptions
│       ├── slices/         # input_validation, discovery, health_check, seo,
│       │                   # accessibility, security, scoring, audit,
│       │                   # reporting, ai_summary
│       ├── main.py         # app factory, middleware, router wiring
│       ├── requirements.txt
│       └── Dockerfile
├── frontend/               # Next.js 16 + React 19 app
│   ├── app/                # App Router pages
│   ├── components/         # audit / discovery / layout / ui
│   ├── lib/                # api client, schemas, i18n (en/pl), llm, types, utils
│   ├── hooks/
│   └── Dockerfile
├── docs/                   # architecture, workflow, scoring & security docs
├── docker-compose.yml
├── Makefile
└── CLAUDE.md               # engineering principles & conventions
```

---

## 📚 Documentation

`docs/` is the primary source of truth for architecture, workflows, business rules, and scoring logic:

- `project assumptions.md` — product & architectural assumptions
- `service_monitor_workflow_documentation_en.md` — input collection & crawl-planning workflow
- `audit_result_structure.md` — shape of audit results
- `security_audit.md` — security checks & rationale
- `ai_audit_summary_architecture_claude_prompt.md` — AI summary architecture
- `frontend_api_integration.md` — frontend ↔ API integration contract
- `internationalization.md` — EN/PL i18n approach

---

<div align="center">

Built with a bias toward **transparency, determinism, and explainability**.

</div>
