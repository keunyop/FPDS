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
  explicit ISO code or currency name in verified evidence; country defaults and
  an ambiguous dollar symbol are insufficient.
- Do not translate or paraphrase source-language product facts. UI labels may be
  localized. Do not infer false, zero, a currency, missing duration, a rate total,
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
| Money | finite nonnegative number | explicitly verified product currency |
| Count/duration | nonnegative integer | count or literal days; do not convert an ambiguous month to days |
| Boolean | boolean | explicit supported positive/negative statement; unknown is omitted |
| Product name/qualified description | string | exact source-language wording |
| Currency | string | verified ISO code |
| Term schedule | nonempty array of objects | `term_label` string, `rate` number; optional `term_length_days` integer, `minimum_deposit` number, `notes` string |

Unambiguous written counts from zero through ten may map to native integers
when directly attached to a transaction count; retain the exact source quote.
Ranges, alternatives, fractions and qualifying conditions remain ineligible.
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
   `collection-accuracy-2026-09-30`, bound to the exact identity and payload digest.
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

- Diagnose saved candidates/evidence against current gates before paying for
  recollection. A historical pass still needs current official-source identity
  and equality checks; an old verification timestamp cannot become current by
  rebuilding a projection. The legacy recovery diagnostic is read-only and
  pinned to the authorized manifest.
- No captured explicit supported currency means no official-grounding model
  call: the model cannot provide an exact currency quote that is absent. This
  preflight never establishes product ownership or proves the currency itself.
- Request identity, currency and comparison essentials, including their available
  alternatives. Retain existing annual/APY-basis and redemption qualifiers needed
  for Public comparisons, opportunistically from the same evidence. Optional
  descriptive fields do not justify model output or extra searches. Retain full
  evidence context and financial qualifiers.
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
