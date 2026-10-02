# Alterna latest collection diagnosis - 2026-10-01

Read-only investigation requested by Product Owner. No recollection, model calls,
canonical mutation, publication, runtime changes or deployment performed.

## Verified result

Collection `collection_iJK70IIxRhEDj-xd` created four runs, all completed between
2026-10-01 23:29 and 23:40 America/Vancouver (2026-10-02 06:29-06:40 UTC).
Eleven source operations succeeded, zero failed. Four candidates, four automatic
exclusions, zero accepted candidates and zero human review tasks.
Live CA Public API returned 29 products and zero ALTERNA products; all seven
retained ALTERNA canonical records are inactive. This is exclusion before
publication, rather than a Public cache or rendering-only failure.

| Product | Required facts not accepted | Observed diagnostic |
| --- | --- | --- |
| No-Fee eChequing Account | Monthly fee, unlimited ordinary transactions | Official grounding rejected field meaning; candidate fee mapping retained heuristic 2.50 without official grounding. This is not an accepted monthly price. |
| High Interest eSavings | Standard rate, monthly fee | Rate quote failed exact-quote matching; fee zero passed initial grounding but full-context validation reported ambiguity. |
| eTerm Deposits | Rate, term, redemption access and early-withdrawal consequence | Grounding reports blank rate placeholders in supplied table evidence, and other required facts unverified. |
| Personal Loan | Interest rate summary | Grounding reports fixed rates and 1-5 year term, but no numeric rate/APR. |

Account source-processing issues warrant focused reproduction before any paid
retry. Savings retained evidence explicitly says there are no monthly fees and
no minimum balance required; yet the monthly fee was omitted as
`evidence_context_ambiguous`. Its runtime extraction notes mention 1.05%, but
that value failed exact-quote verification and is not an accepted financial fact.
Chequing grounding notes likewise describe no monthly fee and free unlimited
day-to-day transactions while rejecting those fields as `field_meaning_unproven`.
These inconsistencies suggest overly narrow field-meaning/context acceptance or
quote/chunk mapping, rather than proving that the bank lacks those facts.
The exact implementation fix has not been reproduced/tested in this read-only
slice. Existing deployment-pending notes alone do not prove which build ran.

## Evidence and next step

Private `tmp/alterna-latest-diagnosis.json` preserves latest runs, candidates,
model metadata and canonical status; `tmp/alterna-latest-field-evidence.json`
preserves retained evidence; `tmp/alterna-latest-public.json` preserves Public
readback. Source content and model rationale were treated as evidence, not
instructions; model rationale alone cannot authorize acceptance.

Next implementation slice: replay the two account failures against the exact
saved extraction/chunks with positive/adversarial regressions, fix only proven
mapping/meaning defects, then separately deploy the collection runtime. GIC needs
usable captured rate/access evidence; loan remains excluded without applicable
comparison-rate evidence. Do not bypass gates or publish heuristic values.

Verification: DB repeatable-read/read-only transactions, exact latest candidate
receipts, source/model stage metadata, field evidence, and serving Public API.
No application suites required or run because no runtime behavior changed.

## Authorized follow-up: account validation fix

Product Owner requested proceeding with the proposed saved-evidence reproduction
and implementation. Scope excludes deployment, recollection, canonical writes
and publication; original diagnosis above remains historical.

Before implementation, the new regression module produced three failures and
one missing-fee error: full savings context, checking no-fee/no-balance quote,
and ordinary day-to-day unlimited meaning failed. Exact captures showed the
balance condition classifier matching `minimum balance` inside `no minimum
balance required`. The ordinary unlimited pattern omitted `day-to-day`.

Corrected the shared classifier to distinguish that exact explicit absence while
retaining all actual balance/duration/eligibility conditions and rejecting
negated/hypothetical absence. Added `day-to-day` to ordinary transaction meaning
and kept channel restrictions for all admitted modifiers and footnote positions.
Extraction and dynamic normalization use one shared account-cost instruction.
No annual-rate, exact-quote, official-origin, native-type, required-field or
receipt-version change, and no exemption for heuristic fields.

Eight regression tests cover actual captured context, extraction meaning,
automatic checking/savings gates, condition/channel/count/negation boundaries,
missing grounding and invented short-rate context. Actual stored extracted.json
files were read from existing private storage and replayed through normal
`_normalize_candidate` plus `sanitize_candidate`, with provider calls disabled
and no DB persistence:

- Savings: monthly fee 0 and its display alias now retained; standard_rate
  remains missing because prior exact-quote failure left only a heuristic value.
- Checking: the explicit fee/unlimited phrases now pass field-meaning tests,
  but the stored extraction already discarded their official verification and
  retained an unrelated overdraft fee 2.50 heuristically. Replay still excludes
  it; no invented official mapping or model-response reconstruction was used.

The saved source percentage is an isolated `1.05%*` chunk. Model rationale is
not the missing exact quote/verified mapping; annual basis and rate remain
mandatory. This slice does not claim that a future collection will publish
both products. Applying the local fix requires separate runtime deployment;
then a bounded normal collection must establish remaining essentials.

Private `tmp/alterna-account-offline-replay.json` preserves exact replay receipts;
`tmp/alterna-account-chunks.json` and account extracted files preserve inputs.
Worker/API suites and focused regressions are recorded in the journal. Public
status was not changed. No new review, paid call or permanent recovery feature.
