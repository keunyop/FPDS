# BNY and Capital One collection diagnosis and generic corrections - 2026-10-09

## Original results and scope

The latest scopes are US / BNY and US / CONA. The five Runs started at
2026-10-09 13:41:28 UTC (06:41 PDT), batch `collection_H37aCxM-BAFYg5Mr`,
with process `2026-10-08-accessible-qualified-source-proof-v10` / parser v19.
No FPDS Admin API was used for diagnosis, direct collection or publication.

| Bank | Type | Candidates | Successful / failed sources | Original approvals |
|---|---|---:|---:|---:|
| Capital One | Savings | 3 | 7 / 2 | 0 |
| Capital One | Personal loan | 1 | 3 / 0 | 0 |
| Capital One | Credit card | 20 | 24 / 0 | 9 |
| Capital One | Checking | 3 | 7 / 2 | 0 |
| BNY | Checking | 0 | 0 / 0 | 0 |

Capital One had 27 candidates, nine approvals and eighteen exclusions. BNY was
skipped before collection with `no_eligible_detail`: the discovered corporate,
private-banking and family-services pages did not establish a named comparable
checking product. Current official private-banking pages and the general legal
agreement did not establish the missing account prices/ordinary transaction
conditions. This does not claim BNY offers no accounts; it explains why these
verified inputs cannot support publication under the current contract.

Thirty-eight original selected snapshots were downloaded and SHA-256 checked.
A bounded current capture inspected 42 exact registry URLs: 38 succeeded and
four malformed nested disclosure paths returned 404. Original-byte replay of
the shared link extractor confirmed these `/site/bank/bank/disclosures/...`
paths are literal links in the official pages, rather than URL concatenation
introduced by FPDS. The already captured real disclosure pages were reused;
no speculative route rewrite was added. Captures and parsing were reused. No paid provider calls, manual review or permanent recovery feature was
introduced. The unrelated City National collection was left running.

## Demonstrated defects and generic corrections

1. **Literal prices and APR declarations disappeared before grounding.**
   Compact native heading blocks such as `No annual fee`, `$95 annual fee`,
   `Purchase rate` and `Low intro APR` were missed by flat exact-label matching.
   The parser now retains a bounded uniquely owned block, its literal product
   label and every uniquely referenced note. Purchase-rate aliases require
   explicit APR semantics; a bare percentage cannot replace complete annual
   purchase terms. Introductory periods, subsequent ranges, creditworthiness
   and transfer conditions remain complete text, never scalar endpoints.
2. **Accessible in-page references were not resolved.** Literal
   `data-scroll-target` identifiers now use the shared local-note resolver.
   Nested superscripts inside a resolved anchor do not become a second missing
   note. Conflicting target attributes, missing/duplicate targets, other-product
   panels and calculators remain rejected. This also applies to deposit notes.
3. **Marketing H1 text hid a native product name.** An immediately preceding
   semantic hero product label is accepted only with captured SEO corroboration,
   distinctive route agreement, current bank/country/snapshot/parsed-document
   origin and its own price record. Metadata or discovery confidence alone
   cannot create an identity. Whitespace/trademark matching preserves meaningful
   distinctions such as Plus, Students and Good Credit.
4. **Separate card prices polluted annual-fee validation.** A complete strictly
   labelled shared disclosure can contain purchase/cash/transfer APR and a
   promotional transfer fee without making the separately stated annual fee
   conditional. The shared classifier checks agreement of every restated annual
   fee and keeps the entire original quote. Actual annual-fee waivers, durations,
   unknown qualifiers and conflicting amounts still block approval, including
   explanatory amounts with ASCII or typographic apostrophes. Audience
   words in an owned product title do not become a fee-waiver condition.

Changes are in the shared native DOM/card records, parser, extraction, grounding
cache fingerprint and financial quote validator. Parser v21, process
`2026-10-09-owned-card-declaration-proof-v12` and shared comparison instructions
advance together. There are no bank/product-name exceptions, financial-value
injections, weaker essentials or manual approvals. The strict disclosure grammar
is shared and numeric values are parsed from original evidence.

Replaying six originally rejected cards using their exact original saved bytes
now automatically validates all six: Venture, VentureOne, Williams Sonoma,
Pottery Barn, Savor and The Key Rewards. That replay uses fixture origin records
for diagnosis, not publication. The actual operation separately resolves real
stored origins and uses the current captures below; historical facts were not
restored to fill Public.

## Current automatic publication

Completed operation `bny-capital-direct-20261009` through the ordinary extraction,
stored-artifact normalization, real DB origin resolution, validation-routing and
automatic-promotion services. Actual stored-origin results matched the rehearsal:
27 candidates, fifteen automatic approvals, twelve exclusions, no reviews,
no providers and no Admin API calls. A transaction rehearsal applied all fifteen
promotions and rolled them back; canonical rows, versions and refresh requests
returned exactly to their before-images before the real promotions.

The ordinary aggregate runner consumed the operation's one US refresh request,
creating `agg_ehR8w3tXsz54HJOw`. Anonymous Public list/API/site checks passed for
all fifteen products, including the entire qualified purchase APR text. US Public
increased from 22 to 28; CA remained 120. Capital One increased from nine to
fifteen. Six products were added and nine existing products received new approved
versions. No BNY product passed the missing-essential evidence gate.

The six newly published products are:

- [Pottery Barn Key Rewards Visa](https://www.switchabank.com/products/prod_1gXkjbh6uh39xlOb?country_code=US)
- [Savor Rewards from Capital One](https://www.switchabank.com/products/prod_b2K_qnM71r7bqMW-?country_code=US)
- [The Key Rewards Visa](https://www.switchabank.com/products/prod_8TQVGrdTkkrsbYHS?country_code=US)
- [Venture Rewards from Capital One](https://www.switchabank.com/products/prod_goB5wtWk7eEMgZg4?country_code=US)
- [VentureOne Rewards from Capital One](https://www.switchabank.com/products/prod_mnfaB88bpQ8Ik6dT?country_code=US)
- [Williams Sonoma Key Rewards® Visa](https://www.switchabank.com/products/prod_DjbgYiZ8TG3RyFWa?country_code=US)

Forty-five current field links were checked against exact original-capture text
and offsets, quoted financial values, selected Run snapshot/parse joins and
bank/country/URL ownership. All fifteen policy receipts pass the final shared
gates. Original five Runs, 27 candidates, 45 stages, 46 bank documents and 95
snapshots are unchanged. All 1,534 previous financial version facts remain intact;
nine approved versions were normally superseded. The other 456 canonical rows
and unrelated Public financial data remain unchanged. Private evidence is absent
from Public API and site responses.

Native student product names update
through existing source continuity, preserving product identity and history.

The twelve remaining Capital One exclusions retain current essentials:
three savings inputs do not prove current comparable rates/fees and complete
identity (captured rate templates still show NaN); three checking inputs do not
prove own fees/ordinary transaction costs; Auto Refinance lacks complete current
APR/term. Five cards remain incomplete: the old Savor route, an unpopulated
Quicksilver price template, T-Mobile without current purchase APR, Bass Pro with
only a restricted purchase offer, and a Kohl's Card/returned Visa identity and
terms mismatch. Unknowns remain absent rather than zero or false.

## Verification and deployment boundary

- Independent API environment: all 649 tests pass, including a full rerun
  after the final quote-punctuation boundary correction.
- New official-source and generic boundary regression module: all 16 tests pass.
- Focused parser, native account records, US account costs, complete RBC purchase
  terms and grounding-cache regression set: 63 tests passed before the final
  additional conflicting-fee boundaries, which then passed the 16-test module.
- Full Worker before the final typographic-apostrophe conflict tightening:
  946 tests, 944 pass and the two pre-existing hash tests below fail; no
  behavior regressions remain. The final affected boundary rerun is recorded
  below. Actual publication receipts and site readback pass.
- Final affected boundary rerun: all 44 tests pass (owned card declarations,
  native records and US account costs), including typographic-apostrophe fee
  contradictions.
- Foundation baseline, changed Python syntax, UTF-8, JSON and six decompressed
  official fixture SHA-256, introduced Markdown references and git diff checks
  pass. No application UI/build changes are involved.
- Two pre-existing hash-test failures were investigated separately: all 23
  mismatching legacy fixture files and their manifests are byte-identical to
  Git HEAD. Neither expected hashes nor original evidence was changed.

No schema migration or UI change is required. Deploy the API and Worker from the
same v12 source, including native modules, prompts and parser/cache versions.
Final serving health is HTTP 200 / ok with process v11; this task does not claim
runtime deployment.
Data publication is a separate one-off operation through the ordinary services.
Future Admin runs need the coordinated v12 deployment to use these corrections.

Private captures, before-images, plans, origin checks and rollback/public receipts
are retained under the operation `bny-capital-direct-20261009` and ignored local
`tmp/bny-capital-20261009`; they are not exposed through Public.
