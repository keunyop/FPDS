# Goal: Vancity Product Coverage and Comparison-Quality Recovery

## Objective

Explain why the completed Vancity collection leaves most candidates in Review,
map Vancity's current official retail product and comparison-condition sources,
implement reusable evidence-grounded improvements for Vancity's site shape, and
recollect only Vancity until the attainable Public-ready coverage is materially
improved without weakening approval safety.

## In Scope

- The latest Vancity candidates, review tasks, validation issues, field
  evidence, generated sources, snapshots, and official-grounding results
- Current official Vancity product detail, account/card/rate/fee/disclosure,
  mortgage, loan, and line-of-credit pages needed by the seven active Product
  Types
- Bounded source discovery, product/source relationships, parsing, evidence
  retrieval, extraction, normalization, and official-grounding fixes supported
  by reproducible Vancity evidence
- Vancity-specific routing only where the official site has a genuinely unique
  structure and a generic safe rule would be less precise
- Focused fixtures/regressions, a Vancity-only recollection, and full downstream
  candidate/Review/canonical/Public audit

## Out of Scope

- Collection of any bank other than Vancity
- Invented, inferred, rounded, or silently coerced product facts
- Manual Review approval or direct canonical/Public value edits
- Relaxing exact-product identity, official-domain, exact-quote, SSRF, country,
  essential-field, Review, or publication gates
- New Product Types/countries, personalized recommendations, public raw
  evidence, BX-PF writes, or unrelated Admin/Public UI work
- Modification or cleanup of the existing unrelated Bankoom Public worktree

## Acceptance Criteria

- Every active Vancity Review candidate is grouped by exact blocker, missing
  comparison requirement, source role, and current official evidence gap.
- A current official Vancity product/source inventory is recorded for all seven
  active Product Types, including separate rate/fee/terms sources where facts
  are split from detail pages.
- The implementation captures only exact-product or explicitly governed
  product-family evidence, retains source-language qualifications, and adds
  deterministic regression coverage for each changed rule.
- Relevant API/discovery/pipeline tests pass and `git diff --check` passes.
- Every stateful recollection is constrained to `country_code=CA` and
  `bank_code=VANCITY`; no other bank is launched.
- Replacement runs finish without source failure/partial state, materially
  reduce Vancity Review blockers where official evidence exists, and report
  candidates that must safely remain in Review.
- Any normal automatic approvals and aggregate refresh effects are verified
  against canonical and latest Public data without manual approval.

## Verification

- Read the shared dev database without exposing credentials.
- Inspect exact Vancity source-catalog scope before each launch.
- Use only current official Vancity pages for financial facts and retain exact
  URL/quote lineage in the normal evidence pipeline.
- Compare before/after counts by Product Type, candidate state, validation
  issue, missing essential field, canonical promotion, and Public visibility.
- Re-read this goal, update the development journal and affected baseline docs,
  inspect the final diff, and remove `goal.md` only after all criteria pass.

## Pause Checkpoint - 2026-08-16

### Current State

- Work is intentionally paused at the Product Owner's request. This goal is
  not complete, `goal.md` must remain, and WBS `5.35` must remain `In progress`.
- The latest Vancity-only collection is still allowed to finish in the
  background because terminating the serial runner can leave runs stuck in
  `started`. Do not launch a replacement until this collection is terminal and
  audited:
  - collection: `collection_pC4G-nfcCpkakYrE`
  - correlation: `corr_syRk20gX8Sf7uoUd`
  - exact scope: `country_code=CA`, `bank_code=VANCITY`
  - last observed state: five runs `started`, zero candidates, zero Review
    tasks, no run errors, and no partial flags; `chequing` was in extraction
    and the other four runs were in serial source-catalog collection
  - run IDs: `run_20260816_065118_vancity_chequing_collect_QaA5CN16`,
    `run_20260816_065118_vancity_credit-card_collect_D5wbgPpV`,
    `run_20260816_065118_vancity_gic_collect_qEoaBxcc`,
    `run_20260816_065118_vancity_line-of-credit_collect_NMxXWIdP`, and
    `run_20260816_065118_vancity_personal-loan_collect_yaGA0ZQp`
- The completed pre-fix comparison baseline is
  `collection_xQrVsioO6c2IcvcX` / `corr_LHaKVlpvuPzAxNF1`: seven completed,
  zero failed/partial, 46 candidates, 17 approved, 29 in Review, 32 Review
  tasks, and validation 14 pass / 32 error.

### Completed Implementation And Evidence Work

- Vancity browser DOM snapshots now retain the structured CMS payload needed
  for discovery. Structured JSON unwrapping, nested `Title` to `Link`
  extraction, internal Sitecore filtering, and case-insensitive alias
  deduplication are covered by regressions.
- Exact official Vancity registries cover all seven active Product Types. The
  curated catalog contains 60 rows after adding the official insured-mortgage
  route `5-year-fixed-term-fixed-rate-insured` as `VANCITY-MTG-014`; migration
  `0041` is applied in shared development.
- Vancity-specific deterministic extraction/grounding was strengthened for
  chequing included-transaction wording, credit-card label/value ordering and
  multi-product pages, GIC cross-sell markers, and the Creditline/Personaline
  comparison table. The line-of-credit expansion occurs only when every
  required table value is grounded.
- Deposit-only numeric ceilings no longer invalidate lending rates. Mortgage
  stress-test/MQR values are excluded from product-rate grounding. Rate
  evidence older than five years is forced to Review; known stale Vancity rate
  support is not silently treated as current.
- Last passing regression totals: discovery 60 tests, API source catalog 160
  tests, and worker pipeline 435 tests.

### Resume From Here

1. Read the repository startup documents, this checkpoint, and the latest
   development-journal entry before editing or launching anything.
2. Check the existing collection once with:
   `api/service/.venv/Scripts/python.exe tmp/fpds_admin_collection_goal_tool.py wait --collection-id collection_pC4G-nfcCpkakYrE --timeout-seconds 1 --poll-seconds 1 --brief`.
   If it is not terminal, do not start another Vancity collection.
3. Once terminal, run the detailed collection summary and compare candidate,
   Review, validation, canonical-promotion, and Public-projection outcomes by
   Product Type against the completed baseline above. Pay particular attention
   to the eight actual cards on seven routes, seven GICs, expanded
   Creditline/Personaline variants, the no-rate HELOC, and the Fair and Fast
   Loan's current-detail versus stale-rate evidence.
4. Refresh/audit the Public aggregate only after the collection is terminal.
   Do not manually approve Review tasks or edit canonical/Public facts.
5. Before completion, rerun affected suites, run `git diff --check`, inspect the
   full diff, restore tracked test-generated artifacts, and remove the ignored
   research helpers only after they are no longer needed. Preserve the
   pre-existing `tmp/fpds_admin_collection_goal_tool.py` and all unrelated
   Bankoom Public worktree changes.
6. Update the journal and WBS only from verified terminal results. Delete this
   file only when every acceptance criterion above is satisfied.
