# Larger legacy recovery batch - 2026-09-30

Status: Completed; data applied and ordinary Public API/BFF/list/detail verified.

## Outcome

The Product Owner requested larger batches. This operation assessed **120
previously unchecked inactive manifest products across 40 banks**: CA 69 / US 51.
Four duplicate source references reduced the initial fetch set to 116 URLs.
114 fetched and parsed successfully, covering 118 products. Two products stopped
at fetch; no acceptance rule or safe-fetch boundary was relaxed.

- Restored Tangerine **No-fee daily Chequing Account** automatically.
- 117 products remain excluded for incomplete current evidence; two remain
  excluded after fetch failure. These are operation outcomes, not a claim that
  future official evidence can never make them eligible.
- Canonical and Public API totals are CA **6** / US **0**. The original
  355-product manifest now contains **349 inactive** products.
- New collection provider/model calls and input/output tokens: **0**. This does
  not measure coding-assistant conversation, hosting, network or storage costs.
- No human review, permanent feature, runtime change or deployment was added.
  The preceding RBC/BMO zero-value runtime fix remains separately awaiting
  deployment confirmation.

| Product type | Products checked |
|---|---:|
| Credit card | 50 |
| Chequing | 26 |
| Savings | 22 |
| Mortgage | 7 |
| Personal loan | 6 |
| GIC/CD | 5 |
| Line of credit | 4 |

## Evidence and restoration

Tangerine product `prod_rgU7RYZTn2B7KlVb` advanced from version 2 to **3**.
The official detail H1 matches the historical product. Its current complete
parsed sections prove the unchanged native monthly fee 0, minimum balance 0,
and unlimited daily transactions flag true. Optional historical descriptions,
transfer benefits and promotional eligibility were omitted when unsupported.
No transaction count, interest rate or transaction fee was invented.

The directly linked Account Terms explicitly state the denomination deducted
from this Chequing Account. The operation checks the actual English section I
heading and its following content through section J, as well as the live detail
links. This establishes CAD for the exact account. It does not borrow a currency
from a travel price, companion account or country default. Full parser chunks,
actual source origins and current capture hashes remain attached privately.
The linked fee schedule was also captured; neither support source was added to
the persistent registry.

The first execution stopped after capture/parse because the private section
check matched a table-of-contents entry. No candidate or canonical write occurred
at that point. The check was corrected to use the actual H2 section boundaries;
positive and missing-section negative checks passed. Processing resumed from the
same persisted captures with verified hashes, without another fetch or model
request. Normal normalization, validation/routing, automatic promotion and
aggregate refresh then completed successfully.

Run: `run_20260930_192555_tangerine_chequing_collect_cfMvusPJ`.
Candidate: `cand-742eed6f1c82af76`.
Version event: `pver_7ZcQ3xTSR80-10Yc`.
CA aggregate: `agg_JysUSYzeHfJBYkDg`, refreshed 19:29:20 UTC.

## Remaining exclusions and economical next step

All 311 matching historical candidates were considered for unchanged full-context
reuse. No candidate passed by reuse alone. Final financial exclusions overlap:
117 lack verified applicable currency, 116 lack one or more comparison essentials,
and 73 lack supported exact identity under that reuse path. Current-page field
support was also screened locally to select promising follow-ups; numeric matches
alone were never treated as product applicability or a publish decision.

Examples:

- RBC/Scotiabank card CAD mentions often concern vouchers, subscriptions, travel
  prices or insurance limits. They do not establish the card's required facts.
- Coast Capital pages combine base fees, discounts and several account columns.
  These were not flattened into unconditional values.
- Vancity Access has reusable fee/count evidence but no resolved exact product
  currency card in the previously captured catalogue. It remains excluded.
- First Citizens Online Savings has current detail facts. Its linked personal
  disclosures and deposit agreement were fetched, but did not supply a complete
  applicable proof accepted by the unchanged flow. Unrelated commercial-payment
  currency clauses were not used.
- `BMO-SAV-005` lacks a usable captured-source official allowlist and is a
  supporting page, not a product detail. `AUTO-RB-SAV-103d3e85b3` retained an access
  challenge after bounded browser fallback. Both remain excluded.

Four unique support URLs were fetched for targeted follow-ups: two Tangerine
pages and First Citizens disclosures/agreement. Only the successful Tangerine
candidate entered the normal persistent processing flow. Failed preflights were
kept as local diagnostic results, without paid extraction or duplicate DB runs.

The next private queue has **182 products across 20 banks** with source IDs not
yet present in the accumulated preflight receipts. Continue with 100-120 product
batches from that queue. Revisit already checked exclusions only when a new
applicable official source, changed source content or demonstrated parser defect
provides a concrete reason. Do not repeat paid extraction against unchanged gaps.

## Verification and private evidence

Ordinary Public API and Public BFF both return CA 6 / US 0 as applicable.
The list and restored product detail contain Tangerine, with native numeric
zeros and boolean unlimited flag. Private receipts and evidence quotes are absent.
An initial list/BFF response retained five products while the existing caches
revalidated. After expiry/revalidation, the final checks passed at 19:36 UTC;
no cache configuration, deployment or force-publish shortcut was used.

- Independent DB readback: exactly one canonical product changed; the other
  **433 canonical rows**, all **311 historical candidates** and registry rows
  are unchanged. Previous version 2 of the restored product retains the exact
  pre-operation payload; all three versions and original evidence remain available.
- All **six active products** pass fresh sanitizer replay from their approved
  candidates and persisted field evidence, plus receipt validation.
- One new approved candidate, two local model-execution stage records, no paid
  extraction/normalization requests, no running ingestion jobs and no pending
  or new human reviews.
- Native numeric zeros and boolean true checked on the restored product;
  irrelevant transaction fee/count values remain absent.
- Accuracy and maintenance regression suite: **31 tests passed**. Private
  account-section success/failure checks passed. `git diff --check` and UTF-8/94 relative-link checks passed; no runtime
  code changed in this slice.

Private artifacts under ignored `tmp/`: `oneoff-broad-selection.json`,
`oneoff-broad-before.json`, `oneoff-broad-historical.json`, per-source raw captures
and chunks, `oneoff-broad-preflight.json`, `oneoff-broad-assessment.json`,
`oneoff-broad-potential.json`, `oneoff-broad-outcomes.json`,
`oneoff-broad-next-unchecked.json`, `oneoff-broad-db-readback.json`,
`oneoff-broad-public-readback.json`, and `oneoff-tangerine-*` operation receipts.
Do not rerun an execute script; inspect its plan/result and current DB state.
