"""Evidence management — evidence records linked to shipments/claims.

An evidence record is the metadata for one uploaded document / photo:
kind, filename, storage key (R2, see services/storage.py), and
extraction status. The starter keeps records in memory, seeded with
sample rows clearly labelled SAMPLE; production persists them in the
``evidence`` table (database/schemas.sql).
"""
from models.models import Evidence
from services import audit_log

SAMPLE_EVIDENCE: list[Evidence] = [
    Evidence(id="ev_001", shipment_id="shp_001", charge_id="chg_001",
             kind="pod", filename="SAMPLE-1001-pod.pdf", storage_key="shipments/shp_001/ev_001-SAMPLE-1001-pod.pdf",
             extraction_status="done"),
    Evidence(id="ev_002", shipment_id="shp_001", charge_id="chg_002",
             kind="invoice", filename="SAMPLE-1001-redelivery-invoice.pdf",
             storage_key="shipments/shp_001/ev_002-SAMPLE-1001-redelivery-invoice.pdf",
             extraction_status="done"),
    Evidence(id="ev_003", shipment_id="shp_002", charge_id="chg_003",
             kind="email", filename="SAMPLE-1002-shipper-email.txt",
             extraction_status="pending"),
]


def list_evidence(shipment_id: str | None = None, charge_id: str | None = None) -> list[Evidence]:
    rows = list(SAMPLE_EVIDENCE)
    if shipment_id:
        rows = [e for e in rows if e.shipment_id == shipment_id]
    if charge_id:
        rows = [e for e in rows if e.charge_id == charge_id]
    return rows


def add_evidence(shipment_id: str, kind: str, filename: str, charge_id: str | None = None,
                 storage_key: str | None = None, actor: str = "system") -> Evidence:
    evidence = Evidence(
        id=f"ev_{len(SAMPLE_EVIDENCE) + 1:03d}",
        shipment_id=shipment_id, charge_id=charge_id, kind=kind,
        filename=filename, storage_key=storage_key, extraction_status="pending",
    )
    SAMPLE_EVIDENCE.append(evidence)
    audit_log.log_event(actor, "evidence.added", "evidence", evidence.id,
                        detail=f"{kind} {filename} for shipment {shipment_id}")
    return evidence
