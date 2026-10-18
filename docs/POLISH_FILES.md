# Exact change manifest — approved polish release

Compared byte-for-byte with `AegisLend_AI_Enhanced.zip` from the prior enhancement. No source files removed. Historical migrations and dependency locks are unchanged.

## Modified files

- `README.md`
- `backend/.env.example`
- `backend/app/assistant_tools.py`
- `backend/app/auth.py`
- `backend/app/config.py`
- `backend/app/domain_routes.py`
- `backend/app/ids.py`
- `backend/app/incident_routes.py`
- `backend/app/main.py`
- `backend/app/schemas.py`
- `backend/app/security_policy.py`
- `docs/API.md`
- `docs/ENHANCEMENTS.md`
- `docs/ENHANCEMENT_VERIFICATION.md`
- `frontend/e2e/smoke.cjs`
- `frontend/src/App.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/Foundation.tsx`
- `frontend/src/admin.tsx`
- `frontend/src/client.ts`
- `frontend/src/components/AgentAvatar.tsx`
- `frontend/src/components/IncidentCenter.tsx`
- `frontend/src/components/SessionChallenge.tsx`
- `frontend/src/customer.tsx`
- `frontend/src/index.css`
- `frontend/src/ui.tsx`
- `frontend/src/workflows.test.tsx`

## Added files

- `backend/app/account_repository.py`
- `backend/app/account_service.py`
- `backend/tests/test_polish.py`
- `docs/POLISH_FILES.md`
- `docs/POLISH_REPORT.md`
- `docs/POLISH_VERIFICATION.md`
- `frontend/public/agents/chatbot-illustrated.png`
- `frontend/src/components/ChatPanel.tsx`
- `frontend/src/components/DraftEditor.tsx`
- `frontend/src/polish.test.tsx`

## Responsibilities

- Shared frontend/routed pages: banking design system, responsive navigation, real dashboard/marketplace, chatbot-only imagery.
- DraftEditor and domain routes/schemas: owner-only optimistic editing and immutable eligibility snapshots.
- ChatPanel, AgentAvatar and account tool/service/repository: illustrated identity, error/retry behavior and authenticated read scope.
- Auth, security policy, incident routes and IDS: factor-change guard, validated state/action transitions, recorded enforcement and configurable correlation thresholds.
- Tests and browser script: expanded synthetic regression coverage; browser script remains unverified because Chromium is unavailable.
- README and docs: current instructions, exact outcomes, API inventory, asset provenance and honest limitations.
