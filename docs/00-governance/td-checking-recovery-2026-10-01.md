# TD checking fee rows and additional publication — 2026-10-01

## Outcome

Two previously hidden TD accounts passed fresh normalization, automatic validation and promotion. Public API now shows CA 11 / US 2 (13 total). Both website detail pages visibly show the ordinary monthly allowance and $1.25 excess cost. All 11 actual API/BFF/list/detail and existing card URL checks passed after normal cache revalidation; all previously public products are preserved.

| Product | Monthly fee (CAD) | Ordinary transactions/month | Excess transaction (CAD) |
|---|---:|---:|---:|
| TD Every Day Chequing Account | 11.95 | 25 | 1.25 |
| TD Minimum Chequing Account | 3.95 | 12 | 1.25 |

These records were already canonical-active but failed the current Public gate. They received new approved versions with current official evidence. Canonical totals remain 428: 26 active / 402 inactive. Active hidden records fall from 15 to 13; 415 records remain unpublished. No products were deleted. The original 355-product manifest remains 26 active / 323 inactive / 6 deleted.

## Shared correction

The previous checker failed ordinary allowance rows whose footnote-bearing label and value occupy separate lines. Its broad unlimited pattern also accepted unlimited public transit transactions as an account-wide benefit. Regression fixtures reproduced both failures before implementation.

The shared accuracy gate now recognizes exact ordinary count and excess-fee rows with preserved line boundaries and full captured context. Footnote markers cannot supply counts. Ambiguous, conditional, duplicate or conflicting rows fail closed; special-channel fees cannot replace ordinary account pricing. Transit/ATM/wire/e-transfer-only unlimited benefits cannot establish ordinary unlimited transactions. Excess charges remain `additional_transaction_fee`; no false unlimited flag or invented zero is stored.

The common extraction instructions explain the same distinctions. Known checking products use deterministic normalization, and normalization/validation share the corrected accuracy gate. Existing identity, currency, consulted official URL, exact quote, current evidence, native types and comparison prerequisites remain. Receipt/profile versions remain `collection-accuracy-2026-10-01-cost-access` / `2026-10-01-v7`: the financial contract and receipt compatibility are unchanged. Existing cache fingerprints include changed instructions/code. No schema, Admin/Public UI or permanent recovery feature was added.

## Bounded data execution

Two official product pages were checked in preflight and rechecked through normal capture/parse during execution. Complete fee-table contexts matched; product identity and CA/CAD default conditions passed. Proven optional minimum balance was retained for Every Day. No optional-only searches or repeated unchanged paid extraction occurred.

Run `run_20261001_220820_td_chequing_collect_TQT3C4R7` completed with two approved candidates, two new versions and a completed CA aggregate refresh. Before-images and current input objects were retained privately. Existing original extraction provenance was resolved through preserved execution lineage; no provider request was fabricated. Collection-model calls and provider tokens: zero. Conversation token use was not measured.

Independent DB readback and full captured-evidence replay passed. Other 426 canonical rows, 26 historical target candidates, previous target versions and the source registry are unchanged. No new review tasks or running collection remain. No manual approval or raw evidence entered Public responses.

## Verification and deployment

- Focused accuracy/cost/row tests: 33 passed, including real full fee tables, footnotes, LF/CRLF, channel qualifiers, conditional/range/conflicting counts/costs and receipt acceptance/exclusion.
- Worker: 601 tests passed. API: 539 tests passed. Repository doctor passed.
- All 11 actual API/BFF/list/detail and existing card checks passed. Exact fee/count/excess values and all previously public products were preserved; private evidence was absent. Website detail text independently showed 25/12 included per month and $1.25 per extra transaction.
- Final diff/goal checks passed; older goal ownership and previous work are preserved.

The corrected local worker performed this authorized data operation against the verified compatible serving policy. Future Admin collection requires collection-runtime/API deployment. No deployment was performed: the direct Vercel command is unavailable and `npx.cmd --no-install vercel whoami` reports the CLI package missing. No external authentication or environment change was made.

Private artifacts: `tmp/td-fee-recovery-*`, `tmp/td-fee-*-tests.log`, `tmp/td-fee-focused.log`, `tmp/td-fee-doctor.log`. Completed execution must not be rerun. Raw captures, rollback images and evidence remain private.

Next separate slice: investigate the previously reproduced purchase-rate context false exclusion using preserved official evidence and adversarial fixtures before changing accepted patterns.
