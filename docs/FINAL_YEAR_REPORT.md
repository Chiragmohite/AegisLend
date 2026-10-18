> This document describes the integrated baseline. Read [ENHANCEMENTS.md](ENHANCEMENTS.md) for the added session/OTP, incident, agent UI and appointment architecture, and [ENHANCEMENT_VERIFICATION.md](ENHANCEMENT_VERIFICATION.md) for current test evidence.

# Final-year engineering report material

## Title

AegisLend AI: An Intelligent and Secure Digital Lending Ecosystem Using Agentic AI, RAG, and Hybrid Intrusion Detection

## Abstract

AegisLend AI is an academic digital-lending demonstration integrating deterministic financial estimates, secure account access, transactional application and appointment workflows, grounded document retrieval, and observable security analytics. The system uses a React/TypeScript frontend and a FastAPI/SQLAlchemy backend with a MySQL migration target. Password hashing and signed access tokens support customer and administrator roles enforced at the API boundary. A retrieval pipeline produces source-quoted educational answers, with optional Chroma vector storage and a bounded external/CrewAI source-selection interface. A hybrid intrusion-detection subsystem combines explicit rules with an Isolation Forest trained on reproducible synthetic telemetry. A centralized Risk Engine explains its scores, while human administrators retain control over application review and permitted security acknowledgements. Automated tests cover core workflows, authorization, migrations on isolated SQLite, document processing and model persistence. Real MySQL, Windows/Docker deployment and browser execution remain verification gaps documented separately. No real lending, private customer dataset or paid-model API access is required for the default demonstration.

## Problem statement

A fragmented academic prototype can show an eligibility formula, chatbot and anomaly model without a consistent authorization or data boundary. This project investigates how to integrate those components into a coherent demonstration while preserving human decision authority, transparent limitations and reproducible testing.

## Objectives

1. Provide secure synthetic customer onboarding and server-side RBAC.
2. Make indicative eligibility explainable and separate it from review outcomes.
3. Preserve transactional application history and prevent conflicting appointments.
4. Ground educational assistant output in identifiable source documents.
5. Combine representative deterministic threat signals with anomaly scores.
6. Expose actual backend security/audit data through an authorized dashboard.
7. Provide incremental migrations, reproducible setup and honest validation evidence.

## Suggested chapter structure

1. Introduction: motivation, scope, academic/non-banking boundary.
2. Background: web authentication, deterministic EMI, RAG, agent/tool boundaries, IDS and anomaly detection.
3. Requirements: role matrix, functional requirements, constraints and assumptions.
4. System design: architecture and entity relationships from PROJECT_GUIDE.md.
5. Implementation: source modules, transaction boundaries, UI workflows and service degradation.
6. Methodology: eligibility formula, document pipeline, synthetic feature generation, rules and risk weights.
7. Testing and results: actual commands/counts from FINAL_VERIFICATION.md, negative cases and skipped infrastructure checks.
8. Security analysis: threat/control/residual-risk table, privacy decisions and privileged-action boundaries.
9. Demonstration: reproducible customer-to-admin walkthrough and screenshots captured locally.
10. Conclusion and future work.

## Methodology

The implementation extends a preserved two-phase baseline. Schema changes are added through a new dependent migration rather than rewriting user/auth tables. Input/response models separate client data from server-owned fields. Business actions are executed by authenticated services, with database constraints and optimistic locking guarding races. Eligibility uses Decimal arithmetic and product configuration. Retrieval uses deterministic lexical vectors by default; optional external selection cannot produce arbitrary facts or invoke tools. IDS training uses four sanitized counts over synthetic windows, log1p preprocessing, fixed seeds and persisted metadata. Risk bands combine explicit rule weights with an anomaly contribution and never feed the credit decision path.

## Results and interpretation

Use the exact latest verification report rather than inventing accuracy, precision, recall, throughput, approval improvement or breach-prevention claims. Passing functional tests support implemented behavior on the tested runtime. They do not establish deployment compatibility on unexecuted platforms or real-world IDS effectiveness. The live Chroma test demonstrates vector ingestion/query/deletion on a temporary local server. External inference has not been tested, and the default extractive assistant remains independent of paid credentials.

## Conclusion

The project demonstrates an integrated academic lending workflow with explainable calculations, preserved human control, source-grounded information and observable security signals. Its contribution is the integration and enforcement of boundaries across customer, administrator, retrieval and telemetry operations. Further validation is needed for real MySQL concurrency, Windows/Docker/browser operation, distributed event processing and any externally configured LLM provider. It must not be represented as a production lender, regulator-approved platform or penetration-tested banking system.

## Future work

- Real MySQL deployment and concurrency validation on the target Windows host.
- Semantic embeddings evaluated on a labeled retrieval dataset.
- IDS evaluation with appropriately sanitized labeled traffic and false-positive analysis.
- Durable event delivery, distributed counters and tamper-evident audit storage.
- MFA, verified email, recovery and revocable refresh sessions.
- Stronger document sandboxing and OCR.
- Accessibility audit and browser/device coverage.

## Citation starting points

Use your institution's required citation format and consult the primary documentation: FastAPI security guide, SQLAlchemy 2.x documentation, Alembic tutorial, Argon2-cffi documentation, PyJWT documentation, scikit-learn IsolationForest API, Chroma documentation and CrewAI agent/task documentation. Do not cite generated code as independent research evidence or fabricate publications.
