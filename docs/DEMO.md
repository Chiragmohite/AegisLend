> This document describes the integrated baseline. Read [ENHANCEMENTS.md](ENHANCEMENTS.md) for the added session/OTP, incident, agent UI and appointment architecture, and [ENHANCEMENT_VERIFICATION.md](ENHANCEMENT_VERIFICATION.md) for current test evidence.

# Demonstration walkthrough and screenshot plan

## Before the demonstration

Follow the current README, apply migration 0003, seed the synthetic catalog/policy, bootstrap a synthetic administrator and train the synthetic IDS model. Start both servers. Confirm `/health/application` returns ready. Never demonstrate against real customer records. Keep screenshots free of passwords, JWTs, environment files and terminal secrets.

## Customer journey

1. Open the landing page. Explain that this is an academic ecosystem with human decision authority.
2. Register a synthetic `@example.com` customer using a newly chosen password. The dashboard loads real backend data. Refresh requires re-login because the token is held only in memory.
3. Edit the permitted display name/employment profile fields. Show a success response.
4. Browse the three seeded demo products. Open Estimate & apply; use synthetic income 50,000, obligations 5,000, amount 100,000, tenure 24, salaried.
5. Calculate. Explain EMI, estimated repayment, DTI and each rule reason. The result is not a loan approval. Repeat with low income to show an explainable non-qualifying estimate.
6. Create a draft, inspect the stored assessment, then submit for review. Expand history.
7. Book one available consultation. The UI shows local browser time; server policy is UTC. Cancel it and show that its slot returns to availability. A concurrent duplicate must fail rather than appear successful.
8. Ask the assistant “How does human application review work?” Expand sources and show page/chunk metadata. Explain that the local mode quotes vetted source text rather than inventing policy.
9. Attempt an administrator URL while logged in as a customer. Explain that frontend routing redirects for UX and backend APIs independently return 403.

## Administrator journey

10. Sign out and log in with the explicitly bootstrapped administrator. Open Admin → Applications.
11. Move the customer's submitted application to under review with a note, then approve or reject with another note. Explain optimistic version checks and the prohibition on self-review.
12. Open Knowledge. Upload a small UTF-8 synthetic policy; inspect index status. Query it from a customer session, then demonstrate re-indexing/removal. Vector outages show local fallback, not fake vector success.
13. Open Security Center. Click Generate controlled probe, refresh, and inspect the actual recorded event, rules, numeric features, correlation ID and Risk Engine history. The probe is an explicit synthetic event, not a real attack.
14. If the model is untrained, click Train synthetic IDS model. Explain that its metrics are not a published real-world accuracy result.
15. Acknowledge or escalate one event with a human note. Show the audit trail. No automatic user blocking, permission change or loan decision occurs.
16. Show product settings, read-only user roles and the advisor calendar. Finish with health/limitations rather than a production-readiness claim.

## Suggested screenshots

| Screenshot | Evidence to show |
|---|---|
| Landing + status | Branding, demo disclosure, real API status |
| Eligibility result | EMI, rule reasons, assumptions and disclaimer |
| Application history | Customer submission and human-reviewed transitions |
| Appointment screen | Real booked/cancelled entries and timezone policy |
| Assistant answer | Exact source text, document title and chunk/page references |
| Security Center | Actual event totals, severity counts, rules and model health |
| Audit record | Actor/target/correlation and safe metadata only |
| Test terminal | Actual counts, skipped MySQL tests and environment limits |

Browser screenshots were not generated or validated during the build because Chromium download failed. Capture these after starting the application locally.
