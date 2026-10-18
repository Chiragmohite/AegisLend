> Historical enhancement record. For the latest approved changes and chatbot-only asset placement, see [POLISH_REPORT.md](POLISH_REPORT.md) and [POLISH_VERIFICATION.md](POLISH_VERIFICATION.md).

# Enhancement verification — 2026-10-16

## Actual results

- Core dependencies installed into a fresh isolated `/tmp/aegis-enhance-venv` from the unchanged core pinned requirements. `pip check`: no broken requirements.
- Full backend: **92 passed, 4 skipped, 1 warning in 17.80 seconds**. Skips: live Chroma and three MySQL tests. The warning is an upstream Starlette TestClient/httpx deprecation.
- Focused enhancement tests after the last session-status response adjustment: **19 passed**. Covers four signature evidence cases, benign signatures, challenge expiry/recovery, revoked copied token, admin restrictions/releases/stale updates, scoped assistant, rescheduling rollback, TOTP enrollment/login/replay and known vector, capacity/idempotency/waitlist, stuffing/enumeration, API flood/bot signal, parameter/privilege abuse, suspicious access, attendance and concurrent login.
- Frontend: **13 passed across 3 files**. Includes original workflows plus portrait fallback and OTP challenge UI.
- Production build: **passed**, TypeScript then Vite, 108 modules transformed.
- Python compilation: passed. Alembic: one head `0007`; MySQL offline upgrade SQL generated successfully.
- Actual temporary SQLite migrations and metadata comparison passed within backend tests, including Phase 2 user preservation. These tests are not a substitute for real MySQL DDL, collation and lock verification.
- Original migrations `0001`, `0002`, `0003` byte-compared with the prior complete ZIP: unchanged.
- Generated portrait assets visually inspected; source photos preserved. No browser visual QA is claimed.
- Browser installation attempted again: download returned invalid/truncated ZIPs. E2E command failed before execution because Chromium was missing.

## Exact commands used

From workspace root:

```bash
python3 -m venv /tmp/aegis-enhance-venv
/tmp/aegis-enhance-venv/bin/pip install -r aegislend/backend/requirements.txt
```

From `aegislend/backend`:

```bash
/tmp/aegis-enhance-venv/bin/pytest -q
/tmp/aegis-enhance-venv/bin/pytest -q tests/test_enhancements.py
/tmp/aegis-enhance-venv/bin/pip check
/tmp/aegis-enhance-venv/bin/python -m compileall -q app tests alembic
/tmp/aegis-enhance-venv/bin/alembic heads
/tmp/aegis-enhance-venv/bin/alembic upgrade head --sql > /tmp/aegis-enhanced-mysql.sql
/tmp/aegis-enhance-venv/bin/python -m app.evaluate_ids
```

From `aegislend/frontend`:

```bash
npm test
npm run build
npx playwright install chromium
AEGIS_PYTHON=/tmp/aegis-enhance-venv/bin/python npm run test:e2e
```

The first two passed. The last two failed due to unavailable browser binaries/downloads, not a completed workflow assertion.

## Executed synthetic ML evaluation

500 holdout windows, RNG seed 2026; training remains separate with seed 42. Confusion matrix: TN 387, FP 13, FN 0, TP 100. Precision 0.88496, recall 1.0, F1 0.93897, false-positive rate 0.0325. The synthetic abnormal distribution is deliberately well separated; these numbers do not establish real attack detection performance.

## Failures corrected or bounded

- The previous optional-package environment crashed during PyArrow import. A clean core environment was used; optional external/CrewAI packages are not reverified in this release.
- Expected migration-head assertions were updated for additive migrations. The signed-role injection test now uses a real persisted session and still asserts administrator denial.
- Frontend logout tests now mock the actual revocation endpoint and await completion; waitlist requests have explicit fixtures.
- A new test selector used an unsupported `exact` option. It was replaced with an exact-name regular expression and the production build passed.
- Two command attempts used the wrong working directory; they failed and were rerun from the correct directory. No success is attributed to those attempts.

## Unverified boundaries

No live MySQL, Redis, Docker, PowerShell, external LLM or browser execution is claimed. No penetration test, production security assurance or comprehensive detection of all attack variants is claimed. Remaining functional boundaries are listed in ENHANCEMENTS.md.
