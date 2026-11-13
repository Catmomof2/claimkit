"""Deadline monitoring — scheduled check for at-risk / overdue claims.

Run on a schedule in production (Redis + Celery beat, e.g. daily at
08:00). The starter function is pure and testable: given ``as_of``,
it classifies every unpaid claim as overdue / due_soon (<= 7 days) /
ok, logs overdue ones to the audit log, and returns the lists so the
dashboard and follow-up generation can act on them.
"""
from dataclasses import dataclass
from datetime import date

from models.models import ClaimStatus
from services import audit_log, claims_service

UNPAID = (ClaimStatus.DRAFT, ClaimStatus.READY, ClaimStatus.SUBMITTED, ClaimStatus.PARTIALLY_PAID)


@dataclass
class DeadlineReport:
    overdue: list[dict]
    due_soon: list[dict]
    ok: list[dict]


def check_deadlines(as_of: date | None = None, actor: str = "deadline-monitor") -> DeadlineReport:
    as_of = as_of or date.today()
    overdue, due_soon, ok = [], [], []
    for claim in claims_service.list_claims():
        if claim.status not in UNPAID:
            continue
        days_left = (claim.filing_deadline - as_of).days
        row = {"claim_id": claim.id, "shipment_id": claim.shipment_id,
               "filing_deadline": claim.filing_deadline.isoformat(),
               "days_left": days_left, "total_claimed": claim.total_claimed,
               "status": claim.status.value}
        if days_left < 0:
            overdue.append(row)
        elif days_left <= 7:
            due_soon.append(row)
        else:
            ok.append(row)
    for row in overdue:
        audit_log.log_event(actor, "deadline.overdue", "claim", row["claim_id"],
                            detail=f"Filing deadline {row['filing_deadline']} passed "
                            f"({-row['days_left']} days overdue)")
    return DeadlineReport(overdue=overdue, due_soon=due_soon, ok=ok)
