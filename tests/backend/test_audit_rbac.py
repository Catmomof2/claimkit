"""Audit logs + role-based access."""
import pytest

from models.roles import CAN_CHANGE_DEADLINE, Role
from services import audit_log
from services.auth import check_role, parse_role


def test_audit_log_records_who_what_when():
    entry = audit_log.log_event("alice@example.com", "claim.created", "claim", "clm_001",
                                detail="test", role="staff")
    assert entry.actor == "alice@example.com"
    assert entry.action == "claim.created"
    assert entry.timestamp
    assert audit_log.list_recent(limit=1)[0].id == entry.id


def test_audit_log_most_recent_first():
    audit_log.log_event("a", "x", "claim", "1")
    audit_log.log_event("b", "y", "claim", "2")
    recent = audit_log.list_recent(limit=2)
    assert recent[0].action == "y"
    assert recent[1].action == "x"


def test_roles_parse_and_default_to_viewer():
    assert parse_role("admin") == Role.ADMIN
    assert parse_role("STAFF") == Role.STAFF
    assert parse_role(None) == Role.VIEWER
    assert parse_role("nonsense") == Role.VIEWER


def test_viewer_blocked_from_admin_only_deadline_change():
    with pytest.raises(PermissionError):
        check_role(Role.VIEWER, CAN_CHANGE_DEADLINE)
    with pytest.raises(PermissionError):
        check_role(Role.STAFF, CAN_CHANGE_DEADLINE)
    check_role(Role.ADMIN, CAN_CHANGE_DEADLINE)
