> Historical phase record. For the current integrated build, see README.md, PROJECT_GUIDE.md and FINAL_VERIFICATION.md.

# AegisLend AI architecture

Phase 1 is a modular monolith: React/TypeScript → Axios → FastAPI → SQLAlchemy 2.x → MySQL. React Router owns client navigation; Vite proxies `/api` during development. Tailwind uses its official Vite plugin. Pydantic validates configuration and response contracts. Alembic exclusively owns schema changes; application startup never calls `create_all`.

SQLAlchemy uses a synchronous PyMySQL engine and per-request sessions; database routes are synchronous FastAPI handlers executed in the thread pool. Sessions close on request completion and the engine is disposed at shutdown. Passwords use SecretStr and SQLAlchemy URL.create to avoid string interpolation bugs. Database failure responses do not disclose exception messages or credentials.

## Phase 1 acceptance criteria

- Frontend dependency lock, TypeScript checks, tests and production build.
- Backend pinned dependencies, validated environment, automated health/configuration tests.
- `/api/v1/health/live` returns 200 independent of database availability.
- `/api/v1/health/ready` returns 200 only when MySQL responds and the migrated phase marker exists; otherwise 503.
- Vite proxy carries requests to the real running FastAPI process.
- Alembic baseline upgrade/downgrade and environment templates are supplied.
- MySQL migrations and readiness are verified against a real MySQL instance when one is available. Offline SQL and mocked tests are explicitly not substitutes.
- Exact run commands and remaining verification gaps are documented.

## Later phases and mandatory boundaries

1. Authentication/RBAC: secure password hashing, session/token design, customer/admin authorization on backend operations, audit records, tests for privilege escalation.
2. Loan catalog, deterministic eligibility and application tracking: money represented using Decimal/database DECIMAL; explicit, versioned rules; AI cannot approve or decline loans.
3. Appointment scheduling: transactional database constraints/locking for capacity, idempotency and concurrency tests. Redis can support coordination but must not replace database invariants.
4. RAG and CrewAI: ChromaDB stores retrievable document chunks with provenance; responses cite retrieved sources, acknowledge missing evidence, and treat retrieved instructions as untrusted. Model calls remain server-side behind a configurable provider boundary.
5. IDS: signature/rule detection plus Isolation Forest through pandas, NumPy and scikit-learn; centralized Risk Engine combines signals. Model validation and synthetic-data fixtures precede activation.
6. Security Center: backend RBAC and policy-controlled, audited response actions. AI produces advice only; no independent privileged action execution.

Redis and ChromaDB are optional Compose services in this phase; no application integration or service availability is claimed. CrewAI, ML packages and inference SDKs are intentionally deferred to their phases rather than installed without working features. No customer financial data is used.

## LLM access gate

Astra Light/Medium availability in the coding/chat environment does not establish an application API. Available tool metadata did not identify a callable Astra inference endpoint; no provider endpoint, model ID, authentication contract or API entitlement was supplied or tested. `LLM_PROVIDER=disabled` is the only accepted setting in Phase 1. Before adding the configurable adapter, verify provider documentation, actual API entitlement, endpoint, model identifier, credentials and a minimal authorized inference call. Never reuse session/browser credentials as API keys or invent model IDs.

## Scope and operational limits

This is a development foundation, not a production lending service. Health readiness covers MySQL plus the baseline marker only, not Redis, ChromaDB or future migrations. Configure production HTTPS, secret management, rate limits, logging, backups and production routing in later deployment work. The Vite dev proxy is not a production API gateway. The Compose service ports bind to loopback. Supporting-service image tags are explicit; immutable digest pinning and deployment validation remain future work.

## References used

- https://vite.dev/guide/
- https://tailwindcss.com/docs/installation/using-vite
- https://docs.sqlalchemy.org/en/20/core/engines.html
