# FPDS Frontend Benchmark Baseline

Version: 3.0
Date: 2026-04-22
Status: Active current benchmark
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/product-grid-information-architecture.md`
- `docs/03-design/insight-dashboard-metric-definition.md`
- `docs/03-design/product-type-visualization-principles.md`
- `docs/03-design/admin-information-architecture.md`
- `docs/03-design/fpds-design-system.md`

---

## 1. Purpose

This document is the short, current benchmark for frontend implementation.

Use it to answer:
- what visual benchmark FPDS follows
- what Shadcnblocks is responsible for
- what FPDS must still own directly
- how public and admin surfaces should feel today

If this document and `fpds-design-system.md` differ on current frontend direction, follow this document.

---

## 2. Current Position

FPDS uses this split:
- `Stripe` is the structural benchmark for restraint, density, hierarchy, and state communication.
- `Shadcnblocks` is the implementation base for shells, sections, and generic UI building blocks.
- `FPDS` owns domain semantics, evidence boundaries, product comparison rules, workflow meaning, and localization behavior.

FPDS should not spend time inventing new generic shells, cards, tables, or form patterns unless the domain requires a real deviation.

---

## 3. Authority Rules

### 3.1 Stripe Benchmark

Follow Stripe for:
- clear information hierarchy
- compact but readable density
- strong empty, loading, warning, and success states
- restrained visual language

Do not copy Stripe literally. Use it as a benchmark for product quality and discipline.

### 3.2 Shadcnblocks Baseline

Follow Shadcnblocks for:
- initial page and shell composition
- reusable admin structure
- generic blocks and primitives
- implementation speed for non-domain UI

Start from vendor assets first. Wrap or edit only where FPDS needs domain-specific behavior.

### 3.3 FPDS-Owned Layer

FPDS still owns:
- product-type-aware public comparisons
- methodology and freshness messaging
- evidence-aware admin review flows
- review, run, audit, usage, and health semantics
- locale-aware labels and copy boundaries

---

## 4. Surface Direction

### 4.1 Public

Public surfaces should feel:
- balanced
- professional
- comparison-oriented
- lighter than the admin shell

Current public priority:
- `/products`
- `/dashboard`

Public UI should emphasize:
- filter clarity
- product-type-aware comparison
- freshness and methodology transparency
- navigation that preserves query scope

### 4.2 Admin

Admin surfaces should feel:
- compact
- operational
- state-heavy
- route-oriented

Current admin priority:
- login
- reviews
- runs
- changes
- audit
- usage
- health

Admin UI should optimize for triage speed and evidence readability, not marketing polish.

---

## 5. Implementation Rules

1. Prefer Shadcnblocks templates or blocks over bespoke base components.
2. Keep FPDS-specific behavior in repo-owned wrappers or route code.
3. Track direct vendor edits in the override and adoption docs.
4. Keep admin density tighter than public density.
5. Keep the current baseline light-first unless a later decision says otherwise.
6. Do not let visual work weaken evidence boundaries or review clarity.
7. Keep screen copy minimal and action-oriented; remove internal implementation detail unless the operator needs it to act safely.
8. Preserve locale switching without adding a second explanatory layout just to hold extra text.

---

## 6. Supporting Tracking Docs

Use these docs when implementation changes vendor-derived UI:
- `docs/03-design/shadcnblocks-adoption-log.md`
- `docs/03-design/shadcnblocks-block-inventory.md`
- `docs/03-design/ui-override-register.md`

---

## 7. What This Doc Is Not

This doc is not:
- a full design-system token spec
- a route-by-route implementation diff
- a historical migration narrative

It is the current benchmark baseline for ongoing frontend work.
