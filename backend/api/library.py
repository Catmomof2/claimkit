"""Searchable document library endpoint.

GET /library/search?q=&shipment_id=&kind=&min_amount=&max_amount=
    &date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
Searches by shipment, date, type, amount, and keyword.
"""
from datetime import date

from fastapi import APIRouter, Depends

from models.roles import CAN_READ
from services import library as library_service
from services.auth import require_roles

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/search")
def search(q: str | None = None, shipment_id: str | None = None,
           kind: str | None = None, min_amount: float | None = None,
           max_amount: float | None = None,
           date_from: date | None = None, date_to: date | None = None,
           role=Depends(require_roles(*CAN_READ))):
    return library_service.search_library(
        query=q, shipment_id=shipment_id, kind=kind,
        min_amount=min_amount, max_amount=max_amount,
        date_from=date_from, date_to=date_to)
