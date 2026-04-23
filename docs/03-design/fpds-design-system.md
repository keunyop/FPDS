# FPDS Design System Baseline

Version: 2.0
Date: 2026-04-13
Status: Approved Working Baseline after Shadcnblocks Template-First Overhaul

Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/03-design/product-grid-information-architecture.md`
- `docs/03-design/admin-information-architecture.md`
- `docs/03-design/insight-dashboard-metric-definition.md`
- `docs/03-design/product-type-visualization-principles.md`
- `docs/03-design/fpds_design_system_stripe_benchmark.md`
- `https://docs.stripe.com/stripe-apps/design`
- `https://docs.stripe.com/stripe-apps/style`
- `https://docs.stripe.com/stripe-apps/patterns`
- `https://www.shadcnblocks.com/docs`
- `https://www.shadcnblocks.com/docs/blocks/getting-started`
- `https://www.shadcnblocks.com/docs/shadcn-cli/overview`
- `https://www.shadcnblocks.com/docs/blocks/styles`
- `https://www.shadcnblocks.com/docs/templates/getting-started`
- `https://www.shadcnblocks.com/docs/templates/project-structure`
- `https://www.shadcnblocks.com/docs/templates/adding-blocks`
- `https://www.shadcnblocks.com/admin-dashboard`

---

## 1. Purpose

This document defines the FPDS design-system baseline after the project-level decision to move away from a bespoke component-system approach and adopt **Shadcnblocks as the official template and block foundation** for frontend implementation.

Goals:
- keep Stripe as the benchmark for structure, restraint, and state communication
- use Shadcnblocks as the implementation base for shells, pages, sections, and generic UI primitives
- preserve FPDS-owned domain behavior for product comparison, evidence workflows, operational status, and localization
- provide implementation-ready direction for upcoming public and admin UI work without re-opening core design decisions

This is a design-system and template-adoption baseline. It is not a backend architecture spec and it is not a route-by-route implementation diff.

---

## 2. Decision Shift

The previous baseline treated FPDS as a mostly bespoke UI system built with custom tokens and custom page scaffolds inspired by Stripe.

The new baseline is different:
- **Stripe remains the benchmark** for product experience principles.
- **Shadcnblocks becomes the implementation base** for templates, blocks, and generic interface patterns.
- **FPDS owns only the domain layer**: product-type-aware comparison rules, evidence-aware admin workflows, public methodology/freshness communication, domain status semantics, and trilingual behavior.

In practical terms, FPDS no longer starts by inventing new generic cards, tables, badges, dialogs, or shell layouts. It starts from vendor template assets and only customizes what is product-specific.

---

## 3. Authority Hierarchy

### 3.1 Benchmark Authority

Stripe remains the authority for:
- restrained, high-density product UI
- contextual navigation and focus escalation
- token-driven styling discipline
- clear loading, empty, state, and action patterns

### 3.2 Implementation Authority

Shadcnblocks is now the authority for:
- template structure
- page and section starting points
- generic admin shell patterns
- block installation workflow
- shadcn/ui style selection
- project structure conventions for the frontend layer

### 3.3 FPDS Domain Authority

FPDS remains the authority for:
- Public Product Grid meaning
- Insight Dashboard metrics and visualization rules
- review, trace, run, publish, usage, and health workflows
- public evidence non-exposure
- locale rules and source-language handling
- domain status vocabulary

### 3.4 Conflict Rule

When Stripe benchmark ideas and Shadcnblocks implementation defaults differ, FPDS should:
1. keep the Stripe principle,
2. use the closest Shadcnblocks pattern available,
3. add the smallest possible FPDS wrapper or override,
4. avoid creating a second bespoke primitive system.

When this document and the benchmark doc differ, follow `docs/03-design/fpds_design_system_stripe_benchmark.md`.

---

## 4. Template Baseline Decisions

## 4.1 Frontend Template Direction

FPDS standardizes on the **Shadcnblocks Next.js template direction** for frontend implementation.

This means the frontend layer assumes:
- Next.js 15 App Router conventions
- React 19
- Tailwind 4
- shadcn/ui primitives
- section-based composition

This does not override broader FPDS platform decisions outside the UI layer.

## 4.2 Primitive Library Baseline

FPDS uses **Radix UI** as the baseline primitive library.

Reason:
- Shadcnblocks explicitly presents Radix as the preferred and more battle-tested default.
- FPDS admin workflows prioritize operational stability over experimentation.

## 4.3 Global Style Baseline

FPDS uses **`radix-nova`** as the global shadcn style baseline.

Reason:
- Nova is documented as tighter and better suited to data-heavy dashboards.
- FPDS admin surfaces are compact by design.
- Public surfaces can be relaxed through section spacing and card padding without fragmenting the component style system.

### Result
- **Admin** uses Nova density almost directly.
- **Public** uses the same style family with relaxed spacing wrappers.
- FPDS does **not** mix Vega, Nova, Maia, Lyra, or Mira on a route-by-route basis.

## 4.4 Installation Baseline

FPDS adopts a **CLI-first** installation policy for Shadcnblocks.

Default rules:
- use the official `shadcn` CLI for adding blocks and components
- configure private registry authentication for premium/pro assets
- use copy/paste only as an exception
- keep `components.json` aligned with the selected style and aliases

## 4.5 Registry and Auth Baseline

FPDS assumes private-registry authentication for premium blocks and templates.

Required baseline inputs:
- `SHADCNBLOCKS_API_KEY`
- authenticated `@shadcnblocks` registry configuration in `components.json`

## 4.6 Project Structure Baseline

FPDS aligns its frontend structure with the Shadcnblocks template conventions and extends them with a domain layer.

Recommended structure:

```text
src/
  app/
    (public)/
    (admin)/
    globals.css
    layout.tsx
  components/
    ui/
    layout/
    sections/
    fpds/
      public/
      admin/
      shared/
  lib/
```

Interpretation:
- `components/ui` is vendor-installed primitive territory.
- `components/layout` and `components/sections` are template-derived building blocks.
- `components/fpds` is where FPDS-specific business UI lives.

---

## 5. System Architecture for the UI Layer

### 5.1 Vendor Layer

Contains:
- Shadcnblocks templates
- Shadcn Admin Kit
- installed shadcn/ui primitives
- imported template sections and layout blocks

Rule:
- keep this layer as close to vendor defaults as practical.

### 5.2 Theme Layer

Contains:
- `components.json`
- shadcn semantic CSS variables in `globals.css`
- FPDS color, chart, and status semantic overrides
- spacing and density rules

Rule:
- do not preserve a separate parallel token tree when shadcn semantic variables can express the same intent.

### 5.3 Domain Layer

Contains FPDS-owned business UI, such as:
- `ProductCard`
- `FreshnessIndicator`
- `MethodologyNote`
- `DashboardRankingList`
- `EvidenceTracePane`
- `ReviewActionBar`
- `RunStageStrip`
- `PublishStateCard`
- `DashboardHealthDomainList`

Rule:
- domain components should carry business meaning, not generic UI responsibility.

### 5.4 Route Composition Layer

This is where FPDS composes pages from:
- template shells
- template sections
- vendor primitives
- FPDS domain sections

Rule:
- stable shells, replaceable sections.

---

## 6. Theme and Token Direction

## 6.1 Source of Truth

The source of truth for product UI theming is now:
1. `components.json` style selection
2. `globals.css` shadcn semantic variables
3. supplemental status and chart tokens
4. route-level spacing and density rules

## 6.2 Semantic Token Model

FPDS should express its visual system through shadcn semantic roles such as:
- `background`
- `foreground`
- `card`
- `popover`
- `primary`
- `secondary`
- `muted`
- `accent`
- `destructive`
- `border`
- `input`
- `ring`
- sidebar-specific semantic tokens

Supplemental FPDS-specific tokens may exist for:
- chart categories
- success, warning, info semantics
- evidence or freshness states when needed

## 6.3 Visual Direction

The visual direction stays close to the previous benchmark intent:
- crisp
- calm
- analytical
- financial without looking old-fashioned
- restrained rather than decorative

Color direction:
- light neutral canvas
- indigo as primary action and active state
- cool neutral borders and surfaces
- teal/green for success
- amber for warning
- red for destructive

Typography direction:
- keep the product UI simple and implementation-friendly
- avoid introducing a more ornamental editorial font as a core product dependency
- use a clear UI sans and a readable mono for IDs, runs, and diagnostic values

---

## 7. Surface Mapping

## 7.1 Public Surfaces

| Surface | Vendor Starting Point | FPDS-Owned Layer |
|---|---|---|
| `/dashboard` | Shadcnblocks public template header and section rhythm | market snapshot framing, methodology/freshness messaging, filter context |
| `/dashboard/products` | card/grid, toolbar, filter, and pagination patterns | product-type-aware `ProductCard`, shared scope summary, product-specific metrics |
| `/dashboard/insights` | stats cards, chart cards, ranking/list sections | ranking semantics, scatter preset logic, insufficiency handling |
| `/methodology` | docs/article/content sections | FPDS metric definitions, freshness policy, evidence boundary |

## 7.2 Admin Surfaces

| Surface | Vendor Starting Point | FPDS-Owned Layer |
|---|---|---|
| `/admin` | Admin Kit shell and dashboard widgets | urgent-attention ordering, dashboard health and retry semantics |
| `/admin/reviews` | Admin Kit table, filters, badges, pagination | review-state, confidence, validation, issue summary semantics |
| `/admin/reviews/:id` | Admin Kit page shell, cards, forms, sheets | evidence trace, diff preview, review action logic |
| `/admin/runs` | Admin Kit table and metric panels | run lifecycle semantics and stage vocabulary |
| `/admin/changes` | Admin Kit list/table patterns | change-event taxonomy and chronology |
| `/admin/publish` | Admin Kit tables and alert cards | retry/reconciliation behavior and publish risk messaging |
| `/admin/usage` | Admin Kit metric and chart panels | run/agent/model cost interpretation |
| `/admin/health/dashboard` | Admin Kit status cards and tables | aggregate freshness, completeness, and cache semantics |

---

## 8. Component Ownership Rules

## 8.1 Vendor-Managed by Default

FPDS should use vendor-installed primitives for generic UI such as:
- buttons
- cards
- badges
- dialogs
- sheets
- tables
- form controls
- tabs
- dropdowns
- tooltips
- skeletons
- alerts

## 8.2 FPDS-Managed by Design

FPDS should own business-specific components such as:
- product comparison cards
- ranking widgets with metric semantics
- freshness and methodology modules
- evidence trace panels
- validation issue lists
- review action bars
- diff previews
- publish risk and reconciliation panels
- usage anomaly drilldowns
- dashboard health domain summaries

## 8.3 Customization Boundary

Allowed:
- theme overrides
- spacing and density wrappers
- route-specific composition
- domain-specific cells, notes, and panels

Disallowed as the default path:
- rewriting vendor primitives into a second in-house primitive set
- changing style families per route
- forking template pages for trivial copy changes
- scattering hard-coded colors outside the theme layer

## 8.4 Edit Order Rule

When changing UI:
1. try configuration and theming first,
2. then composition and wrappers,
3. then domain-specific custom sections,
4. only edit vendor code last.

---

## 9. Public and Admin Experience Rules

### 9.1 Public

Public remains dashboard-first.

Key rules:
- no marketing-led homepage narrative
- Product Grid and Insights remain sibling surfaces
- methodology and freshness must remain reachable
- evidence is never exposed publicly

### 9.2 Admin

Admin remains triage-first and diagnosis-oriented.

Key rules:
- overview is not a giant everything-dashboard
- review queue is table-first
- review detail is a domain page, not a generic template demo
- publish, usage, and health remain separate operational surfaces

### 9.3 Shared Rules

- public and admin share the same style family and theme system
- public is balanced; admin is compact
- source-derived product text remains in the source language
- translated UI labels follow locale-resource governance
- UI copy stays task-focused and minimal across all surfaces
- avoid explanatory implementation detail, role lists, and process narration unless they are required for the current decision or action
- keep locale controls available without forcing a second explanatory panel or extra chrome

---

## 10. Status, Localization, and Accessibility

## 10.1 Status

Vendor badge components should be reused, but FPDS owns the semantic mapping.

Minimum baseline:
- queued / pending / in review → info
- approved / published / healthy → success
- deferred / reconciliation / stale soon → warning
- rejected / failed / critical → destructive

State must never rely on color alone.

## 10.2 Localization

Translate:
- navigation
- page titles
- widget labels
- filter labels
- chart titles
- methodology notes
- helper text
- status labels

Do not translate:
- source-derived product names
- source-derived descriptions or conditions
- evidence excerpts

## 10.3 Accessibility

Maintain:
- visible focus treatment
- strong text contrast on light surfaces
- non-color state cues
- sufficiently large hit areas for chips, tabs, and locale controls
- reduced-motion respect

---

## 11. Upgrade and Maintenance Boundary

Shadcnblocks is a commercial template and block source, so upgrade discipline is part of the design-system baseline.

Required maintenance principles:
- isolate FPDS custom logic from vendor primitives
- record imported templates and blocks
- document any direct edits to vendor-derived code
- re-test public/admin shells after vendor updates
- keep locale, status, and evidence behaviors under regression coverage

Recommended supporting artifacts:
- Shadcnblocks adoption log
- block inventory
- override register

---

## 12. Implementation Boundary

This baseline does not by itself implement:
- React page files
- Tailwind config files
- vendor acquisition or licensing
- API integration
- chart library selection details

It does provide the approved starting point for:
- public dashboard surfaces
- public product grid
- methodology surface
- admin shell and operations pages
- FPDS domain wrappers on top of Shadcnblocks

---

## 13. Follow-On Artifacts

The next natural implementation artifacts are:
- a Shadcnblocks adoption log
- a frontend block inventory
- a theme variable file aligned to `radix-nova`
- public and admin layout scaffolds
- domain component inventory under `components/fpds`
- locale label mapping for badge, status, and helper text

---

## 14. Change History

| Date | Change |
|---|---|
| 2026-04-10 | Initial FPDS design-system baseline created using Stripe design guidance as a benchmark |
| 2026-04-12 | Added benchmark-refresh authority note |
| 2026-04-13 | Reworked the baseline to adopt Shadcnblocks as the official template-first implementation layer |
| 2026-04-13 | Standardized on `Radix UI + radix-nova` and added vendor/theme/domain ownership rules |
| 2026-04-13 | Reframed public/admin surface guidance around template composition rather than bespoke primitives |
| 2026-04-22 | Added a shared copy-discipline rule: keep screens simple, task-focused, and free of unnecessary explanatory text |
