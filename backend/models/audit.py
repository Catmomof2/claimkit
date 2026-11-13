"""Audit-log model.

Every significant action is recorded: who did what, when, to which
entity. See services/audit_log.py for the logging helper and
api/audit.py for the read endpoint. The audit_log table is also in
database/schemas.sql (and migration 0001).
"""
from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    id: int
    actor: str
    role: str | None = None
    action: str
    # e.g. "claim.created", "draft.generated", "draft.approved",
    # "draft.rejected", "packet.generated", "deadline.changed",
    # "extraction.failed", "document.rejected"
    entity_type: str
    entity_id: str | None = None
    detail: str | None = None
    timestamp: str = Field(description="ISO-8601 UTC timestamp")
