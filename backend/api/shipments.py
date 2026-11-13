"""Shipments endpoints. Errors are clear 404s, logged to the audit log."""
from fastapi import APIRouter, Depends, HTTPException

from models.roles import CAN_READ
from services import audit_log, claims_service
from services.auth import get_current_role, require_roles

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("")
def list_shipments(role=Depends(require_roles(*CAN_READ))):
    return claims_service.list_shipments()


@router.get("/{shipment_id}")
def get_shipment(shipment_id: str, role=Depends(require_roles(*CAN_READ))):
    shipment = next((s for s in claims_service.list_shipments() if s.id == shipment_id), None)
    if shipment is None:
        audit_log.log_event("api", "shipment.not_found", "shipment", shipment_id,
                            detail=f"Unknown shipment ID requested: {shipment_id}")
        raise HTTPException(status_code=404, detail=f"Unknown shipment: {shipment_id}")
    charges = claims_service.charges_for_shipment(shipment_id)
    return {"shipment": shipment, "charges": charges}
