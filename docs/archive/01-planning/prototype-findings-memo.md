# FPDS Prototype Findings Memo

Date: `2026-04-11`
WBS: `3.10`
Status: `completed`
Primary evidence base:
- `docs/archive/01-planning/evidence/2026-04-11-first-successful-run/evidence-pack.md`
- `docs/archive/01-planning/evidence/2026-04-11-first-successful-run/validation-output.json`
- `app/prototype/viewer-payload.json`

## 1. Purpose

This memo closes the prototype learning loop after the first live end-to-end TD Savings run.

It is intended to:
- summarize what the prototype has already proven
- record the most important quality and scaling gaps
- recommend whether Gate B should pass now or wait
- translate prototype learnings into the next implementation priorities before Big 5 expansion

## 2. Executive Recommendation

Recommendation:
- treat the TD Savings prototype as `feasibility proven`
- treat Gate B as `Deferred` until the current `required_field_missing` validation gap is reduced to a level the Product Owner explicitly accepts

Reasoning:
- the prototype now proves source capture, snapshotting, parse/chunk, extraction, normalization, validation/routing, and viewer-based reviewability on live TD Savings data
- evidence linkage is real and reviewable for all three target products
- however, all three target candidates from the first successful run still land in `validation_status=error` with `validation_issue_codes=["required_field_missing"]`
- `docs/00-governance/stage-gate-checklist.md` says `Conditional Pass` is not the default gate mode, so the cleanest interpretation is not `Pass`, but `Deferred pending targeted hardening`

In short:
- the prototype succeeded as a technical proof
- it is not yet a clean Gate B pass as an operationally trustworthy canonical pipeline

Implementation note:
- subsequent hardening slices on `2026-04-11` cleared the original `required_field_missing` blocker in live reruns, added selective governing-PDF merge, and improved `TD Growth` qualification cleanup. This memo remains the factual interpretation of the first successful run evidence pack, not the later rerun state

## 3. What The Prototype Proved

The prototype successfully proved the following:
- live TD Savings source discovery works from the approved registry seed
- snapshot persistence works across HTML and PDF source types
- parse and chunk generation works across HTML detail pages, current-values HTML, and governing PDF sources
- field-to-evidence retrieval works well enough to support downstream extraction and viewer inspection
- extraction, normalization, and validation/routing all persist usable candidate records into the live dev database
- the static internal result viewer can display candidate state, validation issues, and evidence excerpts without requiring the future admin runtime
- all three target products appear in one end-to-end run:
  - `TD-SAV-002` `TD Every Day Savings Account`
  - `TD-SAV-003` `TD ePremium Savings Account`
  - `TD-SAV-004` `TD Growth Savings Account`

This means the repo has now cleared the main feasibility question behind the prototype: FPDS can create reviewable, evidence-linked candidate output from live bank sources inside the approved TD Savings scope.

## 4. Key Findings

### 4.1 Coverage And Evidence Trace Are Strong Enough

What went well:
- the first successful run covered the 3 target products and the required source-type mix
- sample evidence linkage is easy to explain to a reviewer
- anchors and excerpts are readable enough for human validation
- no stage failed in the `2026-04-11` end-to-end run chain

Why this matters:
- the core Evidence First principle is working
- later admin review and publish work has a real prototype baseline to build on

### 4.2 Canonical Completeness Is Not Good Enough Yet

Main issue:
- all three candidates in `run_20260411_3901_validate` were queued with `validation_error`
- the concrete issue code was `required_field_missing` for every target product

Interpretation:
- the pipeline is producing candidates, but not yet consistently producing sufficiently complete canonical candidates under the current validation rules
- this is the main blocker for calling the prototype a clean operational pass

Product impact:
- a reviewer can inspect the candidates
- a downstream publish path should not trust them yet without manual review or targeted normalization improvement

### 4.3 Extraction Is Useful But Still Noisy

Observed pattern:
- fee and simple numeric fields such as `monthly_fee` are often extracted well
- long-form fields such as `eligibility_text`, `fee_waiver_condition`, `notes`, `transaction_fee`, and some rate-related text are still noisy or overly broad
- some fields are filled with nearby descriptive text rather than narrowly-scoped canonical meaning

Examples from the live viewer payload:
- `TD Every Day` correctly shows `monthly_fee=0.0` and cites `Section account-fees`
- `TD ePremium` correctly captures strong interest-calculation evidence but still carries noisy `eligibility_text` and fee-related text
- `TD Growth` shows meaningful boosted-rate evidence but still mixes supporting narrative into canonical fields

Interpretation:
- the current heuristic baseline is good enough for evidence-supported review
- it is not yet good enough for broad auto-trust or Big 5 scaling

### 4.4 TD Growth Is The Highest-Risk Prototype Product

Why:
- `TD Growth Savings Account` contains boosted-rate qualification logic
- that logic depends on behavioral and cross-account conditions, not just a flat fee or flat rate statement
- the current pipeline can capture and cite the relevant section, but the resulting canonical mapping remains coarse

What was proven:
- the viewer shows grounded evidence for boosted-rate eligibility from `Section boosted-rate-eligibility`
- reviewability for this special case is acceptable

What is still weak:
- special-case normalization rules for boosted-rate eligibility are not explicit enough yet
- the current canonical output does not cleanly separate base product facts from qualification logic

Interpretation:
- Growth should remain the reference special case for future rule hardening
- if FPDS cannot normalize Growth-like cases more cleanly, Big 5 expansion will accumulate reviewer burden quickly

### 4.5 Supporting-Source Merge Is Still Incomplete

Current state:
- the first successful run included `TD-SAV-005`, `TD-SAV-007`, and `TD-SAV-008` in snapshot and parse coverage
- however, candidate-producing extraction and normalization still primarily work product-by-product from the three detail pages

Why this matters:
- real bank product truth is often split across:
  - detail page
  - current values page
  - fee PDF
  - interest calculation PDF
- without stronger supporting-source merge logic, some required canonical fields will remain missing or weakly inferred

Interpretation:
- this is likely one of the main reasons the current run still ends in `required_field_missing`
- Big 5 expansion should not start before the repo has a clearer multi-source merge strategy

### 4.6 Discovery Noise Is Manageable But Needs Better Reviewer Framing

Observed pattern:
- discovery warnings were high because TD pages expose many `out_of_registry_link` and `cross_domain_link` references

Interpretation:
- this is expected under the approval-first registry policy
- it is not the main prototype blocker
- but it will create reviewer fatigue unless warnings are summarized and categorized more cleanly

Recommendation:
- treat this as a hardening and observability issue, not as a core prototype failure

### 4.7 Rerun Hardening Is Still Missing

Current state:
- the prototype now has one successful live run with evidence pack
- this is enough to prove feasibility
- it is not enough to claim stable repeatability

Risk:
- source drift, extraction heuristics, and registry refresh noise can still affect rerun consistency

Interpretation:
- rerun hardening remains a `P1` follow-up
- it should not block the memo itself, but it should block any claim that the current pipeline is already durable enough for broader bank rollout

## 5. Source-Specific Assessment

### 5.1 TD Every Day Savings Account

Strengths:
- fee extraction is strong
- included/additional transaction evidence is understandable
- monthly fee evidence is clean and reviewer-friendly

Weaknesses:
- some supporting descriptive fields are broad
- at least one required canonical field is still missing under current validation rules

### 5.2 TD ePremium Savings Account

Strengths:
- product identity is clear
- high-interest tier positioning is visible
- interest-calculation evidence is one of the stronger prototype examples

Weaknesses:
- fee and eligibility-related long text is still overly broad
- supporting-source merge is likely needed to close the remaining required-field gap cleanly

### 5.3 TD Growth Savings Account

Strengths:
- special-case eligibility evidence is captured and reviewable
- boosted-rate qualification can be explained to a human reviewer from the current viewer

Weaknesses:
- special-case normalization is not mature enough
- the product is the clearest sign that rule quality must improve before expansion

## 6. Big 5 Expansion Readiness

Current recommendation:
- do not begin Big 5 product expansion yet

Why not:
- the prototype proves architecture direction and evidence-grounded reviewability
- it does not yet prove that canonical completeness and field precision are stable enough to scale source count, bank variation, and reviewer load

What is ready for reuse:
- discovery, snapshot, parse/chunk, evidence linkage, validation/routing, and viewer scaffolding
- registry policy direction
- object-storage and DB persistence structure

What is not ready for reuse at scale:
- supporting-source merge
- special-case normalization rules
- field-level precision for long-form text fields
- rerun hardening and reviewer-facing warning summarization

## 7. Recommended Next Work Before Big 5

Priority order:

1. Improve required-field closure for the three TD target products.
   Focus on the exact fields now failing validation and make the pipeline produce clean pass-state candidates or clearly justified manual-review-only candidates.

2. Add stronger supporting-source merge logic.
   Product detail, current values, and governing PDFs should contribute to one candidate more deliberately instead of only coexisting in upstream evidence coverage.

3. Harden special-case normalization around `TD Growth`.
   Separate base facts, qualification logic, and promotional or conditional text more explicitly.

4. Tighten extraction for noisy text fields.
   Reduce over-broad passages in `eligibility_text`, `fee_waiver_condition`, `notes`, and related fields.

5. Add lightweight rerun hardening.
   Run at least one repeat end-to-end validation pass, record drift behavior, and document expected reuse versus reparse behavior.

6. Improve warning summarization for discovery and preflight.
   Keep the approval-first registry policy, but reduce operator noise in evidence and viewer surfaces.

## 8. Gate B Recommendation

Recommended gate decision:
- `Deferred`

Recommended summary for the future Gate B note:
- FPDS prototype feasibility for TD Savings is proven
- evidence-linked reviewability is proven
- Big 5 expansion should wait until required-field completeness and supporting-source merge quality improve

What would justify moving from `Deferred` to `Pass`:
- the three prototype target products no longer all fail with `required_field_missing`, or
- the Product Owner explicitly accepts the remaining gaps as within prototype acceptance after reviewing this memo and the evidence pack

## 9. Conclusion

The prototype did its job.

It proved that FPDS can ingest live TD Savings sources, preserve evidence lineage, produce reviewable candidate output, and surface the result in a reviewer-friendly viewer. That is a meaningful milestone and materially lowers implementation risk.

The main remaining issue is not feasibility. It is quality closure.

Before the team expands to Big 5 coverage, the pipeline should close the current required-field gaps, merge supporting sources more intentionally, and harden the Growth-style special-case rules. Once those are addressed, the prototype foundation should be strong enough to support the next stage with much lower ambiguity.
