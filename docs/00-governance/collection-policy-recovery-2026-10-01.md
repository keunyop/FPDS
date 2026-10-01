# Approved currency/default policy and recovery readiness

Status: code implemented; operating API deployment is required before publication.

## Implemented

- Undisclosed currency uses registered CA/CAD or US/USD, with private provenance. Explicit/foreign/conflicting disclosures do not become defaults.
- Reduced market-profile prerequisites and comparison prompts are aligned. Former optional requirements remain collectable without vetoing publication.
- Removed the duplicate GIC opening-deposit prerequisite in fresh normalization; missing core rate/term still fails. No historical validation-error records were edited.
- Existing strict-policy receipts remain compatible. Missing currency no longer aborts grounding. Health metadata exposes the running policy versions.

## Verification

- Worker: 578 tests passed. API: 536 tests passed. Maintenance: 8 tests passed.
- Actual 7 active product receipts remain compatible. No runtime data writes or collection-model calls in this turn.
- Read-only diagnosis covered 350 surviving original records: 7 active and 343 excluded. The 5 deleted non-products were not reconsidered.
- Combined saved evidence and current diagnosis produced 25 source candidates. All 25 current detail captures succeeded; exact identity and full evidence contexts yielded 18 proposals.
- Fresh NormalizationService and ValidationRoutingService accepted 17; one still lacks a retained monthly-fee fact after normalization. No review task was created.
- A prior attempt to remove stale error flags in a reconstructed candidate was blocked by automatic approval review. The completed safer path creates fresh candidates through normal normalization and recalculates validation from current evidence.

## Ready products

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

These 17 comprise CA 10 / US 7. If all still pass the fresh execution checks, Public becomes CA 17 / US 7 (24 total), leaving 326 of the original manifest inactive. These are projected counts, not the current catalogue.

## Remaining dependency and resume

Vercel CLI authentication is unavailable in this environment (no login/auth file/token). The live API health check still returns only status, so serving the new receipt version is not confirmed. The user has been asked to deploy `switchabank-api` through their existing process. No candidate has been promoted before that dependency.

After deployment, `/healthz` must report `collection_accuracy_version=collection-accuracy-2026-10-01` and `market_profile_version=2026-10-01-v6`. The prepared private `tmp/policy-recovery-operation.py --execute` refuses all live writes until this matches. It then checks inactive version baselines, captures current official detail sources again, creates fresh candidates, runs normal automatic validation/promotion, and refreshes aggregates. Check survivors, original versions, active receipts, run completion and actual Public counts afterward. Do not rerun if `tmp/policy-recovery-plan.json` already exists; inspect partial progress instead.

Private artifacts: `tmp/policy-live-diagnosis.json`, `tmp/policy-recovery-preflight.json`, `tmp/policy-recovery-assessment.json`, `tmp/policy-recovery-selected.json`, `tmp/policy-recovery-dryrun-v2.json`, and the operation script. These contain evidence/internal payloads and are not Public assets.
