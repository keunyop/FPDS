# FPDS RAID Log

Version: 2.0
Date: 2026-04-22
Status: Active current baseline
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/working-agreement.md`

---

## 1. Purpose

This file keeps only the active risks, assumptions, issues, and dependencies that still matter for current execution.

Rules:
- keep it short and current
- remove closed items once they stop shaping execution
- avoid turning this file into a full history dump
- use the development journal for slice-level detail

---

## 2. Current Risks

| ID | Priority | State | Risk | Current Response | Owner |
|---|---|---|---|---|---|
| R-001 | High | Open | Bank source structure varies by bank and product type, so extraction and normalization quality can still drift across expansions. | Keep evidence-first review fallback, source-specific hardening, and schema-aligned validation active. | Tech Lead, AI/Data |
| R-002 | High | Open | PDF-heavy sources can still produce unstable parse quality and weak field extraction. | Preserve raw artifacts, keep supporting-merge and manual review options available, and verify PDF-heavy banks explicitly. | AI/Data |
| R-003 | High | Open | BX-PF environment or contract readiness can still delay true publish readiness. | Keep interface-first behavior, mock-safe dev posture, and explicit pending or retry semantics until live readiness is confirmed. | Product Owner, Backend |
| R-004 | Medium | Open | Public aggregate refresh, snapshot freshness, and canonical truth can drift if queue or retry behavior regresses. | Keep dashboard health visibility, retry flow, and latest-successful serving fallback in place. | Backend |
| R-005 | Medium | Open | LLM, browser automation, and source collection costs may grow faster than expected during Big 5 hardening. | Use usage dashboard signals, bounded collection behavior, and targeted reruns instead of broad reruns by default. | Product Owner, Backend |
| R-006 | High | Open | Delivery capacity remains tight relative to ongoing data, UI, QA, and docs work. | Keep slices small, protect scope boundaries, and avoid reopening settled baselines without clear value. | Product Owner, Tech Lead |

---

## 3. Current Assumptions

| ID | Priority | State | Assumption | What Still Needs Validation | Owner |
|---|---|---|---|---|---|
| A-001 | High | Monitoring | Canada Big 5 deposit products remain a realistic Phase 1 coverage target with the current registry-driven approach. | Continued bank-by-bank collection and parser hardening. | Product Owner, AI/Data |
| A-002 | Medium | Monitoring | EN/KO/JA public and admin UI remains supportable within current team capacity. | Ongoing translation, QA, and copy ownership pressure as public scope grows. | Product Owner |
| A-003 | Medium | Monitoring | Shared filter vocabulary between Product Grid and Insight Dashboard remains usable as scope grows. | Continued UX validation as more product types and edge cases accumulate. | Frontend, Product Owner |
| A-004 | High | Open | BX-PF will remain the intended target store for approved normalized products in Phase 1. | Contract, environment, and real write readiness. | Product Owner, Tech Lead |

---

## 4. Current Issues

| ID | Priority | State | Issue | Current Impact | Next Action | Owner |
|---|---|---|---|---|---|---|
| I-001 | High | Open | Some source-specific gaps still remain after orchestration hardening, including known bank-page validation misses. | Individual banks can still land in review with real data-quality gaps after collection succeeds. | Fix bank-specific extraction or supporting-merge gaps one reproducible case at a time. | AI/Data, Backend |
| I-002 | Medium | Open | Historical migrations still seed some baseline rows on a fresh database even though runtime reseeding was removed. | Resettable runtime behavior is fixed, but fresh-DB bootstrap behavior is still broader than some operator reset cases. | Decide explicitly whether fresh databases should also start empty before changing migrations. | Product Owner, Backend |
| I-003 | Medium | Open | Several active governance docs outside this slice still contain old encoding or readability problems. | Some startup docs are harder to inspect from the shell than they should be. | Clean remaining active docs in later docs-hygiene slices. | Tech Lead |

---

## 5. Current Dependencies

| ID | Priority | State | Dependency | Impacted Work | Current Handling | Owner |
|---|---|---|---|---|---|---|
| D-001 | High | Monitoring | BX-PF access, contract confidence, and production environment readiness | publish readiness, Gate D, release operations | Keep Phase 1 work interface-first until live readiness is explicit. | Product Owner, Backend |
| D-002 | High | Monitoring | Stable access to bank websites and PDFs | collection quality, parsing, evidence capture | Keep bounded fetching, registry governance, and source-specific hardening active. | AI/Data |
| D-003 | Medium | Open | Domain review bandwidth for taxonomy and field interpretation edge cases | normalization quality, validation rules, public semantics | Escalate only when bank-specific ambiguity blocks canonical decisions. | Product Owner |
| D-004 | Medium | Open | Phase 2 external API policy and tenant model remain undecided | later API work only | Leave this closed out of current Phase 1 implementation unless scope changes. | Product Owner, Backend |

---

## 6. Review Rule

Review this file when:
- a risk becomes release-relevant
- a long-lived issue starts blocking active WBS work
- a dependency changes stage readiness
- a supposedly closed item becomes active again

If an item is no longer shaping decisions, remove it.

---

## 7. Change History

| Date | Change |
|---|---|
| 2026-04-22 | Rewrote the RAID log as a short current-baseline document and removed stale closed design-stage items from the default path |
