"""Evidence management endpoints."""
from fastapi import APIRouter, Depends

from models.roles import CAN_READ
from services import evidence as evidence_service
from services.auth import require_roles

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("")
def list_evidence(shipment_id: str | None = None, charge_id: str | None = None,
                  role=Depends(require_roles(*CAN_READ))):
    return evidence_service.list_evidence(shipment_id=shipment_id, charge_id=charge_id)
