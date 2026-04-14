# Canada Big 5 Source Registry Baseline

Version: 1.0
Date: 2026-04-13
Status: Approved Implementation Baseline for WBS 5.1
Source Documents:
- `docs/02-requirements/scope-baseline.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/source-registry-refresh-and-approval-policy.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/00-governance/codex-internet-domain-allowlist.md`

---

## 1. Purpose

This document closes `WBS 5.1 Big 5 source registry` by defining the approved Phase 1 registry baseline for Canada Big 5 deposit products.

The baseline is designed to do three things:
- give `5.2`, `5.3`, and `5.4` a committed source set for parser expansion
- keep the active registry approval-first instead of letting discovery auto-expand scope
- make the current completeness cutline explicit so future enrichment work is easy to judge

---

## 2. Completeness Cutline

`WBS 5.1 complete` means the repo now contains an approved baseline registry for all `5` banks and all `3` in-scope product types:
- `chequing`
- `savings`
- `gic`

The baseline includes high-confidence public retail sources only:
- entry pages that enumerate the current consumer lineup
- product detail pages when a stable standalone public page exists
- shared rates, fees, or governing support pages needed for parser and validation follow-on work

This baseline does **not** claim that every future supporting PDF, campaign page, or edge-case legal artifact is already exhausted.
Those follow-on additions stay governed by the active-registry approval policy.

---

## 3. Inclusion Rules

Include only sources that are all of the following:
- public Canadian personal deposit-product pages
- on the official bank domain
- useful for canonical product identification, fee or rate extraction, or governing support
- stable enough to act as a repeatable seed for discovery or parser work

Allowed product boundary:
- Canada Big 5 only
- personal retail deposit products only
- Phase 1 product types only: `chequing`, `savings`, `gic`

Priority guidance:
- `P0`: entry, core detail, rate, fee, or governing support needed by the first parser pass
- `P1`: lower-priority but still in-scope public variants such as standalone USD savings pages

---

## 4. Exclusion Rules

Do not add the following to the active registry baseline unless separately approved:
- business banking pages
- authenticated flows
- open-account or application flows
- compare tools and recommendation flows
- promo-only landing pages
- registered-plan wrappers such as RRSP, TFSA, RESP, or FHSA packaging pages
- mortgage, loan, card, wealth-advice, or insurance pages
- third-party summaries or non-official sources

---

## 5. Registry Catalog

Canonical registry catalog:
- `worker/discovery/data/source_registry_catalog.json`

Registry files:

| Bank | Product Type | Registry File |
|---|---|---|
| RBC | chequing | `worker/discovery/data/rbc_chequing_source_registry.json` |
| RBC | savings | `worker/discovery/data/rbc_savings_source_registry.json` |
| RBC | gic | `worker/discovery/data/rbc_gic_source_registry.json` |
| TD | chequing | `worker/discovery/data/td_chequing_source_registry.json` |
| TD | savings | `worker/discovery/data/td_savings_source_registry.json` |
| TD | gic | `worker/discovery/data/td_gic_source_registry.json` |
| BMO | chequing | `worker/discovery/data/bmo_chequing_source_registry.json` |
| BMO | savings | `worker/discovery/data/bmo_savings_source_registry.json` |
| BMO | gic | `worker/discovery/data/bmo_gic_source_registry.json` |
| Scotiabank | chequing | `worker/discovery/data/scotia_chequing_source_registry.json` |
| Scotiabank | savings | `worker/discovery/data/scotia_savings_source_registry.json` |
| Scotiabank | gic | `worker/discovery/data/scotia_gic_source_registry.json` |
| CIBC | chequing | `worker/discovery/data/cibc_chequing_source_registry.json` |
| CIBC | savings | `worker/discovery/data/cibc_savings_source_registry.json` |
| CIBC | gic | `worker/discovery/data/cibc_gic_source_registry.json` |

---

## 6. Domain Boundary

Approved public-domain boundary for this baseline:

| Bank | Allowed Domain |
|---|---|
| RBC | `rbcroyalbank.com` |
| TD | `td.com` |
| BMO | `bmo.com` |
| Scotiabank | `scotiabank.com` |
| CIBC | `cibc.com` |

This keeps `WBS 5.1` aligned with the Codex internet allowlist baseline and the safe-fetch operating model.

---

## 7. Working Assumptions Locked For 5.1

- If a bank publishes a product family mostly through a strong entry page plus a rates page, that combination is acceptable for the `5.1` baseline even if parser-specific enrichment later adds more detail pages.
- Standalone foreign-currency savings pages may be included as `P1` when they are clearly part of the public personal deposit lineup.
- Existing TD savings registry remains the source of truth for the prototype slice and is preserved in place.
- Discovery and refresh runtime behavior is still strongest on the TD prototype path. Big 5 registry completion here is a data-and-governance baseline, not a claim that every bank-specific discovery rule is already implemented.

---

## 8. Verification Baseline

WBS `5.1` verification requires:
- all registry files load successfully
- the catalog covers `5 x 3 = 15` bank or product combinations
- each registry has a valid `entry_source_id`
- the worker test suite continues to pass with the new registry baseline present

---

## 9. Follow-On Work Unlocked

- `5.2` Chequing parser expansion
- `5.3` Savings parser expansion for non-TD banks
- `5.4` GIC parser expansion
- bank-specific discovery-rule hardening where entry or linked-document behavior differs from the TD prototype baseline
- candidate source promotion or deprecation under the registry refresh policy

---

## 10. Change History

| Date | Change |
|---|---|
| 2026-04-13 | Initial Canada Big 5 source registry baseline added for WBS 5.1 |
