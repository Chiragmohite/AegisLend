> Historical phase record. For the current integrated build, see README.md, PROJECT_GUIDE.md and FINAL_VERIFICATION.md.

# Phase 2 — Authentication and RBAC

Implemented incrementally on the existing Phase 1 source. No frontend files, original tests, database session code, migration 0001 or health response contracts were replaced. The source directory has no Git metadata; existing backend files were inspected and a local pre-edit snapshot was retained during implementation.

## Repository inspection before edits

- frontend/: React/Vite/TypeScript/Tailwind/React Router/Axios, UI and API tests.
- backend/app/: config.py, db.py, main.py, models.py; app factory with liveness/readiness.
- backend/alembic/: env.py and 0001_baseline.py, creating system_metadata only.
- backend/tests/: 9 health/config unit tests and 1 opt-in real-MySQL health test.
- Authentication dependencies, users, credentials, token settings and auth routes were absent.
- Settings already used SecretStr for database password, explicit CORS origins, Redis/Chroma URLs and disabled LLM access.

## Behavior and design decisions

| Method / endpoint | Access | Behavior |
|---|---|---|
| POST /api/v1/auth/register | Public, signing key configured | JSON email/password; creates customer; 201 |
| POST /api/v1/auth/login | Public, signing key configured | JSON email/password; returns bearer token; 200 |
| GET /api/v1/auth/me | Active authenticated user | Returns own id/email/current role |
| GET /api/v1/admin/access | Active administrator | Read-only RBAC demonstration, no security actions |
| GET /api/v1/health/live | Public | Unchanged Phase 1 response |
| GET /api/v1/health/ready | Public | Unchanged Phase 1 MySQL/baseline-marker check |

The login contract is JSON, not OAuth2 form submission. Use the Swagger HTTPBearer Authorize control with the token returned by login. No frontend login UI is added in Phase 2.

Passwords: Argon2id via argon2-cffi (64 MiB, 3 iterations, 4 lanes); random per-password salt; rehash on successful login when parameters change. Registration accepts 12–128 characters, login 1–128. Passwords are not trimmed or transformed. Email is validated and lowercased as the documented login-identity policy. Database unique constraint prevents duplicate registrations including concurrent inserts; duplicate registration returns generic 409. It still reveals that registration could not complete for that address; email verification/privacy-preserving onboarding is not implemented.

JWT: HS256 only, environment signing secret, default 15-minute lifetime (configurable 5–60 minutes); signature, expiry, not-before, issuer and audience checked. Required claims: sub, iat, nbf, exp, iss, aud, jti. UUID subject identifies the user. No role claim is issued or trusted. Each protected request reloads role and active state from the database, so role changes, deletion and disabling affect existing tokens immediately on subsequent requests. Missing signing key returns 503 for auth and protected endpoints while health remains available. Tokens/auth responses are marked no-store.

Registration forbids extra fields including role, id, password_hash and is_active. Database role constraint allows only customer or administrator; both ORM and migration default to customer. Password hashes never appear in response models. Unknown user, wrong password, disabled user and invalid token use generic 401 with a Bearer challenge. Known/unknown login paths both perform a password-hash verification. Insufficient role is 403. Validation errors never echo submitted values; SQLAlchemy failures become safe 503 responses.

CORS now permits POST and Authorization in addition to the existing GET/Content-Type allowlist. Allowed origins remain explicit. No LLM or AI code participates in authentication, role assignment or privileged actions.

## Existing installation upgrade

From the project root with the existing virtual environment activated:

```bash
python -m pip install -r backend/requirements.txt
python scripts/configure_auth.py
cd backend
alembic upgrade head
alembic current
uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

`configure_auth.py` appends a locally generated random key to backend/.env, prints no key and refuses to replace an existing JWT_SECRET. Other environment values remain unchanged. It was run in the current workspace. For a new checkout, run scripts/init_env.py first, then scripts/configure_auth.py. A deployment may inject JWT_SECRET through its secret manager instead. Restart the API after changing configuration. The runtime must have access to a strong random key; the minimum length check does not prove entropy.

| Variable | Requirement |
|---|---|
| JWT_SECRET | Random secret of at least 32 bytes; generated locally with 48 random bytes by helper; no default |
| ACCESS_TOKEN_MINUTES | Optional; 15 by default, integer 5–60 |
| JWT_ISSUER | Optional; aegislend-api by default |
| JWT_AUDIENCE | Optional; aegislend-client by default |
| DB_* | Existing Phase 1 MySQL settings, unchanged |

Never put JWT_SECRET in a VITE_ variable, Git, logs or shared example files. Rotation invalidates existing tokens. Migration 0002 adds users with unique email, Argon2 hash, constrained role, active flag and UTC application-created timestamp. It leaves system_metadata and schema_phase=1 intact. The existing health readiness checks the Phase 1 marker, not the auth migration: confirm `alembic current` is 0002 before using authentication. `alembic downgrade 0001` deletes all users; use only on a disposable test database.

## Administrator provisioning

No public administrator signup or role-change route exists. Register the intended synthetic test account through /auth/register, then an authorized local operator with database credentials can run from backend/:

```bash
python -m app.manage set-role --email synthetic-admin@example.com --role administrator
# Explicit demotion:
python -m app.manage set-role --email synthetic-admin@example.com --role customer
```

The example address is synthetic; no account or administrator is seeded. Use the actual synthetic address you registered. The command changes only an existing active account and takes a row lock. Host/DB access is the authorization boundary for this development command. It does not create a default admin password or expose privilege assignment to HTTP or an LLM. Production operator access control and durable privilege-change audit trails remain future work.

## Actual verification results

Executed 2026-10-15, final run: **43 passed, 2 skipped, 1 warning in 6.70s**. The original 9 unit tests passed unchanged. The 34 new parametrized cases exercised real SQLAlchemy persistence in isolated SQLite databases, with random signing keys/passwords and synthetic example.com identities. These are not MySQL database tests.

Exact commands executed from `/workspace/scratch/6ff36c919e6d/aegislend/backend`:

```bash
../../.venv/bin/pytest -q
../../.venv/bin/pip check
../../.venv/bin/alembic upgrade head --sql > /tmp/aegis-phase2-upgrade.sql
../../.venv/bin/alembic downgrade 0002:0001 --sql > /tmp/aegis-phase2-downgrade.sql
../../.venv/bin/python -m compileall -q app tests alembic
../../.venv/bin/pip freeze > requirements.txt
```

Results: pytest above; pip reported no broken requirements; offline migrations emitted MySQL upgrade/reversal SQL; Python compilation succeeded. The installed Starlette test client emits the existing httpx-deprecation warning; no failure was suppressed.

Exact smoke command from `/workspace/scratch/6ff36c919e6d`:

```bash
.venv/bin/python aegislend/scripts/smoke.py
```

Passed: Vite served the app entry point, actual Vite proxy → FastAPI liveness returned 200, and readiness returned its expected 503 unavailable contract. No frontend files changed; frontend tests/build were not rerun for Phase 2. No browser-rendered check is claimed.

MySQL availability was rechecked: docker/mysql/mysqld absent and localhost:3306 unreachable. Both real-MySQL tests were skipped. No migration was executed against MySQL.

## Real MySQL verification still required

Create an empty dedicated MySQL 8.4 database such as aegislend_test_phase2 and grant a dedicated test user permissions there. Use synthetic accounts only. With test database credentials in the environment and the virtual environment active, from backend/:

```bash
export DB_NAME=aegislend_test_phase2
# Set DB_USER/DB_PASSWORD/DB_HOST/DB_PORT for that test database securely.
alembic upgrade head
alembic current
alembic check
RUN_MYSQL_TESTS=1 RUN_MYSQL_AUTH_TESTS=1 pytest -q -m mysql
```

The auth integration test refuses databases without the aegislend_test_ prefix, requires migration 0002 and a signing key, creates a random synthetic account, verifies registration/login and customer/admin authorization, and removes only its test account. Do not point it at customer data. After testing, restore normal DB settings. Test downgrade/re-upgrade only on this disposable database; actual MySQL DDL, collation, uniqueness under concurrency and migration reversal remain unverified here.

## Changed files

Modified: backend/app/config.py, backend/app/main.py, backend/app/models.py, backend/.env.example, backend/requirements.in, backend/requirements.txt, README.md. Local backend/.env had only a new random JWT_SECRET appended; it is excluded from deliverables.

Added: backend/app/auth.py, backend/app/security.py, backend/app/manage.py, backend/alembic/versions/0002_users.py, backend/tests/test_auth.py, backend/tests/test_mysql_auth.py, scripts/configure_auth.py, docs/PHASE2.md.

## Known limitations

This is the requested project phase, not a production authentication service. No email verification, MFA, password recovery, refresh tokens, per-token logout/revocation, shared rate limiting or durable auth audit events are implemented. Distributed login/register throttling and TLS are required before public deployment; the default server binds to loopback. Login/register hashing consumes memory and CPU, so do not publicly expose the service without request limits. Tokens remain usable until expiry unless the account is disabled/deleted or the signing key is rotated. Administrator MFA and audited role provisioning belong before production use. Future security/audit work must preserve these server-side authorization boundaries.

## Primary references

- https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- https://argon2-cffi.readthedocs.io/en/stable/api.html
- https://pyjwt.readthedocs.io/en/stable/api.html
