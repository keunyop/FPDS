# Admin pre-handover review and fixes

## Objective
Review FPDS Admin against descent/README.md, repair reproducible handover defects,
and leave an evidence-based readiness record for the Product Owner.

## Scope
Admin operator flows, auth/RBAC, country isolation, error/retry handling, related
API contracts, and handover documentation. Small reversible fixes for confirmed
defects. Assess screen purpose and missing essentials within approved scope.

## Exclusions
No production deployment, live collection/review/publication, canonical mutation,
migration execution, account changes, external transfer, release tag or UAT approval.
No Public redesign, new countries/products or restored standalone audit/usage.
Preserve existing edits in descent/README.md and the journal, deleted SEO documents,
and the deleted temporary log.

## Acceptance
- [x] Record findings and screen/feature disposition against the handover guide.
- [ ] Fix confirmed in-scope defects with success/boundary/failure regression checks.
- [x] Run Admin typecheck/build, API/Worker suites and foundation checks as available;
      record exact results and limitations without claiming client UAT.
- [x] Provide a readiness record and actionable remaining owner tasks.
- [x] Update the journal, inspect final diff and run git diff --check.

## Verification
Use repository commands and focused regressions. No live secrets or external
mutations. Layout changes require desktop/tablet/exact 390px checks.

## Current completion boundary
Authorized auth/UI/attention/header fixes and local verification are complete.
The account lifecycle CLI remains unwritten pending explicit approval after
automatic approval review rejection. Keep this goal until that scope is resolved.
No live account operation is authorized by a code implementation approval.

## Parallel bounded slice: 2026-09-07 Search Console diagnosis

Ownership: the Admin goal above remains open and is preserved. This independent
SEO investigation does not take over its acceptance or delete this goal file.

Objective: interpret the supplied Coverage ZIP and verify current public crawl
signals, recording confirmed defects and concrete Search Console follow-up.
Scope: report CSVs, existing Public SEO policy, read-only public HTTP checks,
and a dated diagnosis. No deployment, GSC mutation, data change, or UI redesign.
Acceptance: reconcile counts and dates; distinguish observed signals from unknown
reported URLs; verify representative live routes and sitemap using the existing
audit where available; record limitations and next steps; update journal.
Verification: public HTTP reads, existing SEO audit, document diff review and
git diff --check. Runtime fixes require a reproduced defect and relevant tests.

SEO diagnosis acceptance is complete: four CSVs reconciled, historical dates
identified, Production audit passed 225 sitemap URLs and 10 representative
routes, and diagnosis/journal record known limits and GSC follow-up. No runtime
fix was justified by the observed responses. Preserve this root goal for the
unresolved Admin scope above; SEO completion does not close that ownership.

## Independent slice: 2026-09-12 Admin purpose and feature documentation

Ownership: preserve the unresolved Admin handover goal and completed SEO slice.
This documentation request neither authorizes the account lifecycle CLI nor
closes the earlier goal.

Objective: write a Korean Markdown guide to FPDS Admin purpose and all current
features, grounded in active documentation and executable source code.
Scope: inspect Admin routes/components, related API/worker contracts and tests;
correct confirmed stale active documentation and add navigation to the guide.
Exclusions: runtime changes, live collection, account/data mutations, migrations,
deployment, scope expansion, and edits to existing untracked manual/images.
Acceptance:
- [x] Explain purpose, workflow, screens, roles, country/locale boundaries,
      automation/publication, and implemented versus deferred/removed features.
- [x] Link source evidence and reconcile confirmed stale active descriptions.
- [x] Verify document links and final diff; run git diff --check; update journal.
Verification: read-only route/API/worker inspection, focused document-link and
manifest checks, and diff review; no unrelated application builds required.

Completion: the Korean guide and active-document reconciliation are complete.
18 page files match the Admin manifest and all Admin routes are covered; 59
API method/path pairs match the API README. Markdown references and diff checks
pass. No runtime or external state changed. Preserve this goal file because
the earlier Admin account-lifecycle acceptance remains unresolved.

## Independent slice: 2026-09-16 Public growth investigation

Ownership: preserve the unresolved Admin handover goal and prior completed slices.
Objective: inspect SwitchaBank source and the public site, then propose features
that improve qualified acquisition, useful engagement, and official-bank visits.
Scope: read-only Public/API/data-contract inspection, public HTTP/browser checks,
current primary-source research, and a Korean evidence-based proposal.
Exclusions: runtime changes, deployment, collection/publication, canonical data
changes, analytics/account configuration, or approval of expanded product scope.
Acceptance:
- [x] Distinguish existing features, observed gaps, and unmeasured hypotheses.
- [x] Prioritize concrete features with user flows, dependencies, metrics, and
      existing-scope versus new-approval boundaries.
- [x] Record source/site evidence, limitations, verification, and journal outcome.
Verification: static source review, anonymous live-site reads and bounded browser
checks where available, document-link verification, and git diff --check.

Completion: the Korean proposal records existing functionality, verified live
findings, prioritized features, scope boundaries, and measurement limitations.
The 225-URL Production SEO audit and representative browser/API probes passed
within their stated scope; the observed product issues remain unfixed because
this was a proposal request. Preserve this goal for the prior Admin ownership.

## Independent slice: 2026-09-16 Public rate semantics correction

Ownership: preserve the unresolved Admin goal and earlier completed slices.
Objective: prevent reference-rate spreads, ranges, conditional rates and
promotions from being represented or compared as an unqualified full rate.
Authorization: Product Owner explicitly requested implementation and separate
self-review of API/UI changes and existing-public-data corrections.
Scope: shared public rate interpretation, catalog/detail/Home/finder consumers,
rate-based sorting and calculations, regression coverage, and a bounded audit
of already published CA/US records. Preserve original qualifying source text.
Exclusions: growth features, freshness remediation, collection automation,
new countries/types, account changes, or inferred current-prime calculations.
Acceptance:
- [x] Classify full rates, ranges, reference spreads, conditional rates and
      promotions; exclude non-comparable values from rankings and differences.
- [x] Reproduce and fix BMO word-plus/word-minus and symbolic reference cases.
- [x] Audit published data separately and record whether persisted corrections
      are required; make no speculative or unaudited canonical changes.
- [x] Verify API and EN/KO/JA Public behavior, regression tests, responsive UI,
      builds and final diff; record checks and any unverified external behavior.
Verification: focused semantic fixtures, complete API/Public test suites,
Public lint/typecheck/build, bounded browser checks with analytics blocked,
anonymous published-data audit and git diff --check. Production deployment is
not part of this implementation slice unless explicitly requested.

Completion: shared rate semantics and every numeric consumer are implemented;
API 481 and Public 12 tests, lint/typecheck/build, 19 browser scenarios and
foundation/diff checks pass. The separate one-record Vancity correction is
committed with version/change/snapshot history, unchanged unrelated records,
idempotence and live-read verification. BMO source data required no mutation.
Code deployment remains outside this slice. Preserve the unresolved prior
Admin goal and its independent ownership.

## Independent slice: 2026-09-16 Home Top 5 bank logos

Objective: restore official bank images missing from the Home Top 5 lists.
Scope: reproduce CA/US Home, add verified same-origin logo assets for the
missing displayed banks, preserve existing text fallback and dimensions.
Exclusions: rate/ranking changes, database writes, API contracts, deployment.
Acceptance:
- [x] Identify missing mappings versus failed network/image requests.
- [x] Verify sourced bank assets and render affected Home rows at 390/768/1440px.
- [x] Run Public tests, typecheck/build and diff checks; update journal.
Preserve prior goal ownership and unrelated proposal edits.

Completed: 13 Public tests, lint, typecheck, production build and all 18
CA/US x EN/KO/JA x 390/768/1440 browser cases passed (two initial data-load
timeouts passed on retry). Local image decode, alt text and no horizontal
overflow verified. No deployment or canonical-data mutation.

## Independent slice: 2026-09-21 Public verification freshness

Ownership: preserve unresolved Admin goal and earlier slices.
Objective: separate snapshot generation from product verification, with elapsed
verification status and manual operator follow-up under D-069.
Scope: Public API/UI, product-type policy, read-only overdue report, documentation.
Exclusions: automated collection, live mutations, deployment, ranking formulas,
new countries/types, evidence exposure, unrelated Admin work.
Acceptance:
- [x] Separate snapshot success/date from product verification/status; no date fallback.
- [x] Document and implement product-type intervals, expiry and unknown handling.
- [x] Provide overdue list and manual operator review cadence.
- [x] API/Public regression suites, lint/typecheck/build, 390/768/1440px UI checks.
- [x] Update contracts/journal, inspect diff and run git diff --check.
Verification: deterministic boundary, failure and regenerated-snapshot checks;
localized browser regression with no analytics writes. Initial warning-only policy uses 7/30 and 30/90 elapsed days; optional PO preference remains adjustable.

Completion: API 490, Public 16 and worker aggregate-refresh 7 tests pass;
lint/typecheck/production build, 70 browser cases, read-only CA/US report,
repo doctor/foundation and final diff checks pass. Dates, statuses, manual report
and initial warning-only policy are documented. No deployment or live mutation.
Preserve this file for the earlier unresolved Admin ownership.


## Independent slice: 2026-09-24 Public deposit comparison and estimates

Ownership: preserve the unresolved Admin goal and all prior completed slices.
Objective: implement growth proposal section C with defensible deposit comparison
conditions, explicit calculation eligibility and a self-reviewed INDEXED GIC
investigation; keep the existing restrained EN/KO/JA experience.
Scope: approved Public fields, API comparison/calculation contract, Home deposit
rankings, same-type finder, detail calculator, regressions and active documents.
Exclusions: other growth features, personal scoring, new countries/types,
collection, deployment, speculative canonical edits or unrelated Admin work.
Acceptance:
- [x] Review INDEXED GIC against its official source and document the result.
- [x] Match currency, deposit type, rate basis and GIC term before comparison;
      reject ambiguous, conditional and promotional calculations.
- [x] Make amount/period assumptions visible; avoid a zero initial amount;
      show concise unavailable reasons and an official-bank path.
- [x] Explicitly revise FR-PUB-021 and related runtime/design documents.
- [x] Pass focused and regression API/Public tests, lint/typecheck/build and
      EN/KO/JA desktop/tablet/exact-390px browser checks; inspect final diff.
Verification: read-only official-source investigation, financial boundary/failure
regressions, existing suites, browser checks with analytics blocked, journal
update and git diff --check. Do not claim zero bugs or a deployment from tests.

Completion: the selected comparison/calculation slice and INDEXED GIC self-review
are complete. API 502, Public 22, aggregate 8 and Admin 5 tests pass; final
lint/typechecks/builds, 79 browser cases plus 15 final-build smoke checks,
216-product compatibility replay, repository/foundation and diff checks pass.
No deployment or live data writes. Missing source semantics remain explicit
unavailable states. Preserve this file for the unresolved earlier Admin goal.

## Independent slice: 2026-09-24 Home comparison condition refinement

Ownership: preserve the unresolved Admin goal and prior completed slices.
Objective: replace Home Deposit Top 5 currency choices with concise product
conditions while preserving compatible rate comparisons and other features.
Scope: Public Home condition grouping, EN/KO/JA labels, regression tests and docs.
Use the selected country's home currency; Savings conditions use disclosed zero
monthly fee or zero minimum balance, and GIC retains exact term/redemption.
Exclusions: API/data changes, finder/calculator behavior, deployment, collection,
new countries/types and unrelated Admin work.
Acceptance:
- [x] Replace currency-led choices with grounded product conditions.
- [x] Preserve country/currency/basis/term gates, ordering and empty/error states.
- [x] Verify Public regressions, lint/typecheck/build and EN/KO/JA at
      1440/768/exact 390px, including unaffected Loan/catalog/finder/calculator.
- [x] Update active docs/journal, inspect final diff and run git diff --check.
Verification: deterministic boundary tests, browser fixtures and published-data
reads with analytics/feedback blocked. Do not claim zero bugs or deployment.

Completion: product-condition presets and concise currency/basis context are
implemented. Public 28 tests, lint/typecheck/production build, 79 browser
regression cases and 30 final-build Home cases pass; EN/KO/JA at 390/768/1440px,
keyboard focus, empty/error, Loan isolation, catalog comparison, finder and
calculator paths verified. KO mobile/EN desktop screenshots inspected. No API,
canonical data or deployment changes. Keep this file for prior Admin ownership.

## Independent slice: 2026-09-24 Loan Home comparison conditions

Ownership: preserve the unresolved Admin goal and completed Deposit changes.
Objective: add concise Loan Top 5 conditions matching the Deposit interaction.
Scope: Home loan Product Type and disclosed secured/unsecured presets, complete
snapshot pagination, EN/KO/JA, regression tests and active documentation.
Boundaries: use CA CAD / US USD, retain explicit comparable full-rate eligibility
and ascending order; do not infer security from names or unknown flags.
Exclusions: API/worker/financial data changes, finder/catalog changes, deployment,
new countries/types or personalized suitability.
Acceptance:
- [x] Provide product-based conditions with the existing compact selector style.
- [x] Rank each type/condition from all pages without mixing country/currency;
      later-page failures and changed snapshots fail closed.
- [x] Verify Public tests/lint/typecheck/build, EN/KO/JA at 390/768/1440px,
      empty/error/pagination and Deposit/Loan independence plus existing flows.
- [x] Update docs/journal, inspect final diff and run git diff --check.

Completion: Loan product-type/security presets and full-snapshot pagination are
complete. Public 34 tests, lint/typecheck/build, 52 final-build browser cases,
visual screenshots and git diff --check pass. Existing API source/classification
discrepancy I-005 remains a separately scoped follow-up; no financial data or
API semantics were changed. Keep this goal for prior unresolved Admin ownership.

## Independent slice: 2026-09-24 bounded Home Top 5 data completion

Ownership: preserve the unresolved Admin goal and all earlier slices.
Objective: investigate short Deposit/Loan condition lists and supplement only
the official-bank facts/products needed to fill existing Home Top 5 conditions.
Authorization: Product Owner requested official-page research and bounded
product-data completion; no full-catalog research or unrelated release.
Scope: existing CA/US countries and Deposit/Loan types, existing canonical
products first, evidence-backed corrections and audited publication.
Exclusions: invented rates, relaxed comparison gates, new countries/types,
account operations, general collection sweeps, UI redesign and deployment.
Acceptance:
- [x] Record current condition counts and why records are excluded.
- [x] Research a bounded shortlist on official bank pages; preserve financial
      basis, currency, term, qualifiers and field-level evidence.
- [ ] Apply verified additions/corrections through an audited, reversible path;
      stop each condition at five or document a concrete evidence limitation.
- [x] Verify Public eligibility/counts, unchanged unrelated records, relevant
      regressions, final diff and journal outcome.
Verification: read-only baseline, official-source review, rollback rehearsal,
bounded apply and live readback; preserve immutable history.

Progress: nine existing-product corrections are committed and verified; CA
Savings presets reach five. US three-candidate manual review approval remains
pending; Loan/GIC evidence limits are recorded in the dated data report. No
blanket Top 5 completion is claimed. Preserve this goal and prior ownership.
