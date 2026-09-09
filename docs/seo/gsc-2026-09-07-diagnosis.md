# SwitchaBank Search Console diagnosis — 2026-09-07

## Conclusion

The supplied export does not establish a new site-wide indexing defect. Its
largest category is 213 URLs discovered but not yet crawled, rather than the
three categories highlighted in the email. Current public samples implement
the approved canonical/redirect/noindex policy. The exact five URLs highlighted
in the email cannot be identified from this ZIP, so their individual disposition
remains unresolved. Do not remove intentional noindex or canonical redirects.

## Export evidence

Input: `docs/seo/switchabank.com-Coverage-2026-09-07.zip` (1,028 bytes).
Read all four CSV entries directly, without changing the archive:
`차트.csv`, `심각한 문제.csv`, `중요하지 않은 문제.csv`, `메타데이터.csv`.
The metadata scope is all known pages, not a particular submitted sitemap.
There is no affected-URL list, last-crawl detail, or Google-selected canonical.

The chart ends on **2026-09-03**, despite the September 7 filename. It reports
27 indexed and 218 not indexed since August 28; August 27 had 17 indexed and
193 not indexed. September 3 impressions are 22. These are historical export
values, not a September 7 live index count. The chart does not show a new drop
in indexed pages after August 28.

| Export reason | Count | Interpretation and disposition |
|---|---:|---|
| Page with redirect | 3 | Expected for aliases and retired routes if the final canonical is correct; reported URLs are missing. |
| Excluded by noindex | 1 | Expected for filtered catalogs, KO/JA product variants, or private operations; reported URL is missing. |
| Duplicate without user-selected canonical | 1 | Inspect the exact URL and Google's selected canonical before deciding whether a correction is needed. |
| Discovered — currently not indexed | 213 | Main follow-up: Google has found the URLs but has not crawled them yet. The export cannot establish a server-capacity or content-quality cause. |
| Total not indexed | 218 | 3 + 1 + 1 + 213. Indexed count is a separate 27. |

All four reason rows say validation has not started. This alone does not mean
that each category needs a code fix or validation request.

Google explains these categories and that intentional exclusions can be normal
in its [Page indexing report documentation](https://support.google.com/webmasters/answer/7440203).
Redirects, canonical links, and sitemap membership should consistently indicate
the preferred URL; see [Google's canonical guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls).

## Current production observations

Public GET requests on September 7, without authentication or external writes:

| Requested URL/path | Observed response |
|---|---|
| `http://switchabank.com/` | 308 to `https://switchabank.com/` |
| `https://switchabank.com/` | 308 to `https://www.switchabank.com/` |
| `https://www.switchabank.com/` | 200 |
| `/dashboard` on www | 308 to `/` |
| `https://www.switchabank.com/robots.txt` | 200; allows `/`, excludes `/api/` and `/admin`, references the www sitemap |
| `https://www.switchabank.com/sitemap.xml` | 200, XML response |
| `/products/prod_IbZVSqaogb3BkWBd` | 200, `index, follow`, self-canonical on www |
| Same product with `?locale=ja` | 200, `noindex, follow`, canonical to clean English URL |
| `/products?sort_by=display_rate` | 200, `noindex, follow`, canonical to `/products` |
| `/products/prod_LuH-Kei2S8uFFOyY` | 308 to `/products/prod_SNcPg2yBYt4rgyAt` |

The two-hop HTTP-apex redirect remains a possible efficiency improvement, but
it resolves successfully and is not evidence of the reported 213-URL backlog.
These samples are **not** claimed to be the missing three redirect URLs or the
single noindex/duplicate URLs from Search Console.

The observed behavior matches `FR-PUB-020`, decisions D-065/D-075, and Public
README Search and Sharing. September 3 repository fixes are visibly present in
these production responses, though this audit does not identify the deployment
commit or its exact release time. No redeployment is justified merely by the
older journal's pending-deployment note.

## Search Console follow-up

1. In Indexing > Pages, open each reason, then export its **affected URL table**.
   Prioritize the duplicate (1), noindex (1), and redirect (3) URLs; also export
   the 213 discovered URLs. The overview ZIP currently supplied contains only
   totals and chart data.
2. For the duplicate URL, use URL Inspection to record last crawl, user-declared
   canonical, and Google-selected canonical. Compare the indexed record with
   Test live URL. If today's canonical is already correct, a historical report
   is not proof that the current implementation still lacks one.
3. For the noindex URL, distinguish an intentional variant/private route from a
   clean English public product. Only an unintentionally excluded public URL
   should have its indexing behavior changed. For redirects, inspect the final
   target and retain valid aliases.
4. Check the submitted `https://www.switchabank.com/sitemap.xml` entry for
   Success and last-read time. Submit it if absent or outdated. Request indexing
   for a small set of important clean English pages after their live inspection
   succeeds, using Home/catalog and the five existing audit priority products.
   Repeated submission does not establish or guarantee index inclusion.
5. For the 213 discovered URLs, match the export against the current sitemap,
   then inspect representative current URLs. Review Crawl stats host status and
   response failures to distinguish scheduling from an actual fetch problem.
   Do not label these pages thin content or server overload without evidence.
6. Compare the refreshed report after 7 and 28 days (September 14 and October 5):
   clean indexed URLs, discovered backlog, last crawl, and search impressions.
   Expected redirects/noindex variants need not disappear from exclusion totals.

Only the property owner can supply authenticated URL Inspection/Crawl stats
and perform these Search Console actions with the tools available in this
session. No Search Console property, sitemap submission, hosting configuration,
production deployment, canonical data, or runtime code was changed.

## Verification result

Passed against Production from `app/public`:

```powershell
$env:SEO_AUDIT_ORIGIN='https://www.switchabank.com'
node scripts/seo-audit.mjs
```

Result: `SEO audit passed: 225 sitemap URLs and 10 representative routes.`
The existing audit additionally covers localized static content, KO/JA product
noindex, filtered catalog noindex, polluted detail redirects, the duplicate
alias, invalid-product HTTP 404/410, and representative deposit/card links.
All 225 sitemap pages passed its status, canonical, HTML robots, title,
description, H1, language, JSON-LD, and internal-product-link checks, including
unique titles/descriptions across the sitemap. Separate host/robots/sample
requests above also checked redirect Location and X-Robots-Tag headers.
This is a point-in-time HTTP/content audit, not a Googlebot crawl, authenticated
URL Inspection, complete header audit, rendered-browser QA, or indexing promise.
No runtime changes were needed; no new build or application test suite was run.
