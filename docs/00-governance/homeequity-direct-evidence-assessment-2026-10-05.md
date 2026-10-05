# HomeEquity direct official evidence assessment - 2026-10-05

This is a feasibility investigation requested by the Product Owner, without
FPDS Admin API. No automatic approvals or publications are claimed.

## Preserved latest result

The October 5 batch started at 12:52 Vancouver time. GIC and Mortgage finished
with six successful source operations, two candidates, two automatic exclusions,
zero automatic approvals and zero review tasks. Recent candidate field metadata
was inspected in a repeatable-read/read-only database transaction; no writes.
GIC lacked standard rate/schedule and grounded access/consequences; CHIP lacked
an interest-rate summary. The original result remains unchanged.

## Current official inspection

- [GIC detail](https://www.homeequitybank.ca/products/gic/) contains five term
  columns and five payment-frequency rows, annual units, CAD-country context,
  a 5,000 minimum deposit, and a complete sentence prohibiting redemption before
  maturity except upon death of a registered owner. Do not discard the exception,
  mark ordinary redeemability true, assume no penalty, or select the highest
  term/payment rate as an unconditional standard rate. Web retrieval displayed
  October 5 effective rates (annual one-year 3.50%); the independent rendered
  capture displayed October 6 07:30 effective rates (annual one-year 3.58%).
  The client date is October 5. These inputs cannot establish one current rate;
  exclude future-effective values until current applicability is proven.
- The unchanged `quote_supports_value` function rejects the complete GIC access
  sentence for `redeemable_flag=false`, `non_redeemable_flag=true`, and as an
  `early_withdrawal_penalty` string. This demonstrates a bounded evidence-pattern
  gap, not an automatic pass or authorization to extend accepted patterns.
  Actual saved metadata had true/false access values, but they were omitted by
  grounding. No runtime change was made. Any correction needs regression evidence
  preserving the exception and all existing financial gates.
- [CHIP detail](https://www.homeequitybank.ca/products/chip-reverse-mortgage/)
  proves named identity, home security, fixed/variable options and reset terms.
  [Official posted rates](https://www.homeequitybank.ca/rates/chiprates/)
  expose numeric values only after browser rendering in this inspection:
  variable 7.11%, six-month 6.99%, one-year 7.59%, three-year 7.29%, five-year
  7.54%. The page explicitly limits these to rates applicable upon reset and
  preserves individual premiums/contract-number qualifications. APR is a separate
  column based on a 150,000 mortgage and closing costs; it is not the interest
  rate. These values support a qualified existing-customer reset schedule, not
  an unconditional new-origination offer.
- The detail directly links the official [CHIP new-origination rates](https://www.chip.ca/reverse-mortgage-rates/). Web retrieval has empty numeric
  placeholders and location/credit/offer conditions. One bounded browser attempt
  timed out. No current new-origination numeric rate was established; do not use
  old indexed blog figures or existing-customer reset rates to fill that gap.
- [Income Solution](https://www.homeequitybank.ca/products/income-solution/)
  provides a distinct named detail. Rendered [Income Advantage rates](https://www.homeequitybank.ca/rates/iarates/) provide numeric rate/term rows,
  but planned advances must remain variable and the lump-sum account has its own
  term structure. Income Solution/Income Advantage identity mapping and current
  offer/contract applicability require proof before producing a separate product.
- [Custom Solutions](https://www.homeequitybank.ca/products/custom-solutions/)
  describes use cases. Marketing purposes and rate-page variants alone do not
  establish additional independent priced products. No extra product count is
  inferred for CHIP Max/Open or the purpose-based pages.

## Verification and next step

Three official rendered HTML captures were obtained with the existing safe-fetch
browser fallback and parser, with timestamps/URLs/SHA-256 receipts. Independent
hash readback passed for all three. Private files are under
`tmp/homeequity-direct-assessment-20261005`; they are not Public evidence.
The fourth capture (CHIP new rates) timed out within the existing bounded fetch;
no broad retries or dependency installation were performed.

Concrete opportunities exist, especially CHIP's missing rendered rate evidence
and GIC's missing complete access/schedule interpretation. A successful count
requires current-applicability resolution and ordinary extraction, normalization,
validation and final promotion rehearsal. Neither a full service replay nor a
publication operation was performed. Do not report these as two proven approvals.

No paid model calls, Admin API calls, canonical/registry mutation, runtime fixes,
deployment, weakened essentials, or manual review. Documentation and final
whitespace/diff checks are the proportionate checks for this investigation.
