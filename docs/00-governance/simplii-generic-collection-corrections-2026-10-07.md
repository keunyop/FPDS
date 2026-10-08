# Simplii shared collection correction and direct publication - 2026-10-07

## Scope and diagnosis

The Product Owner requested current direct official collection without the FPDS
Admin collection API, generic fixes and automatic publication. The six latest
Runs started 2026-10-07 23:24:34 UTC, used process v6/parser v15, and completed
with 17 successful sources, seven candidates, one USD Savings approval and six
automatic exclusions. There was no stage failure or manual review queue.

Preserved original selected snapshot/parse joins, raw checksums and artifacts
reproduced the losses. The capture succeeded; shared code failed to preserve
some literal native facts through discovery, parsing, extraction and normalization:

| Boundary | Demonstrated defect | Shared correction |
| --- | --- | --- |
| Companion discovery | Generic Rates and fees navigation overrode product-family mismatch and selected a Visa schedule for non-card scopes | Keep current-rate hubs/own-family paths; veto unrelated family/network labels and preserve explicit shared lending schedules |
| Owned account facts | Unlimited debit purchases, bill payments and withdrawals appeared as H3 rather than P/LI | Retain owned heading assertions and recognize the complete ordinary three-part list; reject partial/channel/conditional/recommendation claims |
| Annual fee | Primary/additional-card count sat between Annual fee and $0; up to 3 cards was mistaken for a waiver condition | Preserve exact cardholder scope while still rejecting actual eligibility, balance and duration conditions |
| PDF rate record | Wrapped Annual / Interest / Rates column and card name did not fit previous layouts | Keep a literal single named purchase/cash annual row plus every default consequence and the payment definition |
| Final normalization | Native rate context was dropped as a non-rate field; summary could lose default notes | Recognize the exact native proof through the shared verifier and require complete excerpt in both evidence and summary, with final product ownership |
| Display-fee lineage | Final readback found an equal $0 display alias still pointed to a previous heuristic source | After final acceptance copy the exact verified monthly-fee mapping and rebuild persisted alias links, across account types |
| Savings native row | Current owned Annual rate / 2.80% single-row table was not grounded | Retain exact local ownership/annual units/disclosure and same-record daily calculation and monthly payment facts |

No bank name, rate or financial value is hardcoded into production acceptance.
New parser v16/process v7 and coordinated shared instructions invalidate existing
code-version cache fingerprints. Financial essentials, source provenance,
country isolation, security, privacy and bounded research remain unchanged.

## Current evidence and acceptance

Eleven distinct original official URLs and five observed essential-evidence leads
were captured once without paid providers or Admin API calls. Raw bytes and
capture timestamps/checksums are retained privately. Original saved sources
were inspected before direct current acquisition; historical facts were not
restored to fill Public. Observed links, not synthesized URLs, supplied leads.

| Current candidate | Automatic result | Current proof or missing essentials |
| --- | --- | --- |
| No Fee Chequing Account | Pass | $0 monthly fee; unlimited debit purchases, bill payments and withdrawals |
| Cash Back Visa Card | Pass | $0 annual fee; 21.99% ordinary purchase AIR and 22.99% cash AIR; full default/payment conditions retained |
| USD Savings Account | Pass | Explicit USD; current annual 2.80%; $0 monthly fee; daily-balance calculation and monthly payment |
| High Interest Savings Account | Exclude | Current regular rate still has unresolved dynamic placeholders; discontinued-account 0.05% cannot be substituted |
| GICs | Exclude | Unresolved dynamic annual/APY cells and no publishable full rate/term/access/consequence variant |
| Personal Line of Credit | Exclude | Prime plus an undisclosed customer-specific percentage; security not proven |
| Personal Loan | Exclude | Customer-specific undisclosed rate and insufficient term proof |

The current USD table is literal evidence despite a separate unresolved hero
widget. Optional unknown facts are omitted; this does not weaken required facts.

## Verification and publication

Exact official HTML/PDF bytes are regression fixtures under
worker/pipeline/tests/fixtures/native-disclosure-parity. Before correction,
original Chequing/card regressions and the current USD regression failed.
After correction ordinary artifact serialization, source-origin lookup,
normalization and automatic validation pass. Other bank names and rate values
exercise the same shapes. Negative boundaries cover wrong products/countries,
recommendations, missing units, partial transaction lists, conditional fees,
incomplete/default/payment clauses, unresolved references and retired products.

The first automatic publication exposed a further lineage error during independent
readback: an equal $0 derived display fee retained a different heuristic chunk.
The saved-input regression failed before correction and passes afterward. This
triggered one bounded corrective automatic run using identical current captures;
no new acquisition/provider call or manual canonical edit was used. The first
operation, its approved financial history and immutable parse/raw objects are
preserved. Corrective publication and independent readback pass:

- Final cohort: six completed scopes, seven candidates, three automatic approvals,
  four automatic exclusions and zero manual reviews, failures or partial Runs.
- Three distinct Public products, including two newly active products and the
  freshly verified existing USD Savings product. CA Public 104 -> 106; US remains
  five. The corrective run keeps those same three product IDs and creates three
  ordinary versions; both operation histories remain intact (six versions total).
- Ordinary persisted-origin validation, fee-mapping/link assertions and promotion
  rollback rehearsals pass. Original six Runs/seven candidates/17 source items,
  original document/snapshot/financial histories and unrelated canonical/Public
  records remain unchanged; previous approved versions are normally superseded.
- Seventeen current field-evidence checks pass, including source ownership,
  bank/country, URL, selected snapshot/parse/chunk, exact character range, typed
  value and complete financial context. Private evidence is absent from Public.
- Real Public list/detail APIs and all three live detail pages return approved
  facts; the card's complete missed-payment/payment-definition summary is visible.
  Public comparison eligibility continues to use its existing conservative
  rate/currency boundaries; an approved fact is not a ranking override.
- Final native regressions: 14 pass. Earlier final-shape focused set: 67 pass;
  updated normalization service/persistence assertions: two pass. Independent
  full API: 641 pass. Full final Worker: 858 run, 856 pass, two pre-existing
  immutable-source hash tests fail (National/Oaken fixture groups). All 23
  underlying discrepancies have current bytes identical to committed HEAD and
  clean file status; hashes/fixtures were not rewritten to conceal this limit.
- Foundation baseline, changed-document references, JSON/UTF-8/final newline,
  final goal/diff review and git diff --check pass. Zero provider or Admin
  collection API calls; no new source fetch in the bounded corrective run.

Published details:

- [No Fee Chequing Account](https://www.switchabank.com/products/prod_gVy9bcz1ML5f7cA4)
- [Cash Back Visa Card](https://www.switchabank.com/products/prod_X6l2-TncRr7TyCQ4)
- [USD Savings Account](https://www.switchabank.com/products/prod_lj2TT4yy7wCJ52pd)


## Deployment boundary

Live health reports process `2026-10-07-owned-price-rate-proof-v6`; the generic
API/Worker corrections are local process v7. Direct publication uses the corrected
local ordinary services and existing live automatic promotion/Public projection.
No runtime deployment/restart was performed. Future unattended Admin collection
requires deploying the API and Worker corrections through the normal release.
Private operation receipts/before-images are under
`tmp/simplii-improvement-20261007` and `tmp/simplii-improvement-20261007-v2`
and the existing private operation object prefix;
none are part of Public responses. This is a bounded one-off operation, not a
permanent recovery feature or scheduler.
