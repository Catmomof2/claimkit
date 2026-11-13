# Document-Processing Accuracy — Starter Report

> Measured 2026-11-13 against the three labelled sample documents in
> `backend/document_processing/samples/` (also copied to
> `tests/fixtures/`). The extractor under test is the rule-based stub in
> `backend/document_processing/extractor.py` — not an LLM. Re-run
> `tests/backend/test_document_processing.py` after any extractor change;
> the suite must pass before shipping that change.

## Sample set

| Sample document | Expected charge(s) | Found by stub? | Amount found |
| --- | --- | --- | --- |
| `detention-sample.txt` | detention | ✅ yes | $262.50 |
| `loading-delay-sample.txt` | loading_delay | ✅ yes | $195.00 |
| `missed-appointment-sample.txt` | missed_appointment | ✅ yes | $250.00 |

## Accuracy on this set

- Charge-type recall: **3 / 3 (100%)** — every expected type found.
- Charge-type precision: **3 / 3 (100%)** — no extra types found in
  these three documents.
- Amount extraction: **3 / 3 (100%)** — the amount nearest the charge
  keyword matched the expected amount in each sample.
- Shipment-reference extraction: **3 / 3** — `SAMPLE-1001`, `SAMPLE-1002`,
  `SAMPLE-1003` all recovered from the `BOL #` line.

## What this does NOT prove

- Three short, clean, labelled samples are not real-world accuracy.
  Real BOLs / PODs / emails are messier: handwriting, photos, scanned
  PDFs, inconsistent wording, and amounts in tables.
- The stub scores every charge at confidence 0.6. That is honest:
  rule-based matching is a stand-in. An LLM-backed extractor should
  score per field and be measured the same way.
- Empty / malformed documents are handled separately: see
  `tests/backend/test_document_processing.py::test_empty_document`
  and `test_malformed_document_does_not_crash` — they return no
  charges (or a clear error at the API layer), never a crash.

## How to extend the measurement (Days 61–75)

1. Add anonymised real-world documents to `tests/fixtures/` with an
   expected-charges file per document.
2. Extend `test_document_processing.py` to compute precision / recall
   per field (dates, times, amounts) across the whole set.
3. Record the numbers here, with the extractor version and date.
4. Any extractor change that lowers recall on the labelled set fails CI.
