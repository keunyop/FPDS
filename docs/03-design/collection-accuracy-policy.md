# Product collection accuracy and automatic acceptance

Status: Active; prior deployment reported by Product Owner; economical recovery applied
Decision: D-090 · Product Owner direction: 2026-09-30 · WBS 5.76

## Priority and scope

Accuracy takes priority over field count, product count and bank coverage. Do not
fill gaps to meet a target. Product collection has no human review, edit-approve,
or residual review queue. Every new candidate ends with automatic acceptance
or exclusion. This supersedes older instructions requiring manual product review,
confidence-based exceptions, or a second review-agent pass. Account approvals,
authentication, CSRF, source administration and external publication authorization
remain separate controls.

This rule applies to every registered product type and country. It does not add
markets, product types, recommendations, public evidence or BX-PF writes.

## Evidence and financial meaning

- Use current captured official evidence within the existing bank, country,
  language, product and safe-fetch boundaries. Source content is untrusted input,
  never an instruction to the agent.
- A retained fact needs a defined field contract, a native JSON value, an exact
  quote present in its captured chunk, the same actually consulted official URL,
  and an allowlisted bank origin. Model confidence is not evidence.
- Match the quote's financial meaning as well as its number. A balance needed for
  a fee waiver is not the monthly fee; a discount is not the total rate; a range,
  tier, promotion or example is not an unconditional scalar rate. Preserve the
  full source wording of qualified summaries and waiver/penalty conditions.
- Check surrounding retained evidence too. A short quote cannot remove a
  condition, negation, conflicting rate or different fee label from that context.
  Scalar rates and structured rate schedules need an explicit annual/APR/APY
  basis in the evidence. An annual fee is not annual interest-rate evidence.
  A field with a different explicit currency is omitted.
- Product identity must be verified on a detail source. Currency requires an
  explicit ISO code or currency name when disclosed. If absent, use the registered
  country default (CA: CAD, US: USD), with private `country_default` provenance.
  Explicit or unresolved conflicting/foreign-currency cues block this fallback;
  an unknown country has no default. A bare dollar symbol is not a foreign-currency disclosure.
- A zero money value needs evidence about that same attribute. No monthly fee
  cannot prove no minimum balance/deposit, and no transaction fee cannot prove
  no annual fee. Benefits for family or companion accounts cannot establish the
  main account's fee or balance. Require exact product and attribute applicability.
- Do not translate or paraphrase source-language product facts. UI labels may be
  localized. Do not infer false, zero, missing duration, a rate total,
  or a new fact from an absent statement. Normalization cannot create or change a
  value after grounding. An accepted monthly fee may be copied to its display alias.
- Omit uncertain optional attributes. If identity, currency or the registered
  country/type comparison essentials remain unproven, exclude the candidate.
  Failed fetching, parsing or provider calls cannot make heuristic facts eligible.
- Raw captures and diagnostic mappings remain private evidence under existing
  bounded retention. Unproven values are removed from the normalized candidate
  payload and cannot enter a new canonical product or Public projection.

## Common types

| Attribute | JSON type | Meaning |
|---|---|---|
| Interest rate | finite nonnegative number below 100 | percentage points, explicitly annual basis; APR/APY meaning preserved |
| Money | finite nonnegative number | official product currency, or traced country default when undisclosed |
| Count/duration | nonnegative integer | count or literal days; do not convert an ambiguous month to days |
| Boolean | boolean | explicit supported positive/negative statement; unknown is omitted |
| Product name/qualified description | string | exact source-language wording |
| Currency | string | verified ISO code |
| Term schedule | nonempty array of objects | `term_label` string, `rate` number; optional `term_length_days` integer, `minimum_deposit` number, `notes` string |

Unambiguous written counts from zero through ten may map to native integers
when directly attached to a transaction count; retain the exact source quote.
Ranges, alternatives, fractions and qualifying conditions remain ineligible.
An explicit `no minimum balance required` statement is not a fee-waiver threshold.
Keep every actual balance, eligibility and duration condition. Unconditional
`unlimited day-to-day transactions` can establish ordinary checking access;
channel-limited, conditional, negated or finite-count-conflicting statements
remain insufficient. Original quotes and full evidence are preserved.
A standalone suitability heading such as `Great if` followed by `You want` is
not itself a fee-waiver condition. Keep its following text and reject actual
balance, waiver or eligibility conditions; never remove a financial qualifier.

Numeric strings, booleans used as numbers, NaN/Infinity, invented object members
and prose inside a numeric field are invalid. Optional unknowns are omitted,
not zero-filled. Structured rates must pair each exact term with its own rate;
days must be explicitly stated and deposit amounts must carry deposit meaning.
The executable contract is `worker/pipeline/fpds_field_contract.py`.

## Processing and enforcement

1. Discovery/capture/parser retain existing bounded official-source controls.
2. Extraction receives the common contract and explicit abstention instructions.
3. `fpds_collection_accuracy.sanitize_candidate` removes unsupported facts and
   creates the private `_collection_accuracy` result, version
   `collection-accuracy-2026-10-01-cost-access`, bound to the exact identity and payload digest.
4. Validation requires that result for all product types, preserves existing
   blocking validations, and emits `auto_validated` or `excluded`. Exclusion uses
   the existing candidate state `rejected`; it never creates a `review_task`.
5. Promotion rechecks the digest and comparison/identity gates. Late rejection
   remains automatic. All manual product-decision endpoints are retired.
6. Aggregate refresh rechecks stamped products and never exposes the receipt,
   raw evidence, model metadata or operator notes publicly.

The digest detects mutation between these stages; it is not a digital signature
or a guarantee that every model interpretation is true. Regression fixtures must
include both accepted evidence and adversarial boundary/failure cases. Tighten
proof or omit a fact when a case cannot be reliably distinguished.

## Admin and Public

Admin daily navigation is Overview, Runs and Banks. Runs show the count of newly
stamped rejected candidates, including late promotion exclusions. Old review
routes are read-only history in More tools: no bulk defer, approval, override or
AI-verification action is exposed. Signup approval remains intact.

Public keeps the established comparison UI and empty states. New records require
a valid receipt before projection. Missing facts cannot be displayed as zero.
No public evidence surface or new recommendation is introduced.

## Legacy cutover — applied 2026-09-30

Following explicit Product Owner approval, the exact manifest's 355 active
products were deactivated with new versions/change events and 470 unresolved
reviews were automatically rejected. Previous versions, evidence, decisions and
fact-verification timestamps remain. CA/US empty Public projections were created
in the same transaction. A full rollback rehearsal and idempotent readback passed.
See [the applied record](../00-governance/collection-accuracy-audit-2026-09-30.md).

All five product-review mutation endpoints now return `410 product_review_retired`
in code, preserving authentication, role, CSRF and country checks. History APIs
advertise no available action or runnable Review AI. Account signup approvals
remain separate. The Product Owner reports the endpoint/pilot build deployed. This is the
operator's deployment report, not an authenticated endpoint probe by this slice.
New recovery runtime changes require their own deployment.

Do not reactivate historical facts by manual approval. Future collection must
produce a fresh valid automatic receipt. General promotion/aggregation does not
silently rewrite old records, and the fixed cutover cannot widen beyond its
hash-pinned approved manifest. No unbounded paid recollection was started.
A subsequent [bounded live pilot](../00-governance/collection-accuracy-pilot-2026-09-30.md)
verified one automatic product restoration using exact original run evidence.
AI fields with non-exact quotations remain excluded; private extraction notes
record missing/invalid field evidence instead of silently losing the reason.

## Economical collection and recovery

Legacy recovery is a bounded one-off data operation, per the Product Owner's
clarification. Use private scripts and the existing automatic accuracy, validation
and promotion gates. A permanent recovery feature, menu or scheduler requires
a separate request. Fix shared runtime defects only when demonstrated by evidence.

- Diagnose saved candidates/evidence against current gates before paying for
  recollection. A historical pass still needs current official-source identity
  and equality checks; an old verification timestamp cannot become current by
  rebuilding a projection. The legacy recovery diagnostic is read-only and
  pinned to the authorized manifest.
- Missing explicit currency no longer skips official grounding. Resolve the
  authorized country default while continuing to verify product identity and
  comparison essentials; never fabricate a currency quote.
- Request identity, currency and comparison essentials, including their available
  alternatives, plus the current profile's optional fields and explicitly registered
  typed optional fields. Requiredness is the publication minimum, not a collection
  ceiling. Collect proven optional facts from supplied captures and official pages
  already consulted for the essentials. Keep complete financial conditions and
  field-level evidence; unknown or invalid optional facts are omitted.
- Optional information alone must not trigger extra searches, model calls, repairs
  or retries. Omit absent optional entries from AI output rather than generating
  verbose unverified placeholders. Required targets still report missing evidence.
  Optional omissions neither block an otherwise complete product nor create human
  review. Historical source lists cannot suppress current profile fields during
  extraction or normalization. Existing cache fingerprints invalidate changed
  prompts/field selection automatically.
- This optional-collection rule follows the Product Owner's subsequent 2026-10-01
  instruction and supersedes the earlier essential-only AI request economy rule.
  Field contracts, exact official proof and conditional publication gates remain
  unchanged. Additional proven output may use tokens; no token reduction is
  guaranteed. No live recollection or data mutation is part of this code change.
- Reuse a completed extraction grounding result only when the complete input,
  source/snapshot, parser chunks, allowlist/metadata, requested fields, model,
  relevant code and UTC date match. Reuse retained omissions too. A source has
  one private current cache entry under existing evidence retention. Provider
  errors and corrupt/mismatched caches fall back to ordinary grounded extraction.
- Fresh safe-fetch/capture remains ahead of parsing/extraction in the normal
  runner. Extraction must use that run's selected successfully parsed snapshot,
  never the latest unrelated historical parse. Reused facts still pass all gates.
- Preserve original run/model provenance and run-specific extraction artifacts;
  reuse does not invent a new provider request. Record zero new tokens on cache
  hits in bounded execution metadata. This is an application result cache, not
  a claim about provider prompt-cache billing. Dynamic normalization is separate.
- Bound recovery batches and do not repeatedly sample an unchanged failed source.
  The approved first batch checked 10 detail URLs and collected six once each.
  Future broad recollection should first resolve missing official currency/rate/
  condition documents, with explicit product applicability, rather than guess.
- A balance for waiving transaction charges cannot be stored as the general
  minimum balance or monthly-account-fee threshold. Omit that scalar when its
  exact meaning does not fit the field. Preserve the base transaction fee only
  under the existing adjacent-label contract.

See [the recovery result](../00-governance/collection-accuracy-recovery-2026-09-30.md).

## Current conservative limits

Only proven fact patterns are retained. Unsupported boolean wording, ambiguous
structured tables, compound contexts, and supporting-page evidence without a
resolved origin in the normalization input are omitted. This can exclude correct
facts; it must not be worked around by lowering a score or approving manually.
A future improvement should add bounded evidence resolution and adversarial
fixtures before extending supported patterns. Do not start unlimited paid
recollection to compensate for missing historical evidence.

## Deleting excluded non-products

Exclusion is not proof that a product can never be published. Do not delete a product solely because evidence is missing, a source is inactive/unreachable, or automatic validation fails. Under an explicit deletion authorization, remove only exact records with affirmative evidence that they are not individual in-scope products or have another conclusively established deletion basis. Preserve shared sources, recoverable products and private operation/rollback evidence. The 2026-10-01 authorized cleanup removed five non-product records; it does not authorize deletion of the remaining uncertain exclusions.

## Product Owner override: 2026-10-01

The Product Owner explicitly approved country currency defaults, reduced publication prerequisites, and restoration of excluded products that pass the new policy. This supersedes prior requirements to prove every product currency explicitly and older market-profile minimums. No human review is introduced.

| Product | Required comparison facts (CA and US) |
|---|---|
| Chequing/checking | Monthly fee and transaction cost structure: unlimited ordinary transactions, or finite allowance plus excess fee, or explicit per-use fee |
| Savings | Ongoing annual rate/APY and monthly fee |
| GIC/CD | Rate or valid term schedule, exact term, and explicit early-withdrawal access; permitted access additionally needs material consequences or explicit no penalty |
| Credit card | Annual fee and purchase rate (US qualified APR/range allowed) |
| Mortgage | Rate (US qualified summary), fixed/variable type and term |
| Personal loan | Rate/range and term |
| Line of credit | Rate/range and explicit secured/unsecured or collateral requirements |

Minimum balances/deposits, fee-waiver conditions and lending amounts/limits remain optional. The subsequent Product Owner instruction restores checking transaction costs, GIC/CD withdrawal access/consequences and line-of-credit security as conditional essentials. Missing optional facts do not block publication; invalid ones are omitted. They remain available in the shared collection field catalog. Core rate/fee/term conditions remain binding; no introductory, conditional, tiered or penalty value may be presented as an unconditional scalar.

Receipts now use `collection-accuracy-2026-10-01-cost-access` and market profile `2026-10-01-v7`. Older receipt digests remain compatible only when the payload also passes the current comparison requirements. New defaults carry a private `currency_basis` and mapping provenance. Neither provenance nor evidence is exposed through Public projections. Grounding-cache fingerprints include country-default code. `/healthz` exposes policy/profile versions to verify the serving runtime before restoring products. A stricter historical error state is not deleted to force acceptance; generate fresh candidates through normal normalization and automatic validation.

## Conditional cost/access/security essentials - subsequent 2026-10-01 approval

- CA and US checking: unlimited ordinary transactions do not require an excess fee. A finite included count (including explicit zero) requires an additional/per-transaction fee. Explicit per-use pricing can satisfy the structure without fabricating an included count. A fee solely for ATM, wire, international or e-transfer transactions cannot establish general account pricing. A count alone or `unlimited_transactions_flag=false` alone is insufficient. Contradictory unlimited/finite fields fail closed.
- CA GIC and US CD: explicit `redeemable_flag=false` or `non_redeemable_flag=true` establishes no access before maturity, so no separate penalty is required. Permitted access needs complete official withdrawal restrictions and a material penalty/lost-interest formula or explicit no-penalty statement in `early_withdrawal_penalty`. Numeric penalty amounts are not universally required. A penalty alone does not prove withdrawal permission; conflicting access flags fail closed.
- CA/US line of credit: a proven `secured_flag=false` is a valid unsecured fact. A security/collateral description must explicitly establish the requirement; generic approval language and optional/ambiguous security do not satisfy it. Conflicting alternatives fail closed.
- Extraction receives grouped alternatives and conditional requirements, not an instruction to fill every field. Missing essentials cause automatic exclusion; no human review or extra repair loop is introduced. Transaction fee fields remain native nonnegative money values and raw source-language withdrawal/security prose remains exact.
- Promotion, receipt compatibility and aggregate refresh enforce this contract. Public reads recheck the exact snapshot-pinned approved version for affected types so old projections cannot bypass it; country counts use the same eligible rows. Private payloads/receipts never enter responses. Checking costs and GIC access/consequences appear in shared catalog, detail, comparison and curated displays in EN/KO/JA.
- Code changes require API/worker and Public deployment. Read-only impact on the current 24 active products: 5 pass, 19 need more official evidence. No live canonical mutation or paid collection is part of this change. Existing versions remain preserved; deploy API first, then Public, and allow cache expiry. A later normal aggregate refresh applies the same gate without resetting verification dates.


## Public display of optional information - subsequent 2026-10-01 direction

Public lists, comparisons and Top 5 present current required decision facts.
Verified optional information belongs in detail; absent rows are omitted and
never filled with zero/false. Top 5 does not use optional coverage as a score or
eligibility prerequisite; actual known financial qualifications remain binding.
See [the presentation contract](product-grid-information-architecture.md).

## Supporting-document provenance - 2026-10-01 correction

Normalization retains official origins for supporting evidence selected by the existing product-specific merge/grounding paths. Before normalization, the repository loads only referenced chunks joined to this run's successful selected snapshot and parsed document. The URL comes from the stored source document, not extraction/model-provided URLs. The normalizer verifies chunk/document/snapshot, full text, run, bank and country before passing that origin to the unchanged shared accuracy gate. Missing or mismatched supporting origins remain excluded; unrelated source documents are never relabelled as the product detail.

The extraction artifact cannot populate the trusted origin map. The ordinary same-document path remains compatible, with matching snapshot required. Input expansion retains the map. Existing official-domain, actually-consulted URL, exact quote, product applicability, financial semantics and required-field checks remain binding. This change adds no requests to the collection model and does not broaden supporting-source selection. No accuracy/profile version or prompt change is needed because accepted financial patterns and extraction instructions are unchanged.

The corrected local worker restored the two prepared Scotiabank accounts through normal automatic gates. Future Admin collection requires deployment of the collection runtime/API package. Public reads use the existing compatible receipts and continue to hide private provenance. See [the operation and tests](../00-governance/supporting-evidence-recovery-2026-10-01.md).


## Exact checking account-fee rows - 2026-10-01 correction

The shared gate accepts a single exact multiline ordinary Transactions included per month row and Additional/Extra/Excess/Overage transaction fee row with a separately delimited native value. Label footnotes cannot become counts; LF and CRLF preserve row meaning. Conditional, duplicate, ambiguous or conflicting ordinary rows fail closed. Full captured context and existing official origin, exact quote, currency and applicability checks remain mandatory. Other ATM/e-transfer fees elsewhere in the same fee table cannot replace the adjacent ordinary price.

Only explicit ordinary unlimited wording proves account-wide unlimited transactions. Public transit, ATM, wire or e-transfer scope, including preceding/following qualifiers, cannot prove it. Excess-only pricing retains its distinct field. Matching extraction instructions preserve row line breaks and these distinctions; deterministic checking normalization and validation share the corrected accuracy gate. No publication essential, field type/unit or receipt/profile version changed; new code/prompt fingerprints invalidate unchanged-input extraction cache reuse as applicable.

The local corrected worker restored two hidden TD accounts through normal automatic gates. Public API is CA 11 / US 2; existing receipts remain compatible. Deploy the collection-runtime/API package to apply the shared correction to future Admin collection. See [operation and regression evidence](../00-governance/td-checking-recovery-2026-10-01.md).


## Separated card-offer eligibility and current annual rates - 2026-10-01 correction

A switch-from existing-card offer exclusion can be distinguished only when it precedes a separate Rates and Fees heading and an explicit current preferred annual Account-rate declaration. The bounded existing-card phrase and exclusion must match; any other from use remains conditional, including lower bounds and later periods. The rate section must also have no payment-provision, customer-only, conditional, default or penalty language for this exception. Entire original chunks and exact quotations remain; no qualifiers are removed. Unique scalar percentages, exact field labels, annual basis, currency, official origins and all other condition checks remain mandatory. Missing/ambiguous boundaries, conflicting or qualified rates fail closed.

Extraction and requested card-rate dynamic normalization share the same short instruction. Other dynamic prompts receive no additional card text. Existing field registration and required/optional policies remain. Current receipts keep the same policy/profile versions and types; cache fingerprints include changed code/instructions. The local corrected worker restored the verified Platinum card through normal automatic gates, with no model calls or human review. Deploy collection-runtime/API for future Admin collection. See [operation and regressions](../00-governance/platinum-card-recovery-2026-10-01.md).


## Bounded labelled current card rates — 2026-10-01

A complete explicit current preferred annual Account-rate declaration may prove distinct purchase and cash-advance percentages when each has its own label. Every percentage in the retained context must belong to that single declaration; additional/repeated rates, scalar ranges, conditions and missing annual basis remain excluded. Balance-transfer applicability needs its explicit inclusion. Preserve the full source context and official field proof through all normal gates. Shared extraction and requested card normalization instructions match.

The [14-card one-off batch](../00-governance/card-bulk-recovery-2026-10-01.md) produced two normal automatic passes and retained twelve exclusions, with no provider calls or weaker prerequisites. A direct evidence pass alone does not bypass subsequent normalization/validation. Code remains local; future runtime deployment is separate.


## Bound numeric context and current zero fees — 2026-10-01

Unchanged extracted numeric fields with a real chunk and full excerpt retain that bound context through normalization. Identical numbers in other chunks cannot replace their label/provenance/conditions. Missing bound evidence or changed/AI-introduced values still follow the existing lookup and final official accuracy gates; an unchanged value alone is not acceptance.

Future subject-to-change notices alone do not qualify an explicitly current fee. Actual payment, balance, eligibility or waiver conditions remain binding. First-year/month and introductory/promotional zero-fee contexts cannot prove an unconditional zero; absent information is never zero. Matching instructions reach extraction and requested fee normalization only. Required/optional contracts, receipt/profile versions, privacy and automatic exclusion remain.

The [remaining-card operation](../00-governance/remaining-card-recovery-2026-10-01.md) verified explicit personal Visa/Amex agreement family applicability for directly linked student variants and separate current Mastercard CAD settlement documents. Six of twelve cards passed normal current validation; six are retained exclusions. Future collection-runtime deployment remains separate from applied data.


## Separate offer revocation and numbered transaction notes - 2026-10-01

The exact Offer-revocation sentence for unmet Offer eligibility can be distinguished only before a separate line-start Rates and Fees heading and a complete current preferred annual card-rate declaration. Only that sentence's `if` is unrelated; all other rate conditions, ranges, percentages and conflicting declarations remain blocking. Full original evidence is retained. Explicit cash-advance parentheses may additionally name Scotia credit-card cheques alongside balance transfers and cash-like transactions; labels cannot be swapped. A later numbered note beginning `Transaction fees may apply when` describes a separate charge and cannot qualify the preceding rate. It does not establish a transaction fee or permission to omit an actual rate condition. Matching shared collection instructions and positive/adversarial regressions apply. Receipt/profile versions and publication prerequisites remain unchanged; future collection-runtime deployment is separate.

## Bounded checking rows, conditional zero and reference rates - 2026-10-01

One explicit `N Debits / Month` row proves its ordinary monthly included allowance only with the exact native integer count. Its immediately following monetary `each thereafter` price proves the distinct excess charge. Disclaimer numbers are not counts; duplicate rows, nonmonthly/range/conditional/special-channel contexts and competing unlimited statements remain rejected. Included allowance alone cannot publish checking without required excess cost.

Zero fees limited by fixed duration, age/graduation or average daily/monthly balance are conditional outcomes, not regular fees. Preserve a separately proven positive base fee and verified waiver conditions; never invent an unconditional zero. National/industry/market averages and competitor benchmark percentages are not the named product's own payable scalar rate. Full retained context and tightly selected quotations receive the same checks; borrowing examples remain insufficient current product-rate evidence. Shared instructions and adversarial/success regressions accompany all changes.

The [staged recovery](../00-governance/staged-unpublished-recovery-2026-10-01.md) published ten current automatic passes and removed 394 unsupported targets from the one-off work list, preserving canonical/history and registry. Receipt/profile versions, conditional essentials and public privacy remain unchanged. No permanent queue or recovery feature; future shared runtime deployment is separate.


## Verified optional checking interest - 2026-10-02 correction

CA/US checking includes optional standard/display deposit rates and the shared
typed deposit rate/calculation/payment/tier/promotion qualifiers. Current-profile
fields reach retrieval as well as official grounding and normalization, even
when older source lists omit them. Explicit field overrides remain bounded.
No optional-only search, model call, retry or review is added; publication still
requires monthly fee and transaction cost structure, not a rate.

A complete standalone annual deposit-rate declaration may distinguish a separate
explicit CDIC/FDIC insured-up-to line from a rate ceiling. Keep full original
context and every actual rate/eligibility/balance condition; combined, ambiguous,
conditional or competing-rate declarations remain excluded. Shared extraction
instructions match the shared accuracy gate. Deposit-interest fields reject
borrowing/overdraft and conflicting companion-account contexts in both heuristic
and official-model output. Exact quote, actually consulted official origin,
currency, annual basis, native types and automatic acceptance remain binding.

Saved Alterna detail evidence reproduces both the missing field request and
unrelated insurance-condition false rejection. Cross-market and adversarial
regressions verify the generic correction without bank exceptions. Worker/API
runtime deployment remains separate; no live rate was rewritten. See the
[diagnosis and verification](../00-governance/optional-checking-rates-2026-10-02.md).
