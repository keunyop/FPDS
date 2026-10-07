# Admin collection parity implementation - 2026-10-06

Status: P1-P4 common runtime implementation and local verification; P5/P6
preparation. Paid model experiments, deployment and live Public acceptance have
not been executed. This is a code result, not a National publication result.

## What changed

The [approved plan](../01-planning/admin-collection-publication-parity-plan-2026-10-06.md)
now runs on shared ordinary services. There is no bank-specific approval branch,
manual product review or permanent recovery workflow.

- Parser v13 decodes bounded literal CMS product maps without executing scripts.
  A local component alias and exact captured product identity bind flat keys to
  their own DOM. Unknown tokens, conflicting aliases/maps, duplicate keys and
  conflicting period units stay unresolved. Consent headings cannot identify a
  product; financial dialogs and conditions remain evidence.
- Product-owned term rows, explicitly named regular card PDF columns, exact
  referenced savings rate/fee notes and named GIC annual units are preserved.
  Investment horizon and redemption timing cannot become a contract maturity.
  A zero fixed monthly base fee cannot erase transaction/statement charges.
  Ambiguous reduced-rate fee rows are omitted instead of proving regular fees.
- Long native financial declarations survive the actual parse/chunk storage
  stage intact. A regression using the normal default 900-character limit first
  reproduced loss of the card's nine-month default/reset rule and GIC payout
  reductions, then verified their retention. The same records reach retrieval,
  extraction, stored artifact loading, normalization, current-run origin
  resolution, validation and automatic promotion gates.
- The planner may select an observed same-page render or current-snapshot
  reparse for an essential gap. Login/image templates cannot justify a render.
  No new source identity, guessed URL or optional-only research is introduced.
  The ordinary snapshot and parse workers execute the actions.
- Render failures make one attempt. SQL preserves only an already successful
  selection in this exact Run with matching source, snapshot and parse IDs;
  foreign/failed selections follow normal failure handling. The failed action
  remains visible in the private research receipt. Historical data is untouched.
- Actual typed optional cash rates, complete default conditions and calculation/
  payout conditions survive normalization. Source-proven values cannot be
  erased by a model rewrite or a final grounding result with no added facts.
- Normalization CLI emits field names and omission reasons. Private Run
  `collection_result` records extraction/normalization loss, validation source
  counts, actual promoted candidate counts and projection-launch state.
  `completed` remains a processing result; Public visibility stays `not_verified`
  until separate readback establishes it.

Current process version: `2026-10-06-admin-evidence-parity-v3`.
Existing required/optional policies, currency defaults, financial units,
accuracy/profile receipt versions, authentication, authorization and evidence
privacy remain in force. Changed proof/parser/chunk code participates in the
same-day grounding fingerprint.

## Bounds and failures

Two acquisition waves, two additional URLs per detail, 48 additional URLs and
eight link-planner calls per Run remain. Ordinary final grounding stays within
its existing single-pass/cache path. Browser attempts include automatic fallback
and forced renders: one per URL and at most 48 per Run across capture stages.
Initial browser usage is carried forward; the snapshot CLI accepts only a
remaining allowance from 0 through 48. Unknown failed-stage usage exhausts the
remaining render allowance conservatively. Reparse is once for an observed
snapshot/parser version. Preflight keeps direct HTTPS/URL checks and does not
spend another browser render on the same page.

No separate optional completeness calls, retries, model change, waiver of
checking costs/GIC access consequences/LOC security, or financial guesses were
added. Captures enter the existing allowlist/private-network checks and bounded
browser implementation. Browser availability or source failure can still cause
a correct exclusion.

## Fixed evidence acceptance

[Fixtures and immutable hashes](../../worker/pipeline/tests/fixtures/admin-collection-parity/sources.json)
retain 17 official National targets and matching public companion/rendered
captures. Reduced HTML keeps the original financial data/conditions. It contains
no internal candidate IDs, canonical records, provider secrets or operator notes.

| Target | Independently expected minimum |
| --- | --- |
| ECHO Cashback Mastercard | CAD 30 annual fee; 20.99% annual purchases |
| Platinum Mastercard | CAD 70 annual fee; 20.99% annual purchases |
| World Mastercard | CAD 115 annual fee; 20.99% annual purchases |
| World Elite Mastercard | CAD 150 annual fee; 20.99% annual purchases |
| High Interest Savings Account | 0.55% annual; zero fixed monthly base fee; daily calculation/monthly payment |
| Redeemable Plus GIC | 36 months; 0.30% annual base row; full/partial issue-anniversary redemption without penalty |

Card cash rates and the full default/payment reset conditions are retained.
GIC simple/compound payment wording includes the disclosed monthly 0.125% and
semi-annual 0.05% reductions; these do not become a new unconditional rate.
Months/years never become guessed day counts. HISA transfer/statement/debit costs
are not represented as zero by the base monthly fee.

The six priorities pass the ordinary stored snapshot/parse/extraction and
normalization artifact path, actual production origin-resolution query contract,
automatic routing and promotion checks. Database query results and canonical
write/refresh side effects are fixture-controlled: no real database mutation or
Public projection is claimed. The other eleven preserved targets stay excluded
under their supplied evidence, including missing LOC security/car-loan rate,
conditional rates, family/action identities and conflicting GIC boundaries.
All product-review task assertions remain zero.

## Verification

The full Worker suite passed 808 tests and the full API suite passed 631 tests.
Snapshot/runner CLI checks, changed-document links, harness prerequisites,
fixture JSON and git diff --check passed. The full repository doctor failed on
one pre-existing broken link in ignored `tmp/public-top5-20261004/app/README.md`;
that unrelated temporary artifact is unchanged. Detailed results are in the
[development journal](development-journal.md). The source-backed test is
[test_admin_collection_parity.py](../../worker/pipeline/tests/test_admin_collection_parity.py).
Additional tests cover alias/product/unit conflicts, no script evaluation,
render failure/provenance, unsafe URLs, concurrent render bounds, reparse without
fetch, field-loss receipt privacy and independent cache evaluation.

## P5 controlled model evaluation preparation

Ordinary callers keep same-day result reuse. The internal
`grounded_with_reuse(..., reuse_cache=False)` control calls the same extractor
without reading or writing its result cache; it returns the unchanged provider
receipt plus an evaluation input digest. It has no Admin setting/menu or
scheduler. Tests prove that independent repeats call the provider mock each time
and leave the ordinary cache unchanged.

For a separately scoped paid evaluation, pin raw capture hashes, chosen chunks,
field policy/schema, reasoning and actual configured model ID. First assess the
configured model against the fixed positive/negative set. A model-only comparison
uses three representative cases, two explicitly chosen models and three
independent final-grounding trials: at most 18 such calls, with each actual
provider receipt checked. Reuse captures, not model responses, for independence.
Do not infer the Codex model identity or compare differently acquired inputs.
Any normalization/planner calls need their own explicit call budget. Financial
truth and zero incorrect approvals take precedence over coverage scores.

## P6 release and live acceptance

1. Deploy matching API/collection runner and Worker code/dependencies. Check the
   health-reported process version, parser v13, browser executable and required
   PDF parsing dependency; a prior deployment report cannot establish this one.
2. Verify the new snapshot CLI allowance, failed-render current-selection SQL
   behavior and private Run receipts against the deployed database. Local tests
   exercise service/query contracts; live PostgreSQL writes have not been tested.
3. In a separately scoped fresh authenticated ordinary Admin Run, compare
   capture/chunk/extracted/normalized/validated values and field origins. Confirm
   the proven minima and material conditions; incomplete targets stay excluded.
4. Read actual canonical versions and promotion audit records, then aggregate
   refresh request/completion and the current country projection.
5. Check Public API list/detail and rendered values/conditions, zero product
   Review tasks and no private evidence exposure. Record approval and visibility
   counts separately. Until this readback, P6 remains open.

No fresh paid collection, model experiment, deploy, canonical/Public write or
change to historical review/cutover evidence occurred in this implementation.
