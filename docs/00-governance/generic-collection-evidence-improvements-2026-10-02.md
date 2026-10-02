# Generic collection source and evidence improvements ? 2026-10-02

## Authorized outcome

The Product Owner requested implementing the prioritized [Alterna/B2B audit](alterna-b2b-collection-audit-2026-10-02.md) improvements generically. The shared discovery, preparation, parsing, grounding and normalization paths now correct demonstrated defects without a bank-name/domain exception, relaxed financial essentials, manual product review or optional-completeness retry.

This is a runtime implementation and offline verification slice. No deployment, new collection-model call, registry/canonical mutation, publication or Public rebuild was performed. Earlier live audit results remain historical observations; these changes do not make the eighteen old candidates newly publishable.

## Changes and evidence

| Demonstrated problem | Shared change | Preserved boundary |
| --- | --- | --- |
| New checking opening ended, yet a candidate was grounded | Product/type-scoped current explicit availability notices checked in discovery, preparation and extraction; grounding skipped for an unavailable source | Other types and named sibling variants, negated/uncertain statements, future or unparsable effective dates do not establish closure; high model score/seed cannot override |
| Mortgage support/portability/renewal pages treated as products | Clear service routes/identities excluded before product grounding | Ordinary fixed/variable mortgage detail remains eligible; support text cannot define an offer |
| `/pdf?doc=...` and `/pdf?form=...` lose document identity or are classified as HTML | Bounded document query keys retained on disclosure paths; extensionless `/pdf` classified; actual PDF responses on HTML hints accepted by preflight only with PDF magic bytes | Existing safe-fetch/domain/redirect/byte limits and declared-PDF byte validation remain; unrelated query tracking still removed |
| Old PDF/HTML mismatch stays held after fixing dispatch | Preparation signature v2 and precise repairable HTML/application-PDF mismatch return to normal bounded probe | Non-PDF, allowlist and challenge failures stay blocked; no paid retry loop or permanent recovery feature |
| GIC aliases without H1 produce duplicate candidates | Content fingerprint plus proven identity, equal bank/country/type/language, equivalent locale/www path and identical query deduplicate missing-H1 aliases | Different content, market, domain or document query stays separate; existing H1-based identity dedup also gains country/language isolation |
| Linked HELOC pricing lies on a shared mortgage-rate page | Exact-detail companion planner accepts directly linked bounded shared lending pricing schedules as evidence-only | Unrelated brochures remain excluded; no rate page becomes a standalone product; per-detail/batch caps remain |
| Captured official companion never reaches the detail grounding call | Captured extraction-batch companions matched by exact parent or named identity with bank/country/language/official-domain/document/snapshot checks | Detail heuristics remain detail-only; companion facts use their real chunk/document/snapshot and actually consulted exact official URL; normalization resolves current-run origins from DB |
| Account row and annual footnote separated; term schedule conditions split | Parser v5 emits original product row/column-header/full scoped notes evidence, or one full term schedule | Full original sections retained; multiple pricing tables need explicit footnote links; no invented labels/units, row shifts, truncated notes or inferred relationship |
| Explicit annualization and maturity-only wording rejected | Shared validator recognizes `Interest rate is annualized` and complete explicit maturity-only access sentences; shared prompts match | Bare percentages/annual fees remain insufficient for annual basis; exceptions, contradictory early permission, conditional scalar rates and invented days remain excluded |
| Grounded Short-Term identity changed to Short Term | Any officially grounded match/corrected identity survives later discovery formatting and dynamic normalization | Grounding and exact final receipts still prove identity; ungrounded titles remain tentative |
| Deposit payment/calculation omitted because overdraft legal clause shares the chunk | Descriptive interest facts checked against complete quoted sentence and governing heading; numeric rates retain full-context screening | Original full chunk preserved; borrowing, companion headings and ambiguous repeated quotations fail closed |

Parser row structures are copied from captured HTML: existing headers, original cells and actual notes. A single pricing table can use document-wide Legal/Rate Notes; multiple tables require explicit fragment links. No paragraph is fabricated to fill a financial field. Atomic evidence is capped at 6,400 characters, with at most 24 model chunks and the existing 43,200 excerpt-character ceiling; oversized structures remain omitted. There is still only the existing bounded official grounding call per eligible detail, with no optional-only searches or retries. The prompt distinguishes effective/as-of dates from capture verification without treating old wording as proof of either current validity or expiry.

## Regression evidence and verification

Failures were reproduced before extending patterns. New positive/boundary/failure regressions cover CA/US and alternate bank identities, source URL mismatches, wrong bank/country/language/document/snapshot, sibling products, future closure dates, malformed formats, document query identities, alias content equality, service pages, split structural rate evidence, interest/overdraft headings, scalar-versus-qualified schedules and total grounding input bounds.

Source-backed fixtures preserve the retained official Alterna table and complete legal notes, term schedule and compound deposit/overdraft chunk. Tests use controlled provider responses; they are evidence-processing verification, not fresh official grounding or a new publication receipt for the live products. A real normalization/accuracy service integration retains the saved Savings row's 1.05% and an independent US APY row with actual companion source origins. The actual promotional term schedule retains all five rows, investment cap, payout/promotion and maturity-only wording; it cannot be coerced to a standard scalar or 365 days. Current source-origin gate regressions remain intact.

Final checks: Worker 659 tests and API 550 tests pass; repository doctor, fixture parsing, report/document links, goal review and `git diff --check` pass. Logs are private ignored `tmp/generic-collection-*-tests.log`. No UI/schema change; no frontend build or live paid collection was needed.

## Apply and remaining limits

Deploy the updated API/collection runtime together. Preparation v2 invalidates older preparation signatures; parser v5 prevents reuse of v4 parsed artifacts on future normal capture/parse. Then an operator-triggered bounded normal collection can establish fresh grounded candidates and automatic Public results. Deployment and those stateful runs were not performed in this slice.

Missing official numeric loan pricing, ambiguous multi-table note relationships, unsupported PDF parse content, access exceptions or a provider's unverified field remain automatic omissions/exclusions. These fixes address proven cross-bank patterns and prevent several false candidates; they do not promise all bank products or override evidence to increase coverage. B2B's explicitly closed Chequing should remain unavailable. Checking deposit interest remains optional and missing optional facts do not penalize ranking/publication.
