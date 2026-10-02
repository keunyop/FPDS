# Fast whole-catalogue publication — 2026-10-01

## Result

Product Owner broadened the request to all unpublished products, prioritizing quick bulk work. The interrupted six-card investigation was superseded before runtime/data changes.

- Read-only diagnosis covered all **406 unpublished** canonical products (393 inactive, 13 active hidden), 1,430 preserved candidates and trusted database evidence.
- Replayed saved official captures for 253 products with the current gate. Diagnostic matching was an upper bound only: cross-product benefits, conditional free fees, duplicate identities, wrong bank/country bindings and example APRs were excluded before execution.
- Bounded current preflight checked 12 distinct official detail URLs in parallel. The two selected sources were captured again through the normal pipeline (14 logical source-fetch operations in total; existing bounded fallback handling retained). A three-product real normalization/validation dry run accepted two; Western Alliance Personal Checking lost its monthly fee in normal normalization and was retained without an override.
- **Two products published** through current capture, normal normalization, automatic validation and promotion. Two bank/type runs completed; one aggregate refresh was launched. No collection-model/provider calls, new human reviews, code/UI/schema changes, deletion, permanent recovery feature or deployment.

| Product | Current verified comparison facts | Canonical ID |
|---|---|---|
| First Citizens Bank Online Savings Account | USD; monthly fee 0; annual percentage yield 0.10% | `prod_kJPYb0EzJ2uEVxQa` |
| City National Bank Personal Checking Account | USD; monthly maintenance fee 20; unlimited transactions; opening minimum deposit 1,000 | `prod_OTG4JcSp6_JNGmBf` |

Public API now has **24 products: CA 20 / US 4**. Canonical remains 428 products: 37 active / 391 inactive. Thirteen active products remain hidden, so **404 remain unpublished**.

## Why the batch was small

Saved evidence did not establish a large immediate publication group under the current prerequisites. Apparent successes included another account's unlimited allowance, a conditional CIBC zero fee, an incorrectly linked Canadian TD source for a US record, and a loan example APR. These were retained as exclusions. Some otherwise plausible current declarations still fail existing normalization/meaning checks. This operation did not turn diagnostic number matches into financial facts or change the gates to increase counts.

The quick path is to group candidates by the same missing essential and shared current official document, reuse captures, then apply normal gates once per batch. The remaining large card groups need correct annual purchase-rate/table binding; deposit groups need current annual rates and actual transaction/withdrawal conditions. They require further work beyond this bounded quick batch. No claim is made that all remaining products are permanently unpublishable.

## Verification

- Normal dry run: two `auto_validated` candidates; one automatic exclusion, no review tasks.
- Independent readback: only the two intended canonical products changed; other **426** canonical rows, **1,430** historical candidate rows and source registry unchanged. Five previous version fact payloads preserved; only the prior current-version status/time changed normally to `superseded`. Each target has one new version.
- Both newly approved candidates replay successfully using database-resolved official evidence and have valid content-bound receipts. Both runs completed; no started runs or new reviews. Model records are heuristic normalizer/validator only.
- Actual CA/US API lists preserve all 22 earlier public products and include the two new products. Both API details and actual website details pass; visible values are 0.1% / US$0 and US$20. The actual US website list contains both IDs.
- The separately cached US BFF list initially returned the earlier two-product snapshot. It uses ordinary cache revalidation; no cache policy was changed or bypassed. See the final check artifact for its latest observation.
- No runtime code changed, so the application suites were not rerun for this data-only slice. Normal pipeline dry runs, independent data/evidence checks and actual public readbacks were run. `git diff --check` passed; the final documentation diff and shared goal were reviewed.

Private before-images, diagnosis, exact captures, dry runs, plans, results and readbacks: `tmp/fast-bulk-*`. These are private evidence; do not publish their raw contents. Earlier shared collection fixes still need their separate runtime deployment, which this operation did not perform.
