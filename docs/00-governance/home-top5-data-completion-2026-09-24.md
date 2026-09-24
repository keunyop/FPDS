# Home Top 5 bounded data completion — 2026-09-24

Status: existing-product corrections published; three US candidate approvals pending.
Scope: official-bank research for existing CA/US Deposit and Loan conditions.
No runtime release, comparison relaxation, full-catalog refresh or new types.

## Outcome and limits

A short list means fewer **published, eligible records**, not proof that fewer
qualifying products exist in the market. Missing annual/APY semantics, missing
conditions, pending review and incorrectly extracted rates all affected counts.
Counts below use the actual Home grouping functions on snapshot-pinned API rows.
A zero means there is no eligible group; the UI does not manufacture placeholders.

| Country / condition | Before | Published after |
|---|---:|---:|
| CA Savings / All | 1 | 5 |
| CA Savings / No monthly fee | 1 | 5 |
| CA Savings / No minimum balance | 1 | 5 |
| US Savings / All | 0 | 2 |
| US Savings / No monthly fee | 0 | 2 |
| US Savings / No minimum balance | 0 | 1 |
| CA Mortgage / All | 5 | 5 |
| CA Personal Loan / All | 2 | 2 |
| CA Line of Credit / All and Unsecured | 3 | 2 each |
| US Mortgage / All | 1 | 0 |
| US Personal Loan / All | 1 | 0 |
| US Line of Credit | 0 | 0 |
| CA/US eligible GIC groups | 0 | 0 |

Other secured/unsecured groups remain empty where flags or comparable rates are
missing. Unchanged CA mortgages and residual loans were not comprehensively
reverified. These counts do not certify their current pricing.

## Published bounded corrections

The [manifest](../../scripts/maintenance/top5_completion_20260924.json) records
exact products, optimistic version/payload guards, field changes, official URLs,
review dates and field-level facts. The companion
[maintenance script](../../scripts/maintenance/top5_completion_20260924.py)
rehearses with rollback by default; `--apply` commits one serializable transaction.

| Product | Official facts used / correction |
|---|---|
| [Alterna High Interest eSavings](https://www.alternabank.ca/en/personal/accounts/high-interest-esavings) | Preserve 1.05%; add annual calculation basis. |
| [National High Interest Savings](https://www.nbc.ca/personal/savings-investments/accounts/high-interest.html) | Preserve 0.55%; add annual calculation basis. |
| [RBC NOMI](https://www.rbcroyalbank.com/bank-accounts/nomi-find-and-save.html) | Preserve 0.15%; annual daily/monthly basis corroborated by [account rate disclosure](https://www.rbcroyalbank.com/rates/persacct.html). |
| [Tangerine Children's Savings](https://www.tangerine.ca/en/personal/save/childrens-savings-account) | Preserve 0.40%; annual basis and parent/child eligibility retained. |
| [First Citizens Online Savings](https://www.firstcitizens.com/personal/savings/online-savings-account) | Preserve 0.10%; explicitly identify APY. Opening deposit is distinct from ongoing minimum balance. |
| [Marcus Online Savings](https://www.marcus.com/us/en/savings/high-yield-savings) | 3.50% standard APY and no account fees. Separate optional referral promotion. Existing approved product now passes essential fields and enters the snapshot. No minimum deposit is not silently converted into no minimum balance. |
| [BofA refinance](https://www.bankofamerica.com/mortgage/refinance/) | Remove 0.375 discount represented as full rate; no guessed replacement. Projection inactive because a full rate is absent. |
| [Manulife Access LOC Plus](https://www.manulifebank.ca/personal-banking/loans/line-of-credit.html) | Secured by investments/life insurance, with limit-dependent rates; remove standalone 5.45 from ranking and retain qualified schedule. |
| [U.S. Bank Simple Loan](https://www.usbank.com/loans-credit-lines/personal-loans-and-lines-of-credit/simple-loan.html) | 35.65% is representative APR for a stated repayment example, not an unconditional account rate; preserve context and remove comparison scalar. |

Oaken's already eligible 2.80% Savings was checked against its
[official page](https://www.oaken.com/oaken-savings-account/) and left unchanged.
The duplicate Alterna savings record was not enriched to pad the count.

## Three prepared US candidates — not approved or published

[Review patches](../../scripts/maintenance/top5_review_candidates_20260924.json)
contain exact candidate hashes, rendered-source hashes, typed changes and expected
Public eligibility. Official rendered product pages confirmed:

- [Capital One 360 Performance Savings](https://www.capitalone.com/bank/savings-accounts/online-performance-savings-account/): 3.00% APY.
- [Amex High Yield Savings](https://www.americanexpress.com/en-us/banking/online-savings/high-yield-savings-account/): 3.10% APY.
- [Capital One Kids Savings](https://www.capitalone.com/bank/savings-accounts/kids-savings-account/): 2.50% APY; child/adult joint account.

All three disclose zero monthly fee and no minimum balance. They pass essential
and Public eligibility preview checks. If approved, US All and No monthly fee
would reach five; No minimum balance would reach four because Marcus remains
unknown for that distinct field. This is a preview, not a published count.

Existing official-source AI verification was attempted for 360 and Amex under
the persisted policy; neither passed the 1.0 verification threshold (0/4 fields
verified). No invented model result or approval was substituted. Both remain
queued; Kids remains in Review. The three manual proposals are stored in the
manifest, not silently applied to the candidate rows. A concrete approval request
was presented to the Product Owner; no answer has been received at this record.

## Remaining Loan/GIC investigation

The bounded shortlist does not establish that five comparable products cannot
exist. It establishes why the inspected sources were not sufficient:

- [TD Personal Loan](https://www.td.com/ca/en/personal-banking/products/loans-and-lines-of-credit/personal-loan) and [RBC LOC](https://www.rbcroyalbank.com/loans-line-of-credit/line-of-credit.html) require individual pricing or reference-rate terms. No complete universal rate was inferred.
- [Laurentian student LOC](https://www.laurentianbank.ca/en/personal/lending/student-line-of-credit) describes variable base-rate pricing. The existing 6.70 scalar was not certified current by this review; it remains an explicit follow-up, not a newly verified Top 5 entry.
- [Vancity Fair and Fast](https://www.vancity.com/borrow/loans-lines-of-credit/fair-fast-loan) already occupies a personal-loan position; it is not a new additional product.
- [Alterna term rates](https://www.alternabank.ca/en/personal/rates/term-deposits) include promotional qualification. It was not stripped to make a GIC eligible.
- [Manulife GIC](https://www.manulifebank.ca/personal-banking/investments/guaranteed-investment-certificates.html) has multiple payout schedules and short/long redemption distinctions. The broad existing identity cannot safely be narrowed from headline rates alone.
- Vancity GIC schedules, redirected CIBC FHSA/non-redeemable pages and Laurentian/EQ access or schedule gaps did not yield five fully matched term/redemption records in this bounded pass. No GIC was published from incomplete evidence.
- Ally's disclosed balance tiers were preserved. No comparison-code exception was added merely to fill five positions.

Next work is targeted manual review of the prepared three US candidates and
exact-product GIC schedule evidence. Any broader ingestion/parser change is a
separate implementation decision. I-005's known bad BofA record is corrected;
the generic discount-language classifier regression remains open.

## Audit and verification

Operation: `top5-completion-20260924`; nine new approved versions and change events.
Previous immutable payloads are preserved; previous versions are superseded.
Unchanged evidence links are retained; changed-field official facts are private
change-event evidence, not public raw traces. This is a partial field review:
product `last_verified_at` and snapshot `refreshed_at` were not reset.

| Country | Prior snapshot | Published snapshot |
|---|---|---|
| CA | `agg_ratefix_d4eb3c61663f48b692233d1f140062dc` | `agg_top5_99d472e42bcd46d89d8a42f15eac21e1` |
| US | `agg_MI9ZhAwRg91x587w` | `agg_top5_f2f631407d044c2d933af435562fa3b1` |

- Rollback rehearsal passed before commit. Initial rehearsal failures on the
  missing Marcus projection and qualified loan text rolled back completely.
- Readback confirmed all nine normalized patches, nine immutable prior payloads,
  120 unchanged other canonical products and unchanged unrelated snapshot rows.
  An initial readback assertion was adjusted for existing normalization of
  no-op null fields; no financial discrepancy remained.
- Re-run returned `already_applied`, nine records, no commit.
- Production anonymous paginated HTTP reads matched all 165 CA and 51 US active
  products and their rate, deposit terms, fee, minimum and security fields to DB.
- Home grouping replay confirmed the table above with actual Public functions.
- API: public-products 13, deposits 11, rates 8 tests passed. Initial direct
  module invocation of deposits/rates failed import resolution; corrected
  discovery invocation passed. Public 34 and worker aggregate 8 tests passed.
- No runtime/UI files changed; no builds, deployment or layout QA claimed.
- Final document links and `git diff --check` checked at completion.

The existing unrelated Admin root goal remains open. This slice is partial while
manual approval is pending; not all requested conditions have five products.
