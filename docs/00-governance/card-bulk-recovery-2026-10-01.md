# Scotiabank card bulk recovery — 2026-10-01

## Outcome

The Product Owner authorized a bounded bulk check of the remaining 14 retained Scotiabank cards. Two cards passed current normal normalization, automatic validation and promotion in one run. Public API now contains CA 14 / US 2, total 16. Canonical has 428 records: 29 active / 399 inactive. Thirteen active records remain hidden, so 412 records remain unpublished. No deletion, UI change, paid collection-model call, human review or deployment.

| Published existing product | Annual primary-card fee (CAD) | Current preferred annual purchase rate |
|---|---:|---:|
| Scotiabank Passport® Visa Infinite Privilege* Card | 599 | 20.99% |
| Scotiabank Passport® Visa Infinite +* Card | 150 | 20.99% |

## Bounded diagnosis and reusable correction

Saved evidence was diagnosed before collection. Fresh preflight captured 14 current detail URLs and the shared linked agreement scope/PDF, with maximum three concurrent fetches and no model calls. Explicit purchase and cash-advance rates in one current preferred annual declaration were incorrectly treated as competing scalar rates. Regression failures were reproduced before extending the shared gate.

The gate now recognizes only one complete explicitly labelled current preferred annual Account-rate declaration, with exactly its two percentages and no competing percentage or repeated declaration. Purchase and cash percentages bind to their own labels. Balance-transfer applicability requires its explicit parenthetical. All original context, annual basis, native types, financial conditions, official origins and currency requirements remain. The existing separate switch-from offer distinction also handles a current declaration on the same line and `this Account`. Matching instructions reach extraction and card dynamic normalization. Normalization can recognize the same exact quote/full-context proof; other filters still apply.

Fourteen cards were assessed together. Three passed the direct evidence gate; the real normalization dry run accepted two. Gold American Express still lost its purchase rate in a subsequent context filter and was excluded. The other eleven lack complete admissible annual-fee, purchase-rate or exact currency-applicability proof. Explicit no-fee words embedded in conditional full context cannot bypass the existing zero-value guard. Student and Mastercard products cannot inherit an unlisted agreement scope. These exclusions do not prove products are permanently unpublishable; all twelve are retained without manual overrides or paid retries.

For the two accepted cards, historical discovery formatting hints were removed only from operation-local metadata after exact current H1/name proof, preventing a stale title from replacing the existing canonical name. Registry entries remain unchanged. No unproven optional attributes or new optional registrations were introduced. Raw evidence stays private.

## Execution and verification

- Run: `run_20261002_024620_scotia_credit-card_collect_nBzFZ-vK`.
- Normal capture rechecked the two accepted detail pages and shared scope/PDF once each, followed by normal parse, normalization, validation and promotion. One completed run, two approved candidate versions and one completed CA aggregate request.
- Before-images were taken before mutation. The first execute attempt stopped at a stale inventory-count assertion before any reservation or write; the assertion was updated to the independently verified 27-active starting state.
- Independent DB readback: other 426 canonical records, six saved target historical candidates, prior target versions and source registry unchanged. Both complete current evidence receipts replay. Zero reviews, provider tokens or unfinished runs.
- Worker 608 / API 539 tests pass; seven focused card-context/label tests pass. Repository doctor and final diff check are recorded at completion.
- API catalogue and both details immediately confirm correct CAD annual fee/purchase rates and preservation of all previously public products. Website verification is completed after ordinary cache revalidation; see completion note below.

Private artifacts use `tmp/card-bulk-*`: original inventory/items, 16 captures, assessment and exclusions, dry run, before-images, plan, execution captures, result and independent DB/Public readback. Completed execute must never be rerun. Timestamps are UTC 2026-10-02, local Vancouver 2026-10-01.

Shared code is local. Deploy the collection-runtime/API package to apply it to future Admin collections; deployment was not performed. This recovery remains a one-off operation with no new menu or scheduler.


## Completion

All 11 actual API/BFF/deposit-list/card-list/product-detail checks passed after ordinary cache revalidation; CA 14 / US 2 and all previous products are preserved. Both website details display exact annual fees $599/$150 and purchase rate 20.99%. BFF cache initially retained CA 12, then refreshed to CA 14 without cache/code mutations. Final numeric-bound regression preserves the existing less-than-100% limit. Worker 608 / API 539 and seven focused tests, repository doctor, independent DB/evidence replay, final diff and goal checks passed. Shared generated parser bytecode was restored; unrelated prior TD/Platinum work remains.
