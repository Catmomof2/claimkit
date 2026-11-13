"""Claim service — sample store + claim calculation.

In production this layer reads PostgreSQL (see database/schemas.sql).
The starter uses an in-memory store seeded with clearly labelled SAMPLE
data so the API works with zero setup. Nothing here is real customer data.
"""
from datetime import date

from models.models import (
    Charge,
    ChargeStatus,
    ChargeType,
    Claim,
    ClaimStatus,
    Shipment,
    detention_amount,
)

SAMPLE_SHIPMENTS: list[Shipment] = [
    Shipment(
        id="shp_001", reference="SAMPLE-1001", origin="Tacoma, WA",
        destination="Portland, OR", carrier="Sample Carrier LLC",
        pickup_date=date(2026, 11, 3), delivery_date=date(2026, 11, 4),
    ),
    Shipment(
        id="shp_002", reference="SAMPLE-1002", origin="Spokane, WA",
        destination="Boise, ID", carrier="Sample Carrier LLC",
        pickup_date=date(2026, 11, 5), delivery_date=date(2026, 11, 6),
    ),
    Shipment(
        id="shp_003", reference="SAMPLE-1003", origin="Lakewood, WA",
        destination="Seattle, WA", carrier="Sample Carrier LLC",
        pickup_date=date(2026, 11, 7), delivery_date=date(2026, 11, 7),
    ),
]

SAMPLE_CHARGES: list[Charge] = [
    Charge(
        id="chg_001", shipment_id="shp_001", type=ChargeType.DETENTION,
        description="Detention at delivery: waited 5.5h, 2h free",
        amount=detention_amount(5.5, 2.0, 75.0),
        basis="3.5 billable hrs x $75/hr", status=ChargeStatus.INCLUDED,
    ),
    Charge(
        id="chg_002", shipment_id="shp_001", type=ChargeType.ADDITIONAL_DELIVERY,
        description="Re-delivery fee after missed dock appointment",
        amount=185.00, basis="Receipt: re-delivery invoice",
        status=ChargeStatus.INCLUDED,
    ),
    Charge(
        id="chg_003", shipment_id="shp_002", type=ChargeType.LOADING_DELAY,
        description="Loading delay: 4h at shipper, 1h free",
        amount=detention_amount(4.0, 1.0, 65.0),
        basis="3.0 billable hrs x $65/hr", status=ChargeStatus.EVIDENCE_MISSING,
    ),
    Charge(
        id="chg_004", shipment_id="shp_003", type=ChargeType.MISSED_APPOINTMENT,
        description="Missed delivery appointment (no fault of carrier)",
        amount=250.00, basis="Contract accessorial schedule",
        status=ChargeStatus.IDENTIFIED,
    ),
]

SAMPLE_CLAIMS: list[Claim] = [
    Claim(
        id="clm_001", shipment_id="shp_001", counterparty="Sample Shipper Inc.",
        status=ClaimStatus.READY, filing_deadline=date(2026, 12, 4),
        charge_ids=["chg_001", "chg_002"], total_claimed=447.50,
    ),
    Claim(
        id="clm_002", shipment_id="shp_002", counterparty="Sample Shipper Inc.",
        status=ClaimStatus.DRAFT, filing_deadline=date(2026, 11, 20),
        charge_ids=["chg_003"], total_claimed=195.00,
    ),
    Claim(
        id="clm_003", shipment_id="shp_003", counterparty="Sample Receiver Co.",
        status=ClaimStatus.DRAFT, filing_deadline=date(2026, 11, 18),
        charge_ids=["chg_004"], total_claimed=250.00,
    ),
]


def list_shipments() -> list[Shipment]:
    return list(SAMPLE_SHIPMENTS)


def charges_for_shipment(shipment_id: str) -> list[Charge]:
    return [c for c in SAMPLE_CHARGES if c.shipment_id == shipment_id]


def list_claims() -> list[Claim]:
    return list(SAMPLE_CLAIMS)


def get_claim(claim_id: str) -> Claim | None:
    return next((c for c in SAMPLE_CLAIMS if c.id == claim_id), None)


def create_claim(shipment_id: str, counterparty: str, filing_deadline: date) -> Claim:
    """Create a draft claim from the shipment's included charges."""
    charges = charges_for_shipment(shipment_id)
    included = [c for c in charges if c.status == ChargeStatus.INCLUDED]
    total = round(sum(c.amount for c in included), 2)
    claim = Claim(
        id=f"clm_{len(SAMPLE_CLAIMS) + 1:03d}",
        shipment_id=shipment_id,
        counterparty=counterparty,
        status=ClaimStatus.DRAFT,
        filing_deadline=filing_deadline,
        charge_ids=[c.id for c in included],
        total_claimed=total,
    )
    SAMPLE_CLAIMS.append(claim)
    return claim


def upcoming_deadlines() -> list[Claim]:
    """Claims sorted by filing deadline, soonest first."""
    return sorted(SAMPLE_CLAIMS, key=lambda c: c.filing_deadline)
