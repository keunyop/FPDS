# Remaining-product recovery: CIBC and Scotiabank - 2026-09-30

Status: Data applied; independent DB/API/Public verification passed.

## Scope and selection

The Product Owner requested continued recovery. Inspected six CIBC credit cards
and five Scotiabank chequing products from the original authorized manifest.
Each bank was bounded separately. This is private one-off data work, with no
permanent feature, runtime change, deployment, human approval or registry edit.

CIBC was stopped after read-only preflight, before a collection run or model
call. Scotiabank's rehearsal accepted Basic Plus Bank Account and excluded four
candidates. Normal capture, parsing, sanitization, validation and automatic
promotion processed the five Scotiabank details plus two directly linked supports.

## Applied outcome

- Restored Basic Plus Bank Account, product `prod_Zh1bc0R9v40uyGIN`, version 11,
  candidate `cand-ed96096ea4d8e7ce`, event `pver_tNRBc97HJzsqOCst`.
- Verified native values: CAD, monthly fee 11.95, minimum fee-waiver balance
  3,000 and included transaction count 25. The balance is the monthly account
  fee-waiver threshold, not an opening deposit. Optional unproven facts are omitted.
- Five Scotiabank candidates ended with one automatic approval and four automatic
  exclusions. CIBC's six exclusions stayed in read-only diagnostics, without a run.
- Public API CA 5 / US 0. Of the original 355 products, 350 remain inactive.
  Across 434 canonical rows, only Basic Plus changed; 433 are unchanged, including
  all six CIBC products. Global inactive count is 429, including earlier rows
  outside the cutover manifest. Eleven original candidates and all registry rows
  remain unchanged. No new or pending human reviews.
- New collection model requests and input/output tokens: **0**. This excludes
  coding-assistant conversation, hosting and storage costs.
- Collection: `collection_lDVHj-0Hj5viX8dV`.
  Run: `run_20260930_184124_scotia_chequing_collect_-G20dp3g`.
  Aggregate: `agg_YdYdz1X2przB1Lza`, refreshed at 18:43:31Z.
- No runtime feature or deployment was added.

## CIBC: no paid retry of unsupported rate contexts

Fetched six current details, the catalogue, the agreements page and three linked
PDFs: the cardholder agreement, ordinary rate/fee summary and Costco summary.
The six cards are Aeroplan Visa Infinite Privilege, Aventura Visa Infinite
Privilege, Aventura Gold Visa, Dividend Visa for Students, Aeroplan Visa for
Students and Costco Mastercard.

Full-context reuse and a scan of current detail chunks produced zero acceptable
annual purchase-rate contexts for all six. PDF tables contain purchase, cash
advance, provincial and missed-payment rates together. Existing gates reject
those mixed contexts. Airline-reward currency statements do not prove the card's
currency. Do not crop competing rates/conditions out of evidence or pay for an
unchanged retry. This is an evidence-representation limitation, not a claim that
the bank lacks current published rates. No CIBC data or registry row changed.

## Scotiabank: exact applicability with complete source contexts

Preflight fetched five details, the comparison page, the catalogue, the current
[fees page](https://www.scotiabank.com/ca/en/personal/bank-accounts/fees.html) and
its directly linked banking companion booklet. The comparison/catalogue are not
needed in execution. The ordinary source plan retains five registered targets;
two directly linked documents are recorded as explicit temporary support sources
in the operation plan and captured normally. Neither support is a product, and
neither creates or changes a persistent source-registry row.

Only Basic Plus receives supplemental grounding:

- Exact detail H1 and links must identify Basic Plus and both supporting URLs.
- The fees table must have one exact Basic Plus row with its exact detail URL,
  the complete monthly fee/balance cell, and all remaining cells unchanged.
- The directly linked booklet states a default currency with an exceptions
  clause. Its exact Basic Plus column has no currency exception. All booklet
  bytes, including amendment pages, are pinned to the freshly inspected SHA-256
  `c28b464542d2234facf5b965e9681faf1927a9571583bd7524323e33c1bbc0b6`.
  A changed booklet fails the operation until applicability is checked again.
- Booklet currency and product-table pages 25 and 33 (one-based PDF pages) were
  checked, including table layout. Historical booklet prices never replace current
  detail/fee values. All financial amounts remain the existing native values.
- The existing 3,000 balance is re-grounded in the current linked Basic Plus fee
  row. The entire normal parser chunk, including nearby rows, remains intact;
  the unchanged shared sanitizer checks both quote and complete context.
- Fee, count and identity reuse requires the full historical context to match
  current detail evidence. Real document URLs/chunks and original candidate/model
  references are preserved. No supporting source is relabeled as a detail page.

The acceptance rehearsal passes Basic Plus only. Ultimate and Preferred lack
accepted current fee/transaction contexts; Basic lacks a proven minimum balance;
Student/Youth lacks accepted current identity/fee/transaction evidence. These
remain exclusions, with no human review. Support currency is not spread to
other products without a complete product-specific applicability check.

## Verification

- Nine safety cases passed: exact product binding; changed booklet; changed
  balance; wrong row URL; missing supporting link; native valid facts; changed
  full historical context; wrong evidence origin; numeric string rejection.
- Existing accuracy/maintenance regression suites: 29 tests passed.
- Independent DB checks recompute the receipt from three real evidence origins,
  verify native types and all before-images, and confirm zero review tasks and
  zero tokens across local normalization/validation records.
- At 18:49:30Z, ordinary API, Public BFF, list and detail URLs confirm CA 5 /
  US 0 and the restored product. Private receipts and evidence quotes remain
  absent. Normal cache revalidation took about six minutes.
- Repository doctor, final diff, UTF-8 and relative Markdown link checks pass.

Private evidence, scripts and before-images are under ignored
`tmp/oneoff-cibc-*` and `tmp/oneoff-scotia-*`. Never rerun the mutation entrypoint.
Preserve failures and missing-proof diagnostics to avoid unchanged paid retries.
