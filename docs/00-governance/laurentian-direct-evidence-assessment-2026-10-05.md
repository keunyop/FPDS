# Laurentian direct evidence assessment - 2026-10-05

Status: completed read-only feasibility assessment; no demonstrated new automatic acceptance.

## Outcome and scope

Direct inspection finds credible additional acceptance opportunities for three
of the latest eight targets: fixed-rate GIC, fixed-rate mortgage and variable-rate
mortgage. This is evidence availability, not three approved products or a claim
that rerunning the unchanged runtime will succeed. Existing gates still reject
important native table representations. HISA has useful evidence but unresolved
comparison/fee conditions. Three lines of credit and the indexed GIC are not
established acceptance opportunities from this bounded assessment.

The assessment did not use FPDS Admin API, call paid models, create collection
Runs, change policies/runtime, write canonical data or publish products. Read-only
saved inputs were reused, with bounded official source inspection. All earlier
goal ownership and collection/security boundaries remain.

## Baseline and verification

Latest saved batch: `collection_tP_RPEAAkVrNKVOL`, October 5, 2026, four Runs;
15:41:03-16:18:41 America/Vancouver (22:41:03-23:18:41 UTC).
The new `2026-10-05-evidence-research-v1` process was present. The batch produced
eight excluded candidates, zero approved candidates, zero review tasks and zero
new product versions. Forty-nine successful source-processing operations do not
mean forty-nine valid financial pages or verified products.

Retained private assessment artifacts are under
`tmp/laurentian-direct-assessment-20261005/` (ignored; not a public evidence path):

- `original-metadata.json`: latest target/source/field-receipt readback, no DB writes.
- `saved-capture-receipts.json`: eleven existing same-day snapshots, raw bytes
  checked against stored SHA-256, including all eight target details, proper
  lending/mortgage rates and one malformed lending URL.
- `direct-capture-receipts.json`: two bounded new official URL captures, one valid
  account-rate page and one HTML soft 404 returned by a PDF route.
- `financial-gate-probes.json`: nine diagnostic function evaluations and eight
  saved-candidate comparison replays; no fabricated grounding metadata.

Existing receipt comparison failures replay unchanged for all eight candidates.
These diagnostic probes do not execute the full extraction, provenance,
normalization, promotion or public projection path and cannot prove acceptance.
Current financial observations below come from October 5 captures; stale search
snippets were not used as current rates. Official linked PDF references supplement
fee/security inspection, with source-binding and freshness limits preserved.

## Target assessment

| Latest target | Direct evidence and constraints | Assessment |
|---|---|---|
| Fixed-rate GIC | Named detail, annual percentage table by term, terms from 90 days to 10 years, minimum investment CAD 500, explicit non-redeemable access; interest payment/compounding and offer eligibility stated | Strong additional opportunity; native table proof and access must survive grounding |
| Fixed-rate mortgage | Named detail identifies fixed rate, open/closed terms; proper companion rate page identifies term, property-unit scope and open/closed/convertible rates | Strong additional opportunity; preserve separate regular/promotional/high-ratio APR scopes |
| Variable-rate mortgage | Named detail states variable rate and 3-/5-year closed terms; proper rate page provides nominal rates, prime spreads and conversion conditions | Strong opportunity, particularly the consistent 3-year row; 5-year legal spread conflicts with its displayed row |
| HISA | Annual rates by balance, daily minimum calculation, monthly payment, fee information and paper/electronic statement conditions | Conditional opportunity; current CA savings contract requires an ongoing scalar rate, and sources disagree at exactly CAD 100,000 |
| Personal line of credit | Named detail and variable reference-base language; proper lending page has reference base | No current product-scoped explicit security proof located; base is not the client's final rate |
| Student line of credit | Named detail, study/repayment conditions and variable reference-base language | No current product-scoped security proof located; an endorser requirement is not unsecured proof |
| Equity line of credit | Named detail, home-value language and companion minimum-rate condition | Home value/name alone cannot prove security; minimum rate is not a universal granted rate |
| Indexed GIC / SEO ActionGIC | Named H1 INDEXED GIC, current subscription dates and series-specific full-term return bounds, principal protection and non-redeemability | Identity/series/return-period handling required; cumulative indexed returns must not become annual interest |

### Fixed-rate GIC

The [official detail](https://www.laurentianbank.ca/en/personal/investments/gics/fixed-rate)
shows 1-year 3.50%, 2-year 3.80% and 5-year 4.10%, with other terms in an
annual-percentage table. These are term-specific offers, not one unconditional
product-wide maximum. The page explicitly states non-redeemability; no invented
withdrawal penalty is needed once the non-redeemable access flag is proven.
Shorter-than-two-year simple interest pays at maturity; longer terms offer annual
simple payments or annual compounding paid at maturity. Retain offer eligibility:
outside Quebec, people without a current Laurentian investment are ineligible for
the offer. This assessment does not decide separate issuer/account product identity.

The actual candidate lost its rate and access evidence despite their presence in
its retained detail. The existing `quote_supports_value` probe accepts the literal
non-redeemable statement but rejects the unchanged native term table. Its labels
repeat across responsive/desktop renderings, and percent units are in headers
rather than appended to every numeric cell. A structure-preserving proof adapter
is needed; rewriting a quote to append percent signs is not official evidence.

### Mortgages

The [proper mortgage rate page](https://www.laurentianbank.ca/en/personal/rates/mortgages)
contains posted closed fixed 1-year 5.640%, 2-year 5.940%, 3-year 6.090% and
5-year 6.290%, plus a separately labelled promotional 5-year 5.190%.
Open/convertible scopes differ. A separate 4.69% high-ratio APR example is subject
to new-loan, down-payment, insurance and example-loan conditions; it cannot prove
a universal regular nominal mortgage rate.

The [fixed detail](https://www.laurentianbank.ca/en/personal/mortgages/fixed-rate)
provides fixed/open/closed term facts, yet its candidate lost the term as well as
rate. The existing numeric rate-label detector returns false on the unchanged
fixed table section because cells are bare numbers under a percent header.

The [variable detail](https://www.laurentianbank.ca/en/personal/mortgages/variable-rate)
and companion rate table identify the 3-year row as prime +0.00%, currently
4.450%, and the 5-year row as prime -0.25%, currently 4.200%. The legal 5-year
note instead says minus 0.00%; do not silently correct it. The coherent 3-year
row is the stronger bounded opportunity. The scalar mortgage-rate proof probe
rejects the unchanged full variable section. A prime spread alone must never
replace a proven nominal rate, and illustrative APR assumptions are not a
substitute for current product-table evidence.

### HISA and remaining exclusions

The [HISA detail](https://www.laurentianbank.ca/en/personal/accounts/high-interest-savings)
provides 2.20% through CAD 100,000, 3.20% from CAD 100,000.01 through CAD
5,000,000 and 1.00% above that, with daily minimum calculation and monthly
payment. The newly captured [bank-account rates](https://www.laurentianbank.ca/en/personal/rates/bank-accounts)
instead place exactly CAD 100,000 in the 3.20% band. Retain the boundary conflict;
do not select a source interpretation silently. Neither 3.20% nor 2.20% is an
unconditional whole-account scalar. CA savings comparison does not currently
accept a tier summary in place of its required ongoing scalar rate.

The bank-linked [My Money Guide](https://assets.ctfassets.net/b5xlbty9p8dy/z6IJ5ALADBfrEBj00DrUe/8e819dbefaf9285e6163248ddb87425e/my-money-guide.pdf)
(effective March 12, 2026) distinguishes electronic statements without a
maintenance charge from paper statements charged monthly. The inspected detail
also distinguishes transaction charges. A free-management headline cannot erase
statement conditions. This guide requires correct column/footnote attribution;
no other account's fees were imported. Its student endorsement note supplies no
explicit unsecured status. The literal bank PDF route returned HTML soft 404;
the official asset was reachable through web inspection, without changing runtime
allowlists or claiming production acceptance of a new source origin.

The [personal](https://www.laurentianbank.ca/en/personal/lending/personal-line-of-credit),
[student](https://www.laurentianbank.ca/en/personal/lending/student-line-of-credit)
and [equity](https://www.laurentianbank.ca/en/personal/mortgages/equity-line-of-credit)
details contain no explicit security statement recognized by existing gates.
The shared lending base of 6.700% and equity minimum of 4.950% remain reference
or conditional rates, not invented universal final rates. An additional official
[home-purchase guide](https://assets.ctfassets.net/b5xlbty9p8dy/3c6CBkHApzuiI09rrh32LI/a7bc1fee78017881a78e32651eee7c03/my-home-my-mortgage.pdf)
was checked: the secured-mortgage sentence belongs to note 5 for another financing
scope, not the equity-line note 4. No fresh target binding was established, so it
was not borrowed to mark this equity product secured. Absence in this bounded
inspection is not a claim that the bank never discloses security.

The [indexed GIC detail](https://www.laurentianbank.ca/en/personal/investments/gics/indexed)
is open for subscription until October 7, with issuance October 13-15, 2026.
Its 2-/3-/5-year series list cumulative minimum/maximum returns (including a
5-year maximum of 60%), not annual rates. The pending-investment annual rate is
a different phase. Do not annualize the bounds, collapse series identity or
claim already-issued current terms.

## What explains the direct/Admin gap in this batch

The observed failures are not uniformly bank nondisclosure:

1. Invalid acquisition inputs were counted as processed successes. The retained
   `/en/personal/rates/en/personal/rates/lending` capture has a page-not-found
   title and approximately 99 characters of main content. Repeated path forms
   occur in multiple stored URLs. Their exact construction cause was not traced
   in this read-only slice; safe URL resolution and financial-content validation
   need reproduction before a repair is selected.
2. Valid financial evidence was not reliably retained as field proof. Proper
   GIC and mortgage details/rates were already captured, yet required rates,
   term or access disappeared during extraction/grounding. The failed native
   table probes identify an additional representation boundary; obtaining more
   of the same pages alone will not repair it.
3. Some product semantics do not fit the current comparison representation.
   HISA's conditional tiers cannot be forced into a universal scalar. Indexed
   returns, reference bases and minimum lending rates cannot become ordinary
   annual rates. These exclusions require honest typed modelling/evidence or
   must remain excluded.

The evidence supports prioritizing the GIC and two mortgage targets for a shared,
source-structure-preserving correction and identical-input full-path regression.
Do not lower essentials, copy direct conclusions into canonical data, infer
security, relax provenance or count page fetches as successful products. Actual
additional automatic acceptance remains unproven until the normal path and its
final financial/provenance gates pass and resulting publications are checked.

## Checks performed

Eleven stored raw snapshot hash checks; two bounded official captures with
content-type/body inspection; two official PDF inspections; nine existing
financial/security diagnostic probes; comparison replay of all eight saved
candidates. No application code was changed and no full application suite was
rerun for this documentation-only assessment. Final documentation/link and
`git diff --check` results are recorded in the journal.
