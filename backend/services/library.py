"""Searchable document library.

Search evidence records by shipment, date, type, amount, or keyword.
The starter searches the in-memory evidence + charge records; the
production implementation runs the same filters as a PostgreSQL query
against ``evidence`` joined to ``charges`` / ``shipments``.
"""
from datetime import date

from services import claims_service, evidence as evidence_service


def search_library(query: str | None = None, shipment_id: str | None = None,
                   kind: str | None = None, min_amount: float | None = None,
                   max_amount: float | None = None,
                   date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    """Return matching library entries, each with its shipment + charges."""
    q = (query or "").lower()
    results: list[dict] = []
    for ev in evidence_service.list_evidence(shipment_id=shipment_id, charge_id=None):
        if kind and ev.kind != kind:
            continue
        shipment = next((s for s in claims_service.list_shipments() if s.id == ev.shipment_id), None)
        if shipment is None:
            continue
        if date_from and shipment.pickup_date < date_from:
            continue
        if date_to and shipment.delivery_date > date_to:
            continue
        charges = claims_service.charges_for_shipment(ev.shipment_id)
        if min_amount is not None and not any(c.amount >= min_amount for c in charges):
            continue
        if max_amount is not None and not any(c.amount <= max_amount for c in charges):
            continue
        haystack = " ".join([ev.filename, ev.kind, shipment.reference, shipment.origin,
                             shipment.destination, shipment.carrier] +
                            [c.description for c in charges]).lower()
        if q and q not in haystack:
            continue
        results.append({
            "evidence_id": ev.id, "kind": ev.kind, "filename": ev.filename,
            "storage_key": ev.storage_key, "extraction_status": ev.extraction_status,
            "shipment_id": shipment.id, "shipment_reference": shipment.reference,
            "pickup_date": shipment.pickup_date.isoformat(),
            "delivery_date": shipment.delivery_date.isoformat(),
            "charges": [{"id": c.id, "type": c.type.value, "amount": c.amount} for c in charges],
        })
    return results
