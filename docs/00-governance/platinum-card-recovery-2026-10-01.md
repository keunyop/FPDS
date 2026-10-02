# Platinum card rate context and additional publication — 2026-10-01

## Outcome

Scotiabank Platinum American Express® Card was restored through fresh automatic validation and promotion. Verified current facts: CAD 399 annual primary-card fee and 9.99% preferred annual purchase interest rate. Public API now shows CA 12 / US 2, total 14. Actual card-list and detail pages show the card and its fee/rate. All nine actual API/BFF/deposit-list/card-list/detail checks passed after normal cache revalidation; all 13 previously public products are preserved.

Canonical totals: 428 products, 27 active / 401 inactive. Thirteen active records still fail Public prerequisites, hence 414 records remain unpublished. The original 355-product manifest is 27 active / 322 inactive / 6 deleted. No deletion was performed.

## Shared correction

The saved full official rate chunk reproduced a false exclusion: unrelated offer eligibility said existing cardholders who switch `from` an existing card are excluded. The blanket conditional-word detector treated that `from` as a qualified rate, although the following separately labelled Rates and Fees section explicitly declared the current preferred annual rates.

The shared gate distinguishes only this bounded structure: an existing-credit-card switch exclusion before a separate Rates and Fees heading and an explicit current preferred annual Account-rate declaration. Other `from` uses, including numeric lower bounds and later-period rates, still exclude. The exception also rejects payment-provision, customer-only, conditional, default and penalty language in the rate section. Existing full-context checks for unique scalar rates, labels, annual basis, currency, exact official quotes and all other conditions remain. Missing section boundaries, ranges, introductory/conditional rates and conflicting values fail closed. No evidence is shortened or rewritten to hide conditions.

Extraction uses the matching shared instructions. Dynamic normalization receives the same short rule only when the registered requested fields include a card rate; other product prompts receive no extra text. The normal field registry is unchanged: additional unregistered cash/transfer attributes remain suppressed by the existing product-type contract. No schema, UI, financial prerequisite, human review or permanent recovery feature was added. Receipt/profile versions remain `collection-accuracy-2026-10-01-cost-access` / `2026-10-01-v7`; financial types and serving compatibility are unchanged. Changed code/instructions participate in existing grounding-cache fingerprints.

## Economical operation

Replayed 15 saved card inputs without network fetches, provider calls or DB writes: exactly Platinum passed; the other 14 retained receipts excluded their purchase-rate mappings (`value_changed_after_grounding`). These dispositions establish neither current retirement nor a deletion basis.

Fresh preflight checked exactly three official sources: the Platinum detail, its linked credit-agreement scope page and linked 2025 revolving-credit agreement. The named Personal Credit Card Accounts listing links this exact Platinum detail, separately from the US Dollar product. The applicable American Express conversion clause proves CAD settlement; its full mixed-currency context and product applicability were preserved. The agreement hash remained pinned to the saved current document. The old 2022 amendment was not used as current rate evidence.

Normal execution rechecked those three sources, persisted current inputs and used repository-resolved current-run supporting origins. Provider calls were disabled for this bounded deterministic operation; normal field, accuracy, taxonomy, validation, promotion and aggregation gates remained. One completed run added one approved version and completed a CA aggregate refresh. Collection-model calls/provider tokens: zero; conversation token use was not measured. Run IDs and capture timestamps are UTC, while this report date follows the Product Owner's America/Vancouver date.

Independent DB readback and complete captured-evidence replay passed. Other 427 canonical records, four historical target candidates, previous target versions and registry are unchanged. No new reviews or started runs remain. Before-images, current inputs and full sources are private.

## Verification and runtime

- Before-fix regression reproduced the exact full-context failure. Focused rate/accuracy/cost/row tests: 37 passed, including LF/CRLF, current-rate positive, lower-bound/temporal/introductory/range/conditional/conflicting/payment/customer/penalty values, missing annual basis, receipt acceptance/exclusion and card-only prompt forwarding.
- Worker 605 / API 539 tests and repository doctor passed. Final diff/goal checks passed.
- All nine actual API/BFF/list/card/detail checks passed; private receipt/evidence text is absent from Public responses. The site detail visibly showed Annual fee $399 and Purchase interest rate 9.99%.

The corrected local worker completed the authorized data restoration against the verified compatible serving policy. Code deployment was not performed. Future Admin collection requires the collection-runtime/API build deployed. Public UI was unchanged.

Private artifacts: `tmp/card-rate-recovery-*`, `tmp/card-rate-retained-assessment.json`, focused/full test logs and doctor log. Never rerun completed execute.

Next separate slice: trace the other cards' purchase-rate mapping/value mismatches to preserved extraction/normalization inputs, then preflight only complete exact current evidence. Do not restore historical values to fill Public or pay for unchanged failures.
