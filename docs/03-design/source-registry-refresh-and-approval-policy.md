# FPDS Source Registry Operations Policy

Version: 1.2
Date: 2026-04-21
Status: Active Operating Baseline
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/admin-information-architecture.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/source-snapshot-evidence-storage-strategy.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This document defines the Phase 1 operating policy for source registry management.

Goals:
- make source registry ownership explicit before implementation starts
- let operators manage bank and product coverage from the admin UI without editing repo JSON files
- keep collection runs reproducible even when registry entries are edited over time
- keep the first implementation intentionally small: bank management, source catalog management, and source-selected product collection

This is an operating-policy baseline, not an implementation approval by itself.

---

## 2. Baseline Decisions

1. The operational source of truth for the active source registry will be the FPDS database.
2. Admin operators will manage banks and source catalog coverage directly in the admin UI, while generated source rows remain system-managed except for admin-only removal that marks a bad row `removed`.
3. After the DB-backed source registry is introduced, `source_registry_catalog.json` and per-bank registry JSON files will no longer be the ongoing operational control surface.
4. The admin `collect` action means full product collection through candidate creation, not raw fetch only.
5. The first collection target is `normalized_candidate` plus normal validation/routing side effects such as `review_task` creation when rules require it.
6. Candidate-producing scope is controlled by registry role. `detail` sources are candidate-producing by default. Supporting sources may be included for evidence support, but they should not create standalone product candidates unless their registry role explicitly allows it.
7. Registry edits are direct operational changes, so they must be audit-visible.
8. The MVP stays intentionally narrow: no diff-heavy refresh approval workflow is required for the first admin-managed registry slice.
9. Committed seed rows are discovery hints, not permanent safety exceptions. Each refresh applies the current action-flow, calculator, servicing/help, onboarding/join, forms-repository, editorial/tips, product-type, and supporting-relevance policy to seeded hints before materializing active rows.

Short form:

`source registry is DB-backed, admin-managed, and collect means candidate-producing ingestion`

---

## 3. Why This Policy Was Chosen

### 3.1 Why Not Keep JSON as the Live Registry

Repo JSON files were useful to bootstrap the Big 5 registry baseline, but they are not a good long-term operator control surface.

Problems with JSON-as-operations:
- non-developers cannot safely manage it from the admin runtime
- edit history is tied to git workflow instead of operator workflow
- runtime state and operator action history drift apart
- launching collection from a selected source list becomes awkward if the true registry still lives in files

### 3.2 Why Bank and Catalog Editing Is Acceptable for MVP

The Product Owner explicitly prefers a minimal management flow over a heavier approval system.

That makes sense for the next slice because:
- the team needs a practical operator surface now, not a full registry governance product
- bank/profile editing plus catalog coverage management is simpler than candidate-diff plus promotion workflow
- it keeps focus on the immediate business value: maintain source scope and collect product candidates

### 3.3 Why Collect Should Produce Candidates

FPDS is not building a crawl archive for its own sake. The useful operator outcome is a reviewable product candidate.

Benefits:
- operators see whether a selected source actually leads to product candidates
- source management and operational outcome stay connected
- the admin console can link registry, run, candidate, and review flows directly

Tradeoff:
- the collection action is heavier than raw fetch-only collection
- quality guardrails matter more because supporting pages should not become noisy standalone candidates

That is why candidate-producing scope must stay registry-role-aware.

---

## 4. Minimum Registry Data Model

The DB-backed source registry should retain at least the following fields for generated or materialized source rows:

- `source_id`
- `bank_code`
- `country_code`
- `product_type`
- `product_key` or equivalent stable logical grouping key
- `source_name`
- `normalized_url`
- `source_type`
- `discovery_role`
- `status`
- `priority`
- `source_language`
- `last_verified_at`
- `last_seen_at`
- `change_reason`
- `redirect_target_url` when applicable
- `alias_urls` when applicable
- `created_at`
- `updated_at`

The DB-backed bank profile should also retain screen-facing logo metadata:

- `logo_url`
- `logo_alt_text`

Logo presentation rule:
- Admin and Public present bank marks without a surrounding card, border, or decorative background.
- `logo_url` should use a verified official brand asset where one is publicly available. Favicon URLs are a narrowly scoped resilience fallback for a blocked, retired, or otherwise unavailable full official asset.
- A migration refresh must not replace an operator-supplied custom logo URL.

Minimum status vocabulary for the MVP:

| Status | Meaning | Default Collection Eligible |
|---|---|---|
| `active` | current approved source row | Yes |
| `inactive` | stored but not part of default collection scope | No |
| `deprecated` | historical row kept for traceability | No |
| `removed` | no longer operationally used | No |

Minimum role vocabulary for the MVP:

| Role | Meaning | Candidate-Producing |
|---|---|---|
| `detail` | primary product truth source | Yes |
| `supporting_html` | supporting page for fees/rates/terms | No by default |
| `supporting_pdf` | supporting governing/rates PDF | No by default |
| `entry` | listing/discovery page | No by default |

---

## 5. Minimal Admin Functions

The first admin-managed source registry slice should support only the following functions:

1. List and filter banks.
2. Create and edit bank profiles with auto-generated bank codes.
3. List and filter source catalog items by bank, product type, and status.
4. Create and edit source catalog items using controlled bank and product-type inputs.
5. Select one or more source catalog items and start collection.
6. See the resulting run id and success/failure summary.
7. Inspect generated source rows in the source registry surface.
8. Remove a bad generated source row by marking it `removed`, preserving audit and historical run context.

Current live workflow note:
- `/admin/banks` is now the primary operator-owned surface for bank setup, bank-owned coverage management, and collection launch.
- `/admin/source-catalog` may still exist as a compatibility route, but it is no longer the preferred primary workflow.
- bank list bulk collect is allowed as long as the action resolves to the underlying bank-plus-product coverage items.
- a bank/Product Type without a completed ingestion run carrying a non-empty
  source scope always performs precision discovery; generated source count
  alone is not completion
- after completion, single and bulk Banks collection accept an explicit
  precision-rediscovery option. Completed items default to current active
  source reuse, while first-time items in the same bulk request stay precision
- standard reuse is valid only with an active `detail` source. If the scope
  was removed or became empty before execution, the runner forces precision
  discovery and records that fallback

Current AI bank-onboarding note:
- an `admin` may request `1` to `10` missing banks for the authenticated
  server-session country
- live web research must use one current comparable size measure, consult an
  authoritative ranking source, and establish each official homepage
- the registry `bank_name` is the official customer-facing display name;
  full legal entity names and exact ranking-source labels remain separate
  private execution/audit evidence, and fixed-width regulatory abbreviations
  are not valid display names
- existing identities and homepage domains are excluded again on the server;
  the requested set is rejected unless every bank remains fully valid
- coverage is created only for active Product Type registry codes supported by
  a current official retail page. The page may be on a separate consumer-brand
  domain only when a consulted page on the bank or brand domain contains an
  exact quote proving the brand/product relationship to the registered bank
- each AI-created coverage row preserves the verified page as private
  `coverage_source_url` evidence and stores bounded verification metadata,
  including the product-specific domain, current-offering quote, relationship
  quote, consulted sources, and model lineage. Collection starts there before
  bounded homepage fallback; the additional domain is not shared with other
  banks or Product Types
- a directly verified same-domain logo is preferred; the homepage-domain
  favicon is the only automatic fallback
- all bank and coverage writes are atomic and usage/audit records remain
  private; the action does not collect or publish products

Still deferred from the MVP:
- crawler-driven registry auto-promotion
- candidate-diff review UI for registry changes
- visual diffing between historical registry versions

Current live product-type onboarding note:
- `/admin/product-types` now lets operators manage product type definitions with searchable name and description fields.
- Bank coverage creation validates against that registry instead of a hard-coded canonical list.
- Chequing, savings, GIC, and every later product type are all ordinary operator-managed DB rows. Collection must fail clearly when the requested product type row is missing or inactive.
- Product type code is an operator-managed identity field. When a code is corrected from the Product Types detail modal, the backend renames the registry row and cascades source catalog, generated source, candidate, canonical product, public projection, and taxonomy references instead of relying on aliases.
- For the Phase 1 canonical deposit product types `chequing`, `savings`, and `gic`, product-type registry writes must keep the full approved subtype taxonomy synchronized, not only the generic `other` fallback. Dynamic or newly added product types still start with `other` unless a later approved subtype registry is introduced.
- The Canada retail lending baseline is registered as `credit-card`, `mortgage`, `personal-loan`, and `line-of-credit` under `product_family=lending`. FPDS canonical product type codes use hyphens even when an operator enters spaces or underscores.
- Homepage-first discovery now carries the stored product type definition into AI-assisted detail-source resolution.
- Country-local discovery vocabulary is allowed without renaming canonical
  Product Type codes. In the US, canonical `chequing` is discovered as
  checking, canonical `gic` as certificates of deposit/CDs, and canonical
  `personal-loan` may use auto/student/installment-loan identity terms. Local
  identity nouns are merged narrowly; they also prevent an explicit HELOC or
  certificate-of-deposit route from being rejected solely because its parent
  path contains a sibling family word such as `mortgage` or `savings`.
  Attribute-only terms do not establish a different product identity.
- Dynamic component catalogs may expose official links and product copy only
  inside JSON-valued `data-*` attributes. Discovery and parsing may read those
  values only with fixed size/node/count limits and the normal same-domain,
  HTTPS, role, and page-evidence checks.
- Homepage-first discovery may infer a bounded discovery profile from the stored display name, description, and discovery keywords. For example, a registered `saving` row whose definition clearly describes savings accounts can use `savings` discovery signals, while generated source rows still preserve the registered product type code.
- the approved follow-on design now upgrades discovery quality through bounded AI parallel scoring, stronger product-type-description grounding, and page-level evidence scoring before `detail` promotion. See `docs/03-design/homepage-discovery-scoring-enhancement.md`.
- generated source rows now persist structured `discovery_metadata`, and `/admin/sources/:sourceId` exposes that explainability block for operator inspection.
- Operator-managed product types without specialized parser support, including
  the current lending baseline, continue through generic AI
  extraction/normalization. They may use normal policy auto-approval only when
  the persisted official-grounding assessment verifies product identity and
  `100%` of the type-specific essential comparison set. Empty optional
  marketing and operational fields are not requested by default;
  missing rate, price, amount, or term requirements are validation errors and
  ungrounded lending attributes are suppressed. Unknown dynamic types require
  a registry contract with a percentage field plus another decision field.
  Otherwise the candidate remains in Review.
  Approved `mortgage`, `personal-loan`, and `line-of-credit` products are
  included in the Public aggregate snapshot; unapproved candidates remain
  non-public.
- Collection-field selection is market-profile driven. The executable profile
  key is `(country_code, product_type)` and its version/key are stored in
  generated source discovery metadata. Canada uses the approved baseline
  contract; US Checking/Savings/CD/Mortgage/Personal Loan use the D-035 market
  overrides. A future country adds a bounded declarative profile and fixtures,
  not scattered pipeline conditionals. An explicitly named country without a
  profile and missing/unknown dynamic contracts fail closed.
- US Savings treats a positive monthly fee exactly like US Checking for
  comparison safety: the complete waiver condition is mandatory. A conditional
  APY is publishable only with an `interest_rate_summary` that preserves the
  official new-customer, qualifying-balance/timing, fallback-rate, as-of-date,
  and variability context. A simple unconditional current APY does not require
  invented qualifier prose. US lending relationship/autopay discounts retain
  their qualifying account/payment and existing-customer conditions.
- Every materialized and newly discovered URL must agree with the collection
  country. An explicit other-country path/locale, subdomain, or country-code TLD
  is a hard scope veto even when the bank uses the same official parent domain
  for both markets. Existing generated detail rows that violate this boundary
  are inactivated with audit lineage; seed, entry, supporting, and PDF routes
  are filtered before fetch or merge.
- Source collection plans and extraction artifacts must carry `product_family` from the product type registry so lending candidates are not normalized as deposits.
- Known Big 5 seed entry URLs are authoritative for homepage-first collection. When a bank has approved seed registry rows, collection must materialize the `entry` row from that official product-list URL rather than from a homepage-discovered hub.
- Precision discovery may reuse active DB registry `entry` and `detail`
  rows after official-domain, country, source-language, and Product Type
  validation. It may inspect at most 12 existing detail pages for current
  sibling-product links, and every resulting candidate still requires normal
  page-evidence and product-boundary validation
- precision run metadata must expose reused/rejected seed counts, attempted
  and successful hub/detail page counts, candidate and promoted/rejected
  counts, and every reached cap; this telemetry is operational context, not
  public evidence
- Discovery must reject investor/shareholder pages, registered-plan wrapper pages such as TFSA/RRSP/RESP/FHSA packaging, and links whose URL or visible title clearly belongs to another product type before promoting generated source rows.
- A source-catalog collect should merge newly generated source rows with existing active detail rows for the same bank/product scope so a partial discovery pass does not accidentally shrink candidate-producing coverage.
- A successful rediscovery should deactivate only explicitly rejected, non-seed, automatically generated detail rows in the same bank/Product Type scope. It must preserve seed rows and candidates whose page fetch was unavailable, so stale false-positive details leave collection scope without treating transient fetch failures as deletion evidence.

---

## 6. Collection Semantics

For this policy, `collect` means:

1. use the selected source rows as run scope
2. fetch and persist snapshots as needed
3. parse and chunk the fetched content
4. run extraction and normalization
5. persist `normalized_candidate`
6. run normal validation/routing behavior
7. create `review_task` rows when the candidate is not auto-clear
8. promote policy-clear `auto_validated` candidates through the audited canonical upsert path
9. when enabled, AI-verify and safely correct a bounded set of active detail
   review tasks left by this run
10. system-approve only candidates meeting the complete essential-field
    contract with no hard identity/boundary/taxonomy/type/range/conflict/
    ambiguity blocker, and queue the normal
    country aggregate refresh; retain every other candidate in Review
11. when no eligible detail source remains, perform one bounded current-coverage
    repair. A verified current route is persisted and discovery is retried once;
    explicit official retirement evidence deactivates that catalog coverage and
    closes the run as `product_not_currently_offered` without Partial; an
    uncertain result remains a no-detail Partial

Configured collection extraction performs a bounded current-official-source
grounding pass for each candidate-producing detail source before normalization.
The registry supplies the canonical official-domain allowlist and normalized
origin URL. Values remain eligible only when a consulted allowlisted URL and
an exact quote from the fresh captured chunk agree; provider failure falls back
to deterministic extraction and does not weaken review or publication gates.
An exact labeled currency fee on an identity-matched, high-confidence official
`detail` snapshot may be grounded deterministically under the narrower field
contract rule; it still requires an explicitly configured official domain,
co-located label/value evidence, and all normal validation and publication
gates. The same origin rule may preserve a qualified lending rate summary and
its amount/limit/term/rate-type companions when both the value and qualifying
context are co-located in that verified detail snapshot; it never converts a
range, formula, or representative example to a scalar rate. When several fees
share a chunk, the nearest label/value pair wins and authorized-user,
additional-card, supplementary-card, and employee-card fees are excluded from
the base product fee. Editorial paths, including singular
`/article/` routes, remain outside
candidate-producing scope even when their copy discusses the requested product.
For dynamic/lending candidates, this grounding also produces a persisted
decision-field eligibility assessment. A passing assessment removes the old
blanket manual-review rule but does not remove any validator, force-review,
source-role, product-boundary, canonical, audit, or aggregate-refresh guard.
Residual Review AI v7 uses identity plus one field for every mandatory
comparison requirement as its denominator. It does not request or penalize
absent optional marketing/operational fields, and it does not reuse earlier
assessment contracts. A partial-source or confidence warning alone is
non-blocking once all essentials pass. If Review AI abstains on
an unchanged fee or qualified lending comparison field already carrying the
narrow exact-origin contract, the assessment may reuse that persisted evidence after the registered-domain check;
an explicit mismatch remains fail-closed.

Important rules:
- the run must persist which source rows were selected so the collection scope is reproducible later
- the run must carry exactly one country and every worker-stage
  `ingestion_run` upsert must persist that `country_code`
- a worker subprocess failure must retain the exact failed stage plus a
  bounded, credential-redacted diagnostic in private run metadata; a generic
  exit code alone is not sufficient operational evidence
- `detail` sources are the default candidate-producing scope
- supporting sources may still be fetched and parsed during the same run only
  when they are bounded to the selected product: a detail descendant/companion,
  a Product-Type-compatible rate/APR page, or a relevant essential-fact
  FAQ/disclosure. Educational, servicing, application, transfer, investment,
  sibling-product, and conflicting Product-Type routes are excluded before fetch
- only `detail` sources create primary standalone candidates; supporting and linked sources remain evidence-only even when selected or auto-included
- AI-classified `supporting_html` pages should be retained when they provide product-matched rate/fee/term evidence, and normalization may merge their grounded fields into the related detail candidate
- official rate, pricing, disclosure, and terms pages are priority supporting
  sources for lending. Collection AI must actively search them for missing
  mandatory fields. A range, variable-rate formula, or representative example
  is retained with all stated assumptions in `interest_rate_summary` and is not
  coerced into one misleading scalar.
- an exact-product official bundle may combine the detail page with a rate page,
  fee schedule, and governing disclosure. Supporting sources never create
  standalone candidates; every accepted companion keeps its own source
  document and exact quote. US CD disclosures may contribute a quantified
  early-withdrawal penalty, and lending support may contribute a qualified
  rate summary plus grounded rate-type/term/amount companions.
- retail collection scope must reject clearly business/commercial/corporate product pages before they become generated detail sources
- cross-domain collection is allowed only for the single verified catalog
  coverage domain carried with its relationship evidence; ordinary discovered
  links remain bounded to the registered bank homepage domain
- route validation uses only the proposed URL and current-offering quote for
  Product Type scope. Explanatory model prose about a rejected prior route must
  not taint the replacement route
- seed-backed detail hints with low page evidence remain eligible only when page validation has no negative signal; low-evidence pages with negative signals should not become candidate-producing detail sources and should rely on later rerun/source correction instead
- a source-catalog bulk collect should enqueue the selected bank/product groups as one collection plan and process those groups sequentially inside one background runner process; the deeper source-collection stages still apply per-stage timeouts, but the plan-level runner should avoid launching one DB-connected process per group and exhausting the session pool
- snapshot checksum reuse is scoped to the same source document. Different URLs that return the same WAF, consent, or error body remain independently attributable and cannot borrow one another's successful snapshot identity
- when a URL is shared as supporting evidence by later scopes, snapshot persistence must preserve an existing candidate-producing `detail` metadata assignment. A later supporting fetch may add evidence, but it cannot silently change that source document's product boundary or role

---

## 7. JSON Retirement Rule

Current repo JSON registry files remain useful as historical baseline artifacts and migration input.

However, once the DB-backed admin-managed registry is introduced:
- operators do not manage live registry state through JSON anymore
- runtime collection must read the DB-backed registry state
- JSON files stop being the operational source of truth

This is an operations-policy change, not a requirement to immediately delete the historical files from the repository.

---

## 8. Current Repository State

Current repository state:
- the repo contains `source_registry_catalog.json` and per-bank registry JSON baselines
- the live admin runtime now includes `/admin/banks`, `/admin/source-catalog`, and `/admin/sources` with generated-source inspection plus admin-only soft remove
- operator-managed registry ownership now lives in `bank` and `source_registry_catalog_item`
- generated source detail lives in `source_registry_item`
- the live DB tables are now respected as-is at runtime, including intentionally empty reset states; committed JSON baselines remain import/reference material rather than an automatic runtime bootstrap path
- collection can now be started from the admin source catalog list and produces generated source rows, `normalized_candidate` rows, and normal review-routing side effects
- collection now also invokes audited auto-promotion for validation-pass candidates that meet confidence and force-review policy; for Canada Big 5 deposit collection, validation-pass follows the golden fixture field contract; promoted candidates enqueue aggregate refresh, non-detail/non-product false positives are audit-logged and rejected, and an approved newer candidate resolves older active reviews from the same detail source as superseded
- detail promotion now requires independent product-identity evidence for a strong page override and honors AI support/not-detail veto reasons; the 2026-07-13 Alterna chequing verification rerun used two active product-detail sources, auto-validated two valid products, and created zero review tasks while three stale support/rates details were made inactive
- the worker execution path is still file/catalog oriented under the hood, so the API-side runner currently materializes temporary grouped registry files for the selected source scope
- candidate-producing scope is role-aware and limited to `detail`. Existing bank-specific merges remain supported, while generated product-matched supporting HTML can now provide generic savings or GIC rate evidence without becoming a candidate itself
- generated collection allowlists canonicalize only a leading `www.` host label so official apex redirects remain bounded. Supporting links under an unrelated product path are excluded, and multi-product family pages carry an explicit ambiguous-boundary reason that prevents automatic canonical publication.
- homepage discovery may recover bounded routes and product copy from
  non-executable `application/json` and `application/ld+json` script payloads
  when a server-rendered application shell exposes no ordinary anchors. Only
  recognized link keys are read, payload/link/node limits are enforced, and
  every recovered URL remains subject to the same official-domain, exclusion,
  source-role, page-evidence, review, and publication boundaries as an HTML
  anchor.
- page-level evidence may use the normalized official URL path as a bounded
  product-identity signal. Login/comparison/legal words count against a page
  only when prominent in the route, title, or primary heading; shared
  navigation and serialized application state do not independently disqualify
  coherent product and pricing evidence.
- any already validated official HTML source whose direct fetch times out or is reset/closed by the remote host receives one browser DOM attempt, independent of bank or Product Type and without adding that bank to a rendering exception list. Configured dynamic-rendering domains retain their format-aware behavior; PDF routes do not enter this generic transport path. A high-confidence HTTP-200 access-challenge shell likewise receives one browser DOM attempt on any validated official domain. A recovered page re-enters all ordinary evidence gates; a still-challenged page is structurally rejected and may quarantine a zero-detail scope, while browser runtime failure remains transient. The requested output format is explicit, all attempts remain on the same validated official URL and per-bank domain boundary, snapshot metadata records `browser_html_fallback` plus `direct_transport_failure` when applicable, and downstream missing-field validation still protects publication.
- bounded browser recovery is serialized inside each worker process so a concurrent source batch does not amplify the institution's access challenge. A declared PDF source is fail-closed when recovery yields HTML instead of PDF bytes. On a later standard collection, a source whose latest result is either a persisted post-browser challenge or that PDF/content-type mismatch is omitted from the runtime scope without mutating the registry; precision rediscovery remains the explicit revalidation path, and browser-unavailable or timeout outcomes remain retryable.
- exact-product companion selection rejects global user agreements and deposit-scope wealth/investment disclosures that contain no account, deposit, rate, or fee context. The same rule applies when a standard run reuses older active registry rows. Product-specific account/card agreements and pricing disclosures remain eligible, so the exclusion removes structurally irrelevant work without weakening comparison evidence.
- corporate annual, climate, and climate-disclosure reports are not product-supporting evidence. Discovery excludes them before source materialization even when a broad PDF link heuristic matches, so their retirement cannot make otherwise healthy Product Type runs partial.
- when an official CMS separates a product card's visible identity, canonical link, and condition fields into nested structured values, discovery may preserve that same-card relationship from rendered DOM instead of relying on flattened visible/PDF text. Vancity is the bounded current case: internal Sitecore routes are ignored, canonical `href` wins over sibling internal `url`, exact curated details are not demoted by unrelated bottom-page cross-sells, and a revalidated canonical route retires case-only generated aliases.
- one official detail URL may produce more than one product candidate only when separate bounded blocks each contain an exact product name plus every required comparable fact for the expansion contract. Current Vancity Student Visa handling requires name, annual fee, and purchase rate in each block; partial or mixed blocks remain a single Review-bound proposal. Fresh capture time never overrides an explicit financial `rates as of` date, and evidence dated more than five years before validation is hard-blocked from automatic publication.
- retail discovery treats explicit commercial URL/title signals as hard scope vetoes across deposit and lending types. Successful rediscovery also revalidates previously generated detail rows and inactivates stale rows that now match a deterministic hard-scope veto, so an old commercial detail cannot survive merely because it was excluded before current candidate evaluation. Plural family identities such as a generic credit-cards heading plus multiple named variants are classified as `multi_product_family_overview`; lending family overviews are evidence-only rather than standalone candidates, while any review-first family handling remains blocked from auto-publication.
- explicit application/prequalification routes and internal `shadow-site` mirrors are hard source-scope vetoes. Their absence must not make a run partial because they are operator journeys or stale internal mirrors, not evidence sources.
- a confirmed singular product heading/title with explicit attributes may override a family marker caused only by plural SEO copy or related-product headings; generic plural/category identities remain supporting-only.
- plural wording alone does not make one branded lending offering a family.
  Repeated personal-loan use cases remain one product, while distinct subtype
  sections remain a family boundary. AI `hub_page_not_detail` sources allowed
  as deposit fallback are treated as ambiguous by validation, API
  auto-promotion, and the collection review autopilot.
- rejected detail candidates retain a bounded diagnostic summary with URL, AI role/score, page score, title/H1, and reason codes so Operations can distinguish a weak source from a discovery-policy defect without reopening raw worker logs.
- when no detail survives, the run summary prioritizes that rejection aggregate
  and a representative rejected detail over incidental hub-fetch noise.
- seed detail hints retain discovery continuity but cannot reduce the current Product Type expected-field baseline; generated details request the union so stale seed metadata cannot create structurally incomplete approved products.
- operator-managed product type onboarding is now live, and its next discovery-quality improvements are documented in `docs/03-design/homepage-discovery-scoring-enhancement.md`
- the Canada retail lending Product Type baseline is live in DB through migration `0019`, with active generic `other` taxonomy fallback rows for `credit-card`, `mortgage`, `personal-loan`, and `line-of-credit`
- the recognized Canada financial-institution baseline is live in DB through migrations `0020`, `0021`, and `0022`, with 28 active Canadian bank/direct-bank/credit-union profiles, refreshed official logo metadata where publicly available, and full active Product Type source-catalog coverage for every active Canadian financial institution

---

## 9. Non-Goals

The following are intentionally out of scope for the first source-registry admin slice:

- automatic source discovery that silently edits the active registry
- complex candidate-diff review UX for registry promotion
- generalized multi-bank supporting-source inference engine beyond what the existing pipeline already needs
- replacing run diagnostics, review queue, or change history with a source-centric workflow
- bulk destructive actions without audit visibility

---

## 10. Follow-On Work Remaining

- explicit DB import/export tooling for source-registry administration beyond first-boot seeding
- broader supporting-source auto-inclusion rules beyond the existing explicit TD, BMO, and Scotia savings paths
- dedicated collection-progress UX on the source surfaces instead of relying on the run views for deeper execution visibility
- optional approval governance follow-ons if source-registry operations later need tighter release controls

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-04-10 | Initial source registry refresh and approval policy added |
| 2026-04-15 | Replaced the JSON-first approval baseline with a DB-backed admin-managed source registry baseline and defined `collect` as candidate-producing ingestion |
| 2026-04-15 | Refined the MVP so operators manage banks and source catalog coverage while generated source rows remain read-only |
| 2026-04-15 | Updated the policy after the `WBS 5.15` implementation so current-state notes now reflect the live DB-backed `/admin/sources` runtime |
| 2026-04-18 | Linked the approved homepage-discovery quality follow-on design and corrected the current-state note for live operator-managed product-type onboarding |
| 2026-04-18 | Recorded the first homepage-discovery explainability implementation slice on generated source rows and source-detail inspection |
| 2026-04-28 | Added admin-only generated source soft removal using `removed` status so bad collected source details can be excluded from future collection without losing audit history |
| 2026-07-05 | Added bank logo metadata and recognized Canada bank full active Product Type coverage baseline status |
| 2026-07-05 | Added Vancity to the recognized Canada coverage set by explicit Product Owner request |
| 2026-07-13 | Added the unframed bank-logo presentation rule and official asset refresh policy |
| 2026-07-22 | Applied current scope policy to seed hints, excluded non-evidence servicing/onboarding/editorial repositories, and added bounded detail-rejection diagnostics plus named-product recovery rules |
| 2026-07-22 | Made detail expected fields additive over the active Product Type contract and extended dynamic-rate recovery to double-bracket rate/APR placeholders |
| 2026-07-30 | Added the official-evidence, duplicate, logo-fallback, active-coverage, and atomicity rules for AI bank onboarding |
| 2026-07-30 | Separated customer-facing bank display names from legal entity names and exact ranking labels; rejected fixed-width US regulatory abbreviations as registry display names |
| 2026-08-06 | Excluded singular editorial article routes, preserved explicit local Product Type identity across sibling route vocabulary, and allowed narrowly bounded exact-origin grounding for labeled currency fees |
