# BMO zero-approval diagnosis and shared collection correction

Date: 2026-10-03. Scope: Product Owner request to explain zero BMO approvals
and correct generic collection logic/prompts. Implementation is local; deployment
and paid collection/publication are separate. No financial acceptance minimum was
removed and no manual review or bank-specific exception was introduced.

## Findings from preserved inputs

The completed seven-scope BMO operation produced 27 rejected candidates, zero
approved candidates and zero new review tasks. These are candidate records, not
27 verified products. All 27 lack current-run comparison essentials; 23 also lack
verified identity and two lack verified currency. The latest completed replacement
Mortgage Run is included; its original DB-disconnection failure is preserved.
Diagnosis used a repeatable-read, read-only DB transaction and retained stage
artifacts: 41 selected snapshots, 41 parsed records, 834 chunks, 32 source documents
shared across scopes and 101 model-execution records. The evidence does not support
the claim that BMO has no published product information.

| Failure path | Observed evidence | Shared correction |
|---|---|---|
| Capture structure | All 41 selected snapshots used browser PDF fallback. Comparison text clipped names/amounts and cookie overlays displaced useful text. | HTML routes retain rendered DOM by default; explicit/native PDF and query-identified PDF sources retain PDF. Existing safe-fetch, retries and timeouts remain. |
| Comparison scope | The actual Performance HTML table associates fee/transaction cells with their product column using `headers` and `th` IDs. Parser v5 did not retain those financial cell relationships. | Parser v6 adds atomic cells with exact column/row headers, all value/header conditions and explicit local notes. Missing/duplicate/cross-table headers, ambiguous local notes and oversized context produce no new cell proof. Matching named columns precede navigation within the existing budget; other columns cannot be cited as the target's atomic proof. |
| Redundant grounding search | Extraction had current official chunks but required another provider search's source list. Saved notes rejected fields as `consulted_source_missing`, while model summaries described captured fees/allowances. | One model pass grounds only supplied owned captures and bounded captured companions. The server builds allowed citations from those captures; no extra web-search tool is attached. Discovery/coverage repair retains its existing bounded search. |
| Provenance overwrite | Actual Personal Loan chunk `chunk-56754cf69bf2aa50` has 897 characters. Different fields linked its full text and an 853-character scoped excerpt. Strict equality removed the scoped link's URL; duplicate chunk rows let that link overwrite the valid identity origin. | Validate a scoped link as an exact contiguous part of the authoritative current-run raw chunk, then use the full raw chunk once per ID. Missing resolved origins fail closed, and run/bank/country/document/snapshot ownership remains mandatory. |
| Non-product detail selection | Retained identities include Mortgage Protection Insurance, card access/security/travel-insurance pages, a prepaid card and a GIC search tool. | A shared prominent-identity policy screens these at discovery, ordinary reuse preflight, model grounding and automatic acceptance. Supporting documents remain evidence-only; insurance benefits on a named financial product remain valid optional evidence. |

The original raw provider field response was not retained for every target. The
`consulted_source_missing` stage loss and contradictory summary are demonstrable;
a particular model URL spelling or redirect cannot be established retrospectively.
No undocumented URL alias or missing financial fact was invented to explain it.

## Evidence and runtime contracts

- Grounding still requires exact supplied chunk/quote/source, native field type,
  official origin, identity, currency, annual-rate basis, financial meaning,
  conditional comparison essentials and a content-bound automatic receipt.
- Companion selection remains within the existing current-run bank, country,
  language, exact-parent/named-product boundaries. A provider source outside the
  supplied captures, a different document query, an invented chunk or changed
  quotation cannot supply proof. Source text is data, not instructions.
- The model copies the exact captured product identity, uses the column named by
  financial-table evidence and preserves all fee/rate/access conditions. Missing
  required facts remain unverified; missing optional facts are omitted without
  extra searches/retries. Optional facts remain collected when the same proof exists.
- Grounding remains at most 24 chunks / 43,200 characters, with the existing eight
  companion slots and no truncation of an atomic context above 6,400 characters.
  No provider/fetch retry allowance was increased. Code/policy fingerprints
  invalidate grounding reuse after this correction.
- `collection-official-grounding-v2` and `official_web_sources` remain compatible
  evidence fields. New results record `official_grounding_method=captured_official_evidence`
  and `grounding_source_mode=captured_evidence`; usage records no required web search.
- Normalization uses DB-joined successful current-run origins, keeping the original
  full text available for condition/negation/conflicting-value checks. A short
  excerpt cannot hide a qualification or create a new financial fact.

## Verification and limits

1. Saved BMO Personal Loan extraction was replayed through provider-disabled
   normalization: product identity is now verified; calculator input 5% remains
   absent as a product rate, and missing product rate/term still excludes the loan.
2. One bounded read-only fetch of the official [Performance page](https://www.bmo.com/en-ca/main/personal/bank-accounts/chequing-accounts/performance)
   returned rendered HTML (3,048,693 bytes, 181 pre-change parsed segments), with
   complete product identity and fee text. No collection Run, model call, registry
   update or publication was performed. The tracked fixture retains selected original
   column/fee/transaction rows and their conditions, omitting styling attributes.
3. The real DOM fixture validates the Performance base monthly fee with its actual
   balance-waiver context and without another column's fee/currency. Changing it
   to unconditional zero is rejected. This verifies a field, not publication of
   the account: absent transaction essentials still block the test candidate.
4. Independent CA/US captured-only examples pass the real automatic gate without
   provider web-search sources. Adversarial foreign bank/country/snapshot/parse,
   unprovided URL/chunk, changed document ID, altered quote, lost origin, hidden
   conditional zero, malformed table links/notes, oversized context and
   non-product identity cases remain excluded. Existing financial/security tests pass.
5. Worker: `uv run python -m unittest discover -s worker -p "test_*.py"` —
   674 tests passed. API: `uv run --directory api/service python -m unittest discover
   -s tests -p "test_*.py"` — 574 tests passed in the separate API environment.
   Repository doctor and final diff hygiene are recorded in the development journal.

All model-response tests use deterministic stubs; they prove prompt/payload/validator
behavior, not a fresh live model's extraction yield. Some required disclosures may
still be missing from selected current inputs. No result claims all 27 candidates
should pass, that unknown terms are absent at the bank, or that a fake calculator
rate is usable. BMO remains at zero published products from this operation until
runtime deployment and a separately scoped normal collection pass produce valid
receipts. Do not reapprove legacy candidates or restore facts to fill Public.

## All 27 original candidate exclusions

These are the retained operation receipts before the correction. Missing-field
lists express applicable alternatives/conditional requirements, not proof that the
bank omits those facts. Identity and currency failures are independent of the
comparison failure present on every row.

| Type | Retained candidate label | Other blocking reasons | Missing comparison facts |
|---|---|---|---|
| chequing | Blue Rewards Chequing Account | product_identity_unverified | monthly_fee, unlimited_transactions_flag |
| chequing | Performance Chequing Account | product_identity_unverified | monthly_fee, unlimited_transactions_flag |
| chequing | Plus Chequing Account | product_identity_unverified, product_currency_unverified | monthly_fee, unlimited_transactions_flag |
| chequing | Practical Chequing Account | product_identity_unverified | monthly_fee, unlimited_transactions_flag |
| chequing | Premium Chequing Account | product_identity_unverified | monthly_fee, unlimited_transactions_flag |
| chequing | U.S. Dollar Primary Chequing Account | product_identity_unverified, product_currency_unverified | monthly_fee, unlimited_transactions_flag |
| credit-card | Affinity credit cards | product_identity_unverified | annual_fee, purchase_interest_rate |
| credit-card | BMO Prepaid Mastercard ®* | product_identity_unverified | annual_fee, purchase_interest_rate |
| credit-card | BMO Support Our Troops Mastercard | product_identity_unverified | annual_fee, purchase_interest_rate |
| credit-card | BMO ® Mastercard ®* Travel Insurance | product_identity_unverified | annual_fee, purchase_interest_rate |
| credit-card | Credit Card Access Details | product_identity_unverified | annual_fee, purchase_interest_rate |
| credit-card | Credit Card Security Protection | product_identity_unverified | annual_fee, purchase_interest_rate |
| gic | BMO Progressive GIC Series search tool | None | standard_rate, term_length_text, redeemable_flag, early_withdrawal_penalty |
| line-of-credit | Homeowner Readiline®: Mortgage & Line of Credit | product_identity_unverified | interest_rate_summary, secured_flag |
| line-of-credit | Homeowner’s Line of Credit | product_identity_unverified | interest_rate_summary, secured_flag |
| line-of-credit | Medical or Dental Student Line of Credit | product_identity_unverified | interest_rate_summary, secured_flag |
| line-of-credit | Personal Line of Credit | product_identity_unverified | interest_rate_summary, secured_flag |
| line-of-credit | Professional Student Line of Credit | product_identity_unverified | interest_rate_summary, secured_flag |
| line-of-credit | Student Line of Credit | product_identity_unverified | interest_rate_summary, secured_flag |
| mortgage | Homeowner ReadiLine | None | interest_rate_summary, term_length_text |
| mortgage | Mortgage Protection Insurance | None | interest_rate_summary, rate_type, term_length_text |
| personal-loan | Personal Loan | product_identity_unverified | interest_rate_summary, term_length_text |
| savings | High Interest Savings Account | product_identity_unverified | standard_rate, monthly_fee |
| savings | Premium Rate Savings Account | product_identity_unverified | standard_rate, monthly_fee |
| savings | Savings Amplifier Account | product_identity_unverified | standard_rate, monthly_fee |
| savings | Savings Builder Account | product_identity_unverified | standard_rate, monthly_fee |
| savings | U.S. Dollar Premium Rate Savings Account | None | standard_rate, monthly_fee |
