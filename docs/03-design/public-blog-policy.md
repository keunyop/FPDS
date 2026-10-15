# SwitchaBank Blog

Status: Implemented locally; Production deployment remains separately scoped.
Authority: Product Owner's 2026-10-14 two-market card-rewards request,
2026-10-13 US checking article request,
2026-10-10 additional US article request and
2026-10-09 country-scoped blog/US article request;
earlier blog requests, FR-PUB-028, D-088 and WBS 5.74 remain historical context.

## Reader experience

`/blog` lists the selected country’s allowlisted original articles in EN/KO/JA:
four Canadian and four US articles, including market-specific credit-card
cashback/welcome-bonus guides alongside the existing deposit comparisons. US index and article URLs include
`country_code=US`; Canada retains its existing URLs. A ruled feature section,
existing official bank logos, an article contents list, mobile-stacked comparison
table, illustrative interest, penalty or fee example, checklist and related guides
lead to the
matching country’s deposit or credit-card catalog, according to the article.
Desktop/mobile navigation and the footer expose Blog. No account ownership is required.

The blog is implemented in the existing Next.js Public package.
Browser verification found that the former root loading boundary hid streamed
article HTML without JavaScript. Its unchanged skeleton now belongs to the
existing data routes and Home's explicit Suspense wrapper; blog pages render
complete readable HTML without that boundary. For these authored articles,
versioned typed content avoids a separate CMS account, database, publishing API,
dependency or runtime Markdown execution. Existing Button, feedback, logo and
semantic tokens are reused; no vendor primitive is edited.

Header/mobile/footer Blog links retain the selected country. The list and its
structured data include only that country’s articles. Changing country from an
article, or explicitly requesting another country for that article, redirects
to the selected country’s blog index with locale preserved. A bare US article
URL resolves to its native US query, keeping the header and article consistent.
Markets without authored articles show localized empty text and remain noindex;
this does not activate a new market. Related editorial links stay in the same
market. Product catalog actions and feedback use the article’s country.
Article content and country-scoped listing do not depend on the product API. Comparison links target the catalog, which already handles empty
and unavailable data; they do not imply all three named accounts are published.

## Editorial contract and initial verification

Author/publisher is SwitchaBank; there is no invented professional author or
independent expert review. The visible disclosure states AI-assisted writing
and translation, official-source checks, no compensation from discussed
institutions, and the existing site-feedback correction route. The source date
is separate from product verification. Initial publication/source check:
2026-09-30. Names remain in English; localized prose is authored explanation,
not a translation written into canonical product conditions.

Official sources and bounded claims:

- [EQ Personal Account](https://www.eqbank.ca/personal-banking/personal-account):
  no monthly fee/minimum balance; the higher rate requires qualifying recurring
  direct deposits of at least CAD 2,000/month. Search fetch returned 403; a
  direct read-only HTTP fetch succeeded and the exact official application
  content confirmed these statements. No interest percentage was copied.
- [Tangerine Savings](https://www.tangerine.ca/en/personal/save/savings-account):
  no monthly fee/minimum balance; distinguish regular rate and eligible
  new-client offer. Rate fields returned unresolved templates, so no numeric
  rate or current promotional return was inferred.
- [TD Every Day Savings](https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/every-day-savings-account):
  CAD 0 monthly fee, one included transaction, CAD 3 extra chargeable
  transaction, and separate eligible own-TD-account transfer treatment.
  Other fees/exceptions remain subject to the linked current terms.
- [FCAC Savings accounts](https://www.canada.ca/en/financial-consumer-agency/services/banking/bank-accounts/savings-account.html):
  introductory rates, balance thresholds and calculation-basis checks.

The interest example is explicitly fictional in every language. For CAD 10,000
and simple annual interest over 12 months, 5% for three months followed by 1%
for nine gives CAD 200; 3% throughout gives CAD 300. No compounding, exact-day
accrual, tax, fee or changing-balance assumption is hidden. It is neither a
current bank offer nor an APY claim. No bank ranking, suitability promise,
deposit-protection/tax claim or financial-data mutation is introduced.

## Second article — 2026-10-05

The chequing comparison targets the intent behind Canadian no-monthly-fee
accounts and balance-based rebates. It covers Tangerine No-fee daily Chequing,
Simplii No Fee Chequing and CIBC Smart Tier 1, with eight official citations
checked October 5. Product names remain in English; all three editorial
versions preserve identical financial conditions.

- Tangerine: CAD 0 base monthly fee, no minimum balance for that fee, unlimited
  named daily transactions and free Interac e-Transfer. The separate current
  fee schedule proves CAD 1.50 for other-bank Canadian ATM withdrawals.
- Simplii: CAD 0 monthly fee, unlimited named debit purchases/bill payments/
  withdrawals and free CIBC ATM use. No unproved minimum-balance claim or
  changing promotional amount is copied.
- CIBC: positive CAD 16.95 Tier 1 base fee remains visible. The rebate requires
  CAD 4,000 end-of-day balance each day of that month in one Smart Account,
  for up to three Smart Accounts. Separate tier/customer benefits qualify the
  comparison; this is not an unconditional zero-fee account.
- FCAC Chequing, ATM fees and transferring-service pages support transaction/
  channel checks, distinct operator charges and the payment-migration sequence.
  Historical ATM price ranges are not reused.

The example uses one account: twelve assumed fee months = CAD 203.40;
three missed-rebate months = CAD 50.85; separately, constant CAD 4,000 at a
fictional annual simple 3% = CAD 120 foregone interest, assuming zero interest
in the account holding that balance. Do not sum all scenarios. The visible
notes exclude compounding/tax/fees/balance changes and label the fictional
rate. Actual eligibility and realistic availability of the money matter.

Mid-article and closing buttons open the existing Canadian chequing catalog
ordered by monthly fee. Comparison selection/device saving/verification and
official-bank checks are explained using existing capabilities; no promise
that every discussed account is published is made. Both articles link to each
other; the older article's content and source dates remain September 30.

## Search and measurement

Clean index/article URLs receive localized canonicals, reciprocal EN/KO/JA and
x-default alternates, descriptions, social metadata and thirty country-scoped sitemap entries.
BlogPosting and BreadcrumbList describe the visible article; CollectionPage/
ItemList describe the index. The index has a generic PNG preview; each article has a distinct locally served
`/blog/[slug]/opengraph-image` preview. Only allowlisted article image paths
bypass the article check; unknown image paths still return 404.
Unknown slugs return HTTP 404 before streaming. Extra, repeated and invalid
query parameters are noindex/follow and canonicalize to a clean locale/market URL.
The single native US country query is indexable; a redundant CA query is not.
The blog does not create arbitrary SEO filter pages or alter product KO/JA
noindex and curated readiness gates.

Publication and modification dates are explicit content records, not build or
request times. Index lastmod is the latest article modification date.
Only the existing fixed-screen pageview mapping is extended to Blog and Blog
article. No slug, title, query, new event or identifier is transmitted.

Google's [article guidance](https://developers.google.com/search/docs/appearance/structured-data/article)
and [helpful-content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
inform metadata and authorship/source transparency. Indexing, rich results and
traffic increases are not guaranteed or measured by local verification.

## Add or revise an article

1. Confirm the topic/market remains within Product Owner scope. Add the slug,
   actual publication/modification/source-check dates and reading estimate to
   `app/public/src/lib/public-blog.ts`.
2. Add complete localized authored content and exact official sources in
   `public-blog-content.ts`. Keep the article-to-content mapping explicit.
   Keep source registries scoped per article via `blogSources`; update the
   content map and `blogPresentation` for its topic, catalog and related reading.
   Use `blogCatalogHref` for article actions: credit-card guides open native
   `/cards`; deposit guides retain their existing curated catalog destinations.
3. Recheck any fee, condition or offer with the exact official product source.
   Preserve ambiguity; do not infer numbers from templates or calculator copy.
   Update all affected languages together. Advance only the dates actually
   supported by the editorial change/check.
4. Update the route manifest allowlist and article-specific social artwork when
   adding a new topic. Sitemap entries and the index follow the article registry.
5. Run Public tests, lint, typecheck/build and the relevant browser audit.
   Record material changes in the journal before the normal release workflow.

Review each article's bank-specific conditions monthly and before reuse in a
campaign; recheck sooner when a reported correction or known bank change
arrives. This is an editorial maintenance instruction, not an automated job.
Use site feedback to report the title and passage; correct confirmed errors
against official sources. Product records still use automatic acceptance
and the existing freshness workflow.

## Verification

From the repository root, against a locally started Public production build:

```powershell
uv run --with playwright python app/public/scripts/blog-audit.py
```

The audit covers 390/768/1440px EN/KO/JA index/detail, exact financial example,
source links, metadata/JSON-LD, thirty sitemap entries, PNG preview, real 404,
query noindex, country-scoped lists/redirects/empty states, source-independent
rendering, menu focus and country/locale controls,
JavaScript-free article HTML and the catalog handoff. Browser writes and
third-party calls are stubbed. Screenshots are local under ignored
`tmp/blog-audit/` (override with `FPDS_BLOG_AUDIT_OUTPUT`). Public unit tests cover
allowlists, query policy, country
handoff, citation/anchor integrity, financial example arithmetic and analytics.


## Third article — 2026-10-08

`/blog/cashable-vs-non-cashable-gic-canada` adds an original EN/KO/JA comparison
of cashable and non-cashable access, with source-check date October 8. The CIBC
Flexible non-registered option and RBC One-Year Cashable examples preserve the
first-29-days/no-interest versus at-least-30-days boundary and partial-withdrawal
qualifications. TD Non-Cashable is explicitly inaccessible before maturity;
no invented early-exit fee or current numeric rate is supplied. FCAC supports
the disclosure checklist. Exact official URLs are in `public-blog-gic.ts`.

The fictional example holds CAD 10,000 for twelve months at annual simple 3%
and 3.5%: CAD 300 versus CAD 350, a CAD 50 difference. It excludes compounding,
tax, fees and early withdrawal and claims neither current offers nor APYs.
All three versions preserve these assumptions. The article targets the existing
GIC catalog and maturity guide, with no promise of catalog coverage.

The article uses topic-specific access column labels, four citations, its own
social preview, canonical/hreflang/BlogPosting and explicit dates. The three
articles plus index generate twelve localized sitemap URLs. Prior article
content/source dates remain unchanged. `blog-audit.py` now covers all three
articles and derives expected counts from its registry.


## US article and country-scoped discovery — 2026-10-09

`/blog/ally-vs-capital-one-vs-amex-high-yield-savings?country_code=US` adds a
concise EN/KO/JA comparison with four official sources checked October 9. Ally,
Capital One 360 Performance Savings and American Express HYSA each disclose no
monthly maintenance fee/minimum balance. Ally’s certain-transaction limit is ten
per statement cycle with no excess fee but potential closure for repeated excess
use. Capital One has no direct savings ATM withdrawal; Amex HYSA supplies no ATM
card, debit card or checks. All three rates remain variable. No current numeric
bank APY, rate winner or guaranteed annual return is asserted.

A semantic HTML infographic shows APY → fees → access. A proportional, labelled
bar chart compares fictional 3%/4% APYs on USD 10,000 for one year: USD 300/400,
a USD 100 difference. APY already includes compounding. Every locale states the
unchanged APY, retained interest, no deposits/withdrawals/fees/tax assumptions.
Text alternatives remain readable without JavaScript and do not rely on color.
US catalog links preserve locale and country; Canadian-only guides are omitted.

Only authored market/locale variants enter the sitemap: two country indexes and
four articles in three languages = eighteen URLs. US English uses `en-US`;
Canada retains `en-CA`. Unknown slugs/image slugs remain HTTP 404 before streaming.
Registry/source dates of the three existing Canadian articles are preserved.


## US savings versus CDs — 2026-10-10

`/blog/high-yield-savings-vs-cds-us?country_code=US` adds a concise EN/KO/JA
comparison. Four official sources checked October 10: Capital One 360
Performance Savings, Marcus CD guide, Ally No Penalty CD and CFPB's CD overview.
It preserves Capital One's variable APY/no direct ATM withdrawal, Marcus's
USD 500 minimum and early-exit penalty, and Ally's fixed 11-month term,
full-balance-plus-interest withdrawal after the first six days following funding.
It does not claim immediate access or invent a current numerical bank APY.

An accessible three-part infographic explains account structures. The second
visual shows a hypothetical penalty comparison on USD 10,000 original principal
at a 4.00% annual interest rate, explicitly not APY or a current bank quote.
Marcus's 12-month boundary is 90 days of interest (USD 98.63); an 18-month term
uses 180 days (USD 197.26), assuming a 365-day year. The note discloses rounding,
366 days in a leap year and that these are penalties, not earnings.

The closing link opens the US CD catalog; the related article stays in the US.
US-only list/schema discovery, localized canonicals/hreflang, BlogPosting,
article-specific social preview and explicit October 10 dates follow the existing
contract. Two country indexes plus five articles in three languages now produce
21 sitemap URLs; older article dates remain unchanged. No collection, database
publication or runtime deployment is part of this editorial slice.


## US checking fees comparison — 2026-10-13

`/blog/chase-vs-bank-of-america-vs-wells-fargo-checking-fees?country_code=US`
adds a concise EN/KO/JA article with five official sources checked October 13:
Chase's fee schedule, BofA Advantage Plus clarity statement, Wells Fargo's
Everyday fee summary/waiver page and CFPB maintenance-fee guidance.

Base monthly fees remain USD 15/12/15. The table explicitly shows only one
waiver route: Chase USD 500 in qualifying electronic deposits per statement
period; BofA at least one qualifying direct deposit of USD 250 per cycle;
Wells Fargo total qualifying electronic deposits of USD 500 per fee period.
Other waiver routes exist. Two USD 125 deposits do not meet BofA's single-deposit
route. Chase/Wells Zelle exclusions remain separate from their deposit thresholds.
Domestic cash withdrawals outside each bank’s ATM network cost USD 3/2.50/3
before operator fees;
overdraft and other services are not implied free or included in the example.

Reused accessible three-step infographic and cost bars show USD 180/144/180
for twelve charged periods at unchanged base fees, without waivers/initial fee
relief. Every locale distinguishes this from a first-year quote or total account
cost. Native US checking catalog and related links preserve country/locale.
Registry, allowlist, localized metadata, distinct PNG preview and 24 sitemap
URLs integrate with existing routing. Filipino article requests keep the English
fallback and native market; no untranslated Filipino article hreflang is added.
Existing article dates and CA/PH behavior are unchanged. Local editorial code
only; no collection, data publication or runtime deployment.


## Canada and US credit-card rewards guides — 2026-10-15

Two original EN/KO/JA articles use the requested Banksalad topic as inspiration,
with attribution separate from the official financial sources. They explain
planned-spending cashback and welcome offers. No source paragraphs, illustrations,
Korean offer rules, gift-card profit claims or monthly bonus cycling are reused.
Canada uses Tangerine's verified regular categories, conditional third category,
extra 10%/CAD100 offer, CAD1000 cap, November 30 application cutoff, 45-day
activation/60-day purchase windows and account/payout requirements. The US uses
Chase and Wells Fargo examples; Chase's USD500/three-month/20,000-point USD200
bonus preserves current-holder/24-month restrictions, fulfillment and posting rules.
Wells Fargo's prepaid-gift-card exclusion is named without claiming all issuers
have identical rules. FCAC/CFPB explain interest and purchase grace-period limits.

Each article has a three-step infographic and a clearly fictional first-year/
following-year chart: CAD340/240 or USD440/240 from annual eligible spending of
12,000 at 2%, with a separate one-time CAD100/USD200 bonus. Notes disclose zero
assumed fees/interest, unchanged spending and rates, and no quoted issuer return.
One Canadian and two US card examples keep exact native currency/annual fees;
responsive identities support one, two or three banks. Card article CTAs use
native /cards URLs; existing deposit article destinations and dates are preserved.
Filipino retains English editorial fallback. Four articles per country produce
30 localized blog sitemap URLs, with distinct social images and authored dates.
Local editorial code only; no collection, data publication, schema or deployment.
