"""Audit-log helper — records who did what, when.

In-memory in the starter (list ``AUDIT_LOG``); production writes the
same entries to the ``audit_log`` table in database/schemas.sql.
Every helper call is cheap and never raises: audit logging must never
break the action it is recording, so failures are swallowed after a
best-effort print to stderr.
"""
import sys
from datetime import datetime, timezone

from models.audit import AuditLogEntry

AUDIT_LOG: list[AuditLogEntry] = []


def log_event(
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    detail: str | None = None,
    role: str | None = None,
) -> AuditLogEntry:
    """Append one audit entry and return it."""
    try:
        entry = AuditLogEntry(
            id=len(AUDIT_LOG) + 1,
            actor=actor,
            role=role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        AUDIT_LOG.append(entry)
        return entry
    except Exception as exc:  # audit logging must never break the action
        print(f"[claimkit] audit log failed: {exc}", file=sys.stderr)
        raise


def list_recent(limit: int = 50) -> list[AuditLogEntry]:
    """Most recent entries first."""
    return list(reversed(AUDIT_LOG))[: max(1, limit)]


def clear() -> None:
    """Test helper only — never expose via the API."""
    AUDIT_LOG.clear()
