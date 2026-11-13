"""ClaimKit data models (Pydantic; SQLAlchemy tables in database/schemas.sql).

Charge types mirror the product requirements: detention, loading delay,
unloading delay, additional delivery expense, missed appointment, and
unexpected transportation cost.
"""
from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChargeType(str, Enum):
    DETENTION = "detention"
    LOADING_DELAY = "loading_delay"
    UNLOADING_DELAY = "unloading_delay"
    ADDITIONAL_DELIVERY = "additional_delivery"
    MISSED_APPOINTMENT = "missed_appointment"
    UNEXPECTED_TRANSPORT = "unexpected_transport"


class ChargeStatus(str, Enum):
    IDENTIFIED = "identified"
    EVIDENCE_MISSING = "evidence_missing"
    INCLUDED = "included"
    REJECTED = "rejected"


class ClaimStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    DENIED = "denied"


class Shipment(BaseModel):
    id: str
    reference: str
    origin: str
    destination: str
    carrier: str
    pickup_date: date
    delivery_date: date


class Charge(BaseModel):
    id: str
    shipment_id: str
    type: ChargeType
    description: str
    amount: float = Field(ge=0)
    basis: Optional[str] = None  # e.g. "3.5 billable hrs x $75/hr"
    status: ChargeStatus = ChargeStatus.IDENTIFIED


class Claim(BaseModel):
    id: str
    shipment_id: str
    counterparty: str
    status: ClaimStatus = ClaimStatus.DRAFT
    filing_deadline: date
    charge_ids: list[str] = []
    total_claimed: float = Field(default=0, ge=0)
    total_recovered: float = Field(default=0, ge=0)


class Evidence(BaseModel):
    id: str
    shipment_id: str
    charge_id: Optional[str] = None
    kind: str  # bol | pod | invoice | email | photo | receipt
    filename: str
    storage_key: Optional[str] = None  # Cloudflare R2 key in production
    extraction_status: str = "pending"


def detention_amount(waited_hours: float, free_hours: float, hourly_rate: float) -> float:
    """Recoverable detention amount.

    billable_hours = max(0, waited - free); amount = billable * rate.
    Waited time under free time recovers $0 — that is correct, not an error.
    """
    billable = max(0.0, waited_hours - free_hours)
    return round(billable * hourly_rate, 2)
