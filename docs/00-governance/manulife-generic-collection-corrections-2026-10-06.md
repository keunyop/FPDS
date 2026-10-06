# Manulife generic collection corrections and verified publication

Date: 2026-10-06
Authority: Product Owner requests direct inspection, generic corrections, repeated verification and publication.
Status: five unique products verified on the live anonymous API and website; runtime deployment remains separate.

## Outcome and latest collection baseline

The latest original batch, `collection_2WMc50Tt43xnBfYn`, began at
2026-10-06 04:01:29 UTC (October 5 evening in Vancouver). Its five Runs
completed with seven exclusions, no automatic approvals and no manual reviews.
Credit cards, mortgages and savings each produced two excluded candidates;
line of credit produced one. GIC produced no eligible detail candidate.
The original collecting Runs already reported `2026-10-05-native-rate-proof-v2`.
A previously undeployed change therefore does not explain these original failures.

Direct inspection and the corrected ordinary services prove five additional
eligible products. No FPDS Admin API or paid model was used for the direct
operation. The official detail pages were fetched again immediately before
publication: all seven were byte-identical to the latest selected captures.
Both pricing PDFs were also currently fetched and hash-identical to selected
older snapshots. Original snapshot dates remain historical; separate current
check receipts establish reuse. Current rates and GIC family pages were examined
through bounded official captures, without using historical financial facts.

| Published product | Verified public behavior |
|---|---|
| [Manulife Bank Visa Infinite](https://www.switchabank.com/products/prod_vbMmBsVAHgLM9fFJ) | CAD; $139 base annual fee, 21.99% ordinary purchase AIR; full separate increased-rate rule and existing-client application limitation retained |
| [Manulife Bank Visa Platinum](https://www.switchabank.com/products/prod_hJ77_DW7pC9hRY9U) | CAD; explicit $0 annual fee, 21.99% ordinary purchase AIR; complete rate qualifications retained |
| [Manulife One](https://www.switchabank.com/products/prod_jh96nmfVMnfNmlhQ) | Exact named open/closed APR term schedule, fixed/variable wording and linked APR/compounding/prime notes; positive-deposit-balance rows excluded |
| [Manulife Bank Select](https://www.switchabank.com/products/prod_6SxplEExzSou8jjE) | Its own fixed/variable APR schedule, exact term labels and own linked notes; no neighbouring product pricing inherited |
| [Lines of Credit](https://www.switchabank.com/products/prod_H2H0zIU2jgks36-a) | Complete credit-limit/prime-spread tiers and annual note; full affirmative collateral sentence plus independently grounded `secured_flag=true` |

Cards also retain the independently labelled 22.99% cash/transfer rate as a typed
optional fact and in the approved public rate summary. A welcome fee waiver does
not replace the regular $139 annual fee. No optional unknown becomes zero/false.
Public catalogue totals changed CA 73 → 78; US stayed 5. These are dated results.

## Why the original Admin collection could not prove these facts

| Confirmed shared defect | Correction and preserved boundary |
|---|---|
| Long menus displaced an observed Current rates lead within the link cap; irrelevant video transcripts/agreements competed with pricing | Reserve literal current/interest-rate leads within the same caps, across pages without a main-content wrapper; required-rate research keeps an observed exact lead ahead of generic agreements. Video transcripts/testimonials and rate-news leads cannot satisfy essential pricing research. Specific other-product pricing remains excluded. |
| Native H1 used nonbreaking spaces or differed from an action SEO title; plural category names differed from their own route | Capture the actual owned H1, normalize whitespace and require body/SEO/route corroboration. Cards additionally require owned price or named bound information-box evidence. Action routes, family pages, mismatched routes and foreign origins remain rejected. |
| PDFs used wrapped Card Information Box labels rather than the previously supported purchase-column layout | Preserve the named ordinary Annual Interest Rates record and separate Annual Fees row. Keep the complete missed-payment increase, start and reset conditions; purchase, cash and default rates remain distinct. Missing terminators, duplicated owners and incomplete rules fail. |
| Mortgage tables put explicit APR (%) inside a generic Rate table; multiple numbered notes shared a paragraph | Preserve each named fixed/variable term subgroup, literal terms and uniquely linked notes. Numeric note anchors own only their text up to the next note. Reference-base/deposit rows cannot enter the borrowing schedule; unresolved notes fail. |
| Credit-limit tables delegated annual units to an explicitly linked headline note | Retain the owned table and actual annual-unit reference together. Preserve every credit-limit/spread tier; no headline scalar replaces the qualified schedule. |
| Navigation inside main included an unrelated US Dollar account and blocked CAD default | Strip semantic navigation from parsed financial evidence. Keep actual product-denomination and conflicting currency text; approved CA/CAD and US/USD defaults remain unchanged. |
| Cleanup did not recognise an affirmative “by securing … with assets” sentence; duplicate/long copy filters destroyed a full term value | Reuse the shared explicit security meaning, preserve the complete collateral sentence and derive its typed flag from that same affirmative evidence. Preserve literal term cells separately from full rate conditions; hypothetical security is not evidence. |
| Dynamic field targeting deleted already proved registered optional facts | Research targets continue to bound collection. Preserve only registered, typed, exact grounded facts encountered in the same capture, without new searches or model calls. Final current-origin/type/currency/condition gates still apply. |

The fixes use document structures and financial meanings, without a Manulife
bank-code/hostname acceptance exception. Parser version is `fpds-parse-chunk-v12`;
process version is `2026-10-06-native-information-proof-v2`. Shared prompts,
atomic evidence chunks, deterministic extraction, final accuracy gates and cache
fingerprints were updated together. Complete native rate records are required
at the final gate: shortening a quote cannot drop attached conditions.

## Automatic exclusions retained

- USD savings: the detail has a numerical rate, but the retained evidence does
  not establish an unconditional scalar annual rate with complete applicable
  balance/annual-unit conditions. A bare percentage or another account's annual
  wording cannot replace that proof.
- Investment savings account: the family contains CAD/USD pricing; the selected
  inputs do not prove one product-specific denomination, annual rate and fee
  combination. No currency selection or inherited fee/annual basis is invented.
- GIC: the discovered official page is a family with different long-term,
  short-term and TFSA payout/redemption regimes. It is not converted into a
  single accepted product by mixing rates and withdrawal terms. No new GIC
  variant or extra optional-only research was added.

These exclusions describe the verified-input boundary, not a claim that the
bank never discloses the facts. They stay outside Public, with no human queue.

## Publication and independent verification

Private one-off artifacts are under `tmp/manulife-improvement-20261006/` and the
existing private object-storage operations prefix. No recovery menu, scheduler
or permanent remediation feature was added. Original before-images, captures,
checksums, stored extraction JSON, Run metadata and per-field links are retained.

The first operation ran four new scoped Runs through ordinary extraction,
stored-artifact loading, normalization, current-origin validation, automatic
promotion and aggregate refresh. Five candidates passed and two were excluded.
Live readback initially exposed four products: the deployed Public interpreter
could not recognise the new collateral wording. A bounded second ordinary Run
used the same source to retain the explicit standard secured boolean as well
as the complete sentence. It produced a new automatically approved LOC version,
then normal refresh made all five visible. This is a generic typed-fact fix,
not manual editing or a security bypass. There are six approval events across
five unique products, eight new candidates and zero manual reviews.

Final readback verified:

- All five live anonymous API details and actual website details (HTTP 200).
- 23 current field links against exact retained bytes, chunk offsets, official
  URLs and the same-bank/country Run-selected snapshot/parse joins.
- Required facts, source-language financial conditions, typed optional facts,
  valid acceptance receipts and no private evidence/internal identifiers exposed.
- All five original Runs, seven original candidates, 25 original Run-source items,
  70 existing bank documents and 100 existing snapshots unchanged.
- 435 unrelated canonical products and original facts in 1,454 versions preserved;
  four prior versions superseded through ordinary versioning. No old financial
  values were restored to fill Public.
- US products unchanged and previously published unrelated CA products unchanged
  except normal snapshot/freshness metadata.

Final verification/check receipts remain in the local private task directory.
Automatic approval review rejected an optional additional external archival
copy because exact destination/payload approval was not established. That copy
was not transmitted; ordinary publication/evidence storage completed earlier.

Final CA snapshot: `agg_eskLZZ642u_s9b4j`. Provider calls and Admin API calls for
both direct operations: zero. Data publication succeeded against the serving
Public environment. This work does not claim a production API/Worker deployment
or a new live paid Admin collection yield; deploy the matching API/Worker code
for subsequent ordinary collections and verify its process-version receipt.

## Regression and repository checks

- Worker: 783 behavior tests; API: 621 behavior tests. Test process exit codes
  recorded independently of PowerShell stderr formatting.
- Native fixtures: official captured HTML bodies/PDF page text with source URLs,
  capture times and raw hashes; renamed other-bank information-box replay proves
  the structure is generic through the actual stored-artifact/current-origin path.
- Negative checks cover truncated default conditions, missing/duplicated owners
  and note targets, foreign companions, unrelated pricing, source/route mismatch,
  actual foreign denomination, conditional security and shortened native quotes.
- `git diff --check`, changed-document Markdown reference checks and foundation
  environment baseline validation are recorded in the final private checks.
- The full foundation entrypoint encountered a pre-existing broken link in the
  ignored scratch copy `tmp/public-top5-20261004/app/README.md`. That unrelated
  artifact was preserved; the complete foundation entrypoint is not claimed to
  pass. Application behavior suites and focused changed-document checks pass.

Official evidence: [Infinite](https://www.manulifebank.ca/personal-banking/credit-cards/visa-infinite.html),
[Infinite information box](https://www.manulifebank.ca/documents/personal-banking/credit-cards/manulife-visa-infinite-card-rates-fees.pdf),
[Platinum](https://www.manulifebank.ca/personal-banking/credit-cards/visa-platinum.html),
[Platinum information box](https://www.manulifebank.ca/documents/personal-banking/credit-cards/manulife-money-plus-visa-platinum-card-rates-fees.pdf),
[Current rates](https://www.manulifebank.ca/current-rates.html),
[Manulife One](https://www.manulifebank.ca/personal-banking/mortgages/manulife-one.html),
[Bank Select](https://www.manulifebank.ca/personal-banking/mortgages/manulife-select.html),
[Line of credit](https://www.manulifebank.ca/personal-banking/loans/line-of-credit.html),
[USD savings](https://www.manulifebank.ca/personal-banking/bank-accounts/us-dollar-high-interest-chequing-savings-account.html),
[ISA](https://www.manulifebank.ca/personal-banking/investments/investment-savings.html),
[GIC family](https://www.manulifebank.ca/personal-banking/investments/guaranteed-investment-certificate.html).
