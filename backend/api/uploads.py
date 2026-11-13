"""Document upload API — PDF documents and photographs.

POST /documents/upload accepts multipart form data (file + shipment_id
+ kind). It validates the file (type/size, see services/storage.py),
records the metadata, creates an evidence record linked to the
shipment, and returns the metadata — it never stores real credentials
and, with no R2 configured, stores locally as a stub (see
services/storage.py). Uploaded bytes are NOT persisted by the starter
beyond the request; wire R2 before using this with real documents.

Sample PDFs / photos: the repo ships only labelled .txt sample
documents (backend/document_processing/samples/). There are no sample
PDFs or photos in the repo — upload your own test files, or use the
.txt samples via POST /documents/extract.
"""
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from document_processing.classifier import classify_document
from models.roles import CAN_EXTRACT_DOCUMENT
from services import audit_log, claims_service, evidence as evidence_service, storage
from services.auth import require_roles

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", status_code=201)
async def upload_document(
    shipment_id: str = Form(...),
    kind: str = Form("bol"),
    file: UploadFile = File(...),
    role=Depends(require_roles(*CAN_EXTRACT_DOCUMENT)),
):
    if not any(s.id == shipment_id for s in claims_service.list_shipments()):
        audit_log.log_event(role.value, "shipment.not_found", "shipment", shipment_id,
                            detail="Upload rejected: unknown shipment ID", role=role.value)
        raise HTTPException(status_code=404, detail=f"Unknown shipment: {shipment_id}")
    data = await file.read()
    try:
        stored = storage.store_file(shipment_id, f"ev_{uuid.uuid4().hex[:8]}",
                                    file.filename or "upload.bin",
                                    file.content_type or "application/octet-stream", data)
    except ValueError as exc:
        audit_log.log_event(role.value, "document.rejected", "document", shipment_id,
                            detail=str(exc), role=role.value)
        raise HTTPException(status_code=400, detail=str(exc))
    classification = classify_document(file.filename or "", "")
    record = evidence_service.add_evidence(
        shipment_id, kind, file.filename or "upload.bin",
        storage_key=stored.storage_key, actor=role.value)
    return {
        "evidence": record,
        "storage": stored,
        "classification": {"label": classification.label,
                           "confidence": classification.confidence,
                           "note": "Starter heuristic classifier — see document_processing/classifier.py"},
    }
