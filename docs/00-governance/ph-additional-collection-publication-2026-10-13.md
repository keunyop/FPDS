# Additional Philippines collection and publication - 2026-10-13

Five additional products from LANDBANK, Chinabank and Security Bank passed the
ordinary automatic pipeline and are publicly available. Philippines now has 12 products at five banks:
EastWest Bank (6), Metrobank (1), LANDBANK (3), Chinabank (1), Security Bank (1).
This extends the [initial diagnosis and seven publications](ph-generic-collection-corrections-2026-10-13.md).
Dates use the owner's Vancouver day; current captures are dated October 14 UTC.

## Current official products published

| Bank / product | Verified native financial conditions | Official source |
| --- | --- | --- |
| LANDBANK Regular Passbook Savings Account | PHP; 0.05% per annum requires daily balance PHP10,000; initial/maintaining balance PHP10,000; below-ADB charge PHP200 monthly after two consecutive month-ends, starting at the end of the second month | [Current detail](https://www.landbank.com/personal-regular-passbook-savings-account) |
| LANDBANK Savings Account with ATM | PHP; 0.05% per annum requires daily balance PHP2,000; initial/maintaining balance PHP500; below-ADB charge PHP200 with the same explicit monthly trigger/timing | [Current detail](https://www.landbank.com/personal-savings-account-with-atm) |
| LANDBANK US Dollar Savings Account | Explicit USD; 0.025% per annum requires daily balance USD500; initial/maintaining balance USD100; below-ADB charge USD5 with the same explicit monthly trigger/timing | [Current detail](https://www.landbank.com/personal-us-dollar-savings-account) |
| Chinabank HomePlus | Explicit PHP; 7.50% p.a. for 1-3-year fixing and 8.00% p.a. for 4-5-year fixing; booking rates/repricing remain binding; purpose-dependent repayment maxima 10/15/20 years, subject to management approval | [Detail](https://www.chinabank.ph/loans-homeplus), [application FAQ](https://www.chinabank.ph/loans-faqs-homeplus-application) |
| Security Bank Easy Savings Account | Explicit PHP; 0.05% p.a. with interest-earning balance PHP100,000; opening PHP0 and maintaining PHP3,000; minimum-balance charge PHP300 per month only after falling below the minimum for two consecutive months | [Detail](https://www.securitybank.com/personal/accounts/savings-checking/easy-savings/), [linked fees](https://www.securitybank.com/personal/accounts/fees-charges/) |

None of the deposit rates is presented as an unconditional all-balance comparison
rate. Public retains the complete native earning-balance declaration and displays
`conditional`, with no scalar comparable/display rate. The native annual number
remains a verified typed fact. HomePlus preserves fixing periods and repayment
periods separately; neither a scalar mortgage rate nor invented days were supplied.

## Additional research scope and exclusions

The bounded follow-up examined 35 explicit official targets across the other eight
banks: UNIONBANK4, LANDBANK8, CHINABANK6, DBP2, RCBC7, BPI2, SECURITYBANK2, PNB4.
One additional already-captured current Easy Savings detail was reused, bringing
this follow-up to 36 distinct selected source URLs. There were 31 successful direct
captures of the 35-target manifest, four direct errors, and nine separately
retained rendered captures, including a verified soft 404. DBP's existing browser
fallback also failed on its two scoped pages. Existing validated fetch/render
budgets and TLS/SSRF controls were retained. Identical current inputs were reused;
there were no paid/model-provider calls or Admin collection API requests.
This is a selected current-source audit, not a claim that each bank has no other
publishable product. Missing acquisition is distinguished from missing proof.

| Bank / selected targets | Result and reason for remaining exclusions |
| --- | --- |
| LANDBANK | New current paths are behind a rendered Inertia application/menu; the old selected path is 404. Three products pass. PISO remains excluded: `Waived` below-ADB charge without proven monthly-cost semantics cannot become zero. |
| Chinabank | HomePlus detail has a corroborated H3 rather than H1. The linked FAQ index leads to its named application FAQ, which proves current annual rates and purpose-dependent terms. One product passes. |
| UnionBank | The current main page's literal application link supplies annual loan bounds and terms after safe browser retrieval. Actual principal denomination remains ambiguous bare P; PHP income/illustrative repayments cannot supply product currency. No TLS bypass or example-derived unconditional rate. |
| BPI | Selected card disclosures supply monthly rates. Selected mortgage rates lack proven annual price basis; fixing periods do not establish it. Checking transaction-cost proof remains incomplete. |
| RCBC | Current corporate/card domains and actual fee/rate notices were followed. Cards remain monthly-only; selected loan pages do not prove actual annual prices. Passbook annual rate is proved, but below-ADB fee cadence is not proved by the bounded evidence. |
| Security Bank | Easy Savings passes with its own explicit annual rate, earning/maintaining balances and exact linked peso-savings monthly-cost column. The earlier high-balance-tier exclusion was resolved by checking the complete already-captured detail, using the same conditional-rate standard as LANDBANK. Its interest rate is not assumed below the threshold. Selected card rates remain monthly-only; other savings records lack a complete accepted ownership/rate/cost combination in this bounded audit. |
| PNB | Old card URL is a soft 404. Followed the current `/card/` resources to the actual June 2026 fee PDF; purchase finance-charge annual meaning remains insufficient. |
| DBP | Two selected current pages failed transport/browser acquisition. This is an acquisition limit, not proof of nondisclosure or bank-wide ineligibility. |

## Why the shared collection path missed the verified products

1. Successful HTTP responses could be empty official SPA roots. The existing
   rendered fallback detected rate placeholders but missed this application shell.
2. A full desktop H1 and its explicitly complementary, truncated mobile H1 were
   treated as two unrelated product identities. A current lending page with a
   literal H3, matching SEO title, issuer host and exact leaf route was missed.
3. Informational FAQs were filtered as general support. Spending both existing
   research URL slots on first-wave companions left no slot for the product FAQ
   linked by a FAQ index, although it contained required rate/repayment facts.
4. Separate native account feature blocks lost their joint earning-balance and
   monthly-fee trigger context. Long, purpose-dependent repayment terms were
   incorrectly discarded by a generic 240-character broad-copy heuristic.
   A compact account definition and table lacked a primary heading; a shared cost
   needed exact named-row/currency/category/return-link binding. Unrelated rate/card
   benefit footnotes could also trigger a false mask when mixed into cost conditions.
5. Final Public readback exposed a comparison defect: the native phrase
   `Required Daily Balance To Earn Interest` remained in detail but did not trigger
   the existing minimum-balance classifier. The correction preserves the whole
   source declaration and repeats only its exact printed amount/currency under
   `Minimum balance to earn interest (daily)`. Exact deterministic validation
   prevents arbitrary paraphrases or changes to the threshold.

## Generic corrections and regression boundaries

Parser v31/process `2026-10-13-linked-account-cost-conditions-v23`, market profile v8:

- Empty official SPA fallback reuses safe rendering and existing budgets; populated
  pages, ordinary blank HTML and untrusted hosts do not receive this extension.
- Responsive aliases require a literal full heading, a substantial matching prefix,
  a shared hero ancestor and complementary CSS at the same breakpoint. Ambiguous
  product families and unproved truncations stay excluded.
- Primary lending identity requires independent visible heading, SEO, issuer and
  exact route corroboration. Supporting FAQ facts require named product ownership,
  a literal return link to the selected detail and current independent origins.
- Missing-essential research admits informational FAQs and reserves the second
  existing URL slot for their named child. The actual two-wave regression proves
  the same two-URL cap, acquisition of required facts and immediate stop when
  essentials pass. Authentication/servicing links remain excluded.
- A single native account definition plus its own compact four-row table, SEO and
  exact route can prove identity without H1. Opening, maintaining and earning
  balances remain distinct. Linked category costs require a current matching
  named account row, explicit currency, exact cost column and literal detail link.
  Only the applicability column is used; unrelated rate/card-benefit footnotes
  cannot donate facts or become false cost masks. Complete shared cost conditions
  survive the broad-copy guard under exact current source verification.
- Native account feature records and complete named lending FAQ records stay atomic
  through the ordinary 900-character chunk builder, extraction and final gates.
  Purpose-bound terms, annual rate basis, repricing, fees, currency and full timing
  are preserved. Cross-issuer mutations use the same rules; no bank-code exception
  or weaker required-field profile was added.

Immutable fixtures contain nine actual official HTML captures and original
SHA-256 receipts. Regressions cover success, other issuers, foreign-country origins,
wrong sibling ownership, ambiguous responsive headings, missing cadence/earning
threshold, monthly instead of annual rates, missing repricing, wrong return link,
shortened conditions, guessed zero, scalar donation and two-wave acquisition.

## Actual publication and independent verification

Five initial candidates yielded four automatic passes and one exclusion. A final
comparison correction reused the same current three LANDBANK inputs and produced
three ordinary approved replacement versions. The additional Easy Savings
candidate passed independently. Totals: nine candidates, eight approved version
events, five distinct newly published products, one exclusion,
zero manual reviews. Replacement history is retained; no extra product duplicates.
Promotion rollback rehearsals and actual stored-origin checks passed before writes.
Eight unique current raw/parsed storage pairs were read back; the correction's three
reused pairs were read back again. Final current versions have 42 independently
verified field-origin links and five valid acceptance receipts.

Final anonymous external APIs return CA120/US85/PH12; all five external web details
return HTTP200 with complete financial conditions after normal cache revalidation.
External catalogs list all 12: deposits4, loans2, cards6.
Original seven PH products and unrelated facts/rows remain unchanged, including
46 original PH Runs, 162 candidates and all 1,615 original version financial facts.
Local v23 details match external facts; ten wrong-country requests return 404.
No private field evidence or operational metadata is exposed.

Actual checks: API671, Discovery86, final account-cost4 and earlier focused33
pass. Final broad Worker971 has the same four prior failures (two existing fixture-hash failures and two existing named-annual-record
expectations). Exact earlier HEAD reproduction ran25 with those same four failures;
these fixtures/assertions were preserved. The broad suite is not reported green.
Foundation, Python syntax, UTF-8/JSON, all nine immutable hashes, new references
and `git diff --check` pass. Full repository doctor additionally reports a broken
link in an unrelated ignored temporary Admin copy; new tracked references pass.

The repository-connected localhost:4000 runs process v23/market v8. Final external
health reports process v20/market v8: this follow-up's runtime code has not been
deployed externally. Published data is verified on the actual external service and
its comparison conditions are compatible with that serving runtime. Future hosted
collection needs the normal coordinated API/Worker release; no Vercel deployment
was performed or claimed. Private operational receipts remain ignored under
`tmp/ph-extra-20261013`, `tmp/ph-extra-qualifier-20261013` and
`tmp/ph-extra-security-20261013`.
