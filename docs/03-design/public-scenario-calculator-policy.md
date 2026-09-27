# Public same-amount calculator

Date: 2026-09-26. Authority: Product Owner P1-3 implementation request,
FR-PUB-025, D-082, WBS 5.68. This amends only the P1-2 prohibition on adding
arithmetic; comparison storage and finder rules remain unchanged.

## Screen and approved data

`/compare` opens a separate noindex `/calculator` with the same public IDs,
country and locale. Choose two of up to four selected products. Reuse the
uncached comparison BFF, including current active membership, timeout, country,
identity and single-snapshot validation. Loading/recheck hides old calculations;
missing products and request errors stay distinct, with Check latest to retry.
A visible-window return rechecks data. Inputs survive rechecks, but reset on
reload or route/scope changes. No canonical mutation or deployment is required.

Both products must be different active records of the same deposit type,
country and explicit currency. Savings/Chequing offer 1/3/6/12 whole calendar
months (default 12). GIC offers only exact shared approved rows, up to 120 months
or 3650 literal days; prefer 12 months when available. Month and day keys never
substitute for one another. Each product uses its own selected-row rate and
minimum, never its headline or a representative maturity. Different redemption
terms may be displayed at the full shared maturity; early withdrawal is excluded.

Interest reuses version-1 `deposit_terms`, with an explicit annual basis and no
reason/calculation_reason. Missing annual basis, APY/APR, promotions (including
expired promotions), tiers/bonuses, linked returns, compound and variable GICs
remain unavailable. Chequing interest is outside the first model. Existing
single-product calculators, Home and finder retain their existing contracts.

Monthly fees use only the approved Savings/Chequing `public_display_fee`, whose
financial-field contract defines the base monthly charge and excludes caps,
transaction charges and conditional zero outcomes. A disclosed waiver or
promotion blocks the fee estimate. Missing, negative, non-finite or fractional-
cent fees stay unknown. GIC fees are unavailable because the current Public
contract supplies no verified monthly GIC fee. Never infer zero from missing.

## Arithmetic and boundaries

- Initial hypothetical amount: 20,000; show published minimum failures per product.
- Accept decimal input from 0 through 1,000,000,000,000, up to two decimals.
  Blank, negative, exponent, grouped, non-finite and oversized input is invalid.
  Disclosed product and selected-row minimums apply to each interest result.
- Interest = amount × annual percentage / 100 × months / 12, or literal days / 365.
- Fixed fees = disclosed monthly charge × whole months. Never prorate monthly
  fees to literal-day terms. Invalid amount does not erase independent fixed fees.
- Use decimal rational arithmetic and round each final result half up to cents.
  Difference = displayed B cents minus displayed A cents; preserve sign and zero.
- Show interest and fee differences separately. No combined total, net profit,
  recommendation, suitability ranking or guaranteed payout.
- Keep concise assumptions visible: unchanged rate/fee; excludes tax, compound
  interest, other charges and early withdrawal. Full formula is in a disclosure.
  Preserve source names, localized EN/KO/JA labels, product verification and
  the existing official-bank action.

## Privacy and measurement

Financial amount and chosen period live only in the calculator component.
They enter no form submission, URL, fetch, GA/dataLayer, engagement payload,
comparison provider, fingerprint, localStorage or sessionStorage. The input has
no form/name and disables autofill. Existing official-click counters receive
only country, product ID and their fixed event name; no calculator event is added.
No visitor profile or held-product relationship is inferred.

QA checks network payloads, browser storage and navigation after editing an
identifiable test amount; fixtures block engagement/GA/feedback writes. Existing
aggregate counts cannot isolate post-calculation conversion. Actual user ability
to explain differences/exclusions and changes in official-bank visits require
post-release observation; no uplift or user acceptance is claimed from tests.

## Implementation verification

Public 61 unit tests, lint, typecheck and production build passed. The existing
API deposit/product suites passed 24 tests, including expired promotions and
APY contracts. Production-build Chrome passed 73 fixture, live-projection replay
and regression cases across EN/KO/JA and 390/768/1440px. Browser QA confirmed
input isolation, explicit-save privacy, existing official-click payloads,
removed-maturity handling, BFF snapshot failures and retry. No user study,
measured conversion uplift or production deployment is claimed.
