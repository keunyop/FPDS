# One-off TD legacy recovery - 2026-09-30

Status: Data applied; automatic acceptance, with no runtime feature added.

## Scope and outcome

The Product Owner clarified that legacy recovery is a one-off data operation,
then authorized one bank and 5-10 excluded products. Inspected eight existing
TD CA products (five chequing, three savings) and five registered supporting
sources. Revalidated the five chequing products using current detail pages and
one shared official fee table. Savings did not enter collection in this batch.

- TD Unlimited Chequing Account was automatically restored as the same product:
  `prod_UdO8cpEjURq1VhJz`, candidate `cand-008d6a399a806329`, version event
  `pver_OAFXbKqj7ZYnsca0` (product version 13).
- Four chequing candidates were automatically excluded; no human review was
  created. The three savings products remain inactive without a paid retry.
- Current canonical/Public API totals are CA 3 / US 0; 352 manifest products
  remain inactive. The other 354 manifest product versions/payloads are unchanged.
  Across all 434 canonical rows, only this product changed; the other 433 are
  unchanged. The global inactive count is 431, including earlier excluded rows
  outside the 355-product cutover manifest.
- New collection model requests: **0**; new input/output tokens: **0**.
  This excludes the coding assistant conversation, hosting and storage costs.
- No Admin/Public runtime, menu, scheduler, registry row or deployment changed.
  This operation does not need a new runtime deployment. The earlier recovery
  code's separate deployment status remains as previously reported.

## Evidence and automatic processing

The preflight safe-fetched eight detail pages and five supporting sources.
Five historical candidates had full evidence contexts still present verbatim
(after whitespace normalization) in their current official detail captures.
Only matching contexts were eligible for reuse; a quote alone was insufficient.

The current [TD fee table](https://www.td.com/ca/en/personal-banking/products/bank-accounts-fees-services-charges)
has one active CAD chequing tab and exactly the five target product columns.
The one-off script checks that DOM structure and every exact column name before
extracting the explicitly written ISO currency. Other tabs, FX wording, country
and dollar symbols cannot supply currency. Shared evidence keeps its own source,
snapshot, chunk and URL; it is never relabeled as detail-page evidence.

Execution freshly captured and parsed five detail URLs plus that one shared
fee-table URL through the existing snapshot/parser services. All six captures
succeeded on their first attempt. The common table was captured once during
this execution and reused for all five candidates, after the separate preflight.

The private one-off script reconstructs candidate records from unchanged
previously grounded values, binds exact full contexts to current persisted
chunks, and resolves their real source origins from DB joins. It calls the
unchanged shared `sanitize_candidate`, then the normal validation persistence,
automatic promotion and aggregate refresh. Currency grounding is recorded as
local DOM verification; no model request or human decision is invented.
Original candidate and model provenance remain explicit. Old records are intact.

Accepted TD Unlimited fields are numeric monthly fee 17.95 CAD, numeric 4,000
monthly-fee rebate balance, and boolean unlimited transactions. This balance
retains the existing chequing fee-rebate semantics; it is not an opening deposit.
Unverified descriptions, eligibility and paraphrased waiver text are omitted.
Additional-transaction charges were removed from the base transaction-fee field
before automatic checking. No financial value was manually approved.

| Candidate | Automatic result | Missing essential proof |
|---|---|---|
| TD Unlimited Chequing Account | Accepted | None |
| TD All-Inclusive Banking Plan | Excluded | Accepted transaction-count/unlimited evidence |
| TD Every Day Chequing Account | Excluded | Accepted transaction-count evidence |
| TD Minimum Chequing Account | Excluded | Minimum-balance and transaction-count evidence |
| TD Student Chequing Account | Excluded | Accepted transaction-count/unlimited evidence |

These exclusions describe the retained evidence contract, not a claim that the
bank lacks the feature. Do not retry unchanged inputs or weaken acceptance.
The savings subset needs separate proof of the applicable rate, annual basis
and balance conditions; this batch did not extend savings support mapping.

## Operational record and verification

- Collection: `collection_8i8irLWSS1CBb4BX`.
- Run: `run_20260930_175132_td_chequing_collect_4wwpRXwH`.
- Aggregate snapshot: `agg_czWJKhMNRdS8501M`.
- Read-only candidate validation rehearsal: five candidates, one automatic pass,
  four exclusions; no DB/object writes or provider calls.
- Six one-off safety checks passed: valid DOM, wrong currency, missing active
  tab, wrong product columns, changed full context and wrong evidence origin.
- Existing accuracy/maintenance regression suites: **29 tests passed**.
- Independent DB readback confirms the accepted receipt against persisted
  evidence from two genuine origins, native types, unchanged registry and five
  original candidates, unchanged other products, and zero new/pending reviews.
- At 18:02:56Z, independent API, Public BFF and ordinary list/detail URLs all
  confirm the new product and CA 3 / US 0. Private receipts and quotations remain
  absent. Initial list/BFF reads held the previous response until normal cache
  revalidation completed; no cache or application code was changed.
- Repository doctor, final diff, UTF-8/whitespace and relative Markdown links pass.

The first persistence attempt used an invalid candidate state; its transaction
rolled back with zero candidates/products written. The state was corrected to
`draft`, and the same stored captures were resumed without refetching or model
calls. Original extraction and normalization execution references were separated
before successful persistence. This was an operation-script correction, not a
runtime schema or acceptance change.

Private before-images, source captures, dry-run/safety results, scripts and final
readback are under ignored `tmp/oneoff-td-*`. The scripts are single-use and are
not a maintained recovery interface. Preserve them for audit; do not rerun the
execution or resume entrypoints. Future batches should first diagnose current
exact-context reuse and applicable shared evidence within a separately bounded
scope, using the existing automatic gates.
