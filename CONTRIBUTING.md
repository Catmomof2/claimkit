# Contributing to ClaimKit

Thanks for helping with ClaimKit — Automated Business Claims Recovery for
freight brokers. This guide covers the setup and the rules that keep the
project honest about what it is (a working starter, not production-ready)
and safe for the people who run it.

## Ways to contribute

- **Report a bug** with the bug report template (include steps to reproduce,
  what you expected, and what happened).
- **Request a feature** with the feature request template (describe the
  problem first, then the proposed change).
- **Fix a bug or add a feature** with a pull request — see below.
- **Improve the docs** — the architecture, roadmap, and accuracy docs live
  in `docs/` and go stale fast; corrections are welcome.

## Development setup

ClaimKit has two parts: a Python + FastAPI backend and a Next.js frontend.
You need Python 3.12 and Node 20.

```bash
git clone https://github.com/Catmomof2/claimkit.git
cd claimkit

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm ci
cd ..
```

Set any environment variables you need directly — the list is in
`docs/architecture.md` — and never commit real values.
The backend runs without any external service configured: no database URL
means the in-memory sample store, no Gemini key means the rule-based
extractor, no email transport means a logged no-op. That is by design —
the starter must run with nothing configured.

## Running the tests

```bash
# Backend: compile check + full suite (from the repo root)
python -m compileall -q backend
python -m pytest tests/backend tests/integration -v

# Frontend: typecheck + tests + build (from frontend/)
npx tsc --noEmit
npm test
npm run build
```

CI runs the same commands on every push and pull request. Both jobs must
pass before a PR is merged.

## Pull requests

- Keep PRs small and focused — one change, one reason.
- Open the PR against `main` from a branch named after the change
  (for example `fix/detention-amount` or `docs/accuracy-update`).
- Describe what changed and why in the PR body, and say how you tested it.
  The PR template asks for this.
- Do not merge your own PR, and do not force-push, rebase, or amend
  commits that are already on the shared branch.
- Update the docs when behavior changes — especially
  `docs/document-processing-accuracy.md` when extraction changes, and
  `docs/architecture.md` when configuration changes.

## Rules that are not negotiable

- **Never commit a secret.** No API keys, tokens, passwords, or real
  credentials in code, tests, fixtures, or docs. Test keys must be
  obviously fake (for example `test-key-not-real`). Keys come from
  environment variables only — `GEMINI_API_KEY` for the Gemini client,
  never a hardcoded value.
- **Never bypass the human-approval gate.** Follow-up drafts stay drafts
  until a human approves them. Do not add any path that sends email, or
  marks a follow-up as sent, without approval.
- **Never invent data.** Sample documents and fixtures must be labelled as
  samples, and accuracy numbers must come from a real run against the
  labelled set — never from a guess. If a number is unmeasured, say so.
- **Do not present a stub as production.** The extractor, classifier,
  storage, auth, and email paths all have stub or fallback behavior;
  keep the docs honest about which path is which.

## Questions

Open a discussion or an issue — a short question with context gets a faster
answer than a long one without it. For anything security-related, see
`SECURITY.md` first: do not open a public issue for a vulnerability.
