# Worker Boundary

This directory holds private pipeline and integration workers.

Current boundary:
- `discovery/` for source discovery and registry-driven fetch entry
- `pipeline/` for parse, chunk, extraction, normalization, validation, and review routing work
- `publish/` for BX-PF-facing publish and reconciliation work
- `runtime/` for worker bootstrap, scheduling, and execution plumbing

Current implementation slices:
- `WBS 3.1` source discovery, preflight drift checks, and scheduled refresh artifacts in `worker/discovery/`
- `WBS 3.2` snapshot capture and persistence in `worker/discovery/fpds_snapshot/`
- `WBS 3.3` parse/chunk pipeline in `worker/pipeline/fpds_parse_chunk/`
- `WBS 3.4` evidence retrieval in `worker/pipeline/fpds_evidence_retrieval/`
- `WBS 3.5` extraction flow in `worker/pipeline/fpds_extraction/`
- `WBS 3.6` normalization mapping in `worker/pipeline/fpds_normalization/`
- `WBS 3.7` validation/confidence routing in `worker/pipeline/fpds_validation_routing/`
- `WBS 3.8` result-viewer payload export in `worker/pipeline/fpds_result_viewer/`

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
- validation treats both deterministic `multi_product_family_overview` and AI
  `hub_page_not_detail` discovery evidence as an ambiguous product boundary;
  either condition routes a candidate to Review rather than auto-validating a
  family page as one product
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
  `fpds_market_profile.py`. Canada retains fee/balance/transaction Chequing and
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
  the same official parent domain.
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
- APR ranges, reference-rate formulas, and representative mortgage examples
  stay in `interest_rate_summary` with their disclosed assumptions instead of
  being collapsed into a misleading scalar. Unknown dynamic types fail closed
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
  comparison, and detail rendering.
