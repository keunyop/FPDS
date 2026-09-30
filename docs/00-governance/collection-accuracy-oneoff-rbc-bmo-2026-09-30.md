# Remaining recovery: RBC and BMO - 2026-09-30

Status: Read-only recovery assessment completed; no additional restoration.
Shared zero-value validation fix implemented and tested; runtime deployment pending.

## Outcome

- Inspected six RBC and five BMO inactive manifest products. BMO has two legacy
  Performance records referencing the same source/candidate: 11 products cover
  ten unique detail URLs. Six supporting sources were also freshly fetched.
- Full-context reuse through the unchanged acceptance flow produced no complete
  eligible candidate. No collection run, candidate write, model request, human
  review, registry edit or canonical mutation was performed.
- Public remains CA 5 / US 0; 350 manifest products remain inactive. Independent
  DB readback confirms the selected products and ten historical candidates are
  unchanged. All registry rows match the previous verified before-image.
- All five active products were re-evaluated from their actual approved candidates
  and persisted evidence using the corrected validator. All still pass.
  Ordinary API, Public BFF and list reads confirm five products without private
  receipts or quotations. There are no running ingestion jobs or pending reviews.
- New collection model requests and input/output tokens: **0**. This excludes
  coding-assistant conversation, hosting and storage costs.

## Evidence findings

RBC targets: Advantage for students, Signature No Limit, U.S. Personal, Day to Day,
VIP and Advantage. Supporting sources: the registered account disclosure booklet,
interest-rate page and chequing catalogue. The current Advantage page identifies
its own base monthly fee as 12.95; the saved 16.95 value appears in Signature No
Limit cross-selling content. The historical value was not reused or silently
corrected. The broader batch lacks complete current identity/currency/essential
proof within the retained contracts. Generic companion-account CAD/USD mentions,
foreign-exchange clauses and savings-account minimums were not borrowed.

BMO targets: Premium, Performance (two historical records), Plus and Blue Rewards.
Supporting sources: registered agreements/fees and global terms pages, followed
by the directly linked banking agreement PDF. The PDF redirects to the current
Agreements_Bank_Plans_and_Fees_for_Everyday_Banking.pdf. Current page contexts mix
plan comparisons and currencies; old full contexts no longer match. Plan bundles
can contain both CAD and USD accounts, so a country default cannot prove currency.
No duplicate Performance product was restored and no conditional bonus balance
was turned into a general minimum balance.

## Demonstrated common defect and minimal correction

A real Blue Rewards chunk contains a 4,000 balance for bonus points and a separate
family no-fee benefit. Before the fix, the shared validator accepted zero minimum
balance from that complete chunk because any nearby 'no fee' or 'no minimum'
phrase could prove zero for any money field. The same error affected minimum
deposits and different kinds of fees.

The common quote validator now requires the negation to name the same financial
attribute: monthly fee, annual fee, transaction fee, minimum balance or deposit.
Explicit numeric zeros still pass their existing adjacent-label checks. Native
value types, full-context checking, units, currency, conditions and automatic
exclusion remain required. This is a demonstrated accuracy defect fix, not a
new recovery feature or an expansion of accepted financial meaning. Existing
extraction/normalization instructions already prohibit inferred or changed facts;
no new model prompts, model calls or model configuration were needed.

Key files:
- worker/pipeline/fpds_collection_accuracy.py
- worker/pipeline/tests/test_collection_accuracy.py
- docs/03-design/collection-accuracy-policy.md

## Verification and continuation

- Two new tests reproduced five failures before the fix, covering cross-attribute
  zero claims and end-to-end candidate exclusion; both pass after the fix.
- Accuracy/maintenance suites: 31 tests passed.
- Worker full suite: 571 tests passed. API full suite: 535 tests passed.
- Live evidence replay: all five active products still pass, no data writes.
- Repository doctor, foundation baseline, final diff, UTF-8 and relative
  Markdown link checks passed.

The fix must reach the collection runtime for future collection to use it.
No deployment was performed. No existing product needs deactivation due to this
specific correction. Continue with new source evidence or a separately evidenced
common parsing/grounding defect; do not resend these unchanged inputs to a model.

Private source captures, assessment and live/public readbacks are under ignored
`tmp/oneoff-rbc-*`, `tmp/oneoff-bmo-*` and `tmp/oneoff-rbc-bmo-*`.
