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
    model receives authoritative discovery identity candidates, the registered
    active field contract, current collected values, and bounded fresh evidence
    chunks. The discovered `product_name` is tentative until official grounding
    confirms or corrects it; a feature heading must not outrank a corroborated
    detail-page title/H1. A grounded
    value may replace or supplement extraction only when the cited URL appears
    in the provider's consulted allowlisted sources and an exact returned quote
    exists in the selected evidence chunk, then passes the canonical type and
    numeric safe-range checks used by review edits. Supporting pages remain
    evidence-only; provider failure keeps the deterministic extraction result
    and normal validation/review routing. A deterministic currency-fee fact may
    carry the same grounding contract without a provider citation only when
    its own field label and value are co-located in one fresh evidence chunk,
    the source is an identity-matched high-confidence `detail` page with no
    negative page signal, the field belongs to the active Product Type
    contract, and the origin URL matches an explicitly configured official
    bank-domain allowlist. The same origin rule may preserve a lending
    `interest_rate_summary`, `loan_amount_text`, `credit_limit_text`,
    `term_length_text`, or mortgage `rate_type` only when the value and its
    qualifying context are co-located in that verified detail-page excerpt.
    Scalar lending rates, inferred prose, unlabeled numbers, supporting pages,
    and a domain inferred only from the fetched URL remain outside this
    exception.
42. Dynamic/lending auto-validation requires a persisted collection grounding
    assessment. `product_name` and one selected field for every mandatory
    comparison requirement (`100%` of that bounded set) must carry accepted
    official grounding metadata. A missing optional marketing fact is an
    omission; a missing mandatory comparison fact is a validation error. A
    lending value without the
    accepted grounding metadata is removed before validation rather than
    published as heuristic copy. This eligibility does not remove confidence,
    force-review, source-role, type/range, or product-boundary checks.
43. Collection residual-review automation uses an approval-field set as its
    denominator: verified `product_name` plus one selected field for every
    mandatory comparison requirement. Empty optional marketing and operational
    fields are excluded even when older registry rows still list them. Only official
    matches and successfully applied safe mismatches pass; an unverified
    approval field fails. At least one official source, no unapplied correction,
    no unresolved hard blocker (`ambiguous_product_boundary`,
    `invalid_taxonomy_code`, invalid type/range/term, evidence conflict,
    ambiguous mapping, or inconsistent cross-field logic), and `100%` are
    required for system approval. A partial-source or confidence warning alone
    is non-blocking once the essentials pass. Older assessment contracts are not
    reused under this contract. When Review AI abstains with `unverified`, an
    unchanged currency fee or qualified lending comparison field may reuse the
    persisted exact-origin grounding from rule 41 after the registered-domain
    check; an AI `mismatch` cannot use this fallback.
44. Product identity may use persisted origin evidence when Review AI returns
    only `unverified`: the source must be an official detail page, discovery
    must record `product_identity_match=true`, and the candidate name must equal
    the primary H1 after Unicode, case, punctuation, and trademark-symbol
    normalization or differ only by a trailing descriptor registered for that
    Product Type (for example, `Credit Card`). An AI `mismatch`, missing H1,
    an unrelated marketing suffix, non-detail source, or a
    checking/savings composite cannot use this identity fallback. A separate
    official fact is still required for dynamic/lending auto-approval.
45. Deposit rate and subtype semantics are market-relative and evidence-local.
    Domestic currency comes from the candidate country rather than a global CAD
    assumption. A labeled ongoing APY remains `standard_rate` when a separate
    referral offer exists later in the page. An incremental `rate boost` is not
    a total `promotional_rate` without an explicit total, and comparison-
    calculator balances or assumptions are omitted from product terms.
46. Descriptive fields remain scoped to the current financial product. Payment-
    service enrollment and purchase disclaimers cannot populate
    `application_method` or `eligibility_text`; a list of linked accounts that
    qualifies for a fee waiver is not customer eligibility; and an investment-
    product "not FDIC insured / not a deposit" disclaimer cannot populate
    `deposit_insurance`. These exclusions are semantic and apply across banks
    and Product Types.
47. Comparison-grade lending approval is independent of the percentage score.
    Credit cards require `annual_fee` and a purchase-rate requirement. The US
    profile prefers percentage-bearing `purchase_interest_rate_summary` and
    permits an exact fixed `purchase_interest_rate` only as an alternative;
    Canada retains `purchase_interest_rate`. Mortgages
    require `mortgage_rate` or a percentage-bearing `interest_rate_summary`,
    plus `rate_type` and `term_length_text`; personal loans require
    `interest_rate` or a percentage-bearing APR/rate summary, plus
    `loan_amount_text` and `term_length_text`; lines of credit require a numeric
    rate or percentage-bearing rate/formula summary plus `credit_limit_text`.
    APR ranges, reference-rate formulas, and representative examples retain
    their source-language assumptions in `interest_rate_summary` rather than
    becoming one scalar. An unknown dynamic type fails closed until expected
    fields provide at least one percentage field and another decision field.
    Automatic promotion, human approval, and public projection each enforce the
    same completeness boundary.
48. D-034 narrows current default collection to the following executable
    essentials: Chequing = fee + minimum balance + included/unlimited
    transactions; Savings = ongoing rate + fee + minimum balance; GIC = rate +
    term + minimum deposit + redeemability; Credit Card = annual fee + purchase
    rate; Mortgage = rate/qualified summary + rate type + term; Personal Loan =
    rate/APR summary + amount + term; Line of Credit = rate/formula summary +
    limit + security. Alternative fields satisfy one requirement, not several.
    Explicit zero money values and explicit boolean states are valid facts when
    evidence-grounded. Default collection does not request optional copy.
49. D-035 resolves that executable contract by `(country_code, product_type)`
    before any collection, validation, Review, approval, or Public decision.
    Canada retains rule 48. US Checking replaces transaction count with
    opening/minimum balance and a fee-waiver or qualifying-activity requirement
    when the grounded recurring fee is positive; explicit zero fee needs no
    invented waiver. US Savings accepts an opening deposit as the relevant
    balance fact, but a positive recurring fee requires its complete waiver
    condition. A conditional APY also keeps new-customer eligibility,
    balance/timing, fallback-rate, as-of-date, and variability conditions in
    `interest_rate_summary`. US CDs replace redeemability with a quantified
    `early_withdrawal_penalty`. US Mortgage requires a percentage-bearing
    `interest_rate_summary` that preserves all stated ZIP, LTV, points, credit,
    effective-date, and similar assumptions, plus rate type and term. US
    Personal Loan keeps percentage-bearing APR/rate range, amount range, and
    term range as source-language text. US Credit Card and Line of Credit own
    explicit profiles even while their current minimum facts match rule 48, so
    later market changes and essential-only Public projection remain isolated.
    Canada and country-less legacy calls retain rule 48, but any other explicit
    country fails closed until its profiles and fixtures are registered. A
    versioned declarative override may
    change only the market semantics; it never weakens product identity,
    official evidence, type/range, conflict, ambiguity, or the `100%` gate.
    Country ownership is also a source boundary: an explicit route, locale,
    subdomain, or country-code TLD for another market is excluded from entry,
    detail, seed, and supporting evidence even when the parent official domain
    is shared by both countries.
    Official detail, rate, fee, and disclosure documents may form one evidence
    bundle only when every merged field retains exact-product field-level
    evidence and its supporting source document id. Legal agreements,
    enrollment/service flows, calculators, and generic hubs are never
    standalone product identities.
    Source planning bounds that bundle before fetch: only selected-product
    descendants/companions, a Product-Type-compatible rate/APR page, or an
    essential-fact FAQ/disclosure that identifies the selected product may be
    included. Educational, servicing, application, transfer, investment,
    sibling-product, and conflicting Product-Type routes are excluded.
    AI evidence quotes cannot contain ellipses; every proposed numeric token
    must occur in the quote, and decision-critical waiver, penalty, security,
    or qualified-rate prose must be copied there in full.
50. A percentage elsewhere on a page does not make a lending rate summary
    usable. Masked/template values such as `X.XXX%`, `$XXXX`, `RDS%...`, or
    unresolved rate tokens are invalid, and a usable textual summary must bind
    a concrete numeric percentage locally to Rate, APR, APY, or an explicit
    reference-rate formula. Transaction, currency-conversion, point-of-sale,
    and ATM/ABM assessment-fee percentages are non-rate context and cannot
    populate a deposit or lending rate. For a country-specific override, aggregate refresh
    projects only its comparison fields plus product identity, status,
    freshness, and official product link. Extra normalized copy remains in the
    private candidate/evidence record for audit but cannot leak navigation,
    calculator, transfer-limit, or misclassified eligibility text to Public.
    Comparison-critical prose also uses a field-specific safe length and must
    end as a complete sentence or condition. Never satisfy a requirement with
    a fixed-width value cut mid-word or mid-clause; keep the full bounded value
    or omit it for Review/AI repair.
    The same assumption-preservation rule applies to a US Personal Loan or
    vehicle-loan representative APR: model year/vehicle age, LTV, down payment,
    credit assumptions, origination fees, and rate-change qualifiers stated in
    official evidence remain attached to `interest_rate_summary`. When a
    displayed lending rate includes a relationship or automatic-payment
    discount, the qualifying account/payment and existing-customer conditions
    remain attached as well.
51. `card_display_rate` is a Public presentation derivative, not canonical
    truth. Deposits reuse their approved `public_display_rate`. Lending and
    Credit Card cards use the lowest explicit absolute rate available in the
    current approved projection, including an explicit introductory APR or the
    lower endpoint of a disclosed range. Down-payment, discount, fee, LTV/CLTV,
    cap, and reference-rate component percentages are excluded; a formula such
    as `Prime + 2%` is not converted into an absolute rate. Full qualified rate
    summaries remain unchanged for comparison/detail, and card-rate derivation
    never triggers recollection, Review, or canonical mutation.

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
