# TD Bank, National Association: direct collection and shared corrections

Date: 2026-10-10 (America/Vancouver). Scope: existing `.env.dev` PostgreSQL,
private evidence storage and US Public. No Admin collection API, paid/model
provider calls, manual product approval, migration or runtime deployment.

## Recent collection and first losses

The latest six per-type ordinary Runs started at 2026-10-10 05:09:30 UTC
(2026-10-09 22:09:30 PDT), using process v15. All completed, with 58 successful
Run/source joins and zero source failures. Their 17 candidates were rejected:
nine cards, three checking accounts, two savings accounts, one personal loan,
one mortgage and one HELOC. Successful source capture did not establish approval.
All 50 distinct selected original snapshots were downloaded and SHA256 checked.

The original card receipts lacked `purchase_interest_rate_summary`. The retained
PDFs already contained purchase APRs, while the common parser supported a
specific two-to-four-page Pricing Information Disclosure format. TD's six/eight-
page application terms had enumerated APR alternatives, introductory periods
and continuation-page variable-index/grace conditions; no complete native
record reached the ordinary same-product extraction and financial gates. This
was a representation/ownership gap, not inaccessible evidence or permission to
weaken required fields. Official-byte regression reproduced the loss before
extending acceptance.

A second shared loss affected amount-first account fees. The parser omitted
`$15 Monthly Maintenance Fee` and its linked complete waiver section. A repeated
account H2 was also mistaken for a sibling because the H1 appended marketing
copy after a colon. This is fixed at native-record preservation, while the
independent publication identity and financial gates remain unchanged.

## Generic correction and boundaries

- `worker/native_single_card_pdf.py`: complete named multi-page pricing requires
  repeated agreeing native card identity, all purchase APR alternatives and
  introductory terms, full financial table and complete continuation through
  variable calculation/margins, dated Prime Rate, eligibility, balance-transfer
  and promotional purchase-interest rules. Explicit administrative boundaries
  are mandatory. Later APR/interest-price/annual-fee restatements, empty/missing
  sections, competing identity, invalid percentages and oversized records exclude.
  Preserve original text; never convert alternatives to a range or scalar.
- Literal unconditional `Annual Fee None` maps to zero only in its independent
  native annual-fee record. First-year/conditional waivers remain conditional;
  they never become zero annual fees.
- `worker/native_owned_account_records.py` and extraction retain amount-first
  monthly account/maintenance fees and every resolved waiver note. Exact repeated
  account-name prefixes before an H1 colon preserve ownership without inventing
  a shorter publication identity. Both checking and savings use this path.
  Missing transaction essentials and unresolved/multiple prices remain excluded.
- Shared prompts, parser v26/process
  `2026-10-10-complete-named-pdf-pricing-v17`, the parser-version regression and
  the existing source-code cache fingerprint agree. No bank exception, review
  queue, budget increase, permanent recovery menu or scheduler was added.

`test_extended_card_terms.py` and compressed immutable official captures cover
three actual PDF disclosures, actual account fee/waiver markup, another issuer,
checking/savings, conditional fees, invalid/missing continuation, later financial
conditions, different identities and foreign-bank evidence. Existing automatic
extraction/normalization/validation accepts complete proofs and rejects foreign
origins. Unrelated existing source bytes and expected hashes were preserved.

## Current direct collection and exclusions

All 50 unique latest-scope official URLs were directly fetched successfully.
The current no-provider ordinary pipeline produced 17 candidates: three automatic
passes and fourteen exclusions. Fresh captured bytes, not the historical fixture
facts, supplied publication. Identical inputs and unchanged PDF parses were
reused; the final HTML account change reparsed affected HTML. No capture retry,
optional-only search, model/provider call or Admin collection API was used.

| Target | Final result and evidence boundary |
| --- | --- |
| TD Cash, TD Double Up, TD FlexPay | Complete current native identity, USD, annual fee and qualified purchase APR pass. |
| Five existing-customer benefits pages | No proven separate current product identity/pricing; excluded. |
| First Class card | Current rate evidence exists, but wrapped PDF naming/text and current detail identity do not meet the supported exact proof; excluded. This is not a claim that the issuer withholds APRs. |
| Two savings accounts | Current captured location-dependent rates do not prove owned numeric annual/APY essentials. |
| Three checking accounts | Marketing H1/price-waiver contexts and ordinary transaction costs remain insufficient. Fee/waiver text is now retained; retention alone is not approval. |
| Personal loan | Current full interest-rate interval/example exists, but supported exact product/annual-rate meaning is unproven. No example or lowest rate was substituted. |
| Mortgage and HELOC | Current complete annual rate/term/security proof is not established; HELOC rate slots remain empty. |

## Actual publication and verification

Operation `td-us-direct-20261010` created six scoped Runs, seventeen candidates,
three normal automatic approvals and fourteen exclusions; zero manual reviews.
Actual selected snapshot/parse DB joins reproduced the three passing candidates
before canonical mutation. Promotion was rehearsed in a real transaction and
rolled back; products, versions and refresh requests were confirmed restored.
Ordinary promotion then created three products and one US refresh request,
consumed by the ordinary Public aggregate runner.

Published and checked through anonymous API plus HTTP-200 rendered details:

- [TD Cash Credit Card](https://www.switchabank.com/products/prod_iDj3vyfm-Hmd75j9?country_code=US), [official current page](https://www.td.com/us/en/personal-banking/credit-cards/cash-card).
- [TD Double Up Credit Card](https://www.switchabank.com/products/prod_nDoIe4hhI7oMUwmw?country_code=US), [official current page](https://www.td.com/us/en/personal-banking/credit-cards/double-up).
- [TD FlexPay Credit Card](https://www.switchabank.com/products/prod_kNIeN3iTD1lEmfCc?country_code=US), [official current page](https://www.td.com/us/en/personal-banking/credit-cards/flex-pay).

US Public increased 68 -> 71; Canada remains 120. All three full qualified
purchase summaries (5,775/5,957/6,078 characters), numeric annual fees, exact
source meaning and acceptance receipts were verified. Actual private-storage
readback matched twenty raw/parsed pairs and all nine published field origins,
quote spans, bank/country and current Run selection. No private evidence is
exposed through the public API/site.

Original six Runs, seventeen candidates, fifty-eight Run/source joins,
eighty-six bank documents, 137 snapshots, 1,591 financial versions and all
479 pre-existing canonical products are unchanged. Concurrent unrelated TB
Runs were neither restarted nor modified. Private baselines, source receipts,
execution plan, stored-origin proof, rollback and Public readback are under
`tmp/td-us-20261010`, with operation baselines/results in existing private storage.

## Tests, limits and rollout

Final affected Worker: 78 pass. Independent API: 650 pass. Extended official/
cross-type regression: nine pass. Foundation baseline, UTF-8/syntax/JSON,
changed-document local references and `git diff --check` pass.

An earlier 89-test broader selection had one existing
`test_source_fixture_hashes_and_priority_count` failure. Every mismatched
legacy fixture was byte-identical to Git HEAD; neither those bytes nor expected
hashes changed. The other 88 passed. Initial wrong-directory API invocation
had import errors; the final README-style independent directory invocation
passed all 650. No UI layout changed, so responsive/build work is outside scope.

Serving health at pre-publication reports process v16; local v17 is not deployed.
Future Admin collection needs a coordinated API/Worker v17 release and a bounded
ordinary-run smoke covering complete disclosures, negative fee/origin cases and
Public privacy. Data publication above is complete independently of that release.
Rollback code if runtime smoke fails; no schema/config change is required.
