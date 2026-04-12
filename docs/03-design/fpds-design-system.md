# FPDS Design System Baseline

Version: 1.0
Date: 2026-04-10
Status: Approved Working Baseline for FPDS UI Implementation
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/03-design/product-grid-information-architecture.md`
- `docs/03-design/admin-information-architecture.md`
- `docs/03-design/product-type-visualization-principles.md`
- `docs/03-design/localization-governance-and-fallback-policy.md`
- `https://docs.stripe.com/stripe-apps/design`
- `https://docs.stripe.com/stripe-apps/style`
- `https://docs.stripe.com/stripe-apps/patterns`

---

## 1. Purpose

This document defines the FPDS design-system baseline for public and admin surfaces.

Goals:
- translate the approved FPDS IA into a reusable visual and interaction system
- benchmark Stripe Dashboard and Stripe Apps guidance without copying it literally
- keep future public, admin, and docs surfaces visually aligned through shared tokens and component rules
- provide implementation-ready guidance before WBS `3.8`, `4.x`, and `5.x` UI work begins

This is a design-system baseline, not a route implementation or component-library implementation by itself.

---

## 2. Benchmark Interpretation

FPDS uses Stripe as a benchmark in three ways.

1. Official guidance says app design should stay consistent, clear, and scalable, and should rely on recommended patterns rather than one-off custom UI.
2. Official guidance says custom styling should stay limited and token-driven so accessibility and platform consistency remain strong.
3. Stripe Apps guidance emphasizes patterns for state, empty/loading, actions, lists, and context views instead of decorative novelty.

FPDS keeps those principles, but applies them to a different product domain:
- financial-product review and evidence trace
- public comparison grids and dashboard views
- admin triage, diagnosis, and decision surfaces

Inference:
- Stripe does not publish a full "clone the dashboard" recipe.
- The FPDS shell, paneling, and data-density choices below are an inference from Stripe's documented design philosophy and common Dashboard conventions.

---

## 3. Core Principles

### 3.1 System Before Decoration

- Tokens, spacing, density, and state language are more important than ornamental branding.
- Custom color use should stay restrained.
- Brand expression belongs in accent moments, not in every component.

### 3.2 Triage First

- The admin surface should feel like an operational cockpit.
- Queue state, risk, confidence, freshness, and failure should be readable within a few seconds.
- High-signal surfaces use panel rhythm, status color, and hierarchy before charts or flair.

### 3.3 Context-Preserving Navigation

- Like Stripe Dashboard patterns, FPDS should keep users inside a stable shell while detail views deepen context.
- Primary navigation, scoped filters, detail panes, and back context should feel continuous rather than page-jumpy.

### 3.4 Evidence Is a First-Class UI Object

- Evidence excerpts, field provenance, and validation issues are not secondary metadata.
- The system should visually support comparison between candidate value, issue state, and evidence source.

### 3.5 Data-Dense, Not Visually Heavy

- Use compact spacing, subtle borders, and strong typography hierarchy.
- Prefer panel stacks, tables, and metric strips over oversized cards.
- Avoid flat single-color surfaces and avoid noisy gradients in work areas.

### 3.6 State Must Be Unambiguous

- `queued`, `warning`, `error`, `retry`, `published`, `fresh`, and `stale` each need stable color and badge behavior.
- State color is supportive, not the only signal; icon, label, and placement should reinforce it.

### 3.7 Public and Admin Should Feel Related, Not Identical

- Admin should be denser, more operational, and more muted.
- Public should be lighter, more comparative, and more editorial.
- Both should still share the same tokens, spacing scale, motion language, and status semantics.

---

## 4. Visual Direction

### 4.1 Overall Character

- crisp
- confident
- financial but not old-fashioned
- structured and calm under high information density

### 4.2 Color Direction

FPDS should avoid Stripe-purple imitation and instead use:
- deep navy for shell and emphasis
- cobalt blue for primary action and active state
- teal for success and verified states
- amber for warnings and pending states
- brick red for critical and rejection states
- cool neutral grays for structure

### 4.3 Typography Direction

Recommended type roles:
- UI sans: `Instrument Sans`
- data mono: `IBM Plex Mono`
- editorial or long-form docs accent: `Newsreader`

Rules:
- admin and product UI rely mostly on UI sans + mono
- editorial serif is optional and should not appear in dense operational tables
- avoid generic default stacks as the primary design voice

### 4.4 Shape Direction

- small radii by default
- medium radii for cards or drawers
- rounded pills only for badges/chips
- minimal shadow; rely more on surface steps and borders than floating-card aesthetics

---

## 5. Design Tokens

The shared token baseline lives in:
- `shared/design/fpds-design-tokens.json`
- `shared/design/fpds-theme.css`

### 5.1 Color Roles

Foundations:
- canvas
- surface
- surface-raised
- surface-inset
- border-subtle
- border-strong

Text:
- text-primary
- text-secondary
- text-muted
- text-on-accent

Interactive:
- accent-primary
- accent-primary-hover
- accent-secondary
- focus-ring

Status:
- info
- success
- warning
- critical
- queued
- published
- stale

### 5.2 Spacing Scale

Use an `8px` base rhythm:
- `2`
- `4`
- `8`
- `12`
- `16`
- `24`
- `32`
- `40`
- `48`
- `64`

Rules:
- admin tables and filter bars usually use `8`, `12`, `16`
- page sections use `24`, `32`
- hero or high-emphasis public layouts can use `40`, `48`, `64`

### 5.3 Radius

- `sm = 8px`
- `md = 12px`
- `lg = 18px`
- `pill = 999px`

### 5.4 Shadow

- `shadow-0`: none
- `shadow-1`: subtle edge lift
- `shadow-2`: hover/focus lift

Shadows should stay soft and sparse.

### 5.5 Motion

Use short, purposeful transitions:
- `fast = 120ms`
- `base = 180ms`
- `slow = 260ms`

Motion should prioritize:
- drawer or detail-pane entry
- table/filter state transitions
- staggered dashboard reveal

Avoid playful or bouncy motion in admin operations surfaces.

---

## 6. Layout System

### 6.1 Admin Shell

Recommended structure:
- left navigation rail
- top utility bar
- page header band
- content canvas
- optional right-side detail or trace pane

Desktop baseline:
- left rail: `248px`
- content max width: fluid
- detail split panes are preferred for review and trace workflows

Tablet baseline:
- nav rail may collapse
- secondary pane may convert to tabbed sections

Mobile baseline:
- navigation collapses to drawer
- dense tables convert to stacked list cards
- state badge, confidence, and action affordances must remain visible

### 6.2 Public Shell

Recommended structure:
- compact top nav
- wide content container
- strong page header
- sticky filter row where appropriate
- alternating comparison sections and list/grid sections

Public width guidance:
- reading sections: `720-840px`
- grid/dashboard sections: `1200-1440px`

### 6.3 Panel Rhythm

Panels are the main work unit.

Panel rules:
- subtle background step or border
- clear internal header
- action row aligned to panel purpose
- no decorative gradients inside dense work panels

---

## 7. Component Baseline

### 7.1 Shell Components

- AppShell
- SideNav
- TopBar
- PageHeader
- Breadcrumb or BackContext
- SectionHeader

### 7.2 Filter and Search Components

- FilterBar
- FilterChip
- SearchInput
- ScopeSummary
- SortToolbar

### 7.3 Data Display Components

- MetricStrip
- DataTable
- ComparisonCard
- DetailPanel
- FieldRow
- EvidenceSnippet
- KeyValueGrid

### 7.4 State Components

- StatusBadge
- SeverityBadge
- InlineNotice
- EmptyState
- LoadingState
- ErrorState

### 7.5 Workflow Components

- ReviewActionBar
- ValidationIssueList
- TracePane
- RunStageStrip
- PublishStateCard
- UsageTrendPanel

### 7.6 Public-Specific Components

- ProductCard
- DashboardRankingList
- ScatterPlotPanel
- MethodologyNote
- FreshnessIndicator

---

## 8. Component Behavior Rules

### 8.1 Badges

- Use soft background plus strong text, not neon fills.
- Use one stable semantic per badge family.
- Never invent one-off badge colors per page.

### 8.2 Tables

- Admin tables are compact and should support sticky headers where useful.
- Numeric columns align right.
- IDs and timestamps may use mono text.
- Row actions should not crowd the default list surface.

### 8.3 Panels and Drawers

- Review detail and trace should prefer side-by-side inspection on desktop.
- Side drawer or split pane is preferred over full hard navigation for secondary context.
- Long diagnostic surfaces should chunk into titled sections, not one long blob.

### 8.4 Empty and Loading States

Follow the Stripe-inspired pattern approach:
- tell the user what is happening
- explain why the surface is empty when possible
- provide the next useful action

### 8.5 Forms and Decisions

- Primary action is singular and visually clear.
- Destructive actions must read as deliberate, not equal-weight neighbors.
- Edit-and-approve flows should show diff or changed-field context before commit.

---

## 9. Status Semantics

| State | Token Direction | UI Treatment |
|---|---|---|
| `pass` / verified | success | subtle green badge, low visual noise |
| `warning` / pending | warning | amber badge, visible but not alarming |
| `error` / rejected | critical | red badge, strongest emphasis |
| `queued` | queued | blue-gray badge, operational attention |
| `published` | success | success badge with calm treatment |
| `retry` / `reconciliation` | warning or critical based on severity | always visible in list rows |
| `stale` | warning | freshness-specific emphasis |

---

## 10. Surface-Specific Guidance

### 10.1 Admin Overview

- prioritize queue count, failures, retries, stale aggregates, and recent changes
- use dense metrics and short labels
- keep charts secondary to triage signals

### 10.2 Review Queue

- table-first
- sortable and filter-heavy
- issue summary, confidence, and validation status must scan quickly

### 10.3 Review Detail / Trace Viewer

- two-pane or three-zone structure on desktop
- candidate fields on the left, evidence/trace on the right
- action area anchored and always discoverable

### 10.4 Runs

- timeline/state strip first
- stage summaries second
- per-source failures below

### 10.5 Public Product Grid

- product cards should stay comparison-oriented
- do not over-style cards with hero marketing visuals
- emphasize rates, fees, minimums, freshness, and badges

### 10.6 Public Dashboard

- use strong headline metrics with disciplined supporting charts
- mixed-type views should feel like market overview
- single-type views can become more comparative and analytical

---

## 11. Accessibility and Restraint Rules

- color is never the only state signal
- all interactive states must have visible focus treatment
- body copy and secondary text must keep strong enough contrast on all surface levels
- avoid low-contrast pastel-on-white patterns
- avoid decorative color bars that carry meaning without text support
- animation should respect reduced-motion preferences

---

## 12. Implementation Boundary

This baseline does not yet implement:
- React components
- Tailwind config
- Next.js layout code
- Figma files

It does provide the approved starting point for:
- `WBS 3.8` internal result viewer
- `WBS 4.x` admin surfaces
- `WBS 5.x` public grid and dashboard

---

## 13. Follow-On Artifacts

The next natural implementation artifacts are:
- component primitive inventory in code
- token export for frontend build tooling
- admin layout scaffold
- public layout scaffold
- localized label mappings for badge/state names

---

## 14. Change History

| Date | Change |
|---|---|
| 2026-04-10 | Initial FPDS design-system baseline created using Stripe design guidance as a benchmark |
