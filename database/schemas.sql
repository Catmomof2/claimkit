-- ClaimKit — PostgreSQL schema (see also migrations/0001_initial.sql)
-- Tables: shipments, charges, claims, evidence, deadlines, audit_log,
-- followup_drafts (approval queue).

CREATE TABLE IF NOT EXISTS shipments (
    id TEXT PRIMARY KEY,
    reference TEXT NOT NULL UNIQUE,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    carrier TEXT NOT NULL,
    pickup_date DATE NOT NULL,
    delivery_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS charges (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id),
    type TEXT NOT NULL CHECK (type IN (
        'detention', 'loading_delay', 'unloading_delay',
        'additional_delivery', 'missed_appointment', 'unexpected_transport')),
    description TEXT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    basis TEXT,
    status TEXT NOT NULL DEFAULT 'identified' CHECK (status IN (
        'identified', 'evidence_missing', 'included', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id),
    counterparty TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'ready', 'submitted', 'paid', 'partially_paid', 'denied')),
    filing_deadline DATE NOT NULL,
    total_claimed NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (total_claimed >= 0),
    total_recovered NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (total_recovered >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS claim_charges (
    claim_id TEXT NOT NULL REFERENCES claims(id),
    charge_id TEXT NOT NULL REFERENCES charges(id),
    PRIMARY KEY (claim_id, charge_id)
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id),
    charge_id TEXT REFERENCES charges(id),
    kind TEXT NOT NULL CHECK (kind IN ('bol', 'pod', 'invoice', 'email', 'photo', 'receipt')),
    filename TEXT NOT NULL,
    storage_key TEXT,  -- Cloudflare R2 key
    extraction_status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS deadlines (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    kind TEXT NOT NULL,  -- filing | response | follow_up
    due_date DATE NOT NULL,
    reminded BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Users and roles. Supabase Auth owns the credential / JWT; this table
-- maps a Supabase user id to a ClaimKit role (admin / staff / viewer).
-- Roles are enforced in backend/models/roles.py + services/auth.py.
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,  -- Supabase Auth user id (UUID)
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'staff', 'viewer')),
    display_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Approval queue: follow-up drafts. status='draft' is the queue.
-- A draft may only be sent after an approval record (approved_by/at).
CREATE TABLE IF NOT EXISTS followup_drafts (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'rejected', 'sent')),
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    rejected_by TEXT,
    rejected_at TIMESTAMPTZ,
    rejection_reason TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Audit log: who did what, when. Append-only in application code;
-- never update or delete rows from the API.
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    role TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    detail TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);
