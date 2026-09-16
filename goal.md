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
