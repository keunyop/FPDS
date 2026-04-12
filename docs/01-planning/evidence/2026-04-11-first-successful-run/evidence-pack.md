# FPDS Prototype First Successful Run Evidence Pack

Date: `2026-04-11`
WBS: `3.9`
Status: `completed`
Gate posture: `Conditional Pass candidate`, pending `3.10` findings memo

## 1. Purpose

This evidence pack records the first live end-to-end TD Savings prototype run that reached:
- live discovery
- live snapshot capture
- parse and chunk persistence
- extraction
- normalization
- validation and prototype review routing
- read-only viewer export

It is intended to satisfy the `PB-07` requirement for a first successful run evidence pack and to give `3.10` a stable input for the findings memo.

## 2. Run Scope

Target product detail sources:
- `TD-SAV-002` `TD Every Day Savings Account`
- `TD-SAV-003` `TD ePremium Savings Account`
- `TD-SAV-004` `TD Growth Savings Account`

Supporting source-type coverage:
- `TD-SAV-005` current values source
- `TD-SAV-007` governing fee PDF
- `TD-SAV-008` governing interest PDF

Shared correlation id:
- `corr_20260411_3901`

Stage run ids:
- discovery: `run_20260411_3901_discovery`
- snapshot: `run_20260411_3901_snapshot`
- parse: `run_20260411_3901_parse`
- extraction: `run_20260411_3901_extract`
- normalization: `run_20260411_3901_normalize`
- validation: `run_20260411_3901_validate`
- viewer export target run: `run_20260411_3901_validate`

## 3. Acceptance Mapping

| Area | Result | Evidence |
|---|---|---|
| Source coverage | Met | all 3 target products appear in the live viewer payload |
| Source type coverage | Met | parse output includes HTML detail, current values HTML, and governing PDF sources |
| Pipeline execution | Met | discovery through validation and viewer export all completed |
| Reviewability | Met | live viewer payload exported to `app/prototype/` and can be opened in the static viewer |
| Evidence linkage | Met | candidate-level evidence links exported with section anchors and excerpts |
| Findings closure | Pending | covered next in `WBS 3.10` findings memo |

Because the findings memo is still pending and all three target candidates currently land in `validation_error`, this pack should be read as a `Conditional Pass` input rather than final Gate B closure.

## 4. Stage Summary

Discovery summary:
- selected total: `12`
- discovered total: `10`
- warnings: `391`
- warning pattern was dominated by `out_of_registry_link` and `cross_domain_link`, which is expected under the approval-first registry policy

Snapshot summary:
- source total: `6`
- stored count: `2`
- reused count: `4`
- failed count: `0`

Parse summary:
- source total: `6`
- stored count: `2`
- reused count: `4`
- failed count: `0`
- total new evidence chunks persisted in this run: `39`

Extraction summary:
- source total: `3`
- stored count: `3`
- failed count: `0`
- extracted field count: `67`
- evidence link count: `43`

Normalization summary:
- candidate count: `3`
- field evidence link count: `43`
- all three candidates persisted successfully

Validation and routing summary:
- candidate count: `3`
- queued count: `3`
- review task count: `3`
- auto validated count: `0`
- each candidate routed with `review_reason_code=validation_error`

Viewer export summary:
- candidate count: `3`
- review task count: `3`
- evidence link count: `43`
- active schema: `public`

## 5. Source-By-Source Status

Snapshot and parse coverage:

| Source ID | Type | Role | Snapshot | Parse | Chunk Count |
|---|---|---|---|---|---|
| `TD-SAV-002` | HTML | target detail | `reused` | `reused` | `20` |
| `TD-SAV-003` | HTML | target detail | `fetched` | `stored` | `20` |
| `TD-SAV-004` | HTML | target detail | `reused` | `reused` | `22` |
| `TD-SAV-005` | HTML | current values | `fetched` | `stored` | `19` |
| `TD-SAV-007` | PDF | governing fee PDF | `reused` | `reused` | `49` |
| `TD-SAV-008` | PDF | governing interest PDF | `reused` | `reused` | `27` |

This satisfies the acceptance requirement that at least one HTML detail source, one current values source, and one governing PDF source appear in the parse/evidence path.

## 6. Reviewable Candidate Summary

| Source ID | Product | Product Type | Validation Status | Review Task | Evidence Links |
|---|---|---|---|---|---|
| `TD-SAV-002` | `TD Every Day Savings Account` | `savings` | `error` | `review-ee7d9aded05be1e2` | `14` |
| `TD-SAV-003` | `TD ePremium Savings Account` | `savings` | `error` | `review-055dad56cf0d43cc` | `14` |
| `TD-SAV-004` | `TD Growth Savings Account` | `savings` | `error` | `review-c451a2ba4c341cd6` | `15` |

Observed caveat:
- all three target candidates currently carry `validation_issue_codes=["required_field_missing"]`
- this does not invalidate the first successful run, because reviewable output, evidence linkage, and viewer export all exist
- it does mean the run should be treated as `Conditional Pass` input until the findings memo records the normalization and validation gaps

## 7. Sample Evidence Linkage

Sample A. `TD Every Day Savings Account` monthly fee:
- field: `monthly_fee`
- candidate value: `0.0`
- source id: `TD-SAV-002`
- anchor: `Section account-fees`
- excerpt:
  `Monthly Fee $0 ... Additional Transactions $3.00 each`

Sample B. `TD Growth Savings Account` boosted-rate eligibility:
- field: `eligibility_text`
- source id: `TD-SAV-004`
- anchor: `Section boosted-rate-eligibility`
- excerpt:
  `Earn the Boosted rate ... Here's how to qualify ... Complete at least 2 out of the 3 Qualifying Monthly Transactions`

Sample C. `TD ePremium Savings Account` interest calculation:
- field: `interest_calculation_method`
- source id: `TD-SAV-003`
- anchor: `Section plan-highlights`
- excerpt:
  `Earn interest calculated daily, when your account balance is $10,000 or more`

## 8. Viewer Equivalent

Live viewer export artifacts:
- [viewer-payload.json](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/app/prototype/viewer-payload.json)
- [viewer-payload.js](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/app/prototype/viewer-payload.js)
- [index.html](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/app/prototype/index.html)

For prototype acceptance, the static viewer with live payload is used as the `viewer screenshot or equivalent` artifact.

## 9. Raw Run Artifacts

- [discovery-output.json](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/docs/01-planning/evidence/2026-04-11-first-successful-run/discovery-output.json)
- [snapshot-output.json](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/docs/01-planning/evidence/2026-04-11-first-successful-run/snapshot-output.json)
- [parse-output.json](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/docs/01-planning/evidence/2026-04-11-first-successful-run/parse-output.json)
- [extraction-output.json](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/docs/01-planning/evidence/2026-04-11-first-successful-run/extraction-output.json)
- [normalization-output.json](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/docs/01-planning/evidence/2026-04-11-first-successful-run/normalization-output.json)
- [validation-output.json](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/docs/01-planning/evidence/2026-04-11-first-successful-run/validation-output.json)
- [viewer-export-output.json](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/docs/01-planning/evidence/2026-04-11-first-successful-run/viewer-export-output.json)

## 10. Next Step

Use this evidence pack as the factual base for `WBS 3.10 prototype findings memo`, with special attention to:
- `required_field_missing` across all three target candidates
- current heuristic extraction noise around rates and eligibility text
- `TD Growth` special-case rule quality
- rerun hardening as a `P1` follow-up rather than a blocker for this first successful run
