## What changes

<!-- What does this PR do, and why? One change, one reason. -->

## How it was tested

<!-- Commands you ran and their results, for example:
- `python -m pytest tests/backend tests/integration -v` — all passed
- `npx tsc --noEmit && npm test && npm run build` — all passed
- Manual check: what you tried and what you saw.
-->

## Checklist

- [ ] Tests pass (`python -m pytest tests/backend tests/integration -v`, `npx tsc --noEmit`, `npm test`, `npm run build`)
- [ ] No secrets committed (no API keys, tokens, or credentials in code, tests, fixtures, or docs)
- [ ] No path that sends email or marks a follow-up as sent without human approval
- [ ] Docs updated if behavior or configuration changed (especially `docs/document-processing-accuracy.md` for extraction changes)
- [ ] Accuracy numbers in the docs come from a real run, or are marked unmeasured
