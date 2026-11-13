"""Rules engine — identifies potentially recoverable expenses.

Each rule inspects an extracted charge / expense description and says
whether it is potentially recoverable, why, and what evidence is still
needed. "Potentially" is deliberate: the rules flag candidates for
human review; they do not decide a claim on their own.

Rules (from docs/product-requirements.md):
- detention: waited > free time
- loading_delay / unloading_delay: delay beyond the scheduled window
- additional_delivery: re-delivery / storage / lumper fees
- missed_appointment: appointment missed, no fault of the carrier
- unexpected_transport: detours / tolls / accessorials not in the quote
"""
from dataclasses import dataclass

from document_processing.extractor import ExtractedCharge
from models.models import detention_amount

RULES = {
    "detention": "Detention: waited time exceeds free time; billable hours x hourly rate.",
    "loading_delay": "Loading delay: delay beyond the scheduled loading window.",
    "unloading_delay": "Unloading delay: delay beyond the scheduled unloading window.",
    "additional_delivery": "Additional delivery expense: re-delivery, storage, or lumper fee.",
    "missed_appointment": "Missed appointment: appointment missed through no fault of the carrier.",
    "unexpected_transport": "Unexpected transport cost: detour, toll, or accessorial not in the quote.",
}


@dataclass
class RuleResult:
    charge_type: str
    potentially_recoverable: bool
    reason: str
    evidence_needed: list[str]
    suggested_amount: float | None = None


def evaluate_charge(charge: ExtractedCharge, waited_hours: float | None = None,
                     free_hours: float | None = None, hourly_rate: float | None = None) -> RuleResult:
    reason = RULES.get(charge.type, "Unknown charge type.")
    evidence = ["BOL / POD", "Invoice or receipt showing the amount"]
    if charge.type == "detention":
        evidence.append("Arrival / departure timestamps proving waited time")
        amount = None
        if waited_hours is not None and free_hours is not None and hourly_rate is not None:
            amount = detention_amount(waited_hours, free_hours, hourly_rate)
            if amount == 0:
                return RuleResult(charge.type, False,
                                  "Waited time did not exceed free time — $0 recoverable.",
                                  evidence, suggested_amount=0.0)
        return RuleResult(charge.type, True, reason, evidence, suggested_amount=amount)
    if charge.type in ("loading_delay", "unloading_delay"):
        evidence.append("Scheduled window and actual arrival / departure times")
    if charge.type == "missed_appointment":
        evidence.append("Appointment confirmation and proof the dock was closed / unavailable")
    if charge.type == "additional_delivery":
        evidence.append("Re-delivery or storage invoice")
    if charge.type == "unexpected_transport":
        evidence.append("Original quote (to show the cost was not included) and receipt")
    return RuleResult(charge.type, True, reason, evidence, suggested_amount=charge.amount)


def flag_recoverable(charges) -> list[RuleResult]:
    """Flag every extracted charge as potentially recoverable or not.

    Accepts either a list of ExtractedCharge or an ExtractionResult
    (its .charges are used).
    """
    items = getattr(charges, "charges", charges)
    return [evaluate_charge(c) for c in items]
