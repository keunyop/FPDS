# Latest Alterna and B2B collection audit ? 2026-10-02

## Outcome

The latest collections completed, but completion does not establish usable product coverage. Alterna approved one of four candidates; B2B approved none of fourteen. Current Public API returned the approved Alterna checking account and no B2B products. No manual review queue was created. Automatic exclusion remains appropriate where required evidence is absent; several upstream defects prevent otherwise available evidence from reaching the gate.

| Bank | Collection | Vancouver window, October 2 | Completed runs | Successful selected source operations | Failed selected source operations | Candidates | Approved | Excluded | Active Public products |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Alterna | collection_i_lRV5vFsAlb59IO | 09:51?10:02 | 4 | 11 | 0 | 4 | 1 | 3 | 1 |
| B2B | collection_Zc3hGizXOI7A9O6h | 09:59?10:30 | 6 | 37 | 0 | 14 | 0 | 14 | 0 |

Source counts are processing operations, not unique pages or discovery completeness. B2B Savings has a preparation skip for a PDF presented to the HTML fetcher, despite zero failures in the selected-source counters. One B2B mortgage candidate also records `partial_source_failure`. B2B candidate counts include aliases and support pages; fourteen is not fourteen proven bank products.

Run prefixes: `run_20261002_165110_alterna_*` and `run_20261002_165837_b2b_*`. The approved checking run is `run_20261002_165110_alterna_chequing_collect_qNJcj1ZR`.

## Alterna findings

- **No-Fee eChequing Account: approved and visible.** Annual rate 0.05%, monthly fee CAD 0, unlimited ordinary transactions. Current Public values match the accepted candidate. Optional interest calculation/payment fields were omitted with `other_product_interest_context`: the deposit legal section and later overdraft section share a chunk. The full-chunk overdraft guard added in the previous optional-rate change is too broad for this compound evidence. Optional omission does not invalidate publication, but merits a generic section/field context fix with adversarial tests.
- **High Interest eSavings: excluded for missing standard rate.** The captured detail has `1.05%*` separately from the legal annualization paragraph; the captured [official checking/savings rate table](https://www.alternabank.ca/en/personal/rates/chequing-savings) also explicitly identifies this account and 1.05%. Official grounding omitted the numeric rate with `field_meaning_unproven`. The problem is linking product row, annual-basis footnote and consulted evidence without importing another account's values. A bare percent chunk must not become an annual scalar by assumption.
- **eTerm Deposits: excluded for rate, term and withdrawal essentials.** Detail HTML contained percent placeholders, but a captured supporting [official term-deposit schedule](https://www.alternabank.ca/en/personal/rates/term-deposits) contains annual 1/2/3/4/5-year rates of 2.65/2.85/3.10/3.25/3.30%. Grounding did not establish the applicable schedule from this companion evidence. Legal text also says cashable upon maturity only and includes promotional and investment-limit conditions. Preserve separate term/rate rows and all material conditions; do not select a convenient scalar or infer withdrawal semantics without proven mapping.
- **Personal Loan: appropriate exclusion on retained evidence.** The borrowing-family page establishes a one-to-five-year term, but not a current numeric applicable loan rate. Do not substitute line-of-credit wording or values from another product.

## B2B findings

- **Chequing: should be screened out for availability.** The retained official product page and [official fee schedule](https://b2bbank.com/sn_uploads/marketing/640-08-526E-B2BBank-Chequing-Fee-Schedule.pdf) explicitly state new Chequing Accounts ceased opening on August 6, 2026. The current run instead extracted this candidate and excluded it for missing fee/transaction essentials. Add a product-scoped availability check before grounding; the same notice in a savings-page footer must not mark Savings unavailable. These findings rely on the stored official captures; independent web-tool re-fetch of B2B pages/PDF was unavailable during this audit.
- **High Interest Savings Account: evidence acquisition/linkage needs repair.** Retained rate evidence contains 2.20% tier rates and annual daily-calculation/monthly-payment text; some typed descriptive facts survived, while scalar rate failed `field_meaning_unproven`. Monthly fee failed `exact_quote_missing`. A linked PDF was skipped with `Text fetch expected HTML content but received application/pdf`; query-based document identifiers occur on these official links. Dispatch by validated response content type, preserve meaningful query parameters and existing safe-fetch limits, and connect exact product fee/rate evidence. Do not infer unconditional rate or zero fee from a brochure summary.
- **GICs: duplicate aliases and a confirmed identity mutation.** Four candidates represent short/long-term pages with `/en/` and non-`/en/` aliases. Normalization changes grounded `Short-Term` to `Short Term`, triggering `product_name:value_changed_after_grounding`. Preserve grounded identity or establish an explicit verified display/canonical distinction. One alias also has `evidence_source_mismatch`; fix source linkage rather than relaxing receipts. Short-term durations are 30?364 days, not a one-year term. Long-term withdrawal variants and rate conditions require exact product/variant boundaries. Some grounding notes reject dated schedules as stale: distinguish effective date, retrieval verification and actual expiry without automatically accepting old terms.
- **Mortgage: discovery selects service pages rather than offers.** Six candidates are portability, renewal, refinancing and broker-support pages, including aliases. They lack product rate/type/term essentials and are correctly excluded downstream, but should be classified as supporting/service evidence before grounding. The collection captured a mortgage rate schedule; discovery needs actual offer boundaries and accurate term/rate/APR mapping, not publication of a service-page title.
- **HELOC and RSP Loans: required pricing/security/term evidence remains missing.** Selected investment-loan brochures do not establish the exact products' essentials. A mortgage-group capture includes HELOC pricing, but it was not selected as the LOC run's companion. Improve exact-product companion planning within bounded collection, preserving current-run consulted origins; never inject another run's chunks to bypass evidence validation.

## Recommended order

1. Screen product-specific availability and service/support pages before model grounding; consolidate aliases only when source identity equivalence is proven.
2. Fix HTML/PDF content-type dispatch and document query identity, then exact-product companion selection. Expose preparation skips separately from successful selected-source counts in diagnostics.
3. Bind captured product rate rows, annual-basis footnotes, terms and fee/withdrawal conditions with exact consulted origins. Keep conditional financial meaning and typed comparison boundaries.
4. Preserve grounded product names through normalization; narrow interest-context rejection to the applicable field/section while retaining full evidence and cross-product safeguards.
5. Add source-backed regressions before implementation: current/ineligible products, service-page exclusion, PDF query links, aliases, split row/footnote evidence, promotional GIC variants, identity preservation and compound deposit/overdraft legal text. Change gates and prompts together where acceptance semantics change.

Checking interest remains optional. These improvements concern acquisition and preservation of proven facts, not weakening publication essentials, adding human review or chasing optional completeness. No new collection or deployment is justified by this audit alone.

## Verification and limits

- PostgreSQL inspection used a repeatable-read, read-only transaction: latest runs, candidate payloads, retained source/model metadata and canonical active states.
- Inspected 48 retained extraction artifacts and associated chunks. No new model calls, collection runs, registry/canonical/publication writes or runtime changes.
- Replayed all 18 saved candidates through the current accuracy sanitizer using saved evidence: accepted/rejected outcomes matched all stored outcomes. This confirms gate consistency, not discovery completeness or proof of every omitted value.
- Read current Public API `https://switchabank-api.vercel.app/api/public/products?country_code=CA&page_size=100`: CA total 30, no next page, Alterna one active checking account, B2B zero. Approved Alterna rate/fee/transaction values match.
- Independently fetched Alterna official rate pages through the web tool. B2B re-fetch failed there; B2B conclusions are bounded to the retained official evidence from these collections.
- Private diagnostic files remain under ignored `tmp/two-bank-*`; raw evidence, internal source traces and operator identifiers are not published. No application tests were necessary because this slice changed only governance documentation. Final `git diff --check` and report-link checks are recorded in the journal.
