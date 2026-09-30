# SwitchaBank Blog

Status: Implemented locally; Production deployment remains separately scoped.
Authority: Product Owner's 2026-09-30 blog request, FR-PUB-028, D-088, WBS 5.74.

## Reader experience

`/blog` and the allowlisted `/blog/eq-bank-vs-tangerine-vs-td-savings`
deliver one original comparison article in EN/KO/JA. A ruled feature section,
existing official bank logos, an article contents list, mobile-stacked comparison
table, hypothetical interest example, checklist and related guides lead to the
existing Canadian savings catalog. Desktop/mobile navigation and the footer
expose Blog. No account ownership is required.

The blog is implemented in the existing Next.js Public package.
Browser verification found that the former root loading boundary hid streamed
article HTML without JavaScript. Its unchanged skeleton now belongs to the
existing data routes and Home's explicit Suspense wrapper; blog pages render
complete readable HTML without that boundary. For one article,
versioned typed content avoids a separate CMS account, database, publishing API,
dependency or runtime Markdown execution. Existing Button, feedback, logo and
semantic tokens are reused; no vendor primitive is edited.

Coverage is explicitly Canadian. Blog links from another market enter the
Canadian editorial surface with its scope visible. Switching country while
reading, or requesting a non-CA country query, redirects to that country's
Savings catalog with locale preserved. Article content does not depend on the
product API. Comparison links target the catalog, which already handles empty
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

## Search and measurement

Clean index/article URLs receive localized canonicals, reciprocal EN/KO/JA and
x-default alternates, descriptions, social metadata and six sitemap entries.
BlogPosting and BreadcrumbList describe the visible article; CollectionPage/
ItemList describe the index. The code-native PNG preview is served locally.
Unknown slugs return HTTP 404 before streaming. Extra, repeated and invalid
query parameters are noindex/follow and canonicalize to a clean locale URL.
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
   Extend the source registry per article when adding the next article.
3. Recheck any fee, condition or offer with the exact official product source.
   Preserve ambiguity; do not infer numbers from templates or calculator copy.
   Update all affected languages together. Advance only the dates actually
   supported by the editorial change/check.
4. Update the route manifest allowlist and article-specific social artwork when
   adding a new topic. Sitemap entries and the index follow the article registry.
5. Run Public tests, lint, typecheck/build and the relevant browser audit.
   Record material changes in the journal before the normal release workflow.

Review this article's bank-specific conditions monthly and before reuse in a
campaign; recheck sooner when a reported correction or known bank change
arrives. This is an editorial maintenance instruction, not an automated job.
Use site feedback to report the title and passage; correct confirmed errors
against official sources. Product records still use their existing approval
and freshness workflow.

## Verification

From the repository root, against a locally started Public production build:

```powershell
uv run --with playwright python app/public/scripts/blog-audit.py
```

The audit covers 390/768/1440px EN/KO/JA index/detail, exact financial example,
source links, metadata/JSON-LD, six sitemap entries, PNG preview, real 404,
query noindex, country redirect, source-independent rendering, menu focus,
JavaScript-free article HTML and the catalog handoff. Browser writes and
third-party calls are stubbed. Screenshots are local under ignored
`tmp/blog-audit/`. Public unit tests cover allowlists, query policy, country
handoff, citation/anchor integrity, financial example arithmetic and analytics.
