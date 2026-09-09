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
