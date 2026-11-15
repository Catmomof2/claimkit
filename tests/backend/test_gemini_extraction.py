"""Google Gemini extraction/classification — mocked, no live API calls.

No test here calls the real Gemini API: the HTTP layer is exercised
with httpx.MockTransport, and the extractor/classifier wiring is
exercised by monkeypatching ``gemini_client.generate_json``. A live-key
accuracy re-check is documented in
docs/document-processing-accuracy.md and must be run by hand before
relying on Gemini numbers.
"""
import json
import os

import httpx
import pytest

from document_processing import gemini_client
from document_processing.classifier import classify_document
from document_processing.extractor import extract_charges

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def _read(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return f.read()


def _no_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)


def _with_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")


def _gemini_body(text_payload):
    return {"candidates": [{"content": {"parts": [{"text": text_payload}]}}]}


def _mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


# --- gemini_client HTTP layer (MockTransport, no network) ---

def test_client_success_returns_parsed_json(monkeypatch):
    _with_key(monkeypatch)
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        assert "test-key-not-real" in str(request.url)  # key as query param
        return httpx.Response(200, json=_gemini_body('{"charges": []}'))

    result = gemini_client.generate_json(
        "prompt", {"type": "object"}, client=_mock_client(handler)
    )
    assert result == {"charges": []}
    assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"
    assert "responseSchema" in seen["body"]["generationConfig"]
    assert seen["url"].startswith(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    )


def test_client_uses_configured_model(monkeypatch):
    _with_key(monkeypatch)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        return httpx.Response(200, json=_gemini_body("{}"))

    gemini_client.generate_json("prompt", {}, client=_mock_client(handler))
    assert "gemini-2.5-pro:generateContent" in seen["url"]


def test_client_http_error_raises(monkeypatch):
    _with_key(monkeypatch)

    def handler(request):
        return httpx.Response(400, json={"error": {"message": "bad key"}})

    with pytest.raises(gemini_client.GeminiError, match="HTTP 400"):
        gemini_client.generate_json("prompt", {}, client=_mock_client(handler))


def test_client_malformed_response_json_raises(monkeypatch):
    _with_key(monkeypatch)

    def handler(request):
        return httpx.Response(200, content=b"not json at all")

    with pytest.raises(gemini_client.GeminiError, match="malformed JSON"):
        gemini_client.generate_json("prompt", {}, client=_mock_client(handler))


def test_client_empty_candidates_raises(monkeypatch):
    _with_key(monkeypatch)

    def handler(request):
        return httpx.Response(200, json={"candidates": []})

    with pytest.raises(gemini_client.GeminiError, match="no candidates"):
        gemini_client.generate_json("prompt", {}, client=_mock_client(handler))


def test_client_malformed_model_json_raises(monkeypatch):
    _with_key(monkeypatch)

    def handler(request):
        return httpx.Response(200, json=_gemini_body("{not valid json"))

    with pytest.raises(gemini_client.GeminiError, match="malformed JSON"):
        gemini_client.generate_json("prompt", {}, client=_mock_client(handler))


def test_client_missing_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert not gemini_client.is_configured()
    with pytest.raises(gemini_client.GeminiError, match="No Gemini API key"):
        gemini_client.generate_json("prompt", {})


# --- extractor wiring ---

def test_no_key_falls_back_to_rule_based(monkeypatch):
    _no_key(monkeypatch)
    result = extract_charges(_read("detention-sample.txt"))
    assert result.source == "rule-based"
    assert result.shipment_reference == "SAMPLE-1001"
    charge = next(c for c in result.charges if c.type == "detention")
    assert charge.amount == 262.50


def test_gemini_success_uses_model_output(monkeypatch):
    _with_key(monkeypatch)
    captured = {}

    def fake_generate(prompt, schema, **kwargs):
        captured["prompt"] = prompt
        captured["schema"] = schema
        return {
            "shipment_reference": "SAMPLE-1001",
            "charges": [
                {
                    "type": "detention",
                    "amount": 262.50,
                    "description": "Detention: 3.5 billable hours",
                    "confidence": 0.92,
                    "evidence_snippet": "Detention charge: $262.50",
                }
            ],
        }

    monkeypatch.setattr(gemini_client, "generate_json", fake_generate)
    result = extract_charges(_read("detention-sample.txt"))
    assert result.source == "gemini"
    assert result.shipment_reference == "SAMPLE-1001"
    assert len(result.charges) == 1
    charge = result.charges[0]
    assert charge.type == "detention"
    assert charge.amount == 262.50
    assert charge.confidence == 0.92
    # The prompt carries the guardrails: hourly rates are not totals.
    assert "$65/hr" in captured["prompt"] or "$75/hr" in captured["prompt"]
    assert "detention" in captured["schema"]["properties"]["charges"]["items"]["properties"]["type"]["enum"]


def test_gemini_error_falls_back_to_rule_based(monkeypatch):
    _with_key(monkeypatch)

    def failing_generate(prompt, schema, **kwargs):
        raise gemini_client.GeminiError("Gemini API returned HTTP 500: boom")

    monkeypatch.setattr(gemini_client, "generate_json", failing_generate)
    result = extract_charges(_read("loading-delay-sample.txt"))
    assert result.source == "rule-based"
    charge = next(c for c in result.charges if c.type == "loading_delay")
    assert charge.amount == 195.00


def test_gemini_malformed_json_falls_back_to_rule_based(monkeypatch):
    _with_key(monkeypatch)

    def malformed_generate(prompt, schema, **kwargs):
        raise gemini_client.GeminiError("Gemini returned malformed JSON")

    monkeypatch.setattr(gemini_client, "generate_json", malformed_generate)
    result = extract_charges(_read("missed-appointment-sample.txt"))
    assert result.source == "rule-based"
    charge = next(c for c in result.charges if c.type == "missed_appointment")
    assert charge.amount == 250.00


def test_gemini_unknown_charge_type_is_dropped(monkeypatch):
    _with_key(monkeypatch)

    def fake_generate(prompt, schema, **kwargs):
        return {
            "shipment_reference": None,
            "charges": [
                {"type": "not_a_real_type", "amount": 99.0,
                 "description": "invented", "confidence": 0.9},
                {"type": "detention", "amount": 100.0,
                 "description": "real one", "confidence": 0.8},
            ],
        }

    monkeypatch.setattr(gemini_client, "generate_json", fake_generate)
    result = extract_charges("Detention charge: $100.00")
    assert result.source == "gemini"
    assert [c.type for c in result.charges] == ["detention"]


def test_llm_api_key_fallback_env(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "legacy-key")
    assert gemini_client.is_configured()


# --- classifier wiring ---

def test_classifier_no_key_uses_heuristic(monkeypatch):
    _no_key(monkeypatch)
    result = classify_document("dock-photo.jpg", "")
    assert result.source == "rule-based"
    assert result.label == "photo"


def test_classifier_gemini_success(monkeypatch):
    _with_key(monkeypatch)

    def fake_generate(prompt, schema, **kwargs):
        assert "invoice" in schema["properties"]["label"]["enum"]
        return {"label": "invoice", "confidence": 0.95,
                "reason": "Invoice header and total present."}

    monkeypatch.setattr(gemini_client, "generate_json", fake_generate)
    result = classify_document("scan.pdf", "INVOICE #42 total $300")
    assert result.source == "gemini"
    assert result.label == "invoice"
    assert result.confidence == 0.95


def test_classifier_gemini_error_falls_back_to_heuristic(monkeypatch):
    _with_key(monkeypatch)

    def failing_generate(prompt, schema, **kwargs):
        raise gemini_client.GeminiError("Gemini API returned HTTP 429: slow down")

    monkeypatch.setattr(gemini_client, "generate_json", failing_generate)
    result = classify_document("receipt-123.pdf", "receipt for $45")
    assert result.source == "rule-based"
    assert result.label == "receipt"


def test_classifier_gemini_unknown_label_falls_back(monkeypatch):
    _with_key(monkeypatch)

    def fake_generate(prompt, schema, **kwargs):
        return {"label": "mystery", "confidence": 0.9, "reason": "unknown"}

    monkeypatch.setattr(gemini_client, "generate_json", fake_generate)
    result = classify_document("invoice-9.pdf", "invoice total")
    assert result.source == "rule-based"
    assert result.label == "invoice"
