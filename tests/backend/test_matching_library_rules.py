"""Matching, rules engine, library search, storage, evidence, deadlines."""
from datetime import date

from automation.deadline_monitor import check_deadlines
from document_processing.extractor import extract_charges
from services import evidence as evidence_service, library as library_service, storage
from services.matching import match_expense_to_shipment
from services.rules import evaluate_charge, flag_recoverable


def test_match_by_reference():
    m = match_expense_to_shipment("Detention on BOL # SAMPLE-1001", reference="SAMPLE-1001")
    assert m.shipment_id == "shp_001"
    assert m.confidence == 1.0


def test_match_by_text_reference():
    m = match_expense_to_shipment("Re-delivery for SAMPLE-1002, Spokane")
    assert m.shipment_id == "shp_002"


def test_no_match_returns_none_with_zero_confidence():
    m = match_expense_to_shipment("Random expense, no reference anywhere")
    assert m.shipment_id is None
    assert m.confidence == 0.0


def test_rules_flag_detention_and_zero_when_under_free_time():
    charges = extract_charges("Detention: driver waited 5.5 hours, $262.50")
    results = flag_recoverable(charges)
    assert results and results[0].potentially_recoverable is True
    zero = evaluate_charge(charges.charges[0], waited_hours=1.0, free_hours=2.0, hourly_rate=75.0)
    assert zero.potentially_recoverable is False
    assert zero.suggested_amount == 0.0


def test_library_search_by_keyword_and_amount():
    rows = library_service.search_library(query="redelivery")
    assert rows and rows[0]["shipment_reference"] == "SAMPLE-1001"
    rows = library_service.search_library(min_amount=200)
    assert all(any(c["amount"] >= 200 for c in r["charges"]) for r in rows)
    assert library_service.search_library(query="no-such-keyword-xyz") == []


def test_library_search_by_kind():
    rows = library_service.search_library(kind="pod")
    assert rows and all(r["kind"] == "pod" for r in rows)


def test_storage_rejects_bad_type_and_oversize():
    import pytest
    with pytest.raises(ValueError):
        storage.store_file("shp_001", "ev_1", "evil.exe", "application/x-msdownload", b"x")
    with pytest.raises(ValueError):
        storage.store_file("shp_001", "ev_1", "big.pdf", "application/pdf", b"x" * (26 * 1024 * 1024))


def test_storage_returns_metadata_without_credentials():
    stored = storage.store_file("shp_001", "ev_1", "doc.pdf", "application/pdf", b"%PDF-1.4 sample")
    assert stored.storage_key.startswith("shipments/shp_001/")
    assert stored.backend == "local-stub"  # no R2 configured in tests
    assert len(stored.sha256) == 64


def test_evidence_linked_to_shipment():
    rows = evidence_service.list_evidence(shipment_id="shp_001")
    assert rows and all(e.shipment_id == "shp_001" for e in rows)
    new = evidence_service.add_evidence("shp_002", "photo", "dock.jpg", actor="staff")
    assert new.shipment_id == "shp_002"


def test_deadline_monitor_flags_overdue():
    report = check_deadlines(as_of=date(2026, 11, 19))
    overdue_ids = {r["claim_id"] for r in report.overdue}
    assert "clm_003" in overdue_ids  # due 2026-11-18
    assert "clm_001" not in overdue_ids  # due 2026-12-04
