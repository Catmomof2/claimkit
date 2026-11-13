# ClaimKit Architecture

## Overview

ClaimKit is a full-stack claims-recovery platform for freight brokers and
transportation companies. A shipment and its scattered evidence (BOL, POD,
invoices, emails, photos) go in; a reviewable claim packet with recoverable
charges, matched evidence, and a filing deadline comes out.

```
Browser (Next.js) ──► FastAPI ──► PostgreSQL
                        │  ▲
                        │  └─ Redis + Celery (background jobs)
                        ▼
              Supabase Auth · Cloudflare R2 · LLM API · Stripe
```

## Components

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS | Dashboard, detention calculator, deadline list, claim review, approval UI |
| Backend | Python 3.12 + FastAPI | REST API, claim calculation, packet assembly, follow-up drafts |
| Database | PostgreSQL (SQLAlchemy) | Shipments, charges, claims, evidence, deadlines, audit log |
| Auth | Supabase Auth | JWT auth; role-based access (admin / staff / viewer) — see roadmap Days 61–75 |
| File storage | Cloudflare R2 | Original documents and generated claim packets (S3-compatible) |
| AI processing | LLM API + document extraction | Extract dates, times, amounts, parties from unstructured documents |
| Background jobs | Redis + Celery | Extraction, matching, packet generation, scheduled deadline checks |
| Payments | Stripe | Subscription billing (Days 76–90) |
| Hosting | Cloudflare + app hosting | Frontend on Cloudflare Pages (or equivalent); API on a container host |
| CI | GitHub Actions | Frontend + backend tests on every push / PR |

## Data model

See `database/schemas.sql`. Core tables:

- `shipments` — one row per load (origin, destination, carrier, dates).
- `charges` — one recoverable charge per shipment: `detention`,
  `loading_delay`, `unloading_delay`, `additional_delivery`,
  `missed_appointment`, `unexpected_transport`. Each has an amount,
  a basis (hours × rate, or a receipt amount), and a status.
- `claims` — a claim groups charges for one shipment + counterparty,
  with `status` (`draft` → `ready` → `submitted` → `paid` / `denied`)
  and a `filing_deadline`.
- `evidence` — a document / photo / email linked to a shipment or
  charge, stored in R2, with extraction results.
- `deadlines` — filing / response deadlines per claim, with reminders.
- `audit_log` (roadmap) — who did what, when; every approval and send.

## Request flow

1. **Upload.** Frontend uploads documents → API stores the file in R2,
   creates an `evidence` row, and enqueues an extraction job (Celery).
2. **Extract.** `document_processing/extractor.py` pulls structured fields
   (arrival / departure, free time, amounts, signatures). The starter
   ships a rule-based stub; production replaces `extract_charges()` with
   an LLM call behind the same interface, so callers never change.
3. **Match.** The claims service matches each extracted charge to a
   shipment, computes the recoverable amount (e.g. detention:
   `max(0, waited_hours − free_hours) × hourly_rate`), and flags
   charges that lack supporting evidence.
4. **Assemble.** Packet generation bundles the claim, its charges, and
   its evidence into a single reviewable packet (PDF in production).
5. **Review + approve.** A human reviews the packet and approves it.
   Follow-up emails are **drafts only** until approved — see below.
6. **Track.** Deadlines are checked on a schedule; at-risk claims are
   surfaced on the dashboard.

## Human-approval gate (non-negotiable)

No external action — no email, no claim submission to a counterparty —
happens without an explicit human approval record.

- `backend/automation/followups.py`: `draft_followup()` creates a draft.
  `approve_followup()` records approver + timestamp. `send_followup()`
  raises `ApprovalRequiredError` unless the draft is approved, and the
  starter's `send` implementation is a logged no-op (no SMTP configured).
- The API exposes the same gate: there is no endpoint that sends mail.
  Adding one must go through `approve_followup()` first, and must write
  an `audit_log` row.
- Tests in `tests/backend/test_approval_gate.py` assert this: an
  unapproved draft cannot be sent, period.

## Configuration

Environment variables (never commit real values; use `.env`, gitignored):

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL DSN; unset → in-memory sample store |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` | Auth |
| `R2_ENDPOINT` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET` | File storage |
| `LLM_API_KEY` | Document extraction (when the stub is replaced) |
| `REDIS_URL` | Celery broker |
| `STRIPE_SECRET_KEY` / `STRIPE_PRICE_ID_*` | Billing (Days 76–90) |
| `NEXT_PUBLIC_API_URL` | Frontend → backend base URL |

## What is a stub in this starter, and why

- **Document extraction** (`document_processing/extractor.py`) is
  rule-based (regex over text) so the pipeline runs without an LLM key
  or a paid API. Swap in the LLM behind `extract_charges()` when ready.
- **Storage / database** run in-memory with sample data when
  `DATABASE_URL` is unset, so `uvicorn main:app` works with zero setup.
  Wire SQLAlchemy + R2 when deploying.
- **Email sending** is a logged no-op. Wiring SMTP / an email provider
  is a deliberate, reviewed step — never a silent default.
- **Auth** is not enforced in the starter API. Add Supabase JWT
  verification (and the role checks in the roadmap) before any pilot
  user touches real data.
- **Stripe** is not wired up. Billing lands in Days 76–90.

## Authentication and permissions (design)

- Supabase Auth issues JWTs; the backend verifies them against
  Supabase's JWKS and looks up the role in the `users` table
  (`backend/services/supabase_auth.py` documents the full design).
- Roles Admin / Staff / Viewer are defined in `models/roles.py` and
  enforced by `services/auth.py` (`require_roles` in the API,
  `check_role` in services/tests). Viewer is read-only; changing a
  claim deadline is admin-only; approving/sending follow-ups is
  staff/admin **plus** an approval record.
- The starter's `X-ClaimKit-Role` header is a test stand-in only.

## Document storage, library, classification, matching

- Storage: Cloudflare R2, S3-compatible, `services/storage.py`;
  metadata only in PostgreSQL (`evidence.storage_key`).
- Upload: `POST /documents/upload` (multipart, PDF/photos);
  extraction: `POST /documents/extract` (text, graceful 400/404/422).
- Library: `services/library.py` + `GET /library/search` — by
  shipment, date, type, amount, keyword.
- Classification: `document_processing/classifier.py` — heuristic
  starter (BOL / receipt / photo / invoice / email), LLM-ready interface.
- Matching: `services/matching.py` (reference > carrier > lane).
- Rules engine: `services/rules.py` flags potentially recoverable
  charges with evidence-needed lists.
- Deadline monitoring: `automation/deadline_monitor.py` —
  overdue / due-soon (<= 7 days) / ok, audit-logged, run daily via
  Celery beat in production.
