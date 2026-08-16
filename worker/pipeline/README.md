# Pipeline Worker Area

Use this area for ingestion pipeline stages after discovery.

Current scope:
- `fpds_parse_chunk/` implements `WBS 3.3` parsed text generation, chunk creation, parsed artifact storage, and DB persistence
- `fpds_evidence_retrieval/` implements `WBS 3.4` metadata-only candidate chunk retrieval with field-aware scoring and DB reads
- `fpds_extraction/` implements `WBS 3.5` sparse extracted draft generation, extracted artifact storage, and bounded `model_execution` persistence
- `fpds_normalization/` implements `WBS 3.6` canonical candidate mapping, `normalized_candidate` persistence, `field_evidence_link` persistence, and normalized artifact storage
- `fpds_validation_routing/` implements `WBS 3.7` candidate validation recheck, confidence recomputation, prototype review-task routing, and validation artifact storage
- `fpds_result_viewer/` implements `WBS 3.8` read-only prototype viewer payload export from persisted run, candidate, and evidence rows
- `fpds_aggregate_refresh/` implements `WBS 5.6` the retained aggregate source dataset in `public_product_projection`; dashboard metrics, rankings, and scatter are derived from it at read time

Planned follow-on scope:
- canonical upsert and change assessment
- publish preparation

Big 5 source-id note:
- when `--registry-path` is omitted, worker CLI stages that resolve `--source-id` now use the committed registry catalog, so `TD-*`, `RBC-*`, `BMO-*`, `SCOTIA-*`, and `CIBC-*` `chequing`, `savings`, and `gic` source ids can run without switching the default TD savings registry file by hand

Run parse/chunk against stored snapshots in dev:

```powershell
python -m worker.pipeline.fpds_parse_chunk `
  --env-file .env.dev `
  --persist-db `
  --run-id run_20260410_3301 `
  --source-id TD-SAV-002 `
  --source-id TD-SAV-004 `
  --source-id TD-SAV-007 `
  --source-id TD-SAV-008
```

Run evidence retrieval against stored parsed documents in dev:

```powershell
python -m worker.pipeline.fpds_evidence_retrieval `
  --env-file .env.dev `
  --run-id run_20260410_3401 `
  --source-id TD-SAV-007 `
  --field-name monthly_fee `
  --field-name fee_waiver_condition
```

`0040_bounded_operational_storage.sql` removes the historical pgvector side
table. Use metadata-only retrieval; the field-aware metadata scorer is the
correctness baseline and does not duplicate every evidence chunk.

Run extraction against stored parsed documents in dev:

```powershell
python -m worker.pipeline.fpds_extraction `
  --env-file .env.dev `
  --persist-db `
  --run-id run_20260410_3501 `
  --source-id TD-SAV-002 `
  --source-id TD-SAV-007
```

Run normalization against the latest extraction artifacts in dev:

```powershell
python -m worker.pipeline.fpds_normalization `
  --env-file .env.dev `
  --persist-db `
  --run-id run_20260410_3603 `
  --source-id TD-SAV-002 `
  --source-id TD-SAV-007
```

Run validation/routing against the latest normalization artifacts in dev:

```powershell
python -m worker.pipeline.fpds_validation_routing `
  --env-file .env.dev `
  --persist-db `
  --run-id run_20260410_3701 `
  --source-id TD-SAV-002 `
  --source-id TD-SAV-007
```

Export a run into the prototype viewer payload in dev:

```powershell
python -m worker.pipeline.fpds_result_viewer `
  --env-file .env.dev `
  --run-id run_20260410_3701
```

Run aggregate refresh against the current canonical dataset in dev:

```powershell
python -m worker.pipeline.fpds_aggregate_refresh `
  --env-file .env.dev `
  --persist-db `
  --snapshot-id agg_20260413_5601 `
  --country-code CA
```

What `WBS 3.5` stores today:
- extracted draft JSON artifact per parsed document in object storage
- metadata JSON artifact with counts and storage references
- `model_execution` row per source extraction attempt
- no persisted zero-token usage row; heuristic execution state is already represented by `model_execution`
- updated `run_source_item.stage_metadata` for extraction status and artifact linkage

Current boundary:
- this stage produces source-level sparse drafts, not `normalized_candidate`
- `field_evidence_link` rows are still deferred because they require `candidate_id` or `product_version_id`
- the extraction baseline now includes product-type-specific canonical fields for `chequing`, `savings`, and `gic`, including transaction bundle signals, savings tiering or withdrawal text, and GIC term, redeemability, compounding, payout, and registered-plan support fields
- for canonical product types, source-registry `expected_fields` now stay bounded to extractable canonical fields so source-management hints such as rebates or discovery summaries do not become arbitrary candidate payload fields
- BMO chequing fee-waiver wording such as `$17.95 OR $0/month with min. $4,000 balance` now maps to monthly fee, public display fee, minimum balance, and fee waiver condition instead of treating `$0` as the base fee
- chequing extraction now keeps cheque text concise and treats student/newcomer flags as account-specific signals rather than generic cross-product navigation mentions
- BMO Practical Chequing extraction now keeps the `$4` monthly fee product-scoped and suppresses comparison-table waiver balances from Plus/Performance rows, generic cheque-deposit wording, and cross-product expected fields
- BMO Premium Chequing extraction is covered against comparison-table noise so `$30.95` monthly fee, `$6,000` minimum-balance waiver text, unlimited transaction signals, and concise cheque-book evidence stay product-scoped while savings/tier/withdrawal/student/newcomer/family-bundle noise is excluded
- BMO AIR MILES Chequing extraction now keeps AIR MILES comparison-table fee and minimum-balance text product-scoped, avoids using the generic word `plus` as a Plus-account boundary, and suppresses nav-only cheque/student/newcomer/interest noise
- generic BMO footer/navigation text such as `Important banking info` is suppressed before it can populate canonical fields such as notes or interest calculation method
- dynamic product extraction now suppresses obvious cross-product navigation chunks before deriving product titles or long-text fields, so `gic-term-deposit` candidates do not promote chequing or card menu text as product evidence
- operator-defined product extraction and normalization are bounded to the registered `expected_fields`; the AI may not introduce deposit aliases or unrelated fields into lending/card candidates, and percentage prompts explicitly separate interest rates from cashback, rewards, prepayment, equity, and down-payment values
- dynamic AI extraction is limited to candidate-producing detail sources; entry, supporting HTML/PDF, and linked-PDF sources remain evidence-only and use deterministic extraction, reducing latency and preventing support-page prose from being treated as a standalone product draft
- all comparable fields use the executable cross-bank type and unit contract in `fpds_field_contract.py`; annual rates are numeric percentage points, money is numeric in product currency, flags are booleans, and term-rate schedules are structured arrays
- source-profile numeric extensions such as `regular_interest_rate`, `smart_interest_rate`, and `transaction_fee` follow the same typed rate/money contract; exact-label evidence-wide recovery may fill a missed value but cannot substitute a nearby rate, fee, or evidence paragraph
- term-rate extraction evaluates adjacent `term -> rate` and `rate -> term` row orientations, chooses the more complete grounded pairing, and resolves ties from the first term/rate order in the document so duplicated rendered values cannot shift every rate onto the next term. When parallel `Rate` and `APY` headers are explicit, comparable rows use APY and retain that qualifier in row notes
- withdrawal, redemption, encashment, and prepayment percentages are rejected as annual rates, while overdraft service-fee waivers and cross-product audience or navigation mentions are rejected as account facts
- flattened account-fee rows now recognize footnote-separated `Transaction Fee ... $X each` and `Additional Transactions ... $X each` values, while explicit multi-step qualification evidence outranks a nearby promotional summary

What `WBS 3.6` stores today:
- normalized candidate JSON artifact per source candidate in object storage
- metadata JSON artifact with candidate id, validation status, and confidence
- `normalized_candidate` row per source candidate
- `field_evidence_link` rows tied to `candidate_id`
- bounded `model_execution` rows for normalization; no usage ledger row
- updated `run_source_item.stage_metadata` for candidate id and normalization results
- for selected savings products, missing rate fields can now be supplemented from product-matched supporting rate-page artifacts when available: `TD-SAV-005`, `BMO-SAV-006` for BMO Savings Amplifier, Savings Builder, and Premium Rate Savings, and `SCOTIA-SAV-006`
- for the TD Savings prototype, noisy `interest_calculation_method` fields can now be replaced with stronger `TD-SAV-008` governing-PDF wording when the detail-page extraction only captured PDF link text
- for the TD Savings prototype, `TD-SAV-007` fee-governing evidence can now suppress misleading `fee_waiver_condition` values for zero-monthly-fee savings products instead of persisting raw fee-table text
- `TD Growth` qualification text is now split more deliberately into `eligibility_text`, `boosted_rate_eligibility`, and `promotional_period_text`
- clearly noisy long-text fields such as generic notes, marketing promo copy, and fee-at-a-glance snippets can now be suppressed before canonical candidate persistence
- chequing subtype inference now aligns to the approved taxonomy: `standard`, `package`, `interest_bearing`, `premium`, `other`
- normalization and validation now also align GIC term and redeemability rules at candidate creation time so missing deposit or term values, invalid term lengths, and conflicting redeemability flags are surfaced before review routing
- shared candidate cleanup now removes wrong-type flag values, unresolved template tokens, duplicated/whole-page field copy, short `Document ...` navigation labels, payment-frequency values misused as interest frequency, and numeric term values that conflict with the published term text
- lending cleanup also removes account-fee text mapped as loan payments or fees, short multi-marker navigation mapped as security, prose-only loan amounts, and product titles mapped as prepayment privileges; the same rules are surfaced in Review diagnosis for already-persisted candidates
- lending cleanup also requires concise duration-shaped amortization values, actual periodic payment-frequency values, and concise prepayment terms; removes calculator/estimate output from eligibility; and suppresses numeric rate fields when their own evidence is an unresolved template or describes cashback, prepayment, equity, down payment, or loan-to-value instead of interest
- lending cleanup requires `minimum_payment_text` to contain actual payment, repayment, minimum-payment, or interest-only semantics, so a product/category heading cannot survive as an operator-facing repayment term
- lending cleanup now requires evidence-backed security semantics, rejects adjacent-product and government-program application CTAs, and suppresses marketing copy mapped as repayment or eligibility; a scalar term duration must match a duration stated in the source instead of falling numerically somewhere inside a published range
- GIC cleanup removes term scalars backed only by an expired promotion, does not collapse a list of payment/payout options to one value, rejects rate cards mapped as customer eligibility, and carries a common current minimum deposit into applicable official term-table rows
- promotion end dates are not stored as product `effective_date`; `valid until`, expiry, and offer-end evidence stays omitted until the canonical contract provides a distinct field
- GIC rate fallback rejects account/direct-deposit percentages from navigation or footer evidence, and footer/company navigation is not accepted as deposit-insurance evidence
- percentage fallbacks use one shared bounded context window across extraction, normalization, and supporting merge so market scenarios, cumulative/index returns, fees, principal-access percentages, and fund performance cannot lose their governing semantics near a percentage
- savings/GIC normalization aligns `public_display_rate` to at least the grounded regular or promotional rate and validation rejects a lower display value; a legal-example bonus component therefore cannot replace the official total promotional rate
- after ordinary retrieval, evidence-wide recovery may fill only strongly labelled monthly account fees and explicit finite monthly/debit counts. It retains conditional-zero, duration, balance, and named-other-product guards and links the recovered field to the exact missed chunk
- derived product titles become the target identity for remaining fields; excerpts that explicitly name a different bank product are skipped unless the target is present in the same bounded evidence
- dynamic lending/card validation checks a concise product-type priority set instead of reporting every optional expected field as required; these candidates remain review-first and are never auto-published by this fallback
- extraction overlays selected registry metadata onto persisted source-document metadata so shared support URLs, such as BMO savings and chequing rate pages, keep the current run's product type and expected fields
- supporting official rate pages are ranked before the bounded source cap, and split GIC-family schedules can be reconstructed across a bounded set of relevant chunks while filtering savings or unrelated-product rows
- generic supporting merge maps horizontal comparison-table columns to the target product identity, keeps recurring fees separate from conditional zero outcomes and balance thresholds, preserves material balance-tier summaries, and supplements only explicit account-wide unlimited-transaction facts
- normalization reduces broad fee tables and repeated application controls to decision-ready transaction rules and channels, and removes audience cross-sells, switching-service CTAs, award copy, and incomplete fragments from product descriptions
- normalized candidates retain concise `field_notes` for qualified comparable values and preserve the actual supporting source document id on each merged `field_evidence_link`
- an identity-matched official Vancity card page may expand into multiple candidates only when each sibling product block independently binds its exact product name, annual fee, and purchase rate to the same bounded evidence chunk. The shared Vancity LOC page may likewise expand `Creditline` and `Personaline` only when one official table binds both names to their rate, limit, payment, and accessible Check/X security cells. Resolved variants replace the composite candidate; incomplete or mixed blocks remain unsplit and Review-bound
- the annual-deposit plausibility ceiling is scoped to deposit Product Types, so valid card, mortgage, personal-loan, and line-of-credit borrowing rates are not discarded as implausible deposit yields; the existing non-interest percentage and unresolved-placeholder guards still apply
- mortgage affordability and stress-test examples, including an OSFI Minimum Qualifying Rate, cannot ground a customer product rate; they stay contextual underwriting evidence rather than a comparable mortgage offer
- static Golden product profiles are fixture-only and require explicit `product_profile_expansion_mode=fixture`; live collection cannot use them to replace evidence or bypass validation

Current boundary:
- normalization now persists `normalized_candidate` and candidate-level evidence links
- supporting-source merge includes the original explicit TD, BMO, and Scotia rules plus a generic product-scoped deposit-family path for official detail/rate pages; it remains bounded by bank, family, type, source role, and product-boundary evidence
- canonical upsert, change assessment, and publish preparation still belong to later stages

What `WBS 3.7` stores today:
- validation/routing JSON artifact per source candidate in object storage
- discovery metadata marked `multi_product_family_overview` produces `ambiguous_product_boundary`, an error-level review route that prevents one normalized proposal from representing several distinct products
- metadata JSON artifact with candidate state, review reason, and review task id
- updated `normalized_candidate` validation fields and `candidate_state`
- validation routing treats dynamic-product runtime notes such as "no grounded product details" as `partial_source_failure`, preventing weak source captures from appearing as clean `pass` review tasks
- `review_task` row per prototype candidate with `queued` review state
- bounded `model_execution` rows for validation/routing; no usage ledger row
- updated `run_source_item.stage_metadata` for review queue linkage

Current boundary:
- Prototype routing mode sends every candidate to review even when validation passes
- review decisions, canonical upsert, and change history still belong to later stages

What `WBS 3.8` exports today:
- static viewer payload JSON and browser-consumable JS for `app/prototype/index.html`
- run summary, candidate summary, canonical payload, validation issues, and evidence excerpt data loaded from DB
- registry-backed `source_id` labels mapped back onto persisted candidate rows for operator readability

Current boundary:
- this is a read-only prototype viewer export, not the full admin review queue or trace viewer
- write actions, queue mutation, and deep trace drilldown remain deferred to later admin slices

What `WBS 5.6` stores today:
- one `aggregate_refresh_run` row per attempted snapshot
- flattened `public_product_projection` rows with the shared filter vocabulary and approved bucket codes
- no duplicate dashboard snapshot rows; API reads derive summary, ranking, and scatter payloads from the latest retained projection

Current boundary:
- this slice builds aggregate source datasets only; it does not implement the public products API, dashboard APIs, or public UI
- later public API work can now read from persisted aggregate rows instead of joining live canonical tables directly

Reliability note:
- DB-backed worker stages now run `psql` with `ON_ERROR_STOP=1` so SQL errors abort the stage instead of being reported as false-positive success
- extraction, normalization, and validation/routing resolve their required DB relations through `information_schema.tables`, which includes both base tables and the discard-only compatibility views retained by migration `0040`; a removed physical usage ledger therefore cannot make an otherwise valid runtime schema appear missing
- percentage fields now require their exact numeric `%` token in the linked evidence excerpt; market/index returns, fund metrics, FX/conversion percentages, calculator scenarios, and unresolved dynamic templates are omitted instead of becoming deposit rates
- rate extraction distinguishes regular, time/eligibility-limited promotional totals, and ongoing conditional bonus totals. Public display may use the grounded advertised total, while the standard field remains the regular rate and ambiguous components stay review-routed
- monthly/public fee values require direct base-fee wording and must agree when both are present; conditional waivers, maxima, transaction charges, and adjacent-product fees cannot be promoted into the monthly scalar
- foreign-currency product identity is carried into normalization rather than defaulting every Canadian source to CAD, and product-scoped field ranking prevents nearby product sections from lending their rate, fee, transaction, or term values
- dollar, euro, and pound fee/waiver amounts share the same numeric parser; separately worded balance waivers can recover both the base fee condition and threshold without turning the waived zero into the base fee
- an explicitly advertised promotional total can supplement an already-grounded regular rate, while an ongoing `regular + extra bonus` disclosure aligns public display to the grounded sum without misclassifying it as a time-limited promotion
- shared legal copy that publishes registered and non-registered promotions in parallel is selected sentence-by-sentence against the target product identity; a registered product cannot inherit a non-registered period and a standard or foreign-currency product cannot inherit a registered period
- withdrawal limits require actual constraint semantics such as a count, fee, availability restriction, maximum, or minimum; calculator assumptions, tax explanations, and cross-sell prose mentioning withdrawals are not product limits
- a recurring fee disclosed as `$X or $0` with a minimum daily account balance keeps `$X` as the comparable fee and records the zero as a waiver condition plus balance; legacy seed field hints cannot prevent those contract fields from being requested
- audience flags require the target page/product identity to name that audience; related student, newcomer, senior, or trades sections on a general account page cannot tag the base product. Footnote glyphs between a finite transaction count and `included each month` are tolerated, and a fee-waiver balance scalar is aligned to its explicit positive threshold

Run all worker tests:

```powershell
python -m unittest discover -s worker -t .
```
