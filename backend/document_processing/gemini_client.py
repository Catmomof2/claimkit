"""Google Gemini client for ClaimKit document extraction/classification.

Calls the Gemini REST API (``generateContent``) with a JSON response
schema, so the model returns valid, structured JSON. No new
dependencies: uses ``httpx``, already in ``backend/requirements.txt``.

Configuration (environment variables, never commit real values):

- ``GEMINI_API_KEY`` — the Gemini API key. Falls back to the generic
  ``LLM_API_KEY``. When neither is set, this module reports itself as
  not configured and callers must use the rule-based / heuristic
  fallback; this module never invents a key.
- ``GEMINI_MODEL`` — model name, default ``"gemini-3.8-flash"`` (the
  model the Gemini API recommends for new keys; ``gemini-2.5-flash``
  is no longer available to new users).

The API key is sent as the ``key`` query parameter (the documented
Gemini REST auth method). The key is never logged: error messages
include the HTTP status and a short slice of the response body only,
never the request URL.
"""
import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.8-flash"
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
_TIMEOUT_S = 30.0


class GeminiError(Exception):
    """Raised on any Gemini failure: missing key, HTTP/API error,
    malformed JSON, or an empty response. Callers catch this and fall
    back to the rule-based stub — a Gemini failure must never crash
    the pipeline or lose the document."""


def _api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY") or None


def _model_name() -> str:
    return os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL


def is_configured() -> bool:
    """True when a Gemini API key is present in the environment."""
    return _api_key() is not None


def generate_json(prompt: str, response_schema: dict, *, client: httpx.Client | None = None) -> dict:
    """Call Gemini ``generateContent`` and return the parsed JSON object.

    ``response_schema`` is passed as the generation config's JSON schema
    (with ``responseMimeType: application/json``), so the model returns
    structured JSON rather than free text. ``client`` is injectable for
    tests (e.g. an ``httpx.Client`` with a ``MockTransport``); when
    omitted a short-lived client is created.

    Raises :class:`GeminiError` on a missing key, any HTTP/transport
    failure, a non-200 response, malformed JSON, an empty candidate
    list, or a non-object JSON payload.
    """
    key = _api_key()
    if not key:
        raise GeminiError("No Gemini API key configured (set GEMINI_API_KEY).")

    model = _model_name()
    url = f"{_BASE_URL}/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
            "temperature": 0.0,
        },
    }

    own_client = client is None
    if own_client:
        client = httpx.Client(timeout=_TIMEOUT_S)
    try:
        try:
            response = client.post(url, params={"key": key}, json=payload)
        except httpx.HTTPError as exc:
            raise GeminiError(f"Gemini request failed: {type(exc).__name__}: {exc}") from exc
        if response.status_code != 200:
            raise GeminiError(
                f"Gemini API returned HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )
        try:
            body = response.json()
        except (ValueError, UnicodeDecodeError) as exc:
            raise GeminiError(f"Gemini returned malformed JSON: {exc}") from exc
        candidates = body.get("candidates") if isinstance(body, dict) else None
        if not candidates:
            raise GeminiError("Gemini returned no candidates.")
        parts = candidates[0].get("content", {}).get("parts") or []
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise GeminiError("Gemini returned an empty response.")
        try:
            parsed = json.loads(text)
        except ValueError as exc:
            raise GeminiError(f"Gemini returned malformed JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise GeminiError("Gemini returned a non-object JSON payload.")
        return parsed
    finally:
        if own_client:
            client.close()
