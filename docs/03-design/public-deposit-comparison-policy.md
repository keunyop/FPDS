# Public deposit comparison and interest estimates

Date: 2026-09-24
Authority: Product Owner implementation request for growth proposal section C;
FR-PUB-021 amendment, D-079, WBS 5.65.

## Comparison boundary

Home Deposit Top 5 uses one selected Product Type, currency, annual-rate/APY
basis and, for GIC/CD, exact term and known redemption category. It ranks the
selected term row, never a representative rate from a different maturity.
Savings and GIC no longer share an ordered list. The Product Owner's Home
refinement replaces currency choices with Savings All / No monthly fee / No
minimum balance, and GIC/CD exact term plus redemption conditions. Home uses
CAD for Canada and USD for the United States, visibly shown alongside the
selected annual/APY basis. Other currencies remain available in the catalog;
there is no foreign-currency fallback or inferred currency for another country.

No monthly fee requires an explicit zero public fee and no fee-waiver condition.
No minimum balance requires an explicit zero minimum balance; this does not
claim a zero opening deposit. Unknown values never qualify. Presets appear only
when compatible records exist, with rate-basis labels added to distinguish
otherwise identical choices. Each preset retains rate-descending Top 5 order.
The single compact selector retains the existing Home layout and Loan list.
Empty eligible scope is honest; Top 5 does not promise five eligible records.

The finder retains optional bank/type search, exact My product selection and
at most three strict improvements. All types now require the same country and
currency. Savings/GIC additionally require the same explicit rate basis and
period; GIC requires a selected exact term and matching known redemption
category. These are eligibility gates for the existing one-metric comparison,
not a personal suitability score. Fees and lending retain their existing metric.
All pages are read before selection; a changed snapshot or failed later page
fails the request instead of presenting a partial ranking. Input amounts are
never sent by the calculator to a URL, storage or analytics.

## Additive Public contract

Product list/detail add nullable `deposit_terms` for Savings/GIC:

- `version: 1`; `basis: annual | apy | unknown`.
- `reason`: null for a usable comparison or a stable unavailable reason.
- `calculation_reason`: APY/compound or another reason, independent of ranking.
- `withdrawal: redeemable | non_redeemable | unknown`.
- `options`: explicit `key`, `months`, `days`, `rate`, `minimum_deposit` pairs.

A key such as `m12` is a calendar month term; `d360` is exactly 360 days. A
12-month label normalized historically to 360 days and a 1-year label normalized
to 365 days share `m12`; an explicitly stated 360-day investment does not.
Ranges do not create a scalar term. An unambiguous table may supply separate
options; conflicting duplicate rows, mismatched term labels/days, representative
terms outside the table and scalar rates absent from the schedule fail closed.
Promotions (including expired ones), balance tiers/bonuses, market-linked,
step-up and variable GIC returns cannot drive the simple estimate. An explicit
uniform annual rate for all balance tiers can be used without a tier formula.
Unknown annual basis is never inferred from a country or a naked percentage.

The aggregate builder now retains a bounded `deposit_conditions` whitelist
from the approved payload: calculation/payment/compounding/payout text, tier
flag/text and promotion rate/period/introductory flag. Until old snapshots are
rebuilt, Public reads only these fields from the exact `product_version_id`
already pinned by that projection, with matching product ID. It never joins the
latest canonical version and never returns the source payload, notes, evidence
or version ID to the browser. Stored snapshots, canonical data and verification
dates remain unchanged. Missing version records remain conservative omissions.

The single reviewed Oaken legacy annual-basis clarification is bound to the
exact product, country, bank, currency, approved version and matching 2.8%
scalar/standard values in [the review](../00-governance/public-deposit-comparison-review-2026-09-24.md).
It adds no replacement rate or product verification date; a new version/value
must supply a basis again. Existing public-rate classification also stops
mistaking eligibility for CDIC/FDIC coverage for a rate qualification, and
excludes indexed/market-linked/step-up GIC identity from all numeric consumers.

## Calculator

Savings lets the visitor select 30/90/180/365 days. GIC uses an actual permitted
term option. The initial amount is the greater of 10,000 and disclosed positive
minimums; a zero minimum is not an instruction to deposit zero. Explicit input
zero is valid only if minimums permit it. Blank, negative, non-finite, exponent,
more-than-two-decimal and over-1-trillion inputs have no estimate. Selected-row
and product minimums must be met. No currency substitution occurs.

The simple scenario formula is amount × annual rate / 100 × years. Years are
calendar months / 12 for an explicit month/year term, otherwise literal days /
365. Round only the final interest to two decimals. The UI says the rate is
assumed unchanged and excludes compounding, fees and taxes; it makes no net
benefit or guaranteed maturity-value claim. APY and explicit compounding need
another model and show a short reason plus the bank link. Other unsupported
cases retain the same concise unavailable state. Source content remains in its
original language; controls and reasons use EN/KO/JA.

## Release and verification

Release API before Public; legacy cached responses without `deposit_terms`
fail closed until their existing cache expires. The read bridge requires no
migration, refresh or live mutation. The aggregate writer preserves the same
conditions on subsequent authorized refreshes. Neither deployment nor
collection is part of this implementation request.

Use the Public package checks, the full API suite and worker aggregate tests.
Browser verification covers 1440/768/exact 390px, EN/KO/JA, real Oaken/INDEXED
GIC, Home product conditions and currency isolation, fixture GIC/APY/promotion
cases, finder loading/error/empty, and existing deposit/card/loan catalogs. Block analytics/feedback writes in QA.
