"""Pytest setup: put backend/ on sys.path and reset in-memory stores."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_state():
    from automation import followups
    from services import audit_log, claims_service, evidence as evidence_service

    orig_claims = len(claims_service.SAMPLE_CLAIMS)
    orig_evidence = len(evidence_service.SAMPLE_EVIDENCE)
    yield
    followups.clear()
    audit_log.clear()
    del claims_service.SAMPLE_CLAIMS[orig_claims:]
    del evidence_service.SAMPLE_EVIDENCE[orig_evidence:]
