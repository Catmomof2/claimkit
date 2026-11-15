# Document-Processing Accuracy — Starter Report

> Measured 2026-11-13 against the three labelled sample documents in
> `backend/document_processing/samples/` (also copied to
> `tests/fixtures/`). The extractor under test was the rule-based stub in
> `backend/document_processing/extractor.py` — not an LLM. Re-run
> `tests/backend/test_document_processing.py` after any extractor change;
> the suite must pass before shipping that change.

## The Gemini path (added 2026-11-15, unmeasured against a live key)

`backend/document_processing/extractor.py` now calls Google Gemini
(`backend/document_processing/gemini_client.py`, model from
`GEMINI_MODEL`, default `gemini-3.8-flash`) when `GEMINI_API_KEY` (or
the legacy `LLM_API_KEY`) is set, and `backend/document_processing/classifier.py`
does the same for document classification. Both use a JSON response
schema so the model returns structured output, and both fall back to
the rule-based / heuristic implementation on any Gemini failure — or
with no key at all. Results carry `source: "gemini" | "rule-based"`.

The numbers below were measured with the rule-based stub only. **No
live-key accuracy measurement has been run yet** — the mocked tests in
`tests/backend/test_gemini_extraction.py` prove the wiring and the
fallback, not the model's real-world accuracy.

### How to re-run the accuracy check with a live key

1. Set `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`) in the
   environment — never commit the key.
2. Run the accuracy suite: `python -m pytest tests/backend/test_document_processing.py -v`
   — it must still pass (the labelled set asserts the same types and
   amounts). If the Gemini path finds different charges on a sample,
   record the difference here instead of editing the expectations
   to fit the model.
3. Record the model name, date, and the per-sample results in the
   table below (add a Gemini column), plus precision/recall on the
   labelled set.
4. To compare paths directly, run the suite once with the key set
   (`source: "gemini"`) and once without it (`source: "rule-based"`).

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
  rule-based matching is a stand-in. The Gemini path scores per field;
  measure it the same way, with a live key, before quoting its numbers.
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
