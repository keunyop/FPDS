# FPDS Decision Log

Version: 2.0
Date: 2026-04-22
Status: Active current baseline
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/00-governance/working-agreement.md`

---

## 1. Purpose

This file keeps the current decisions that still shape active implementation work.

Rules:
- keep only decisions that still matter for current execution
- do not use this file as a full historical archive
- move old gate and prototype context to `docs/archive/`
- update this file when a decision changes current execution, scope, architecture, or release posture

---

## 2. How To Use

Use this document to answer:
- what FPDS is currently trying to build
- what the approved technical and delivery baseline is
- what boundaries must not be reopened casually
- what decisions future slices should assume by default

If a topic is not covered here, follow document authority:
1. latest Product Owner instruction
2. requirements
3. plan
4. WBS
5. this decision log
6. RAID log
7. detailed design docs

---

## 3. Current Decisions

| ID | Date | Area | Decision | Why It Matters | Source |
|---|---|---|---|---|---|
| D-001 | 2026-03-28 | Product Boundary | FPDS is a financial product data platform, not a consumer recommendation service. | Keeps scope centered on evidence, canonical data, reviewability, and publish readiness. | PRD, scope baseline |
| D-002 | 2026-03-28 | Delivery Stages | Delivery remains split into `Prototype`, `Phase 1`, and `Phase 2`. | Prevents Phase 2 work from leaking into current implementation by default. | PRD, plan |
| D-003 | 2026-03-30 | Prototype Scope | The prototype boundary was `TD Bank + Savings Accounts` only and is now historical. | Confirms that prototype docs are archive material, not current planning authority. | `docs/archive/01-planning/*` |
| D-004 | 2026-03-30 | Phase 1 Scope | Phase 1 scope is Canada Big 5 deposit products plus public grid, insight dashboard, admin console, and BX-PF connector readiness. | This is the active product boundary for current implementation. | scope baseline |
| D-005 | 2026-03-30 | Non-Goals | Personalized recommendation, public evidence exposure, billing, and broader expansion remain out of scope. | Guards against scope creep during WBS 5 work. | scope baseline |
| D-006 | 2026-03-30 | Build-Start Rule | Build start requires `Gate A Pass + Product Owner explicit approval`. This has already been satisfied for current implementation. | Remains important as the rule for future stage transitions and any new gated work. | scope baseline, stage-gate checklist |
| D-007 | 2026-04-07 | Language Baseline | Product code uses `Python` primarily, and browser-facing surfaces use `TypeScript`. | This is still the working language split across worker, API, admin, and public UI. | README, WBS |
| D-008 | 2026-04-07 | Runtime Baseline | Frontend runtime is `Next.js App Router`, API runtime is separate `FastAPI`, worker runtime is a separate Python worker process, frontend package manager is `pnpm`, and Python manager is `uv`. | This is the approved implementation shape and should not be casually reopened. | README, WBS |
| D-009 | 2026-04-07 | Auth Baseline | Admin auth uses server-side session auth managed by the Python API. | This remains the baseline for admin runtime work and route protection. | security design, README |
| D-010 | 2026-04-07 | Environment Baseline | Official env model remains `dev` and `prod`, with real BX-PF write-back allowed only in `prod`. | Keeps env and secret handling consistent across active slices. | env spec |
| D-011 | 2026-04-07 | Data and Evidence Baseline | Evidence artifacts stay private, browser surfaces never get direct raw object access, and canonical truth stays separate from public projection or publish state. | Protects evidence boundaries and keeps public serving decoupled from internal storage. | storage baseline, workflow design |
| D-012 | 2026-04-11 | Gate B Outcome | Gate B passed and the prototype stage is complete. | Confirms prototype planning and evidence docs are archival by default. | `docs/archive/00-governance/gate-b-prototype-review-note.md` |
| D-013 | 2026-04-12 | Admin Account Baseline | Admin runtime starts from DB-backed operator accounts and DB-backed sessions, not env-only bootstrap auth. | This remains the durable auth direction for admin operations. | WBS 4.1 implementation |
| D-014 | 2026-04-13 | Gate C Outcome | Gate C passed, WBS 4 is complete, and WBS 5 is the active stage. | Confirms current execution should focus on WBS 5 and Phase 1 readiness. | `docs/archive/00-governance/gate-c-admin-ops-review-note.md`, WBS |
| D-015 | 2026-04-13 | Source Registry Baseline | Canada Big 5 source registry is the active source coverage baseline for Phase 1. | Current source expansion and collection behavior should build on this baseline. | `docs/01-planning/canada-big5-source-registry.md` |
| D-016 | 2026-04-13 | Aggregate Vocabulary | Public aggregate buckets and product filtering vocabulary are approved and should be reused consistently across APIs and UI. | Prevents filter semantics and dashboard metrics from drifting. | product-grid IA, WBS |
| D-017 | 2026-04-18 | Discovery Direction | Homepage-first discovery stays bounded and same-domain, but quality improvements should use hybrid candidate scoring rather than unconstrained crawling. | This is the current direction for source discovery hardening. | homepage discovery enhancement |
| D-018 | 2026-04-21 | Aggregate Refresh Behavior | Canonical approval should enqueue asynchronous aggregate refresh, and public serving should fall back to the latest successful snapshot if a newer refresh fails. | This is the live serving and health behavior for public data. | development journal, admin health slice |
| D-019 | 2026-04-21 | Registry Reset Behavior | Runtime code must not silently reseed bank, product type, source catalog, or generated source rows after operator resets. | Protects resettable registry state and empty-state replay testing. | development journal |
| D-020 | 2026-04-22 | Docs Operating Rule | Active implementation should start from `README.md`, `docs/README.md`, `development-journal.md`, and relevant active design docs, while `docs/archive/` is skipped by default. | Reduces startup cost and keeps Codex on current sources of truth. | docs map, development journal |

---

## 4. Current Interpretation Notes

- `WBS 5` is the active execution stage.
- Prototype and gate history are still retained, but they are not default reading paths anymore.
- Current implementation should optimize for data quality, evidence traceability, operator reviewability, and public-serving stability before polish.
- Future scope beyond the approved Phase 1 cutline still needs explicit Product Owner direction.

---

## 5. Change Rule

Update this file when one of these happens:
- the Product Owner changes active scope, priority, or release posture
- the approved technical baseline changes
- a new live behavior becomes the default operating rule
- an old decision stops being current and should be removed from the active log

Do not update this file for:
- routine slice completion
- one-off bug fixes with no baseline impact
- historical notes that belong in archive or in the development journal

---

## 6. Change History

| Date | Change |
|---|---|
| 2026-04-22 | Rewrote the decision log as a short current-baseline document and removed stale detailed history from the default path |
