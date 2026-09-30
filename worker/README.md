# Worker Boundary

The 2026-09-30 zero-value correction requires explicit evidence for the same
financial attribute: a no-fee benefit cannot prove zero minimum balance or
deposit. See the [RBC/BMO assessment](../docs/00-governance/collection-accuracy-oneoff-rbc-bmo-2026-09-30.md).
This correction is tested locally and requires collection-runtime deployment.

## Accuracy gate — 2026-09-30

`fpds_collection_accuracy` runs after normalization and before validation. It
omits facts without exact official evidence, type, meaning and currency proof.
All product types require its content-bound receipt. Validation emits
`auto_validated` or `excluded` and creates no review task. Legacy confidence
thresholds cannot weaken this rule. Earlier manual/residual-review instructions
below are superseded for new collection. See
[policy](../docs/03-design/collection-accuracy-policy.md).
Live pilot regressions cover written transaction counts, standalone suitability
headings versus actual fee conditions, and annual-fee/rate-basis separation.

Economical recovery now skips official grounding when captured chunks contain no
explicit supported currency. AI requests target identity/currency and registered
comparison essentials, retaining annual/APY and redemption qualifiers needed for
Public comparisons without extra searches. A private one-entry-per-source cache reuses completed
positive or negative grounding only for identical source/snapshot/chunks, metadata,
requested fields, model, relevant code and UTC date. Provider failures are not
cached. Normalization/validation/promotion still run; dynamic normalization is
not covered by this extraction cache. The normal CLI binds parsing to the current
run's successful selected snapshot. New extraction artifacts use run-specific
paths, preserving previous runs. Usage summaries stay in bounded model execution
metadata; no standalone usage ledger/UI is introduced. See the
[recovery report](../docs/00-governance/collection-accuracy-recovery-2026-09-30.md).

This directory holds private pipeline and integration workers.

## OpenAI model and reasoning

The model defaults to `gpt-6-luna`, selected through `FPDS_LLM_MODEL` and the
shared `fpds_ai_runtime` helper. Extraction/official grounding explicitly uses
`high`; dynamic normalization uses `medium`. Financial evidence, field contracts,
provider-failure fallback and approval gates remain unchanged. See the
[environment contract](../docs/03-design/dev-prod-environment-spec.md)
for all API/worker task settings and deployment configuration.

Current boundary:
- `discovery/` for source discovery and registry-driven fetch entry
- `pipeline/` for parse, chunk, extraction, normalization, validation, and review routing work
- `publish/` for BX-PF-facing publish and reconciliation work
- `runtime/` for worker bootstrap and execution plumbing

Current implementation slices:
- `WBS 3.1` source discovery, preflight drift checks, and operator-initiated refresh artifacts in `worker/discovery/`
- `WBS 3.2` snapshot capture and persistence in `worker/discovery/fpds_snapshot/`
- `WBS 3.3` parse/chunk pipeline in `worker/pipeline/fpds_parse_chunk/`
- `WBS 3.4` evidence retrieval in `worker/pipeline/fpds_evidence_retrieval/`
- `WBS 3.5` extraction flow in `worker/pipeline/fpds_extraction/`
- `WBS 3.6` normalization mapping in `worker/pipeline/fpds_normalization/`
- `WBS 3.7` validation/confidence routing in `worker/pipeline/fpds_validation_routing/`

Runtime invariants:
- one ingestion run owns exactly one normalized ISO alpha-2 country code;
  snapshot, parse/chunk, extraction, normalization, and validation persistence
  all write that country and reject mixed-country scopes before DB work
- HTML discovery reads ordinary anchors plus bounded JSON component links from
  `data-*` attributes and non-executable `application/json` or
  `application/ld+json` scripts. The same official-domain and product-boundary
  checks apply to every recovered URL. Parser version `fpds-parse-chunk-v4`
  also retains bounded component/script text as `structured_component`
  evidence when the visible HTML shell hides the product copy, and preserves
  accessible Check/X values used as boolean cells in comparison tables
- A bounded exact-product attribute such as `data-cardDescriptionUrl` is kept
  ahead of ordinary navigation when the global link cap is reached. Known
  public AEM content-tree aliases are converted to their canonical public path;
  the recovered URL still passes the ordinary official-domain, locale,
  Product-Type, page-evidence, and action-flow boundaries.
- Admin discovery now excludes unresolved `multi_product_family_overview`,
  `hub_page_not_detail` and verified-coverage Review exceptions before new
  candidate-producing source materialization (D-086). Validation still routes
  any historical/direct candidate carrying those reasons to Review, with
  `verified_coverage_lending_review_source` equivalent. Canonical and publication
  gates remain fail-closed; newly found missing facts still require Review.
- an HTTP 403, a direct timeout/connection-close failure, or a high-confidence
  HTTP-200 JavaScript/access-challenge shell from an already SSRF-validated,
  allowlisted official HTML source receives one bounded headless-browser
  attempt regardless of bank or Product Type. Generic transport recovery uses
  browser DOM so the result remains ordinary inspectable HTML. A
  rendered page that remains a challenge is rejected as product evidence and
  is held before new catalog ingestion-run creation (D-089); legacy in-flight
  plans retain their quarantine behavior. A missing browser or render failure
  remains transient. Other HTTP/upstream browser
  fallback remains restricted to configured domains. Browser recoveries are
  serialized within one worker so concurrent source capture does not retrigger
  the same institution's WAF. A source declared as PDF must still return PDF
  bytes; a recovered HTML viewer or challenge shell is rejected before storage
- market defaults are country-owned (`CA -> CAD`, `US -> USD`); an unknown
  country remains explicit instead of silently inheriting CAD
- savings subtype inference compares the candidate currency with that country
  default, so a US/USD account is domestic while a CA/USD account is foreign
  currency
- savings normalization treats an explicit APY product header as the ongoing
  rate even when a later referral offer appears in the same document. An
  incremental APY rate boost is omitted from the total promotional-rate field
  unless a resulting total is stated, and comparison-calculator balances and
  assumptions are excluded from product terms
- product-title extraction prefers high-confidence official location-gated
  page identity and removes SEO action suffixes while rejecting legal
  documents, enrollment CTAs, calculators, and other non-product headings
- configured OpenAI collection runs apply one official-domain grounding pass to
  every candidate-producing `detail` source, including the standard Product
  Types. The pass receives the full active field contract and may replace or
  supplement a field only when the provider actually consulted an allowlisted
  official URL and the model returns an exact quote from the freshly captured
  evidence chunk. Supporting sources remain evidence-only, and provider
  unavailability falls back to the existing heuristic extraction path. A
  co-located labeled currency fee may be grounded directly from a verified,
  identity-matched official detail snapshot only when the origin belongs to an
  explicitly configured bank-domain allowlist. A qualified lending rate summary
  and its amount/limit/term/rate-type companions may use the same path only when
  their value and qualifying context are co-located in that snapshot; scalar
  rates and general prose do not use this fallback.
- dynamic/lending extraction is limited to the registered Product Type field
  contract. Ungrounded lending attributes are omitted instead of publishing
  heuristic feature copy.
- descriptive-field extraction rejects adjacent service and disclosure copy:
  payment-service enrollment terms are not product application or eligibility,
  linked-account fee-waiver lists are not customer eligibility, and investment
  risk disclaimers are not deposit insurance.
- current Deposit and Lending collection resolves identity plus comparison
  essentials from the versioned `(country_code, product_type)` profile in
  `fpds_market_profile.py`. Canada Chequing accepts an explicit non-balance
  fee waiver when a positive-fee product has no balance waiver, and accepts an
  explicit product-wide transaction fee when no included/unlimited count
  exists. Canada otherwise retains fee/balance/transaction Chequing and
  rate/term/deposit/redeemability GIC semantics. US Checking uses fee,
  opening/minimum balance, and a conditional fee-waiver/qualifying-activity
  fact. US Savings additionally requires a complete waiver for a positive fee
  and an assumption-preserving summary for conditional APYs; US CDs use APY/rate schedule, term, opening deposit, and quantified
  early-withdrawal penalty; US Mortgage requires an assumption-bearing
  percentage rate/APR summary, rate type, and term. US Credit Card and Line of
  Credit also have explicit market ownership even where today's required facts
  match Canada's current minimums. An explicitly named new country fails closed
  until its profiles are registered; only country-less legacy calls retain the
  Canada baseline. Unknown Product Types fail closed on a registered
  rate-plus-decision contract.
- Country scope also applies to URLs, not only database rows. Explicit
  other-market paths/locales, subdomains, and country-code TLDs are excluded
  from entry, seed, detail, and supporting evidence even when both markets use
  the same official parent domain. Language-specific hosts and paths are
  removed before bounded candidate selection, and Review AI applies the same
  country/language boundary to consulted official sources.
- Supporting-source planning is bounded before fetch to exact-product
  descendants/companions, Product-Type-compatible rate/APR pages, and relevant
  essential-fact FAQs/disclosures. Educational, servicing, application,
  transfer, investment, sibling-product, and conflicting Product-Type routes
  are excluded. Collection official grounding v2 rejects ellipsized quotes,
  requires every proposed number in the quote, and requires complete waiver,
  penalty, security, and qualified-rate prose rather than model extrapolation.
- Selected exact-product details may add at most two directly linked official
  pricing/fee/agreement companions, with a 48-source scope cap. Offer,
  document, product, and market query keys are retained as source identity;
  campaign and presentation keys are discarded. Browser fallback covers the
  registered US dynamic pricing domains and structured JSON extraction keeps
  APY/APR/rate and fee keys that are not rendered as ordinary visible text.
- dynamic/lending candidates must verify official product identity and `100%`
  of the selected essential facts. Optional marketing or operational fields are
  outside collection and Review by default. A partial-source or legacy
  confidence warning alone does not block a complete candidate; missing,
  contradictory, invalid, or ambiguously mapped essentials remain Review-bound.
  When multiple fields are alternatives for one requirement, Review AI checks
  only the preferred satisfied or missing field for that requirement; redundant
  populated alternatives do not add approval blockers.
- APR ranges, reference-rate formulas, and representative mortgage examples
  stay in `interest_rate_summary` with their disclosed assumptions instead of
  being collapsed into a misleading scalar. Review repair prefers that summary
  and explicit security prose before scalar rate/boolean alternatives. Unknown
  dynamic types fail closed
  until their registry defines a percentage field plus another decision field.
- US Personal Loan and vehicle-loan representative APR examples also retain
  any official model-year/vehicle-age, LTV, down-payment, credit,
  origination-fee, rate-change, relationship/autopay-discount qualification,
  and existing-customer assumptions; omission is Review-bound.
- masked/template financial values (`X.XXX%`, `$XXXX`, unresolved RDS/rate
  tokens) never satisfy comparison quality. A textual rate summary needs a
  concrete percentage adjacent to Rate, APR, APY, or an explicit reference-rate
  label; unrelated percentages such as down payment, transaction/conversion
  fees, or ATM/ABM assessment fees do not count.
- savings supporting fallback requires a local Interest Rate/APY label or
  structured rate-table header. Tiered savings stores the first balance that
  earns the selected Public rate, and an ongoing qualification-based Boosted
  Rate is not mislabeled as a bounded promotional rate.
- Flattened account-fee rows may carry a footnote number and a currency marker
  between an exact Transaction Fee label, amount, and `each`; that bounded
  layout is still parsed as a per-transaction fee.
- AI-grounded comparison prose uses field-specific safe bounds. Fee-waiver,
  penalty, tier, and qualified-rate text is retained as a complete condition or
  omitted for Review; it is never blindly sliced mid-word or mid-clause.
- country-specific Public projections retain only the resolved comparison
  fields plus identity, status/freshness, and official product link. Broader
  normalized copy remains private for Admin evidence and review traceability.
- credit-card projection is enabled through the same completeness gate and
  retains annual fee plus purchase interest rate for Public card list,
  comparison, and detail. US Purchase APR ranges retain their exact disclosed
  range and material creditworthiness/variable-rate qualification in
  `purchase_interest_rate_summary`; the qualified summary is the governing US
  card essential, and a scalar lower bound cannot replace it.
- Fixed card-rate fallback accepts only an exact adjacent field label and
  percentage. This includes `Interest: Purchases` and `Interest: Cash
  Advances`; purchase, cash-advance, and balance-transfer labels remain
  distinct so a nearby 22.99% cash rate cannot populate the purchase rate.


## Deposit comparison conditions (2026-09-24)

The [deposit comparison policy](../docs/03-design/public-deposit-comparison-policy.md) supersedes headline-only Savings/GIC
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

See the [bounded CA/US audit and correction report](../docs/00-governance/public-collection-alignment-2026-09-29.md) for six applied
existing-product repairs, preserved verification dates, remaining gaps and the
read-only `scripts/maintenance/public_collection_gap_report.py` command.

D-089 validates every browser HTML fallback result, including HTTP 403/429
paths, for a remaining managed-access challenge. Cloudflare blocked-page
signatures need both explicit blocked text and vendor markers; ordinary product
copy mentioning access does not trigger a hold. This uses the existing bounded
browser attempt and does not add a challenge bypass or expand allowed domains.
