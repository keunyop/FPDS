# FPDS Public

This package is the anonymous FPDS market view and product catalog. It presents
only review-approved public projections; raw evidence, review state, and private
source traces remain inside FPDS Admin. Its customer-facing identity is
`SwitchaBank`; `FPDS` remains the internal platform/runtime name.

## Runtime Routes

- `/` is the canonical public Home view. Its first viewport pairs a short market
  thesis with a simple world map and the published product count for every
  currently collected country. Deposit, Credit Card, and Loan are equal direct
  next actions. The main content places Deposit Top 5
  on the left and Loan Top 5 on the right at desktop, stacking both lists below
  that breakpoint. Deposit uses the highest disclosed numeric rates; Loan uses
  the lowest disclosed numeric rates. Neither list is a personalized
  recommendation. The two groups use distinct Deposit/Loan family rails,
  labels, and icons; catalog navigation is a text-style more link below each
  list rather than a competing header button.
  Home always reads the full selected-country snapshot: bank, Product Type,
  customer-tag, amount, fee, term, sort, page, and catalog-view query state
  from a Deposit, Credit Card, or Loan screen does not narrow Home.
- `/dashboard` is a permanent compatibility redirect to `/`. Query parameters
  are preserved, but all internal Home links and search metadata use the root.
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

The Public visual system uses a warm flat canvas, deep ink typography,
evergreen verification states, maple selection emphasis, and ochre Loan cues.
The code-native SwitchaBank mark is a simple pair of opposing horizontal
arrows. It communicates comparing the current option with another and making a
switch without introducing a literal bank, toggle, or decorative illustration.
The wordmark is one uninterrupted same-color name. The shell mark and
white-on-evergreen app icon share the same geometry so the identity remains
clear at small sizes.
Generic dashboard-card
repetition, decorative gradients, synthetic scores, and recommendation
language are avoided.

Home uses real snapshot values rather than invented illustration data. Its
country coverage map reads the existing public country catalog, and its dual
Top 5 lists avoid repeated family labels, internal
evidence explanations, and competing header actions. Catalog cards are
product-family-aware records with visible institution identity, one primary
metric, up to two essential supporting facts, a Compare control, and an
official bank-page action when `product_url` is available. Optional audience
tags and highlight badges stay off list cards so they do not compete with the
comparison facts; approved detail remains available on comparison and product
detail. The product name still opens the internal detail route. The metrics
follow the resolved country-product essential contract.
Canada shows Chequing fee/balance/transactions and GIC
rate/term/minimum-deposit/redeemability. US Checking shows
fee/opening-or-minimum-balance/fee-waiver activity, US CDs show
rate/term/minimum-deposit/early-withdrawal penalty. Lending and Credit Card
catalog cards render one numeric Interest rate from the current approved
projection; a disclosed range uses its lowest explicit absolute rate, while
reference-rate components and qualification percentages are excluded. The
complete assumption-bearing rate/APR summary remains visible in comparison and
product detail. Savings, Personal Loan, and Line of Credit likewise use their
market profile. Incomplete governed products are excluded during aggregate
refresh. Filters are progressively disclosed and sort controls stay close to
the results. Deposit opens at Interest rate descending, Credit Card at Annual
fee ascending, and Loan at Interest rate ascending; there is no separate
Default sort choice.
Every catalog Search conditions panel includes one localized bank-or-product
search field. Its bounded q value matches institution or product names
case-insensitively as a literal substring. Typing is debounced briefly;
search, checkbox, and select changes update the shareable URL and filtered
results without an Apply action.

Catalogs server-render the first 20 products. An intersection sentinel requests
only the next API page through /api/public/products, appends unseen product
IDs, and continues when the end of the expanded list is reached. The loader,
completion state, error message, and retry action are localized and announced
accessibly. Previous/Next controls and page URL state are not part of the
catalog experience.

The sort rail ends with accessible Grid and List controls. Grid retains the
type-aware comparison cards. List presents one compact product row and
emphasizes the value for the active sort while retaining product detail,
Compare, and available official-bank actions. The view mode is catalog-local
URL state and remains in place while filters, sort, or additional pages load.
When no `view` value is present, desktop starts in Grid and mobile starts in
List. An explicit Grid or List choice overrides that responsive default and is
preserved in subsequent catalog URLs.

Home ranking rows reuse the same text-style official-bank action as catalog
cards, including the external-link icon and safe new-tab attributes. They do
not wrap that action in a secondary outline button.

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

Home and every product detail show the same localized information notice:
Public facts are collected and organized from public materials with AI-agent
assistance, are not financial-product advertising, and are independently
provided without compensation from the displayed institutions. The notice
also states that SwitchaBank works to keep information current and that users
must reconfirm current product information and conditions on the institution's
official website before applying.

The desktop header uses a compact country selector backed by countries
represented in their latest completed active public snapshots. The mobile
header keeps the switch mark and `SwitchaBank` wordmark visible and moves Home,
Deposit, Credit Card, Loan, and country selection into one hamburger menu.
Country changes reset
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
- Korean body copy keeps words together, Japanese copy follows strict line
  breaking, and compact navigation, filter, action, rate, and freshness labels
  remain on one line. Purposeful body and heading wrapping is still allowed.
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
the localized unavailable state instead of leaving navigation pending. Public
product and filter reads use a five-minute server revalidation window; summary,
ranking, and scatter reads use fifteen minutes, matching their aggregate
refresh cadence while preserving snapshot freshness metadata in the UI.

Verified bank logo assets live under `public/bank-logos/` or use approved
official URLs in the `BankLogo` mapping. A failed image falls back to an
unframed, accessible bank-code mark while retaining the institution name for
assistive technology. The SwitchaBank shell mark is implemented in
`public-mark.tsx`; `src/app/icon.svg` is the matching favicon/app icon.

## Analytics and Consent

Public GA4 is loaded with Next.js `Script` and is disabled unless the build
receives a valid `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` in the `G-...` format. The ID
is a public tag identifier, not a secret, but the real value still lives in the
deployment environment rather than source control.

When configured, a first visit shows localized EN/KO/JA analytics choices.
Google scripts and `_ga` cookies load only after Allow; Decline leaves the tag
unloaded. The footer keeps an Analytics choices control available, and revoking
a prior grant denies analytics consent, removes GA cookies, and reloads without
the tag. Advertising storage, advertising user data, personalization, and
Google signals are denied. No user ID, financial value, product-click event, or
conversion event is sent by the Public application.

The integration disables the tag's default page view and sends one explicit
`page_view` for the initial screen and each Next.js client-side navigation,
including the previous virtual URL as the referrer. Keep GA4 Enhanced
Measurement's `Page changes based on browser history events` option disabled to
avoid duplicates. Verify live changes with Google Tag Assistant and the GA4
Realtime or DebugView report.

## Search and Sharing

The canonical production origin is `https://www.switchabank.com`. Root Home,
catalog, Methodology, and public product detail pages emit absolute canonical
URLs plus EN/KO/JA language alternates while retaining country-owned URL state.
Catalog search, filter, sort, and view variants canonicalize to the clean
country/locale catalog URL and use `noindex,follow` to avoid duplicate index
surfaces.

`https://www.switchabank.com/robots.txt` allows the anonymous site, excludes
same-origin API paths, and points to
`https://www.switchabank.com/sitemap.xml`. The explicitly XML-escaped sitemap
includes clean static Public routes and available product detail URLs for each
published country, with language alternates. Product details emit
product-specific metadata and public-only
`FinancialProduct`/breadcrumb structured data. A two-second product-detail
proxy checks active-snapshot membership before streaming so missing products
return HTTP 404; timeouts and broader API failures fall through to the honest
noindex unavailable state. The code-native
`https://www.switchabank.com/opengraph-image` supplies the shared Open
Graph/Twitter preview without exposing private evidence or introducing
financial claims.

## Verification

Run from `app/public`:

```powershell
pnpm run typecheck
pnpm run build
```

## Vercel Deployment

Use `app/public` as the Vercel project root. The Public server components and
same-origin BFF routes read the upstream API from `FPDS_PUBLIC_API_ORIGIN`; set
it to `https://switchabank-api.vercel.app` for both Preview and Production.
There is no browser-side database or private API credential.

The Vercel project is `switchabank-public`. Its customer Production domains are
`https://switchabank.com` and `https://www.switchabank.com`; the underlying
stable project domain remains `https://switchabank-public.vercel.app`. The
legacy `bankompare-public` stable, team, and main-branch aliases were removed
after the 2026-08-23 SwitchaBank domain migration; historical generated
deployment URLs remain immutable Vercel records.

The project-local `vercel.json` pins the framework to Next.js so the
repository-root FastAPI configuration cannot override this app in Git builds.
Keep the `switchabank-public` Root Directory at `app/public`, its Framework
Preset at Next.js, and **Include source files outside of the Root Directory**
disabled. Public has no runtime dependency on files above its project root.
The production build uses the supported Next.js Webpack opt-out because the
current Next.js 16.2.3 Turbopack build can nondeterministically emit different
server chunks to the same output path on Vercel. Development continues to use
the default Turbopack path.

```powershell
cd app/public
pnpm dlx vercel@latest link --yes --project switchabank-public
pnpm dlx vercel@latest env add FPDS_PUBLIC_API_ORIGIN production,preview `
  --value https://switchabank-api.vercel.app --force --yes --no-sensitive
pnpm dlx vercel@latest env add NEXT_PUBLIC_GOOGLE_ANALYTICS_ID production `
  --value G-REPLACE_WITH_REAL_ID --force --yes --no-sensitive
pnpm dlx vercel@latest deploy --prod --yes
pnpm dlx vercel@latest deploy --yes
```

Verify the Production root Home, the `/dashboard` permanent redirect,
`https://www.switchabank.com/robots.txt`,
`https://www.switchabank.com/sitemap.xml`, and the same-origin
`/api/public/countries` route.
Because `NEXT_PUBLIC_*` values are embedded at build time, adding or changing
the GA4 ID requires a new Production deployment. Do not configure the
placeholder value or reuse the Production stream in Preview unless the Product
Owner explicitly approves Preview traffic in the same Analytics property.
Preview deployments may require the Vercel deployment-protection bypass used by
`vercel curl`. When the Public domain changes, update the FastAPI project's
Public web-origin/CORS setting before enabling direct browser-to-API calls; the
current Public client uses its own same-origin BFF for interactive reads.

The current production-rendered baseline was checked at `1440px`, `768px`, and
exact `390px` widths across Home, Deposit, Credit Card, Loan, selected
comparison, Deposit detail, Loan detail, and Methodology in EN, KO, and JA. The
checks cover document
overflow, language metadata, heading structure, touch targets, browser errors,
comparison selection, reduced motion, the mobile wordmark/menu, responsive
Grid/List defaults, and the live aggregate snapshot.
