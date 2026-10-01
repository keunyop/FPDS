# Currency defaults and reduced publication prerequisites - approved

Status: Explicitly approved by the Product Owner; code implemented, tested and deployed. Final automatic recovery published 17 products; actual Public readback confirms 24 total. See [completed recovery](collection-policy-recovery-2026-10-01.md).

## Requested policy

The Product Owner explicitly requested country currency when the product does not state a currency, and removal of less important or rarely captured publication prerequisites. This supersedes the earlier no-country-default direction following explicit approval. The subsequent explicit instruction also authorizes publication of excluded products that pass the new policy.

## Concrete required fields after the change

| Type | Publication prerequisites for CA and US |
|---|---|
| Chequing/checking | Monthly fee |
| Savings | Ongoing annual rate/APY and monthly fee |
| GIC/CD | Rate/APY or supported term schedule, and exact term |
| Credit card | Annual fee and purchase rate; US qualified APR/range remains supported |
| Mortgage | Rate (US qualified summary), fixed/variable type and term |
| Personal loan | Rate or supported range and term |
| Line of credit | Rate or supported range |

All types still need country, bank, actual detail-product identity and resolved currency. Minimum balances/deposits, transaction allowances/fees, fee-waiver conditions, redeemability, early withdrawal penalties, loan amount/limit and security requirements become optional, with no guessed values. Evidence attached to a retained rate or fee must still preserve its applicable conditions; making separate waiver fields optional never turns a conditional promotional rate/fee into an unconditional value.

## Currency handling

- No explicit currency: use CA -> CAD, US -> USD, derived from the registered collection country. Record `country_default` provenance privately; never fabricate an official currency quote.
- Explicit currency: preserve it and its applicable official evidence. Ambiguous/multiple currencies or unresolved foreign-currency descriptions do not permit a default.
- Unknown countries: no guessed currency. Locale, IP and website language do not determine the country.
- Current currency-only grounding preflight must be removed so missing currency text does not stop verification of otherwise useful product facts.
- Existing stricter accepted receipts should remain valid through the deployment; previously excluded products must undergo validation again, not mass activation.

## Runtime boundaries and checks

Local worker/shared API code only: market profiles, shared accuracy validator, grounding cache/preflight and comparison prompts. No new UI or schema migration. Verify deployment before approved live recovery. Keep native types, exact sources, annual-rate basis, product applicability, anti-promotion/tier/rate-conflict safeguards and no-human-review workflow.

Before implementation completes, test CA/US defaults; explicit foreign currencies and conflicts; unsupported country; missing noncurrency evidence; optional-field omission; essential-field failures; preserved optional collection; negative financial cases; receipt compatibility and tampering; grounding reuse; normalization/validation and Public projection compatibility. Worker 578, API 536 and maintenance 8 tests passed; final checks are recorded in the development journal.

## Evidence and approval block

Cached diagnosis of the 350 surviving original records (including the 7 active records, not a new live revalidation) shows missing old-contract fields: savings minimum balance 41/49, GIC minimum deposit 32/35, personal-loan amount 13/19, line-of-credit limit 6/8 and security requirements 7/8. These measurements support optionality; core rate/fee prerequisites remain even when frequently missing. Private summary: `tmp/lean-requirements-coverage.json`.

Automatic approval review rejected the attempted local multi-file edit because it regarded receipt/default/profile/prompt changes as a broad publication-gate change whose exact scope and financial-data risk were not sufficiently authorized. No attempted runtime edits ran. That earlier block was resolved by the subsequent explicit approval of code changes and eligible product publication.

The Product Owner subsequently approved the exact change and eligible product publication. The prior approval block is resolved. The fresh-normalization dry run accepted 17 of 18 candidate products from a 25-page current-source check; full live diagnosis covered the 343 exclusions. No legacy error flag is removed to force acceptance.
