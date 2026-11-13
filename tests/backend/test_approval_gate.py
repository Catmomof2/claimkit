"""Approval gate: no follow-up can be sent without an explicit approval record."""
import pytest

from automation.followups import (
    ApprovalRequiredError, approve_followup, draft_followup,
    generate_draft_for_claim, generate_followup_drafts_for_overdue,
    reject_followup, send_followup,
)
from models.roles import Role
from services.auth import check_role
from models.roles import CAN_APPROVE_FOLLOWUP


def test_send_blocked_without_approval():
    draft = draft_followup("clm_001", "billing@example.com", "Follow-up", "Body")
    assert draft.status == "draft"
    with pytest.raises(ApprovalRequiredError):
        send_followup(draft.id)


def test_approve_then_send_succeeds():
    draft = draft_followup("clm_001", "billing@example.com", "Follow-up", "Body")
    approve_followup(draft.id, approved_by="staff@example.com")
    sent = send_followup(draft.id)
    assert sent.status == "sent"
    assert sent.approved_by == "staff@example.com"
    assert sent.approved_at is not None


def test_rejected_draft_cannot_be_sent_or_approved():
    draft = draft_followup("clm_001", "billing@example.com", "Follow-up", "Body")
    reject_followup(draft.id, rejected_by="staff@example.com", reason="Wrong amount")
    assert draft.status == "rejected"
    with pytest.raises(ApprovalRequiredError):
        send_followup(draft.id)
    with pytest.raises(ValueError):
        approve_followup(draft.id, approved_by="staff@example.com")


def test_generated_draft_contains_amount_deadline_and_evidence():
    from datetime import date
    drafts = generate_followup_drafts_for_overdue(as_of=date(2026, 11, 19))
    assert drafts, "expected drafts for overdue/unpaid claims"
    draft = next(d for d in drafts if d.claim_id == "clm_003")
    assert "$250.00" in draft.body
    assert "2026-11-18" in draft.body
    assert "Evidence" in draft.body or "evidence" in draft.body
    assert draft.status == "draft"  # DRAFT only — nothing sent


def test_generate_is_idempotent_no_duplicates():
    from datetime import date
    first = generate_followup_drafts_for_overdue(as_of=date(2026, 11, 19))
    second = generate_followup_drafts_for_overdue(as_of=date(2026, 11, 19))
    assert second == []
    assert len(first) >= 1


def test_viewer_cannot_approve():
    with pytest.raises(PermissionError):
        check_role(Role.VIEWER, CAN_APPROVE_FOLLOWUP)
    check_role(Role.STAFF, CAN_APPROVE_FOLLOWUP)
    check_role(Role.ADMIN, CAN_APPROVE_FOLLOWUP)
