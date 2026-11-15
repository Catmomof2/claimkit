"""Document extraction — Google Gemini LLM with a rule-based fallback.

When a Gemini API key is configured (``GEMINI_API_KEY``, falling back
to ``LLM_API_KEY``), ``extract_charges()`` calls Gemini behind the
same function signature, so callers (API, Celery jobs, tests) never
change. On ANY Gemini failure — no key, HTTP/API error, malformed
JSON, empty response — extraction falls back to the rule-based stub
below, so the pipeline runs without an LLM key, a paid API, or
network access, and a model failure never loses the document.

Never silently accept low-confidence fields: every extracted charge
carries a confidence score, and callers should flag < 0.7 for review.
The ``source`` field on the result says which path produced it:
``"gemini"`` or ``"rule-based"``.
"""
import logging
import re
from dataclasses import dataclass, field

from document_processing import gemini_client

logger = logging.getLogger(__name__)

CHARGE_TYPES = (
    "detention",
    "loading_delay",
    "unloading_delay",
    "additional_delivery",
    "missed_appointment",
    "unexpected_transport",
)

# Bound the prompt: long documents are truncated rather than sent whole.
_MAX_PROMPT_CHARS = 12000

_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "shipment_reference": {"type": "string"},
        "charges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": list(CHARGE_TYPES)},
                    "amount": {"type": "number"},
                    "description": {"type": "string"},
                    "confidence": {"type": "number"},
                    "evidence_snippet": {"type": "string"},
                },
                "required": ["type", "description", "confidence"],
            },
        },
    },
    "required": ["charges"],
}

_EXTRACTION_PROMPT = """You extract recoverable freight charges from a shipping document
(bill of lading, proof of delivery, receipt, invoice, or email) for a
freight broker's claims recovery system.

Return a JSON object with:
- "shipment_reference": the BOL / PRO / load / shipment reference, or null if none is shown.
- "charges": an array of charges, each with "type", "amount", "description",
  "confidence", and "evidence_snippet".

Rules:
- Use ONLY these charge types: detention, loading_delay, unloading_delay,
  additional_delivery, missed_appointment, unexpected_transport.
- Only $-prefixed amounts count as money. Bare numbers (dates, BOL numbers,
  hours) are not amounts.
- Hourly rates like $65/hr or $75/hr are NOT charge totals. Return the
  charge total explicitly (e.g. the total detention fee), never the rate.
- "amount" is the charge total in dollars, or null if the document states
  no total for that charge.
- "confidence" is 0 to 1. Score below 0.7 when the charge or amount is
  unclear — a human must review those.
- "evidence_snippet" is a short verbatim quote from the document that
  supports the charge.
- If the document contains no recoverable charge, return an empty "charges" array.

Document:
{text}
"""


@dataclass
class ExtractedCharge:
    type: str  # detention | loading_delay | additional_delivery | ...
    amount: float | None
    description: str
    confidence: float = 0.5
    evidence_snippet: str = ""


@dataclass
class ExtractionResult:
    shipment_reference: str | None = None
    charges: list[ExtractedCharge] = field(default_factory=list)
    raw_text_excerpt: str = ""
    # "gemini" when the LLM produced this result, "rule-based" otherwise.
    source: str = "rule-based"


_AMOUNT_RE = re.compile(r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)")
_HOURS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b", re.IGNORECASE)
_REF_RE = re.compile(r"\b(?:BOL|PRO|LOAD|SHIPMENT)\s*#?\s*([A-Z0-9-]{4,})\b", re.IGNORECASE)

_KEYWORDS = {
    "detention": ["detention", "waited", "waiting time", "held at dock"],
    "loading_delay": ["loading delay", "delayed loading"],
    "unloading_delay": ["unloading delay", "delayed unloading"],
    "additional_delivery": ["re-delivery", "redelivery", "storage fee", "lumper"],
    "missed_appointment": ["missed appointment", "appointment missed"],
    "unexpected_transport": ["detour", "toll", "accessorial"],
}


def _first_amount(text: str) -> float | None:
    """$-amount after a charge keyword. Only $-prefixed numbers count:
    bare numbers (dates, BOL numbers like SAMPLE-1001, hours) are not
    amounts and must never be mistaken for one.

    Hourly rates ($65/hr, $75/hr) are NOT charge totals, so amounts
    followed by ``/hr`` are skipped. The first remaining $-amount is
    the charge total. This is a stub heuristic; the LLM extractor
    should return the charge total explicitly.
    """
    matches = list(_AMOUNT_RE.finditer(text))
    if not matches:
        return None
    totals = [m for m in matches if not text[m.end(): m.end() + 4].lstrip().startswith("/hr")]
    chosen = totals[0] if totals else matches[-1]
    try:
        return float(chosen.group(1).replace(",", ""))
    except ValueError:
        return None


def extract_charges(text: str) -> ExtractionResult:
    """Extract recoverable charges from document text.

    Gemini when a key is configured; the rule-based stub otherwise, and
    on any Gemini failure. Never raises for a bad model response — the
    fallback always runs.
    """
    if not text or not text.strip():
        return ExtractionResult(raw_text_excerpt="")

    if gemini_client.is_configured():
        try:
            return _extract_with_gemini(text)
        except Exception as exc:  # noqa: BLE001 — any Gemini failure falls back
            logger.warning("Gemini extraction failed, falling back to rule-based: %s", exc)

    return _extract_rule_based(text)


def _extract_with_gemini(text: str) -> ExtractionResult:
    """Call Gemini and validate its structured output.

    Raises :class:`gemini_client.GeminiError` (or ``ValueError``) on a
    bad response; the caller falls back to the rule-based stub.
    """
    prompt = _EXTRACTION_PROMPT.format(text=text[:_MAX_PROMPT_CHARS])
    parsed = gemini_client.generate_json(prompt, _EXTRACTION_SCHEMA)

    charges_raw = parsed.get("charges")
    if not isinstance(charges_raw, list):
        raise gemini_client.GeminiError("Gemini response has no 'charges' list.")

    charges: list[ExtractedCharge] = []
    for item in charges_raw:
        if not isinstance(item, dict):
            continue
        charge_type = item.get("type")
        if charge_type not in CHARGE_TYPES:
            continue  # never invent a charge type outside the known set
        amount = item.get("amount")
        if amount is not None:
            try:
                amount = float(amount)
            except (TypeError, ValueError):
                amount = None
        try:
            confidence = float(item.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        charges.append(
            ExtractedCharge(
                type=charge_type,
                amount=amount,
                description=str(item.get("description", ""))[:500],
                confidence=confidence,
                evidence_snippet=str(item.get("evidence_snippet", ""))[:500],
            )
        )

    reference = parsed.get("shipment_reference")
    if reference is not None and not isinstance(reference, str):
        reference = str(reference)
    return ExtractionResult(
        shipment_reference=reference or None,
        charges=charges,
        raw_text_excerpt=text[:500],
        source="gemini",
    )


def _extract_rule_based(text: str) -> ExtractionResult:
    """Rule-based stub: regexes over plain text (the original v0.1.0
    extractor, unchanged). Runs whenever no Gemini key is configured
    and whenever the Gemini call fails."""
    if not text or not text.strip():
        return ExtractionResult(raw_text_excerpt="")

    lowered = text.lower()
    ref_match = _REF_RE.search(text)
    result = ExtractionResult(
        shipment_reference=ref_match.group(1) if ref_match else None,
        raw_text_excerpt=text[:500],
    )

    for charge_type, keywords in _KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                idx = lowered.index(keyword)
                snippet = text[max(0, idx - 60): idx + 120].strip()
                result.charges.append(
                    ExtractedCharge(
                        type=charge_type,
                        # Amount is searched in the text AFTER the keyword,
                        # not just in the snippet: the $ amount usually
                        # follows the charge description.
                        amount=_first_amount(text[idx: idx + 400]),
                        description=f"Possible {charge_type.replace('_', ' ')}: {snippet[:120]}",
                        # Rule-based stub: modest confidence; LLM should score higher.
                        confidence=0.6,
                        evidence_snippet=snippet,
                    )
                )
                break  # one charge per type per document in the stub

    return result
