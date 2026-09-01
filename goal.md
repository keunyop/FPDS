# Goal: Move Public feedback review to Public `/admin`

## Objective

Make anonymous product-error reports and site feedback submitted through FPDS
Public visible in the password-protected FPDS Public `/admin` page, not in the
authenticated FPDS Admin application.

## In scope

- Add a Public-app-credential-protected feedback read API with optional country,
  type, category, search, and pagination filters.
- Add feedback totals and a detailed inbox to FPDS Public `/admin` behind its
  existing signed HttpOnly session.
- Remove the FPDS Admin feedback page, navigation, client types, and Admin-session
  feedback API.
- Update requirements, planning, decision, API, security, IA, runtime, and
  operating documentation to the corrected Product Owner boundary.
- Add or update focused API regression coverage and verify both frontend
  runtimes.

## Out of scope

- Changing anonymous submission fields, product-context authority, retention,
  rate limiting, or storage schema.
- Adding feedback status, assignment, replies, canonical mutation, Review-task
  creation, notifications, or visitor identity.
- Changing Public analytics collection or the Public `/admin` authentication
  contract.

## Acceptance criteria

- A valid Public `/admin` session can render stored feedback without exposing
  the server-only Public app credential to the browser.
- The inbox supports all-country or exact-country views plus type, category,
  search, and bounded pagination.
- Product reports show immutable product/snapshot context; site feedback shows
  no invented product context.
- Anonymous Public visitors and FPDS Admin sessions have no feedback-list route
  or UI.
- EN/KO/JA submission behavior, privacy, 2,000-character bound, and 400-day
  retention remain unchanged.
- Focused tests, API test suite, both frontend typechecks/builds, and
  `git diff --check` pass.

## Verification

- Focused API feedback tests for credential failure, optional country scope,
  filters, pagination, and removed Admin-session route.
- Public/Admin typecheck and production build.
- Public `/admin` loading, empty, filtered, unavailable, desktop/tablet/390px,
  keyboard-focus, and noindex/auth boundary review.
- Final diff and documentation consistency inspection.
