# Approved enhancement report — 2026-10-17

## Scope and preservation

This is an incremental update of the supplied enhanced AegisLend repository, not a new scaffold. Password-based synthetic customer registration, Argon2id, JWT verification, database-loaded roles, persistent sessions, optional authenticator TOTP, deterministic lending calculations, RAG, optional bounded CrewAI integration, appointment capacity, audit logging and health routes remain in place.

All seven historical migrations are byte-identical to the enhanced baseline. No model/table changes or new migrations were necessary. Existing `.env` files were not edited and are excluded from the ZIP. Existing Compose files, dependencies and lockfiles are preserved. Fresh MySQL still uses port 3307; existing MySQL remains on its configured port, normally 3306.

## Application redesign

The shared navy/teal/white visual system applies across the actual routed application: landing, login/register, dashboard, profile/OTP, marketplace, eligibility, applications and review, appointments/waitlist, assistant, administration, knowledge, users, audit and Security Center. Forms, spacing, cards, status badges, responsive navigation, focus outlines and reduced-motion behavior are consistent. The mobile navigation has a real toggle with accessible state, and the admin area has a persistent subsection navigation. Sign-out failures are inline rather than browser alerts.

The landing page no longer embeds the Foundation diagnostic panel. `/status` retains the original health-check functionality with current wording. No authentication is bypassed.

Dashboard data now comes from a scoped aggregation endpoint: exact application counts by state, five latest applications and five next appointments. It does not infer balances, approvals, repayment history or credit scores. Empty and failure states remain distinct. Profile information and activity reuse existing endpoints.

Marketplace search, type filtering and comparison operate on up to 100 actual active products from the API. Rate, amount, tenure and income rules are configured values. Fees and required-document rules are explicitly shown as unconfigured, not assumed free or invented.

Draft editing reuses existing application and assessment tables. PUT edits require ownership, draft state and the current version. Every successful edit creates an immutable assessment using the existing deterministic calculator, records history and audit, and increments the application version. Stale or concurrent edits return 409 and roll back the unused assessment. Submitted applications cannot be edited; administrators cannot edit another customer's draft. Original idempotent creation keys remain associated with their application; replaying creation returns the current application, without reverting later edits.

## Chatbot and reference artwork

Only `frontend/src/components/ChatPanel.tsx` imports `AgentAvatar`. It appears inside the chatbot header and disappears when minimized. Login, dashboard, landing and other pages contain no character. Originals remain unchanged in the supplied uploads, outside the frontend; no original photograph is bundled as a frontend asset.

- New asset: `frontend/public/agents/chatbot-illustrated.png`.
- Rendering component: `frontend/src/components/AgentAvatar.tsx`.
- Consumer: `frontend/src/components/ChatPanel.tsx`, routed through `Assistant` in `customer.tsx`.
- Existing earlier generated portraits are retained as unused assets to avoid deleting user work.
- Generation method: built-in image-generation capability, not an external paid API adapter.
- Primary visual reference: `c5875b84-0082-4839-bc6b-20e7f64cf5af.jpeg` (glasses/swept hair). Secondary reference: `d3ad340a-7eee-417e-8f4f-847e82097dba.jpeg` (approachable expression). One consistent character is used; the two people are not represented as an exact merged identity.

Generation prompt: Create one NEW professionally illustrated banking assistant for the AegisLend AI chatbot. Both attached images are visual references only, never paste photographs or composite a real face onto a body. Use reference 1 (glasses, swept black hair, round face, trimmed beard, warm brown skin) as the primary recognizable character identity; reference 2 informs the youthful approachable natural expression. One character only, waist-up, centered, navy fitted blazer over a white formal shirt, natural proportions, approachable gentle smile. Clearly hand-illustrated refined editorial cartoon aesthetic with clean contour lines and simplified painted shading, NOT photorealistic, NOT anime or childish exaggerated features. Preserve primary reference's glasses, skin tone, apparent age and hair. Professional premium fintech aesthetic, modest posture with hands together, no props, no text, no watermark. Transparent background, generous clear margin, high quality edges. This will be a small chatbot header avatar and optional chatbot-only illustration.

Animation is restrained whole-image motion during an actual request, with no facial deformation or fake blinking. The image and typing indicator unmount when minimized; reduced-motion CSS disables animation. An image failure leaves the chat form usable. New turns show the question immediately, keep failed questions with a retry button, scroll to current output, and restore input focus. Sources remain expandable and rendered as text, not executable HTML. Conversation state is page-local, not durable chat storage.

The existing `/assistant` endpoint and RAG provider behavior are preserved. Account tools now call `account_service` → `account_repository` with the authenticated database user; prompt text cannot select an owner ID. Tools are read-only. No new provider credentials, model names or Astra API access are assumed.

## IDS, risk and policy changes

The existing event → rules/Isolation Forest → risk → incident/audit pipeline is retained. A reusable feature extractor makes the four-feature schema explicit without invalidating trained artifacts. New configurable settings are `IDS_INCIDENT_THRESHOLD` (default 30) and `IDS_STUFFING_THRESHOLD` (default 5). The latter counts distinct hashed attempted account identities, not raw emails. Historical ML features and model version remain unchanged because the model itself is not replaced.

Deterministic mutation policy uses server-verified pending challenges and active restrictions. ML predictions alone cannot impose restrictions. The previously broad authentication-route exemption is narrowed: only logout and challenge confirmation remain usable during a challenge/restriction. OTP enrollment/activation cannot be used to modify factors while a challenge is pending.

Incident actions now expose server-derived `allowed_actions` and validate the same lifecycle on the backend. Triaging an already actioned incident or reopening a resolved incident through an investigation action is rejected. Notes and release remain available after closure. Repeat active restrictions on the same incident are rejected. Optimistic versions still prevent lost updates.

A human administrator can require re-authentication for a selected active session belonging to the incident account. It uses the existing server-controlled 120-second challenge; repeated actions do not extend an existing deadline. The action and policy version are audited. Session revocation, restriction, release, resolution and false-positive handling remain operational. Recommendations and applied actions are distinct; a permitted read containing a suspicious unused query is logged rather than falsely reported as blocked.

Security Center now also displays actual open incidents, active restrictions and live challenges. Its action selector uses backend-permitted actions; rejected operations show errors. Incident details can be closed without leaving the page. No hardcoded live statistics are added.

## Concurrent-login behavior

Existing database locks and unique active-session reservation remain unchanged. Competing logins are rejected; successful verification retains the existing session. Tests verify expired challenges, no extension from repeat login, prevention of two active sessions, and preservation of saved drafts. The UI shows remaining time based on the server deadline and refreshes status when a hidden tab becomes visible. The countdown is presentation only; backend time controls authorization.

## API and schema changes

Additive, backward-compatible API changes:

- `GET /api/v1/dashboard`: authenticated owner's totals and recent records.
- `PUT /api/v1/applications/{application_id}`: owner-only versioned draft edits.
- `GET /api/v1/applications`: optional validated `status` filter.
- Eligibility responses additionally include stored `inputs`, subject to existing ownership/admin checks.
- Security summary adds active restriction/challenge/open incident counts.
- Incident responses add `allowed_actions`; actions accept `require_reauthentication`.
- Authenticated API responses use `Cache-Control: no-store`; responses use `X-Content-Type-Options: nosniff`.

No tables, migrations, reset operations, default credentials or automatic credit/security decisions were added. Rollback of this source release requires restoring the prior code and removing the two newly added optional environment settings if explicitly configured, because the prior settings parser forbids unknown names. Application data and draft revisions remain in the existing schema. Prior policy-v3 audit records remain historical data.

## Known limits

- No live MySQL/Redis/Chroma, Docker, Windows PowerShell, external LLM/CrewAI or real-browser verification was possible in this run. SQLite tests are not proof of MySQL locking behavior.
- Browser download failed; responsive CSS, focus behavior and asset loading have unit/source checks but still need actual browser validation. This is not a visually verified release.
- The 15-category security matrix contains representative local cases, not exhaustive attack coverage or a penetration test. Signatures inspect URL/query input only. Bot signals are suspicion, not identity proof.
- Telemetry windows remain process-local. No durable queue, cross-event incident grouping, automated retention or tamper-evident audit store was added. Incident uniqueness is per security event.
- Authentication remains synthetic email/password with optional TOTP. Public registration status can reveal account existence. No MPIN, mandatory MFA, email verification, self-service password recovery or refresh-token rotation. Signing-key rotation requires the documented authenticator recovery process.
- Concurrent-login alerts use polling. User-agent hashes do not establish device identity. Login conflicts apply generally, not only while editing an application. Refresh loses the in-memory browser token; existing server session recovery applies.
- No customer document upload/verification, fees schema, repayment ledger, sanction generation or personalized lending recommendation model is added. Financial inputs remain self-reported synthetic data.
- Appointment waitlist availability is manual/in-app; no automatic promotion, SMS/email delivery or new scheduling policy.
- Optional Astra access in this environment is not proof of API access; no external call was made or claimed.

## Demo walkthrough

1. Run the setup/migration/seed commands in README; bootstrap a synthetic administrator only if one does not already exist.
2. Register a synthetic customer and verify the dashboard has no invented financial data or portrait.
3. Filter/compare products, calculate an estimate, create and edit a draft, then submit.
4. Book or reschedule an appointment and inspect waitlist behavior.
5. Open Assistant: inspect the new illustration, ask about your applications and a policy question, expand citations, minimize/reopen.
6. Use a second login attempt to trigger the existing session challenge; verify before its deadline.
7. Sign out, sign in as administrator, review the application and use a controlled probe in Security Center.
8. Inspect an incident's evidence, permitted actions and audit history. Use only synthetic accounts for any restriction test.

Suggested screenshots after local browser verification: desktop dashboard, mobile navigation, marketplace comparison, edited draft, chatbot with citations, incident detail, and identity challenge. No screenshots are fabricated in this release.
