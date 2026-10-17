# Development journal

Past completed work notes were removed at the Product Owner's request.
Required cutover reports, current decisions/risks and unfinished goal ownership
remain in the repository; previous journal revisions remain in Git history.

## 2026-10-16 - Hosting costs, bounded retention and clone cleanup

- Added anonymous API CDN caching, threaded read-only DB work, body-free detail
  HEAD and latest-comparison CDN bypass. Combined completed-snapshot/latest-attempt
  lookup into one SQL round trip, preserving exact CA/US/PH and missing-country
  results; live local samples changed from about 32ms to 16ms.
- Fixed the product-search BFF force-dynamic cache override, bounded its fetch,
  disabled automatic product-card detail prefetch and excluded bank-logo/map
  assets from the page proxy. Local code remains separate from serving deployment.
- Existing DB retention was rehearsed with rollback, then committed: 125,330
  unused chunks, 5,962 diagnostic executions, 185 aggregate snapshots, 327 requests,
  78 expired login attempts and 74 expired/revoked sessions removed; 681 Run and
  3,703 source-stage metadata rows compacted. Ten permanent tables compare exactly
  by digest; 178,012 protected chunks, CA120/US85/PH12 and zero orphan links verified.
- Owner requested deletion of bank reports and completed work notes. After initial
  automatic review rejected broader history removal, owner separately approved
  the exact 19-report/91-completed-goal/past-journal list. Total 49 completed dated
  reports removed; nine cutover reports, unresolved parity report and explicit
  open ownership retained. Current README contracts, migrations and captured
  financial fixture bytes remain intact; report links use immutable Git references.
- Final verification: API678/Public128/security11 and browser60 pass with zero
  browser errors. Real BFF repeated reads issue one upstream request; HEAD, fresh
  comparison bypass, true missing/wrong-country404, empty/error/delayed states,
  keyboard/no-JS, four locales and 390/768/1440px pass; three viewports reviewed.
  Lint/typecheck, isolated production build, all tracked Markdown references,
  foundation baseline, strict UTF-8/Python syntax and git diff --check pass.
  Live external API still returns CA120/US85/PH12. No tracked private env/log/pyc.
- Bounded 975.9s SQL sample: 162 current full projection reads/12,004 rows and four
  exact details; older full-query forms did not increase. Billing bytes, requester
  attribution and project memory/paid Observability settings remain unverified.
  Vercel memory accrues while requests remain active, including I/O waits; its
  Observability events also include CDN/functions/external requests, so log-line
  deletion alone cannot remove the charge. [Fluid pricing](https://vercel.com/docs/functions/usage-and-pricing),
  [event definitions](https://vercel.com/docs/observability).
- Owner authorized Production API/Public rollout. Vercel remains uninstalled in
  the latest connection state; await installation/account connection, then inspect
  project integration and release API first, Public second. Permission persists.
  Source changes are local/uncommitted. No runtime/billing change, paid collection,
  data publication or new scheduler was performed. Test servers are stopped.
  Evidence: ignored tmp/hosting-retention-applied.json, hosting-read-verification.json,
  hosting-browser-results.json, hosting-final-delivery-checks.json and hosting-screens/.

## 2026-10-16 - English local startup guide

- Replaced the root README with concise English PowerShell steps for clone,
  frozen installs, local configuration, existing/new development DB prerequisites,
  first-admin bootstrap and separate API4000/Admin3001 terminals.
- Verified commands against package definitions, environment path resolution,
  health response and bootstrap implementation; CLI help for bootstrap, uvicorn
  and Next dev passed. Markdown links, PowerShell snippet syntax, strict UTF-8
  and git diff --check passed. No fresh-clone install or server/login walkthrough
  was performed; the owner will follow the guide. No DB/runtime changes.

## 2026-10-16 - Minimal local DB installation

- Rewrote db/README.md as a concise English first-install guide; aligned root/API
  instructions with api_service.init_local_db. Existing migrations remain unchanged.
- Added empty-development-DB-only atomic initialization: preserve country/type/
  taxonomy/policy/migration references, remove historical bank/source catalog seeds,
  and create exactly one active scrypt-hashed admin/admin account. Production or
  nonlocal settings and pre-existing tables/views/sequences are rejected. Existing
  accounts are never reset; the normal bootstrap minimum-password rule is unchanged.
- API suite: 689 pass. Final initializer suite: 11 pass, including six disposable
  PostgreSQL integration tests for minimal counts, actual login/model and wrong
  password, re-entry/custom-schema preservation, seeded-user rejection and rollback.
  All 48 migration wrappers validate. Local PostgreSQL lacks pgvector: successful
  integration exercised the other 47 migrations; the full path's missing-vector
  failure rolled back completely. Full 48-migration success needs a pgvector server.
- Markdown references, seven PowerShell snippets, strict UTF-8, CLI help, unchanged
  migration diff and git diff --check pass. No existing configured/production DB,
  user account, financial data or serving runtime was changed. Test server stopped.
