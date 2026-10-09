# Citibank direct collection and generic corrections - 2026-10-09

Status: complete for local generic corrections and verified current publication.
Private operation: `citibank-direct-20261009`. No FPDS Admin API, paid provider,
manual product approval or permanent recovery workflow is used.

## Latest ordinary results

The six latest US/CN scopes started at 2026-10-09 16:14:23 UTC (09:14 PDT),
batch `collection_mFe0sgs6_Oqp_M-k`. Collection used process v11/parser v20.

| Product type | Candidates | Successful / failed sources | Approvals |
|---|---:|---:|---:|
| Credit card | 20 | 20 / 0 | 0 |
| Personal loan | 1 | 12 / 0 | 0 |
| CD | 1 | 1 / 0 | 0 |
| Mortgage | 1 | 1 / 0 | 0 |
| Savings | 0 | 0 / 0 | 0 |
| Checking | 0 | 0 / 0 | 0 |

All 23 candidates were excluded automatically; no review is needed. Savings and
checking stopped at `no_eligible_detail`, with unavailable or category/overview
pages failing named-product validation. The older line-of-credit scope is from
August 29 and is historical context, not part of today's batch. It was not
recollected or restored.

Thirty-four original selected snapshots were independently retrieved and their
raw SHA-256 verified. Direct current acquisition inspected the same 34 registry
URLs. Additional required-only browser acquisition was bounded to one attempt
per URL: sixteen attempts, fifteen successful renders and one failed MileUp
render without a retry. Original snapshots and current
captures are separate. Only current captures feed publication.

## First actual losses and reusable corrections

1. **Acquisition missed empty DOM price bindings.** The static card HTML had
   literal `data-id` rate/fee slots and an unlinked pricing control; prices and
   the complete legal URL appeared after rendering. Existing pattern detection
   did not recognize that representation. Shared native binding detection now
   finds the owned label within four bounded ancestors, preserves inline-only
   name markup, and rejects foreign names, calculators, optional-only requests,
   ordinary empty containers and exhausted/already-attempted budgets. The
   snapshot fetch and Admin essential-research planner use the same detector.
   This never turns a data attribute into a financial fact.
2. **Rendered purchase disclosures were not retained as complete units.** A
   uniquely named Pricing Details block can contain separate paragraphs for
   purchase/transfer offers, variable ranges, creditworthiness, plan fees,
   penalty/default triggers and application conditions. The parser retains the
   entire bounded record. Purchase clauses must explicitly bind a numeric APR
   interval to purchases; cash-only or balance-transfer-only copy is insufficient.
   Prices/range endpoints/promotions never become scalar interest rates. An
   independently labelled unconditional annual fee is separate from other card
   prices; waivers, conflicts and unresolved conditions remain blocking.
3. **Full lending APR evidence was shortened or omitted.** The actual personal
   loan note contains its full APR interval, lowest-rate prerequisites, automatic
   payment discount, relationship discounts, repayment terms, a labelled payment
   example and a default increase. The owned-record path preserves all of it and
   the literal repayment sentence. Its reciprocal Go back link points to two
   responsive numeric callers, both linking to the same uniquely identified note;
   it is navigation rather than an unresolved financial disclosure. Missing or
   conflicting callers still fail closed. An exact original-byte loan replay now
   passes ordinary automatic validation; that historical replay is diagnostic only.

Parser v22 and process `2026-10-09-owned-pricing-disclosure-proof-v13` advance
together with shared instructions and the existing code-bound grounding cache.
There are no bank/product-name exceptions, invented values, identity relaxations,
weaker checking/withdrawal/security requirements or review overrides.

## Current-input assessment and remaining exclusions

Current ordinary service replay produces eight automatic passes: Citi Personal
Loans, Strata Elite, Simplicity, Diamond Preferred, Strata Premier, AAdvantage
Globe, Double Cash and Strata. Seven cards plus one personal loan are distinct
products. All eight subsequently passed actual stored-origin validation and were
published through ordinary automatic promotion and aggregate refresh.

The fifteen other candidates remain excluded: two lending/deposit categories and
thirteen cards with unresolved essentials, product boundaries, identity/name
scope, incomplete pricing, waivers/qualifications or a failed render. A stale AT&T
route returns a page-not-found identity. Exact suffixes/World Elite/World Legend
names are not silently collapsed. Costco retains an unresolved annual-price
condition. A waived or incomplete fee never becomes an invented zero. Checking
and savings discovery results do not prove that Citi offers no such accounts.
The directly inspected bank-accounts overview still requires home-ZIP pricing
and does not supply one complete comparable product; the savings seed is not
accessible as a usable detail, and CD/mortgage inputs lack current complete facts.

## Verification and release boundary

- Independent API final suite: 650 tests pass.
- Final affected Worker suite: 59 tests pass; final render/official-source suite
  after the last calculator-boundary tightening: 18 tests pass.
- Full Worker initial run: 956 tests, three failures. Its new empty-container
  boundary failure was corrected and independently reverified. The other two
  are pre-existing National/Oaken fixture-hash tests; four manifest mismatches
  inspected in this operation are byte-identical to Git HEAD. Expected hashes
  and original source files were not changed.
- Ten immutable current official-source gzip fixture hashes, Python syntax,
  strict UTF-8/JSON, foundation baseline and `git diff --check` pass.

Runtime deployment is separate. Serving health at the operation baseline is v11;
API and Worker must be released together at v13 for future ordinary Admin runs.
No serving restart/deployment or schema migration is performed by this task.
Serving health was checked again after publication and remains v11. Local code
verification and this bounded data publication do not deploy the future Admin
collection runtime. Publication and origin/rollback receipts remain private.

## Actual publication and independent readback

Ordinary stored-origin reassessment accepted exactly eight candidates and
excluded fifteen, with zero manual reviews, provider calls or Admin API calls.
A transaction rollback rehearsal restored canonical products, versions and
refresh requests exactly before actual promotion. Two operation-owned refresh
requests completed normally as `agg_cY2GcCw9cCDisYh_`.

At 2026-10-09 18:12:11 UTC, independent database and anonymous Public readback
verified all eight products and 25 exact field-to-current-capture evidence links.
All eight web details return HTTP 200 and contain the full APR conditions; the
personal loan also displays the literal repayment terms. Public US increased
from 28 to 36; CA remained 120. Unrelated Public values and 465 unrelated
canonical rows are unchanged; 1,549 original version facts remain preserved
(with six ordinary previous-version supersessions). Seven original Runs,
23 original candidates, 34 original Run-source records, 52 bank documents and
225 original snapshots are unchanged. No private evidence fields appear in Public.

Published detail links:

- [Citi Double Cash ® Card](https://www.switchabank.com/products/prod_wKbld436bFNExuZj?country_code=US)
- [Citi Simplicity ® Credit Card](https://www.switchabank.com/products/prod_zOnvKhIVZlYWS3-2?country_code=US)
- [Citi Strata Elite ® Card](https://www.switchabank.com/products/prod_IX4XMfWB2L8TEks3?country_code=US)
- [Citi Strata Premier ® Card](https://www.switchabank.com/products/prod_NVY6ar64WLuBeBP3?country_code=US)
- [Citi Strata ® Card](https://www.switchabank.com/products/prod_3bDNKlefVGFOJxVR?country_code=US)
- [Citi ® / AAdvantage ® Globe ™ card](https://www.switchabank.com/products/prod_tzs6ftUM9dOW7y_h?country_code=US)
- [Citi ® Diamond Preferred ® Credit Card](https://www.switchabank.com/products/prod_l01UKijDpilIW9a1?country_code=US)
- [Citi® PERSONAL LOANS](https://www.switchabank.com/products/prod_YVG2_MSOSUtZEDG7?country_code=US)
