# Ally, American Express and Bank of America collection corrections

Date: 2026-10-08 (America/Vancouver). Status: complete for local corrections and direct data publication.

## Original collection result

Read the latest ordinary scoped Runs and preserved their original registry,
snapshot checksums, source-stage records, candidates and canonical/version state.
The latest batches were `run_20261008_162755` (AB/AE) and
`run_20261008_164840` (BOAN). All substantive Runs used process v8,
`2026-10-07-referenced-disclosure-proof-v8`.

| Bank | Latest Runs | Original candidates | Auto-approved |
|---|---:|---:|---:|
| Ally (AB) | 3 | 2 | 0 |
| American Express (AE) | 3 | 1 | 0 |
| Bank of America (BOAN) | 5 | 17 | 0 |
| Total | 11 | 20 | 0 |

AB CD stopped at duplicate normalized registry identity; AE CD had no eligible
parsed target. AE Checking completed without a discovered target. AE Savings
lost its actual HYSA detail source and produced only the generic account page.
Original twenty candidates were rejected automatically, with no manual review.

## Where proven evidence was lost

- Accessible identity: SVG titles in semantic product headings were deleted by
  snapshot parsing and concatenated into discovery's document title. Empty H1s
  could crash account parsing. The AE HYSA/CD actual accessible product names
  differ from the marketing headings used in the original registry assessment.
- Acquisition: BOAN card pricing uses literal unresolved JSON values inside
  HTML data attributes. The previous visible-text detector erased these leads,
  so missing essential APR/fee information did not request a bounded render.
  On the saved static card source, old required-render detection is false and
  corrected detection is true. AE HYSA also keeps its unresolved APY header in
  literal encoded JSON/Transit hydration state; the old planner did not request
  rendering. The actual static-to-rendered ordinary planner/artifact regression
  now requests one render and then automatically validates the rendered price.
  Placeholder values themselves prove no facts.
- Costs: monthly maintenance labels were missed; whole mixed fee sections could
  make a separate transaction qualification contaminate an unconditional base
  fee. Financial labels rendered as headings were mistaken for sibling products.
  Product-name audience text, such as "for Students", was mistaken for a fee
  waiver. Actual fee qualifications must remain binding.
- Annual yield: literal linked product APY components and complete numbered
  current-APY notes were not retained as product-owned annual evidence. A
  comparison benchmark must never replace the account's current payable APY.
- Qualified card rates: complete introductory/current-variable-range paragraphs
  need to remain prose with billing-cycle, transfer-window, fee and note context.
  Neither a zero introduction nor one range endpoint is a standard scalar APR.

AB's duplicate identity is the earlier v8 failure. The already implemented v9
canonical research-URL correction addresses it; it is not credited as a new
bank-specific exception in this change. Observed serving health before this
operation was v9, while these preserved original Runs used v8.

## Independently collected current evidence

Fetched the original official target/supporting URLs directly using the existing
safe-fetch/domain policies, without the FPDS Admin collection API or paid model
calls. Preserved current bytes, timestamps, SHA-256 and the original raw evidence.
Initial rendering was bounded at 16 attempts; four additional explicit renders
used two bounded batches, one per target, without repeating a target render.
Actual initial fetch-method metadata was unavailable and is not reconstructed.
The four explicit render receipts record their actual fetch method and timestamp.
Identical current captures are reused during every extraction/gate rehearsal.

| Verified product | Current essential facts from the capture |
|---|---|
| Ally Bank Savings Account | 3.10% variable APY; USD 0 monthly maintenance fee |
| American Express High Yield Savings | 3.10% variable APY; USD 0 monthly fee; explicitly no minimum opening deposit |
| BOAN Travel Rewards Credit Card | USD 0 annual fee; complete introductory/current variable APR summary |
| BOAN Travel Rewards Credit Card for Students | USD 0 annual fee; complete introductory/current variable APR summary |

Savings disclosures explicitly date the APYs to 2026-10-08. Card summaries keep
0% for the first 15 billing cycles, the first-60-day balance-transfer boundary,
current variable 17.74%-27.74% APR, introductory 3% and subsequent 5% transfer fees
and the complete local cost disclaimer. No purchase APR scalar is created.

Official sources: [Ally Savings](https://www.ally.com/bank/online-savings-account/),
[Ally APY comparison](https://www.ally.com/bank/savings-account-rates/),
[Amex HYSA](https://www.americanexpress.com/en-us/banking/online-savings/high-yield-savings-account/),
[BOAN Travel Rewards](https://www.bankofamerica.com/credit-cards/products/travel-rewards-credit-card/),
[BOAN student card](https://www.bankofamerica.com/credit-cards/products/student-rewards-credit-card/).

The direct ordinary-service rehearsal produces 23 candidates: four pass, nineteen
remain excluded. Missing complete comparable rate/term/access/consequence proof
still blocks CDs; ordinary transaction-cost proof blocks Checking; qualified
rate/type/term proof blocks Mortgage. BOAN location-gated rates are not replaced
by a selected ZIP scenario. Generic family/feature pages and the wrongly scoped
HELOC cannot become a CD. This is not a claim that these banks offer no additional
products or that every source with a rate is publication-ready.

## Shared implementation and regression contract

Parser v19/process `2026-10-08-accessible-qualified-source-proof-v10` align discovery,
parsing, extraction, normalization/validation origin checks, prompts and cache
identity. New source DOM fixtures pin original bytes and independent expectations.
No bank-code/domain acceptance branch, supplied financial fact, review override,
new collection menu/scheduler or permanent recovery feature is added.

- Unique literal accessible image titles inside semantic headings survive;
  hidden/decorative/ambiguous/conflicting SVG labels cannot establish identity.
- An owned native brand prefix can be corroborated by the verified official
  hostname only with the complete remaining SEO/route identity and own price.
- Owned monthly-maintenance rows retain complete row/table-wide local notes.
  Bare numeric/dagger markers require a unique literal note. Heading conditions
  apply within the actual DOM pricing section. Separate cash-reward conditions
  cannot qualify an independently declared ordinary fee.
- Named APYs require the actual detail link and complete annual-yield disclosure;
  referenced APYs require the current numbered account-family note. Component
  references, local qualifications, conflicts, tiers and promotions cannot be
  silently removed to obtain a scalar. Qualified card offers stay full prose.
- Bounded JSON pricing templates in attributes and literal hydration-state
  financial headers are essential-only acquisition leads. Strict JSON and encoded
  JSON/Transit maps execute no scripts or derive prices. Invalid,
  duplicate-key, nonfinite, excessive, navigation and nonfinancial payloads cannot
  supply evidence or execution. Existing origin/security and acquisition limits
  remain; optional completeness adds no searches/retries/review.

Regression coverage includes actual AB/AE/BOAN sources plus existing other-bank
Savings, Checking, CD, card and lending evidence. Tests exercise success, missing
and ambiguous notes, local conditions, bonuses, wrong bank/country/detail links,
foreign products, source-byte hashes and ordinary stored-artifact origin gates.
Windows command transmission lost some characters in added synthetic note cases;
those cases were corrected with escaped exact Unicode and a positive control,
then rerun. Original official fixture bytes were not altered.

## Verification and publication receipts

Completed operation `us-three-bank-direct-20261008`: ten direct Runs created
23 candidates, four normal automatic promotions and nineteen exclusions, with
zero manual reviews, provider calls or Admin collection API calls. Actual stored
chunk/source/snapshot origins and unchanged field contracts were revalidated
before promotion. The transaction rollback rehearsal passed before commitment.
Normal aggregate refresh consumed three US requests and completed snapshot
`agg_t_BmGQmoVSsEYaRU` at 2026-10-09 03:35 UTC (2026-10-08 local).

Anonymous Public lists and all four API/site details were read back successfully;
all four site details returned HTTP 200 and complete card qualifications were
visible. Nineteen field-evidence checks match current captured bytes and origins.
US Public increased from five to nine; CA remained 120. The original eleven Runs,
twenty candidates, 57 source-stage records, 108 bank documents, 224 snapshots and
1,515 version facts are preserved; 448 unrelated canonical products and all
unrelated Public financial facts are unchanged. Private evidence was not exposed.

| Public product | Verified detail |
|---|---|
| Ally Savings | [Public detail](https://www.switchabank.com/products/prod_gz7OGr1gCCeAs1ty?country_code=US) |
| Amex HYSA | [Public detail](https://www.switchabank.com/products/prod_eexWmSX9ieNaylmI?country_code=US) |
| BOAN Travel Rewards | [Public detail](https://www.switchabank.com/products/prod_uKhl2l2K4aqXVhfl?country_code=US) |
| BOAN Travel Rewards for Students | [Public detail](https://www.switchabank.com/products/prod_ToRADeUTz-zLGUFp?country_code=US) |

Final independent API suite: 647 tests pass. The full Worker suite ran 910 tests
with only the two existing fixture-hash failures below. After the final literal
hydration-state acquisition addition, all 38 affected source/cost/evidence-planner
regressions pass; a further three final bounded-decoder/planner checks also pass.
The actual previously failing Simplii ordinary fee/origin cases pass after fixing
heading scope. Test invocation/import-path and Unicode transmission errors were
corrected and rerun; they are not reported as product defects or passing runs.
Foundation baseline, changed Markdown references, strict UTF-8/Python syntax,
fixture JSON/hash and git diff whitespace checks pass. Global repo-doctor remains
blocked by an unrelated broken design-document link inside the ignored operational
clone `tmp/admin-vercel-pnpm-fix-20261008/admin/README.md`; this task did not change
or delete that clone.
Private operation artifacts are under `tmp/us-three-bank-20261008`; they are not
Public API/page evidence. The operation uses ordinary stored-origin validation,
normal automatic promotion and normal US public aggregate refresh, with a rollback
rehearsal before canonical mutation and readback afterward.

Existing National/Oaken fixture-hash failures reproduce with source/manifest
bytes unchanged from HEAD. Their expected hashes were not changed to hide them.

## Runtime release boundary

This change does not deploy or restart API/Worker/Admin. Serving code was observed
at v9; local parser/process changes require a coordinated API/Worker v10 release.
Published product data is verified separately from that runtime release. No schema,
authentication, CSRF, country isolation or private evidence exposure change.
