> Historical phase record. For the current integrated build, see README.md, PROJECT_GUIDE.md and FINAL_VERIFICATION.md.

# Phase 1 verification record

Executed on 2026-10-15 in the provided workspace.

| Check | Actual result |
|---|---|
| Backend pytest | 9 passed, 1 skipped |
| Python dependency consistency (`pip check`) | No broken requirements found |
| Alembic upgrade SQL generation | Passed; emitted MySQL DDL and phase marker insert |
| Alembic downgrade SQL generation | Passed; emitted baseline reversal SQL |
| Python source compilation | Passed |
| Frontend Vitest | 6 passed across 2 test files |
| TypeScript and Vite production build | Passed; 97 modules transformed |
| Live HTTP smoke | Passed: Vite entry point HTTP 200 and Vite → FastAPI liveness HTTP 200 |
| Live readiness response | HTTP 503, database unavailable; expected failure state |
| Real MySQL connectivity and migrated schema | Not verified; no server available |
| Browser-rendered end-to-end test | Not run; Playwright library present but Chromium executable absent |
| Redis / ChromaDB startup and integration | Not run; Docker absent; services unused in this phase |
| LLM API integration | Not attempted; API access unverified and provider disabled |

MySQL availability checks: docker, mysql, mysqld and mariadbd executables were absent; localhost port 3306 was not reachable. The real database test is deliberately skipped unless RUN_MYSQL_TESTS=1. Mocked readiness tests cover success, database exceptions and missing migration marker, but do not validate actual MySQL semantics.

One warning remains: the installed Starlette test client deprecates its httpx integration in favor of httpx2; tests still pass. npm also prints an environment-level unknown `http-proxy` config warning, and jsdom's transitive whatwg-encoding dependency reports a deprecation. No test failure was suppressed.

The first separately launched server could not be reached by a later shell call in this environment. Running both servers and probes inside the same smoke-test process verified the connection successfully. The script terminates its servers on completion.

## Remaining MySQL acceptance checks

On a host with Docker Compose or MySQL 8.4:

1. Initialize environment files; start MySQL and apply `alembic upgrade head`.
2. Run `alembic current`, `alembic check` and `RUN_MYSQL_TESTS=1 pytest -q -m mysql`.
3. On a disposable database, downgrade to base and reapply the migration.
4. Run `python scripts/smoke.py --expect-ready` from the project root.
5. Open the UI in a browser and confirm both API Connected and MySQL Ready, then check retry after stopping/restarting the backend.

Phase 1 source and all feasible local checks are complete. Full database acceptance remains pending these real-MySQL checks.
