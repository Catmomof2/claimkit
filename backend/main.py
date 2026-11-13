"""ClaimKit API — FastAPI entrypoint.

Run:  uvicorn main:app --reload --port 8000
Docs:  http://localhost:8000/docs

Without DATABASE_URL the service runs on the in-memory sample store in
services/claims_service.py, so the endpoints work with zero setup.
"""
from fastapi import FastAPI

from api import audit as audit_router
from api import claims as claims_router
from api import deadlines as deadlines_router
from api import documents as documents_router
from api import evidence as evidence_router
from api import followups as followups_router
from api import library as library_router
from api import shipments as shipments_router
from api import uploads as uploads_router

app = FastAPI(
    title="ClaimKit API",
    description="Automated business claims recovery for freight brokers.",
    version="0.1.0",
)

app.include_router(shipments_router.router)
app.include_router(claims_router.router)
app.include_router(deadlines_router.router)
app.include_router(followups_router.router)
app.include_router(audit_router.router)
app.include_router(documents_router.router)
app.include_router(uploads_router.router)
app.include_router(evidence_router.router)
app.include_router(library_router.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "claimkit-api", "version": "0.1.0"}
