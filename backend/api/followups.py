"""Follow-up approval queue endpoints.

- GET /followups[?status=draft] — the approval queue (all roles can read)
- POST /followups/generate-overdue — staff/admin; drafts only, never sends
- POST /followups/{id}/approve — staff/admin; records approver + timestamp
- POST /followups/{id}/reject — staff/admin; records rejecter + reason
- POST /followups/{id}/send — staff/admin, AND the draft must be approved;
  unapproved drafts are blocked with 403 and the attempt is audit-logged.

Viewers get 403 on every write here. Nothing in this file sends email
without an approval record — see automation/followups.py.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from automation import followups
from models.roles import (
    CAN_APPROVE_FOLLOWUP, CAN_DRAFT_FOLLOWUP, CAN_READ,
    CAN_REJECT_FOLLOWUP, CAN_SEND_FOLLOWUP,
)
from services import audit_log
from services.auth import require_roles

router = APIRouter(prefix="/followups", tags=["followups"])


class ApproveRequest(BaseModel):
    approved_by: str


class RejectRequest(BaseModel):
    rejected_by: str
    reason: str | None = None


class GenerateRequest(BaseModel):
    as_of: date | None = None
    actor: str = "system"


@router.get("")
def list_followups(status: str | None = None, role=Depends(require_roles(*CAN_READ))):
    return followups.list_drafts(status=status)


@router.post("/generate-overdue", status_code=201)
def generate_overdue(payload: GenerateRequest, role=Depends(require_roles(*CAN_DRAFT_FOLLOWUP))):
    drafts = followups.generate_followup_drafts_for_overdue(as_of=payload.as_of, actor=payload.actor)
    return {"generated": len(drafts), "drafts": drafts}


@router.post("/{draft_id}/approve")
def approve(draft_id: str, payload: ApproveRequest, role=Depends(require_roles(*CAN_APPROVE_FOLLOWUP))):
    if followups.get_draft(draft_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown draft: {draft_id}")
    try:
        return followups.approve_followup(draft_id, payload.approved_by)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{draft_id}/reject")
def reject(draft_id: str, payload: RejectRequest, role=Depends(require_roles(*CAN_REJECT_FOLLOWUP))):
    if followups.get_draft(draft_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown draft: {draft_id}")
    try:
        return followups.reject_followup(draft_id, payload.rejected_by, payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{draft_id}/send")
def send(draft_id: str, role=Depends(require_roles(*CAN_SEND_FOLLOWUP))):
    draft = followups.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail=f"Unknown draft: {draft_id}")
    try:
        return followups.send_followup(draft_id, actor=role.value)
    except followups.ApprovalRequiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
