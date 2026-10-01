# Approved currency/default policy and completed recovery

Status: completed. Product Owner deployed; serving policy versions verified; 17 products automatically published and actual Public results checked on 2026-10-01.

## Implemented

- Undisclosed currency uses registered CA/CAD or US/USD, with private provenance. Explicit/foreign/conflicting disclosures do not become defaults.
- Reduced market-profile prerequisites and comparison prompts are aligned. Former optional requirements remain collectable without vetoing publication.
- Removed the duplicate GIC opening-deposit prerequisite in fresh normalization; missing core rate/term still fails. No historical validation-error records were edited.
- Existing strict-policy receipts remain compatible. Missing currency no longer aborts grounding. Health metadata exposes the running policy versions.

## Pre-deployment verification

- Worker: 578 tests passed. API: 536 tests passed. Maintenance: 8 tests passed.
- Actual 7 active product receipts remain compatible. No runtime data writes or collection-model calls occurred during that preparation step.
- Read-only diagnosis covered 350 surviving original records: 7 active and 343 excluded. The 5 deleted non-products were not reconsidered.
- Combined saved evidence and current diagnosis produced 25 source candidates. All 25 current detail captures succeeded; exact identity and full evidence contexts yielded 18 proposals.
- Fresh NormalizationService and ValidationRoutingService accepted 17; one still lacks a retained monthly-fee fact after normalization. No review task was created.
- A prior attempt to remove stale error flags in a reconstructed candidate was blocked by automatic approval review. The completed safer path creates fresh candidates through normal normalization and recalculates validation from current evidence.

## Published products

| Product | Currency |
|---|---|
| Essential Plus Chequing | CAD |
| USD Chequing Plus for seniors | USD |
| TD Every Day Chequing Account | CAD |
| Basic Bank Account | CAD |
| TD All-Inclusive Banking Plan | CAD |
| Vancity Total Chequing | CAD |
| TD Minimum Chequing Account | CAD |
| TD Student Chequing Account | CAD |
| Chequing Plus for youth | CAD |
| Personal Checking Plus | USD |
| Prime Checking | USD |
| Chase High School Checking℠ | USD |
| Preferred Platinum Checking | USD |
| Personal Interest Checking | USD |
| Personal Savings Account | USD |
| 1-Year Better-than-Cash GIC | CAD |
| Chase Premier Plus Checking℠ | USD |

All 17 passed fresh execution: CA 10 / US 7 restored. Public now has CA 17 / US 7 (24 total), leaving 326 of the original manifest inactive and 5 previously deleted.

## Completed publication and verification

- Live `/healthz` confirms `collection-accuracy-2026-10-01` and `2026-10-01-v6` after the Product Owner's deployment.
- The prepared one-off operation fetched official sources again and ran normal fresh normalization, automatic validation and promotion. All 17 candidates were approved across 9 completed runs. No human review tasks or collection-model calls were used.
- Both countries' aggregate refreshes completed. Actual API and Public BFF return CA 17 / US 7. Deposit lists show CA 16 / US 7; the existing Canadian card remains visible. All 17 new detail pages return the expected products. Initial stale list responses refreshed normally; final 24 URL checks pass, including private-field exclusion.
- Independent database readback and full captured-document evidence replay passed for all 24 active receipts. Exactly 17 canonical products advanced one version; all 412 unrelated products, the source registry, 150 historical candidates and each target's previous version payload remained unchanged. There are 429 canonical products in total (24 active / 405 inactive); within the original 355-product manifest, 24 are active, 326 inactive and 5 deleted.
- Previously completed regression coverage remains Worker 578 / API 536 / maintenance 8. This publication turn changed no runtime code; it ran the operation, independent database/evidence checks, actual Public checks and final diff verification.
- The remaining 326 original exclusions are outside this completed 17-product batch. They require adequate official evidence before any further publication.

Private operation evidence: `tmp/policy-recovery-before.json`, `tmp/policy-recovery-plan.json`, per-run captures/results, `tmp/policy-recovery-result.json`, `tmp/policy-recovery-db-readback.json` and `tmp/policy-recovery-public-readback.json`. These include internal evidence and must remain private. Do not rerun the completed execution script. The legacy database audit view does not persist writes; this operation's durable local artifacts and this journal record retain its verification trail.
