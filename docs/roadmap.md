# ClaimKit Roadmap

## Vision

Start with one workflow — detention-time recovery from uploaded shipment
documents — and expand into a larger claims platform: every recoverable
charge type, every counterparty, full reimbursement tracking.

## Phases

### Days 1–30: Core workflow (starter — this repo)

- [x] Shipment + charge + claim + evidence data model
- [x] Detention calculator (free time vs. waited time × rate)
- [x] Document-extraction stub with a clean LLM-ready interface
- [x] Claim packet assembly (checklist + evidence list)
- [x] Deadline tracking and dashboard surfacing
- [x] Follow-up drafts with a human-approval gate (no auto-send)

### Days 31–60: Evidence, matching, and deadlines

- Build deadline monitoring: scheduled checks, at-risk / overdue flags,
  reminder schedule per claim.
- Implement automated follow-up drafts (draft only — approval gate stays).
- Add human approval before external actions (UI + API + audit record).
- Shipment ↔ expense matching accuracy: contract terms per carrier /
  shipper, free-time rules, rate tables.
- Evidence collection: email ingestion, photo upload, R2 storage,
  extraction confidence scores.

### Days 61–75: Security and customer testing

- Add audit logs: every create / approve / send / status change, with
  actor, timestamp, and before/after values.
- Implement role-based access: admin, staff, viewer — enforced in the
  API (Supabase Auth + JWT), not just hidden in the UI.
- Test document-processing accuracy: labelled sample set, precision /
  recall per field (dates, times, amounts), regression suite that must
  pass before any extractor change ships.
- Add error handling: extraction failures, partial packets, and missing
  evidence must degrade gracefully and be visible — never silently drop
  a charge.
- Test with real-world sample workflows: end-to-end runs on anonymised
  real shipment packs (detention, missed appointment, re-delivery).
- Invite initial business users: pilot onboarding, feedback loop, and a
  clear list of what is still a stub (see `docs/architecture.md`).

### Days 76–90: Commercial launch preparation

- Integrate subscription billing (Stripe): checkout, webhooks, dunning.
- Create pricing plans: e.g. starter / growth / scale by shipments or
  recovered value — confirm pricing with pilot feedback before launch.
- Build onboarding: guided first-claim flow, sample data clearly labelled,
  workspace setup, carrier / shipper profiles.
- Publish product documentation: user guide, API reference, security
  overview, data-retention policy.
- Launch a marketing website: problem, sample report, pricing, pilot
  testimonials (only with permission).
- Convert initial pilot users into paying customers: migration from
  pilot terms to a paid plan, with no surprise charges.

## After launch

- Analytics: recovery rate, average days to reimbursement, charges
  missed vs. recovered, per-carrier / per-lane breakdowns.
- More charge types and counterparty integrations.
- Bulk / EDI ingestion for high-volume brokers.
