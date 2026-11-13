# ClaimKit — Automated Business Claims Recovery

Freight brokers and transportation companies lose money because they fail to
recover charges for driver detention time, loading/unloading delays, additional
delivery expenses, missed appointments, and unexpected transportation costs.
Much of the supporting evidence is scattered across emails, receipts,
photographs, and documents.

ClaimKit collects evidence, identifies recoverable charges, assembles claim
packages, and tracks reimbursement — so a company can upload its shipment
documents and receive a report showing which expenses it may be entitled to
recover.

> **Sample data only.** The starter ships with clearly labelled sample
> shipments, charges, and deadlines. No real credentials, customer data, or
> carrier accounts are included. Bring your own Supabase, R2, Stripe, and
> LLM keys via environment variables (see `.env.example` guidance in
> `docs/architecture.md`).

## The problem, in dollars

| Recoverable charge | Example trigger |
| --- | --- |
| Driver detention time | Driver waits past free time at pickup / delivery |
| Loading / unloading delays | Dock delay beyond the scheduled window |
| Additional delivery expenses | Re-delivery, storage, lumper fees |
| Missed appointments | Appointment missed through no fault of the carrier |
| Unexpected transportation costs | Detours, tolls, or accessorials not in the original quote |

## Product

- **AI-powered document extraction** — pull dates, times, amounts, and
  parties from BOLs, PODs, invoices, emails, and photos.
- **Shipment and expense matching** — match each expense to the shipment,
  leg, and contract terms it belongs to.
- **Automated evidence collection** — gather the documents that support
  each charge into one packet.
- **Claim deadline tracking** — every claim carries a filing deadline;
  overdue and at-risk claims are surfaced first.
- **Claim packet generation** — assemble a reviewable packet per claim.
- **Email follow-up automation — with human approval** — follow-ups are
  drafted, never sent, until a human approves them. See
  `backend/automation/followups.py`. There is no code path that sends
  email without an explicit approval record.

## Tech stack

| Component | Technology |
| --- | --- |
| Frontend | Next.js + TypeScript |
| Interface | Tailwind CSS |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Authentication | Supabase Auth |
| File storage | Cloudflare R2 |
| AI processing | LLM API + document extraction |
| Background jobs | Redis + Celery |
| Payments | Stripe |
| Hosting | Cloudflare + suitable application hosting |
| Version control / CI | GitHub Actions |

## Repository layout

```
claimkit/
├── frontend/          # Next.js + TypeScript + Tailwind
│   ├── app/           # App Router pages (incl. dashboard)
│   ├── components/    # Shipment cards, detention calculator, deadlines
│   ├── dashboard/
│   └── services/      # Typed API client for the FastAPI backend
├── backend/           # Python + FastAPI
│   ├── api/           # Routers: shipments, claims, deadlines
│   ├── models/        # SQLAlchemy / Pydantic models
│   ├── services/      # Claim calculation + packet assembly
│   ├── document_processing/  # Text extraction stub (LLM-ready)
│   └── automation/    # Follow-up drafts + human-approval gate
├── database/
│   ├── migrations/    # 0001_initial.sql
│   └── schemas.sql    # shipments, charges, claims, evidence, deadlines
├── tests/
│   ├── frontend/
│   ├── backend/
│   └── integration/
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   └── product-requirements.md
└── .github/workflows/ # CI
```

## Run locally

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
# Health:    http://localhost:8000/health
```

Set `DATABASE_URL` for PostgreSQL when you are ready for a real database;
without it the starter runs on the in-memory sample store in
`backend/services/claims_service.py` so the endpoints work out of the box.

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000  (dashboard: http://localhost:3000/dashboard)
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` to point the dashboard at
your local backend; otherwise it renders the labelled sample data.

### Tests

```bash
# Backend (no extra deps beyond pytest)
cd backend && python -m pytest ../tests/backend -v
# Frontend smoke test
cd frontend && npm test
```

## Roles — Admin / Staff / Viewer

| Role | Can do |
| --- | --- |
| Admin | Everything staff can do, plus admin-only actions: changing a claim filing deadline (`PATCH /claims/{id}/deadline`) |
| Staff | Create claims, generate packets, draft / approve / reject / send follow-ups (sending still needs an approval record), upload and extract documents |
| Viewer | Read-only: list shipments, claims, deadlines, drafts, evidence, library, and the audit log. Every write returns 403 |

Roles are defined in `backend/models/roles.py` and enforced in
`backend/services/auth.py` (`require_roles` / `check_role`). The
starter reads the role from the `X-ClaimKit-Role` header so the checks
can be exercised without a Supabase project — that header is **not**
production auth. Production design is in
`backend/services/supabase_auth.py`: Supabase Auth JWT (Bearer token),
verified against Supabase's JWKS, role looked up in the `users` table
(`database/schemas.sql`). Implement that before any pilot user touches
real data.

## Document storage — Cloudflare R2

Files are stored in Cloudflare R2 (S3-compatible) under
`shipments/<shipment_id>/<evidence_id>-<filename>`; only the storage
key, filename, content type, size, and SHA-256 are stored in the
database. See `backend/services/storage.py` — credentials come only
from `R2_*` environment variables, never from code. With no R2
configured the starter validates the upload and returns metadata with
`backend: "local-stub"`; it does not pretend a file is in R2. Upload
via `POST /documents/upload` (PDF / JPEG / PNG / WebP, max 25 MB) or
the dashboard Upload form. There are no sample PDFs or photos in the
repo — the labelled samples are `.txt` documents in
`backend/document_processing/samples/` (also `tests/fixtures/`).

## Searchable document library

`GET /library/search?q=&shipment_id=&kind=&min_amount=&max_amount=&date_from=&date_to=`
searches evidence by shipment, date, type, amount, and keyword. See
`backend/services/library.py` and `backend/api/library.py`.

## AI document classification (starter)

`backend/document_processing/classifier.py` labels documents BOL /
receipt / photo / invoice / email with a confidence score, using
filename + keyword heuristics — clearly marked as a starter
implementation. Production replaces it with an LLM / vision-model
call behind the same signature.

## Expense matching & rules engine

- Matching (`backend/services/matching.py`): expense → shipment by
  exact reference, reference in text, carrier, or lane; low-confidence
  matches (< 0.7) need human review.
- Rules (`backend/services/rules.py`): flags detention, loading /
  unloading delay, additional delivery, missed appointment, and
  unexpected transport charges as potentially recoverable, with the
  evidence still needed per charge.

## Sample workflow

1. Open the dashboard — three sample shipments are listed with their
   recoverable charges and claim status.
2. Use the detention calculator: enter free time, arrival, and departure,
   and it computes billable detention hours and the amount at your rate.
3. Open a claim — see the matched evidence, the deadline, and the packet
   checklist.
4. Draft a follow-up — the draft is created in `status: draft`. It can
   only move to `approved` / `sent` through the explicit approval step in
   `backend/automation/followups.py`. Nothing is emailed from this starter.

## Roadmap

See `docs/roadmap.md` — including Days 61–75 (security and customer
testing: audit logs, role-based access, document-processing accuracy,
error handling, real-world sample workflows, pilot users) and Days 76–90
(commercial launch: Stripe billing, pricing plans, onboarding, product
documentation, marketing website, converting pilots to paying customers).

## Contributing / licence

MIT — see `LICENSE`. This is a starter scaffold: document extraction is a
rule-based stub ready to be replaced by an LLM call, storage is local /
in-memory until Supabase + R2 are configured, and payments are not wired
up until Stripe is configured.
