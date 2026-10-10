# Seven US banks: direct diagnosis, generic corrections and publication

Date: 2026-10-09 (America/Vancouver). Scope: existing `.env.dev` PostgreSQL,
private evidence storage and US Public. No Admin collection API or paid/model
provider calls. Runtime deployment is separate from this data operation.

## Latest stored results

| Bank | Latest per-type Runs | Candidates | Approved |
| --- | ---: | ---: | ---: |
| KeyBank | 6 | 28 | 1 |
| M&T Bank | 2 | 9 | 0 |
| Morgan Stanley Private Bank | 4 | 3 | 0 |
| PNC Bank, National Association | 6 | 13 | 0 |
| Regions Bank | 7 | 3 | 0 |
| Santander Bank | 3 | 5 | 0 |
| Schwab Bank | 1 | 0 | 0 |

Most current scopes started Oct 9 at 17:52:55 PDT using process v14. Regions
savings ran again at 21:51:11 PDT using v15. Zero-candidate historical scopes
include PNC (Aug 29), Regions (Sep 1) and Schwab checking (Sep 29). These are
latest per-type diagnostic records, not fresh publication evidence. The original
29 Runs, 61 candidates, 117 Run/source joins and 118 bank documents are preserved.
103 distinct selected original snapshots were downloaded and SHA256 verified.
All 29 latest records have terminal completed state; 15 are partial (source
failures or no eligible details). A completed Run is not proof of product approval.
KeyBank's original approval was Auto Loan; it is preserved. The no-provider
replay of original bytes is a different experiment (61 exclusions) and must not
be reported as the original stored model-assisted result (60 excluded/1 approved).

## Confirmed defect and generic correction

The original Key Cashback candidate already had identity, currency and a purchase
APR summary; its accuracy receipt excluded it for missing `annual_fee`. Its
literal fee-row superscript 2 points to a single disclosure section containing
numbered sibling notes 1 through 8. The old resolver imported that whole section,
including note 1's rewards eligibility conditions, into the annual-fee proof.
This is a common DOM ownership problem, not a KeyBank acceptance exception.

The common resolver now accepts a numeric superscript selecting one explicitly
numbered, structurally distinct sibling note. It retains the complete selected
note and every unnumbered shared passage. Missing, duplicate, empty, malformed,
ambiguous or oversized groups fail closed. Ordinary nonnumeric references and
single notes retain their complete container. Real source-byte tests also prove
that shared account-fee and balance-waiver conditions are never removed.

The common card parser also recognizes the explicit `Regular Purchase APR`
label, retaining the complete qualified range and disclosures. It does not
convert that interval into a scalar APR. The shared money gate distinguishes
an independently labelled fee from the exact separate sentence `All credit
products are subject to credit approval.` Actual fee eligibility, first-year
waivers, balances and conflicting fee restatements still reject the value.
Shared extraction/normalization instructions and parser/process identities move
together: parser v25 and process `2026-10-09-numbered-disclosure-scope-v16`.
The parser-version regression assertion was updated to the new identity.

Affected code: `worker/native_dom_ownership.py`, the common parse-chunk parser,
collection accuracy gate, comparison instructions and version declarations.
Source fixture and cross-type/adversarial regressions:
`worker/pipeline/tests/test_grouped_disclosures.py` and its SHA256 manifest/raw
compressed official fixture. No country/profile essentials, review behavior,
security boundaries or ranking rules were weakened.

## Current direct evidence and remaining exclusions

102 unique current official URLs were attempted; 93 returned usable captures
and nine remained unavailable. Current sources were reused by exact SHA256;
original historical bytes were used for diagnosis/regression only. An initial
one-off global browser cap prevented nine KeyBank URLs from being attempted.
Those exact unattempted URLs received their first bounded attempt, all succeeded,
and the previous cap-error receipts remain preserved. No failed browser capture
was retried, and the runtime's per-Run browser budget was not increased.

| Bank | Current candidates | Automatic passes | Main remaining evidence limits |
| --- | ---: | ---: | --- |
| KeyBank | 27 | 1 | Other targets lack complete proven comparison essentials; some links return existing-customer information or time out. |
| M&T | 9 | 0 | Captured location-dependent savings information and mortgage resources do not establish complete current product rates/terms. |
| Morgan Stanley Private Bank | 3 | 0 | Exact account identity and annual rate/term association are not proven across the captured product/rate-monitor names. |
| PNC | 13 | 0 | No current candidate proves all essentials through supported owned records. The six-page Cash Rewards Visa/Visa Signature agreement exists but its two-variant format remains unsupported; this is not a claim that the bank withholds rates. |
| Regions | 2 | 0 | LifeGreen savings remains an access challenge; two PDF URLs return unusable HTML shells. Other captured candidates lack essentials. |
| Santander | 5 | 0 | Three agreements redirect to `assets.santandermedia.com`, outside the configured official-domain allowlist. No external domain was automatically trusted. |
| Schwab | 1 | 0 | Current checking/FAQ pages were captured; unlimited ATM withdrawals alone do not prove general transaction costs. |

The final current no-provider assessment produces 60 candidates, one automatic
pass and 59 exclusions. It has 19 new scoped Runs. This is not a claim that every
excluded product is inherently uncollectable: regional input, a supported
variant-specific agreement format or separately reviewed domain registration
may establish additional essentials. No historical values, unrelated product
terms or fabricated zero/false fields were used to raise coverage.

## Publication and verification

Operation `us-seven-direct-20261009` completed: 19 new Runs, 60 candidates,
one automatically approved/published product and 59 exclusions; zero manual
reviews, model/provider calls or Admin API calls. Newly public product:
[Key Cashback Credit Card](https://www.switchabank.com/products/prod_p3miYCtmLIpyFdRY?country_code=US).
The official [current product page](https://www.key.com/personal/credit-cards/key-cashback-credit-card.html)
proves the USD zero annual fee and complete variable purchase APR range. The
published summary retains the whole qualified source disclosure, including
creditworthiness and Prime Rate basis, rather than a fabricated scalar rate.

Actual selected Run/snapshot/parse origins reproduced the same passing candidate
before any canonical mutation. A real promotion transaction was rolled back and
canonical products, versions and refresh requests were confirmed restored.
Ordinary promotion then approved that candidate and the ordinary Public runner
consumed only this operation's single US refresh request. Anonymous Public API
and the actual HTTP-200 product page confirm the complete APR summary. Public
counts are US 67 -> 68; CA remains 120. Private evidence keys/quotes/provenance
are absent from public responses/pages.

60 actual stored raw/parsed byte pairs were downloaded and matched; all four
published field origins, exact quote spans, financial meanings and the current
acceptance receipt passed. Original 29 Runs, 61 candidates, 117 joins, 118 bank
documents, 213 snapshots and 1590 financial versions are preserved. All
478 pre-existing canonical products remain unchanged. One previous approved version of the same canonical Cashback identity was
normally superseded by the newly collected version; its financial facts remain
unchanged. This reuses the existing product identity using current evidence,
not historical prices. The original KeyBank Auto Loan remains intact. Unrelated active
TD collection Runs were neither restarted nor modified by this operation.

Private one-off receipts, baselines, execution plan, rollback proof and final
readback are under `tmp/us-seven-20261009`; selected current evidence and
operation baselines/results are also retained in the existing private storage.
No permanent recovery feature, menu or scheduler was added.

## Local verification and rollout boundary

Final affected Worker tests: 69 pass; discovery tests: 85 pass; API tests: 650
pass. The first full pipeline run executed 911 tests: four previously reproduced
failures (two source fixture hash assertions and two named-annual-record card
checks), plus the new-version assertion subsequently corrected and rechecked.
No source fixture expected hash was changed. Previous exact-HEAD reproduction is
recorded in [the prior five-bank report](us-five-bank-generic-collection-corrections-2026-10-09.md)
and [the Chase report](chase-generic-collection-corrections-2026-10-09.md).
Foundation baseline, Git-visible Markdown references/JSON/PowerShell syntax,
strict UTF-8/Python syntax and `git diff --check` pass. No UI layout changed, so viewport/build work is outside this change.

The serving API health currently reports process v13. Original latest Runs used
v14/v15, so their losses cannot simply be attributed to that API health version.
Local correction and direct published data must remain distinct from a future
coordinated API/Worker release. No migration or new configuration is required.
After coordinated deployment, verify health identities, a bounded ordinary
collection with literal numbered disclosures, negative conditional-fee cases,
current evidence joins and Public privacy; roll back code if those checks fail.
