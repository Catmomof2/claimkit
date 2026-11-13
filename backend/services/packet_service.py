"""Claim packet generation.

Assembles a reviewable packet for one claim: summary, charges with
amounts and basis, matched evidence, deadline, and a completeness
checklist. Missing evidence is LISTED, never hidden — a packet with
missing evidence is still generated, marked incomplete.
"""
from models.models import ChargeStatus
from services import audit_log, claims_service


def build_packet(claim_id: str, actor: str = "system") -> dict:
    claim = claims_service.get_claim(claim_id)
    if claim is None:
        raise ValueError(f"Unknown claim: {claim_id}")
    charges = [
        c for c in claims_service.SAMPLE_CHARGES if c.id in claim.charge_ids
    ]
    missing = [
        {"charge_id": c.id, "type": c.type.value, "description": c.description}
        for c in charges
        if c.status == ChargeStatus.EVIDENCE_MISSING
    ]
    packet = {
        "claim_id": claim.id,
        "shipment_id": claim.shipment_id,
        "counterparty": claim.counterparty,
        "status": claim.status.value,
        "filing_deadline": claim.filing_deadline.isoformat(),
        "total_claimed": claim.total_claimed,
        "total_recovered": claim.total_recovered,
        "charges": [
            {
                "id": c.id, "type": c.type.value, "description": c.description,
                "amount": c.amount, "basis": c.basis, "status": c.status.value,
            }
            for c in charges
        ],
        "evidence": [
            {
                "charge_id": c.id,
                "status": "on_file" if c.status != ChargeStatus.EVIDENCE_MISSING else "missing",
            }
            for c in charges
        ],
        "missing_evidence": missing,
        "complete": len(missing) == 0,
        "checklist": [
            "Claim summary reviewed",
            "Every charge has an amount and a basis",
            "Evidence attached for every charge" if not missing else "Evidence MISSING — see missing_evidence",
            "Filing deadline confirmed",
            "Human approval recorded before submission",
        ],
    }
    audit_log.log_event(
        actor, "packet.generated", "claim", claim.id,
        detail=f"Packet generated; complete={packet['complete']}, "
        f"missing_evidence={len(missing)}",
    )
    return packet
