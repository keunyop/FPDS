# Public comparison lists

Status: Active implementation contract, 2026-09-25
Authority: Product Owner P1-2 request, FR-PUB-024, D-081, WBS 5.67.

## Selection and entry

One memory-only list per country holds at most four public product IDs across
search, filters, sort, continuous loading, Grid/List, curated pages and detail.
Locale changes preserve it; country changes select a separate list. Unsaved
selection ends on a full reload. The header and footer open `/compare`; a small
mobile bottom action returns to it from long catalogs/details. Consent and open
modal surfaces hide that action. The existing inline ledger remains available.

Detail offers Add to comparison and a same-type catalog scoped to other
published banks, ordered by bank name. The current bank is explicitly excluded;
if bank choices cannot be read the extra link is omitted. Same-bank related
products remain. No candidate score, winner or additional finder rule is added.

## Sharing and local saving

`/compare?product_id=...&product_id=...&country_code=CA&locale=en` contains only
public IDs, country and UI language. IDs are case-sensitive, unique and bounded
to four; malformed/oversized requests are rejected. Every arbitrary comparison
is `noindex,follow`, absent from sitemap and emits no product structured data.
Copy-link failure exposes a selectable URL. No financial input, relationship,
free-text query or private evidence is included.

Save on this device is the only write to
`switchabank.comparison.v1.<country>` localStorage. One saved list per country
contains a schema version, country, public IDs, public product names (bounded
identity for removed rows), and SHA-256 fingerprints of approved public terms.
It stores no financial-input values or full product payload. Saving replaces
that country's previous saved list and updates the comparison baseline.
There is no automatic expiry: it lasts until Delete saved comparison or browser
storage clearing. The short saved-state note explains this; deletion does not
clear the active in-memory list. Storage denial leaves browsing and sharing
usable. A new visit to an empty `/compare` restores the saved list; an explicit
Clear remains empty until restored again. Shared IDs take precedence over a
saved list. No accounts, server saved-list storage, sync or notifications.

## Current data and state handling

The Public-only `GET /api/public/compare` BFF accepts only the sharing fields,
with at most four product detail reads and an eight-second upstream timeout.
It bypasses the normal five-minute detail cache (`no-store`) and returns only
active approved Public projections. Reads on navigation to a new route,
selection/locale/country changes, visible-window returns and Check latest
revalidate the list. Search/sort changes do not clear or own comparison data.

404/inactive products retain a removable identity row with no financial facts.
Network/timeouts/other errors are retriable and never imply product withdrawal.
Different successful snapshot IDs fail closed; no composite snapshot is shown.
Aborted or stale requests cannot restore removed IDs or overwrite another
country. Saved term fingerprints exclude UI translations, product verification
and snapshot dates; a changed fingerprint labels Conditions changed alongside
current approved facts. This is a local comparison to saved terms, not a public
change history or assertion of when a bank changed its offer.

All products retain type, currency and verification context. Mixed type/currency
lists show only individual facts, suppress misleading difference highlights and
state that combined arithmetic is unavailable. Unconfirmed/mismatched deposit
basis, term or redemption gets a short separate boundary. This slice adds no
calculator; existing calculators and FR-PUB-021 gates remain authoritative.

## Verification and operations

Unit tests cover URL limits/privacy, local-data validation, fingerprints,
country/identity boundaries, inactive/404 versus failures, snapshot changes and
comparison eligibility. Browser QA covers navigation, saving/reopening/deletion,
requests in flight, locale/country isolation, unavailable states and exact
390/768/1440 layouts. Existing Home/finder/calculator/curated flows are regression
checks. No API service, DB, collection or deployment change is required.
FR-PUB-022's three fixed events remain unchanged; adding comparison usage events
requires a separate contract change. Browser QA blocks analytics and feedback.
