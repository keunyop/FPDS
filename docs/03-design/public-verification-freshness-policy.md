# Public product verification freshness

Date: 2026-09-21
Status: Implemented and locally verified; no deployment

## Meaning and boundaries

Snapshot generation (`freshness.refreshed_at`) is the assembly time of approved
Public records. It is not an observation or verification of current bank facts.
`last_verified_at` is the existing approved product verification record; it is
not a claim that every bank term remains unchanged today. Aggregate rebuilding
copies this date and cannot advance it. Missing, malformed or future dates are
unknown, and cannot fall back to snapshot time or `last_changed_at`.

The read-time product `verification` object includes `status`, `last_verified_at`,
`review_due_at`, `expires_at`, review/expiry days and `evaluated_at`. Comparison
arithmetic, product availability and canonical state remain unchanged. Expiry
means the verification window has ended, not that the bank withdrew its product.

States are `within_window`, `review_due`, `expired`, and `unknown`. Due/expiry
boundaries are inclusive, computed as UTC elapsed days. Unknown types have no
invented policy and fail closed. Only the operating policy registry in
`api/service/api_service/public_verification.py` defines production intervals.
No automatic collection, automatic withdrawal, migration or background task is
introduced; D-069 remains authoritative.

## Separate API signals

- `freshness.snapshot_status`: completed, stale (flag/later failed attempt), or
  unavailable. A completed snapshot receives neutral presentation, not a green
  current-bank-facts check.
- `freshness.verification`: counts over the complete filtered result before
  pagination, or the one product on detail. Dashboard counts follow its filters.
- Legacy `freshness.status` remains fresh/stale/unavailable, but fresh now requires
  known, within-window products and successful snapshot serving. Empty or unknown
  verification cannot assert freshness. This is an intentional semantic correction.
- Product records carry their own verification metadata. Public caches retain
  their existing bounded TTL; the UI also checks the returned deadlines when
  rendering. Old cached contracts show unknown verification until refreshed.
- No internal evidence, operator notes or source excerpts are added to Public.

## Operator overdue list and manual review

From `api/service`, an authorized operator with existing database access runs:

```powershell
.venv/Scripts/python.exe -m api_service.public_verification_report --env-file ../../.env.dev --country CA
.venv/Scripts/python.exe -m api_service.public_verification_report --env-file ../../.env.dev --country US
```

The report runs in a repeatable-read, read-only transaction. It reads only the
latest successful active Public projection for the explicit country, emits JSON
and does not modify a file or database, schedule collection, approve or publish.
An unavailable snapshot is explicit rather than a false zero-overdue success.
Rows contain public identity, bank/type, official product link, recorded check,
review/expiry deadlines and status. Sort order is expired, unknown, then due;
within each status the earliest due date and stable ID break ties.

At the start of each operating day, review expired/unknown items and upcoming
manual work. Once per week, reconcile the complete country/type list and failed
or partial collection runs. This is an operator checklist, not an execution timer.
Use the existing authenticated Admin Banks collection/retry and Review workflow.
Record corrections through normal evidence-backed approval. Confirm the product
check date in the new published projection after approval. Regenerating an
aggregate alone does not complete product re-verification.

Initial operating defaults selected within the requested warning/reporting slice:

| Product type (CA/US) | Recheck due | Verification expires |
|---|---:|---:|
| Savings, GIC/CD, mortgage, personal loan, line of credit | 7 elapsed days | 30 elapsed days |
| Chequing/Checking, credit card | 30 elapsed days | 90 elapsed days |

These are conservative initial review windows, not bank guarantees or a claim
that rates cannot change sooner. They are reversible policy constants. The
Product Owner may adjust them; the optional preference question is not treated
as explicit approval. Automatic collection, availability changes and deployment
remain excluded from this request. No collection or live-data action is
authorized by this doc.

## Release and recovery

Deploy API before Public through the separately authorized release workflow.
Wait for existing API/page caches to expire before checking the deployed result.
Old Public versions see conservative legacy stale status. New Public versions
reading old APIs show unknown product verification and neutral snapshot success.
No database rollback is needed for this read-only interpretation/presentation
change. Reverting code restores the previous (misleading) freshness semantics;
prefer correcting a confirmed policy or display defect.

## Verification record — 2026-09-21

- Complete API suite: 490 tests passed, including exact inclusive boundaries,
  all seven governed types, malformed/missing/future/overflow dates, no snapshot,
  unknown types, later/earlier refresh failures, regeneration without resetting
  product age, country-scoped overdue ordering, privacy, pre-pagination counts
  and one-product detail scope.
- Public: 16 unit tests, lint, typecheck and production build passed. Existing
  rate semantics, bank logos and canonical URL tests remain passing.
- Existing worker aggregate-refresh suite: 7 tests passed; worker production
  code and snapshot persistence are unchanged.
- Chromium: 54 CA/US x EN/KO/JA x 390/768/1440px catalog/Home/detail checks;
  comparison selection, 3 localized Methodology cases, 4 verification-state
  finder fixtures with annual-fee improvement, error/retry and empty finder,
  4 card/loan Grid/List cases, empty catalog and loading-to-ready. Total 70
  cases passed; no document overflow or JavaScript exception observed. Test
  analytics/feedback writes were blocked. Local scripts/screenshots are under
  ignored `tmp/freshness-verification/`.
- Initial browser harness runs hit a network-idle timeout, stale pre-policy
  local cache, incorrect role selectors and a mock-response/debounce race.
  Final checks used rendered content, isolated API cache key and settled-search
  selectors; the affected checks passed. These were not production fixes.
- Read-only current-projection report at 2026-09-21T17:50Z: CA 165 products
  (45 within-window, 76 recheck due, 44 expired); US 51 (21, 24, 6). Unknown=0
  in both. This verifies classification of stored dates, not today's bank facts.
- Repository doctor, foundation baseline validation and git diff --check passed.

No database/canonical mutation, collection, automatic scheduler, deployment or
bank-fact re-verification was performed. The report identifies manual work; it
cannot establish that old rates remain current. Production needs a separately
authorized API/Public release followed by verification after cache expiry.
