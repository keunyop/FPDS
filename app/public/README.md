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
actions. Filters are progressively disclosed, sort controls stay close to the
results, and unavailable values remain explicitly unavailable.

Selecting up to four products opens a responsive comparison ledger. Differences
are highlighted without declaring a winner, and product-specific facts,
application method, and official-bank links remain visible. The comparison
stacks on mobile and never requires horizontal document scrolling.

Detail pages prioritize product identity and three decision-relevant facts,
then show only available canonical facts and conditions. Deposit details may
include an estimated-interest calculator and an approved term-rate table.
Lending details may include rate type, term, amortization, payment, prepayment,
amount or limit, and security when those fields are approved.

## Localization, States, and Accessibility

- EN, KO, and JA are selected with the `locale` query parameter. Locale is
  preserved across navigation, metadata is localized, and the document `lang`
  value is synchronized before hydration.
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

Public data comes from `GET /api/public/products`,
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
exact `390px` widths across Home, Deposit, Loan, selected comparison, Deposit
detail, Loan detail, and Methodology in EN, KO, and JA. The checks cover document
overflow, language metadata, heading structure, touch targets, browser errors,
comparison selection, reduced motion, and the live aggregate snapshot.
