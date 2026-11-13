"""Document-processing accuracy — labelled sample documents.

Samples live in tests/fixtures/ (copies of
backend/document_processing/samples/). Expected charges are asserted
per document; the accuracy summary is in
docs/document-processing-accuracy.md (3/3 types, 3/3 amounts on this set).
"""
import os

from document_processing.classifier import classify_document
from document_processing.extractor import extract_charges

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def _read(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return f.read()


def _types(result):
    return [c.type for c in result.charges]


def test_detention_sample():
    result = extract_charges(_read("detention-sample.txt"))
    assert "detention" in _types(result)
    assert result.shipment_reference == "SAMPLE-1001"
    charge = next(c for c in result.charges if c.type == "detention")
    assert charge.amount == 262.50


def test_loading_delay_sample():
    result = extract_charges(_read("loading-delay-sample.txt"))
    assert "loading_delay" in _types(result)
    assert result.shipment_reference == "SAMPLE-1002"
    charge = next(c for c in result.charges if c.type == "loading_delay")
    assert charge.amount == 195.00


def test_missed_appointment_sample():
    result = extract_charges(_read("missed-appointment-sample.txt"))
    assert "missed_appointment" in _types(result)
    assert result.shipment_reference == "SAMPLE-1003"
    charge = next(c for c in result.charges if c.type == "missed_appointment")
    assert charge.amount == 250.00


def test_accuracy_on_labelled_set():
    """Precision/recall on the 3-document labelled set: 3/3 types, no extras."""
    cases = {
        "detention-sample.txt": {"detention"},
        "loading-delay-sample.txt": {"loading_delay"},
        "missed-appointment-sample.txt": {"missed_appointment"},
    }
    found_all, expected_all = set(), set()
    for name, expected in cases.items():
        found = set(_types(extract_charges(_read(name))))
        assert found == expected, f"{name}: found {found}, expected {expected}"
        found_all |= found
        expected_all |= expected
    assert found_all == expected_all


def test_empty_document():
    result = extract_charges("")
    assert result.charges == []


def test_malformed_document_does_not_crash():
    result = extract_charges("!!! $$$ ###\n\x00\x01 random bytes, no structure")
    assert isinstance(result.charges, list)  # no crash, no invented charges


def test_classifier_labels_samples():
    assert classify_document("SAMPLE-1001-pod.pdf", "proof of delivery").label in ("bol", "invoice")
    assert classify_document("receipt-123.pdf", "receipt for $45").label == "receipt"
    assert classify_document("dock-photo.jpg", "").label == "photo"
    assert classify_document("invoice-9.pdf", "invoice total").label == "invoice"
