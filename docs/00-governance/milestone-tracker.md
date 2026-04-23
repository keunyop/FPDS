# FPDS Milestone Tracker

Version: 2.0
Date: 2026-04-22
Status: Active current milestone board
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/00-governance/roadmap.md`
- `docs/00-governance/stage-gate-checklist.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This file tracks only the milestones that still matter as current stage checkpoints.

It is intentionally shorter than the WBS.

---

## 2. Milestone Board

| Milestone | Status | Meaning | Main Evidence |
|---|---|---|---|
| M0 Detailed Design Closure | Done | design package and build-start governance were closed | requirements, scope baseline, design docs, Gate A archive note |
| M1 Foundation Setup Complete | Done | repo, env, DB, storage, auth, i18n, security, and CI baselines exist | WBS 2, foundation docs |
| M2 Prototype Acceptance | Done | TD savings prototype feasibility and reviewability were proven | prototype archive docs, WBS 3 |
| M3 Admin and Ops Core Complete | Done | admin review, trace, run, audit, and usage workflows are operational | WBS 4, admin runtime docs |
| M4 Phase 1 Public and Data Expansion | In Progress | Big 5 coverage, public serving, registry admin, and hardening continue under WBS 5 | WBS 5, README, development journal |
| M5 Phase 1 Release Readiness | Not Started | release-level publish readiness, security, runbook, and acceptance evidence are still ahead | future Gate D evidence |
| M6 Phase 2 Preparation | Not Started | Japan expansion and external API preparation remain later-stage work | future roadmap updates |

---

## 3. Current Focus Milestone

Current focus: `M4 Phase 1 Public and Data Expansion`

This milestone should be treated as complete only when:
- WBS 5 remaining required slices are closed or explicitly deferred
- public-serving behavior is stable enough for release readiness
- registry and collection flows are operationally reviewable
- Phase 1 quality gaps are reduced to an acceptable release posture

---

## 4. Next Gate-Oriented Milestone

Next gate-oriented milestone: `M5 Phase 1 Release Readiness`

Expected evidence areas:
- release checklist
- publish readiness and BX-PF handling posture
- security and operational readiness notes
- QA and acceptance evidence
- current runbook and operator documentation

---

## 5. Tracking Rule

Update this file when:
- a milestone changes status
- the current focus milestone changes
- a gate outcome changes stage readiness

Do not use this file for:
- individual task-level progress
- bug lists
- long historical narratives

---

## 6. Change History

| Date | Change |
|---|---|
| 2026-04-22 | Rewrote the milestone tracker as a short current milestone board and removed stale schedule-heavy detail from the default path |
