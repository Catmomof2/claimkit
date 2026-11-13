"""Real-world sample workflow, end to end (Days 61–75):

upload sample docs -> identify charges -> build claim packet ->
draft follow-up -> approve -> mark ready to send.

Uses only the labelled sample documents in tests/fixtures/.
Nothing here sends email: send is a logged no-op in the starter, and
the test asserts the approval gate at the send step.
"""
import os

import pytest

from automation import followups
from automation.deadline_monitor import check_deadlines
from document_processing.extractor import extract_charges
from services import audit_log, claims_service, packet_service
from services.matching import match_expense_to_shipment
from services.rules import flag_recoverable

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def _read(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return f.read()


def test_full_sample_workflow():
    # 1. Upload / read sample docs (detention for SAMPLE-1001).
    text = _read("detention-sample.txt")
    result = extract_charges(text)
    assert result.shipment_reference == "SAMPLE-1001"
    assert [c.type for c in result.charges] == ["detention"]

    # 2. Identify charges + match the expense to its shipment.
    flagged = flag_recoverable(result.charges)
    assert flagged[0].potentially_recoverable is True
    match = match_expense_to_shipment(text, reference=result.shipment_reference)
    assert match.shipment_id == "shp_001"
    assert match.confidence >= 0.9

    # 3. Build the claim packet for the existing claim on that shipment.
    packet = packet_service.build_packet("clm_001", actor="staff@example.com")
    assert packet["claim_id"] == "clm_001"
    assert packet["total_claimed"] == 447.50
    assert packet["complete"] is True
    assert any(a.action == "packet.generated" for a in audit_log.list_recent(limit=10))

    # 4. Deadline monitoring surfaces the claim correctly.
    report = check_deadlines(as_of=__import__("datetime").date(2026, 11, 19))
    assert "clm_001" not in {r["claim_id"] for r in report.overdue}

    # 5. Draft a follow-up for the overdue claim clm_003, approve, then send.
    draft = followups.generate_draft_for_claim("clm_003", actor="staff@example.com")
    assert draft.status == "draft"
    with pytest.raises(followups.ApprovalRequiredError):
        followups.send_followup(draft.id)
    followups.approve_followup(draft.id, approved_by="admin@example.com")
    sent = followups.send_followup(draft.id, actor="admin@example.com")
    assert sent.status == "sent"

    # 6. Audit log shows the whole flow.
    actions = {a.action for a in audit_log.list_recent(limit=50)}
    assert {"packet.generated", "draft.generated", "draft.approved", "draft.sent"} <= actions
