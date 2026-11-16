# Accessibility Statement — ClaimKit

**Last updated:** November 15, 2026

## Our commitment

ClaimKit is Automated Business Claims Recovery for freight brokers and
transportation companies — collecting evidence, identifying recoverable
charges, assembling claim packages, and tracking reimbursement and
deadlines.

We want everyone who works a claim to be able to use it, including people
who use a keyboard, a screen reader, magnification, or other assistive
technology. Accessibility is part of how we judge whether a feature is
finished, not an afterthought.

## Standard we aim for

We aim to meet **WCAG 2.2 Level AA** (Web Content Accessibility
Guidelines, version 2.2, conformance level AA).

We have run automated accessibility testing of the dashboard (see Testing
below) and fixed what it found. We have **not yet had a formal
accessibility audit**, and we have not yet completed structured testing
with screen readers. This statement describes what is in place today and
what we know still needs work — it is not a claim that the app already
fully meets WCAG 2.2 AA.

## What is in place today

- **Keyboard access:** Interactive elements are native HTML controls —
  buttons, inputs, and selects — which are keyboard-operable by default.
  Nothing in the dashboard requires a mouse or a drag. A keyboard
  walkthrough on November 15, 2026 reached every control on the home
  page and the dashboard, and every one showed a visible focus outline.
- **Labels:** Form fields carry visible labels. The detention calculator
  fields (waited, free, rate) are wrapped in visible labels, and the
  upload form's file and document-type fields are labelled.
- **Status is not shown by colour alone:** Claim status, deadlines, and
  amounts are shown as text — pipeline stages, days left, and dollar
  figures — not as colour alone.
- **Plain structure:** The dashboard is built from ordinary headings,
  lists, and tables, so a screen reader can follow the page order. The
  pages carry `lang="en"`, a page title, a single `h1`, and a `main`
  landmark.

## Testing

Automated testing run on November 15, 2026, against the dashboard as
built from `main`:

- **Tool:** axe-core with the WCAG 2.2 AA rule set, run in Chromium
  over the home page (`/`) and the dashboard (`/dashboard`), plus a
  keyboard walkthrough and a mobile-width (390px) layout check.
- **Found and fixed:** 2 critical issues on the dashboard — the upload
  form's file input and document-type select had no labels — and the
  upload row forced horizontal scrolling at 390px. All three were fixed
  (visible labels added, the row now wraps) and re-tested.
- **Result after the fixes:** 0 axe violations on both pages, no
  horizontal scrolling at 390px, and every control reachable by keyboard
  with a visible focus indicator.
- **Not covered:** no structured screen-reader testing and no formal
  audit have happened yet — see Known limitations.

## Known limitations

We are aware of the following, and they are on our list to fix:

- **No formal audit or structured screen-reader testing yet.** Automated
  testing has now been run (see Testing above), but until a screen-reader
  pass and a formal audit happen, some barriers may still be
  undiscovered.
- **Colour contrast:** the automated run checked rendered text contrast
  and found no failures, but a manual check of every text/background
  combination has not been done.
- **Reduced motion and text scaling:** We have not yet verified
  behaviour for users who prefer reduced motion or who use large text /
  zoom. The dashboard currently has no animations or transitions.
- **Hosted demo, phone width:** In the hosted demo, the tab bar and the
  Docs permissions table scroll horizontally inside their own containers
  at phone width.

If you find anything else, please tell us — see Feedback below.

## Feedback

If you hit a barrier using ClaimKit, or you have a suggestion for making
it easier to use, please open a bug report
([bug report template](.github/ISSUE_TEMPLATE/bug_report.md)) and say it
is an accessibility issue.

It helps if you include:

- the page or feature where you hit the problem (for example, the
  dashboard, the upload form, or the approval queue);
- what you were trying to do;
- the device, browser, and assistive technology you were using, if you
  know them.

We will review every report and prioritise fixes, starting with barriers
that prevent someone from completing a task — such as uploading evidence,
reviewing an extraction, or approving a follow-up.

## Review

We review this statement when we add or change a feature, and after any
accessibility testing or audit, and update it to reflect what has changed.
