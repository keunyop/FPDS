# FPDS API Service

Staged recovery (2026-10-01): ten additional products published through normal current gates; Public API CA 29 / US 5. All 404 initial unpublished have dispositions; 394 unsupported targets excluded from this one-off list with history preserved. Exact separate card-offer/rate-note meaning and monthly debit rows are supported; fixed-duration/age/balance zero fees and comparison benchmark rates remain rejected. Matching shared instructions and Worker 624 / API 539 tests pass. Future collection-runtime deployment is separate; no UI/schema or deployment change.

Remaining-card recovery (2026-10-01): shared normalization preserves unchanged field-bound numeric evidence; current no-fee future change notices are distinguished from temporary/conditional waivers. Six cards published through normal gates; Public API CA 20 / US 2. Worker 611 / API 539 pass. No route/UI/schema or deployment; collection-runtime deployment remains required for future collection.

Card bulk recovery (2026-10-01): shared exact labelled current annual-card-rate handling and matching normalization/extraction instructions are updated locally. Two cards published through normal gates; Public API CA 14 / US 2. Worker 608 / API 539 pass. No route/UI/schema change or deployment.

Shared card-rate context correction (2026-10-01): the current Platinum annual-rate false exclusion is fixed with a bounded separate-offer distinction and matching collection/card-normalization instructions. Existing publication prerequisites and receipt/profile versions remain. One card was published through the local corrected worker and compatible serving API. Worker 605 / API 539 tests pass. Future Admin collection requires collection-runtime/API deployment; no route/UI/schema changed.

Shared checking evidence correction (2026-10-01): exact allowance/excess rows and ordinary-versus-channel scope are enforced with matching collection instructions. Existing financial prerequisites and receipt/profile versions are unchanged. Two hidden TD accounts were published through the local corrected worker and compatible serving API. Worker 601 / API 539 tests pass. Future Admin collection requires collection-runtime/API deployment; no route, UI or schema changed.

The shared normalization worker now preserves database-resolved current-run supporting-document origins (2026-10-01). Deploy the collection runtime/API package to apply this fix to future Admin collection. No API route, UI, receipt version, publication prerequisite or schema changed. Two prepared Scotiabank products were published using the local corrected worker and existing deployed gates; code deployment remains separate.


Public list/detail now serialize optional `deposit_conditions` for Savings/GIC:
only six explicit nonempty source-language strings from the approved projection
(interest calculation/payment, compounding, payout, tiers, promotion period).
Wrong types and arbitrary metadata are omitted; absent objects serialize as `{}`.
No raw evidence, private payload or receipt is exposed. Deploy before Public to
show additional verified detail facts; no migration or data mutation is required.

## Autonomous collection — 2026-09-30

New stamped candidates require automatic accuracy acceptance before canonical
promotion; automatic exclusion cannot be bypassed by a manual decision.
Late failures are rejected without review tasks. The collection runner does not
invoke review autopilot. Run detail returns `automatically_excluded_count` from
stamped rejected candidates. The approved legacy data cutover is applied. All
five product-review mutation endpoints now return `410 product_review_retired`
in code after auth/role/CSRF/country checks; historical reads expose no actions.
The Product Owner reports this prior build deployed. New economical-recovery
worker changes and shared accuracy fixes require the next runtime deployment. See
[policy](../../docs/03-design/collection-accuracy-policy.md).

This package is the live FastAPI runtime for authenticated Admin operations
and Public aggregate reads, engagement, and feedback. The current endpoint
map is implemented in `api_service/main.py`; historical WBS delivery numbers
do not by themselves describe the current enabled surface.

## OpenAI model and reasoning

All OpenAI requests use the shared model selection, defaulting to `gpt-6-luna`.
Bank onboarding research (including official bank evidence), candidate page
scoring and coverage route discovery explicitly use `medium`; Product Type
keyword generation uses `none`. The retired Review AI implementation used `high`. Worker extraction uses
`high` and dynamic normalization uses `medium`. Settings are fixed per task;
there is no global effort environment override. See the
[environment contract](../../docs/03-design/dev-prod-environment-spec.md).
Set `FPDS_LLM_MODEL=gpt-6-luna` in each deployed runtime and restart/redeploy it
to apply the change. Local tests do not establish deployed model access,
latency or accuracy; canonical approval and official-evidence gates are unchanged.

Current scope:
- anonymous public aggregate-backed product, product-detail, and dashboard read
  APIs plus credential-bound bounded product-engagement and anonymous-feedback
  writers, a private engagement summary, and a private Public operations
  feedback inbox
- DB-backed admin user accounts
- DB-backed admin sessions
- enabled-country discovery plus country-required login, logout, session
  introspection, and approval-gated signup-request routes
- CSRF-protected switching of the current Admin session to another
  active working country
- admin-only prepared-country registry listing, activation, reversible
  deactivation and session revocation
- review queue list route backed by `review_task` and `normalized_candidate`, including source role, missing expected fields, and a recommended next action
- review-task detail read route with field-level trace, evidence metadata, model-run references, and decision history context
- read-only historical AI verification results; launching a new Review AI check is retired
- run list route backed by `ingestion_run` with protected run-state diagnostics
- run detail read route with source processing summary, error summary, and related review tasks
- change-history list route backed by `change_event` with protected canonical chronology and review-decision context
- bank registry list/detail/create/update routes backed by `bank`
- admin-only, CSRF-protected AI bank onboarding for the session country, with
  required live web research, largest-first duplicate exclusion, official
  homepage/logo/active Product Type evidence, customer-facing display-name
  validation, preserved legal/ranking names, and atomic creation; onboarding
  uses bounded ranking discovery followed by server-pinned, one-bank-at-a-time
  official-evidence calls so one failed candidate cannot consume the batch
- guarded bank deletion when no collected source document, candidate, canonical
  product, or Public projection depends on the bank; remaining coverage and
  generated-source rows are deleted with the profile
- source catalog list/detail/create/update routes backed by `source_registry_catalog_item`
- source catalog-selected collection launch backed by grouped `ingestion_run` creation and an API-side collection runner
- auto-promotion for `auto_validated` pass candidates after collection, including non-detail/non-product skip/reject guards and same-detail-source stale-review supersession
- generated-source list/detail inspection and admin-only soft removal; direct
  create/update handlers return `405`
- shared Product Type registry list/detail/create/update/delete routes; writes
  require admin, while collection/publication profiles remain country-owned
- retired product-review mutation routes: approve, reject, defer, edit-approve and ai-verify return 410
- historical review tasks cannot be reopened through the retired endpoints
- canonical product/version creation and change events for automatically accepted facts
- preserved historical review decisions and evidence, with no manual correction path
- bounded login failure tracking for throttling and lockout enforcement
- bootstrap CLI for the first operator account

Current routes:
- `GET /api/public/countries`
- `GET /api/public/products`
- `GET /api/public/products/:productId`
- `GET /api/public/filters`
- `GET /api/public/dashboard-summary`
- `GET /api/public/dashboard-rankings`
- `GET /api/public/dashboard-scatter`
- `POST /api/public/engagement`
- `POST /api/public/feedback`
- `GET /api/public/admin/engagement-summary`
- `GET /api/public/admin/feedback`
- `GET /api/admin/auth/countries`
- `POST /api/admin/auth/login`
- `POST /api/admin/auth/signup-requests`
- `GET /api/admin/auth/signup-requests`
- `POST /api/admin/auth/signup-requests/:signupRequestId/approve`
- `POST /api/admin/auth/signup-requests/:signupRequestId/reject`
- `POST /api/admin/auth/logout`
- `GET /api/admin/auth/session`
- `POST /api/admin/auth/country`
- `GET /api/admin/countries`
- `POST /api/admin/countries/:countryCode/activate`
- `DELETE /api/admin/countries/:countryCode`
- `GET /api/admin/review-tasks`
- `GET /api/admin/review-tasks/:reviewTaskId`
- `POST /api/admin/review-tasks/:reviewTaskId/ai-verify` — retired, 410
- `GET /api/admin/runs`
- `GET /api/admin/runs/:runId`
- `POST /api/admin/runs/:runId/retry`
- `GET /api/admin/dashboard-health`
- `POST /api/admin/dashboard-health/retry`
- `GET /api/admin/change-history`
- `GET /api/admin/banks`
- `POST /api/admin/banks`
- `POST /api/admin/banks/ai-onboard`
- `GET /api/admin/banks/:bankCode`
- `PATCH /api/admin/banks/:bankCode`
- `DELETE /api/admin/banks/:bankCode`
- `GET /api/admin/source-catalog`
- `POST /api/admin/source-catalog`
- `GET /api/admin/source-catalog/:catalogItemId`
- `PATCH /api/admin/source-catalog/:catalogItemId`
- `POST /api/admin/source-catalog/collect`
- `GET /api/admin/sources`
- `POST /api/admin/sources` (compatibility handler; returns `405`)
- `GET /api/admin/sources/:sourceId`
- `PATCH /api/admin/sources/:sourceId` (compatibility handler; returns `405`)
- `DELETE /api/admin/sources/:sourceId` (admin-only soft removal)
- `GET /api/admin/product-types`
- `POST /api/admin/product-types`
- `GET /api/admin/product-types/:productTypeCode`
- `PATCH /api/admin/product-types/:productTypeCode`
- `DELETE /api/admin/product-types/:productTypeCode`
- `POST /api/admin/source-collections`
- `POST /api/admin/review-tasks/:reviewTaskId/approve` — retired, 410
- `POST /api/admin/review-tasks/:reviewTaskId/reject` — retired, 410
- `POST /api/admin/review-tasks/:reviewTaskId/edit-approve` — retired, 410
- `POST /api/admin/review-tasks/:reviewTaskId/defer` — retired, 410
- `GET /healthz`

## Local Run

Apply the DB baseline in order:

```powershell
psql $env:FPDS_DATABASE_URL -f db/migrations/0001_initial_baseline.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0002_admin_auth.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0003_aggregate_refresh.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0004_source_registry_admin.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0005_source_registry_unique_scope_fix.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0006_bank_catalog_management.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0007_dynamic_product_type_onboarding.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0008_discovery_metadata_persistence.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0009_backfill_review_edit_approved_candidate_product_name.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0010_aggregate_refresh_queue.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0011_admin_signup_requests.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0025_country_scoped_admin.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0026_country_registry_management.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0027_standalone_ai_operations.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0028_source_catalog_coverage_evidence.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0029_collection_ai_autopilot_policy.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0030_collection_approval_field_policy.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0031_catalog_coverage_route_evidence.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0032_comparison_grade_collection_quality.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0033_essential_field_low_touch_publication.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0034_country_product_market_profiles.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0035_collection_publication_automation.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0036_us_pricing_evidence_companions.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0037_us_pricing_companion_scope_cleanup.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0038_us_cross_product_support_cleanup.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0039_us_credit_card_apr_range_contract.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0040_bounded_operational_storage.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0041_vancity_official_product_routes.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0042_three_bank_partial_run_scope_hardening.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0043_generic_zero_detail_scope_quarantine.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0044_remove_admin_collection_scheduler.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0045_public_product_engagement.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0046_public_feedback_submission.sql
```

Create the first operator account:

```powershell
cd api/service
uv run python -m api_service.bootstrap_admin_user --env-file ..\..\.env.dev --login-id admin --display-name "Admin Operator" --role admin
```

Run the API:

```powershell
cd ..\..
$env:FPDS_ENV_FILE=".env.dev"
uv run --directory api/service uvicorn api_service.main:app --reload --host localhost --port 4000
```

## Vercel API Deployment

The repository root is the Vercel project root. Root `app.py` exposes the
existing `api_service.main` FastAPI instance, root `pyproject.toml` and
`uv.lock` install the complete runtime dependency set, and `.python-version`
pins Python 3.12. Do not configure the Vercel project with `api/service` as its
Root Directory.

Root `pyproject.toml` also declares
`[tool.vercel] entrypoint = "app:app"`. Keep this explicit declaration even
though `app.py` is a recognized filename: the wrapper imports the existing
runtime package dynamically, so Vercel must not rely on static app discovery.

This first deployment is operated as a public-read API. The FastAPI process has
no background collection loop; collection starts only through authenticated
Admin actions. Existing authenticated Admin routes remain part of the FastAPI
app, but no Admin web application is deployed in this slice.

Configure these variables separately for Vercel Production and Preview; never
upload or copy `.env.dev` as a production environment file:

- `FPDS_ENV=prod`
- `FPDS_DATABASE_URL` for the selected database; a separate production database
  remains the default release posture
- `FPDS_PUBLIC_WEB_ORIGIN` and `FPDS_ADMIN_WEB_ORIGIN`
- `FPDS_PUBLIC_API_ORIGIN` and `FPDS_ADMIN_API_ORIGIN`
- unique production `FPDS_ADMIN_SESSION_SECRET` and `FPDS_ADMIN_CSRF_SECRET`
- a long random `FPDS_PUBLIC_APP_API_SECRET` shared only with the matching
  Public app environment
- `FPDS_COOKIE_SECURE=true`

After Vercel authentication and environment configuration:

The Vercel project is `switchabank-api`. The 2026-08-23 project rename
preserved its project ID. Its stable Production domain is now
`https://switchabank-api.vercel.app`; the legacy `bankompare-api` stable,
team, and main-branch aliases were removed after the SwitchaBank domain
migration.

```powershell
pnpm dlx vercel@latest link --yes --project switchabank-api
pnpm dlx vercel@latest deploy --prod
```

Verify `/healthz` first, then one country-scoped `/api/public/products` request.
Public reads require the production schema/migrations and a completed aggregate
snapshot. A healthy process alone does not prove that its database projection
is release-ready.

Temporary operating exception (2026-08-22): the Product Owner explicitly
authorized both Vercel environments to reuse the current development database
while automatic refresh is paused. Only the database URL was registered as a
sensitive Vercel variable; `.env.dev` was not uploaded, and Preview/Production
use newly generated environment-specific session and CSRF secrets. Replace the
shared database connection with a separate production database before this
temporary coupling becomes release-critical.

Run the standalone regression suite:

```powershell
cd api/service
.venv\Scripts\python.exe -m unittest discover -s tests/regression -p "test_*.py"
```

## Notes

- Public read routes now use the latest successful `aggregate_refresh_run` snapshot and read from `public_product_projection`.
- GET /api/public/products and GET /api/public/filters accept an optional q
  value up to 120 characters. It is normalized for surrounding/repeated
  whitespace and matches bank_name or product_name case-insensitively as a
  literal substring; percent and underscore are ordinary characters, not
  query wildcards. The normalized value is returned as applied_filters.q.
- GET /api/public/products also accepts product_name, which searches only the
  public product name and does not require bank_code or product_type. A blank
  value with product_name ascending sort returns all active products through
  normal bounded pagination.
- Public list pagination remains page/page_size API state so the web catalog
  can load successive pages without exposing raw evidence or new data.
- POST /api/public/engagement and GET
  /api/public/admin/engagement-summary fail closed without the shared
  Public-app credential. Writes accept only an active product ID plus one fixed
  event type, are process-rate-limited, and persist only 400-day daily product
  counts; no visitor-level or search value is stored.
- POST /api/public/feedback requires the same Public-app credential, fixed
  product/site category pairs, ISO country, EN/KO/JA locale, and at most 2,000
  optional detail characters. Product reports are inserted only from an active
  product in the latest completed Public snapshot. GET
  /api/public/admin/feedback requires the server-only Public-app credential and
  supports an optional exact country plus type/category/search/pagination
  filters for the password-gated Public `/admin`; no visitor or contact
  identity is stored.

- Source-catalog collection starts only from authenticated Admin collection or
  retry actions. The collection runner still performs its bounded in-run
  validation, automatic acceptance/exclusion, promotion and guarded aggregate refresh.
- Public reads are country-scoped by bank-owned ISO alpha-2 codes.
  `/api/public/countries` and `countries[]` in `/api/public/filters` expose only
  countries with active products in their latest completed public snapshot.
  Each country entry returns `code`, active product `count`, and
  `bank_count`, the distinct active `bank_code` count from that same
  snapshot.
- Admin login requires an enabled `country_code`. The selected country is
  persisted on `admin_auth_session`, returned by the session endpoint, and is
  the server authority for country-owned Admin reads and writes.
- Authenticated operators may switch that session authority to another active
  country through `POST /api/admin/auth/country`; the transition is
  CSRF-protected and emits `auth_country_switched`.
- Bank and source natural uniqueness is country-aware. Opaque technical IDs
  (`product_id`, `candidate_id`, `run_id`, document/version IDs) remain stable;
  `product_type_code` remains a global semantic code while country-specific
  subtype taxonomy and bank coverage carry `country_code`.
- Public product list/detail and dashboard-ranking responses may expose a single `product_url` for direct navigation to the bank's public product page; raw evidence traces, source excerpts, and source URL lists remain excluded from public responses.
- Retired manual Review endpoints create no decisions, canonical writes or refresh requests.
- Automatic promotion queues the accepted product's country,
  and the runner claims pending work by country/scope instead of assuming
  Canada.
- Source collection runs the same guarded canonical upsert path for `auto_validated` pass candidates; promoted candidates queue `auto_promotion` aggregate refresh requests, while non-product page-title false positives are rejected before they can become public canonical products.
- Exact-product discovery inspects selected detail pages for directly linked
  pricing, fee, rate, account-guide, and agreement companions. It keeps this
  relationship bounded (two per detail, 48 per scope), filters conflicting
  Product Types, and stores the parent detail URL in private discovery
  metadata. Product/document and market query keys remain part of source
  identity so query-addressed US disclosures do not collapse into one row;
  tracking, locale, and presentation keys are removed.
- `/api/admin/dashboard-health` now exposes aggregate freshness, queue state, serving fallback, stale detection, and manual retry availability for the Canada public aggregate domain.
- Public dashboard summary, ranking, and scatter responses currently derive request-time filtered results from the latest successful projection snapshot so they can share the same filter vocabulary as the product grid without requiring precomputed per-filter dashboard scopes.
- The settings loader now reads both `FPDS_ALLOWED_PUBLIC_ORIGINS` and `FPDS_ALLOWED_ADMIN_ORIGINS`, and the live CORS middleware allows the combined origin set because the same FastAPI service now fronts both public and admin browser surfaces.
- Passwords are hashed with Python's built-in `scrypt`.
- The session cookie is still `fpds_admin_session` per the shared auth contract.
- Login throttling is DB-backed with per-account lockout and recent-attempt checks.
- Public signup creates a pending `user_signup_request`; it does not create an active account until an existing `admin` approves the request and assigns a role.
- The review queue route defaults to active `queued` and `deferred` tasks and supports search, filters, pagination, and sort against the persisted prototype review-task data.
- Review detail now returns candidate fields, field-selectable trace groups, enriched evidence metadata, model execution references, current canonical continuity match, and append-only decision history for `/admin/reviews/:reviewTaskId`.
- Review detail returns the latest historical AI verification attempt with
  `can_run=false`; all product Review actions are retired with HTTP 410.
  Earlier Review AI/backfill contracts remain in historical model records and
  internal test fixtures. They are not an active collection or correction path.
  Recollect through the automatic accuracy gate to verify changed product facts.
- Collection, automatic promotion and aggregate refresh resolve the same
  versioned `(country_code, product_type)` market profile. Generated source
  metadata records the profile key/version. US Checking does not inherit the
  Canadian transaction-count requirement, US CDs use an early-withdrawal
  penalty rather than redeemability, and US Mortgage requires its qualified
  rate/APR summary. US Credit Card and Line of Credit remain explicit US-owned
  profiles even when their current minimum facts match Canada. Explicitly new
  countries remain publication-closed until their profiles are registered.
  Active-scope reads and all entry/seed/detail/supporting URL selections also
  enforce that country: explicit other-market paths/locales, subdomains, and
  country-code TLDs are rejected even on a shared official parent domain, and
  stale generated details are inactivated through guarded state changes.
  Masked financial templates and unrelated percentages, including
  transaction/conversion and ATM/ABM assessment fees, cannot satisfy a rate fact,
  country-specific Public projection omits optional Admin candidate copy, and
  comparison-critical prose is retained only within a field-specific safe bound
  that does not cut a condition mid-word or mid-clause.
  US personal/vehicle-loan representative APR summaries also preserve official
  vehicle-age/model-year, LTV, down-payment, credit, origination-fee, and
  rate-change assumptions plus relationship/autopay discount qualifications.
  US Savings requires a complete waiver when its monthly fee is positive and
  preserves new-customer, balance/timing, fallback-rate, date, and variability
  context for a conditional APY.
  US card Purchase APR labels are recognized independently of the deposit-rate
  plausibility ceiling. Public retains an exact source-language APR range and
  its creditworthiness/variable-rate qualification in
  `purchase_interest_rate_summary`. The qualified summary is the US card
  essential; a scalar is optional and cannot replace the disclosed range.
  The `100%` official-grounding and fail-closed gates are unchanged.
- Canonical continuity normalizes presentation-only product-name differences
  (trademark/punctuation and a trailing generic `account`) inside the same
  country, bank, family, and Product Type. A later approved source versions the
  existing product instead of creating a duplicate Public row; material subtype
  differences remain separate.
- New collection runs now apply that same contract automatically to bounded
  active `queued`/`deferred` detail candidates left after normal validation.
  The policy defaults to enabled, is capped at `200` candidates per run, and
  reuses only completed v2 attempts after a runner restart. Failed,
  sub-threshold, identity-unverified, hard-blocked, or ambiguous candidates
  remain in Review; eligible candidates are system-approved through the
  existing canonical and country aggregate path.
- After a rerun, an older active detail review is superseded when its
  logical name matches the new candidate or its normalized source URL has
  exactly one new active review candidate. The URL fallback permits corrected
  official naming without collapsing a genuine multi-product page.
- Run status returns filtered run list rows plus run detail payloads for `/admin/runs` and `/admin/runs/:runId`, including run alias fields, source processing summary, derived stage summary, error events, and related review tasks.
- Failed run detail now exposes retry availability for supported collection runs, and `POST /api/admin/runs/:runId/retry` requeues failed `source_catalog_collection` or `source_collection` attempts while linking the old run as `retried` and the new run as its next attempt.
- Completed collection runs with `partial_completion_flag=true` expose the same retry path, while clean completed runs remain non-retryable.
- Change history returns filtered canonical change events for `/admin/changes`, including changed-field summaries and linked review/run context.
- Generic audit and LLM usage routes were removed by `0040`; durable business chronology remains in review decisions and change events.
- Bank, product type, and source catalog management now treat the DB as the operational source of truth immediately; if those tables are empty, the admin/runtime surfaces now stay empty until an operator or explicit import/seed step repopulates them.
- Bank creation now accepts optional initial coverage product types and creates the related `source_registry_catalog_item` rows in the same admin write flow so the bank modal can start with coverage already attached.
- `POST /api/admin/banks/ai-onboard` accepts only a bounded count, derives the
  working country from the server session, requires live web search, removes
  existing identities/domains, and creates the full verified bank-plus-active-
  coverage set atomically. The model contract separates the official
  customer-facing display name from the full legal entity name and exact
  ranking-source label; observed US fixed-width report abbreviations are
  rejected as display names while legal/ranking values remain in bounded private
  model-execution context. It does not persist a standalone usage/audit ledger,
  launch collection, or publish data. Migration `0027`
  must be applied before the route is enabled against a database.
- Onboarding contract v8 performs ranking discovery first with a four-search
  ceiling, then pins one ranked candidate at a time into a separate official-
  evidence call with a four-search ceiling. The model may return zero candidates
  instead of a placeholder; the server advances to the next rank and stops as
  soon as the requested count passes the unchanged sanitizer. Evidence cannot
  replace the pinned rank/identity with another bank. The ranking schema requires
  exactly the bounded candidate limit and rejects report/table titles as bank
  labels. When the homepage root was not itself returned by search, a consulted
  URL on the exact same official hostname may serve as homepage evidence; legal,
  ranking, coverage, and relationship URLs still require exact consultation.
  Each stage retains only result-referenced consulted URLs plus the minimum
  same-host homepage evidence, preventing later candidates from being displaced
  by a global source cap. Provider request IDs, combined sources/tokens, total
  and retained per-stage source counts are recorded; insufficient results also
  retain bounded source-fulfilment counts.
- The onboarding route commits its started model execution before the bounded
  live web-search wait, retries one transient transport disconnect or provider
  gateway `502`/`503`/`504`, and treats failure-finalization writes as best
  effort. Client/provider contract errors remain single-attempt. A simultaneous
  provider and database disconnect therefore returns the existing bounded
  non-2xx response without entering the atomic bank/coverage write batch.
- Bank create and update now accept homepage URLs without an explicit scheme by normalizing them to `https://...`, while still rejecting invalid non-http(s) values with a validation error instead of a server crash.
- Bank delete now removes only the bank profile plus admin-managed coverage and generated-source rows; if collected source documents or downstream candidate/product history already exist, the API blocks deletion with a conflict response so operational history is not orphaned.
- Existing bank homepage values are no longer auto-repaired from committed seed data during runtime reads or admin writes; reset and replay flows now preserve intentionally empty operator-managed state.
- Source catalog collection treats a catalog item as `bank homepage + product
  coverage` and derives first-versus-subsequent behavior from completed
  `ingestion_run` history with a non-empty source scope. First collection is
  forced to bounded precision discovery. After completion,
  `precision_rediscovery=false` reuses the current active source scope, while
  `true` repeats precision materialization; a missing active detail forces a
  precision fallback. The API queues this work on a background runner before
  deeper worker stages continue.
- Collection launch accepts only active source-catalog items. Inactive coverage
  is excluded by the Banks client and rejected again by the API so an old or
  crafted request cannot restart deliberately disabled collection scope.
- Precision discovery reuses the verified homepage and coverage route plus
  eligible active official registry entry/detail rows. It inspects no more
  than 12 existing detail pages for newly linked sibling products and evidence
  routes, while retaining all existing hub, candidate, domain, country,
  source-language, SSRF, page-evidence, product-boundary, and companion caps.
  Run metadata records the effective mode and seed/page/candidate/result/limit
  telemetry.
- Only primary hubs actually selected for fetch are marked visited; a category
  outside that cap may still be expanded through the bounded secondary-hub
  path. Exact card routes exposed by TD-style `data-cardDescriptionUrl`
  attributes reserve bounded parser capacity and canonicalize public AEM
  aliases before scoring. A `View offer` anchor is eligible only when its URL
  satisfies the singular credit-card detail-path contract; category, campaign,
  apply, insurance/payment-protection, and other service routes remain excluded.
- An AI parallel-scorer `irrelevant` result cannot skip deterministic page
  validation for a heuristically strong candidate. A singular matching
  title/H1 with at least two pricing or product attributes and no negative
  signal may override that scorer result; plural category/family pages remain
  excluded.
- AI-created coverage preserves its verified official `coverage_source_url` on
  the catalog row and gives that route first priority during bounded discovery.
  A separate consumer-brand domain is accepted only with exact official bank-
  relationship evidence stored in `coverage_source_metadata`; the additional
  domain applies only to that bank/Product Type route. Migrations `0028` and
  `0031` are required; legacy rows with no evidence URL retain homepage fallback.
- When no eligible detail source remains, the catalog runner makes one bounded
  live-search repair. A verified route is persisted and materialized once during
  preparation. Explicit retirement evidence deactivates stale coverage and
  records `product_not_currently_offered`; uncertainty ends preparation without
  an ingestion run (D-089). Existing runs retain their recorded outcomes.
- The queued collection runner forwards that coverage route through the
  materialization boundary. Exact verified coverage pages may use a narrowly
  relaxed location-gate evidence threshold only with high AI support,
  structured product copy, title identity, and no hard product/service veto;
  ordinary homepage links retain the stricter threshold.
- D-086 stops unresolved family/coverage Review exceptions before detail-source
  materialization. Official URL ownership alone cannot justify creating a new
  ambiguous candidate. Existing `verified_coverage_review_source` and historical
  lending-equivalent candidates retain fail-closed validation/publication gates.
- `collection_preflight.py` shares read-only eligibility across catalog launch,
  queued source reuse and direct retry. Latest human defer/reject of one candidate
  on the exact country/bank/type/language/URL holds ordinary recollection. Latest
  approvals, system supersession and multiple candidates on a URL do not create
  that veto. Latest terminal 404/410, post-browser challenges and PDF/content-type
  failures hold the affected source; timeout/429/5xx remain retryable.
- Catalog launch returns additive `skipped_items` with scope/reason/revalidation.
  All held scopes return `workflow_state=skipped` and `run_ids=[]` before any run
  insertion/background launch; mixed requests queue only eligible scopes. Direct
  retry with no eligible target returns `409 collection_preflight_blocked`.
  An unchanged structural zero-detail result is held even if old catalog status
  remained active. Configuration changes or explicit `precision_rediscovery`
  permit fresh evidence checks; inactive coverage must first be explicitly restored.
- D-089 defers run insertion for all Banks/catalog launches, including first,
  precision, normal reuse and catalog retry. The response is `preparing` with
  `run_ids=[]`; group IDs reserve possible future runs. `catalog_preparation.py`
  stores only the latest bounded state under private catalog coverage metadata.
  Atomic reservations and ownership/configuration checks protect queued work.
  Pending/collecting reservations expire after two hours; terminal holds require
  explicit rediscovery or changed verified configuration. Transient checks can retry.
- Discovery/route repair precede ingestion. Before inserting a run, probe all
  selected detail and companion URLs with the worker fetch policy (direct at most
  20 seconds; browser at most 45). Exclude forbidden redirects, unresolved browser
  challenges, missing pages and invalid formats without widening domains. Require
  at least one eligible detail. Excluded companions cannot be auto-included again.
  Probe failures are bounded metadata, not failed source attempts on a new run.
- Source holds do not assert retirement or change canonical data. Preparation
  without eligible detail records `skipped` or retryable `unavailable`, with no
  ingestion run/candidate/Review. New preparation does not quarantine uncertain
  coverage. Legacy in-flight plans retain their old outcome/quarantine semantics;
  previously inactive coverage still needs governed restoration.
- Pre-run model calls retain standalone model-execution/correlation records with
  nullable run IDs. Retry preserves the old outcome until a replacement run is
  committed; the replacement then links the two attempts. Actual ingestion-stage
  errors remain failed/Partial. Source-selected compatibility APIs retain their
  shared historical eligibility checks; fresh catalog preparation is the Banks path.
- An SSRF-validated official HTML URL that returns a high-confidence HTTP-200
  JavaScript/access-challenge shell receives one bank-agnostic browser DOM
  attempt. Recovered HTML re-enters the ordinary Product-Type and evidence
  gates. A challenge that remains after rendering is a structural no-detail
  preparation hold and cannot use the seed-source fallback; browser absence, timeout, or
  render failure remains transient and does not quarantine the scope.
- A direct timeout, socket timeout, connection reset, or remote connection
  close on any SSRF-validated official HTML URL receives the same single
  bank- and Product-Type-agnostic browser DOM attempt, even when the bank is
  not preconfigured for dynamic rendering. The stored snapshot identifies
  `browser_html_fallback` and `direct_transport_failure`; PDF routes remain
  excluded, and a browser result that is still an access challenge is rejected
  before evidence storage.
- Standard collection omits an otherwise active source when its latest attempt
  ended in a persisted post-browser access challenge, or when a PDF source's
  challenge recovery produced non-PDF content. This is a reversible runtime
  exclusion rather than a registry mutation: precision rediscovery can
  revalidate and restore the route, while transient browser-runtime failures
  remain eligible for the next standard run.
- Detail-companion discovery and later standard-scope reuse reject site-wide
  user agreements plus wealth/investment disclosure documents that have no
  deposit-product context. Product-specific account, card, pricing, fee, and
  rate agreements remain eligible. This keeps non-product legal documents out
  of future runs without adding bank-specific URL exceptions.
- US discovery keeps the canonical `chequing` and `gic` codes but uses
  country-local `checking` and certificate-of-deposit/CD vocabulary. Product
  links and evidence embedded in bounded JSON-valued `data-*` component
  attributes or non-executable JSON/JSON-LD scripts are recognized, including
  server-rendered application-state pages and pages whose visible shell is a
  ZIP or county gate. Script-derived URLs still pass the normal official-domain,
  source-role, page-evidence, and product-boundary checks.
- Country-local identity vocabulary is merged with the canonical identity
  baseline instead of being limited to heuristic scoring. This lets an
  allowlisted US `auto loan` route satisfy canonical `personal-loan` identity
  without allowing attribute-only terms such as `debit card` to become a
  chequing product identity.
- HTML candidates already found unreachable during page validation are not
  reintroduced as supporting sources, and supporting paths that conflict with
  the run source language are excluded before snapshot collection. A source
  that becomes unavailable only after discovery remains an explicit isolated
  partial-source failure.
- Before precision materialization, the latest persisted attempt for each
  supporting HTML/PDF/linked-PDF source is checked. A supporting source whose
  latest attempt ended in terminal HTTP 404 is inactivated with reason
  `terminal_404_supporting_source` and excluded from the next source plan;
  primary detail failures remain visible and fail closed.
- Source catalog collect now creates `ingestion_run` rows immediately and returns a fast queued response so `/admin/banks` and compatibility source-catalog actions no longer wait on homepage discovery or candidate-page validation before responding.
- Precision collection preserves the existing active detail scope when no
  replacement detail rows are found. Standard collection deliberately reuses
  that scope without discovery, and the queued runner forces precision
  fallback if the supposedly reusable scope has no active detail.
- After promotion and Review AI, an in-run review candidate is automatically
  superseded when an exact same bank/family/type/subtype/name candidate in that
  run is already approved, preventing a second operator decision for the same
  product.
- Bank-wide source-catalog collect now launches one background runner process for the selected collection plan and lets that runner process bank/product groups sequentially. This keeps bulk collection inside the dev DB session-pool budget while the per-stage watchdog still closes a hung worker stage as `failed` instead of leaving it indefinitely `started`.
- A transient database failure while recording one group's downstream result is
  contained to that group: failure persistence is best-effort and cannot crash
  the bank-wide runner before later groups execute. The affected run remains
  fail-closed and can be retried or audited once the database is reachable.
- Downstream worker stages launched by `source_collection_runner` now have a configurable `FPDS_SOURCE_COLLECTION_STAGE_TIMEOUT_SECONDS` watchdog. If a worker stage hangs past that limit, the run is closed as `failed` with a timeout summary instead of remaining indefinitely `started`. A process that has already emitted a complete JSON result with `persistence.run_state=completed` is recovered after the watchdog terminates it; partial, malformed, or nonterminal output still fails closed.
- Non-zero exits and unrecoverable timeouts retain the exact `failed_stage`,
  failure kind, return code or timeout, and a bounded worker diagnostic in run
  metadata. Credential-bearing URLs and common secret assignments are redacted
  from both runner output and persisted diagnostics, so Runs can expose the
  actionable DB or worker error without relying on a transient console log.
- Fetching uses format-aware browser fallback for domains listed in `FPDS_SOURCE_BROWSER_FALLBACK_DOMAINS`. Blocked or timed-out HTML-only homepage/detail discovery receives browser-rendered DOM; snapshot capture normally receives a browser-rendered PDF, while `FPDS_SOURCE_BROWSER_DOM_SNAPSHOT_DOMAINS` retains HTML for sites such as Vancity whose exact product conditions are encoded in structured CMS payloads. Dynamic rate shells and unresolved customer-visible rate placeholders use the same bounded path. Current defaults include BMO, CIBC, RBC, Simplii, Tangerine, and Vancity plus the configured US banks. Every attempt remains on the exact validated official URL and per-bank allowlist; HTML-only callers still reject PDF payloads, and a usable direct snapshot remains the fail-soft result if optional rendering fails.
- Homepage, coverage-quote, and existing-detail companion discovery load browser settings from the selected environment while replacing the general fetch allowlist with the exact current bank domains. This preserves the Admin collection boundary instead of widening a single-bank collection to all configured source domains.
- Product-supporting source discovery excludes annual/climate disclosure reports. These corporate reports are not exact-product pricing or terms evidence and cannot create recurring partial runs when an old report URL is retired.
- Vancity's seven active Product Type catalog rows are pinned by migration `0041` to their audited official family hubs. The committed Vancity registries seed exact product-detail routes plus the separate account, GIC, mortgage, and consumer-lending rate pages; strongly verified Vancity GIC seed details ignore only the false family signal created by their cross-sell footer, while genuine multi-option pages such as LOC stay boundary-marked until evidence-grounded variant expansion. Case-only generated aliases are retired after the canonical route is revalidated.
- Bridgewater, EQ Bank, and Fairstone no longer inherit all seven Product Types
  merely because migration `0020` registered the bank. Migration `0042`
  pins ten directly collectable official routes and makes eleven known
  zero-detail or misclassified scopes inactive, including EQ's prepaid Card
  under Credit Card and Fairstone group-only products without an attributable
  consumer detail route. Existing source/run history remains available, while
  inactive catalog rows and older sources cannot launch collection. EQ's
  exact `Personal Account` name is recognized as a bank-specific chequing
  discovery alias without changing the global chequing identity boundary.
- Homepage-first discovery now uses bounded hybrid scoring over the candidate set instead of AI-only fallback after heuristic failure: deterministic candidate generation still happens first, but the API layer now runs AI parallel candidate scoring when configured, uses stronger product-type-description terms in heuristic scoring, validates tentative detail pages with page-level evidence scoring, and persists generated-source `discovery_metadata` for explainability.
- Homepage scoring keeps the first `h1` as the primary product identity and stores later headings separately. Generic pages with multiple product variants carry `multi_product_family_overview`, refinance/renewal advice or servicing flows cannot become product details, and lending support links under unrelated account paths are dropped before evidence merging.
- Page scoring uses the normalized official URL path as bounded identity
  evidence and applies login/comparison/legal negatives only when they are
  prominent in that route, title, or primary heading. Shared navigation and
  serialized application state therefore cannot erase otherwise coherent
  structured product/pricing evidence. A high-confidence official product
  title plus structured application payload may recover an unrendered body,
  subject to the existing hard scope vetoes.
- Link exclusions are URL- and CTA-aware: action, login, application, comparison, and promotion flows remain excluded, while ordinary product-card prose such as “mortgage offers stable payments” is not rejected by an `offer` substring.
- Explicit `application`, `prequalification`, account-opening, and internal `shadow-site` paths are excluded from both detail and supporting source plans so stale/operator flows do not create recurring partial runs.
- Seeded supporting hints pass through the same current scope filter as homepage-discovered links; calculators, servicing/help pages, onboarding/join flows, forms repositories, editorial/tips pages, stale action flows, and wrong-product support cannot remain active merely because an older committed registry listed them.
- Seed detail hints may preserve a useful source ID, priority, or extra field request, but they cannot narrow the active Product Type field contract. Generated detail rows use the union of hint fields and the current Product Type baseline so older seeds cannot silently omit fee waivers, minimum balances, rates, or other reviewer-facing decision fields.
- A singular named-product heading/title with explicit attributes may survive plural SEO or related-product headings at the normal confirmed-detail threshold. A plural `Personal Loans` product remains singular when its sections describe uses such as consolidation or home improvement; two distinct subtype sections such as Auto Loan and Student Loan still establish a family boundary. Generic plural/category headings remain family overviews and cannot produce lending candidates.
- The bank list payload now includes its attached coverage items so `/admin/banks` can drive multi-bank bulk collect without reopening each bank detail modal first.
- Homepage-first source generation can still use committed fallback discovery hints from the repo baselines when link extraction comes up empty, but those hints no longer write rows back into the live DB automatically.
- Source collection plans now carry generated-source discovery metadata into the worker registry payload so the runtime `source_document.source_metadata` stays aligned with the source registry explanation fields.
- Source collection plans also carry the canonicalized official-domain
  allowlist and each normalized source URL into extraction. When OpenAI is
  configured, every candidate-producing detail source—not only a dynamic
  Product Type—runs a required official-domain web grounding pass over the
  complete active field contract. A returned value is retained only when its
  cited URL was actually consulted and its exact quote is present in the fresh
  evidence chunk; otherwise the existing evidence-first value or reviewable
  omission remains. A co-located labeled currency fee from an identity-matched,
  high-confidence official detail snapshot may use the narrower deterministic
  exact-origin contract. Qualified lending rate summaries and their
  amount/limit/term/rate-type companions may use the same path only when their
  value and qualifying context are co-located; scalar rates and general prose
  remain provider-grounded or omitted.
  The bounded model result and consulted sources are persisted with the
  extraction execution; standalone token/cost usage is discarded, and AI
  failure does not bypass validation or review.
- The background source-collection runner now launches worker stages through the repo-root `uv` project environment instead of the API service virtualenv, so worker-only dependencies such as `beautifulsoup4` and `pypdf` resolve correctly during collection.
- Discovery, registry refresh, and snapshot capture now merge the active registry's `allowed_domains` into the env allowlist, which keeps bank-scoped safe fetch behavior aligned with the selected source registry during Big 5 collection.
- Snapshot capture now runs source fetches concurrently inside the same run, and the shared fetch timeout baseline moved to `90` seconds to better tolerate slower Big 5 pages without stretching bank-wide collection wall-clock time linearly per source.
- Downstream collection stages now stop when snapshot capture produces no usable sources, and they only process the subset of sources whose snapshots were actually stored or reused so the final run error reflects the real failing stage more accurately.
- Every persisted worker stage now writes the required single-country
  `ingestion_run.country_code`; mixed-country or invalid run scopes fail before
  persistence instead of relying on a database constraint failure.
- `POST /api/admin/sources` and `PATCH /api/admin/sources/:sourceId` are intentionally kept as read-only error responses in the MVP so the live operator flow stays centered on `/api/admin/banks` and `/api/admin/source-catalog`.
- Dynamic product-type onboarding is live for the admin registry and collection pipeline: `/api/admin/product-types` supports list/create/detail/update/delete for operator-defined types, delete is blocked when bank coverage or generated sources still reference the type, bank coverage writes validate against the registry, source collection plans carry product-type definitions into worker stages, and non-canonical types use generic AI extraction/normalization plus official-grounding eligibility. Insufficiently grounded candidates remain safely review-routed.
- Candidate-producing scope is restricted to `detail` sources. Generated `supporting_html`, `supporting_pdf`, and linked-document sources may be fetched, parsed, and merged as evidence, but cannot define standalone products. Product-matched generic supporting rate pages can fill missing or invalid savings/GIC rate fields.
- Named product detail recovery now requires title/heading identity strong enough to survive plural navigation noise, while generic marketing/action pages remain excluded. Deposit support discovery also drops mutual-fund, prospectus, fund-facts, and governance/reporting links before they can contaminate savings or GIC rate evidence.
- Snapshot reuse is source-document scoped even when checksums match, so identical WAF/error responses from different URLs retain separate failure lineage. Repeated snapshots of a shared URL preserve its established `detail` metadata when a later collection scope sees that URL only as supporting evidence.
- Review edit-approve applies the executable field contract to manual values: booleans and list fields retain their JSON types, numeric fields reject negative or implausible values, and fee/rate overrides cannot bypass the same safety boundary used by automated normalization.
- Auto-promotion independently rejects discovery-marked non-product service/editorial sources and queues both deterministic multi-product boundaries and AI-identified family hubs for review even if an older validator labeled them pass. The collection review autopilot excludes the same hubs. Review diagnosis recommends `defer` for an unsplit family page rather than asking an operator to approve a composite product.
- No-detail Partial summaries prefer the bounded rejection aggregate and the
  decisive rejected product URL over an incidental earlier hub fetch error, so
  Runs exposes the actual promotion failure on the next attempt.
- Mixed family-route segments are token-aware: paths such as
  `/savings-cds/...` remain eligible Savings detail routes while CD detection
  remains available for the GIC scope. This prevents a valid same-scope detail
  from being mislabeled as another Product Type.
- A deterministic non-HTML content-type mismatch, including an irrelevant PDF
  discovered where HTML detail evidence was required, is structural no-detail
  evidence rather than a transient fetch outage. Actual timeouts, HTTP
  408/425/429, and HTTP 5xx responses remain transient. The generic zero-detail
  circuit breaker can therefore quarantine the conclusive empty scope and
  prevent a repeated Partial without suppressing a recoverable network failure.
- Review detail reads do not persist view events. Field evidence links and the current evidence excerpt remain available for operator review without creating read-amplification logs.
- Approve and edit-approve now perform the first runtime canonical upsert/change-event side effects using a conservative prototype continuity match of country, bank, product family, product type, subtype, and product name.
- Review write routes now require the stored session plus matching `X-CSRF-Token` header.
- Later admin write routes can keep reusing the same session and CSRF token model.
- The settings loader now resolves a relative `FPDS_ENV_FILE` from either the current working directory or the repo root, so `.env.dev` works both from the workspace root and from inside `api/service`.
- `api/service/tests/test_ops_scenario_qa.py` gives the service layer a Gate C-focused operator scenario test that verifies review decision side effects, durable change-history linkage, and run-detail drilldown context together.

## Admin Handover Corrections (2026-09-06)

- POST /api/admin/auth/logout validates CSRF before revoking an active session.
  Missing/expired sessions remain idempotent and clear stale browser cookies.
- GET /api/admin/auth/session includes the API's environment value, so a
  production-mode web build connected to dev is not labeled Production.
- The run-list summary adds attention_items: the count of failed or partial
  runs, without counting a failed partial run twice.
- Focused regression tests cover logout rejection/success/idempotency, the
  environment contract, and execution of the attention aggregate against mixed
  country/state test data.


## Public rate interpretation (2026-09-16)

`api_service/public_rates.py` is the shared read-time interpretation for product
list/detail, sorting, dashboard metrics/rankings/scatter. The additive `rate`
object distinguishes absolute/range/reference/conditional/promotional/unknown.
Only an absolute full rate supplies numeric comparison values. Legacy
`public_display_rate` and `card_display_rate` responses are safe aliases of that
value; stored data and source summaries remain intact. The interpreter never
loads a prime rate or combines a benchmark and margin. Run the Public rate and
product regression tests together. The separately reviewed, rollback-by-default
single-record correction is documented in
[the rate correction audit](../../docs/00-governance/public-rate-correction-2026-09-16.md).

## Public verification freshness (2026-09-21)

Snapshot generation and product verification are separate. Public product rows
carry read-time verification state/deadlines; snapshot success is neutral and
never substitutes for a missing product check. Catalog, comparison, Home/finder
results and detail share the EN/KO/JA product status. Existing comparisons and
product availability stay intact. Legacy clients retain fresh/stale/unavailable,
with fresh restricted to known checks within their policy window.

See [the freshness policy and operator report](../../docs/03-design/public-verification-freshness-policy.md)
for contract details, the read-only overdue CLI, manual daily/weekly review and
release order. Initial warning-only intervals are 7/30 days for rate-led products and 30/90 days for chequing/cards. D-069 collection
is manual; these changes do not start collection, update facts or publish data.


## Deposit comparison conditions (2026-09-24)

The [deposit comparison policy](../../docs/03-design/public-deposit-comparison-policy.md) supersedes headline-only Savings/GIC
comparison and implicit one-year calculation. Home scopes rankings by type,
currency, rate basis and exact GIC term/redemption category. The finder uses
those gates before its existing metric; the calculator uses disclosed annual
basis and an explicit period, or a concise unavailable reason and official link.
`deposit_terms` is additive. Public reads a bounded whitelist from the exact
approved version pinned by the snapshot; aggregates preserve these qualifiers
for future refreshes. Missing basis is never inferred from country. API release
precedes Public; old cached contracts fail closed. No live refresh or migration
is needed for the version-pinned bridge. See the policy for current data limits.


## Public-aligned comparison collection (2026-09-29)

Market profile v5 retains the existing approval essentials and adds bounded
comparison qualifiers from the same evidence pass: annual/APY basis, calculation,
payment/compounding, promotions/tiers, opening minimums, fee waivers, redemption
and explicit security flags. Supplemental gaps never add approval requirements
or extra Review AI fields. Collection marks them opportunistic in the existing
single grounding call; no extra search/retry is requested for their absence.
Exact quoted prose must support the basis and rate conditions. Discount/reduction
and capped savings bonuses cannot supply full rates; CD rate-guarantee/funding,
grace and penalty days cannot supply maturity. US projections retain these
approved financial qualifiers while continuing to omit private evidence/copy.

See the [bounded CA/US audit and correction report](../../docs/00-governance/public-collection-alignment-2026-09-29.md) for six applied
existing-product repairs, preserved verification dates, remaining gaps and the
read-only `scripts/maintenance/public_collection_gap_report.py` command.

## Approved collection policy update - 2026-10-01

Shared worker/API profiles now apply country currency defaults only when undisclosed and require the reduced core comparison fields documented in the collection policy. `/healthz` returns `collection_accuracy_version` and `market_profile_version` in addition to status. Deploy this API before publishing newly validated receipts; existing strict-policy receipts remain valid. Local verification does not establish deployment. The one-off recovery is complete: deployed health versions matched, 17 fresh candidates passed normal normalization and automatic validation, and all were published without human review or model calls. Actual API/BFF and Public readback confirm CA 17 / US 7 (24 total).

## Conditional transaction, withdrawal and security requirements - 2026-10-01

The shared market profile v7 restores checking transaction costs, GIC/CD early-access rules and consequences, and line-of-credit security. Unlimited checking needs no excess fee; explicitly blocked early withdrawal needs no penalty value; explicit unsecured status is valid. Collection prompts expose grouped alternatives and conditions. Automatic acceptance/exclusion remains the only product workflow; no new Admin action or review queue is added.

The Public API rechecks affected snapshot-pinned versions under the current contract, including older receipts, and exposes numeric `transaction_fee`/`additional_transaction_fee`. Country counts use the same eligible products. Shared Public metrics show checking transaction costs and both GIC access and consequences in all supported locales. Deploy API/worker before Public; previous cached responses can remain until normal expiry. Read-only current-data assessment: 5 eligible of 24 active products, 19 needing evidence. No live mutations, paid collection or deployment were performed in this implementation slice.
