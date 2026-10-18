# AegisLend AI — Phases 1 and 2

An Intelligent and Secure Digital Lending Ecosystem Using Agentic AI, RAG, and Hybrid Intrusion Detection.

Phase 2 authentication and RBAC are now implemented. See [docs/PHASE2.md](docs/PHASE2.md) for upgrade commands, signing-key setup, API contracts, administrator provisioning, test evidence and limitations. Run `python scripts/configure_auth.py` after initial environment setup.

Phase 1 foundation: frontend connection dashboard, FastAPI health API, validated configuration, SQLAlchemy/MySQL sessions, Alembic baseline, development service configuration and tests. Lending, agents, RAG and IDS remain future phases. See `docs/ARCHITECTURE.md` and `docs/VERIFICATION.md`.

## Structure

- `frontend/src/`: React Router application, Axios API client, UI and API tests.
- `backend/app/`: application factory, settings, session dependency and infrastructure model.
- `backend/alembic/`: migration environment and reversible baseline migration.
- `backend/tests/`: unit tests plus opt-in real MySQL readiness test.
- `scripts/init_env.py`: creates local environment files with random development passwords.
- `compose.yaml`: MySQL 8.4; optional Redis and ChromaDB services.
- `docs/`: architecture, scope, integration gate and verification evidence.

## Prerequisites

Node.js 22.12+ (tested with 24.19), npm, Python 3.12, and Docker with Compose v2 or an existing MySQL 8.4 instance. Run these commands from the extracted `aegislend` directory. Shell examples use Bash; on Windows use WSL, or the PowerShell equivalents below.

## Install and configure

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python scripts/init_env.py
cd frontend
npm ci
cd ..
docker compose up -d --wait mysql
cd backend
alembic upgrade head
alembic current
cd ..
```

For an existing MySQL server, create the `aegislend` database and a dedicated user with rights to that database, set `DB_*` in `backend/.env`, and omit `docker compose`. Match the password to the user on the server. Do not use a root account for the application. Migrations require schema-change privileges; a separate runtime user can be introduced with production deployment.

Optional supporting services:

```bash
docker compose --profile support up -d
```

These services are not consumed by the Phase 1 API. The backend can start without MySQL, but readiness and the dashboard database card will report unavailable.

## Run — terminal 1

```bash
cd backend
../.venv/bin/uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

## Run — terminal 2

```bash
cd frontend
npm run dev
```

Open http://localhost:5173. API docs: http://127.0.0.1:8000/docs. Keep both processes running. `VITE_API_BASE_URL` defaults to `/api/v1`; `API_PROXY_TARGET` is the backend URL. Frontend environment values are public: never put secrets there. Production hosting must route `/api` to FastAPI (or configure an explicit API base URL and CORS), and return the SPA entry point for client-side routes.

## Verify

From the project root with the virtual environment active:

```bash
cd backend
pytest -q
python -m pip check
alembic upgrade head --sql
RUN_MYSQL_TESTS=1 pytest -q -m mysql
alembic check
cd ../frontend
npm test
npm run build
curl --fail http://127.0.0.1:5173/api/v1/health/live
curl --fail http://127.0.0.1:5173/api/v1/health/ready
```

The MySQL test is skipped unless enabled. When enabled it must fail if the real database is unavailable or unmigrated. A 503 readiness response is intentional and never counts as a successful database connection.

On a disposable development database only, test the reversible baseline:

```bash
cd backend
alembic downgrade base
alembic upgrade head
RUN_MYSQL_TESTS=1 pytest -q -m mysql
```

Downgrade deletes the infrastructure table. Do not use it on databases containing data you need.

## Windows PowerShell differences

Use `py -3.12 -m venv .venv`, then `.\.venv\Scripts\Activate.ps1`. After activation, use `python`, `pip`, `alembic`, and `uvicorn` directly. In terminal 1 run `uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000` from `backend`. Set `$env:RUN_MYSQL_TESTS='1'` before the database test, then `Remove-Item Env:RUN_MYSQL_TESTS` afterward. Docker Desktop should use Linux containers.

## Credentials and reproducibility

`init_env.py` refuses to overwrite existing files. To configure manually, copy the three `.env.example` files to `.env` in their respective directories and replace placeholders. Keep `.env` out of source control. `requirements.txt` pins the installed Python dependency set; `requirements.in` records direct dependency ranges. `package-lock.json` locks npm dependencies. Update dependencies deliberately and rerun checks.

LLM integration is disabled pending verified API access. Chat model availability is not API entitlement. No real customer data or external inference calls are used.

## Live HTTP smoke test

Stop any development servers using ports 8000/5173 first. With the project virtual environment active, from the project root:

```bash
python scripts/smoke.py
# After MySQL is running and migrations have been applied:
python scripts/smoke.py --expect-ready
```

The script starts both servers, checks the actual Vite proxy and response contracts, then stops its child processes. Without `--expect-ready`, a 503 database response is accepted as a valid unavailable-state response, not proof of database connectivity. This is an HTTP integration test, not a browser-rendered test.
