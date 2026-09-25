# Canadian purpose-specific comparisons

Date: 2026-09-25
Authority: Product Owner implementation request for growth proposal P1-1;
FR-PUB-020 amendment, D-080, WBS 5.66.

## Routes and boundaries

Only `/ca/savings-accounts`, `/ca/no-monthly-fee-chequing` and `/ca/1-year-gic`
are registered. They use approved active Public projections, never canonical,
review or evidence reads. Existing catalogs, finder, Top 5 and calculators keep
their existing eligibility and behavior. No new country/type, collection, data
correction, analytics event, comparison persistence or deployment is authorized.

CA Home shows three compact purpose links without requiring a finder input.
A ready comparison receives its curated link; an unready or unavailable one
links to its existing type-specific catalog. US Home is unchanged. Switching
country from a CA-only route leaves it for the selected country's Deposit
catalog; language switches preserve the curated purpose.

## Launch gate

One shared pure policy governs page rows, metadata, Home destinations and sitemap:

- Active CA/CAD products, valid official HTTP(S) link and recorded verification
  currently `within_window` or `review_due`. Expired/unknown/future verification
  cannot populate a new curated comparison. Due status stays visible.
- At least three distinct banks in the primary comparable group. This is an
  initial editorial quality threshold, **not a Google requirement**.
- Savings: at least three banks with an explicit compatible ongoing annual-rate
  or APY option. Separate bases; separately label qualified/promotional source
  summaries, never replace a base rate with the headline offer.
- Chequing: three banks with an explicit base monthly fee of exactly zero and
  no waiver condition. Positive fees with approved waiver conditions appear in
  a separate table and do not count toward the zero-base-fee gate. A zero value
  with a waiver, a missing amount, and negative/non-finite values are excluded.
  Zero monthly fee does not mean zero transaction fees or universal eligibility.
- GIC: at least three banks **per** matched annual/APY and redemption group,
  with one unambiguous `m12`, 12-month rate option. Literal 360/365-day terms,
  another maturity, uncertain redemption, promotions and linked returns cannot
  stand in for the required calendar-year comparison.
- Suppress established duplicate-product aliases. Exact bank/source duplicates
  collapse to the newest check only when their comparison facts agree; distinct
  variants remain separate. Sorting is bank/product alphabetical, not a ranking.

This stricter launch gate is scoped to the new curated pages. D-078's
warning-only freshness behavior remains unchanged on existing surfaces. It
neither withdraws a canonical product nor performs a new verification. Only an
ordinary authorized operator review can advance the recorded check date.

## Rendering and search

Server rendering includes all eligible comparison rows, the specific question's
short answer, coverage, original-source conditions, per-product check dates,
up-to-four comparison selection, detail links and existing tracked official-bank
links. Unknown promotions or withdrawal facts remain explicitly undisclosed;
no fee, promotion duration or withdrawal rule is invented. Generic eligibility
marketing text is not substituted for fee-waiver conditions.

Own EN/KO/JA copy, canonical URLs, reciprocal language alternates and public-only
CollectionPage/ItemList data apply only to these three allowlisted purposes.
Ready routes enter the sitemap in all three languages. Unknown slugs return
404. Known routes without enough verified data render a short `noindex,follow`
preparation state with a catalog path and no comparison or structured product
list. API failure instead gives a localized retry state. Neither held state is
linked from Home or included in sitemap.

Additional query parameters do not filter the curated dataset and remain
`noindex,follow`, canonicalizing to the clean locale route. Existing arbitrary
catalog filters remain noindex. No country/bank/filter permutations are created.
Product-detail English canonical policy remains unchanged.

The loader requires every page from one completed public snapshot, rejects
missing/duplicate rows, page drift, later-page failure and changing snapshot
identity or totals. Metadata/content share the request cache; existing product
cache is five minutes. The sitemap declares one hour, reduced to five minutes
by its product fetch dependencies in the current Next.js production build. A gate change can
therefore reach these surfaces at their existing cache intervals; held page
content fails closed when refreshed. Snapshot time never replaces a check date.

## Operations and measurement

Readiness on 2026-09-25 is recorded in the development journal after replaying
anonymous public data. No bank facts are re-verified by that replay. Savings
freshness and GIC term/basis/redemption coverage must be resolved through normal
operator review before these routes become discoverable. The code opens them
only after their approved public data meets the gate.

After an authorized release, review each URL's GSC non-brand impressions/clicks,
consented GA landing-page engagement, and same-period existing official-bank
click counts. Those counters have no entry-page attribution and must not be
called a curated-page conversion rate or divided by consented GA sessions.
No analytics credentials, configuration or event contracts changed. Search
performance and actual indexing remain unmeasured.

[Google's faceted-navigation guidance](https://developers.google.com/crawling/docs/faceted-navigation)
supports limiting uncontrolled URL combinations; it does not prescribe the
three-bank operating threshold or promise traffic improvement.
