# SwitchaBank GSC SEO Action Plan — 2026-09-03

## 1. GSC Baseline and Date Range

The two workspace exports dated `2026-09-03` were opened as ZIP archives and
every CSV, including Korean UTF-8 filenames, was parsed. The raw ZIP/CSV inputs
remain untracked evidence and are not application assets.

- Performance rows cover `2026-08-25` through `2026-09-01`: 1 click, 79
  impressions, about 1.27% CTR, and weighted average position 61.21.
- Canada: 1 click / 49 impressions / 2.04% CTR / position 61.22.
- Desktop: 1 click / 67 impressions / 1.49% CTR / position 61.45; mobile:
  0 clicks / 12 impressions / position 59.75.
- The strongest early product intent was `variable flex mortgage` with 6
  impressions at position 18.33. BMO student-line-of-credit variants accounted
  for 32 impressions across the listed queries.
- On `2026-08-27`, GSC reported 17 indexed and 193 non-indexed pages: 188
  discovered/currently not indexed, 3 redirects, 1 noindex, and 1 duplicate
  without a user-selected canonical. This is a young, small sample and is not
  a ranking forecast.
- A Japanese, listing-state BMO product URL received 49 impressions. The CIBC
  listing-state URL received 22. Other priority product URLs also carried sort
  state. The clean root received the only click.

## 2. Confirmed Repository Root Causes

The Public runtime is Next.js 16 App Router with React 19, server components,
`generateMetadata`, server route handlers, and `proxy.ts` middleware.

1. `buildPublicHref` treated product detail routes as catalog destinations and
   copied sort/filter/view state into their links. Production served those
   polluted detail URLs as 200 pages.
2. Every product advertised EN/KO/JA sitemap and hreflang variants even though
   the localization policy keeps source-derived product facts untranslated.
   The Japanese BMO page was self-canonical/indexable, and initial HTML had
   `lang=en` until a client script changed it.
3. Product metadata failure used the Deposit grid title/description even for a
   lending or card product. Product titles also lacked a type-specific search
   intent descriptor.
4. Product content itself was server-rendered, but it was dominated by shared
   fact/compliance UI and lacked a concise product-specific overview and
   contextual related-product links.
5. The original sitemap had 226 URLs and 904 alternate entries, including 432
   KO/JA product alternates that were not substantially localized.
6. Category HTML exposed only the initial product batch; later batches depended
   on client-side continuous loading without a crawlable page chain.
7. The complete sitemap audit found two active CA records for `BMO Performance
   Chequing Account` with identical bank/name/type metadata. The record verified
   on `2026-08-22` is now the representative URL; the older `2026-07-23` route
   permanently redirects to it.
8. Production infrastructure currently redirects `http://switchabank.com` to
   HTTPS apex and then to `https://www.switchabank.com`, creating a two-hop
   HTTP-apex chain. The application cannot remove the first hosting-layer hop.

## 3. URL Normalization Policy

- Canonical host: `https://www.switchabank.com`.
- Default CA English product path: `/products/{productId}` with no query.
- Only meaningful non-default scope is retained: `locale=ko|ja` for the usable
  UI variant and `country_code={ISO2}` when not CA.
- Product routes discard search, bank/type/tag filters, amount/fee/term filters,
  sort, view, page/page-size, `utm_*`, `gclid`, `fbclid`, unknown parameters,
  and fragments. A changed valid route returns one `308` to the normalized
  target after active-product validation.
- Invalid/missing products return 404 before normalization so invalid routes do
  not become soft 404s or redirect to plausible-looking pages.
- `prod_LuH-Kei2S8uFFOyY` is a confirmed duplicate and resolves by `308` to the
  newer verified `prod_SNcPg2yBYt4rgyAt`. No canonical database row was edited.
- Catalog query states remain usable, canonicalize to their clean locale/country
  hub, and are `noindex,follow`. `page>1` exists only as a crawl path and is
  likewise non-indexable.

## 4. Locale, Canonical, and Hreflang Policy

Strategy B applies to product detail pages because their primary facts remain
source-language content:

- English product page: clean, indexable, self-canonical, with `en-CA` and
  `x-default` pointing to the clean English canonical.
- KO/JA product page: usable, server-rendered `lang=ko|ja`, `noindex,follow`,
  English canonical, no hreflang cluster, and no sitemap membership.
- Home, Deposit, Credit Card, Loan, and Methodology are substantially localized
  static surfaces and retain reciprocal `en-CA`, `ko`, `ja`, and `x-default`
  alternates per published country.
- The server derives `<html lang>` from the normalized locale request header;
  it is no longer corrected only after client JavaScript executes.

## 5. Indexable and Non-Indexable Page Rules

Indexable:

- clean Home, Deposit, Credit Card, Loan, and Methodology routes for each
  published country and supported localized static variant;
- one clean English route for each unique active Public product.

Non-indexable or excluded:

- catalog search/filter/sort/view/page variants (`noindex,follow`);
- KO/JA product detail variants (`noindex,follow`);
- Public `/admin`, API routes, invalid/deleted products, redirects, comparison
  state, arbitrary facet pages, and duplicate product aliases;
- any API-unavailable product fallback, which remains honest and noindexed.

## 6. Sitemap and Robots Rules

- Sitemap URLs must be production-host absolute URLs, status 200, indexable,
  canonical, non-redirecting, unique, and free of irrelevant parameters.
- Static localized alternates remain; product entries include English and
  x-default only. Active products use their meaningful `last_changed_at` or
  `last_verified_at` timestamp as `lastmod`.
- The post-fix sitemap has 225 URLs: 10 static country routes and 215 unique
  active product routes after duplicate consolidation.
- `https://www.switchabank.com/robots.txt` remains crawlable, permits Public pages/assets, disallows only
  `/api/` and `/admin`, contains no `noindex`, and points to
  `https://www.switchabank.com/sitemap.xml`.

## 7. Metadata Templates

- Lending title: `{Bank} {Product}: Rate, Term & Prepayment — SwitchaBank` for
  mortgages; `Rate, Limits & Details` for lines of credit; `Rate, Amount &
  Details` for personal loans.
- Deposit/card title: `{Bank} {Product}: Rates, Fees & Details — SwitchaBank`
  or the applicable type descriptor.
- Description: product/bank identity plus up to two present verified facts,
  country context, verification date, and an official-bank confirmation cue.
  Missing/noisy facts are omitted; no value is inferred or statically copied.
- Non-default country pages add the country name to keep market metadata
  distinguishable. API-unavailable detail metadata uses a neutral localized
  unavailable title and is noindexed; it never inherits a category title.
- H1 uses the same bank/product identity. Open Graph/Twitter metadata reuses the
  metadata source rather than independently generating financial claims.

## 8. Implemented Changes by File

- `app/public/src/lib/public-url-policy.ts`: one product URL policy, locale and
  country normalization, clean canonical creation, indexability, and the
  documented BMO duplicate alias.
- `app/public/src/lib/public-query.ts` and product link consumers: remove
  listing state from product links; support non-indexable crawl pages.
- `app/public/src/proxy.ts`: active-product 404 guard, locale request context,
  and permanent clean-product redirects without loops.
- `app/public/src/app/layout.tsx`: server-render the normalized HTML language.
- `app/public/src/lib/public-seo.ts` and
  `app/public/src/app/products/[productId]/page.tsx`: type-specific title,
  verified-fact description, Strategy B robots/canonical/hreflang behavior,
  honest fallback, server data, and related products.
- `app/public/src/components/fpds/public/product-detail-surface.tsx`: visible
  breadcrumb, bank-qualified H1, verified product overview, clean related links,
  and exact 390px wrapping/action layout while retaining notices, dates,
  methodology, feedback, and official-bank verification.
- catalog pages, `product-grid-surface.tsx`, and
  `product-compare-workspace.tsx`: server JSON-LD, visible breadcrumb, clean
  product anchors, and no-script previous/next discovery.
- `public-structured-data.tsx`: truthful Organization/WebSite,
  CollectionPage/ItemList/BreadcrumbList, FinancialProduct, and LoanOrCredit
  graphs using visible Public data and stable canonical URLs.
- `app/public/src/app/sitemap.xml/route.ts`: active unique canonical products,
  English-only product alternates, and meaningful product timestamps.
- `app/public/scripts/seo-audit.mjs`: production-like Googlebot audit of every
  sitemap URL and required representative/dirty/invalid routes.
- `public-url-policy.test.ts`, `eslint.config.mjs`, `package.json`, lockfile,
  and `tsconfig.json`: URL regressions plus repeatable lint/test/audit commands.
- requirements, product-grid IA, decision D-075, WBS 5.60, Public README, and
  development journal: align the live contract and verification record.

## 9. Tests and Command Results

Run from `app/public` unless noted:

- `pnpm install --frozen-lockfile=false`: passed; lockfile updated for ESLint
  9.39.5 and `eslint-config-next` 16.2.3.
- `pnpm run lint`: passed with zero warnings.
- `pnpm run typecheck`: passed.
- `pnpm run test`: 5 URL-policy tests passed.
- `FPDS_PUBLIC_API_ORIGIN=https://switchabank-api.vercel.app pnpm run build`:
  passed with Next.js 16.2.3 Webpack production output.
- production server plus `SEO_AUDIT_ORIGIN=http://127.0.0.1:3000 pnpm run
  seo:audit`: passed for 225 sitemap URLs and 10 required representative
  routes, plus localized/noindex, dirty redirect, duplicate alias, deposit/card
  samples, and invalid-product cases.
- built HTML inspection confirmed product facts, title, description, canonical,
  robots, H1, breadcrumb, JSON-LD, and verification content before client
  execution. Next.js 16 may stream metadata for capable user agents; the audit
  reads both head and streamed metadata while excluding script/style/SVG tags.
- headless browser QA: desktop 1440px BMO detail and tablet 768px Loan catalog
  rendered correctly. Exact DevTools emulation at 390px reported inner/client/
  scroll width `390/390/390`, one H1 ending at x=374, and zero overflow
  offenders; 768px and 1440px also had no document-width overflow.
- repository root `git diff --check`: passed; Windows line-ending notices are
  informational and not whitespace errors.

## 10. Deployment Checks

1. Deploy the Public project from `app/public` with the existing Webpack build
   and `FPDS_PUBLIC_API_ORIGIN=https://switchabank-api.vercel.app`.
2. Confirm server-only app/API secrets remain set and no ZIP, CSV, `.env`, or
   screenshot artifact is included in the deployment.
3. Check `https://www.switchabank.com/robots.txt` and
   `https://www.switchabank.com/sitemap.xml`; expect
   the production host and 225 URLs if the active product snapshot is unchanged.
4. Request the five priority clean product URLs and confirm 200, one H1, English
   canonical, index/follow, product content, verification date, and valid JSON-LD.
5. Request dirty BMO/CIBC/Vancity/Scotia/product-state examples; confirm one
   308 to the clean route. Confirm KO/JA clean product variants remain 200 with
   `noindex,follow`, English canonical, correct HTML lang, and no hreflang.
6. Confirm `prod_LuH-Kei2S8uFFOyY` returns 308 to
   `prod_SNcPg2yBYt4rgyAt`; confirm an invented product ID returns 404.
7. Verify Home, Deposit, Credit Card, Loan, and Methodology at 1440px, 768px,
   and exact 390px, including locale switching, focus order, notices, feedback,
   official links, comparison, filters, and continuous loading.
8. Confirm `https://switchabank.com` goes directly to the www HTTPS origin if
   hosting configuration can be adjusted; otherwise retain the known apex HTTP
   two-hop item for infrastructure follow-up.

## 11. Manual Google Search Console Checklist

- Submit/resubmit `https://www.switchabank.com/sitemap.xml`.
- Inspect both live and indexed versions of the five priority clean product
  URLs and the three canonical hubs. Confirm rendered HTML, indexing allowed,
  declared canonical, and Google's selected canonical.
- Request indexing only for the five clean priority product pages and important
  hubs, not parameterized or noindexed locale variants.
- Start validation for the resolved redirect, noindex, and duplicate-canonical
  groups when GSC offers validation. Do not validate unrelated coverage issues.
- Inspect the former Japanese BMO URL, CIBC sort URL, other GSC dirty URLs, and
  the older BMO duplicate route; verify Google sees their 308/English canonical
  outcomes and later drops them as selected result URLs.
- Confirm KO/JA product URLs are not in the submitted sitemap and that static
  localized hubs retain reciprocal hreflang.
- Record the deployment timestamp and screenshots/export dates so later
  comparisons use a clean pre/post boundary.

## 12. 7-Day and 28-Day Monitoring Metrics

At 7 days (`2026-09-10`) compare against the short baseline:

- sitemap discovered/read status and submitted-versus-indexed counts;
- live/selected canonical for all five priority products;
- count of parameterized product URLs still receiving impressions;
- redirect, noindex, duplicate-canonical, and discovered-currently-not-indexed
  statuses; crawl errors and 5xx rates;
- impressions, clicks, CTR, and position by query/page/device for BMO Student
  Line of Credit, CIBC Variable Flex Mortgage, Vancity Fair and Fast Loan,
  both Scotiabank priority mortgages, clean hubs, and mobile.

At 28 days (`2026-10-01`) repeat the same export and compare clean URL share,
indexed count, discovered-currently-not-indexed count, priority-query visibility,
CTR, and average position. Technical success means consistent crawlable 200/
308/404/noindex/canonical signals and clean selected URLs. Indexing volume,
ranking, impressions, and clicks remain controlled by Google and user demand;
no ranking or indexing guarantee is made.

Remaining monitored risks are the young GSC sample, crawl/indexing lag, upstream
Public API availability during dynamic rendering, the hosting-layer HTTP apex
redirect chain, future canonical-data duplicates, and future KO/JA product
indexing requiring real fact localization before Strategy A can be adopted.
