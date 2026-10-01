# Supporting evidence origins and Scotiabank recovery

## Outcome

The Product Owner approved correcting the common cause when useful for future collection, followed by publication of the prepared two products. The defect affected every normalization input with evidence from a different document: its URL was replaced with null before the accuracy gate. The fix therefore belongs in the shared collection code.

The corrected local worker published **Scotiabank Ultimate Package** (CAD 30.95 monthly fee) and **Preferred Package** (CAD 16.95 monthly fee), both with proven unlimited ordinary transactions. Official fee-waiver and other qualifications remain in the complete retained evidence; the published monthly fee is the base fee. Both receipts use explicit official CAD evidence from the exact linked booklet, rather than a currency default.

Public API and BFF now contain **11 products: CA 9 / US 2**. Final database: 428 canonical records, 26 active / 402 inactive. Fifteen active records remain hidden by current Public requirements, so 417 remain unpublished. Original 355-product manifest: 26 active / 323 inactive / 6 previously deleted. No deletion occurred in this operation.

## Shared fix

- `worker/pipeline/fpds_normalization/persistence.py`: one read restricted to referenced chunks and the current run's successful selected snapshot/parse, retrieving actual stored document URLs.
- `__main__.py`: resolve those origins after the existing supporting-artifact merge and before normalization. Extraction artifacts cannot supply the trusted map.
- `models.py` / `service.py`: preserve origins through input expansion and check run, bank, country, chunk, document, snapshot and full text before using a supporting URL. Same-document input compatibility remains; mismatches fail closed.
- Seven regression tests reproduce the old false exclusion and exercise valid official provenance, missing/mismatched/foreign/forged provenance, actual repository loading, artifact injection rejection and normal acceptance/exclusion without review.

Existing supporting-product selection, official allowlists, actually consulted URL, exact quotes, native financial values, full-context semantics and publication requirements remain unchanged. No model retry, new collection feature, migration, UI, API route or accuracy/profile version change was introduced.

## Bounded live operation

Four official URLs were preflighted: the two detail pages, the shared companion booklet and current fees table. Full captures matched the previously prepared evidence. Exact detail H1, direct booklet link, whole-booklet hash, global currency clause, exact named account column and current fee-table row/link establish applicability. No historical fact was restored solely because it existed before.

Fresh normal capture/parse, DB origin resolution, normalization, automatic validation and promotion completed in one run. The live operation rechecked the same four sources, retained full native contexts and used the same shared code tested for future collection. Serving accuracy/profile gates already match the unchanged current policy. Two new versions advanced exactly once; no human review was created and no collection model was called. CA aggregation completed.

Independent DB readback and evidence replay confirm both new receipts and actual booklet origin, unchanged prior versions, all 426 unrelated canonical products unchanged, 21 original target candidates unchanged, and unchanged source registry. All 9 actual API/BFF/list/detail URL checks passed after normal cache revalidation, including all existing Public products, the new transaction information and exclusion of private evidence fields.

## Verification and deployment

- Before fix: positive linked-currency normalization regression failed.
- Focused normalization/accuracy tests: 200 passed.
- Full Worker: 596 passed. Full API: 539 passed.
- Repository doctor, final `git diff --check` and six updated report links passed.
- No collection-model calls or provider tokens. Coding-assistant tokens are separate and were not measured.
- This data operation is applied. The shared fix is local; **deploy the collection runtime/API package for future Admin-triggered collection**. No deployment was performed in this slice. Public data visibility does not depend on that future deployment because the existing API supports the unchanged valid receipts.

Private artifacts use `tmp/support-origin-*`: before images, four current official captures, selected exact-product evidence, normal dry run, actual execution plan/results, independent DB readback, Public URL checks and test logs. Never rerun the completed execution script. Raw evidence/provenance remains private.

The next separate potential correction is precise field/section handling for finite ordinary transactions versus public-transit-only benefits and unrelated rate promotions. This slice does not alter those gates or retry the remaining catalogue.
