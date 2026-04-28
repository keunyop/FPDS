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
| 2026-04-22 | `vendor_edit` | admin shell block | The live shell was simplified to match the requested `application-shell5` pattern more closely by removing extra navbar/sidebar chrome, using a standard collapsible sidebar presentation, and moving sign-out into the footer avatar menu | `app/admin/src/components/application-shell5.tsx`, `app/admin/src/app/admin/LogoutButton.tsx`, `app/admin/src/app/admin/*/page.tsx` | Revisit when a future Shadcnblocks shell exposes the same footer-user-menu and simplified chrome without direct edits |
| 2026-04-24 | `vendor_edit` | admin shell block | The live shell was tuned again to keep the collapse control in the sidebar on desktop, increase brand and section-title emphasis slightly, remove persistent sidebar highlight fills, and extend the footer menu with a placeholder `Account` row plus an icon-led sign-out action | `app/admin/src/components/application-shell5.tsx`, `app/admin/src/app/admin/LogoutButton.tsx`, `app/admin/README.md` | Revisit when a future Shadcnblocks Application Shell 5 revision exposes the same sidebar-local collapse control and footer menu structure without direct edits |
| 2026-04-24 | `vendor_edit` | admin shell block | The follow-up polish moved the active section title into the same sidebar-header row as the desktop collapse control, removed the visible footer env/role row from the user menu, tightened left alignment for account/sign-out actions, and made the shared sidebar menu button explicitly transparent until hover or active state | `app/admin/src/components/application-shell5.tsx`, `app/admin/src/components/ui/sidebar.tsx`, `app/admin/README.md` | Revisit when a future Shadcnblocks Application Shell 5 revision exposes the same header-row composition and menu-state styling without direct edits |
| 2026-04-24 | `vendor_edit` | sidebar primitive active-state handling | The shared shadcn sidebar primitive used presence-based `data-active` selectors, which still matched `data-active=\"false\"` and kept idle items highlighted, so the active-state selectors were narrowed to `data-[active=true]` value checks | `app/admin/src/components/ui/sidebar.tsx`, `app/admin/src/components/application-shell5.tsx` | Revisit when the upstream sidebar primitive switches to value-specific active selectors and the local fix can be dropped |
| 2026-04-24 | `vendor_edit` | admin dashboard shell label | The Product Owner wanted the `/admin` sidebar item to read `Dashboard` while keeping the broader Overview group and `Overview > Dashboard` breadcrumb path intact | `app/admin/src/components/application-shell5.tsx`, `app/admin/src/app/admin/page.tsx`, `app/admin/README.md` | Revisit if the admin IA changes the top-level route group away from Overview or introduces a separate dashboard route |
| 2026-04-25 | `wrapper` | admin route body headers and unavailable states | The Product Owner wanted every admin menu body to follow the compact overview-dashboard structure with breadcrumb-led paths and fewer card-like explanatory regions | `app/admin/src/components/fpds/admin/admin-page-header.tsx`, `app/admin/src/components/fpds/admin/admin-api-unavailable.tsx`, `app/admin/src/app/admin/*`, `app/admin/src/components/fpds/admin/*` | Revisit when admin IA introduces a new route group or when full responsive browser QA defines a different route-header standard |
| 2026-04-25 | `vendor_edit` | overview metrics block | The edited `stats5` block still rendered as a large explanatory card, so it was tightened into a compact metric group for admin route summaries | `app/admin/src/components/stats5.tsx` | Revisit if metrics move to a shared Admin Kit stat primitive or if `stats5` is removed from protected admin routes |
| 2026-04-25 | `vendor_edit` | admin modal block | The registry modals carried redundant `FPDS Admin` labels, verbose explanatory footer copy, and a corner-aligned close button that clipped against the rounded dialog; the same slice moved open/close state out of App Router navigation for routine modal toggles | `app/admin/src/components/offer-modal4.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx` | Revisit when a shared Admin Kit modal wrapper replaces the Shadcnblocks-derived block or when deep-link modal behavior needs server-first loading again |
| 2026-04-26 | `vendor_edit` | product-type registry modals | Product Type add/detail dialogs needed a narrower no-panel modal than bank and source-catalog dialogs, so `offer-modal4` now exposes a scoped narrow width option used only by `/admin/product-types` | `app/admin/src/components/offer-modal4.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx` | Revisit when the registry surfaces move to a shared Admin Kit modal wrapper with explicit size variants |
| 2026-04-26 | `wrapper` | destructive confirmation dialog | Product Type deletion confirmation was too visually heavy for an operator confirmation step, so the shared destructive dialog now uses a compact title, description, and action row while keeping localized pending labels | `app/admin/src/components/fpds/admin/destructive-confirm-dialog.tsx`, `app/admin/src/components/fpds/admin/product-type-detail-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx` | Revisit if destructive actions need per-resource confirmation copy or a stronger irreversible-warning pattern |
| 2026-04-26 | `vendor_edit` | bank registry modals | Bank add/detail dialogs needed less horizontal space than source-catalog detail while still supporting coverage management, so `offer-modal4` now exposes a medium width option used by `/admin/banks` | `app/admin/src/components/offer-modal4.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx` | Revisit when modal sizing moves to a shared Admin Kit modal wrapper with explicit size variants |
| 2026-04-26 | `wrapper` | registry page actions | Banks and Product Types no longer duplicate add actions in both the page header and list toolbar; the add action stays near the table it mutates | `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx` | Revisit if route headers gain a standardized primary-action slot for all admin list pages |
| 2026-04-26 | `wrapper` | bank detail modal content | Bank detail now keeps the profile form focused on editable bank fields, removes redundant summary/explanatory text, and labels coverage as product type counts | `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx` | Revisit if Bank detail becomes a full page or needs explicit audit-reason capture in the visible operator workflow |
| 2026-04-28 | `wrapper` | registry summary cards | Banks, Product Types, Sources, and Source Catalog summary cards use explicit white surfaces so the route summaries read as neutral cards against the admin canvas | `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `app/admin/README.md` | Revisit if summary cards move to a shared admin metric-card wrapper or if the global theme makes `background` and card-white surfaces equivalent |
| 2026-04-13 | `vendor_edit` | overview support blocks | `stats5` and `banner1` were edited to match FPDS operational copy, tones, and compact admin density instead of generic marketing/demo wording | `app/admin/src/components/stats5.tsx`, `app/admin/src/components/banner1.tsx` | Revisit when the review queue and live operational data require stronger shared wrappers or different blocks |
| 2026-04-13 | `wrapper` | review queue surface | The queue route needed a table-first FPDS-owned composition layer for review-specific filters, badge semantics, pagination, and issue summaries without forking more vendor blocks | `app/admin/src/components/fpds/admin/review-queue-surface.tsx`, `app/admin/src/app/admin/reviews/page.tsx`, `app/admin/src/app/admin/reviews/[reviewTaskId]/page.tsx` | Revisit when real review detail and trace components land and the queue can delegate more of its UI to shared FPDS admin wrappers |

---

## 4. Change History

| Date | Change |
|---|---|
| 2026-04-13 | Initial override register created after the template-first design baseline was approved |
