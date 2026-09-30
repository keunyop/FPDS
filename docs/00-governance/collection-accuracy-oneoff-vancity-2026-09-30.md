# One-off Vancity legacy recovery - 2026-09-30

Status: Data applied; automatic acceptance and independent DB/API/Public checks pass.

## Scope

The Product Owner requested continuation for excluded products. This batch
selects five inactive Vancity chequing products from the original 355-product
manifest. Recovery remains a bounded one-off data operation, with no new feature,
runtime code, deployment, manual product approval or source-registry change.

The read-only rehearsal passed Essential Chequing and excluded four candidates.
Execution captured five official detail pages and the existing registered
[accounts catalogue](https://www.vancity.com/bank/accounts) through the normal
snapshot and parser services. The catalogue remains supporting entry evidence;
it never becomes a product candidate. A sixth detail/rate source was inspected
in preflight but is outside execution.

## Applied outcome

- Essential Chequing restored as existing product `prod_8THVnPgc2ov6luVB`,
  version 6, candidate `cand-bed11d21947007f6`, event `pver__YO25SS2nIGFYYz2`.
- Accepted values: CAD, numeric monthly fee 9.75, numeric monthly-fee rebate
  balance 1,500, and integer included transactions 25. The balance is a fee
  rebate threshold under the existing chequing contract, not an opening deposit.
  Unsupported optional facts, base transaction fee and unlimited flag are omitted.
- Five candidates completed normal validation: one approved and four excluded.
  No human reviews were created; pending reviews remain zero.
- CA 4 / US 0 on the Public API. Of the original 355 products, 351 remain inactive.
  Only the selected product changed among all 434 canonical products: the other
  433, all source-registry rows and five historical candidates are unchanged.
  There are 430 inactive rows globally, including rows outside the manifest.
- New collection model requests and input/output tokens: **0**. This excludes
  coding-assistant conversation, hosting and storage costs.
- Collection: `collection_Dtw9mGUgCi6zi3YR`.
  Run: `run_20260930_181406_vancity_chequing_collect_pFGfw8g5`.
  Aggregate: `agg_-0zxxdt9Hs3ctJke`, refreshed at 18:16:37Z.
- No runtime deployment is needed for this operation.

## Evidence and exclusions

Reuse requires the complete historical evidence context to match the current
official parsed context after whitespace normalization. Only unchanged native
values are eligible. Supporting evidence retains its actual document, snapshot,
chunk and URL, with original candidate/model provenance kept explicit.

Currency comes from the catalogue's native Product Selector currency property,
bound to exactly one card with an exact registered detail URL or alias. The
ISO name, display name, title and currency taxonomy path must agree. The raw
capture hash, JSON pointer, card title and link are retained in private mapping
metadata. Country, dollar symbols, unrelated cards and guessed URL case folding
cannot establish product currency. The senior/youth cards lack this property;
the Essential Plus uppercase link is not a registered alias, so it cannot match.

For Essential Chequing only, its historical integer transaction count 25 is
re-grounded in the current detail page's complete structured Perks component.
The exact count and transaction scope must match; no count is changed or inferred.
The shared sanitizer checks the resulting evidence, native types and semantics.
Extra-transaction charges are omitted from the base transaction-fee field.
Essential Plus's channel-limited unlimited allowance is explicitly omitted from
the account-wide unlimited flag.

| Candidate | Automatic result | Missing accepted proof |
|---|---|---|
| Essential Chequing | Accepted | None |
| Essential Plus Chequing | Excluded | Currency, applicable balance and transaction allowance |
| Chequing Plus for seniors | Excluded | Currency and monthly fee |
| Chequing Plus for youth | Excluded | Current identity, currency, fee and transaction allowance |
| Vancity Total Chequing | Excluded | Transaction allowance |

An exclusion means the retained evidence contract is incomplete, not that the
bank lacks the feature. Do not retry unchanged inputs or loosen acceptance.
The historical duplicate named Chequing Plus is outside this batch and remains
unchanged; the seniors candidate is selected by its exact existing identity.

## Verification

- Eight one-off safety checks pass: exact alias/native currency binding,
  unmatched cards, conflicting currency, wrong product URL, changed full context,
  wrong evidence origin, numeric string rejection and channel-only allowance.
- Existing accuracy and maintenance regression suites: 29 tests passed.
- Independent DB checks recompute the accepted receipt from two persisted
  evidence origins, verify native types and all before-images, and confirm ten
  local normalization/validation records with zero model tokens.
- At 18:22:46Z, API, Public BFF and ordinary list/detail URLs confirm the
  restored product and CA 4 / US 0. Private acceptance receipts and evidence
  quotes remain absent. Normal cache revalidation took about six minutes; no
  cache or application changes were made.
- Repository doctor, final diff, UTF-8 and relative Markdown link checks pass.

Private before-images, captured evidence, scripts, rehearsal and safety output
are stored under ignored `tmp/oneoff-vancity-*`. Scripts are single-use audit
artifacts, not a maintained recovery interface. Do not rerun execution.
