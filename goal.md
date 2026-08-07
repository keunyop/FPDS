# Goal: Generalize Collection Improvements From The JCBN Rerun

## Objective

Inspect every Run and Review Queue outcome from `collection_XbLwUNvRZiBfN1SC`, fix confirmed collection defects with reusable bank- and product-type-neutral rules, and verify the improvements through regression coverage and representative recollection.

## In Scope

- The six JCBN runs and all review tasks created by the replacement collection.
- Root-cause analysis across discovery, source scope, extraction, normalization, validation, auto-promotion, and residual Review AI.
- Narrow implementation changes that encode reusable evidence, product-boundary, field-contract, or lifecycle rules rather than JCBN-specific exceptions.
- Focused and boundary regression tests plus reruns of affected JCBN scopes.
- Auditable cleanup or supersession of review items only through existing guarded workflows when warranted by verified rerun results.

## Out Of Scope

- Bank-name, bank-code, or Chase-domain special cases unless an authoritative source-policy exception is unavoidable and explicitly approved.
- Inventing or force-approving financial facts.
- Widening countries, Product Types, publication scope, or BX-PF behavior.
- Modifying unrelated dirty-worktree changes.

## Acceptance Criteria

- Every failed/partial run and every review item from the target collection is classified as expected review, source limitation, or confirmed reusable defect.
- Confirmed defects are fixed without bank-specific shortcuts and have regression coverage for positive and safety-boundary cases.
- Relevant worker/API tests pass.
- Affected scopes are recollected and show the intended improvement without unsafe auto-approval or new source failures.
- Documentation records the behavior, verification, unresolved manual-review cases, and next action.

## Verification

- Compare original and post-fix run/source/candidate/review summaries.
- Inspect candidate payloads, validation issues, review diagnosis, evidence links, grounding executions, and source discovery metadata.
- Run focused tests, affected module suites, regression suites, and `git diff --check` in proportion to the final change.
