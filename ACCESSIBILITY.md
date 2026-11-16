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

We have **not yet had a formal accessibility audit**, and we have not yet
completed structured testing with screen readers. This statement describes
what is in place today and what we know still needs work — it is not a
claim that the app already fully meets WCAG 2.2 AA.

## What is in place today

- **Keyboard access:** Interactive elements are native HTML controls —
  buttons, inputs, and selects — which are keyboard-operable by default.
  Nothing in the dashboard requires a mouse or a drag.
- **Labels:** Form fields carry visible labels. The detention calculator
  fields (waited, free, rate) are wrapped in visible labels, and the
  upload form's file and document-type fields are labelled.
- **Status is not shown by colour alone:** Claim status, deadlines, and
  amounts are shown as text — pipeline stages, days left, and dollar
  figures — not as colour alone.
- **Plain structure:** The dashboard is built from ordinary headings,
  lists, and tables, so a screen reader can follow the page order.

## Known limitations

We are aware of the following, and they are on our list to fix:

- **No formal audit or structured screen-reader testing yet.** Until
  that happens, some barriers may still be undiscovered.
- **No systematic labelling audit.** Beyond native semantics and the
  visible labels above, `aria` attributes have not been added or checked
  across the dashboard.
- **Focus visibility not yet verified.** Focus styles have not been
  checked on every interactive element.
- **Colour contrast not yet formally checked.** Text and background
  combinations have not been measured against WCAG contrast ratios.
- **Reduced motion and text scaling:** We have not yet verified
  behaviour for users who prefer reduced motion or who use large text /
  zoom.
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
