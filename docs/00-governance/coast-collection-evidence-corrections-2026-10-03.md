# Coast Capital collection evidence corrections - 2026-10-03

Status: local implementation verified; no deployment or live product writes.

The Product Owner requested corrections to confirmed Admin collection failures
and repeated verification. This is a code correction within current CA/US
collection: exact official facts, conditional financial essentials, automatic
exclusion, source ownership and private evidence remain mandatory. It adds no
manual review, permanent recovery feature, provider calls or registry overrides.

## Observed batch and reproduced defects

Read-only evidence pins the latest CCS batch, `collection_QBr7CMQ7AgnzgTQ8`,
started 2026-10-03 19:43 Vancouver. Its recorded outcomes are Chequing: three
candidates, two approved/one excluded; GIC: seven candidates, all excluded;
line-of-credit: one excluded; credit-card: skipped with no eligible detail.
Eighteen selected sources succeeded. No review tasks were created. UTC Run
identifiers use 2026-10-04. Those recorded results have not been rewritten.

| Product/path | Confirmed cause | Corrected local result |
|---|---|---|
| Free Chequing | Explicit base monthly fee zero rejected because a separate low-cost/no-cost classification contains `qualify` | Saved captured fee survives shared grounding, normalization and ordinary validation |
| 1 Year Redeemable GIC | Captured withdrawal access after 30 days and no penalty on payable interest omitted because consequence extraction demanded numeric penalty wording | Complete native withdrawal statement retained; ordinary automatic validation passes |
| 1 Year Better-than-Cash GIC | Detail alone does not retain complete interest-loss terms; linked family catalogue was not selected for essential evidence | Product's own named legal panel proves access and full loss-of-interest/minimum-redemption conditions; ordinary validation passes with that companion |
| Credit-card discovery | Product-labelled detail destinations occur in confirmation-dialog click handlers rather than ordinary anchors | Literal destinations recovered without executing JavaScript; current issuer-domain and detail-identity checks still apply |

Three focused tests failed before the correction. Stored original chunks and
model output reproduce the first two product failures. Better-than-Cash's original
detail remains excluded when the new companion is absent; the additional terms
come from the current official catalogue, not from inferred historic facts.

Official sources inspected and captured on 2026-10-03:

- [Free Chequing](https://www.coastcapitalsavings.com/everyday-banking/chequing/free-chequing).
- [1 Year Redeemable GIC](https://www.coastcapitalsavings.com/investments/gics/1-year-redeemable-gic).
- [1 Year Better-than-Cash GIC](https://www.coastcapitalsavings.com/investments/gics/1-year-better-than-cash-gic)
  and its linked [GIC catalogue](https://www.coastcapitalsavings.com/investments/gics).
- [Credit cards](https://www.coastcapitalsavings.com/everyday-banking/credit-cards).

## Shared correction and boundaries

The monthly-fee guard distinguishes only the evidenced, explicit separate
low-cost/no-cost service-classification phrases. It keeps original quotes and
rejects actual balance, eligibility, duration or waiver prerequisites. No new
zero fee or missing optional value is inferred.

Extraction preserves complete native withdrawal sentences, including any
preceding qualification and adjacent minimum-redemption restrictions. Explicit
no-penalty access after a waiting period does not establish access before that
period. A complete declaration of no interest paid upon redemption within a
specified period is a consequence even without a numeric penalty. Payment
frequency or an unspecified terms pointer remains insufficient. Distinct
conflicting consequence statements are omitted rather than choosing one.
Shared extraction/normalization instructions match these meanings.

Parser v8 preserves a `.flipper` component as an atomic
`product_terms_declaration` only with one nonempty native product title, one
attached Terms and Conditions panel and one unique detail destination. Grounding
requires exact target detail path, product identity and selected parent link,
plus current document/snapshot/parse/bank/country/language and approved origin.
Neighboring product panels cannot prove the target product. Relevant named terms
are prioritized within the existing 24-chunk/43,200-character grounding budget;
no note is truncated. Selected GIC details' explicit family-catalogue link may
become evidence-only within existing companion caps.

The common discovery parser reads only literal HTTPS destinations registered
on an existing confirmation button in one uniquely identified dialog. It ignores
comments, quoted script examples, dynamic expressions, unrelated scripts,
ambiguous destinations and duplicate button/dialog IDs. Existing discovery caps,
domain restrictions and safe fetch remain. No JavaScript is executed.

The current official card page yields five product-labelled links to four
distinct detail destinations. Its World-labelled link points at the Cash Back
card destination; the code preserves this evidence and does not invent a World
URL or identity. The batch also reports unsuccessful coverage-route verification
and no eligible detail. Discovering a URL does not verify issuer-domain authority:
Collabria still requires the existing verified cross-domain registry relationship.
The positive API test supplies that verified allowed domain; the negative test
with only Coast Capital's domain rejects it. No registry/domain boundary was
changed and no card approval is claimed.

## Verification

Source-backed public DOM/chunk/model-output fixtures are retained under
[Worker golden fixtures](../../worker/pipeline/tests/fixtures/golden/).
Operational DB/S3 snapshots and local verification logs remain private under
ignored `tmp/coast-corrections/`; they are not Public projections or source
transfer files. Runtime identifiers in the public fixture are scrubbed.

[Ordinary-service regressions](../../worker/pipeline/tests/test_account_redemption_evidence.py)
replay original model fields as a stubbed response, then run real
ExtractionService, provider-disabled NormalizationService and
ValidationRoutingService. Free Chequing and Redeemable GIC use their original
captured inputs. Better-than-Cash additionally uses the current native official
catalogue, parsed and bound by ordinary production services. All three finish
`auto_validated` with no review task. Removing that companion leaves
Better-than-Cash `excluded`. This proves evidence-to-gate behavior, not the yield
of a new paid model run or a newly published product.

Cross-bank CA/US positive and wrong-bank/country/snapshot/parse/product negatives,
conditional zero-fee cases, qualified/conflicting redemption statements, complete
redemption minimums, atomic panel isolation and companion-budget cases pass.
[Modal regressions](../../worker/discovery/tests/test_modal_product_links.py) and
[API planning/domain regressions](../../api/service/tests/test_collection_evidence_planning.py)
verify the actual official dialog fixture and boundary cases.

Final executed checks:

- Worker: `python -m unittest discover -s worker -p "test_*.py"`: 711 passed.
- API: API package environment, `python -m unittest discover -s tests -p "test_*.py"`: 580 passed.
- Final repository documentation/contracts and diff checks are recorded in the
  [development journal](development-journal.md).

## Rollout and limits

Deploy the API/source-catalog and Worker package together to apply source planning,
parser v8, shared financial guards and matching prompts to future Admin runs.
Existing input/code/parser/prompt fingerprints prevent inappropriate cache reuse.
No schema, policy/profile receipt version, Public UI or publication essential is
changed. Historical records remain intact; this task did not restart processes,
launch paid collection, change canonical/registry data or publish products.

The three-product replay does not declare every original GIC or LOC exclusion
resolved. Scalar rate/term comparability and explicit LOC security still require
current official proof. Card issuer-domain verification remains a separate
existing registry control. Deployment, any newly scoped collection, live
publication and independent Public readback are separate results.
