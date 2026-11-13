"""Deadline endpoints — claims sorted soonest-first."""
from fastapi import APIRouter, Depends

from models.roles import CAN_READ
from services import claims_service
from services.auth import require_roles

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


@router.get("")
def list_deadlines(role=Depends(require_roles(*CAN_READ))):
    return [
        {"claim_id": c.id, "shipment_id": c.shipment_id,
         "counterparty": c.counterparty, "status": c.status.value,
         "filing_deadline": c.filing_deadline.isoformat(),
         "total_claimed": c.total_claimed}
        for c in claims_service.upcoming_deadlines()
    ]
