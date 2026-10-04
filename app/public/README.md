# FPDS Public

## Home Top 5 by required comparison facts - 2026-10-04

Deposit Top 5 now includes Chequing/Checking ordered by the verified base monthly
fee, lowest first, with required transaction costs beside each record. Optional
deposit interest, balances and waiver details do not change the fee order; a
conditional waiver never replaces the base fee. Amounts use the selected market's
currency. Savings/GIC retain comparable-rate order and explicit annual/APY,
exact-term and withdrawal boundaries. Loans retain comparable full-rate order.
Older malformed projections missing required costs, access/consequences, lending
terms/type or credit-line security cannot enter Home rankings. Missing optional
facts never affect eligibility or position. This changes only Public Home; no
collection, projection mutation, deployment or personalized ranking is added.

## Home and product detail clarity - 2026-10-02

Home renders each successfully loaded complete Top 5 product scope even if its
separate summary API fails. Empty lists distinguish no published target products,
home-currency gaps and unknown annual/APY basis or rate/term/access conditions.
Ranking eligibility and arithmetic are unchanged. Read-only API/BFF diagnosis on
October 2 found CA 30 products with no savings/GIC/loan records and US 5 products,
including two savings records with unknown rate basis; these counts are a dated
observation, not a promised live catalogue size.

Detail emphasizes required fees, rates, terms and access/security facts and puts
GIC term/rate tables before optional facts. Removes the repeated generated overview,
product-ID prose exceptions, optional-fact explanation and duplicate snapshot/
disclosure/private-evidence explanations. Product check dates/status, material
conditions, bank confirmation, methodology and reporting remain available.
No financial facts, collection gates, canonical data or deployment are changed.



## Required facts first - 2026-10-01

Catalogue cards and compact lists, comparison and curated tables share the current
required-fact presentation. Detail separates core metrics from verified optional
facts; empty optional rows/columns are omitted and zero/false retain their meaning.
Home Top 5 uses comparable rates, displays other required facts, and removes optional
balance/security presets. Existing financial qualifications and exact GIC terms
still constrain ranking; missing optional information is never a score penalty.
`public-product-presentation.ts` and `public-fact-copy.ts` own these rules/EN-KO-JA
labels. API adds an allowlisted optional `deposit_conditions` object for detail.
Deploy API then Public; this slice does not collect or publish products.

## New collection accuracy — 2026-09-30

Aggregate refresh admits new stamped canonical products only with a valid
content-bound automatic acceptance result. The result and source evidence stay
private; current projection/UI allowlists and comparison semantics remain.
The approved cutover deactivated 355 legacy products and replaced CA/US snapshots
with empty projections. Old versions/evidence remain private; new verified
collection can populate Public again.
The subsequent [live pilot](../../docs/00-governance/collection-accuracy-pilot-2026-09-30.md)
restored one verified CA product automatically. The subsequent
[economical recovery](../../docs/00-governance/collection-accuracy-recovery-2026-09-30.md)
restored TD U.S. Daily Interest Chequing; verified Public counts are CA 2 / US 0.
Its transaction-fee waiver balance is omitted from the general minimum-balance
field; missing rate and count values remain unknown.
See [policy](../../docs/03-design/collection-accuracy-policy.md) and
[impact assessment](../../docs/00-governance/collection-accuracy-audit-2026-09-30.md).

This package is the anonymous FPDS market view and product catalog. It presents
only review-approved public projections; raw evidence, review state, and private
source traces remain inside FPDS Admin. Its customer-facing identity is
`SwitchaBank`; `FPDS` remains the internal platform/runtime name.

## Blog (2026-09-30)

`/blog` and `/blog/eq-bank-vs-tangerine-vs-td-savings` provide a sourced
Canadian bank-account comparison in EN/KO/JA, with a responsive table, explicit
hypothetical interest example, original editorial content, checklist and
existing savings-catalog handoff. Header/mobile/footer links expose the blog.
Content is versioned in `src/lib/public-blog-content.ts`; no separate CMS or
dependency is needed. Clean localized URLs get canonical/hreflang, BlogPosting/
breadcrumb metadata, a local PNG social preview and six sitemap entries.
Fixed Blog/Blog article screen types use existing page views without slugs.

See [editorial checks, scope, maintenance and authoring](../../docs/03-design/public-blog-policy.md).
Run `uv run --with playwright python app/public/scripts/blog-audit.py` from
the repository root against a running local build for focused UI/SEO checks.

## Comparison guides (2026-09-26)

`/guides` and four allowlisted `/guides/[slug]` pages provide original EN/KO/JA
Canadian explanations with official FCAC references and a source-check date.
Home's newcomer entry and contextual links lead through a relevant curated
comparison (or the existing catalog when data is insufficient) to selection,
calculation and bank confirmation. No existing product is required.

The editorial disclosure identifies SwitchaBank, AI-assisted creation/source
checks and the existing site-feedback correction path; independent professional
review is not claimed. Product source-language/KO-JA noindex rules remain intact.
Only the authored guide URLs add localized canonical/hreflang/sitemap entries.
See [guide scope, sources and maintenance](../../docs/03-design/public-comparison-guides-policy.md).

## Persistent comparisons (2026-09-25)

`/compare` is a noindex, country-scoped four-product workspace. Catalog, curated
and detail choices survive filters/sort/navigation in memory; the header/footer
and compact mobile dock open the shared list. URLs contain only public IDs,
country and locale. Explicit device saving stores identities and term hashes
until deletion/browser clearing; revisits read current projections through the
uncached, bounded `/api/public/compare` BFF. Removed products, changed saved
terms and retriable failures stay distinct. No new analytics event or financial
input persistence. See [the complete contract](../../docs/03-design/public-comparison-list-policy.md).

## Runtime Routes

- `/` is the canonical public Home view. Its first viewport pairs a short market
  thesis with a same-type product finder: a visitor selects a product they
  already have, then checks up to three exact-Product-Type products that
  strictly improve one disclosed primary metric after matching country/currency
  and the deposit basis/term conditions below. Deposit, Credit Card, and Loan
  remain equal direct next actions. The main content places Deposit Top 5
  on the left and Loan Top 5 on the right at desktop, stacking both lists below
  that breakpoint. Deposit offers Chequing/Checking monthly fees, Savings conditions (all, no monthly fee)
  and GIC exact term/redemption choices within the selected country's home
  currency (CA CAD / US USD) and matching rate basis. Loan offers exact Product
  Type; security is shown for credit lines without optional security presets,
  within the same home-currency policy. Chequing orders monthly fees ascending;
  Savings/GIC order comparable rates descending; Loan orders comparable full rates ascending.
  Both lists read all snapshot pages before ranking; later-page failure or a
  changing snapshot shows unavailable rather than a partial result. Neither list is a personalized
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
- `/ca/[slug]` allowlists Savings, no-monthly-fee Chequing and 1-year GIC
  comparisons. A shared three-bank and verification gate controls rows, metadata,
  Home links and sitemap inclusion. Insufficient data shows a noindex holding
  state; Home falls back to the appropriate existing catalog. See the
  [curated comparison policy](../../docs/03-design/public-curated-comparison-policy.md).
- `/cards` is the Credit Card catalog for review-approved `credit-card`
  products with annual fee and purchase interest rate comparison.
- `/loans` is the lending catalog for review-approved `mortgage`,
  `personal-loan`, and `line-of-credit` products.
- `/products/[productId]` shows the selected product's available public facts,
  conditions, official-bank action, freshness, methodology boundary, and an
  Important note error-report dialog.
- `/methodology` explains the source-to-snapshot process, metric meaning,
  comparison boundary, freshness states, and public evidence boundary, and
  owns the Equal Earth country coverage map with product/distinct-bank counts.
- `/admin` is a separate noindex Public operations route. It requires a
  server-verified password and signed HttpOnly session, sends no GA page view,
  and shows bounded aggregate product/bank interaction counters plus anonymous
  product-error and site-feedback submissions. Country, type, category, search,
  and pagination filters remain server-rendered behind that session.

## Experience Baseline

The Public visual system uses a warm flat canvas, deep ink typography,
evergreen verification states, maple selection emphasis, and ochre Loan cues.
The code-native SwitchaBank mark is a simple pair of opposing horizontal
arrows. It communicates comparing the current option with another and making a
switch without introducing a literal bank, toggle, or decorative illustration.
The wordmark is one uninterrupted same-color name. The shell mark and
white-on-evergreen app icon share the same geometry so the identity remains
clear at small sizes.
Generic dashboard-card repetition, decorative gradients, and synthetic scores
are avoided. Recommendation language is reserved for the bounded Home finder
approved in `FR-PUB-021`; catalogs and Top 5 lists remain factual comparisons.

Home uses real snapshot values rather than invented illustration data.
Methodology's country coverage map reads the existing public country catalog
and renders active product and distinct-bank totals from the same completed
snapshot. The coverage loader prefers the country response's `bank_count`.
During a staggered API/UI
rollout, if an older cached country response omits that field, Home derives the
count from the established unfiltered `banks_in_scope` dashboard summary for
that country. Each compatibility lookup is isolated so a failed fallback does
not hide the country or its product count, and the fallback stops issuing
extra requests once the country endpoint supplies `bank_count`.

The Home finder uses only anonymous review-approved Public projections and
states that the visitor should start with a product they already have. Bank and
Product Type are optional narrowing controls. Product-name search works with
neither selected; focusing the empty field returns every active product
alphabetically in 40-row pages and loads more inside the bounded list as the
visitor scrolls. A non-empty name query is server-filtered against product
names only before one exact My product is selected. Arrow keys move through product suggestions, Enter selects, and Escape or
Tab closes the list. Product search leads the finder; optional bank/type
controls share a row beneath it. The candidate query stays
inside the active country and exact selected Product Type, reads every page,
and excludes currency mismatches before metric comparisons. Chequing
uses lower monthly fee, Savings and GIC use the higher rate for compatible
annual/APY basis and GIC term/redemption conditions,
Credit Card uses lower annual fee, and Mortgage, Personal Loan, and Line of
Credit use lower disclosed numeric rate. Missing metrics and ties never produce
a candidate, and at most three strict improvements are shown. The action reads
Find a better product and the selected record reads My product in EN/KO/JA.
The removed standing one-metric caveat is not rendered. Broader profile-based
or multi-factor recommendation remains out of scope.

The dual Top 5 lists avoid repeated family labels, internal
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
catalog cards distinguish full rates, ranges/schedules, reference-rate
margins, conditional discounts and promotions in EN/KO/JA. Approved rate text
stays in its source language on cards, comparison and detail. Only the API's
explicit `rate.kind=absolute` and finite `rate.comparable_rate` participate in
catalog rate sorting and dashboard scalar metrics. Deposit Home/finder and
calculators additionally use the explicit `deposit_terms` contract; a validated
GIC schedule supplies its selected term rate even when the headline is a range.
An old cached API response without this contract cannot supply a comparison
rate. Zero is a valid full rate; no benchmark arithmetic or minimum-range/
introductory shortcut is permitted. API deployment should precede Public;
existing response caches expire normally. Savings, Personal Loan, and Line of Credit likewise use their
market profile. Incomplete governed products are excluded during aggregate
refresh. Filters are progressively disclosed and sort controls stay close to
the results. Deposit opens at Interest rate descending, Credit Card at Annual
fee ascending, and Loan at Interest rate ascending; there is no separate
Default sort choice.
Every catalog keeps its localized bank-or-product search field visible above
the optional Search conditions panel. Short family titles and compact spacing
put products closer to the controls. Grid/List actions stay visible beside the
scrollable sort choices and provide 44px targets. Filter disclosure follows the
visitor's choice, including after the final filter is cleared. Its bounded q value matches institution or product names
case-insensitively as a literal substring. Typing is debounced briefly;
search, checkbox, and select changes update the shareable URL and filtered
results without an Apply action. Controls retain keyboard focus during URL
updates and restore their URL values on browser back/forward. Korean/Japanese
composition finishes before search navigation.

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
- A localized skip link moves keyboard focus to the content. The labelled
  route/country menu serves mobile and tablet widths below 1024px; desktop
  navigation exposes route names and the current page.
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

Product interactions use the same-origin `POST /api/public/engagement` BFF,
which forwards only country, active product ID, and one fixed event type with a
server-only shared credential. The password-gated `/admin` server component
loads `GET /api/public/admin/engagement-summary` and
`GET /api/public/admin/feedback` directly with that credential. Neither secret
is available in a browser bundle.

Product error reports and footer site feedback use the same-origin
`POST /api/public/feedback` BFF. Both dialogs require one localized structured
reason, include Other, allow up to 2,000 optional detail characters, warn
against personal/account information, and confirm the current submission.
Product reports send only the current product ID; the API copies bank, product,
Product Type, country, and snapshot context from the latest active Public
projection. Public never exposes other submissions.
The only submission-list surface is the password-gated Public `/admin`; the
anonymous Public experience and FPDS Admin application expose no feedback list.

Verified bank logo assets live under `public/bank-logos/`; asset provenance is
recorded in `public/bank-logos/SOURCES.md`. The registry covers the banks observed
across the CA/US Public catalog in the 2026-09-29 audit, including US BMO/TD
code aliases. `BankLogo` never
loads an institution image from a third-party origin: banks without a local
asset render an unframed, accessible bank-code mark while retaining the
institution name for assistive technology. Rendered image assets have explicit
intrinsic dimensions. The SwitchaBank shell mark is implemented in
`public-mark.tsx`; `src/app/icon.svg` is the matching favicon/app icon.

The Home heading and primary catalog actions render independently of upstream
summary and ranking data. Those requests start together and stream through
separate Suspense boundaries. The optional scatter plot is server-rendered SVG
with a screen-reader table, shared UI imports address only the required Radix
packages, and the small global stylesheet is inlined into the initial document
to avoid a render-blocking stylesheet request. Keep these boundaries measured
before adding a client chart runtime, umbrella UI dependency, or remote logo.

The Home map geometry in `public/world-map-equal-earth.svg` is a local static
asset generated from [Natural Earth](https://www.naturalearthdata.com/downloads/)
1:110m land data under its
[public-domain terms](https://www.naturalearthdata.com/about/terms-of-use/)
through `world-atlas` and the Equal Earth projection. It does not load an
external map service or tracking script at runtime.

## Public Analytics

Public GA4 is loaded with Next.js `Script` and is disabled unless the build
receives a valid `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` in the `G-...` format. The ID
is a public tag identifier, not a secret, but the real value still lives in the
deployment environment rather than source control.

When configured, GA4 starts automatically without a consent prompt or footer
choices (Product Owner instruction, 2026-09-28). Legacy consent storage is
ignored. Advertising storage, advertising user data, personalization and Google
signals remain denied. Only fixed screen-type URLs/titles and an empty referrer
are supplied: no query strings, product IDs, browser title or incoming referrer.
No user ID, financial value, product-click or conversion event is sent to GA.

First-party operational counters are separate from GA. Product-detail
clicks, official-bank clicks, and finder My product selections increment only
daily country/product aggregates retained for 400 days. No visitor ID, IP,
cookie, free-text query, referrer, user-agent, or financial/profile value is
stored. Finder selections are not unique-customer or verified-ownership counts.
The `/admin` path does not initialize GA.

The integration disables the tag's default page view and sends one explicit
`page_view` for the initial screen and each Next.js client-side navigation,
using fixed screen metadata and an empty referrer. Keep GA4 Enhanced
Measurement's `Page changes based on browser history events` option disabled to
avoid duplicates. Verify live changes with Google Tag Assistant and the GA4
Realtime or DebugView report.

## Search and Sharing

The canonical production origin is `https://www.switchabank.com`. Root Home,
catalog, and Methodology pages emit absolute canonical URLs plus reciprocal
`en-CA`/KO/JA language alternates while retaining country-owned URL state.
Product facts remain source-language content, so only clean English product
URLs are indexable. KO/JA product pages remain usable with `noindex,follow`, an
English canonical, and no product hreflang or sitemap membership. Catalog
search, filter, sort, view, and pagination variants canonicalize to the clean
country/locale catalog URL and use `noindex,follow`.

Product links retain only meaningful locale/country scope. Irrelevant catalog
and tracking parameters receive a permanent `308` to the clean detail route.
The confirmed duplicate BMO Performance Chequing Account route also resolves
to its newer verified representative record. Catalog HTML contains product
links and a no-script previous/next path so discovery does not depend only on
continuous client loading.

`https://www.switchabank.com/robots.txt` allows the anonymous site, excludes
same-origin API paths and `/admin`, and points to
`https://www.switchabank.com/sitemap.xml`. The explicitly XML-escaped sitemap
includes clean static Public routes and unique active English product detail
URLs for each published country. Product details emit type-specific metadata
and public-only `FinancialProduct` or `LoanOrCredit` plus breadcrumb structured
data; catalogs emit `CollectionPage`/`ItemList`/breadcrumb data. A two-second product-detail
proxy checks active-snapshot membership before streaming so missing products
return HTTP 404; timeouts and broader API failures fall through to the honest
noindex unavailable state. The code-native
`https://www.switchabank.com/opengraph-image` supplies the shared Open
Graph/Twitter preview without exposing private evidence or introducing
financial claims.

## Verification

Run from `app/public`:

```powershell
pnpm run lint
pnpm run typecheck
pnpm run test
pnpm run build
$env:SEO_AUDIT_ORIGIN='http://127.0.0.1:3000'; pnpm run seo:audit
```

Optional interaction and responsive regression, from the repository root with
Chrome installed and a running local Public build backed by approved products:

```powershell
$env:FPDS_UI_TEST_ORIGIN='http://localhost:3000'
uv run --with playwright python app/public/scripts/ui-ux-audit.py
```

This checks EN/KO/JA at 390/768/1440px, focus-preserving search/filters, IME,
finder keyboard navigation, shell names, comparison/calculator rendering and
skip navigation. It stubs browser writes and external requests. Data is read
through the local app; it needs at least two approved CAD savings products.

Run `pnpm run seo:audit` against a locally started production build. It checks
representative routes and every sitemap URL for status, metadata, canonical,
robots, language, H1, JSON-LD, clean internal product links, redirects, and
invalid-product 404 behavior. Set `SEO_AUDIT_CONCURRENCY=2` when the local API
cannot sustain the default eight concurrent sitemap checks.

## Vercel Deployment

Use `app/public` as the Vercel project root. The Public server components and
same-origin BFF routes read the upstream API from `FPDS_PUBLIC_API_ORIGIN`; set
it to `https://switchabank-api.vercel.app` for both Preview and Production.
There is no browser-side database or private API credential. Configure a long
random `FPDS_PUBLIC_APP_API_SECRET` that exactly matches the API environment,
set `FPDS_PUBLIC_ADMIN_PASSWORD` to the Product Owner value `1112`, and set an
independent long random `FPDS_PUBLIC_ADMIN_SESSION_SECRET`. All three are
server-only and should be sensitive Vercel variables.

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
`https://www.switchabank.com/admin` password/login/logout and aggregate view,
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

## Public verification freshness (2026-09-21)

Snapshot generation and product verification are separate. Public product rows
carry read-time verification state/deadlines; snapshot success is neutral and
never substitutes for a missing product check. Catalog, comparison, Home/finder
results and detail share the EN/KO/JA product status. Existing comparisons and
product availability stay intact. Legacy clients retain fresh/stale/unavailable,
with fresh restricted to known checks within their policy window.

See [the freshness policy and operator report](../../docs/03-design/public-verification-freshness-policy.md)
for contract details, the read-only overdue CLI, manual daily/weekly review and
release order. Initial warning-only intervals are 7/30 days for rate-led products and 30/90 days for chequing/cards. D-069 collection
is manual; these changes do not start collection, update facts or publish data.


## Deposit comparison conditions (2026-09-24)

The [deposit comparison policy](../../docs/03-design/public-deposit-comparison-policy.md) supersedes headline-only Savings/GIC
comparison and implicit one-year calculation. Home scopes rankings by type,
currency, rate basis and exact GIC term/redemption category. The selector uses
product conditions, with currency/basis shown as compact context. Zero-fee and
zero-minimum-balance conditions require explicit values, and conditional fee
waivers do not qualify as no monthly fee. The finder uses
those gates before its existing metric; the calculator uses disclosed annual
basis and an explicit period, or a concise unavailable reason and official link.
`deposit_terms` is additive. Public reads a bounded whitelist from the exact
approved version pinned by the snapshot; aggregates preserve these qualifiers
for future refreshes. Missing basis is never inferred from country. API release
precedes Public; old cached contracts fail closed. No live refresh or migration
is needed for the version-pinned bridge. See the policy for current data limits.

## Same-amount comparison calculator (2026-09-26)

The comparison list opens noindex `/calculator`. Choose two products and apply
one browser-only amount/period. It shows separate interest and fixed-monthly-fee
results and differences, using approved annual semantics and exact GIC rows.
Missing fees stay unknown; no net return, personal ranking or new event. Existing
comparison storage, finder and detail calculator behavior remain unchanged.
See [the calculator contract](../../docs/03-design/public-scenario-calculator-policy.md).

## Official bank handoff (2026-09-26)

Detail and each selected comparison place approved minimum/waiver/withdrawal
conditions beside their bank action, with currency, qualified rate/cost, product
check date and official hostname. Unknown conditions remain explicit. Mobile
shows the viewed product and direct bank action; dialogs and input
keyboards suppress it, and it replaces the comparison return dock while present.
Existing header comparison access and three-field click events remain.

The [handoff policy and operator commands](../../docs/03-design/public-bank-handoff-policy.md)
describe the bounded read-only failure/redirect report. Reports do not update
facts, product verification or official destinations.

## Conditional transaction, withdrawal and security requirements - 2026-10-01

The shared market profile v7 restores checking transaction costs, GIC/CD early-access rules and consequences, and line-of-credit security. Unlimited checking needs no excess fee; explicitly blocked early withdrawal needs no penalty value; explicit unsecured status is valid. Collection prompts expose grouped alternatives and conditions. Automatic acceptance/exclusion remains the only product workflow; no new Admin action or review queue is added.

The Public API rechecks affected snapshot-pinned versions under the current contract, including older receipts, and exposes numeric `transaction_fee`/`additional_transaction_fee`. Country counts use the same eligible products. Shared Public metrics show checking transaction costs and both GIC access and consequences in all supported locales. Deploy API/worker before Public; previous cached responses can remain until normal expiry. Read-only current-data assessment: 5 eligible of 24 active products, 19 needing evidence. No live mutations, paid collection or deployment were performed in this implementation slice.
