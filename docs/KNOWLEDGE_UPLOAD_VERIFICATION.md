# Knowledge documents and upload verification

Only new documents and one focused test were added. No production code, retrieval filters, seed behavior, schemas, routes, authentication, frontend, Docker or database configuration changed.

## Rules inspected

lending.assess checks all five conditions: product.min_amount <= amount <= product.max_amount; product.min_months <= months <= product.max_months; monthly_income >= product.min_income; (rounded EMI + obligations) / monthly_income <= product.max_dti; employment is salaried or self_employed.
EMI: P*r*(1+r)^n/((1+r)^n-1), r=annual_rate/1200; zero rate uses P/n. Decimal rounding is half-up to two decimals. Estimated repayment is rounded EMI times months. Ratio comparison uses the unrounded ratio; displayed ratio is rounded to four decimals. No credit score or bureau check. INR academic estimates exclude fees, taxes and insurance.

Seed defaults (not verified live configuration):
| Product | Amount range INR | Months | Annual indicative rate | Minimum monthly income INR | max_dti |
|---|---|---|---|---|---|
| Personal Growth | 10000–500000 | 6–60 | 12% | 20000 | 0.4 |
| Education Path | 10000–1500000 | 6–60 | 8.5% | 15000 | 0.4 |
| Business Start | 10000–2500000 | 6–60 | 14% | 30000 | 0.4 |
Existing seed preserves existing products; these numbers are not assumed to be current live values. The knowledge document therefore references configured product limits rather than asserting fixed current values.

EligibilityInput: valid product UUID, positive income <=10000000, obligations 0..10000000, positive amount <=100000000, months 1..360, employment salaried/self_employed/student/unemployed; money has two decimal places. ApplicationInput adds UUID request_key. Active product required. Passing input validation is distinct from all eligibility checks passing. Draft/submission does not automatically approve or require indicative_eligible=true. Authorized human review transitions submitted → under_review → approved/rejected, requires a note, and prevents self-review.

No applicant document attachments or definitive checklist/verification model found. KnowledgeDocument holds educational reference title/content/hash/chunks/status/error/uploaded_by/timestamp; it is not applicant evidence. The illustrative identity/address/income examples are explicitly demonstration suggestions, not implemented requirements.

## Upload integration

The test authenticates synthetic customer/admin accounts through existing auth endpoints. It sends the actual two Markdown files as multipart uploads to POST /api/v1/admin/documents, verifies customer upload returns 403, admin upload returns 201 and local_ready, and duplicate upload returns 409. It then calls POST /api/v1/assistant as the customer. Citations are checked against persisted KnowledgeDocument IDs, chunk numbers and exact source text in the isolated SQLite database. No direct document insertion, hardcoded answers or seeded replacement policy was used.

These uploads occurred ONLY in an isolated temporary test database. This does not update the user's Windows/MySQL application. To deploy the content, sign in to the existing application as administrator, open knowledge management, and upload the two files in docs/knowledge individually. The filenames become citation titles. If identical content is already indexed, the API returns 409 rather than duplicating it. Do not upload this report or the test file as knowledge.

## Tests actually executed

From project root using existing /tmp/aegis-rag-venv (Python 3.12.14, project pinned dependencies):
```
PYTHONPATH=backend /tmp/aegis-rag-venv/bin/python -m pytest backend/tests/test_knowledge_upload.py -q -s
source /tmp/aegis-rag-venv/bin/activate
export PYTHONPATH=backend
python -m py_compile backend/app/rag.py
python -m pytest backend/tests -q -rs
```
Upload workflow: 1 passed. Compilation: passed. Full suite: 121 passed, 4 skipped, 0 failures, 1 upstream Starlette/httpx deprecation warning, 23.32s.
The first upload trial surfaced distracting sentence fragments and checklist text in eligibility results. Only document wording/length and focused assertions were adjusted; the final trial passed with eligibility citations restricted to the eligibility document and human-review citations restricted to the existing policy.

Live checks unavailable: no Docker executable or reachable localhost ports 3306/8000/8001 in this environment. Three opt-in real MySQL tests and one live Chroma HTTP test were skipped. Mocked Chroma relevance tests remain passing in the full suite. No user's live records were read or modified. Browser rendering was not retested; answers/citations below are real API responses.

## Exact before/after API answers

### How does human application review work?

**before**

[1] Only an authorized human administrator can review an application and mark it approved or rejected.
[1] An administrator first moves submitted applications to under review and records a decision with a note.
[1] A customer creates a draft and submits it for review.
[1] Customers can cancel drafts and submitted applications.

Academic information only. These excerpts are not a loan approval or financial advice.

[1] Academic demonstration policy, chunk 0 (zero-based), document ID 3ed5d12c-e31d-4330-a789-2789d4c05d7c.

**after**

[1] Only an authorized human administrator can review an application and mark it approved or rejected.
[1] An administrator first moves submitted applications to under review and records a decision with a note.
[1] A customer creates a draft and submits it for review.
[1] Customers can cancel drafts and submitted applications.

Academic information only. These excerpts are not a loan approval or financial advice.

[1] Academic demonstration policy, chunk 0 (zero-based), document ID 3ed5d12c-e31d-4330-a789-2789d4c05d7c.

### How is loan eligibility calculated?

**before**

I could not find enough relevant information in the current knowledge base to answer that question. Please ask an administrator to add a relevant document.

Academic information only. These excerpts are not a loan approval or financial advice.


**after**

[1] # Academic Demo — Preliminary Eligibility Loan eligibility is calculated from five checks: income must meet the selected product minimum, requested amount and tenure must be within its configured ranges, employment must be salaried or self_employed, and (rounded monthly installment + existing monthly obligations) / monthly income must not exceed the product max_dti threshold; all five must pass, without guaranteeing approval.
[1] Eligibility repayment capacity is assessed using EMI = P*r*(1+r)^n/((1+r)^n-1), where P is requested amount, r is the product annual percentage rate / 1200 and n is months; at zero interest EMI = P/n, rounded half-up to two decimals, with estimated repayment equal to rounded EMI times n.

Academic information only. These excerpts are not a loan approval or financial advice.

[1] eligibility-explained.md, chunk 0 (zero-based), document ID bce6ea6b-2f5b-4a9e-a361-cf06d8b9013d.

### What documents are required to apply for a loan?

**before**

I could not find enough relevant information in the current knowledge base to answer that question. Please ask an administrator to add a relevant document.

Academic information only. These excerpts are not a loan approval or financial advice.


**after**

[1] # Academic Demo — Illustrative Document Checklist Documents required to apply: this Academic Demo illustrative checklist suggests fictional identity proof, address proof and income statements for discussion only, not official lending requirements or enforced requirements.
[1] No definitive required-document checklist or customer attachment-verification workflow exists in this application; the form takes structured inputs, while administrator uploads are educational knowledge references.
[1] Use synthetic examples only; do not upload real personal documents.

Academic information only. These excerpts are not a loan approval or financial advice.

[1] academic-demo-illustrative-document-checklist.md, chunk 0 (zero-based), document ID 64d8399d-c9fd-495d-b5ea-38f5f6fb0e1f.

### What is the orchid scholarship deadline?

**before**

I could not find enough relevant information in the current knowledge base to answer that question. Please ask an administrator to add a relevant document.

Academic information only. These excerpts are not a loan approval or financial advice.


**after**

I could not find enough relevant information in the current knowledge base to answer that question. Please ask an administrator to add a relevant document.

Academic information only. These excerpts are not a loan approval or financial advice.
