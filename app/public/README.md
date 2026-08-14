# FPDS Public

This package is the anonymous FPDS market view and product catalog. It presents
only review-approved public projections; raw evidence, review state, and private
source traces remain inside FPDS Admin.

## Runtime Routes

- `/` redirects to `/dashboard`.
- `/dashboard` is the public Home view. Its first viewport pairs a clear market
  thesis with a live verified-record ledger built from the current aggregate
  product count, bank count, coverage, and freshness date. Deposit and Loan are
  equal next actions.
- `/products` is the Deposit catalog for review-approved `chequing`, `savings`,
  and `gic` products.
- `/cards` is the Credit Card catalog for review-approved `credit-card`
  products with annual fee and purchase interest rate comparison.
- `/loans` is the lending catalog for review-approved `mortgage`,
  `personal-loan`, and `line-of-credit` products.
- `/products/[productId]` shows the selected product's available public facts,
  conditions, official-bank action, freshness, and methodology boundary.
- `/methodology` explains the source-to-snapshot process, metric meaning,
  comparison boundary, freshness states, and public evidence boundary.

## Experience Baseline

The Public visual system uses a warm record-paper canvas, deep ink typography,
evergreen verification states, maple selection emphasis, and ochre Loan cues.
The code-native FPDS mark and the source-to-review-to-public ledger make verified
financial records the signature visual idea. Generic dashboard-card repetition,
decorative gradients, synthetic scores, and recommendation language are avoided.

Home uses real snapshot values rather than invented illustration data. Catalog
cards are product-family-aware records with visible institution identity, one
primary metric, up to two supporting facts, and clear Compare and Details
actions. The metrics follow the resolved country-product essential contract.
Canada shows Chequing fee/balance/transactions and GIC
rate/term/minimum-deposit/redeemability. US Checking shows
fee/opening-or-minimum-balance/fee-waiver activity, US CDs show
rate/term/minimum-deposit/early-withdrawal penalty, and US Mortgage keeps its
assumption-bearing rate/APR summary visible. Savings, Personal Loan, and Line
of Credit likewise use their market profile. Incomplete governed products are
excluded during aggregate refresh. Filters are progressively
disclosed and sort controls stay close to the results.

Selecting up to four products opens a responsive comparison ledger. Differences
are highlighted without declaring a winner, and only the type-specific
essential facts plus official-bank links remain visible. The comparison
stacks on mobile and never requires horizontal document scrolling.

Detail pages prioritize product identity and three decision-relevant facts,
then show only available canonical facts and conditions. Deposit details may
include an estimated-interest calculator and an approved term-rate table.
Lending details may include rate type, term, amortization, payment, prepayment,
amount or limit, and security when those fields are approved by the resolved
market profile. For country-specific overrides, optional Admin candidate copy
outside that profile is not projected to Public. Masked/template rates and
unrelated percentages never qualify as displayable rate facts.

The header uses a compact country selector backed by countries represented in
their latest completed active public snapshots. Country changes reset
country-owned bank and product filters rather than carrying invalid scope
across markets. The current governed published and collection scope includes
Canada and the United States; later countries remain fail-closed until their
market profiles and fixtures are registered.

## Localization, States, and Accessibility

- EN, KO, and JA are selected from the footer with the `locale` query
  parameter. Locale is
  preserved across navigation, metadata is localized, and the document `lang`
  value is synchronized before hydration.
- Country is selected from the header with the `country_code` query parameter.
  Canada is the clean-URL default, non-default ISO alpha-2 codes persist across
  navigation, and country names use the active UI locale.
- Source-derived institution and product content remains in its source language;
  FPDS-owned navigation, labels, freshness, methodology, and safety copy are
  localized.
- Loading, unavailable/error, empty, stale, fresh, and missing-value states use
  the same visual vocabulary across Home, catalogs, comparison, detail, and
  Methodology.
- Interactive controls provide a 44px minimum target, visible keyboard focus,
  semantic heading order, and reduced-motion support.
- Mobile sort rails and dense term-rate tables may scroll inside an explicitly
  bounded container; the document itself must not overflow horizontally.
- Public-owned dates use stable `yyyy-mm-dd` or `yyyy-mm-dd hh:mm` formatting.

## Data and Asset Boundaries

Public data comes from `GET /api/public/countries`, `GET /api/public/products`,
`GET /api/public/products/:productId`, `GET /api/public/filters`, and the public
dashboard endpoints. Reads use a short server-side timeout so a slow API renders
the localized unavailable state instead of leaving navigation pending.

Verified bank logo assets live under `public/bank-logos/` or use approved
official URLs in the `BankLogo` mapping. A failed image falls back to an
unframed, accessible bank-code mark while retaining the institution name for
assistive technology.

## Verification

Run from `app/public`:

```powershell
pnpm run typecheck
pnpm run build
```

The current production-rendered baseline was checked at `1440px`, `768px`, and
exact `390px` widths across Home, Deposit, Credit Card, Loan, selected
comparison, Deposit detail, Loan detail, and Methodology in EN, KO, and JA. The
checks cover document
overflow, language metadata, heading structure, touch targets, browser errors,
comparison selection, reduced motion, and the live aggregate snapshot.
