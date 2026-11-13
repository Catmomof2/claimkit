"""Document extraction endpoint — graceful error handling.

- Missing / empty text -> 400 with a clear message, logged as
  "document.rejected". Never crashes on malformed input.
- Unknown shipment_id (when supplied) -> 404, logged.
- Extraction failure -> 422 with a clear message, logged as
  "extraction.failed". The API stays up; the caller can retry.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from document_processing.extractor import extract_charges
from models.roles import CAN_EXTRACT_DOCUMENT
from services import audit_log, claims_service
from services.auth import require_roles

router = APIRouter(prefix="/documents", tags=["documents"])


class ExtractRequest(BaseModel):
    text: str | None = None
    shipment_id: str | None = None


@router.post("/extract")
def extract(payload: ExtractRequest, role=Depends(require_roles(*CAN_EXTRACT_DOCUMENT))):
    if payload.text is None or not payload.text.strip():
        audit_log.log_event(role.value, "document.rejected", "document", payload.shipment_id,
                            detail="Extract rejected: missing or empty text", role=role.value)
        raise HTTPException(status_code=400, detail="Document text is missing or empty.")
    if payload.shipment_id is not None:
        known = any(s.id == payload.shipment_id for s in claims_service.list_shipments())
        if not known:
            audit_log.log_event(role.value, "shipment.not_found", "shipment", payload.shipment_id,
                                detail="Extract rejected: unknown shipment ID", role=role.value)
            raise HTTPException(status_code=404, detail=f"Unknown shipment: {payload.shipment_id}")
    try:
        result = extract_charges(payload.text)
    except Exception as exc:  # extractor must never crash the request
        audit_log.log_event(role.value, "extraction.failed", "document", payload.shipment_id,
                            detail=f"Extraction failed: {exc}", role=role.value)
        raise HTTPException(status_code=422, detail=f"Document extraction failed: {exc}")
    if not result.charges:
        audit_log.log_event(role.value, "extraction.no_charges", "document", payload.shipment_id,
                            detail="Extraction succeeded but found no recoverable charges",
                            role=role.value)
    return result
