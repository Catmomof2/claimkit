# Document-Processing Accuracy — Starter Report

> Measured 2026-11-13 against the three labelled sample documents in
> `backend/document_processing/samples/` (also copied to
> `tests/fixtures/`). The extractor under test was the rule-based stub in
> `backend/document_processing/extractor.py` — not an LLM. Re-run
> `tests/backend/test_document_processing.py` after any extractor change;
> the suite must pass before shipping that change.

## The Gemini path (added 2026-11-15, measured live same day)

`backend/document_processing/extractor.py` now calls Google Gemini
(`backend/document_processing/gemini_client.py`, model from
`GEMINI_MODEL`, default `gemini-3.8-flash`) when `GEMINI_API_KEY` (or
the legacy `LLM_API_KEY`) is set, and `backend/document_processing/classifier.py`
does the same for document classification. Both use a JSON response
schema so the model returns structured output, and both fall back to
the rule-based / heuristic implementation on any Gemini failure — or
with no key at all. Results carry `source: "gemini" | "rule-based"`.

### Live run, 2026-11-15 (model `gemini-3.8-flash`, merged main `45b1ca0`)

Run against the three labelled samples with the real API key. The
pipeline (Gemini-or-fallback) got every sample right — type, amount,
and shipment reference, 3/3 on each. **But only 1 of the 3
extractions actually came from Gemini**; the other two fell back to
the rule-based stub after the model failed.

| Sample document | Expected | Gemini result (live) | Pipeline result |
| --- | --- | --- | --- |
| `detention-sample.txt` | detention $262.50, SAMPLE-1001 | ✅ detention $262.50, confidence 0.98, ref SAMPLE-1001 (134s) | ✅ correct |
| `loading-delay-sample.txt` | loading_delay $195.00, SAMPLE-1002 | ❌ no result — HTTP 503 "high demand" after ~271s, fell back | ✅ correct via stub ($195.00, conf 0.6) |
| `missed-appointment-sample.txt` | missed_appointment $250.00, SAMPLE-1003 | ❌ no result — helper error after ~1.5s, fell back | ✅ correct via stub ($250.00, conf 0.6) |

Gemini-only numbers on this set: type recall 1/3, type precision 1/1
(the one charge Gemini produced was correct), amount 1/1. Pipeline
numbers (Gemini-or-fallback): type recall 3/3, amount 3/3, reference
3/3. Do not quote the 3/3 figures as Gemini accuracy — they are the
fallback doing its job.

Latency is the real finding. Live Gemini calls took 114–271 seconds
or failed outright (one 503, one fast helper error whose cause was not
fully visible in the truncated log). The client timeout is 30 seconds,
so while the model is this overloaded, production calls would almost
always fall back to the rule-based path. That is the safety net
working, not a bug — but it means Gemini is not really doing the work
yet. Re-run this check when the model is less loaded before drawing
any conclusion about its accuracy.

Classification on this run: 2/3 from Gemini (both labelled "invoice",
confidence 0.8 and 0.6), 1/3 heuristic fallback (labelled "receipt",
confidence 0.7). There are no expected classification labels for
these samples, so classification is unscored here — the "invoice"
labels are recorded, not endorsed.

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

## Accuracy on this set (rule-based stub, 2026-11-13)

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
