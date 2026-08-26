# FPDS Workspace

This repository is the implementation and operating workspace for `FPDS`
(Finance Product Data Service), an evidence-grounded financial product data
platform with separate authenticated Admin and anonymous Public experiences.

The repository is currently `product-implementation-in-progress`.

As of `2026-08-15`:
- `Gate A` passed on `2026-04-06`
- `Gate B` passed on `2026-04-11`
- `Gate C` passed on `2026-04-13`
- `WBS 2` foundation scaffolds and baseline artifacts are complete
- `WBS 3.1` source discovery is complete
- `WBS 3.2` snapshot capture and persistence are complete
- `WBS 3.3` parsing/chunking is complete with live dev verification and parsed-document reuse verification
- `WBS 3.4` evidence retrieval is complete with metadata-only live verification and vector-assisted fallback behavior verification
- `WBS 3.5` extraction flow is complete with extracted-draft artifacts, evidence-linked official-domain AI grounding for detail products when OpenAI is configured, zero-token heuristic fallback, bounded `model_execution` persistence, and unit verification
- `WBS 3.6` normalization mapping is complete with `normalized_candidate`, `field_evidence_link`, and live dev verification
- `WBS 3.7` validation/confidence routing is complete with candidate revalidation, `review_task` creation, and live dev verification
- `WBS 3.8` internal result viewer is complete as a static prototype viewer plus live-exportable viewer payload
- `WBS 3.9` first end-to-end run is complete with a committed evidence pack and live viewer export for the three TD savings target products
- `WBS 3.10` prototype findings memo is complete, and its original Gate B `Deferred` recommendation has now been overtaken by three post-memo hardening slices plus an approved Gate B review note
- a first post-`3.10` hardening slice is complete: normalization now supplements missing TD savings rate fields from the `TD-SAV-005` current-rates source, and a live hardening run moved all three target candidates from `validation_error` to `validation_status=pass`
- a second post-`3.10` hardening slice is complete: normalization now selectively reuses `TD-SAV-008` governing-PDF interest rules, has an opportunistic `TD-SAV-007` fee-waiver merge hook, splits `TD Growth` boosted-rate qualification into cleaner canonical fields, and suppresses several noisy long-text fields before candidate persistence
- a third post-`3.10` hardening slice is complete: `TD-SAV-007` fee-governing evidence is now used in a live target-safe way to suppress noisy `fee_waiver_condition` fields for zero-monthly-fee TD savings products instead of persisting misleading waiver text
- `WBS 4.1` admin auth is now complete with a DB-backed operator account table, DB-backed session table, FastAPI auth routes, a bootstrap-admin CLI, approval-gated signup requests, and a protected Next.js admin entry shell
- `WBS 4.2` review queue is now complete with a session-protected review-task list API, a protected `/admin/reviews` queue route, active-state defaults, search, filters, sorting, and stable drill-in links
- `WBS 4.3` review decision flow is now complete with review-task detail read APIs, approve/reject/defer/edit-approve mutations, canonical product/version side effects, durable review/change history, and a live `/admin/reviews/:reviewTaskId` decision surface with override diff preview
- `WBS 4.4` evidence trace viewer is now complete with field-selectable trace drilldown, enriched evidence metadata, parsed mapping context, and model-run references on the live `/admin/reviews/:reviewTaskId` route
- Review Queue collection hardening now prevents AI-classified support/service/rates pages from being promoted through page-evidence overrides without a real product-identity signal, deactivates explicitly rejected non-seed generated detail rows on rediscovery, and gives reviewers registry-backed bank filters plus generic field/evidence/discovery context; an Alterna chequing live rerun completed with two valid candidates and zero new review tasks
- Runs/Review Queue hardening now restricts standalone candidates to `detail` sources, preserves supporting rate evidence without publishing it as a product, rejects retail-scope business pages, reparses snapshots by parser version, safely retries completed-partial runs, and shows source role, missing expected fields, and a recommended reviewer action in the Queue. Alterna live verification auto-approved Savings at `1.05%` and eTerm GIC rates at `2.65%/2.85%/3.10%` with zero new review tasks.
- Multi-bank collection/review hardening now treats `www` and apex redirects as the same bounded bank host, recovers confirmed product details from navigation-wide negative terms, collapses same-product locale/host aliases and byte-identical snapshots only within the same logical source document, preserves end-to-end source failures in final Runs summaries, suppresses navigation/marketing copy from candidate fields, and gives Queue/detail one problem-first diagnosis with a Public-detail-style candidate product summary, inline field correction, and evidence.
- Cross-product collection QA now keeps dynamic candidates inside their registered field contract, rejects cashback/prepayment/equity or unresolved-template numbers as rates, removes wrong-type booleans, duplicated page copy, footer navigation, and term conflicts, and records bounded candidate-score plus rejection summaries in Runs. Official single-product homepages may be detail candidates, while high-confidence deposit family overviews can feed review-first collection without widening retail scope to business, editorial, or service-flow pages. Review Detail opens only flagged fields by default, keeps other collected values collapsed, and puts optional decision notes behind disclosure.
- Collection accuracy hardening now treats generic multi-product family pages as an explicit product-boundary error, blocks them from canonical auto-promotion, pairs both term-first and rate-first schedules without row shifts, canonicalizes bounded `www`/apex redirects, and rejects advice/service pages plus unrelated account supporting paths. Product-card copy containing words such as `offers` no longer hides legitimate detail links; exact action/promo flows remain excluded.
- Current-evidence hardening now removes explicitly expired promotional rates before current official supporting-rate merge, isolates normalization artifacts to the active run, rejects commercial pages from retail collection, treats plural multi-variant lending pages as evidence-only, excludes adjacent-product fields by evidence anchor, parses current GIC tables whose percentage unit is declared only in the column header, preserves range terms without inventing a single duration, and includes the PDF crypto runtime needed for encrypted official documents.
- Official-field accuracy hardening now rejects adjacent-product CTAs and slogans from lending eligibility/security/application fields, keeps promotional end dates out of product effective dates, requires exact evidence for scalar terms and fee/payment fields, restricts dynamic AI extraction to product-detail pages, and propagates a single official GIC minimum across every reconstructed rate row. Fresh National, CIBC, and Oaken Admin collections verified the reusable rules; unsafe historical CIBC term values and exact duplicate BMO/Bridgewater products were retracted through controlled DB workflows and reflected in the latest Public aggregate snapshot.
- Current cross-bank accuracy hardening requires exact percentage evidence, separates regular rates from time/eligibility-limited promotional totals and ongoing bonuses, preserves foreign-product currency, requires direct and cross-field-consistent monthly fees, and prevents adjacent product, family-page, investment-fund, FX, index-return, calculator, or WAF content from becoming public product facts. Snapshot metadata preserves established detail ownership across shared supporting fetches, manual review overrides use the executable type/range contract, and the collection watchdog can recover only a fully persisted terminal result emitted before timeout. Confirmed unsafe historical/live candidates are retracted through controlled remediation before corrected recollection.
- Latest decision-field hardening maps flattened horizontal comparison tables back to the target product column, separates a positive recurring fee from its balance-qualified `$0` outcome, preserves material savings balance tiers and transaction fees, ranks explicit multi-step qualification evidence over marketing summaries, and carries exact account-wide unlimited-transaction facts from official supporting sources. Cross-sell audience offers, account-switching services, incomplete fragments, award copy, and repeated application CTAs are removed from customer-facing fields without inventing missing values.
- Public now has separate Deposit, Credit Card, and Loan catalog routes. Credit Card exposes review-approved annual-fee and purchase-rate facts; Loan accepts review-approved `mortgage`, `personal-loan`, and `line-of-credit` canonical products through the same aggregate snapshot and public-only data boundary. Candidates that still require review remain non-public.
- Admin-to-Public automation now runs from one database-elected API scheduler leader: active CA/US bank/Product Type coverage is recollected weekly in bounded batches, failed or partial coverage retries after 24 hours, abandoned runs are closed after 12 hours, pre-policy candidates are reconciled through the current official-evidence AI contract, and pending aggregate refreshes are restarted without operator action. Migration `0035` controls the live policy and an environment switch remains available as a runtime kill switch.
- Public country readiness is now implemented end to end: bank-owned ISO alpha-2 country codes flow through canonical approval and country-specific aggregate refresh into Public APIs and URL state. The header selects among countries with active latest snapshots, the footer owns EN/KO/JA language selection, and current governed collection scope includes Canada and the United States; each later country remains fail-closed until its own product profiles and fixtures are registered.
- Admin is now country-scoped from sign-in: operators select an enabled country before authentication, the server stores it in the session, the shell keeps the working country visible, and bank/source/collection/run/review/change operations are constrained to that country. Stable product/candidate/run IDs remain opaque; country is enforced through business keys, foreign keys, and lookup indexes.
- Admin administrators can now manage that login allowlist from `/admin/countries`: countries are selected from a prepared ISO catalog, and reversible deactivation preserves historical data while protecting the current and final active country.
- The authenticated Admin header switches the current server-side session among active countries with confirmation and CSRF protection, then returns to Overview in the same language to prevent country-owned screen context from leaking across markets.
- AI-assisted bank registry onboarding is implemented for Banks: an
  administrator selects `1` to `10`, the server researches the largest missing
  banks for the session country with current web evidence, and the full
  official-homepage/logo/active-coverage set is created atomically with
  bounded private model context. Customer-facing display names are kept separate from
  legal entity names and exact ranking-source labels so fixed-width regulatory
  abbreviations cannot become UI bank names. Migration `0027` is applied to
  shared dev.
- US Admin product collection is hardened end to end: every worker stage
  persists one validated run country, AI coverage evidence is retained as the
  first bounded discovery route, US checking/CD vocabulary and structured
  location-gated pages are supported, unreachable supporting HTML is removed
  before collection, US candidates default to USD, and legal/CTA/calculator
  headings cannot become product names. Migration `0028` and five verified Bank
  of America coverage URLs are applied in shared dev; a normal five-type run
  completed `30/30` sources with no partial run.
- Dynamic homepage discovery now reads bounded, non-executable JSON and
  JSON-LD application-state payloads as well as anchors and `data-*` component
  JSON. This recovers official product routes from server-rendered shells while
  preserving the existing domain, page-evidence, product-boundary, review, and
  publication gates.
- US price discovery also follows a bounded set of pricing, fee, rate-table,
  account-guide, and agreement links from an already selected exact-product
  detail. Offer/document/location query keys remain part of source identity,
  dynamic pricing pages receive browser fallback, structured payloads retain
  APY/APR/fee keys, and Public cards preserve qualified Purchase APR ranges
  rather than displaying only a numeric lower bound.
- Page evidence now treats an official product URL as bounded identity evidence,
  ignores shared navigation `Sign in`/`Compare`/legal copy as a page-level
  negative, and merges country-local identity vocabulary such as US `auto
  loan`. Plural product names with several use cases remain one product, while
  genuinely distinct family variants and AI-identified family hubs stay
  review-bound.
- `WBS 4.5` run status is complete with session-protected run list/detail APIs, protected `/admin/runs` and `/admin/runs/:runId` routes, run-level error summary, source processing summary, related review-task links, and bounded model-stage status
- `WBS 4.6` change history is complete with a session-protected change-history API, a protected `/admin/changes` route, canonical event chronology, changed-field summaries, and review/run drilldowns
- historical `WBS 4.7`-`4.9` audit/usage deliveries are superseded by `WBS 5.27`: `/admin/audit`, `/admin/usage`, and their APIs are removed, and no standalone audit or token/cost ledger is retained
- `WBS 4.10` operational scenario QA is complete with automated review-to-history verification across review decision, change history, and run detail linkage
- `WBS 4.11` Review Detail AI verification is now complete: authorized reviewers can force a live search of registered official bank domains, compare official facts with the collected candidate, inspect cited match/mismatch/unverified results, and selectively stage contract-safe corrections without auto-approving or publishing
- Admin collection applies official-domain live-search discipline to a bounded
  product-type contract: identity plus only the facts customers need to compare
  that Deposit or Loan type. An AI value is accepted only with an allowlisted
  consulted URL and exact quote from fresh evidence; optional marketing and
  operational copy is not requested by default.
- Existing active Review Queue candidates can be batch-verified against official
  bank domains. Contract-safe mismatches update only the candidate, and system
  approval requires verified identity plus `100%` of the smaller essential-field
  set through the normal canonical/change-history/aggregate path.
- New collections use that AI judgment automatically: officially grounded
  dynamic/lending candidates can enter normal auto-promotion, and a bounded
  post-validation autopilot verifies and safely corrects remaining detail
  reviews before approving complete essential-field passes. Missing,
  contradictory, invalid, or ambiguous essential facts stay in Review; a
  partial-source or legacy confidence warning alone is non-blocking when the
  essentials pass. An exact match
  between the candidate identity and the persisted official detail-page H1 may
  satisfy identity when web search leaves it unverified, but never when AI
  reports a mismatch or the page crosses product boundaries. A rerun also
  supersedes an older same-URL task when the new URL has exactly one review
  candidate, so corrected punctuation or naming does not duplicate the Queue.
- Collection/publication essentials are now resolved by one versioned
  `(country_code, product_type)` market profile. Canada keeps its existing
  comparison contract; all governed US types have explicit US ownership, with
  Checking, Savings, CDs, Mortgage, and Personal Loan using distinct US
  decision semantics. The resolved profile drives discovery fields,
  validation, AI repair, manual approval, aggregate eligibility, and Public
  labels while retaining `100%` official grounding and fail-closed publication.
  Country overrides expose only essential facts to Public; masked rate
  templates and unrelated percentages cannot satisfy publication quality.
- `WBS 5.1` Big 5 source registry is now complete with a committed Canada Big 5 registry catalog and per-bank `chequing`, `savings`, and `gic` source baselines
- `WBS 5.2` chequing parser expansion is now complete with catalog-backed source-id resolution across the Big 5 registries, chequing-specific extraction fields, schema-aligned chequing subtype normalization, and unit verification
- `WBS 5.3` savings parser expansion is now complete with savings-specific retrieval hints, extraction coverage for tiering or withdrawal or registered fields, and unit verification
- `WBS 5.4` GIC or term parser expansion is now complete with GIC-specific extraction fields, normalization-time term and cross-field validation alignment, and unit verification
- `WBS 5.5` cross-bank normalization hardening is now complete with an executable type/unit contract, reviewer-visible field notes, evidence-scoped official supporting-source merge, general percentage and navigation false-positive guards, fixture-only Golden profiles, and representative Admin-path recollection verification
- `WBS 5.6` aggregate dataset generation is complete with persisted aggregate refresh runs plus `public_product_projection`; dashboard summary, ranking, and scatter are derived from the latest successful projection
- `WBS 5.7` public products API is now complete with anonymous `/api/public/products` and `/api/public/filters` routes backed by the latest successful aggregate projection snapshot, shared filter vocabulary, sort options, pagination, localized labels, and freshness metadata
- `WBS 5.8` dashboard APIs are now complete with anonymous `/api/public/dashboard-summary`, `/api/public/dashboard-rankings`, and `/api/public/dashboard-scatter` routes that reuse the latest successful aggregate projection snapshot for request-time filtered summary, ranking, and scatter responses plus methodology and freshness context
- `WBS 5.9` Product Grid UI is now complete with a live Next.js public package, a `/products` catalog route, public filters, result-summary chips, product-type-aware cards, and pagination
- `WBS 5.10` Insight Dashboard UI is now complete with a dashboard-first canonical `/` Home route (plus a legacy `/dashboard` redirect), a live verified-record ledger, real snapshot coverage and freshness, deposit ranking, bank composition, an accessible like-for-like scatter when supported, and query-preserved navigation back to `/products`
- `WBS 5.11` grid/dashboard cross-filter is now complete with URL-based shared-scope sibling navigation plus dashboard drill-in links back into the Product Grid from breakdowns, rankings, and scatter points
- `WBS 5.12` locale rollout is complete with pre-hydration EN/KO/JA document language, query-preserved navigation, localized operator UI across the Admin shell, Review, Runs, registries, chronology, Health, Login, and Signup, plus source-language preservation for evidence and operator-entered values
- `WBS 5.13` freshness/metric note wording is now complete with locale-aware public methodology/freshness coverage on `/methodology`, concise dashboard data notes on the canonical `/` Home, and clarified snapshot/metric/exclusion messaging for the public surface
- `WBS 5.14` responsive QA is now complete with the verified-record Public design across Home, Deposit, Loan, selection-led comparison, Deposit and Loan detail, and Methodology; production-rendered `1440px`, `768px`, and exact `390px` EN/KO/JA checks confirm no horizontal document overflow
- `WBS 5.15` source registry admin MVP is now complete with DB-backed bank and source-catalog management, source-detail generation during collection, a bank-centered `/admin/banks` workflow for bank setup plus initial coverage and bulk collection, compatibility redirects for `/admin/source-catalog`, and read-only `/admin/sources` operator routes
- `WBS 5.25` continuous collection-to-Public automation is complete with scheduled CA/US catalog collection, bounded failure recovery and Review reconciliation, aggregate restart, scheduler identity metadata, and a first-class Public credit-card catalog
- `WBS 5.27` bounded operational storage is complete: standalone audit/usage storage, evidence embeddings, and redundant dashboard snapshot tables are removed; linked/latest/active evidence and bounded operational metadata are retained; shared dev was compacted without changing the latest Public projection
- `WBS 5.28` numeric Public catalog card rates are complete: cards derive a customer-favorable explicit lending rate from the current approved projection, rate sorting uses the same value, and full source-language qualifications remain on comparison/detail without recollection
- `WBS 5.33` Bankoom Public experience refinement is complete: the larger centered-eye brand, calmer Home and catalog hierarchy, EN/KO/JA wrap rules, shared comparison/detail presentation formatting, bounded server read caching, and production-rendered responsive QA now form the current Public baseline
- `WBS 5.34` Vancity collection recovery is complete: browser-rendered DOM now recovers allowlisted HTML discovery from direct `429` responses, AI stages recognize migration `0040` compatibility views, non-product climate reports are excluded, and all seven Vancity scopes were recollected with `36/36` sources successful
- the live admin runtime now uses a compact evidence-operations design: a deep operational frame and real-data Attention Rail lead into problem-first Review, failure-first Runs, registry workflows, sticky decisions, chronology, cost/anomaly observability, and Public-snapshot health; safe visible auto-refresh, route recovery, accessible dialogs/tables, semantic state tokens, anonymous Login/Signup, and desktop/mobile route navigation share one B2B interaction baseline
- the client-handoff simplification now exposes Overview, Review, Runs, and Banks as direct daily work on desktop and mobile, keeps secondary tools in one labeled sidebar group, progressively discloses advanced filters and technical Review context, and removes stale scaffolds, generated artifacts, unreachable UI modules, and numbered handoff-facing vendor filenames without changing live routes or API contracts

## What This Repo Contains Today

- requirements, scope, planning, governance, and design documents
- foundation baselines for env, DB, storage, auth, i18n, security, observability, and route manifests
- shared design-system and vendor-provenance guidance for the live Public and Admin packages
- a Python worker project under `worker/` with discovery and pipeline stages
- working prototype ingestion code for discovery, preflight drift checks, scheduled registry refresh artifacts, snapshot capture, parse/chunk, and evidence retrieval stages
- metadata-only evidence retrieval over the bounded `evidence_chunk` set
- working extraction code that turns retrieval matches into sparse extracted drafts and, when configured, cross-checks detail products through official-domain live search before retaining evidence-linked field drafts
- working prototype normalization code that maps extracted drafts into canonical candidate rows and candidate-level evidence links
- working prototype validation/routing code that recomputes candidate validation, updates candidate state, and creates prototype review tasks
- working prototype result-viewer export code and a static prototype viewer shell for read-only inspection
- a first live `FastAPI` admin service package under `api/service/` for DB-backed admin auth, session handling, and approval-gated signup requests
- a first live `Next.js` admin package under `app/admin/` with `/admin/login`, `/admin/signup`, protected `/admin`, and session-aware route gating
- an admin-only `/admin/countries` surface backed by a prepared ISO country catalog and protected country-registry activation/deactivation APIs
- a first live `Next.js` public package under `app/public/` with dashboard-first canonical `/` Home, a legacy `/dashboard` redirect, `/products` for Deposit, `/cards` for approved credit cards, `/loans` for approved retail lending, `/products/[productId]` for public product detail, and `/methodology` for public metric/data-boundary notes
- a live review-queue, decision, trace, and AI-verification runtime slice with `GET /api/admin/review-tasks`, `GET /api/admin/review-tasks/:reviewTaskId`, `POST /api/admin/review-tasks/:reviewTaskId/ai-verify`, protected `/admin/reviews`, and a protected `/admin/reviews/:reviewTaskId` decision-plus-trace surface
- a live run-status runtime slice with `GET /api/admin/runs`, `GET /api/admin/runs/:runId`, protected `/admin/runs`, and a protected `/admin/runs/:runId` diagnostic surface
- a live change-history runtime slice with `GET /api/admin/change-history` and a protected `/admin/changes` chronology surface
- a live country-aware public aggregate runtime slice with `GET /api/public/countries`, `GET /api/public/products`, `GET /api/public/products/:productId`, `GET /api/public/filters`, `GET /api/public/dashboard-summary`, `GET /api/public/dashboard-rankings`, and `GET /api/public/dashboard-scatter` backed by `aggregate_refresh_run` plus `public_product_projection`
- a completed dashboard health surface on `/admin/health/dashboard` with aggregate freshness, queue visibility, serving fallback, stale or failed state signals, and operator retry
- a completed source registry admin MVP surface with `/admin/banks` for bank setup, initial bank coverage, bank-list bulk collection, per-bank coverage collection, compatibility redirects for the older `/admin/source-catalog` entry points, and read-only `/admin/sources` plus `/admin/sources/:sourceId` for generated source detail inspection
- an implemented AI-assisted `/admin/banks` onboarding flow with a bounded
  EN/KO/JA count modal, server-session country authority, largest-first
  current-web research, duplicate filtering, official citations, atomic
  profile/coverage creation, readable display-name validation, and standalone
  bounded private model context for legal and ranking names
- a registered Canada retail lending Product Type baseline for future Admin-run source collection, with active `generic_ai_review` fallback taxonomy rows for credit cards, mortgages, personal loans, and lines of credit
- a recognized Canadian bank and credit-union registry baseline with logo metadata and full active Product Type coverage for every active Canadian financial institution in the source catalog
- an FPDS-owned Admin UI built from adapted Shadcnblocks foundations, with semantic component names and recorded vendor provenance
- a committed first successful run evidence pack with raw stage outputs and live viewer artifacts
- a committed prototype findings memo that summarizes feasibility, open quality gaps, and pre-Big-5 recommendations
- a first hardening baseline that merges product-matched current-rate evidence into TD savings normalization when supporting extraction artifacts are available
- a second hardening baseline that selectively merges governing-PDF interest rules, cleans noisy text, and separates `TD Growth` qualification logic in normalization
- a third hardening baseline that uses `TD-SAV-007` to keep zero-fee savings candidates from carrying misleading fee-waiver text
- deposit parser baselines for `chequing`, `savings`, and `gic` that now extract product-type-specific fields such as transaction bundles, savings tiering or withdrawal rules, and GIC term or redeemability signals while normalizing subtype behavior to the approved canonical taxonomy
- an aggregate refresh worker slice that builds the bounded `public_product_projection` dataset from the canonical product baseline
- repository harness scripts, git hooks, and CI validation
- explicit runtime boundaries across `app`, `api/service`, `worker`, `shared`, `db`, and `storage`

This is still not a full FPDS product yet, but the ingestion core is now actively being implemented.

## Start Here

- docs map: [docs/README.md](docs/README.md)
- development journal: [docs/00-governance/development-journal.md](docs/00-governance/development-journal.md)
- requirements baseline: [docs/02-requirements/FPDS_Requirements_Definition_v1_5.md](docs/02-requirements/FPDS_Requirements_Definition_v1_5.md)
- scope baseline: [docs/02-requirements/scope-baseline.md](docs/02-requirements/scope-baseline.md)
- execution plan: [docs/01-planning/plan.md](docs/01-planning/plan.md)
- WBS: [docs/01-planning/WBS.md](docs/01-planning/WBS.md)
- working agreement: [docs/00-governance/working-agreement.md](docs/00-governance/working-agreement.md)
- decision log: [docs/00-governance/decision-log.md](docs/00-governance/decision-log.md)
- RAID log: [docs/00-governance/raid-log.md](docs/00-governance/raid-log.md)
- Canada Big 5 source registry baseline: [docs/01-planning/canada-big5-source-registry.md](docs/01-planning/canada-big5-source-registry.md)
- design docs index: [docs/03-design/README.md](docs/03-design/README.md)
- archive index: [docs/archive/README.md](docs/archive/README.md)

## Client Handoff Map

The runtime boundaries are intentionally separate:

| Area | Purpose | Start here |
|---|---|---|
| `app/admin/` | authenticated operator UI and browser-side API proxies | `app/admin/README.md` |
| `app/public/` | anonymous approved-data UI | `app/public/README.md` |
| `api/service/` | FastAPI routes, auth, CSRF/RBAC, domain services | `api/service/README.md` |
| `worker/` | discovery, collection, extraction, normalization, validation, aggregate refresh | `worker/README.md` |
| `db/` | migrations and canonical schema operations | `db/README.md` |
| `scripts/harness/` | repeatable repository verification | `docs/00-governance/harness-engineering-baseline.md` |

Admin daily work is **Overview → Review → Runs → Banks**. Sources, Product
Types, Changes, Countries, and Public Health remain available under
**More tools**. The current page-to-file maps are
`app/admin/routes.manifest.json` and `app/public/routes.manifest.json`.

Handoff verification:

```powershell
cd app/admin
pnpm run typecheck
pnpm run build

cd ../public
pnpm run typecheck
pnpm run build

cd ../..
uv run --directory api/service python -m unittest discover -s tests -p "test_*.py"
uv run python -m unittest discover -s worker -p "test_*.py"
powershell -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1
git diff --check
```

## Delivery Boundary

- `Prototype`: `TD Bank` plus `Savings Accounts` end-to-end feasibility validation
- `Phase 1`: Canada Big 5 deposit-product data platform plus public product grid, insight dashboard, admin console, BX-PF connector readiness, and EN/KO/JA UI
- `Phase 2`: Japan Big 5 expansion plus external SaaS or Open API

Out of scope for the current FPDS build:
- personalized recommendation
- consumer banking features
- public evidence trace exposure
- billing or subscription
- broad expansion beyond the approved country and product cutline

## Current Status Snapshot

### Ready

- Gate A document package is closed
- `WBS 2.1` to `2.10` foundation work is tracked as complete
- approved runtime and toolchain baselines are documented
- local tools are available: `uv`, `pnpm`, `psql`, `aws`
- hosted dev readiness and real dev secret preparation are recorded
- `WBS 3.1` to `3.4` have runnable code and verification records in-repo
- `WBS 3.5` extraction now has runnable code and unit verification records in-repo
- `WBS 3.6` normalization now has runnable code and live dev verification records in-repo
- `WBS 3.7` validation and routing now has runnable code and live dev verification records in-repo
- `WBS 3.8` prototype viewer now has runnable export code and a browser-viewable static shell in-repo
- `WBS 3.9` now has a live first end-to-end evidence pack in-repo for the three prototype target products
- `WBS 3.10` now has a written findings memo, and three follow-up hardening slices have already cleared the original `required_field_missing` validation gap, added selective `TD-SAV-008` PDF merge, improved `TD Growth` qualification cleanup, and removed misleading zero-fee `fee_waiver_condition` fields using `TD-SAV-007` evidence in live reruns
- Gate B is now closed as `Pass`
- `WBS 4.1` admin auth is now implemented and gives the admin surface its first real runtime bootstrap plus approval-gated operator onboarding
- `WBS 4.2` review queue is now implemented and gives the admin surface its first live reviewer intake route
- `WBS 4.3` review decision flow is now implemented and lets operators complete approve/reject/defer/edit-approve actions against persisted review tasks
- `WBS 4.4` evidence trace viewer is now implemented and lets operators focus a field, inspect linked evidence, and review model-stage context on the same detail route
- `WBS 4.5` run status is now implemented and gives operators a live `/admin/runs` list plus `/admin/runs/:runId` diagnostic detail route
- `WBS 4.6` change history is implemented and gives operators a live `/admin/changes` chronology route with review/run context
- `WBS 4.7`-`4.9` are historical deliveries superseded by `WBS 5.27`; the generic Audit Log and Usage routes and their retained ledgers are removed
- `WBS 4.10` operational scenario QA is now implemented and gives the repo a concrete Gate C QA artifact for the review-to-history operator path
- `WBS 5.7` public products API is now implemented and gives the repo live anonymous `/api/public/products` and `/api/public/filters` endpoints with shared public filter vocabulary, pagination, sort support, localized labels, and snapshot freshness metadata
- `WBS 5.8` dashboard APIs are now implemented and give the repo live anonymous `/api/public/dashboard-summary`, `/api/public/dashboard-rankings`, and `/api/public/dashboard-scatter` endpoints with request-time filtered summary, ranking, and scatter responses derived from the latest successful public aggregate snapshot
- `WBS 5.9` Product Grid UI is now implemented and gives the repo a live `app/public` Next.js package with `/products`, shared public filters, type-aware product cards, and pagination
- `WBS 5.10` Insight Dashboard UI is now implemented and gives the repo a dashboard-first canonical `/` Home route with a legacy `/dashboard` redirect, a live verified-record ledger, real snapshot coverage and freshness, deposit ranking, bank composition, an accessible product-type-aware comparative chart, and sibling navigation that preserves public query scope
- `WBS 5.11` grid/dashboard cross-filter is now implemented and gives the repo scope-preserving public sibling nav plus dashboard-to-grid drill-in links for breakdown, ranking, and scatter views
- `WBS 5.12` locale rollout is now implemented and gives the repo EN/KO/JA locale-aware public and admin shells with query-preserved locale switching, locale-aware labels, and locale-aware date or number formatting for UI-owned copy
- `WBS 5.13` freshness/metric note wording is now implemented and gives the repo locale-aware public methodology/freshness note cards plus clearer dashboard note wording for snapshot timing, metric semantics, exclusion rules, and public evidence non-exposure
- `WBS 5.15` source registry admin MVP is now implemented and gives the repo a live DB-backed bank and source-catalog flow with `/admin/banks` as the primary operator surface for both bank setup and coverage management, compatibility redirects for `/admin/source-catalog`, read-only `/admin/sources`, `GET/POST/PATCH /api/admin/banks`, `GET/POST/PATCH /api/admin/source-catalog`, and `POST /api/admin/source-catalog/collect`
- `WBS 5.16` operator-managed product type onboarding is implemented for the admin and collection pipeline: `/admin/product-types` manages all product types as DB rows, bank coverage is registry-driven, discovery uses stored definitions, and types without specialized parsers use generic AI extraction plus official-grounding eligibility instead of blanket manual review
- the Canada retail lending baseline (`credit-card`, `mortgage`, `personal-loan`, `line-of-credit`) uses the same evidence, validation, official-AI threshold, canonical change-history, and Public aggregate boundaries as other active product types
- a recognized Canadian financial-institution baseline is now registered for Admin-run source collection with 28 active Canadian bank/direct-bank/credit-union profiles, logo metadata for bank screens, and 196 active source-catalog coverage rows across 7 active Product Types
- discovery preflight drift checks and scheduled refresh artifact generation are now available under `worker/discovery/`
- the Python worker baseline and parser dependencies are now tracked in `pyproject.toml`
- the first FastAPI admin service baseline is now tracked in `api/service/pyproject.toml`
- the first Next.js admin package baseline is now tracked in `app/admin/package.json`
- the first Next.js public package baseline is now tracked in `app/public/package.json`

### In Progress

- ongoing source-quality hardening and Phase 1 operational data coverage
- browser smoke follow-ons when new operator or Public workflows are added

### Not Started

- BX-PF runtime integration code

### Hold Rule

The Product Owner has explicitly started WBS `5` product implementation.

Scope now includes the approved post-prototype path through `WBS 5.4`:
- Canada Big 5 source-registry baseline
- continued evidence-first expansion for `chequing`, `savings`, and `gic`
- completed parser baselines for `chequing`, `savings`, and `gic` across the worker stages using the approved registry catalog
- completed aggregate source dataset generation for the public grid and dashboard backing stores
- public-experience follow-on slices only within the approved Phase 1 cutline

## Approved Technical Baseline

- primary product language: `Python`
- browser-facing frontend language: `TypeScript`
- frontend runtime baseline: `Next.js App Router`
- API runtime baseline: `FastAPI` as a separate service
- worker baseline: separate `Python worker process`
- frontend package manager: `pnpm`
- Python package and runtime manager: `uv`
- admin auth approach: server-side session auth managed by the Python API
- dev monitoring baseline: `disabled` for the first implementation pass

These remain the approved baselines for the broader runtime.
Current implementation evidence is still heaviest in the Python worker path, but the first live admin frontend and API packages now exist as well.

## Foundation Baselines In Repo

- env contract: [docs/03-design/dev-prod-environment-spec.md](docs/03-design/dev-prod-environment-spec.md)
- design-system baseline: [docs/03-design/fpds-design-system.md](docs/03-design/fpds-design-system.md)
- frontend benchmark baseline: [docs/03-design/fpds_design_system_stripe_benchmark.md](docs/03-design/fpds_design_system_stripe_benchmark.md)
- env examples: `.env.dev.example`, `.env.prod.example`
- config landing zone: [shared/config/README.md](shared/config/README.md)
- design landing zone: [shared/design/README.md](shared/design/README.md)
- DB baseline: [docs/03-design/db-migration-baseline.md](docs/03-design/db-migration-baseline.md)
- DB entrypoint: [db/README.md](db/README.md)
- storage baseline: [docs/03-design/object-storage-evidence-bucket-baseline.md](docs/03-design/object-storage-evidence-bucket-baseline.md)
- storage entrypoint: [storage/README.md](storage/README.md)
- auth and security baseline: [shared/security/README.md](shared/security/README.md)
- i18n baseline: [shared/i18n/README.md](shared/i18n/README.md)
- observability baseline: [shared/observability/README.md](shared/observability/README.md)
- public route manifest: [app/public/routes.manifest.json](app/public/routes.manifest.json)
- admin route manifest: [app/admin/routes.manifest.json](app/admin/routes.manifest.json)

Rules:
- only placeholder values are committed
- real secrets stay out of git
- `dev` is the current local development shape
- `BX-PF` remains `mock` in `dev` and real write-back is `prod` only
- browser-facing surfaces must not receive direct private object access

## Local Toolchain

Expected local tools:
- `uv`
- `pnpm`
- `psql`
- `aws`

Notes:
- `psql` is installed as PostgreSQL command-line tools only. A local Postgres server is not part of the repo baseline.
- if a new tool is not visible in the current shell, restart the terminal so `PATH` reloads cleanly

## Harness Commands

Install Git hooks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/install-hooks.ps1
```

Run repository health checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1
```

Run the full foundation baseline checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1
```

Run the report-only cleanup audit:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1
```

Optional future project-wide checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-project-checks.ps1
```

## What The Harness Does

- `pre-commit` only inspects staged files
- the hook can auto-fix low-risk text hygiene issues
- staged Markdown references and staged PowerShell syntax are validated
- foundation checks validate env examples, JSON artifacts, observability artifacts, and future package-script baselines
- JavaScript package checks are `pnpm-first`, and the shared project-check entrypoint installs missing dependencies when a tracked package has no local `node_modules`
- CI remains validation-only and does not imply product implementation has started
- cleanup audit is intentionally `report-only`

## Current Top-Level Layout

- `app/` browser-facing public, admin, and prototype viewer boundaries
- `api/` public, admin, and internal API boundaries
- `db/` SQL-first migration baseline and DB notes
- `storage/` object storage and evidence bucket baseline
- `worker/` discovery, pipeline, publish, and runtime worker boundaries
- `shared/` contracts, config, design, domain, i18n, observability, and security modules
- `docs/` requirements, governance, planning, and design
- `scripts/harness/` repository checks, audits, and helper scripts
- `.githooks/` git hook entrypoints
- `.github/workflows/` CI validation workflows
