# ClaimKit Product Requirements

## Problem

Freight brokers and transportation companies lose money because they fail
to recover charges for:

1. **Driver detention time** — driver waits past free time at pickup or
   delivery.
2. **Loading and unloading delays** — dock delays beyond the scheduled
   window.
3. **Additional delivery expenses** — re-delivery, storage, lumper fees.
4. **Missed appointments** — appointment missed through no fault of the
   carrier.
5. **Unexpected transportation costs** — detours, tolls, or accessorials
   not in the original quote.

Much of the supporting evidence is scattered across emails, receipts,
photographs, and documents.

## Product

A platform that collects evidence, identifies recoverable charges,
assembles claim packages, and tracks reimbursement. A company uploads its
shipment documents and receives a report showing which expenses it may be
entitled to recover.

## Users

- Freight brokers (primary paying customer).
- Transportation / carrier operations teams.
- Finance / accounts-receivable staff who chase reimbursement.

## Functional requirements

### 1. Evidence collection

- Upload documents (PDF, image, email text) per shipment.
- Store originals in Cloudflare R2; keep an `evidence` record per file
  with type, source, and extraction status.
- Evidence must be linkable to a shipment and, where possible, to a
  specific charge.

### 2. Document extraction

- Extract, per document: shipment reference, dates/times (arrival,
  departure, appointment), amounts, parties, signatures.
- Return a confidence per field; low-confidence fields are flagged for
  human review, never silently accepted.
- The starter's rule-based extractor is a stand-in for an LLM call
  behind the same interface.

### 3. Shipment and expense matching

- Match each expense / charge to the right shipment, leg, and contract
  terms (free time, hourly detention rate, accessorial schedule).
- Detention calculation (normative):
  `billable_hours = max(0, waited_hours − free_hours)`;
  `amount = billable_hours × hourly_rate`, rounded to 2 decimals.
  Waited time under free time recovers $0 — that is correct, not an error.

### 4. Claim packet generation

- A packet per claim: claim summary, charges with amounts and basis,
  matched evidence list, deadline, and a completeness checklist
  (missing evidence must be listed, not hidden).

### 5. Claim deadline tracking

- Every claim has a filing deadline. Dashboard surfaces overdue first,
  then due within 7 days, then the rest.
- Deadline monitoring runs on a schedule (Redis + Celery in production).

### 6. Email follow-up automation — with human approval

- **Rule: no external action without human approval.**
- Follow-ups are drafted automatically and stored as `draft`.
- A human must approve a draft (recorded with approver + timestamp)
  before it can be sent. `send_followup()` raises
  `ApprovalRequiredError` for any unapproved draft.
- The starter ships no email transport: sending is a logged no-op
  until an email provider is deliberately configured.

### 7. Reimbursement tracking

- Claim statuses: `draft` → `ready` → `submitted` → `paid` / `denied`
  (plus `partially_paid` in production).
- Track amount claimed vs. amount recovered per claim and in aggregate.

## Non-functional requirements

- **Auditability:** every approval, send, and status change is logged
  (audit log, Days 61–75).
- **Access control:** role-based access — admin / staff / viewer
  (Days 61–75).
- **Accuracy:** document-processing accuracy is tested against a
  labelled set before release (Days 61–75).
- **Error handling:** partial extraction or missing evidence degrades
  gracefully and is visible to the user.
- **Privacy:** sample data is clearly labelled; real customer documents
  are never included in the repo or in tests.

## Out of scope for the starter

- Live Stripe billing, live Supabase Auth enforcement, live R2 uploads,
  live LLM calls, live email sending. Each is a deliberate, configured
  step — see `docs/architecture.md`.
