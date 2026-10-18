# Executed verification — 2026-10-17

## Baseline, before backend changes

- Existing frontend `npm test`: **13 passed, 3 files**.
- Existing frontend `npm run build`: **passed**, TypeScript + Vite, 108 modules.
- The earlier `/tmp/aegis-enhance-venv` no longer existed. A first backend command failed with executable-not-found. Recreated it with Python 3.12 and installed the unchanged pinned `backend/requirements.txt`.
- Backend baseline: **92 passed, 4 skipped, 1 warning in 19.55 seconds**.

## Final executed results

| Check | Actual outcome |
|---|---|
| Full backend `pytest -q` | **107 passed, 4 skipped, 1 warning in 20.69 seconds** |
| Focused enhancement + polish run before the final two tests were added | **32 passed, 1 warning in 10.83 seconds** |
| Frontend `npm test` | **20 passed, 4 test files** |
| Frontend `npm run build` | **Passed**; TypeScript and Vite, 110 modules |
| `npm ls --depth=0` | All declared top-level dependencies resolved |
| `pip check` | No broken requirements found |
| Python compilation | Passed for app, tests and Alembic |
| Alembic head | One head: `0007` |
| MySQL offline migration generation | Passed; SQL emitted without applying it to a database |
| SQLite migrations and model comparison | Passed within full suite, including fresh schema and preservation of a Phase 2 user |
| Historical migration comparison | All seven migration files byte-identical to prior enhanced ZIP |
| Isolation Forest synthetic evaluation | Executed; results below |
| Browser installation | Failed downloading Chromium |
| Browser E2E execution | Failed before the workflow: Chromium executable missing |

Skipped backend tests: live Chroma, MySQL readiness, MySQL authentication and MySQL domain workflow. Warning: upstream Starlette TestClient/httpx deprecation. No live MySQL, Redis, Chroma, Docker, PowerShell or external LLM integration success is claimed.

## Commands actually executed

Workspace root:

```bash
python3 -m venv /tmp/aegis-enhance-venv
/tmp/aegis-enhance-venv/bin/pip install -r aegislend/backend/requirements.txt
```

From `aegislend/backend`:

```bash
/tmp/aegis-enhance-venv/bin/pytest -q
/tmp/aegis-enhance-venv/bin/pytest -q tests/test_polish.py tests/test_enhancements.py
/tmp/aegis-enhance-venv/bin/pip check
/tmp/aegis-enhance-venv/bin/python -m compileall -q app tests alembic
/tmp/aegis-enhance-venv/bin/alembic heads
/tmp/aegis-enhance-venv/bin/alembic upgrade head --sql > /tmp/aegis-polished-mysql.sql
/tmp/aegis-enhance-venv/bin/python -m app.evaluate_ids
```

From `aegislend/frontend` (some equivalent invocations used `npm --prefix frontend` from the project root):

```bash
npm test
npm run build
npm ls --depth=0
npx playwright install chromium
AEGIS_PYTHON=/tmp/aegis-enhance-venv/bin/python npm run test:e2e
```

The last two failed because the browser could not be downloaded/found. The E2E script is extended for draft editing, chatbot-only image loading, minimization and mobile navigation, but these browser assertions were not executed successfully.

A few npm/pytest invocations initially used the wrong working directory and failed to find package/test files. They were rerun from the correct directories; no passing result is attributed to a failed attempt.

## Regression failures addressed

The first frontend regression run exposed expectations tied to the old UI: health tests still loaded `/` instead of `/status`, the portrait test expected an image on login, and a chat test expected an internal underscore-delimited mode label. Tests were updated to the explicitly approved behavior, retaining health checks and adding negative assertions against portraits on login/dashboard/landing. No auth, ownership or security assertions were removed to make failures pass. New chatbot and draft tests exercise errors and actual API request contracts through controlled test adapters; production code uses real endpoints.

## Representative 15-category security evidence

All referenced pytest tests below ran in the passing suite. Frontend HTML-rendering tests ran in Vitest. These are local synthetic examples, not proof that every variant is detected.

| Category | Malicious/suspicious case and expected result | Benign/control case |
|---|---|---|
| SQL injection | `test_signature_pair_sanitized_persistence_and_no_execution`: UNION SELECT query records evidence/incident; product results unchanged | Union education policy produces no event; ORM queries remain parameterized |
| XSS | Same parameterized test records script evidence; frontend `assistant renders hostile source text as text, never active HTML` creates no script/hostile image nodes | Ordinary policy text and source rendering preserved |
| Brute force | `test_credential_stuffing_enumeration_evidence` records repeated failures; existing auth-rate tests enforce throttling | Valid password succeeds; generic-login paired test has no incident for low-volume errors |
| Credential stuffing | Distinct synthetic failed accounts trigger correlated rule evidence | Normal authenticated browsing does not create bot restrictions |
| Path traversal | Parameterized signature test records traversal evidence; ignored query cannot select a file path | Ordinary folder-related query has no signature event |
| Command injection | Parameterized signature test records evidence; no request-service shell execution | Ordinary text mentioning a cat produces no signature event |
| Parameter tampering | `test_parameter_and_privilege_abuse_logged` rejects negative amounts with 422 and records category | Valid draft edits/eligibility calculations succeed |
| BOLA/IDOR | Draft ownership and existing application/appointment tests return 404 on cross-user access | Owner can read/edit; assistant scoped lookup returns only own records |
| API abuse | `test_flooding_bot_and_api_abuse_enforcement` produces real 429 responses | Requests below the configured limit succeed |
| Account enumeration | Multiple unknown identities produce evidence; generic-login paired test gives identical known/unknown 401 bodies | Correct credentials authenticate; registration status disclosure remains a documented limitation |
| Session abuse | Revoked copied token, expired challenge and concurrent-login tests reject invalid access | Verified session resumes; saved draft is preserved |
| Privilege abuse | Client role injection is rejected; customer admin requests denied | Authorized admin reads/actions succeed; live database role is authoritative |
| Suspicious data access | Repeated denied access plus burst produces `suspicious_data_access` | Normal own-account reads remain allowed |
| Automated flooding | Burst plus repeated rate violations records flooding evidence and 429 responses | Eight normal catalog reads remain allowed |
| Bot/automation abuse | Multiple behavioral signals record `bot_behavior`; this does not establish bot identity | Benign browsing test asserts no bot rule and no account restriction |

Additional checks: immutable draft snapshots; optimistic concurrent edits; server-derived incident action lists; rejection of invalid lifecycle transitions and duplicate restrictions; selected-session ownership; admin re-authentication audit; expired restrictions no longer blocking; OTP factor-change prohibition during a challenge; stable deadlines despite repeated competing logins; truthful recorded applied actions; scoped dashboard counts; API no-store headers; stable numerical feature schema; configurable incident threshold.

Signatures are observational, not a general WAF. Safe ORM/API use, validation, RBAC and ownership enforce the relevant boundaries. Suspicious unused query parameters may return 200 while producing a logged incident; documentation and tests do not falsely describe them as blocked.

## Executed ML evaluation

Separate synthetic training seed 42 and holdout seed 2026, 500 holdout windows (400 normal, 100 deliberately unusual):

- TN 387, FP 13, FN 0, TP 100.
- Precision: 0.8849557522.
- Recall: 1.0.
- F1: 0.9389671362.
- False-positive rate: 0.0325.

The model/feature schema was preserved. These are reproduced synthetic metrics, not an accuracy improvement claim or production attack-detection accuracy.

## Source and packaging checks

Source scan found no application shell invocation, `dangerouslySetInnerHTML`, or SQL f-string execution pattern in request code. Redis uses a fixed atomic Lua script through `redis.eval`; this is not Python/JavaScript eval of user input. Such searches are useful review checks, not a penetration test.

The release builder excludes environments, credentials, local model/data stores, caches, dependencies and build artifacts; it checks known local secret values and ZIP integrity. Original reference photos are outside the project archive. Generated artwork and its real consuming component are included. See `POLISH_FILES.md` for the exact changed-file manifest.
