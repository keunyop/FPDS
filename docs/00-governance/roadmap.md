# FPDS Roadmap

Version: 2.0
Date: 2026-04-22
Status: Active current roadmap
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/milestone-tracker.md`

---

## 1. Purpose

This roadmap is the short current view of what FPDS has already cleared, what stage is active now, and what remains ahead.

It is not a detailed task tracker.
For detailed task state, use `docs/01-planning/WBS.md`.

---

## 2. Current Stage

Current stage: `WBS 5`

Stage status:
- Gate A passed on `2026-04-06`
- Gate B passed on `2026-04-11`
- Gate C passed on `2026-04-13`
- WBS 5 is the active implementation stage

Current working interpretation:
- prototype work is complete and archived by default
- admin and ops core is complete enough to support current public and source-registry follow-on work
- Phase 1 public and data hardening work is still in progress

---

## 3. What Is Already Done

### 3.1 Foundation and Prototype

Completed:
- WBS 2 foundation scaffolds and repo baselines
- WBS 3 prototype pipeline, viewer, and prototype hardening

### 3.2 Admin and Ops Core

Completed:
- admin login
- review queue and review decision flow
- evidence trace viewer
- run status
- change history
- audit log
- usage tracking and usage dashboard
- operational scenario QA

### 3.3 Phase 1 Public and Registry Progress

Completed:
- Canada Big 5 source registry baseline
- chequing, savings, and GIC parser expansion baselines
- aggregate dataset generation
- public products API
- dashboard APIs
- public Product Grid
- public Insight Dashboard
- grid/dashboard cross-filter behavior
- locale rollout
- freshness and metric wording improvements
- source registry admin MVP
- dynamic product type onboarding
- aggregate refresh queue and dashboard health behavior

---

## 4. What Is Active Now

Current Phase 1 focus:
- source collection hardening
- bank-specific data quality fixes
- public-serving stability and aggregate freshness
- registry governance and operator workflows
- responsive QA and follow-on polish only where it protects real product behavior

Default rule:
- prioritize evidence quality, reviewability, and operator clarity before cosmetic expansion

---

## 5. What Is Next

Near-term next areas:
1. Continue WBS 5 hardening where real bank-source gaps still produce review or validation noise.
2. Keep public grid and dashboard behavior aligned to the approved vocabulary and freshness model.
3. Prepare the remaining release-readiness work needed before Gate D.

Likely later within Phase 1:
- additional public quality and QA follow-on slices
- publish readiness and BX-PF integration follow-on work
- release evidence and operating notes cleanup

---

## 6. Not Active Yet

Not active by default:
- Phase 2 Japan expansion
- external SaaS or open API delivery
- consumer recommendation features
- public evidence exposure
- billing or subscription work

These remain outside current execution unless the Product Owner changes scope.

---

## 7. Roadmap Rule

Use this document for stage-level direction only.

If you need:
- exact task status: use `WBS.md`
- current risks: use `raid-log.md`
- current decisions: use `decision-log.md`
- recent implementation memory: use `development-journal.md`

---

## 8. Change History

| Date | Change |
|---|---|
| 2026-04-22 | Rewrote the roadmap as a short current stage view and removed stale early-stage progress detail from the default path |
