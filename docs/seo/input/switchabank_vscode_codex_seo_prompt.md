# SwitchaBank SEO Optimization — VS Code Codex Prompt

You are the senior technical SEO engineer and senior full-stack engineer responsible for improving the production website **FPDS Public / SwitchaBank** at **https://www.switchabank.com**.

Your job is to inspect this repository, identify the actual framework and routing/data-fetching architecture, then **implement, test, and document production-ready SEO fixes**. Do not stop at a general audit or recommendations. Make safe code changes directly in the repository.

## 1. Business and safety context

SwitchaBank compares Canadian bank deposits, credit cards, mortgages, personal loans, and lines of credit. This is financial/YMYL content.

Hard constraints:

- Never invent or infer a rate, fee, limit, term, eligibility rule, ranking, review, rating, or claim that is not present in the existing verified product data.
- Do not hardcode dynamic financial values in static copy when they can be generated from the current product record.
- Preserve all existing compliance notices, source/verification dates, methodology links, error-reporting links, and official-bank verification language.
- Do not use keyword stuffing, hidden text, doorway pages, mass-generated thin pages, fake FAQs, fake reviews, fake authors, or unsupported structured-data claims.
- Do not describe a product as “best,” “lowest,” “guaranteed,” or similar unless the statement is objectively computed from the current dataset, timestamped, qualified, and already supported by the product methodology.
- Preserve existing UI behavior, accessibility, localization, analytics, product comparison, sorting, and filtering.
- Avoid unrelated refactors and large new dependencies. Reuse the repository’s framework and test tooling.
- Never expose secrets or commit environment files or raw private data.

## 2. Google Search Console baseline — export dated 2026-09-03

First, search the workspace for these files and parse every CSV if they are present. The filenames inside the ZIP files may be Korean UTF-8 filenames.

- `switchabank.com-Performance-on-Search-2026-09-03.zip`
- `switchabank.com-Coverage-2026-09-03.zip`

Do not commit the raw ZIP files unless they are already tracked intentionally. If the files are absent, use the embedded baseline below.

### Search performance

The export filter says “Web” and “Last 3 months,” but the available daily rows run from 2026-08-25 through 2026-09-01.

- Total daily performance represented in the export: **1 click, 79 impressions, about 1.27% CTR, weighted average position about 61.21**.
- Canada: **1 click / 49 impressions / 2.04% CTR / average position 61.22**.
- Desktop: **1 click / 67 impressions / 1.49% CTR / average position 61.45**.
- Mobile: **0 clicks / 12 impressions / average position 59.75**.

Top query rows:

| Query | Clicks | Impressions | CTR | Avg. position |
|---|---:|---:|---:|---:|
| flexible mortgage | 0 | 13 | 0% | 87.31 |
| bmo student line of credit interest rate | 0 | 12 | 0% | 62.92 |
| bmo professional student line of credit | 0 | 10 | 0% | 60.60 |
| bmo student line of credit | 0 | 7 | 0% | 63.00 |
| variable flex mortgage | 0 | 6 | 0% | 18.33 |
| professional student line of credit | 0 | 2 | 0% | 82.00 |
| cibc variable rate | 0 | 1 | 0% | 50.00 |
| bmo medical student line of credit | 0 | 1 | 0% | 52.00 |
| vancity fast and fair loan | 0 | 1 | 0% | 52.00 |
| scotia flex value mortgage 3 year closed term | 0 | 1 | 0% | 54.00 |
| bank of montreal student line of credit | 0 | 1 | 0% | 61.00 |

Top page rows:

| URL | Clicks | Impressions | CTR | Avg. position |
|---|---:|---:|---:|---:|
| `https://www.switchabank.com/` | 1 | 4 | 25% | 40.75 |
| `https://www.switchabank.com/products/prod_IbZVSqaogb3BkWBd?locale=ja&sort_by=display_rate&sort_order=asc` | 0 | 49 | 0% | 61.63 |
| `https://www.switchabank.com/products/prod_vIoiSSdl3kwJjM1d?sort_by=display_rate&sort_order=asc` | 0 | 22 | 0% | 63.05 |
| `https://www.switchabank.com/loans` | 0 | 5 | 0% | 43.60 |
| `https://www.switchabank.com/products/prod_g-yAIYCGJyxWOm8d?sort_by=display_rate&sort_order=asc` | 0 | 3 | 0% | 21.67 |
| `https://www.switchabank.com/products/prod_OOVZNobikI65DAAF?sort_by=display_rate&sort_order=asc` | 0 | 2 | 0% | 6.00 |
| `https://www.switchabank.com/products/prod_IbZVSqaogb3BkWBd?sort_by=display_rate&sort_order=asc` | 0 | 1 | 0% | 3.00 |
| `https://www.switchabank.com/products/prod_h18VyAGREB3optuJ?sort_by=display_rate&sort_order=asc` | 0 | 1 | 0% | 7.00 |

Known product mappings from the public site/data:

- `prod_IbZVSqaogb3BkWBd` = **BMO Professional Student Line of Credit**
- `prod_vIoiSSdl3kwJjM1d` = **CIBC Variable Flex Mortgage**
- `prod_g-yAIYCGJyxWOm8d` = **Vancity Fair and Fast Loan™**
- `prod_h18VyAGREB3optuJ` = **Scotiabank StartRight Mortgage Program for Temporary Residents**
- Resolve `prod_OOVZNobikI65DAAF` from the repository/database before changing it.

### Page indexing / coverage

As of the available 2026-08-27 row:

- **17 indexed pages**
- **193 non-indexed pages**
- Therefore, Google knows about approximately **210 pages**, but only about **8.1%** are indexed.

Non-indexed reasons:

- **188** — Discovered, currently not indexed
- **3** — Page with redirect
- **1** — Excluded by `noindex`
- **1** — Duplicate without user-selected canonical

Treat the low sample size and young data window carefully. Do not promise ranking or indexing outcomes. The immediate goal is to remove technical ambiguity and improve the quality and crawlability of every page that is intentionally indexable.

## 3. Important symptoms to verify in the repository

The GSC rows indicate these likely problems. Verify each one from the code and rendered output rather than assuming:

1. Product-detail URLs are carrying irrelevant listing-state parameters such as `sort_by=display_rate` and `sort_order=asc`.
2. An English-intent product is receiving most impressions on a Japanese URL containing `locale=ja`, indicating possible canonical, hreflang, internal-link, or locale-selection ambiguity.
3. Some public product search results have appeared with a generic category title such as `Deposits — SwitchaBank` even when the page is a loan product, indicating inconsistent dynamic metadata or fallback metadata.
4. Product content or metadata may depend too heavily on client-side fetching/rendering.
5. The sitemap may contain URLs that redirect, are non-canonical, are noindexed, contain unnecessary query parameters, or are not sufficiently valuable/localized to index.
6. Sorting/filtering/locale state may be propagated into internal product links and create duplicate crawl paths.
7. Many product pages may share too much boilerplate and too little product-specific explanatory content.

## 4. Start with repository discovery

Before editing, inspect at least the following:

- `package.json` and lockfile
- framework configuration
- route definitions and product-detail route
- server middleware and redirects
- localization/i18n implementation
- metadata/head generation
- sitemap and robots generation
- product data source, schemas, and fetch lifecycle
- server-rendering/static-generation behavior
- category/listing pagination, sorting, filtering, and link construction
- existing analytics and tests
- deployment configuration

Determine whether the app uses Next.js App Router, Next.js Pages Router, another React framework, or something else. Do not force Next.js-specific code into a different stack. Use the native SEO APIs of the detected framework.

Write a concise implementation plan in your working notes, then proceed immediately with safe changes. Do not stop after planning.

## 5. Implement in this priority order

### P0 — Canonical URL and duplicate-URL cleanup

Create one explicit URL-normalization policy and use it consistently in routing, metadata, internal links, and the sitemap.

Required behavior:

- The canonical English product URL should be the clean product route with no irrelevant listing or tracking parameters, for example:
  - `https://www.switchabank.com/products/prod_IbZVSqaogb3BkWBd`
- Remove at least these irrelevant parameters from product-detail canonical URLs and internal links:
  - `sort_by`
  - `sort_order`
  - category filter parameters
  - pagination state that does not change product-detail content
  - analytics/tracking parameters such as `utm_*`, `gclid`, and `fbclid`
- Preserve a locale parameter only when it represents an intentionally indexable, substantially localized page.
- Update every product-card/list/table/detail link so listing state is not appended to product-detail URLs.
- Prefer a server-side permanent redirect (`301` or `308`, matching framework conventions) from parameter-polluted detail URLs to the clean equivalent when removing the parameters cannot break required UI state.
- Preserve only meaningful parameters during normalization. Avoid redirect loops and redirect chains.
- Ensure HTTP/non-canonical host/trailing-slash variants resolve consistently to one production origin and path convention.
- Invalid, deleted, or unavailable product IDs must return a real `404` or `410`, not a soft-404 page with status `200`.
- Do not rely on `robots.txt` to solve canonical duplication. Google must be able to crawl duplicate URLs long enough to see redirects/canonical signals.

Add automated tests for the normalization function and representative redirects.

### P0 — Locale, canonical, and hreflang strategy

Inspect how English, Korean, and Japanese are implemented and how complete each localization is.

Use one of these two strategies, based on actual content quality and product requirements:

**Strategy A — index a locale** only when the page is substantially localized and intended to rank:

- Default English page: clean URL, preferably the existing URL without `locale`.
- Korean and Japanese: use the existing stable locale URL convention unless a route migration is already planned.
- Every indexable locale page must have a self-referencing canonical.
- Add reciprocal hreflang alternates for all indexable language versions, plus `x-default`.
- Use correct language/region codes based on the actual target, such as `en-CA`, `ko`, and `ja`; do not invent a region unless the product strategy requires it.
- Ensure `<html lang>` matches the visible page language.
- Include only indexable locale variants in the sitemap, with consistent alternate-language mappings if the framework supports them.
- Internal links from a localized page should retain that locale but must not retain irrelevant sort/filter parameters.

**Strategy B — do not index an incomplete locale** when the page only translates UI labels while substantial product facts remain untranslated or duplicated:

- Keep the page usable for visitors.
- Apply `noindex,follow` in server-rendered metadata.
- Keep it crawlable so Google can see the `noindex`; do not block it in `robots.txt`.
- Exclude it from the sitemap and from hreflang clusters.
- Do not redirect users away merely because their browser language differs.

Do not mix contradictory signals such as a noindexed locale in the sitemap or an hreflang alternate pointing to a noindexed URL.

Specifically investigate why the Japanese BMO product URL received 49 impressions for English-intent BMO student-line-of-credit queries, and fix the underlying canonical/hreflang/internal-link/default-locale issue.

### P0 — Server-rendered product content and metadata

For every indexable public route, ensure the initial HTML response contains meaningful content without requiring a client-side fetch to create the primary page.

For product pages, the initial HTML must contain at least:

- product name
- bank name
- primary product type
- available rate/fee/limit/term facts
- product-specific summary
- current verification/snapshot date
- compliance notice
- canonical tag
- robots directive
- title and meta description
- H1
- breadcrumb links
- relevant structured data

Use SSR, SSG, or ISR according to the current framework and data freshness requirements. Do not implement crawler-only dynamic rendering or cloaking.

If the app is Next.js App Router, inspect and correctly use framework features such as `generateMetadata`, server components, `generateStaticParams`, ISR/revalidation, `sitemap.ts`, `robots.ts`, and route redirects only where appropriate. If it is not Next.js, implement the equivalent native mechanisms.

### P0 — Unique and accurate metadata

Fix fallback metadata so no loan or credit-card product can inherit a title such as `Deposits — SwitchaBank`.

Generate deterministic, server-rendered, page-specific metadata from verified product data.

Requirements:

- Exactly one useful `<title>` per page.
- A unique, readable meta description for every important page.
- One visible H1 that closely matches the page’s actual topic.
- The title, H1, visible content, canonical URL, locale, and structured data must agree.
- Add useful Open Graph and social metadata without creating a second source of truth.
- Avoid truncation by keeping titles concise, but do not optimize to an arbitrary character count at the expense of clarity.
- Never put unsupported current rates in metadata. When including a dynamic rate, generate it from the verified record and include an appropriate date/qualification in visible content.

Create metadata templates similar to these, adapted to the actual data fields:

- Product title: `{Product name}: Rate, Limits & Details | {Bank} | SwitchaBank`
- Mortgage title: `{Product name}: Rate, Term & Prepayment | {Bank} | SwitchaBank`
- Product description: `Compare {Bank} {Product name}, including {two or three verified product-specific facts}. Public snapshot verified {date}; confirm current terms with the bank.`
- Category title: `Compare Canadian {Category} Rates & Terms | SwitchaBank`

Do not use the exact same sentence for every product. Build product-type-specific templates and include product-specific facts only when present.

### P0 — Sitemap and robots correctness

Audit the current sitemap generator and robots configuration.

The sitemap must contain only URLs that are:

- intentionally indexable
- canonical
- status `200`
- not redirected
- not `noindex`
- not soft 404s
- free of irrelevant sort/filter/tracking parameters
- valuable enough to expose to search engines

Additional requirements:

- Include the home page, canonical category/hub pages, methodology/about/editorial pages that should rank, and active canonical product pages.
- Exclude internal search results, arbitrary filtered/sorted states, comparison UI states, redirects, noindexed locales, admin/API routes, and invalid/deleted products.
- Use the product/content record’s meaningful updated or verified timestamp for `lastmod`; do not set every URL to deployment/build time unless its main content truly changed.
- Ensure absolute production URLs use `https://www.switchabank.com` consistently.
- Ensure `robots.txt` references the production sitemap.
- Do not block JavaScript, CSS, image, or API resources required for Google to render public pages.
- Do not place `noindex` directives in `robots.txt`.

Add a test that parses the generated sitemap and fails when it finds duplicate URLs, forbidden parameters, redirects, noindexed URLs, non-200 URLs, or an unexpected host.

### P1 — Crawlable internal linking and site architecture

Improve discovery and contextual relevance without changing the main design.

- Use real crawlable `<a href>` links for navigation and product links.
- Ensure the home page links to all principal category pages.
- Ensure category pages expose crawlable paths to all active products; if products are paginated or virtualized, provide crawlable pagination or server-rendered links rather than relying only on client interaction/infinite scroll.
- Add breadcrumb navigation to category and product pages.
- Add contextual “More from this bank,” “Related products,” and product-type links using clean canonical URLs and descriptive anchors.
- Do not let sorting/filter state leak into destination URLs.
- Prefer useful bank/product-type hub links over generating large numbers of thin facet pages.
- If bank hub pages already exist, strengthen them. If they do not exist, create them only when they can contain meaningful unique content and a useful list of products; do not create doorway pages.

### P1 — Product-specific content improvements based on GSC intent

Improve visible page content naturally. Do not create paragraphs solely to repeat keywords.

#### BMO Professional Student Line of Credit — `prod_IbZVSqaogb3BkWBd`

Prioritize this page because its URL accumulated the largest page impression count, but most impressions were assigned to a Japanese parameterized URL.

Naturally address these intents where supported by verified data:

- BMO student line of credit interest rate
- BMO Professional Student Line of Credit
- BMO student line of credit
- Professional Student Line of Credit
- Bank of Montreal student line of credit
- BMO medical student line of credit — mention medical/professional programs only if the current verified eligibility data explicitly supports them

Add useful product-specific sections only when supported, such as:

- current rate basis and how it relates to BMO Prime
- credit-limit range
- eligible program categories
- security/collateral conditions
- repayment timing
- fees
- application method
- last verified date
- comparison considerations

#### CIBC Variable Flex Mortgage — `prod_vIoiSSdl3kwJjM1d`

This is the clearest early ranking opportunity because `variable flex mortgage` has 6 impressions at average position 18.33.

Naturally cover, using verified data:

- CIBC Variable Flex Mortgage
- variable flex mortgage
- flexible mortgage
- CIBC variable rate
- available terms
- variable-rate nature
- annual prepayment allowance
- current verified rate and snapshot date, if present

Do not create a generic mortgage article inside the product page. Keep the copy tightly focused on this product and provide internal links to broader mortgage comparisons.

#### Vancity Fair and Fast Loan™ — `prod_g-yAIYCGJyxWOm8d`

Use the official product name first. Where natural, explain that users may also search for it as “Vancity Fast and Fair Loan,” while avoiding awkward repetition.

Include only verified loan amount, rate, term, eligibility, and application facts.

#### Scotiabank StartRight Mortgage Program for Temporary Residents — `prod_h18VyAGREB3optuJ`

Strengthen the page around its exact program name and verified temporary-resident eligibility, term, rate-type, payment-frequency, prepayment, and application-method facts.

#### `prod_OOVZNobikI65DAAF`

Resolve the product from the data source. It had 2 impressions at average position 6, so preserve its valid search visibility while cleaning the URL and metadata. Do not change or delete it until its identity and current status are confirmed.

### P1 — Trust and people-first financial content

Audit and improve trust signals that can be implemented from existing truthful information:

- clear methodology and data-source explanation
- who operates/publishes SwitchaBank
- how AI agents are used in collection/organization
- human or system verification process, only as actually implemented
- last verified/updated timestamps
- correction/report-error process
- independence/compensation/affiliate disclosure
- contact or feedback path
- clear distinction between SwitchaBank’s summary and the bank’s official terms

Do not fabricate author biographies, credentials, editorial reviewers, or review processes. If the repository has no truthful data for a field, omit it and document the gap.

Reduce boilerplate dominance by ensuring every product page has enough unique, useful, product-specific content. Shared compliance copy may remain shared.

### P2 — Structured data

Add or repair JSON-LD only when it accurately represents visible page content.

At minimum, consider:

- `Organization` and `WebSite` on the home page
- `BreadcrumbList` on category and product pages
- `CollectionPage` / `ItemList` on useful category listings

For product pages, inspect whether `FinancialProduct`, `LoanOrCredit`, `Product`, or another schema.org type accurately matches the visible content and current implementation. Do not assume rich-result eligibility.

Never add:

- fake `AggregateRating` or `Review`
- a false `Offer`, price, availability, or seller
- unsupported FAQ markup merely to chase a rich result
- structured data for content that is not visible on the page

Ensure JSON-LD is server-rendered, uses stable canonical URLs, has valid syntax, and is covered by tests.

### P2 — Performance, accessibility, and mobile rendering

Run the repository’s available performance checks and inspect likely SEO-impacting issues:

- key content must be present in initial HTML
- optimize LCP images and bank logos using existing framework image tooling
- prevent layout shifts caused by images, fonts, and loading placeholders
- remove unnecessary client-side JavaScript from public content pages where safe
- ensure mobile viewport and responsive layout work correctly
- use descriptive image alt text such as `{Bank name} logo` instead of generic `Image`, while using empty alt text for purely decorative images
- maintain keyboard access, labels, and heading hierarchy

Do not sacrifice correctness or accessibility for a synthetic score.

## 6. Build an automated SEO regression audit

Using existing test tooling where possible, add a lightweight automated audit, for example `scripts/seo-audit.*` and/or integration tests.

It should validate representative routes and preferably all sitemap URLs in a production-like build:

- HTTP status
- exactly one non-empty title
- unique title among sampled/all indexable pages
- non-empty page-specific meta description
- canonical exists and matches normalization policy
- canonical host is `https://www.switchabank.com`
- robots directive is correct
- exactly one H1
- `<html lang>` is correct
- reciprocal hreflang for indexable locales
- no forbidden parameters in canonical URLs or sitemap URLs
- no redirect/noindex/404 URL in the sitemap
- primary content exists in returned HTML before client-side execution
- JSON-LD parses successfully
- internal product links use clean URLs
- invalid product route returns 404/410

Use representative URLs at minimum:

- `/`
- `/loans`
- one deposits page
- one credit-card page
- `/products/prod_IbZVSqaogb3BkWBd`
- `/products/prod_vIoiSSdl3kwJjM1d`
- `/products/prod_g-yAIYCGJyxWOm8d`
- `/products/prod_h18VyAGREB3optuJ`
- the resolved clean route for `prod_OOVZNobikI65DAAF`
- supported localized variants
- parameter-polluted versions that should redirect
- an invalid product ID

## 7. Verification commands

Run the appropriate commands supported by this repository. At minimum, run equivalents of:

- dependency/install integrity check when needed
- lint
- type check
- unit tests
- integration/SEO tests
- production build

Do not claim a command passed unless you actually ran it successfully. If an unrelated pre-existing failure blocks a command, isolate it, document it precisely, and still complete every safe SEO change that can be verified.

Also inspect the built/server-rendered HTML rather than checking only React components or client DOM behavior.

## 8. Required documentation

Create or update:

`docs/seo/gsc-2026-09-03-action-plan.md`

Include:

1. GSC baseline and date range
2. root causes confirmed in the repository
3. URL normalization policy
4. locale/canonical/hreflang policy
5. indexable versus non-indexable page rules
6. sitemap rules
7. metadata templates
8. implemented changes by file
9. tests and command results
10. deployment checks
11. manual Google Search Console checklist
12. 7-day and 28-day monitoring metrics

Manual post-deployment GSC checklist should include:

- submit/resubmit the canonical sitemap
- inspect the live and indexed versions of the priority clean URLs
- confirm rendered HTML, canonical, indexing allowed, and selected canonical
- request indexing only for a small set of priority canonical pages, not every duplicate URL
- start validation for resolved redirect, noindex, and duplicate-canonical issues where appropriate
- monitor whether parameterized product URLs disappear and clean URLs become selected canonicals
- monitor indexed count, “Discovered – currently not indexed,” impressions, clicks, CTR, and average position
- compare query/page performance for the priority products after 7 and 28 days

Do not set ranking guarantees. Separate technical success criteria from outcomes controlled by Google.

## 9. Definition of done

The task is complete only when:

- safe production code changes have been implemented, not merely proposed
- product-detail internal links no longer propagate irrelevant sort/filter parameters
- canonical URLs are deterministic and tested
- the locale indexing policy is explicit, consistent, and tested
- product metadata is server-rendered, unique, and no longer falls back to the wrong category title
- primary product content is available in initial HTML
- the sitemap contains only canonical, indexable, status-200 URLs
- robots configuration is correct and references the sitemap
- priority pages have useful, truthful, product-specific content based on verified data
- structured data is truthful and valid
- lint/typecheck/tests/build have been run as far as the repository permits
- `docs/seo/gsc-2026-09-03-action-plan.md` is complete

## 10. Final response format

When finished, report in Korean using this exact structure:

1. **핵심 원인** — confirmed root causes, not guesses
2. **수정 내용** — grouped by canonical/indexing, rendering/metadata, locale, sitemap/robots, content/internal links, structured data/performance
3. **변경 파일** — each file and why it changed
4. **테스트 결과** — commands actually run and pass/fail status
5. **배포 후 GSC 작업** — exact manual checklist
6. **남은 위험/보류 사항** — only genuine unresolved items

Begin by inspecting the repository now. Do not return only a plan.
