# Security Policy

## Supported versions

ClaimKit is an early starter (current release: v0.1.0). Security fixes are
provided for:

| Version | Supported |
| ------- | --------- |
| `main` (latest) | ✅ |
| Latest release (v0.1.0) | ✅ |
| Older releases | ❌ |

If you are running an older release, update to the latest release or `main`
first — a fix may already exist there.

## Reporting a vulnerability

**Do not open a public issue for a vulnerability.** Report it privately
through GitHub's private vulnerability reporting on this repository
(Security tab → Report a vulnerability). That keeps the details private
until a fix is ready.

Please include, when you can:

- A description of the vulnerability and what it affects
- Steps to reproduce it
- The version or commit you tested against
- Your assessment of the impact, if you have one

Reports are reviewed promptly. You will hear back about whether the report
is accepted and what the next step is; please allow time for a fix to be
prepared before disclosing anything publicly.

## Scope

In scope: the code in this repository — the FastAPI backend, the Next.js
frontend, the document-processing pipeline, authentication and role checks,
and the GitHub Actions workflows.

Out of scope: vulnerabilities in third-party services ClaimKit talks to
(such as the Gemini API, Supabase, or Cloudflare), and issues that need a
real API key, credential, or production account to reproduce. Do not test
against anyone else's deployment.

## No bounty program

ClaimKit has no bug bounty program. Reports are appreciated and credited
in the fix (with your permission) but are not paid.

## What not to do

- Do not run automated scanners against the hosted demo or anyone else's
  deployment.
- Do not exfiltrate, modify, or delete data while investigating.
- Do not disclose a vulnerability publicly before a fix is available.
