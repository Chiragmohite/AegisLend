# Verification and release record

Executed in the provided Linux workspace on 2026-10-15. This records actions actually run, not intended checks.

## Results

| Check | Actual outcome |
|---|---|
| Original Phase 2 ZIP inspection | 45 files matched the starting workspace; no later migration existed |
| Original migration preservation | 0001_baseline.py and 0002_users.py byte-identical to Phase 2 ZIP |
| Core-only dependency environment | Installed from requirements.txt; 73 passed, 4 skipped, 1 existing Starlette/httpx deprecation warning |
| Full installed environment with live Chroma enabled | **74 passed, 3 skipped in 28.22s** |
| Skipped tests in full run | Three real-MySQL tests: readiness, auth and full domain workflow |
| Frontend clean dependency installation | npm ci --prefer-offline succeeded; 213 packages installed |
| Frontend Vitest | **11 passed across 3 test files** |
| TypeScript and Vite build | Passed; 103 modules transformed |
| Python compilation | Passed for app/tests/alembic |
| Dependency consistency | pip check: No broken requirements found |
| Migration head/chain | One head: 0003, with 0003 → 0002 → 0001 |
| SQLite migration execution | Fresh schema, upgrade preserving an existing Phase 2 user, downgrade to Phase 2 and re-upgrade passed on temporary databases |
| Model/schema comparison | Alembic compare_metadata returned no differences on migrated SQLite |
| MySQL SQL generation | Full upgrade and 0003→0002 reversal SQL generated successfully; not executed on MySQL |
| Customer-to-admin API integration | Registration, login, products, estimate, draft/submission/history, appointment, sourced answer, suspicious event, risk, admin review/decision and IDOR/admin denial passed |
| Concurrent booking | Two simultaneous attempts produced one 201 and one 409 on isolated SQLite |
| Chroma HTTP integration | Real temporary Chroma 1.5.9 server: index, query, source validation and delete passed |
| CrewAI compatibility | CrewAI 1.15.28 and Agent/Task/Crew/LLM imported successfully; external inference not run |
| Live Vite proxy smoke | React entry point 200, FastAPI liveness 200, expected unavailable-MySQL readiness 503 |
| Compose syntax | Three files parsed as YAML; fresh port 3307 and supporting-only services verified structurally |
| Windows PowerShell | Scripts provided and referenced paths checked, but PowerShell unavailable; not executed |
| Docker/MySQL/Redis services | Executables unavailable here; no real MySQL or Redis execution claimed |
| Browser E2E | Attempted; blocked because Chromium download returned invalid/truncated ZIPs and executable was absent |
| Browser runner | Node syntax check passed; browser workflow itself unverified |
| Security review | Guard/ownership/validation/token/rate-limit/body-limit/source-injection and telemetry-failure tests passed; source scan found only fixed Redis Lua eval, no Python eval/exec or interpolated user SQL |

## Exact commands run

From `/workspace/scratch/6ff36c919e6d/aegislend/backend`:

```bash
PATH="/workspace/scratch/6ff36c919e6d/.venv/bin:$PATH" NO_PROXY=127.0.0.1,localhost RUN_CHROMA_TESTS=1 ../../.venv/bin/pytest -q
../../.venv/bin/pip check
../../.venv/bin/python -m compileall -q app tests alembic
../../.venv/bin/alembic heads
../../.venv/bin/alembic upgrade head --sql > /tmp/aegis-final-mysql-upgrade.sql
../../.venv/bin/alembic downgrade 0003:0002 --sql > /tmp/aegis-final-mysql-downgrade.sql
```

A separately created `/tmp/aegis-core-venv` installed only the core lock and executed:

```bash
/tmp/aegis-core-venv/bin/python -m pytest -q
```

From `aegislend/frontend`:

```bash
npm ci --prefer-offline
npm test
npm run build
npm run test:e2e
```

The first three succeeded; test:e2e failed before starting its workflow because the Chromium executable was unavailable. A prior Playwright Chromium installation attempt downloaded invalid/truncated archives. No browser success or visual QA is asserted.

From the workspace root:

```bash
.venv/bin/python aegislend/scripts/smoke.py
PATH="$PWD/.venv/bin:$PATH" NO_PROXY=127.0.0.1,localhost RUN_CHROMA_TESTS=1 .venv/bin/python -m pytest -q aegislend/backend/tests/test_chroma_live.py
node --check aegislend/frontend/e2e/smoke.cjs
```

The Chroma-only adapter run passed (1 test in 8.87s), then passed again within the complete suite. The dependency resolver/import checks selected Pydantic 2.12.5, Chroma 1.5.9 and CrewAI 1.15.28; the optional lock contains their resolved environment, with uvloop excluded on Windows. Import/installation compatibility does not prove a paid provider call works.

## Discovered and corrected failures

- URL query plus-encoding initially prevented a suspicious-pattern match. Decoding now handles plus-encoded whitespace; detection and telemetry-degradation tests pass.
- Retrieval initially missed singular/plural appointment terms. A documented normalizer and matching stop-word set fixed the tested case.
- Chroma's first live attempt exposed missing SOCKS-proxy support in this environment. socksio is now pinned. The final adapter uses explicit HTTP timeouts and passed the real HTTP test.
- Optional CrewAI dependency resolution required a compatible Pydantic pin; core and optional environments were tested separately.

No failed test was deleted or suppressed to obtain passing results. The existing MySQL auth test's expected revision was updated to the new head; historical migrations were not altered. MySQL tests remain explicitly opt-in and restricted to a dedicated test database where applicable.

## Verification boundaries

SQLite tests do not establish MySQL collation, row-lock or DDL behavior. MySQL foreign-key collation was aligned in source and SQL generation, but actual execution and concurrency must still be verified on MySQL 8.4. Docker image startup, target Windows scripts and real browser layouts remain unverified. Redis fallback/fail-closed design is implemented but a live Redis service was unavailable. External LLM/CrewAI generation is unverified; default local extraction is tested.

This is functional test evidence, not a penetration test, regulatory assurance, performance benchmark or real-world IDS accuracy study. Academic synthetic model results should not be presented as such.

## Release checks

The release builder excludes .env files, virtual environments, node_modules, caches, built assets, local databases, IDS artifacts and older ZIPs. It scans candidate file bytes for secret values found in local environment files and checks ZIP CRC integrity. The final delivery message reports the actual packaging result. All source, migration, test, setup and documentation files are retained.
