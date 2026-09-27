# Initial official bank link checks

Date: 2026-09-26 (America/Vancouver); timestamps below are UTC.

## Outcome

Read-only sample: 16 approved Public product records (8 CA, 8 US). Twelve returned
HTML with a product-name hint in title/H1; four BMO destinations could not be
confirmed over this network. Three US URLs added a trailing slash through HTTP
301. No different-product redirect was established by this sample.

This is a bounded sample, not a complete 216-product URL audit or renewed
financial verification. The CA sample includes separate records that share an
official URL. No canonical data, verification date, collection or deployment
was changed. The tool reports suspected identity changes for human review.

## Operator follow-up

- Recheck the four inconclusive BMO destinations in a normal browser. A timeout
  does not prove a product or URL was withdrawn.
- If a destination is a different product, preserve its original/final URL and
  inspect source/review context before correcting and publishing.
- Run the [manual report](../03-design/public-bank-handoff-policy.md) for affected
  public IDs after bank changes or error reports. No recurring collector is added.

## Results

| Country | Product | Result | HTTP | Original / final URL |
|---|---|---|---|---|
| CA | Alterna Bank - High Interest eSavings | Identity observed | 200 | https://www.alternabank.ca/en/personal/accounts/high-interest-esavings |
| CA | Alterna Bank - No Fee eChequing | Identity observed | 200 | https://www.alternabank.ca/en/personal/accounts/no-fee-echequing |
| CA | Alterna Bank - eTerm Deposits | Identity observed | 200 | https://www.alternabank.ca/en/personal/investing/eterm-deposits |
| CA | High Interest eSavings | Identity observed | 200 | https://www.alternabank.ca/en/personal/accounts/high-interest-esavings |
| CA | eTerm Deposits | Identity observed | 200 | https://www.alternabank.ca/en/personal/investing/eterm-deposits |
| CA | B2B Bank High Interest Savings Account | Identity observed | 200 | https://b2bbank.com/en/saving/high-interest-savings-account |
| CA | BMO Prepaid Mastercard ®* | Unconfirmed (TimeoutError) | — | https://www.bmo.com/en-ca/main/personal/credit-cards/prepaid-credit-cards |
| CA | Blue Rewards Chequing Account | Unconfirmed (TimeoutError) | — | https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/air-miles |
| US | Ally Bank Savings Account | Identity observed | 200 | https://www.ally.com/bank/online-savings-account |
| US | Ally Bank Spending Account | Identity observed | 200 | https://www.ally.com/bank/interest-checking-account |
| US | BMO Cash Back Credit Card | Unconfirmed (TimeoutError) | — | https://www.bmo.com/en-us/main/personal/credit-cards/bmo-cash-back-credit-card |
| US | BMO Premium Rewards Credit Card | Unconfirmed (TimeoutError) | — | https://www.bmo.com/en-us/main/personal/credit-cards/bmo-premium-rewards-credit-card |
| US | Bank of America® Travel Rewards Credit Card | Identity observed | 200 | https://www.bankofamerica.com/credit-cards/products/travel-rewards-credit-card → https://www.bankofamerica.com/credit-cards/products/travel-rewards-credit-card/ |
| US | Bank of America® Travel Rewards Credit Card for Students | Identity observed | 200 | https://www.bankofamerica.com/credit-cards/products/student-rewards-credit-card → https://www.bankofamerica.com/credit-cards/products/student-rewards-credit-card/ |
| US | MONEY Teen Checking Account with Debit Card | Identity observed | 200 | https://www.capitalone.com/bank/checking-accounts/teen-checking-account → https://www.capitalone.com/bank/checking-accounts/teen-checking-account/ |
| US | Citi Double Cash ® Card | Identity observed | 200 | https://www.citi.com/credit-cards/citi-double-cash-credit-card |

## Run metadata

- CA: 2026-09-27T00:41:39.251212+00:00 · snapshot agg_top5_99d472e42bcd46d89d8a42f15eac21e1
- US: 2026-09-27T00:47:28.165496+00:00 · snapshot agg_top5_f2f631407d044c2d933af435562fa3b1

The machine-readable JSON and detailed Markdown reports are generated locally
under tmp/handoff-qa/official-links-CA and official-links-US. They contain
per-product check times and exact redirect hops. The same reports can be
regenerated using the documented operator commands.
