# Additional unpublished-product recovery - 2026-10-01

## Result

The Product Owner requested a one-off data operation: discard conclusively unpublishable records, strengthen collection for currently unpublished products and publish automatic passes with minimal token use. No Admin, Public or runtime code was changed or deployed.

Live startup checks confirmed policy `collection-accuracy-2026-10-01-cost-access` / profile `2026-10-01-v7`. The database held 24 active and 405 inactive products, but the current Public gate exposed only 5 (CA 4 / US 1). The operation therefore considered 424 unpublished records, including 19 active records hidden by the current gate. Existing Public products were excluded from mutation.

Four hidden products passed fresh normalization, automatic validation and promotion:

| Product | Country | Monthly fee | Newly proven comparison fact |
|---|---|---:|---|
| TD All-Inclusive Banking Plan | CA | CAD 30.95 | Unlimited ordinary transactions |
| TD Student Chequing Account | CA | CAD 0 | Unlimited ordinary transactions |
| Vancity Chequing Plus for youth | CA | CAD 0 | Unlimited ordinary transactions |
| Western Alliance Personal Interest Checking | US | USD 10 | Unlimited checking transactions |

The student/youth identities and source qualifications remain in their exact product evidence. Western Alliance's USD 0.01 balance for earning interest was omitted as a general minimum balance. No missing value became zero or false.

Public API and BFF now expose **9 products: CA 7 / US 2**. All four detail pages pass. The initial CA rendered list retained an older cache; all 11 final ordinary API/BFF/list/detail URL checks passed after normal revalidation.

## Confirmed non-product deletion

Deleted only `Deposit Agreement and Disclosures` (`prod_chL0WbIoBxFXI6oA`). A fresh Bank of America Advantage Banking page identifies the exact label as a linked legal deposit-agreement PDF, not an individual account. The operation preserved that source and its financial products.

A transaction rollback rehearsal and before-image backup preceded execution. Deleted one canonical row, two product versions, two change events and three version-evidence links; cleared one historical review's product reference. The review/candidate/raw evidence history remains. No published projection, external publish item, feedback, engagement or refresh request referenced this record. All 428 surviving canonical rows were unchanged by deletion. The legacy audit view is a no-op; the private operation artifacts retain the actual backup and evidence.

## Remaining products and demonstrated limits

The final database has **428 products: 24 active / 404 inactive**. Fifteen active products still fail the current Public gate, leaving **419 unpublished records**. The original 355-product cutover manifest now contains 24 active, 325 inactive and 6 deleted non-products. None of those 325 inactive products was restored in this batch; the four additions were previously active but hidden.

All 405 initially inactive records received a read-only replay of existing evidence. None passed unchanged reuse. Diagnostic reason counts overlap: 403 lack essentials, 197 lack proven identity, 40 have unverified currency, and one is not a product-detail source. These are retained-evidence diagnoses, not proof that official information does not exist or that the products should be deleted.

Twelve unique official sources were then captured for a bounded promising subset and deletion proof. Nine financial product details were assessed; six passed the evidence-level check, but only four passed normal end-to-end normalization and validation:

- Scotiabank Ultimate and Preferred Package: exact current detail headings, linked booklet, unchanged full booklet hash, global CAD clause and exact fee-table product links establish applicable currency. Normalization currently assigns no source URL to evidence from a different source document (`worker/pipeline/fpds_normalization/service.py`, accuracy input construction), so both remain excluded. No source identity was forged, gate patched or historical error stripped to force publication. Their prepared evidence is retained for a separately scoped runtime correction.
- RBC VIP: unresolved currency applicability remains under current gates. No further equivalent fetch/retry was performed.
- TD Every Day and Minimum: ordinary transactions are finite; unlimited public-transit transactions must not be reused as general unlimited pricing. An initial diagnostic proposal exposed the existing validator's overly broad pattern. Both were excluded from execution. Their retained full fee tables also fail current excess-fee/count parsing; runtime correction is outside this data-only slice.
- Other uncertain records remain available for future evidence work. A source failure, missing field or validator limitation was not treated as proof of permanent unpublishability.

## Verification and cost

- 31 existing accuracy/recovery/cutover regression tests passed.
- Four successful automatic promotions across three completed runs; no running collection or new human reviews remain.
- Independent database/evidence replay verifies all four new versions, previous version payload preservation, 424 unrelated surviving canonical rows unchanged, all 1,536 historical candidates unchanged, and the source registry unchanged.
- Both countries' aggregate refresh requests completed. API/BFF totals, restored fields, existing Public-product preservation, four detail pages and private-evidence non-exposure were checked. Final URL results are retained separately.
- Twelve unique preflight sources plus four ordinary execution rechecks; no unchanged paid retries. Collection-model calls and provider tokens: **0**. Coding-assistant conversation tokens are separate and were not measured.
- Final `git diff --check` passed.
- Data-only work: no unrelated application build, UI redesign, permanent recovery feature, scheduler or deployment.

Private artifacts use `tmp/additional-recovery-*` and `tmp/additional-nonproduct-delete-*`: initial database snapshot, 424-product scope/history, 405-record diagnosis, current source captures, assessment, selected inputs, normal dry run, execution plan/results, evidence replay, deletion backup/rollback and actual Public checks. Do not rerun completed execution scripts. Source evidence stays private.
