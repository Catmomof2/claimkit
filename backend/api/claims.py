"""Claims endpoints.

- GET /claims, GET /claims/{id}, GET /claims/{id}/packet
- POST /claims (staff/admin) — unknown shipment -> 404, logged
- PATCH /claims/{id}/deadline — ADMIN ONLY (role-based access)
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from models.roles import CAN_CHANGE_DEADLINE, CAN_CREATE_CLAIM, CAN_GENERATE_PACKET, CAN_READ
from services import audit_log, claims_service, packet_service
from services.auth import require_roles

router = APIRouter(prefix="/claims", tags=["claims"])


class CreateClaimRequest(BaseModel):
    shipment_id: str
    counterparty: str
    filing_deadline: date


class DeadlineRequest(BaseModel):
    filing_deadline: date


@router.get("")
def list_claims(role=Depends(require_roles(*CAN_READ))):
    return claims_service.list_claims()


@router.get("/{claim_id}")
def get_claim(claim_id: str, role=Depends(require_roles(*CAN_READ))):
    claim = claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Unknown claim: {claim_id}")
    return claim


@router.post("", status_code=201)
def create_claim(payload: CreateClaimRequest, role=Depends(require_roles(*CAN_CREATE_CLAIM))):
    shipment = next((s for s in claims_service.list_shipments() if s.id == payload.shipment_id), None)
    if shipment is None:
        audit_log.log_event(role.value, "claim.create_failed", "shipment", payload.shipment_id,
                            detail=f"Create claim failed: unknown shipment {payload.shipment_id}",
                            role=role.value)
        raise HTTPException(status_code=404, detail=f"Unknown shipment: {payload.shipment_id}")
    claim = claims_service.create_claim(payload.shipment_id, payload.counterparty, payload.filing_deadline)
    audit_log.log_event(role.value, "claim.created", "claim", claim.id,
                        detail=f"Claim created for shipment {payload.shipment_id}, "
                        f"total ${claim.total_claimed:.2f}", role=role.value)
    return claim


@router.get("/{claim_id}/packet")
def get_packet(claim_id: str, role=Depends(require_roles(*CAN_GENERATE_PACKET))):
    try:
        return packet_service.build_packet(claim_id, actor=role.value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{claim_id}/deadline")
def change_deadline(claim_id: str, payload: DeadlineRequest,
                    role=Depends(require_roles(*CAN_CHANGE_DEADLINE))):
    """Admin-only: changing a filing deadline is an admin-only action."""
    claim = claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail=f"Unknown claim: {claim_id}")
    old = claim.filing_deadline
    claim.filing_deadline = payload.filing_deadline
    audit_log.log_event(role.value, "deadline.changed", "claim", claim.id,
                        detail=f"Filing deadline changed {old.isoformat()} -> "
                        f"{payload.filing_deadline.isoformat()}", role=role.value)
    return claim
