# BMO collection diagnosis and generic corrections - 2026-10-09

## Scope and original results

The latest BMO Bank scopes belong to **US / BB**, not CA / BMO. The five
completed Runs started at 2026-10-09 05:10:38 UTC, using process
`2026-10-08-accessible-qualified-source-proof-v10` and parser v19. Admin collection
API was not used for this investigation, direct collection or publication.

| Latest Run suffix | Type | Candidates | Selected sources | Original automatic approvals |
|---|---|---:|---:|---:|
| `mortgage_collect_YtztTsTD` | Mortgage | 4 | 8 | 0 |
| `line-of-credit_collect_eJbidpTa` | Line of credit | 2 | 9 | 0 |
| `gic_collect_1ad-ZgXS` | CD / IRA CD | 2 | 5 | 0 |
| `credit-card_collect_iJ-_pkwB` | Credit card | 5 | 19 | 0 |
| `chequing_collect_VZBUYG-F` | Checking | 3 | 10 | 1 |

There were sixteen candidates: fifteen rejected and Smart Advantage Checking
approved. Original Runs, candidates, source-stage rows, documents and snapshots
are preserved. Forty-nine original selected source snapshots were downloaded and
SHA-256 verified for diagnosis. Replaying the original unchanged bytes through
the corrected stored-artifact/origin services automatically validates the same
four cards and HELOC identified below. This isolates actual code/evidence losses
from changes to bank pages; those historical captures are not publication inputs.

## Demonstrated defects and shared corrections

1. **Owned list disclosures were lost.** Exact flat-label matching missed
   `Annual fee*`, accessible `Footnote star`, zero-width formatting and
   `Variable Purchase APR` in semantic list rows. This removed the complete
   labelled record before ordinary grounding. Recognition now tolerates these
   literal formatting markers while retaining original text, local notes and a
   uniquely observed bounded legal link. Missing/ambiguous references, other
   product panels and conditional zeros remain blocking. Synthetic other-bank
   card and savings fee lists exercise the same parser without bank exceptions.
2. **Named PDF purchase columns and introductory conditions were missing.**
   Generic named-column parsing now retains each card's own current variable APR
   range, introductory period when present, creditworthiness/Prime Rate basis,
   loss-of-introductory-APR trigger and promotional grace rule. Complete PDF
   purchase terms supersede the owned display only when percentages and
   introductory account-opening periods corroborate exactly. Rate/period
   conflicts, missing shared clauses, duplicate identities and truncated
   conditions stay excluded. Promotions and endpoints never become scalar rates.
3. **Explicit collateral was rejected and a verified optional explanation was
   dropped.** The HELOC explicitly borrows against home equity as collateral.
   A later sentence says repayment payments may be higher. The old global
   uncertainty matcher treated that separate repayment consequence as optional
   security. The shared classifier distinguishes this complete literal clause
   while retaining the original quote and rejecting uncertain/optional or
   conflicting security. Owned lending records retain the complete APR paragraph,
   including geographic/LTV/credit-score/autopay, floor/ceiling and date conditions.
   The normalizer no longer drops a complete verified security quote solely for
   exceeding a short-copy limit. Registered same-decision descriptive alternatives
   survive without inserting unrelated unrequested required fields.
4. **ATM-only transactions were incorrectly accepted as ordinary coverage.**
   `Unlimited Transactions at 40,000+ fee-free ATMs` and line-wrapped non-bank
   ATM wording prove only the ATM channel. The ordinary transaction gate now
   rejects these directly qualified claims. Aggregate and Public checks use the
   private mapping of the exact approved version pinned by the snapshot, joined
   by bank/country. An older accepted receipt cannot hide that limitation.
   Rechecking only this channel distinction preserves independently proved
   ordinary coverage, separate fee waivers and separately labelled ATM prices.
   Private mappings are removed from returned Public rows.

These changes are parser v20/process
`2026-10-09-owned-list-disclosure-proof-v11`. Shared instructions, exact-origin
checks, complete atomic chunks and grounding cache fingerprints change together.
The mandatory financial essentials, units, currency defaults, confidence policy,
private evidence and account/security approval boundaries are unchanged.
Increasing model confidence or weakening required fields would not recover the
lost source ownership or prove missing terms.

## Current direct collection and exclusions

The bounded operation independently fetched the original forty-seven official
registry URLs: forty-five succeeded and two browser attempts timed out (Escape
card detail and an adjustable-rate mortgage support page). The two unmarked
Canadian support URLs in that registry were excluded from the US input set;
their currency/country was never relabelled. Existing transport/browser budgets
were retained; successful inputs were reused for all subsequent verification.
No provider calls or paid research were made, and no optional-only searches or
retries were added.

Fifteen current detail candidates are processed, with five ordinary automatic
approvals and ten exclusions. Escape has no successful current detail capture
and is not republished from its original snapshot. Mortgages lack complete owned
rate/term proof; the fixed-rate HELOC page describes an option rather than a
separately proved offer; CD/IRA CD pages lack proven current rate/term/access
conditions; checking pages lack ordinary transaction proof and, in some cases,
a complete owned base monthly-fee record. These omissions are not zero/false and
are not a manual-review queue. Optional completeness never overrides essentials.

## Publication and verification

Operation `bmo-direct-20261009` completed five direct Runs, fifteen candidates,
five ordinary automatic promotions and ten exclusions. Sixteen current source
stages and sixteen field-evidence links were checked against exact captured
bytes and the DB-selected source/snapshot/parse joins. Final-code revalidation
produced identical financial values, conditions and private field mappings to
the persisted candidates; only revalidation timestamps and their receipt digests
differed. Each digest was independently checked. The promotion transaction
rollback rehearsal passed before the real five promotions. Manual product
reviews, provider calls and Admin collection API calls were all zero.

Normal US aggregate refresh consumed the two BMO promotion requests and completed
snapshot `agg_GtPzyOYNGT_6vj8t`. Anonymous Public list and all five API/site
details were read back successfully; every site detail returned HTTP 200.
Complete card conditions and HELOC APR/security prose were visible. No scalar
rate was invented and no private evidence/mapping was exposed.

| Product | Public result | Verified detail |
|---|---|---|
| BMO Cash Back Credit Card | Current evidence/version updated | [Public detail](https://www.switchabank.com/products/prod_wHMHXdanP3jneWPf?country_code=US) |
| BMO Platinum Credit Card | Newly public | [Public detail](https://www.switchabank.com/products/prod_D_wy2SBXaWK9VeDS?country_code=US) |
| BMO Platinum Rewards Credit Card | Newly public | [Public detail](https://www.switchabank.com/products/prod_jTlZaeI6EDhgPj85?country_code=US) |
| BMO Premium Rewards Credit Card | Newly public | [Public detail](https://www.switchabank.com/products/prod_qAttoJyRGw5TPWJn?country_code=US) |
| Home Equity Line of Credit | Newly public | [Public detail](https://www.switchabank.com/products/prod_5L9QkFx3IHs7Xkf8?country_code=US) |

The publication adds four visible products and updates the previously public
Cash Back card. The incorrectly approved Smart Advantage Checking is excluded
from the current projection without changing its canonical or original approval
history. Initial BMO Public had two products (Smart Advantage and Cash Back);
current BMO Public has five. This is five recovered latest-Run approvals, four
new Public listings, one current Public update and one accuracy exclusion.

The original five Runs, sixteen candidates, 51 source-stage rows, 54 documents
and seventy snapshots are unchanged. All 1,529 pre-promotion version facts are
preserved; two prior approved versions were normally superseded while keeping
their financial contents. The 460 unrelated pre-promotion canonical products
and all unrelated Public financial facts are unchanged by this operation.
CA remains 120; US is 22.

Concurrent Capital One work added nine canonical products during evidence
storage. The initial global guard correctly stopped BMO before any canonical
promotion. Its approved changes were audited and retained in a new baseline,
while the original baseline remained archived. Capital One's nine Public
listings account for the unrelated increase: initial US 10 + nine Capital One
+ four newly public BMO - one invalid BMO = final US 22. The immediate
pre-promotion US baseline was eighteen. No other-bank Run was restarted or
cancelled. A single-bank SQL guard syntax error had earlier stopped before
reservation/storage/DB writes; it was corrected using identical captured inputs.

Final full Worker suite: **929 tests, only two existing fixture-hash test
failures** (`test_source_fixture_hashes_and_priority_count` and
`test_current_official_fixture_hashes`). All 23 mismatching source/manifest
entries involved in those old checks are byte-identical to HEAD; their expected
hashes and historical bytes were not changed. API: **649 pass**. Final affected
source/origin/channel/optional-field/API tests: **52 pass**, including conflicting
APR/intro periods, incomplete legal clauses, foreign product ownership, qualified
zeros, channel-only allowances and private evidence filtering. Earlier newly
introduced request-field/channel regressions were corrected and rerun.

Foundation baseline, affected Markdown references, strict UTF-8/Python/JSON,
new fixture hashes and final git diff whitespace checks pass. Test import/Windows
encoding and temporary command-quoting errors were corrected; they are not
reported as passing attempts or collection defects. Private operation receipts
remain under `tmp/bmo-improvement-20261009`; raw/current evidence and ordinary
pipeline artifacts, final verification/rollback receipts and concurrent-change
baselines are retained in the configured private evidence store.


## Runtime boundary

Product data publication is separate from runtime deployment. Serving health
was observed at v10; the local v11 API/Worker changes have not been deployed or
restarted. Concurrent Capital One collection Runs are preserved. Future Admin
collection needs the coordinated API/Worker v11 release to use these fixes, and
a later v10 aggregate refresh could reintroduce the old ATM interpretation until
that release. No schema migration, permanent recovery menu/scheduler or manual
product approval path is introduced.
