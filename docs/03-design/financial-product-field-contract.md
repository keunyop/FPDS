# Financial Product Field Contract

Status: Active
Last updated: 2026-07-19

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

## Runtime Validation

Normalization coerces unambiguous scalar representations into the canonical type. Compound rate prose is redirected into `term_rate_table` when it can be parsed safely. Validation emits `invalid_field_type` when a value remains incompatible with the field contract.

Manual Admin overrides use the same coercion and rejection rules. Canonical continuity is based on stable bank, family, type, and product identity so a subtype correction does not create a duplicate product.

Static Golden profiles are test fixtures only. They may be enabled explicitly with `product_profile_expansion_mode=fixture`; they cannot overwrite live collection facts or bypass validation.

## Verification Baseline

Each new false-positive or merge failure class requires a regression test. Representative Admin-path recollection must then verify:

- values and schedules against current official sources;
- JSON types against the executable contract;
- evidence links against the source actually used;
- reviewer-visible field notes;
- safe review routing for facts the source did not publish accessibly.
