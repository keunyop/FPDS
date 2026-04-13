# UI Override Register

Version: 1.0
Date: 2026-04-13
Status: Active Tracking Artifact
Source Documents:
- `docs/03-design/fpds-design-system.md`
- `docs/03-design/fpds_design_system_stripe_benchmark.md`

---

## 1. Purpose

This register tracks intentional deviations from vendor defaults in the frontend UI layer.

Goals:
- explain why an override exists
- show whether the override is theme-only, composition-level, or direct vendor-code modification
- reduce upgrade risk by making exceptions visible

---

## 2. Override Types

| Type | Meaning |
|---|---|
| `theme` | semantic variable, spacing, density, or style override |
| `wrapper` | FPDS-owned composition or wrapper around vendor UI |
| `vendor_edit` | direct edit to vendor-derived code |

---

## 3. Register

| Date | Type | Area | Reason | File Paths | Revisit Trigger |
|---|---|---|---|---|---|
| 2026-04-13 | `theme` | `app/admin` | Move the admin app from bridge token mirroring to app-local shadcn semantic variables and `components.json` as the active source of truth | `app/admin/components.json`, `app/admin/src/app/globals.css`, `app/admin/postcss.config.mjs` | Revisit when another frontend app shares the same shadcn theme contract and a central sync path becomes worthwhile |
| 2026-04-13 | `vendor_edit` | admin login block | The installed `login2` demo had placeholder brand/signup behavior and no FPDS auth wiring, so it was edited into the real operator login block | `app/admin/src/components/login2.tsx` | Revisit when a newer Shadcnblocks login block maps more closely to FPDS operator auth without direct edits |
| 2026-04-13 | `vendor_edit` | admin shell block | The installed `application-shell5` demo carried generic SaaS workspace content, so it was edited to fit FPDS route groups, operator context, and current live admin scope | `app/admin/src/components/application-shell5.tsx` | Revisit when future Shadcnblocks admin shell assets better match FPDS operations IA or when `/admin/reviews` expands the shell needs |
| 2026-04-13 | `vendor_edit` | overview support blocks | `stats5` and `banner1` were edited to match FPDS operational copy, tones, and compact admin density instead of generic marketing/demo wording | `app/admin/src/components/stats5.tsx`, `app/admin/src/components/banner1.tsx` | Revisit when the review queue and live operational data require stronger shared wrappers or different blocks |
| 2026-04-13 | `wrapper` | review queue surface | The queue route needed a table-first FPDS-owned composition layer for review-specific filters, badge semantics, pagination, and issue summaries without forking more vendor blocks | `app/admin/src/components/fpds/admin/review-queue-surface.tsx`, `app/admin/src/app/admin/reviews/page.tsx`, `app/admin/src/app/admin/reviews/[reviewTaskId]/page.tsx` | Revisit when real review detail and trace components land and the queue can delegate more of its UI to shared FPDS admin wrappers |

---

## 4. Change History

| Date | Change |
|---|---|
| 2026-04-13 | Initial override register created after the template-first design baseline was approved |
