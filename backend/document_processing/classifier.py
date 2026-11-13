"""AI document classification — STARTER implementation, clearly marked.

Labels a document as BOL, receipt, photo, invoice, or email, with a
confidence score. This starter uses filename + keyword heuristics so
the pipeline runs without a model. Production replaces
``classify_document()`` with an LLM / vision-model call behind the
same signature — callers never change.

Confidence is honest: heuristics score 0.55–0.75. Anything below 0.7
should be flagged for human review. Do not present these labels as
model output.
"""
from dataclasses import dataclass


@dataclass
class Classification:
    label: str  # bol | receipt | photo | invoice | email
    confidence: float
    reason: str


def classify_document(filename: str, text: str = "") -> Classification:
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
