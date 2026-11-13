"""Document extraction — rule-based stub with an LLM-ready interface.

Production replaces ``extract_charges()`` with an LLM API call behind the
same function signature, so callers (API, Celery jobs, tests) never change.
The stub uses regexes over plain text so the pipeline runs without an
LLM key, a paid API, or network access.

Never silently accept low-confidence fields: every extracted charge
carries a confidence score, and callers should flag < 0.7 for review.
"""
import re
from dataclasses import dataclass, field


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
    """Extract recoverable charges from document text (stub)."""
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
