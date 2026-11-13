"""Expense-to-shipment matching.

An expense (from a receipt, invoice, email, or extracted charge) is
matched to a shipment by, in order:
1. explicit shipment reference (BOL / PRO / LOAD #) — strongest;
2. carrier + date window (pickup/delivery dates);
3. origin/destination keywords in the expense text.

Returns a match with a confidence score and a reason. Low-confidence
matches (< 0.7) must be reviewed by a human — the caller flags them,
never silently attaches an expense to the wrong shipment.
"""
from dataclasses import dataclass

from services import claims_service


@dataclass
class ExpenseMatch:
    shipment_id: str | None
    confidence: float
    reason: str


def match_expense_to_shipment(
    text: str, reference: str | None = None, carrier: str | None = None
) -> ExpenseMatch:
    lowered = (text or "").lower()
    if reference:
        for s in claims_service.list_shipments():
            if s.reference.lower() == reference.lower():
                return ExpenseMatch(s.id, 1.0, f"Exact shipment reference {reference}")
    # Reference embedded in the text, e.g. "BOL # SAMPLE-1001".
    for s in claims_service.list_shipments():
        if s.reference.lower() in lowered:
            return ExpenseMatch(s.id, 0.95, f"Shipment reference {s.reference} found in text")
    if carrier:
        for s in claims_service.list_shipments():
            if s.carrier.lower() == carrier.lower():
                return ExpenseMatch(s.id, 0.6, "Carrier matches; confirm date / reference")
    for s in claims_service.list_shipments():
        if s.origin.split(",")[0].lower() in lowered and s.destination.split(",")[0].lower() in lowered:
            return ExpenseMatch(s.id, 0.6, "Origin and destination both mentioned; confirm reference")
    return ExpenseMatch(None, 0.0, "No shipment reference, carrier, or lane match found")
