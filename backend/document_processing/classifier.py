"""AI document classification — Google Gemini LLM with a heuristic fallback.

Labels a document as BOL, receipt, photo, invoice, or email, with a
confidence score. When a Gemini API key is configured (``GEMINI_API_KEY``,
falling back to ``LLM_API_KEY``), ``classify_document()`` asks Gemini
behind the same signature; on any Gemini failure — or with no key —
it falls back to the filename + keyword heuristics below, so the
pipeline runs without a model.

Confidence is honest: heuristics score 0.55–0.75. Anything below 0.7
should be flagged for human review. Do not present heuristic labels
as model output. The ``source`` field says which path produced the
label: ``"gemini"`` or ``"rule-based"``.
"""
import logging
from dataclasses import dataclass

from document_processing import gemini_client

logger = logging.getLogger(__name__)

LABELS = ("bol", "receipt", "photo", "invoice", "email")

_CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": list(LABELS)},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["label", "confidence", "reason"],
}

_CLASSIFICATION_PROMPT = """Classify this shipping document for a freight broker's claims
recovery system. Reply with a JSON object: "label", "confidence"
(0 to 1), and "reason" (one short sentence).

Labels — use only these:
- "bol": bill of lading / proof of delivery
- "receipt": a payment or expense receipt
- "photo": a photograph (e.g. of the dock, the load, or damage)
- "invoice": an invoice or billing statement
- "email": an email message

Use the filename and the document text. A photo filename (e.g. .jpg,
.png) with no readable text is a "photo". Score below 0.7 when the
classification is uncertain — a human must review those.

Filename: {filename}
Document text:
{text}
"""


@dataclass
class Classification:
    label: str  # bol | receipt | photo | invoice | email
    confidence: float
    reason: str
    # "gemini" when the LLM produced this label, "rule-based" otherwise.
    source: str = "rule-based"


def classify_document(filename: str, text: str = "") -> Classification:
    """Classify a document. Gemini when a key is configured; the
    heuristic fallback otherwise, and on any Gemini failure."""
    if gemini_client.is_configured() and (filename or text):
        try:
            return _classify_with_gemini(filename, text)
        except Exception as exc:  # noqa: BLE001 — any Gemini failure falls back
            logger.warning("Gemini classification failed, falling back to heuristic: %s", exc)
    return _classify_heuristic(filename, text)


def _classify_with_gemini(filename: str, text: str) -> Classification:
    """Call Gemini and validate its structured output.

    Raises :class:`gemini_client.GeminiError` (or ``ValueError``) on a
    bad response; the caller falls back to the heuristic.
    """
    prompt = _CLASSIFICATION_PROMPT.format(
        filename=filename or "(none)", text=(text or "")[:4000]
    )
    parsed = gemini_client.generate_json(prompt, _CLASSIFICATION_SCHEMA)

    label = parsed.get("label")
    if label not in LABELS:
        raise gemini_client.GeminiError(f"Gemini returned unknown label: {label!r}")
    try:
        confidence = float(parsed.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))
    return Classification(
        label=label,
        confidence=confidence,
        reason=str(parsed.get("reason", ""))[:500],
        source="gemini",
    )


def _classify_heuristic(filename: str, text: str = "") -> Classification:
    """Filename + keyword heuristics (the original v0.1.0 classifier,
    unchanged). Runs whenever no Gemini key is configured and whenever
    the Gemini call fails."""
    name = (filename or "").lower()
    body = (text or "").lower()
    if name.endswith((".jpg", ".jpeg", ".png", ".webp")) or "photo" in name:
        return Classification("photo", 0.75, "Image file extension / photo filename (heuristic).")
    if "bol" in name or "bill of lading" in body:
        return Classification("bol", 0.7, "Filename or 'bill of lading' text (heuristic).")
    if "receipt" in name or "receipt" in body:
        return Classification("receipt", 0.7, "'receipt' in filename or text (heuristic).")
    if "invoice" in name or "invoice" in body:
        return Classification("invoice", 0.7, "'invoice' in filename or text (heuristic).")
    if name.endswith(".eml") or "from:" in body or "subject:" in body:
        return Classification("email", 0.7, "Email markers in filename or text (heuristic).")
    if "pod" in name or "proof of delivery" in body:
        return Classification("bol", 0.55, "POD mentioned; labelled BOL family — review needed.")
    return Classification("invoice", 0.55, "No clear markers; default label — human review required.")
