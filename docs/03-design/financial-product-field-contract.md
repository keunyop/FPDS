# Financial Product Field Contract

Status: Active
Last updated: 2026-07-23

## Purpose

FPDS compares products across banks only when a field has the same meaning, JSON type, and unit everywhere. Collection must retain source context without placing prose inside a comparable scalar value.

The executable contract is `worker/pipeline/fpds_field_contract.py`. Database product-type definitions and Admin review serialization expose the same contract metadata.

## Comparable Value Contract

| Field class | JSON type | Canonical unit or shape | Example |
|---|---|---|---|
| annual rate | number | percentage points per annum | `3.3` means 3.30% p.a. |
| money | number | product currency | `100.0` |
| count or duration | integer | field-specific count or days | `365` |
| yes/no characteristic | boolean | `true` or `false` only | `true` |
| descriptive value | string | concise source-grounded text | `Non-redeemable` |
| term-rate schedule | array | rows with typed term and numeric `rate` | `[{'term':'1 year','rate':3.3}]` |
| tags or methods | array | strings | `['online']` |

Numeric rate fields must never contain a sentence, a term table, a prepayment percentage, a withdrawal percentage, cashback, down payment, equity, or loan-to-value value. Money fields must not contain currency prose. Boolean fields must not contain `yes`, `no`, or explanatory text.

## Field Notes

When a comparable value needs qualification, the candidate stores the scalar or structured value in its normal field and stores the explanation in `field_notes.<field_name>`. The Admin review detail displays this as a field-level footnote.

Typical notes identify:

- annual-rate units and whether a rate is a representative term;
- the source and interpretation of a term-rate table;
- fee-waiver conditions;
- minimum-deposit currency or scope;
- variability, eligibility, or other conditions that affect interpretation.

A note does not replace evidence. `field_evidence_link` must still point to the exact supporting source document used for that field.

## Evidence and Merge Rules

1. Prefer product-detail evidence for identity and product conditions.
2. Use official rate, fee, or governing pages as supporting sources when the detail page delegates facts to them.
3. Merge only evidence that matches the bank, product family, product type, and product boundary.
4. Reconstruct split structured tables from a bounded set of relevant evidence chunks, then deduplicate identical rows.
5. Reject cross-product navigation, nearby product tables, calculators, unresolved templates, marketing percentages, and service-fee waivers that do not describe the product field.
6. Preserve the supporting source document id on every merged field link.
7. If an official value is unavailable or genuinely ambiguous, omit it and route the candidate to review; do not infer it.
8. For term-rate tables, support both adjacent `term -> rate` and `rate -> term` layouts and select the orientation with more complete grounded pairs; never shift a rate from one row onto the next term.
9. A page containing multiple named product sections is not one canonical product. Preserve its evidence for review, mark the product boundary ambiguous, and do not publish a composite candidate.
10. A promotion with an explicit end date earlier than the collection date is historical evidence, not a current rate. Remove its rate fields before merging a current official rate source; if no current value is available, omit the rate and route to review.
11. Supporting merge is missing-value-only after unsafe or expired detail values are removed. Current official rate evidence may replace an expired detail-page promotion, but it must not silently replace a different current product value without a boundary-safe rule.
12. Extraction artifacts used for a normalization run must belong to that same `run_id`; a failed current source must never fall back to an older successful extraction as if it were current evidence.
13. Fields whose evidence anchor identifies another-products or related-products content are cross-product context and must be omitted, including boolean or structured fields that are not caught by prose cleanup.
14. Credit-card fees and fixed rates require an adjacent matching label. Secondary/additional-card fees are not the primary annual fee; unresolved template values and variable `prime + margin` expressions remain omitted unless the contract gains a typed variable-rate representation.
15. A current official GIC family table may declare `%` once in its column heading instead of after every value. Parse only a bounded GIC-rate section, prefer the annual column for the canonical one-year comparison rate, preserve variant context in term-row notes, and leave `term_length_days` empty for duration ranges such as `30-59 days`.
16. Evidence rejected as expired, cross-product, or semantically mismatched cannot be reintroduced by a later generic fallback in the same normalization pass.
17. A scalar term duration must equal a duration explicitly stated by the evidence. When text publishes a range, a numeric duration may match a declared boundary but must never reinterpret months as days or select an unrelated guarantee period.
18. Application fields must describe the current product. Government-aid instructions, business-account opening actions, adjacent vehicle-loan actions, and other section-scoped CTAs are omitted when their evidence identifies a different product or service.
19. Security and collateral fields require explicit security semantics such as secured, unsecured, collateral, guarantor, lien, pledge, or down payment. A product heading or marketing slogan is not evidence that a product is secured or unsecured.
20. A list of available interest-payment or payout frequencies cannot become one scalar option. Preserve a single value only when the evidence states that value as the governing choice for the product; otherwise omit it or use a future typed multi-option field.
21. A promotion's `valid until`, end, or expiry date is not the product's `effective_date`. Until an explicit offer-end field is part of the canonical contract, omit that date rather than changing its meaning.
22. A field excerpt that explicitly names another bank product cannot populate the target candidate unless the same bounded excerpt also identifies the target product. Once a document title is derived, use that title as the target identity for all remaining field extraction.
23. Percentage safety classification must retain enough bounded surrounding copy to keep scenario, index, cumulative-return, fee, principal-access, and fund-performance semantics attached to the percentage. The same context rule applies to direct extraction, normalization fallback, and supporting merge.
24. For savings and GIC products, `public_display_rate` cannot be lower than a grounded `standard_rate` or `promotional_rate`. When legal copy exposes a bonus component separately from the total promotional rate, the public display follows the grounded total; unresolved disagreement is `inconsistent_cross_field_logic`.
25. If normal field retrieval misses a core fee or finite transaction count that is present in the parsed detail source, a bounded evidence-wide fallback may recover it only from strong labels such as `monthly account fee` or explicit monthly/debit transaction count language. Conditional zero offers, durations, balances, and named adjacent products remain ineligible.
26. When a current official GIC rate section publishes the same minimum deposit for the included variants, place it on each applicable term row and expose the common scalar `minimum_deposit`; do not borrow a registered-plan minimum from another section. Explicit phrases such as `start with as little as` are valid minimum-deposit evidence when they describe the product's opening amount.
27. A percentage candidate is grounded only when its exact numeric token appears with a percent sign in the linked evidence excerpt. Dynamic-template residue, an adjacent percentage, or a value inferred from another chunk is omitted rather than normalized into a publishable scalar.
28. A time-limited or eligibility-limited advertised total rate belongs in `promotional_rate` and may be the `public_display_rate`; it is never the `standard_rate`. When official terms separately publish regular and promotional components, preserve the advertised total as the promotion and the regular component as the standard rate. An ongoing conditional bonus without an offer period is not automatically a promotion; when the source explicitly states regular plus extra ongoing bonus, public display may use their grounded sum without setting `promotional_rate`.
29. `monthly_fee` and `public_display_fee` are two views of the same base monthly charge. If both are present they must agree. Conditional waivers, caps, maximum charges, transaction fees, and another product's fee cannot supply either scalar.
30. Product currency requires explicit product or rate-table evidence. Foreign-currency identities such as USD, EUR, GBP, or HKD override the collection-country default; an unspecified currency remains reviewable rather than being guessed from nearby navigation. Currency-amount parsing accepts official dollar, euro, and pound symbols while retaining the separately inferred product currency.
31. Source-profile extensions ending in `*_rate` or `*_fee` use the same numeric percentage-point or currency-amount contract as canonical rates and fees, unless an explicit canonical string contract applies. A bounded fallback may recover one only when the requested field's own label is adjacent to the exact value; it must not persist the surrounding evidence paragraph as the field value.
32. When an official term table publishes nominal `Rate` and `APY` columns in parallel, comparable annual term rows use the explicitly labelled APY column and preserve `APY` in row notes. Do not mix the nominal column in `term_rate_table` with an APY headline or public display.
33. Audience-specific onboarding or immigration programs on a general product page cannot populate the general product's eligibility unless the candidate identity itself names that audience/program.
34. A detail-source seed may add useful requested fields but cannot narrow the current Product Type field contract. Collection requests the union of seed fields and the active baseline so legacy discovery metadata cannot silently omit decision fields.
35. When shared legal text states registered and non-registered promotions in parallel, `promotional_period_text` must come from the sentence whose registered scope matches the target product. Preserve the applicable total rate and period together; do not attach a registered period to a non-registered product or the reverse.
36. `withdrawal_limit_text` requires an actual access constraint such as a count, cost, availability restriction, maximum, or minimum. Calculator assumptions, tax treatment, and cross-product navigation are not withdrawal limits. Tax-benefit text must likewise describe the target product type rather than a sibling GIC, savings account, or plan.
37. A base monthly fee shown as `$X or $0` with a balance condition remains `$X` in `monthly_fee` and `public_display_fee`; the balance-qualified zero belongs in `fee_waiver_condition` and `minimum_balance`.
38. Audience booleans and customer tags require the target product identity itself to name the audience; related audience benefit sections on a general account page are cross-product support copy. Finite transaction parsing may ignore bounded HTML footnote glyphs, and `minimum_balance` must equal the positive threshold stated by its grounded `fee_waiver_condition` or validation must review the candidate.
39. Chequing collection requests `transaction_fee` as a currency scalar in addition to the monthly fee. A product-wide per-transaction charge may be stored only from its own adjacent transaction-fee label; balances or audience rules that waive that charge or the monthly fee remain explanatory conditions and cannot replace the base scalar.
40. Review Detail AI verification may propose a correction only when a current official source from the registered bank domain supports the exact field and the value passes the same manual-override coercion and range checks. Unsupported or ambiguous facts remain `unverified`, and verification never guesses or publishes by itself. A verification attempt does not directly approve a candidate; the separate audited assessment in rule 43 may authorize system approval only after its identity, coverage, source, and safe-correction gates all pass.
41. Configured collection applies official-domain AI grounding to every
    candidate-producing detail source, including standard Product Types. The
    model receives the exact product identity, complete active field contract,
    current collected values, and bounded fresh evidence chunks. A grounded
    value may replace or supplement extraction only when the cited URL appears
    in the provider's consulted allowlisted sources and an exact returned quote
    exists in the selected evidence chunk, then passes the canonical type and
    numeric safe-range checks used by review edits. Supporting pages remain
    evidence-only; provider failure keeps the deterministic extraction result
    and normal validation/review routing.
42. Dynamic/lending auto-validation requires a persisted collection grounding
    assessment. `product_name`, at least one additional decision field, and at
    least `80%` of assessed priority/typed fields must carry accepted official
    grounding metadata. This eligibility does not remove requiredness,
    confidence, force-review, source-role, or product-boundary checks.
43. Collection residual-review automation uses the full requested Review field
    set as its denominator. Only official matches and successfully applied safe
    mismatches pass; unverified or omitted fields fail. Verified identity, at
    least one official source, no unapplied correction, and `>=80%` are required
    for system approval.

## Runtime Validation

Normalization coerces unambiguous scalar representations into the canonical type. Compound rate prose is redirected into `term_rate_table` when it can be parsed safely. Validation emits `invalid_field_type` when a value remains incompatible with the field contract.

Manual Admin overrides use the same coercion and rejection rules, including typed booleans, non-negative money/count/duration values, bounded deposit rates, and arrays for list fields. Canonical continuity is based on stable bank, family, type, and product identity so a subtype correction does not create a duplicate product.

Static Golden profiles are test fixtures only. They may be enabled explicitly with `product_profile_expansion_mode=fixture`; they cannot overwrite live collection facts or bypass validation.

## Verification Baseline

Each new false-positive or merge failure class requires a regression test. Representative Admin-path recollection must then verify:

- values and schedules against current official sources;
- JSON types against the executable contract;
- evidence links against the source actually used;
- reviewer-visible field notes;
- safe review routing for facts the source did not publish accessibly.
