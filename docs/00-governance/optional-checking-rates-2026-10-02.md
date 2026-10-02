# Verified optional checking rates - 2026-10-02

Product Owner authorized a shared collection correction after observing missing
Alterna checking interest. Checking rates remain optional publication facts.
This slice changes code and documentation; it does not deploy, recollect,
call a provider, mutate canonical data or publish products.

## Reproduced causes

Read-only latest saved collection: `run_20261002_065609_alterna_chequing_collect_nCee4yEN`.
The checking candidate was approved without a rate. Its official detail capture
already contains `0.05%* Annual Interest Rate.`; the checking/savings rate page
was also collected in that run. No new source search is necessary to demonstrate
the omission.

1. The shared CA/US checking profile contains no deposit-interest fields. The
   old registered list also lacks them, so official grounding never requests
   that already available optional fact.
2. Retrieval/heuristic field selection uses older registry/default lists instead
   of the current profile. This can deprioritize current optional fields before
   the grounding pass, across every supported profile.
3. With the missing rate supplied as a controlled grounded response, the exact
   full saved chunk still rejects it: its separate CDIC `insured up to` clause
   is treated as a condition on the annual rate. This second failure was
   reproduced before extending the shared meaning rule.

## Shared correction

CA and US checking profiles now include optional standard/display deposit rates
and existing typed deposit qualifiers: rate summary, calculation/payment,
compounding/payout, tiers and promotion conditions. Retrieval merges current
profile fields with registered typed fields, matching grounding and normalization.
Explicit caller field overrides retain their existing bounded behavior.

The shared accuracy gate recognizes only a complete separate CDIC/FDIC insurance
line together with a standalone exact annual deposit-rate declaration. It ignores
only that insurance clause's `up to`; all original text, other conditions,
competing percentages, currency, annual basis and official quote/source checks
remain. It cannot excuse an actual rate ceiling, conditional eligibility,
introductory rate or a borrowing rate. The common collection instructions match.

Deposit-interest extraction also applies existing product-context checks to
rate and payout facts, including model output, and excludes overdraft context.
A companion savings account's payment information cannot become checking
information. This is shared code, with no Alterna-specific bank/URL/value branch.

Required comparison facts, receipt/profile version and Public presentation
contracts remain unchanged. Unknown optional rates are omitted without a
publication penalty, repair, review or additional provider call. Grounding
fingerprints already include profile, extraction, shared gate and prompt code,
so results computed under the old selection are not reused as identical inputs.
Unsupported/ambiguous table layouts still require exact product, unit and
condition proof; this correction does not convert a multi-product table into
an unconditional scalar or weaken any origin boundary.

## Verification and limit

Before changes, profile/retrieval/rate-preservation checks produced 18 failing
subcases. The full saved insurance context and two cross-market insurance cases
then failed before the meaning fix. Eleven new regression tests cover both
markets/all seven profiles, actual full Alterna text, another account's APY,
missing optional rates versus evidenced zero, explicit overrides, wrong units/currency, promotion and
balance conditions, companion accounts, overdrafts, nonnative values, invented
quotes and unconsulted URLs. Provider responses in these tests are controlled;
no new live model output is claimed.

An independent private saved-input replay (`tmp/optional-saved-replay.json`)
uses the real latest registry metadata and captured chunks through normal
retrieval/heuristic extraction. The old request lacks `standard_rate`; the new
request includes it and extracts `0.05` for standard/display rates from the
original chunk. Full original context now passes exact rate meaning. Heuristic
replay is diagnostic, not a publishable grounded fact or a new receipt.

Worker 643 and API 539 tests pass. Focused checking/extraction 180 tests pass;
new module 11 tests is included. Repository doctor, report links, fixture JSON
and git diff --check pass. Final goal/diff review confirms this slice acceptance.

Deploy the collection runtime/API package through the normal release flow to
apply the fix to future Admin collections. Existing Alterna canonical/Public
rate remains unchanged by this code-only operation. A future normal collection
must obtain its own official grounding and pass all current automatic gates.
