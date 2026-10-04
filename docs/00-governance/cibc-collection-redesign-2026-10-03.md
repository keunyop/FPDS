# CIBC official supplementation and shared collection redesign - 2026-10-03

Status: shared implementation, same-input parity and CIBC data operation complete.
Fourteen additional products are published; all fifteen CIBC API/site details
are verified at 19:30 Vancouver on 2026-10-03. Serving-runtime rollout remains
separate and has not been performed.

The Product Owner requests current official supplementation of the latest CIBC
collection, publication when financial essentials are proven, and a fresh review
of Admin collection independent of its previous implementation rules. This
supersedes preservation of the old collection architecture. Financial accuracy,
security, supported countries/types, private evidence and automatic exclusion of
incomplete products remain requirements. No human product-review queue is added.

## Diagnosis from current evidence

The pinned batch is `collection_84wInpBJx7XB33TC`, with seven completed CIBC CA
Runs (`run_20261003_214729_cibc_...`) and 44 original candidates. Originally one
Smart Account passed; the other 43 were excluded. The before-image retains all
original candidates, model executions, snapshots, parsed documents and chunks.
This is not evidence that the bank omitted 43 products' financial facts.

Direct capture found current facts that the ordinary pipeline was losing:

- Current card disclosures were displaced by insurance/benefit links. The
  main-content PDF detector tested the combined URL/label against a URL-end
  pattern, so the annual-rate PDF disappeared behind the 256-link cap. Pricing
  also needs priority over general agreement/privacy links in the two-link cap. A shared
  disclosure selected for several products retained only its first parent.
- Mixed marketing sections confused ordinary annual fees with separate welcome
  offers and additional-cardholder fees. Some product names came from navigation.
- The official rates-and-fees URL serves PDF despite its `.html` suffix. Flattened
  PDF text interleaved purchase, cash and missed-payment rate columns.
- Official rate HTML contained unresolved `RDS%...%` templates. The existing
  rendering rule depended on a bank-specific domain configuration.
- Dynamic normalization could rewrite a fact already grounded in captured
  official evidence. Improving extraction alone could therefore lose the result.

No paid model recollection was required to prove these failures. Current original
44 captures were downloaded from private storage and checksum-verified; five
essential official companions were captured. Three unresolved rate pages each
received one bounded render. Original direct bytes and render receipts remain
private. Rates rendered successfully; product-specific term/access/security
binding is still required before those numbers can establish publication.

## Shared evidence-to-approval process

Ordinary Admin and the bounded direct supplement use the same production
ExtractionService, native parser/chunk contract, NormalizationService, database
origin resolution, ValidationRoutingService and automatic canonical promotion.
The direct operation supplies captured bytes and actual product relationships;
it does not author financial values or bypass the normal accuracy gate.

1. Discover real product identities and their essential price/fee/disclosure
   links. Preserve every selected parent of a common companion within existing
   limits; screen unrelated insurance/benefit/checklist documents.
2. Safe-fetch official evidence and render unresolved financial placeholders once
   within the validated domain allowlist. Preserve the successful raw capture.
3. Parser v7 retains complete labelled financial records and explicit purchase
   columns, including full product exceptions and referenced purchase notes.
   Missing notes, ambiguous columns and attached conditions fail closed.
4. Prove exact product-owned facts before the existing model pass. Give those
   values and real quotes to the same grounding request for unresolved facts.
   Reapply captured proof after the pass; contradicting captured values are
   omitted rather than selecting a model or heuristic winner.
5. Preserve grounded native facts through dynamic normalization. Every value
   still needs current-run database-resolved source/document/snapshot/chunk
   ownership, official exact quotation, financial semantics and native type.
6. Automatically accept and promote a complete product, or exclude it. Refresh
   approved Public projections normally; unknown optional facts remain omitted.

Discovery scores and AI confidence do not establish fact evidence. Introductory
fees, neighboring product prices, cash/default interest, channel-only allowances,
wrong-bank/country/language/parse/snapshot origins and uncertain optional facts
remain rejected. Checking excess cost, GIC withdrawal consequences and LOC
security are still conditional essentials. Public does not expose raw traces.

Actual captured detail-link replay now selects the official common annual-rate
PDF for twelve card parents and the own pricing PDF for Costco. The alias used
for direct capture redirects to the exact common PDF target in its retained
receipt. Costco also has an explicit named purchase row in that common PDF,
so ordinary same-bank named evidence binding proves its 21.75% rate even without
a shared-parent relationship. No false Costco shared-parent link is required.

Key implementation: `source_catalog.py` essential companion selection and
multi-parent retention; discovery `discovery.py` main-content disclosure retention and `fetch.py` bounded placeholder rendering;
parser/chunker v7 financial atoms; extraction common captured proof and prompt
planning; normalization preservation; shared financial quote gate/instructions.
No frontend, schema migration or permanent recovery feature was introduced.

## Eligible same-input replay

Provider-disabled ordinary extraction, normalization and validation yields 14
new automatic passes from 44 targets: Everyday Chequing plus all 13 captured
credit-card details. The existing approved Smart Account remains preserved; its
original acceptance is not replaced by the stricter no-model replay result.

Everyday Chequing: CAD 4 monthly fee, 18 included transactions per month and CAD
1.25 per additional transaction. These are ordinary pricing facts, with separate
transfer/ATM costs kept in their own context. No zero-balance or free-transaction
value is inferred from a marketing benefit.

Card fees are CAD per year; purchase rates are percentage points per annum.
The complete official PDF excludes Select and Costco products from the generic
21.99% row. Costco binds its explicit 21.75% purchase row. Cash/default columns
and welcome discounts do not replace ordinary comparison rates.

| Product | Annual fee CAD | Annual purchase rate |
|---|---:|---:|
| CIBC Adapta™ Mastercard® | 0 | 21.99% |
| CIBC Adapta™ Mastercard® for Students | 0 | 21.99% |
| CIBC Aeroplan® Visa Infinite Privilege* Card | 599 | 21.99% |
| CIBC Aeroplan® Visa Infinite* Card | 139 | 21.99% |
| CIBC Aeroplan® Visa* Card | 0 | 21.99% |
| CIBC Aeroplan® Visa* Card for Students | 0 | 21.99% |
| CIBC Aventura ® Gold Visa * Card | 139 | 21.99% |
| CIBC Aventura ® Visa* Card | 0 | 21.99% |
| CIBC Aventura® Visa Infinite Privilege* Card | 499 | 21.99% |
| CIBC Aventura® Visa Infinite* Card | 139 | 21.99% |
| CIBC Classic Visa* Card for Students | 0 | 21.99% |
| CIBC Costco Mastercard | 0 | 21.75% |
| CIBC Dividend® Visa* Card for Students | 0 | 21.99% |

## Applied data outcome and readback

The reserved one-off operation `cibc-captured-supplement-20261003` is applied.
Normal automatic promotion approves fourteen supplemental candidates: one
Everyday Chequing and thirteen credit cards. The previous Smart Account remains
active, making fifteen current CIBC Public products. Normal CA refresh
`agg__iUq_IspcCsOA6is` completes both queued requests; none remain pending.

Independent anonymous readback confirms CA 50 / US 5, total 55. All fifteen
CIBC API details and real SwitchaBank site detail URLs return current products.
No canonical-ID/detail mismatch was found. Public privacy checks expose no raw
evidence, internal receipt, storage key or field-trace metadata.

All 44 original candidates, 188 original model executions and original snapshots,
parsed documents/chunks are byte-equivalent to the private before-image. All
383 other-bank canonical rows and non-CIBC Public IDs remain unchanged; US IDs
remain unchanged. Original Run started/completed timestamps are preserved.
Forty-nine current captures are retained privately. Forty-three current field
citations for the fourteen new public products resolve to exact native spans,
correct document/snapshot/official URL and unchanged typed values. All fifteen
active CIBC policy receipts are valid.

Run history now contains 88 candidates: original 44 plus supplemental 44, with
15 approved and 73 excluded/rejected historical outcomes, zero new product-review
tasks, seven completed Runs and zero partial completions. This history count is
not the number of distinct verified products. Provider/Admin API calls: zero.

The first persistence attempt stopped at a unique source-URL constraint before
any new candidate/canonical approval. Two complete captured sources were already
retained. Reconciliation reused existing source-document identities, verified
those two committed sources and all 44 unchanged original candidates, then
continued only missing native evidence. No recollection or extra provider calls
were used. The new companion metadata was reconciled against twelve actual
shared PDF links; Costco retains named-row applicability without an invented
shared-parent relationship. Its previous new-operation metadata is preserved
in the private reconciliation before-image. The reservation remains; repeated whole-operation execution is refused.

Remaining exclusions are not a bank-nondisclosure claim. This replay still lacks
product-bound standard annual rates/term schedules and withdrawal consequences
for GIC, rate/security proof for LOC, rate/term proof for loans/mortgages and
standard-rate proof for Savings. Conditional checking/offer pages also remain
excluded. Newly rendered rate evidence is retained, but does not permit guessing
these relationships or relaxing essentials. The bounded supplement is not a
claim of exhaustive CIBC coverage or a new recurring recovery mechanism.

## Verification and rollout

- Worker full suite: 698 tests pass. API full suite: 578 tests pass.
- New parity tests cover current official DOM/PDF, conditions before/after fees,
  cash/default separation, missing/conditional referenced notes, conflicts even
  against previous model facts, identity versus navigation, parent ownership,
  exact-product rows, bank/market/language/snapshot boundaries and bounded renders.
- An ordinary ExtractionService test proves that native values enter the existing
  model pass and survive a model response changing monthly fee 4 to 0. A real
  normalization test keeps grounded fee 139 despite a proposed 0, while missing
  required proof still excludes the candidate.
- Final provider-disabled same-capture production replay independently confirms
  the identical fourteen approval IDs with twelve true shared parents and named
  Costco evidence. Private DB/API/site verification passes current native
  citations, immutable history, other-bank/US preservation and Public privacy.
- Repository doctor and narrow foundation contract validation pass. Final changed
  document/reference/text checks and working-tree/staged git diff --check pass.
  No unaffected frontend build or dependency install was run.

No serving runtime deployment is claimed. To apply future Admin discovery and
collection changes, deploy the API/source-catalog and Worker package together.
Parser v7 and changed extraction code invalidate relevant same-input reuse keys;
no existing candidates should be reapproved merely by switching code versions.
A fresh paid Admin discovery run was not used as a parity benchmark. The proven
comparison is the same captured input through ordinary production services.

## Current official sources

- [Everyday Chequing fees and details](https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/everyday-chequing-account/fees-and-details.html)
- [Current annual credit-card interest rates and fees PDF](https://www.cibc.com/ca/visa/article-tools/credit-card-rates-n-fees.html)
- [Bank account rates](https://www.cibc.com/en/interest-rates/personal-bank-account-rates.html)
- [GIC rates](https://www.cibc.com/en/interest-rates/gic-rates.html)
- [Mortgage rates](https://www.cibc.com/en/interest-rates/mortgage-rates.html)

Original per-product official detail URLs, capture checksums, full statements,
field quotations, DB before-images and operation receipts remain in private
storage/ignored `tmp/cibc-redesign`; no secret or internal evidence link is exposed.
