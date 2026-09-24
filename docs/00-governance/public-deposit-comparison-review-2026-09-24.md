# Public deposit comparison self-review

Date: 2026-09-24
Scope: the Product Owner selected growth proposal section C and requested
independent review of INDEXED GIC. This is the agent's bounded self-review,
not a separate human sign-off or a current-price audit of every bank.

## INDEXED GIC result

Public product `prod_uSp8IS79y44HSiyF`, Laurentian, CAD, approved version
`pver_Z8Y2Hmtq91nWwFDr` reproduces the reported conflict: scalar 5%, standard
3.3%, 540 normalized days / 18-month text, and a 5-year / 1825-day row at 5%.
No one of these values is selected as the correction.

The [official product page](https://www.laurentianbank.ca/en/personal/investments/gics/indexed)
was successfully retrieved directly with HTTP 200 after the web reader returned
502. Its current table says the offer is available until 2026-10-07 and lists
2/3/5-year Blue Chip issues dated 2026-10-13/15/14, respectively. The minimum /
maximum returns are 0/13%, 0/24%, and 4/60%. No 18-month term appears in the
retrieved page. Those are issue-specific investment-term bounds, not fixed
annual rates. They must not overwrite the legacy 5% or be converted to a fixed
annual guarantee. The original 2026-08-09 product issue still cannot be reliably
identified from the composite projection.

The bank's [Canadian Sustainable ActionGIC fact sheet](https://assets.ctfassets.net/b5xlbty9p8dy/3pU6PB2z5lKsjJG8PFYeIX/18e5be1ae6d0b52d237b307302fb2eb6/20240111_ESGFactSheet.pdf),
sections 1, 4 and 5, corroborates index-based, non-compounding term-return
semantics; that variant is not asserted to be the current Blue Chip offering.
The indexed search copy dated June 2025 was superseded for this audit by the
successful direct retrieval. Both the original Oaken official URL and Laurentian
URL returned HTTP 200 in the final link check.

Decision: generic indexed/market-linked detection excludes this record from
numeric comparisons and calculation. Detail retains approved source facts,
shows the short market-performance reason and links to the official bank.
Canonical fields remain unchanged. A future normal Admin review must identify
the exact variant/issue before replacing contradictory facts. No live Review
task, canonical correction, collection or publication was created.

## Oaken result

Public product `prod_mL9V64-_mjTai9Pb`, CAD, version `pver_zq7rmli_JKGxZwKC`,
contains 2.8% as both standard and displayed rate with zero minimum balance.
The [official savings page](https://www.oaken.com/oaken-savings-account/)
was read on this review date: its savings section displayed 2.80%, describes
an annualized rate subject to change, daily calculation and monthly payment,
and no minimum balance. An unrelated old GIC promotion appears elsewhere on
the page and was not treated as Savings evidence.

Decision: the reviewed annual-basis clarification applies only to that exact
product/version/currency/value pair. It does not change a rate, freshness date
or canonical record. Fix the initial scenario amount to 10,000, expose the
chosen horizon and describe simple-interest exclusions. A deposit-insurance
eligibility phrase had also been falsely treated as a conditional rate by the
existing interpreter; a narrowly tested insurance-phrase correction restores
its ordinary scalar interpretation without accepting real bonus conditions.

## Data audit and limits

Read-only transactions inspected all active CA 165 / US 51 products and only
the approved versions already pinned to deposit projections. Dropped tier and
promotion fields explain why checking headline numbers alone is insufficient.
The resulting deposit contract admits three CA Savings records (Oaken CAD,
RBC EUR and one Simplii USD record); each belongs to a separate currency group.
CA exclusions: 19 unknown annual basis, 12 promotional, 5 tiered, 2 market-linked.
US exclusions: 2 unknown basis, 2 tiered, 1 promotional. There is no eligible
published GIC/CD in this snapshot. All 216 products remain browsable; the
absence of a numeric candidate does not mean the product is unavailable.
These are conservative eligibility results, not judgments about bank quality.

Future approval must supply missing annual/APY meaning and matching maturity
facts; do not relax these gates merely to populate a list. QA uses labelled
synthetic GIC cases locally to verify functionality without publishing them.

## Verification record

- API full suite: 502 passed, including contradictory terms, indexed identity,
  promotion/reference qualifications, reviewed-version binding and invalid days.
- Public: 22 tests; lint, typecheck and final production build passed.
- Worker aggregate: 8 tests passed, including bounded qualifier preservation.
- Foundation harness: Admin 5 tests, Admin/Public typechecks and production builds
  passed; repository doctor and foundation baseline validation passed.
- Browser: 79 cases passed: 39 actual-data Home/detail/catalog checks, 36
  synthetic GIC/APY/conflict screens, and four finder locale/error-retry scenarios.
  Screens cover EN/KO/JA at 1440/768/exact 390px; checks include loading, empty,
  error/retry, same-currency/term filtering, changing GIC periods and minimums.
  No horizontal overflow or browser exceptions were observed. Analytics and
  feedback were blocked throughout; fixture products were never published.
- Final-build smoke: 15 additional checks passed across EN/KO/JA at 390px and
  existing deposit/card/loan catalog comparisons. Verified the positive initial
  amount, 44px amount control, focus, invalid/zero input and bank-link states.
- Compatibility replay of all 216 published products: 213 existing serialized
  responses were unchanged, excluding additive deposit terms and controlled
  evaluation time. The three intentional differences were Oaken's restored
  ordinary annual scalar and Laurentian/Vancity linked-return classification or
  source display; no other fee, loan, card, date or product field changed.
- Final diff and whitespace checks passed. Existing Product Owner proposal edits
  and unresolved Admin goal ownership were preserved.
- No external writes, deployment, collection, account operations or data migration.


## Remaining operational boundary

Implementation and local verification are complete. Production has not been
deployed. A separately authorized release should deploy API before Public and
verify after existing caches expire. The next ordinary manual Admin review
should resolve INDEXED GIC's exact issue and missing deposit rate/term semantics;
there is no forced collection, speculative correction or automatic publication.
