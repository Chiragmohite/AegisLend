# AegisLend AI

**Chatbot artwork refinement:** The new transparent 3D assistant is integrated exclusively in the chatbot. Real-browser light/dark avatar verification passed; see [AVATAR_3D_REFINEMENT](docs/AVATAR_3D_REFINEMENT.md). This does not supersede limitations for the full application E2E suite.

**Approved polish release (2026-10-17):** Start with [current enhancement report](docs/POLISH_REPORT.md), [executed verification](docs/POLISH_VERIFICATION.md), and [changed files](docs/POLISH_FILES.md). The illustrated character is used only in the chatbot. This release preserves migrations through `0007`; it adds no schema changes. Earlier enhancement reports remain historical evidence.

**An Intelligent and Secure Digital Lending Ecosystem Using Agentic AI, RAG, and Hybrid Intrusion Detection**

A runnable academic demonstration built on the original Phase 1 and Phase 2 project. Use synthetic data only. This is not a bank, real lending offer, compliance certification or production security product. Preliminary calculations never approve a loan; only an authorized human reviewer changes review outcomes.

## What is implemented

- React/Vite/TypeScript/Tailwind application with login, registration, profile, products, eligibility, application history, appointments, assistant and administrator screens.
- Argon2id passwords, expiring HS256 JWTs, server-side customer/admin RBAC, current-role checks, input validation, body limits, auth rate limiting and audited local administrator bootstrap.
- Decimal EMI calculations, explainable synthetic eligibility rules, immutable assessment snapshots, idempotent draft requests, versioned draft editing, optimistic application transitions and mandatory human review notes. Administrators cannot review their own applications.
- Capacity-controlled calendar with timezone validation, database-enforced unique capacity seats, cancellation and ownership checks.
- PDF/TXT/Markdown ingestion, local hashing-vector embeddings, quoted answers with document/page/chunk sources, optional Chroma v2 retrieval and a bounded optional external/CrewAI source-selection adapter.
- Hybrid IDS rules, persisted Isolation Forest training/inference, transparent Risk Engine, sanitized security/audit events and a Security Center with filters, pagination, real backend metrics, health, human acknowledgement/escalation and controlled demo probes.
- Additive migrations through `0007`; historical migrations `0001` and `0002` retained unchanged. Safe additive seeds, tests, pinned requirements and Windows helpers.

See [project guide](docs/PROJECT_GUIDE.md), [API reference](docs/API.md), [verification evidence](docs/FINAL_VERIFICATION.md), [demo walkthrough](docs/DEMO.md), and [final-year report material](docs/FINAL_YEAR_REPORT.md). Prior-phase documents are historical evidence, not the current setup contract.

## Prerequisites

Windows PowerShell, Python **3.12**, Node.js **22.12+** (tested on Node 24), npm, and MySQL **8.4** or Docker Desktop with Compose v2/Linux containers. Backend port 8000 and frontend port 5173 must be free. PowerShell itself and Docker were unavailable in the build environment, so those launch paths require local verification.

The core install does not download an embedding model or require API credentials. All credentials belong only in local environment files or a secret manager. No `.env` files are in the ZIP.

## Option A: fresh isolated Docker database

Use a newly extracted ZIP directory with no local `.env` files. This creates project **aegislend-demo** and a separate MySQL volume on host port **3307**, avoiding the existing Phase 1 container on port 3306. Do not use the fresh mode on your current configured working directory.

From the extracted `aegislend` folder:

```powershell
.\scripts\setup.ps1 -Mode FreshDocker
.\scripts\migrate.ps1
.\scripts\seed.ps1
Push-Location backend
..\.venv\Scripts\python.exe -m app.bootstrap
..\.venv\Scripts\python.exe -m app.train_ids
Pop-Location
.\scripts\test.ps1
.\scripts\start-backend.ps1
```

In a second terminal, from `aegislend`:

```powershell
.\scripts\start-frontend.ps1
```

Bootstrap prompts for a new synthetic `@example.com` administrator email and password without printing the password. No account is created by seeding and no default login exists. Register customer accounts through the UI. If scripts are blocked by your organization's execution policy, follow that policy; the underlying commands are ordinary Python/npm commands shown below.

## Option B: reuse existing Phase 1/2 MySQL

Keep your existing MySQL container running on **3306**. Do not start another MySQL service. Preserve your local environment files when merging source; do not replace them with `.env.example`.

```powershell
.\scripts\setup.ps1 -Mode ExistingMySQL
notepad .\backend\.env
# Verify your EXISTING DB_HOST, DB_PORT, DB_NAME, DB_USER and DB_PASSWORD locally.
# The setup helper preserves existing files and never reads another container's credentials.
.\scripts\migrate.ps1
.\scripts\seed.ps1
Push-Location backend
..\.venv\Scripts\python.exe -m app.bootstrap
# Skip bootstrap when your intended administrator already exists.
..\.venv\Scripts\python.exe -m app.train_ids
Pop-Location
.\scripts\test.ps1
.\scripts\start-backend.ps1
```

Second terminal: `./scripts/start-frontend.ps1`. No new migration is added by this polish release. Existing upgrades through `0007` must still be applied if needed; `0007` revokes older sessions once to establish uniqueness. No database reset or volume deletion is required. Back up any database you care about before upgrading. `setup.ps1 -Mode ExistingMySQL` only creates missing templates; replace their placeholder DB password before migration. It does not infer existing credentials.

If you already have an active registered synthetic account to promote, from `backend` run:

```powershell
..\.venv\Scripts\python.exe -m app.manage set-role --email synthetic-admin@example.com --role administrator
```

This explicitly changes that existing account and writes an audit record. Only a trusted operator with host/database access should run it. There is no public role-change endpoint.

## URLs and readiness

- Frontend: http://localhost:5173
- Backend OpenAPI UI: http://127.0.0.1:8000/docs
- Liveness: http://127.0.0.1:8000/api/v1/health/live
- Original Phase 1 readiness: `/api/v1/health/ready` (MySQL and baseline marker)
- Full application schema readiness: `/api/v1/health/application` (requires migration `0007`)

The Vite proxy routes `/api` to FastAPI. An unavailable database returns 503; it is never treated as a successful domain operation. Host servers use loopback and `--no-proxy-headers`; configure explicit trusted proxy handling before any hosted deployment. Production hosting must supply HTTPS, API routing and SPA history fallback.

## Optional Redis and ChromaDB

With existing MySQL, the following file starts **only** supporting services and never binds a MySQL port:

```powershell
docker compose -f compose.support.yaml up -d
```

For the fresh isolated stack, instead use:

```powershell
docker compose -f compose.fresh.yaml --profile support up -d
```

Choose one supporting stack, not both (both use ports 6379 and 8001). Set `REDIS_ENABLED=true` and/or `CHROMA_ENABLED=true` in `backend/.env`, then restart the API. Chroma is accessed through its bounded-timeout HTTP v2 adapter and uses provided embeddings; no model download is necessary. Re-index existing documents in the UI after enabling Chroma. The original `compose.yaml` remains for compatibility but is not the fresh-isolated path.

Redis is optional: if unavailable at initialization, a visible per-process limiter is used; if an active Redis connection fails during enforcement, auth requests fail closed. The local fallback is suitable for one development worker, not distributed production enforcement. Chroma failures retain local retrieval and return an explicit warning/status. MySQL remains required for persistence.

## Optional LLM / CrewAI

Default `LLM_PROVIDER=disabled` means local, grounded extractive answers. It does not mean the assistant is unavailable. An optional provider selects source indices only; final answer text is copied from validated retrieved chunks. Agents have no account, SQL, browser, shell or loan-decision tools.

Optional packages have a separate pinned lock:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-ai.txt
```

Configure `LLM_PROVIDER=openai-compatible`, an HTTPS `LLM_BASE_URL`, a verified `LLM_MODEL`, and private `LLM_API_KEY`. Set `CREWAI_ENABLED=true` only to opt into bounded CrewAI source selection. Source snippets/questions are sent to that configured provider; only public synthetic knowledge should be used. Missing configuration or provider failure falls back to local answers with a warning.

Astra Light/Medium availability in ChatGPT does not establish API access. No Astra endpoint/model ID is guessed, no chat-session credentials are reused, and no external model call was verified. Historical optional-package checks do not establish current external-provider access; this release tests the core environment only.

## Environment reference

See `backend/.env.example`, `frontend/.env.example` and root `.env.example`.

| Setting | Purpose/default |
|---|---|
| DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD | Required MySQL connection; no real credentials shipped |
| JWT_SECRET | Random signing key, at least 32 bytes; helper generates 48 random bytes |
| ACCESS_TOKEN_MINUTES | 15 by default; 5–60 allowed |
| JWT_ISSUER / JWT_AUDIENCE | aegislend-api / aegislend-client |
| CORS_ORIGINS | JSON list of explicit localhost/127.0.0.1 origins on port 5173 |
| AUTH_RATE_LIMIT | 20 auth attempts per client IP per 60 seconds by default |
| REDIS_ENABLED / REDIS_URL | false / redis://127.0.0.1:6379/0 |
| CHROMA_ENABLED / CHROMA_URL | false / http://127.0.0.1:8001 |
| IDS_FAILED_THRESHOLD / IDS_BURST_THRESHOLD | 5 failures / 60 requests in a 60-second process window |
| IDS_INCIDENT_THRESHOLD / IDS_STUFFING_THRESHOLD | 30 risk points to create an incident / 5 distinct failed-login identities |
| IDS_ANOMALY_THRESHOLD | 0.0 decision-function cutoff |
| IDS_MODEL_PATH | backend/var/ids.joblib by default; trusted local file only |
| LLM_PROVIDER | disabled or openai-compatible |
| LLM_BASE_URL / LLM_MODEL / LLM_API_KEY | Optional external source selector; key private, model explicitly configured |
| CREWAI_ENABLED | false |
| VITE_API_BASE_URL | /api/v1; public browser setting |
| API_PROXY_TARGET | http://127.0.0.1:8000; Vite development proxy |
| MYSQL_* | Root Compose environment for a freshly provisioned database only |
| MYSQL_PORT | Fresh Compose host port; defaults to 3307 |

Browser tokens are held in memory, not persistent browser storage. Refreshing or signing out clears the browser copy. Server-side sessions are checked on every protected request. Successful sign-out revokes that session, including copied tokens. Refreshing clears only the browser copy; the server session remains until revocation or expiry and a new sign-in may trigger a concurrent-login challenge. Role changes are checked from the database on each request.

## Manual setup without helper scripts

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
# Fresh environment only; refuses to overwrite existing configuration:
.\.venv\Scripts\python.exe scripts\init_env.py
.\.venv\Scripts\python.exe scripts\configure_auth.py
# Set backend/.env to your actual MySQL instance before continuing.
Push-Location frontend
npm ci
Pop-Location
.\scripts\migrate.ps1
.\scripts\seed.ps1
```

## Tests and migrations

```powershell
.\scripts\test.ps1
Push-Location backend
..\.venv\Scripts\python.exe -m alembic heads
..\.venv\Scripts\python.exe -m alembic check
..\.venv\Scripts\python.exe -m alembic upgrade head --sql
Pop-Location
```

Default backend tests use temporary SQLite databases and synthetic identities. They validate fresh migrations, Phase 2 upgrades, preservation and isolated downgrade/re-upgrade behavior. They do not prove MySQL compatibility.

To run the opt-in MySQL tests, create a separate empty `aegislend_test_*` MySQL database and supply only its credentials in environment variables. Never use your existing application database for these tests:

```powershell
$env:DB_NAME='aegislend_test_verification'
# Supply DB_USER/DB_PASSWORD/DB_HOST/DB_PORT for this disposable test database securely.
Push-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
$env:RUN_MYSQL_TESTS='1'
$env:RUN_MYSQL_AUTH_TESTS='1'
$env:RUN_MYSQL_DOMAIN_TESTS='1'
..\.venv\Scripts\python.exe -m pytest -q -m mysql
Remove-Item Env:RUN_MYSQL_TESTS, Env:RUN_MYSQL_AUTH_TESTS, Env:RUN_MYSQL_DOMAIN_TESTS
Pop-Location
# Restore your normal DB environment before starting the application.
```

Browser E2E uses temporary SQLite and synthetic accounts, never the configured MySQL:

```powershell
Push-Location frontend
npx playwright install chromium
npm run test:e2e
Pop-Location
```

It requires the project `.venv`; override `AEGIS_PYTHON` only if your test Python is elsewhere. Ports 8010/5174 must be free. Browser download failed in the build environment, so browser execution is not claimed.

Live Chroma test (optional packages installed, virtual environment activated so `chroma` is on PATH):

```powershell
$env:RUN_CHROMA_TESTS='1'
Push-Location backend
..\.venv\Scripts\python.exe -m pytest -q tests/test_chroma_live.py
Pop-Location
Remove-Item Env:RUN_CHROMA_TESTS
```

## Retraining and packaging

From backend, run `../.venv/Scripts/python.exe -m app.train_ids`, or use **Train synthetic IDS model** in Security Center. CLI training requires an API restart; UI training updates the process model immediately. Training data are generated numerically using seed 42. Do not load untrusted joblib files. Artifacts and local databases are excluded from releases.

`python scripts/build_release.py --output ../AegisLend_AI_Polished.zip` creates the complete source ZIP in the project parent folder, excludes secrets/dependencies/caches and checks local secret values are absent. Tests, documentation and both dependency locks are included.

## Current limitations

Real MySQL execution, Windows/PowerShell, Docker images and browser rendering remain unverified in this environment. Redis was not live-tested; fallback behavior is implemented. Live Chroma is not reverified in this release; its optional integration test is skipped without the service. The optional external LLM/CrewAI call path was not exercised with provider credentials. See the verification report for exact command outcomes.

This is an academic demonstration. Optional authenticator TOTP and server-side session logout are implemented. Email verification, self-service password recovery, refresh-token rotation, tamper-evident audit storage, production incident response, OCR and antivirus sandboxing are not implemented. Local IDS counters are per process. Hashing embeddings are lexical and weaker than semantic models. Synthetic IDS evaluation does not establish real-world detection accuracy. PDFs are size/page/text bounded but not a complete malicious-document sandbox. No production/banking/regulatory assurance is claimed.
