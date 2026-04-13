# Shadcnblocks Adoption Log

Version: 1.0
Date: 2026-04-13
Status: Active Tracking Artifact
Source Documents:
- `docs/03-design/fpds-design-system.md`
- `docs/03-design/fpds_design_system_stripe_benchmark.md`

---

## 1. Purpose

This document records the repository-level adoption trail for Shadcnblocks templates, blocks, and supporting frontend conventions.

Goals:
- keep a resumable record of which vendor assets were adopted
- separate vendor imports from FPDS-owned wrappers and overrides
- make future upgrades less guess-based

---

## 2. Logging Rules

Add an entry when one of these happens:
- a Shadcnblocks template is introduced
- a premium or free block is installed
- a style family or primitive baseline changes
- a direct edit is made to vendor-derived code

Do not add an entry for:
- unrelated business logic changes
- copy-only edits inside FPDS-owned wrappers
- reverted experiments that left no repo impact

---

## 3. Entry Template

```md
## YYYY-MM-DD - Adoption Slice

- Surface or Area:
- Vendor Asset:
- Source:
- Install Method:
- Files Added or Changed:
- FPDS Wrappers or Overrides:
- Direct Vendor Edits:
- Verification:
- Notes:
```

---

## 4. Entries

## 2026-04-13 - Admin Login and Shell Migration

- Surface or Area: `app/admin` live runtime for `/admin/login` and protected `/admin`
- Vendor Asset: `@shadcnblocks/login2`, `@shadcnblocks/application-shell5`, `@shadcnblocks/stats5`, `@shadcnblocks/banner1`, generated shadcn UI primitives
- Source: `https://www.shadcnblocks.com/docs`, authenticated `@shadcnblocks` registry in `app/admin/components.json`
- Install Method: `pnpm dlx shadcn@latest add -y -o ...` after manual `components.json` and Tailwind 4 setup
- Files Added or Changed: `app/admin/components.json`, `app/admin/postcss.config.mjs`, `app/admin/src/app/globals.css`, `app/admin/src/components/login2.tsx`, `app/admin/src/components/application-shell5.tsx`, `app/admin/src/components/stats5.tsx`, `app/admin/src/components/banner1.tsx`, `app/admin/src/components/ui/*`, `app/admin/src/app/admin/login/page.tsx`, `app/admin/src/app/admin/page.tsx`
- FPDS Wrappers or Overrides: FPDS auth flow remains in repo-owned page logic while the visual shell and login block now sit on top of Shadcnblocks-derived code and shadcn primitives
- Direct Vendor Edits: yes; the installed demo blocks were edited to remove placeholder SaaS content and align them to FPDS operator login, route-oriented admin navigation, and current WBS scope
- Verification:
  - `pnpm run typecheck`
  - `pnpm run build`
- Notes: `radix-nova` is now active through `components.json` and app-level shadcn semantic variables. The older `src/app/theme.css` mirror was removed because the admin app now styles directly from `globals.css`

---

## 5. Change History

| Date | Change |
|---|---|
| 2026-04-13 | Initial adoption log created after the template-first design baseline was approved |
