# Public Comparison Guides

Status: Implemented P2-1; deployment remains separately scoped.
Authority: Product Owner request, FR-PUB-027, D-084, WBS 5.70.

## Experience and scope

`/guides` provides an entry without an existing product. Four allowlisted
`/guides/[slug]` pages cover base/promotional rates, monthly fee waivers, GIC
maturity/withdrawals and switching ordinary Canadian deposit accounts. Each
has original EN/KO/JA copy, three short reading checks, a relevant comparison
path, official sources and a guide-specific review date. Home exposes one
short link before purpose shortcuts; the footer and matching curated pages
also link to the guides. Existing visual tokens and primitives are reused.

The primary action uses the existing curated comparison readiness gate. When
three compatible banks are not available, or the public API fails, it links
to the relevant existing catalog. The ordinary comparison and calculator lead
to the approved official-bank actions. No account ownership input is required.
Guide content remains readable while the data-dependent link loads or fails.

Scope is explicitly Canada. Country switching/direct non-CA queries go to
that country's related catalog, preserving locale and product type. This does
not add Canadian product assumptions to the US experience or assert that
Korean/Japanese visitors are a validated priority market.

## Authorship, source checks and correction

Publisher is the existing SwitchaBank service. No legal entity, named expert,
professional certification, institutional endorsement or independent human
review is invented. Copy discloses AI-assisted writing/translation and checks
against official sources; independent financial-expert review has not occurred.
These are general comparison explanations, not personalized financial advice.

The initial 2026-09-26 check covered English official FCAC sources and the
meaning of all EN/KO/JA copy against them:

- [Savings accounts](https://www.canada.ca/en/financial-consumer-agency/services/banking/bank-accounts/savings-account.html): introductory periods, balance tiers and rate basis.
- [Chequing accounts](https://www.canada.ca/en/financial-consumer-agency/services/banking/bank-accounts/chequing-accounts.html): monthly fees, balance waivers and separate transaction charges.
- [GICs and term deposits](https://www.canada.ca/en/financial-consumer-agency/services/rights-responsibilities/rights-investing/rights-guaranteed-investment-certificates.html): maturity, interest payment, early access and renewal disclosure.
- [Transferring products/services](https://www.canada.ca/en/financial-consumer-agency/services/banking/transferring-products-services.html): recurring transactions, account access, funding and closure checks; registered transfers are separate.

No current bank-specific offer, eligibility, required application document or
monetary promise is authored. General sources are separate from approved product
projections. Product names and conditions remain in their source language.

The native disclosure reuses the existing `site_feedback` dialog. Visitors
supply guide title/passage in the message; no new payload or analytics event is
introduced. Operators check a reported error against the official source,
correct confirmed errors and update the guide text/review date. Record material
changes and verification in the journal. No response-time promise is made.

Future substantive edits must check the cited official page, align all three
languages, preserve numeric/rate meanings, verify related routes and run the
relevant Public tests. The Product Owner owns editorial scope; external native
language or professional review must only be claimed after it actually happens.
`GUIDE_REVIEWED_AT` is an editorial source-check date, not product freshness.
Currently all four guides share the same actual initial check date; split into
per-guide dates when only a subset is rechecked. Do not automatically advance
review dates on builds or source fetches.

## Search boundary

Only these authored guide pages get localized self-canonicals, reciprocal
hreflang and 15 sitemap entries (index plus four pages, three locales).
Unknown guide slugs return real HTTP 404 before streaming; extra/invalid or
repeated query values are noindex. Non-CA queries redirect to catalogs.
Structured data describes the visible article and actual publisher/source date.

Product KO/JA routes remain noindex with English canonical and no localized
product sitemap entries. Curated data gates and arbitrary filter noindex rules
remain unchanged. No product-condition translation or search-ranking guarantee.
The [Google content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
informs source/creation transparency, not a promise of traffic or rankings.
Language demand should be assessed from actual permitted GA/GSC reports; no
new event, identifier or collection permission is implied.

## Verification

Run Public unit tests, lint, typecheck and production build. Check all five
routes in EN/KO/JA at 390x844, 768px and 1440px; source/disclosure keyboard
access; newcomer-to-comparison/calculator/bank navigation; comparison retention;
consent/dialog/dock behavior; invalid/foreign routes; sitemap and product SEO.
Replay approved CA/US public projections and test ready, held, unavailable and
loading destinations with analytics/outbound writes blocked. Retain the existing
comparison, calculator, catalog, finder and bank-handoff regressions.
