# Remaining Scotiabank cards — 2026-10-01

## Outcome

The Product Owner authorized continuation for the twelve remaining cards. Six existing unpublished cards passed normal automatic collection/validation/promotion together. Public API is CA 20 / US 2, total 22. Canonical contains 428 records: 35 active / 393 inactive; thirteen active records remain hidden, hence 406 records remain unpublished. No deletion, Admin/Public UI change, human review, collection-model call or deployment.

| Published card | Current annual primary fee (CAD) | Preferred annual purchase interest |
|---|---:|---:|
| Scotiabank Gold American Express® Card | 120 | 21.99% |
| Scotiabank® Scene+™ Visa* Card | 0 | 21.99% |
| Scotiabank American Express® Card (for students) | 0 | 21.99% |
| Scotia Momentum® Mastercard* credit card | 0 | 20.99% |
| Scotiabank® Scene+™ Visa * Card (for students) | 0 | 21.99% |
| Scotiabank American Express® Card | 0 | 21.99% |

## Shared corrections and evidence

The prior batch's Gold Amex rejection was traced to normalization overwriting an extracted field's own evidence with every chunk containing the same number. For an unchanged numeric extraction with an actual chunk and full excerpt, normalization now preserves its original field context. AI-introduced/changed values and missing bound evidence still use the existing lookup; official-origin, exact quote, native type, currency, complete-condition and final automatic accuracy checks remain binding. This is a reusable correction across numeric product fields.

A future `subject to change` notice alone does not make an explicitly current fee conditional. The shared zero-value guard distinguishes that notice from payment/waiver/eligibility conditions and explicitly rejects first-year/month and introductory/promotional zero-fee contexts. Separate complete `Enjoy no annual fee` benefit chunks prove unqualified zero fees for four of these cards; Mastercard's complete current Rates and Fees declaration proves its zero. The gate does not invent zero from missing information. Common extraction and requested fee normalization instructions agree; unrelated prompts receive no extra fee text.

Current personal Visa/Amex details directly link the same current agreement scope/PDF. Its explicit footnote applies to personal Visa and Amex branded credit-card accounts, including the verified personal student variants; USD Visa remains a separate exception. CAD settlement proof retains the complete mixed-currency context. Earlier diagnosis required a named scope-panel entry and missed this explicit family coverage; the student cards do not inherit unrelated product terms. Exact current student H1/name, personal-product source, direct agreement link and applicable card family were checked again before promotion.

Momentum Mastercard uses its own directly linked current agreement page. That page names the current Momentum Mastercard agreement, links the base agreement and the current payment-allocation amendment. The base agreement explicitly posts converted transactions to the account in Canadian dollars. The amendment covers payment allocation and leaves the currency clause intact. These are current live-linked documents, not restored historical fee/rate facts. Current primary detail proves fee/rate. The Mastercard scope document already existed in the DB and was reused with its original metadata/registry flag; no source-registry change.

## Bounded operation

- Saved current-day primary/common captures from the preceding batch were reused for diagnosis/dry run. Only three additional essential Mastercard documents were preflighted. No optional-only fetch, model call or paid retry.
- Six of twelve passed the direct evidence gate and real normal normalization/validation. Remaining six (Momentum Visa regular/student, Momentum No-Fee Visa regular/student, Momentum Visa Infinite + and ScotiaGold Passport) still fail the complete purchase-rate context/declaration checks. Their current identity is verified; they remain retained exclusions, not proven non-products.
- Current full contexts were required to match the prepared field evidence during normal fresh capture. Both normal capture attempts checked eleven selected detail/support sources. The first failed at a source-document uniqueness conflict before canonical changes; capture SQL rolled back. Resolved the existing Mastercard scope document ID and resumed the exact same reserved run once after verifying canonical/candidate state. No second run or manual decision.
- Run: `run_20261002_031922_scotia_credit-card_collect_mNPw6Ios`. Six approved versions; one completed run and completed CA aggregate request. Provider calls/tokens and new reviews zero.
- Private `tmp/card-next-*` artifacts retain inventory, reused/additional preflights, direct/normal assessments, before-images, original/resolved plan, one bounded resume, capture lineage, result and independent readback. Do not rerun execute/resume.

## Verification

Independent DB/evidence readback preserves other 422 canonical records, fifteen saved target historical candidates, prior versions and source registry. Existing Mastercard scope metadata/registry flag are unchanged. All six complete receipts replay, including their exact applicable CAD document origin and current fee/rate; no unfinished run or new review.

Worker 611 / API 539 tests pass, plus ten focused card/context/fee tests and repository doctor. The new regressions cover bound numeric evidence with unrelated identical percentages, complete conditional rate rejection, current no-fee future-change wording, and first-year/conditional/introductory zero-fee exclusions. `git diff --check` and final goal/diff review are recorded at completion.

API counts/details and all six actual website details show exact fee/rate (including proven $0). Existing products remain present. Initial website catalogue/card-list cache still showed the previous count; final ordinary revalidation is recorded below.

Shared code is local. Deploy the collection-runtime/API package to apply these fixes to future Admin collection; no deployment was performed. This remains a bounded one-off recovery with no feature, menu or scheduler. UTC capture/run timestamps are 2026-10-02, local Vancouver 2026-10-01.


## Completion

All 19 actual API/BFF/deposit-list/card-list/product-detail checks passed after ordinary cache revalidation: CA 20 / US 2, total 22; all six new and all sixteen previous Public products are present. Six website details display exact fee/rate, including five proven $0 annual fees. Site catalogue temporarily retained CA 14 before normal expiry/revalidation; no cache setting or canonical mutation was used to force refresh.

Final zero-fee regressions also reject change-after-one-year and new-customer-only conditions. Worker 611 / API 539 and ten focused tests pass; independent complete evidence/DB replay still accepts all six and preserves the recorded invariants. Repository doctor, final diff and goal checks pass. Generated parser bytecode is restored; unrelated user changes and prior goal ownership remain. Six other cards are retained exclusions. This completes the authorized twelve-card continuation; deployment remains separate.
