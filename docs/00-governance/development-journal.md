# Development journal

Past completed work notes were removed at the Product Owner's request.
Required cutover reports, current decisions/risks and unfinished goal ownership
remain in the repository; previous journal revisions remain in Git history.

## 2026-11-21 — Desktop Admin ledger

Applied the operator-selected desktop ledger direction using Damir Sokolovsky's
[Unslop](https://github.com/heydamir/unslop) design skill (CC BY 4.0).
The shared shell now has one desktop navigation area. The bank registry joins
search and selection with its counts. The run ledger aligns status, identity,
start time and outcomes. Live refresh sits beside the page heading. Updated
the Admin design system and information architecture to match.

The local production build, typecheck and all 56 Admin tests passed. Chrome
exercised bank and run lists in English, Korean and Japanese at 1440, 768 and
390 pixels against a local fixture API. All 18 combinations fit their available
width. Checked selection, detail loading and Escape, advanced filters, dirty
refresh pause, read-only access, empty results and API failure. The fixture
recorded zero writes and Chrome reported zero uncaught exceptions. Screenshots
and the measurement report are under `tmp/admin-ledger-design/`. Deployment
remains a separate release step.

## 2026-11-21 — Higo and Kagoshima readiness

Registered JP, both Japanese-language banks, eight JP taxonomy entries and 16 catalog scopes in the authorized development database. A second connection verified the configuration and zero JP Runs or canonical products. Rehearsing the registration again showed zero changes. A disposable PostgreSQL test covered initial setup, conflicting ownership rollback, repeated execution and JP login.

The [source inventory](../../worker/discovery/data/jp_higo_kagoshima_listings.csv) has 149 entries from the personal and business directories. The [readiness report](jp-higo-kagoshima-readiness-2026-11-21.md) records source dispositions, the development boundary, and gaps for debit, structured deposits, FX and guarantees. Higo returned a 403 or an access-denied HTML body in the tested environment. Kagoshima's full HTML snapshot yielded 26 scoped PDF leads. A checksum-pinned credit-line disclosure passed ordinary local extraction, normalization and automatic routing including its eight annual brackets and revision terms. The alternate account, corporate scope, removed rate and wrong-document evidence were rejected.

The API suite passed 596 tests with disposable PostgreSQL. The Worker suite ran in four groups (375, 214, 302 and 161 tests). Its obsolete parser version assertion was updated and passed on rerun. Two pre-existing Canadian fixture checksum tests also fail against the committed HEAD bytes (19 National Bank captures and four Oaken captures). The final focused Worker run passed 53 tests. The JP directory and PDF matched their pinned hashes. The foundation baseline, source domains, documentation links and diff checks passed. Runtime deployment and paid collection are pending.

## 2026-11-21 — Official bank documents and collection accuracy

Compared the Floorplan with the actual document selection, snapshot, extraction and approval paths. Both discovery stages now recognize named GIC/CD withdrawal documents. Market and language checks cover document selection and the final response. Relative links use the captured directory, offer query spelling survives the request, and a shared document can retain both parent snapshots at the run URL limit. The snapshot and parser agree on PDF bytes.

The withdrawal condition has one interpretation across extraction and financial verification. A conflicting permission or a qualified prohibition leaves access unverified. Parser v32 also handles the twice-encoded space in the captured TD Cash Back Visa card name. Local replay validated the purchase and cash-advance rates in their respective fields. Restored 23 historical test captures from verified source bytes. All 25 documents in the two affected fixture collections match the existing manifests.

The [collection accuracy policy](../03-design/collection-accuracy-policy.md) states the active rules. The [Korean operator guide](../../descent/은행_상품_수집_검증_가이드.md) explains document and Run checks by product type. The Wells Fargo fixture verified the literal `FPID` and trailing slash used for requests independently of the normalized offer identity.

Local verification passed all 1,045 Worker tests in four groups (335, 198, 185, 327), 594 API tests using disposable PostgreSQL, and 56 Admin tests. Repo Doctor passed on the repository files, as did the foundation baseline, current documentation references and diff checks. Production rollout and live bank collection were outside this local verification.

## 2026-11-21 — Admin collection Floorplan

Rebuilt the Korean collection walkthrough from the current Admin code in the local Floorplan. The 55 file cards and 19 routes cover Banks, selected source collection, official evidence, automatic acceptance and exclusion, canonical versions and Runs. The map and companion explanation are available in the local Floorplan directory.

Verified file and guide links, all three guided flows in Chrome at 390, 768 and 1440 pixels, and the absence of browser errors or network requests from the offline viewer. The Floorplan scanner missed shared guards on Admin endpoints. Manual code verification covered 15 session guards and the role and CSRF guards on all four mapped mutation endpoints. Scope was the selected local code and documentation. The prior walkthrough entry records the earlier map.

## 2026-11-20 — Admin service consolidation

Admin counts active canonical products by country and bank. Collection ends at exclusion or canonical promotion. Removed the consumer web package, anonymous API, projection jobs and refresh monitoring. Migration 0049 registers a separate Admin retention function and preserves existing data.

Local verification passed 592 API tests using disposable PostgreSQL, 56 Admin UI tests, eight maintenance tests and the Admin production build. Chrome exercised Banks and Runs with a fixture API in EN/KO/JA at 390, 768 and 1440 pixels. The retired endpoints returned 404. Of 953 Worker tests, 949 passed. The four failures reproduced on the pre-change revision (two fixture digests and two annual-card disclosure cases). Production services, databases and paid collection were outside this local change.

## 2026-11-20 - Admin bank-product collection walkthrough

- Traced the Banks request through `source_catalog.py`, `source_collection_runner.py`,
  `fpds_collection_accuracy.py` and `candidate_auto_promotion.py` to the country
  publication snapshot. The Korean Floorplan in `floorplan/index.html` covers
  35 source files, 11 request routes and three guided flows.
- Verified the local HTML at 1440, 768 and 390 pixels in Chrome and opened the
  walkthrough at 390 pixels. Reviewed session checks on five Admin routes
  flagged by the static scanner, plus role and CSRF checks on both write routes.
- API 83/83 and Worker 25/26 passed offline. Retrying the existing Worker
  hash test reproduced the failure. All 19 mismatched capture files matched
  Git's stored bytes. For a specific Run, use its retained evidence and the
  country publication status. Live execution and publication were outside scope.

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

## 2026-10-19 - Reversible Switchabank suspension and local startup

- Paused Vercel switchabank-public, switchabank-api and fpds (Admin) through
  authenticated project controls. Final external checks on apex/www, Public alias,
  API health and Admin login all return 503 DEPLOYMENT_PAUSED. Existing project IDs,
  deployments, environment values, domains and unrelated team apps are retained.
- Product Owner corrected scope to keep Supabase running. Kept the existing shared
  DB, account/security controls and private S3 evidence unchanged. Read-only
  inventory: DB about 434 MB; S3 60,022 current objects / 5,787,266,752 bytes.
  Dedicated local DB setup was abandoned before installation after this correction.
- Encrypted original ignored local env files with Windows CurrentUser DPAPI and
  verified decryption equivalence; configured Admin/Public upstreams to
  localhost:4000, matched a new local server-only Public/API credential, and left
  local GA disabled. API4000/Admin3001/Public3000 remain running. README now covers
  all three; descent/05-operations-handbook.md records provider inventory, actual
  actions, billing/access limits, owner work and API-first resume order.
- Verified local health, country reads and CA/US/PH API/BFF product responses; real
  Public Home and Admin login in Chrome at 1440/768/390px return 200 without page
  errors or horizontal overflow. Unauthenticated API session returns 401. Browser
  writes/external requests were blocked. Existing-account login and collection or
  feedback/engagement writes were not exercised; no app code changed. Initial cold
  Admin compilation exceeded the first HTTP timeout; warm HTTP/browser checks pass.
- Limits: Supabase project management is unavailable to the connected account;
  project remains running as requested. AWS storage credentials cannot list EC2;
  broader AWS/billing and paid subscriptions require owner-console checks. Vercel
  Pause stops production serving; Git builds and every historical Preview are not
  claimed stopped. Original build/Preview control settings are absent from connector
  readbacks, so they were preserved and Git disconnect/reconnect is documented for
  the owner. No termination, canonical writes, schema change, paid collection,
  deployment or publication. UTF-8, changed references, PowerShell snippet syntax
  and git diff --check verified; final diff/goal reviewed. Evidence stays ignored
  under .tmp/suspension-20261019/. Next: owner checks remaining billable services;
  resume hosted API, Public, Admin when service return is requested.
