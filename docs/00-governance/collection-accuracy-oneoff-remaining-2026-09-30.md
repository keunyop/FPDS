# Remaining unchecked recovery batch - 2026-09-30

Status: Completed; data applied and ordinary Public API/BFF/card list/detail verified.
Local operation date: September 30 (America/Vancouver). Capture and promotion
receipts use October 1 UTC.

## Outcome

Assessed the remaining **182 previously unchecked manifest products across 20
banks**: CA 94 / US 88. These products reference 161 distinct official source URLs;
157 fetched and parsed successfully, covering 178 products. Four stopped at the
existing allowlist boundary and were classified using current registry state:
two inactive sources and two category entry pages. They were not reactivated.

- **Scotiabank Value Visa** restored automatically. Public API is now CA **7** /
  US **0**; **348** original-manifest products remain inactive.
- 177 other products retain evidence exclusions, with four source exclusions.
- All **355 original manifest products** now have an active accepted result or
  a source preflight disposition. The unchecked-source queue is **empty**.
  This is first-pass coverage, not full restoration of the 348 excluded products.
- New collection model/provider calls and input/output tokens: **0**. No human
  reviews, permanent features, runtime changes or deployment were added.
  These usage figures exclude the coding-assistant conversation and infrastructure.

| Product type | Products assessed |
|---|---:|
| Credit card | 73 |
| GIC/CD | 30 |
| Mortgage | 28 |
| Savings | 20 |
| Chequing | 14 |
| Personal loan | 13 |
| Line of credit | 4 |

## Restored card and applicability checks

`prod_lxTgK43_S1NJGbvh` advanced from version 2 to **3**. Current official Value
Visa wording proves the unchanged native **CAD 29 annual fee** for the primary
card and **13.99% annual purchase rate**. These are the disclosed ongoing fee and
preferred purchase rate, not the first-year fee waiver or introductory balance
transfer offer. Undefined subtype text and unproven optional facts were omitted.

The detail's exact product H1 is checked. Its linked credit-agreement landing
page names this card in the **Personal Credit Card Accounts** panel and links
back to the exact registered Value Visa URL. The current linked agreement
explicitly bills other Visa cards in CAD, with a separately named U.S. Dollar
Visa exception. The operation checks that exception is a distinct card, and pins
the actual agreement PDF hash and clause. The full native parser context remains
attached, including the exception; it was not shortened to conceal other currencies.
The official general card-fees page was also inspected but not used as currency
proof or published as evidence.

The exact-product success check and a wrong-product-URL rejection check both
passed before execution. Standard capture, parse, normalization, validation,
automatic promotion and aggregate refresh completed. Three source documents
entered the normal pipeline: detail, agreement landing page and agreement PDF.
No persistent source-registry entry was changed or added.

- Run: `run_20261001_020505_scotia_credit-card_collect_qSEUUcrO`
- Candidate: `cand-41c5a2ff1fcb8e77`
- Product version: `pver__9b4-t4H4Wq9Cxx_`
- CA aggregate: `agg_axeYiQaCJ-1VoNt3`, refreshed 02:07:16 UTC

## Exclusions and further recovery

All 607 matching historical candidates were checked for unchanged full-context
reuse; none passed by reuse alone. Among the 177 financial exclusions, the best
reuse result lacks verified applicable currency and essential comparison fields;
125 also lack verified product identity. These counts overlap and describe the
retained evidence path, not whether a bank has any accurate facts available.
A separate local readiness scan checked current native values as an upper bound;
its output was explicitly diagnostic and never used as permission to publish.

Concrete findings:

- CIBC USD Non-Redeemable GIC now shows a 4.00% one-year rate while stored
  candidates contain 3.90%. The old rate/table was not restored, and years were
  not converted into invented fixed day counts.
- CIBC Smart Start's own fee detail and linked Personal Account Service Fees
  booklet confirm age-limited rebates and account tiers. Foreign-worker banking
  advertises a two-year fee benefit. Their old zero fees and historical eligibility
  wording were not published as unconditional current facts. The broader service
  fee currency clauses were not borrowed as exact account-currency proof.
- Vancity Pay As You Go has channel-specific transaction prices and free online
  transactions; that does not establish a single transaction fee or an invented
  zero included-transaction count. It remains excluded.
- Several legacy entries are general category, calculator, agreement or online
  banking page titles, rather than verified individual product identities.
- The four un-fetched sources were `AUTO-CIBC-GIC-f9dc8edaef` and
  `AUTO-BOAN-CHE-9d6b032dda` (active entry pages), plus
  `AUTO-CIBC-GIC-ecbbc96c59` and `AUTO-BOAN-MOR-8e53311503` (inactive sources).
  They lack captured official allowlists. Current registry status/role was
  inspected before considering resolution; no boundary or inactive status was
  bypassed and no repeat fetch was made.

Five unique support URLs were inspected: three Scotiabank card/credit-agreement
sources and two CIBC Smart Start fee sources. Only the fully eligible card entered
persistent processing. The remaining 348 exclusions should next be grouped by
new applicable official evidence and demonstrable parsing gaps. Repeating the
same model calls on the same incomplete sources does not establish accuracy.
The empty unchecked queue must not be treated as an empty exclusion backlog.

## Verification and private artifacts

- Exactly one canonical product changed; **433 other canonical rows**, all
  **607 historical candidates**, and all registry rows are unchanged.
- The restored product's previous version retains its exact before-image payload.
  All **seven active products** pass actual approved-candidate/evidence replay
  and receipt validation.
- One new approved candidate, two local execution stage records, **zero new or
  pending human reviews**, and no running ingestion jobs.
- Native fee/rate numbers verified. Accuracy/maintenance regression suite:
  **31 tests passed**. Exact agreement applicability success/failure checks pass.
- Ordinary Public API and BFF both show CA 7 / US 0. The restored card is present
  on `/cards?country_code=CA` and its detail route, with native fee/rate numbers
  and no private receipts/quotes. The deposit-only `/products` catalog correctly
  retains six accounts. Initial cached responses revalidated normally; no cache
  setting or deployment changed. The first list check used the deposit route;
  the final check uses the correct card catalog.
- `git diff --check`, UTF-8 validation and 98 relative Markdown links pass.
  No runtime build was needed for this data/documentation operation.

Private evidence remains under ignored `tmp/oneoff-broad2-*`, including selection,
before-image, inventory, 607 original candidates, source captures/chunks,
preflight, full-context assessment, diagnostic readiness, outcomes, coverage,
DB and Public readbacks. `tmp/oneoff-scotiavalue-*` preserves the exact execution
plan, current capture hashes, validation and promotion receipts.
`tmp/oneoff-cibcstart-*` contains read-only supporting evidence. Do not rerun an
execute script; use its plan/result and current state for any recovery.

## Follow-up: shared evidence strengthening

A bounded read-only pass assessed 15 excluded Scotiabank cards. Nine now have exact applicable CAD agreement evidence in private recovery artifacts; 12 have exact official rate-table rows, with 11 historical purchase rates matching. The official table was the only new fetch. No collection model was called; coding-assistant tokens are separate and were not measured.

No additional product passed the unchanged automatic evidence gates, so Public remains at 7 active products (6 accounts and 1 card); 348 manifest products remain inactive. The shared agreement does not automatically establish applicability to student variants or Mastercard products. Preserve full rate context and annual basis before promoting any remaining card. Evidence report: private `tmp/oneoff-strength-report.json`; 434 canonical rows unchanged and 31 focused tests passed.

For subsequent passes, reuse this report and cached support, fetch only genuinely missing product disclosures, and keep tool output compact. Do not repeat the full first-pass scan or claim collection-model token counts represent all development token use.

### Product-specific disclosure follow-up

Two further official documents were checked: the [Platinum welcome kit](https://www.scotiabank.com/ca/en/personal/credit-cards/american-express/platinum-card/welcome-kit.html) and [2022 rate amendment](https://www.scotiabank.com/content/dam/scotiabank/canada/credit-cards/en/NOC_AmexPlatinum_April2022_En.pdf). Neither supplies independently current, complete evidence that passes the unchanged gate. No product was restored; active 7 and original-manifest inactive 348 remain.

The [current detail](https://www.scotiabank.com/ca/en/personal/credit-cards/american-express/platinum-card.html) does explicitly state the preferred annual purchase rate. A reproducible false exclusion occurs because unrelated promotional eligibility wording shares the retained evidence chunk and triggers the blanket conditional-word rule. This is a field/context attribution limitation, not absence of an accurate official rate. Further equivalent fetches will not resolve it. Preserve full evidence and repair the existing automatic validator with adversarial regression tests before retrying this cohort; no manual review or permanent recovery feature is needed. Private report: `tmp/oneoff-disclosure-report.json`. No model calls or data writes; 31 focused tests passed.
