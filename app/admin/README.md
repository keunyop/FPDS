# Admin App Surface

Use this area for authenticated operator-facing pages.

Planned scope:
- review queue
- review detail and trace
- runs
- change history
- audit log
- bank registry management
- source catalog management and collection
- generated source detail inspection
- publish monitor
- usage and health surfaces

Current scaffold:
- `routes.manifest.json` lists the reserved admin routes and visibility expectations.
- `route-shells/` keeps the original route-by-route design placeholders.
- the live Next.js admin package for `WBS 4.1` to `5.15` now lives alongside this scaffold under `src/`.
- future admin surfaces should follow the template-first baseline from `docs/03-design/fpds-design-system.md` and `docs/03-design/fpds_design_system_stripe_benchmark.md`.

Current runtime:
- `/admin/login` login screen
- `/admin/signup` access-request screen
- protected `/admin` dashboard entry with a real-data Operational Attention Rail that orders run failures, review workload, Public aggregate health, and signup requests by severity and owning route
- protected admin menu bodies share a compact breadcrumb-led header, deep operational frame, cool mineral canvas, restrained teal action color, semantic state vocabulary, joined summary bands, and bounded data regions rather than equal KPI-card grids
- protected `/admin` admin-only access-request approval panel for pending signup requests
- protected `/admin/reviews` review queue with active-state defaults, search, registry-backed active-bank and Product Type filters, sort, pagination, bounded table overflow, queued/deferred row multi-select with bulk defer only, and bank → product → problem/action → severity/confidence → state/time → reference-ID scan order; exact mobile widths receive a dedicated work-card view rather than a compressed desktop table
- protected `/admin/reviews/:reviewTaskId` review detail route with a problem-first correction workspace and sticky desktop decision rail: missing or suspect fields open first, other fields and technical evidence remain progressively disclosed, locale is preserved through queue/run/decision navigation, and edit/decision state pauses refresh while inline evidence, diff preview, alternatives, audit context, and canonical context stay available
- review detail comparable fields expose their canonical JSON type/unit contract and render concise field-level notes with an asterisk so conditions do not contaminate sortable rate, money, boolean, or structured values
- protected `/admin/runs` run list with status filters, partial-completion triage, stable drill-in links, and an operator-focused table that omits lower-value correlation, actor, and retry-chain columns from the list view
- protected `/admin/runs` now keeps its wide diagnostic table inside the application shell and renders the run snapshot as direct stat cards without an extra outer card
- admin table/list routes visibly report live/paused/last-refresh state and refresh server data every 15 seconds; refresh pauses while the tab is hidden, a form control is being edited, a dialog is open, unsaved state exists, or an operator mutation is in progress
- protected `/admin/runs/:runId` run detail route with a numbered execution lifecycle strip, failure-first alert, source impact, related review workload, usage, retry context, guarded retry action, and mutation-safe refresh behavior
- admin-owned date and timestamp displays use fixed `yyyy-mm-dd hh:mm` formatting, with seconds shown as `yyyy-mm-dd hh:mm:ss` only on source-registry timestamps that intentionally include seconds
- protected `/admin/changes` change history route with direct snapshot stat cards, canonical chronology, changed-field summaries, review/run drilldowns, and manual-override audit context
- protected `/admin/audit` audit log route with direct snapshot stat cards, bounded table overflow, append-only chronology, actor/target/reason context, and review/run drilldowns while hiding lower-level request and retention metadata from the primary table
- protected `/admin/usage` usage observability route with cost → anomaly → model concentration → trend priority, compact scope controls, locale-aware formatting, bounded concentration tables, and review/run drilldowns based only on observed usage signals
- protected `/admin/health/dashboard` dashboard health route led by the snapshot currently served to Public, freshness gap, canonical-change time, pending work, fallback/attempt state, and a guarded manual retry action
- protected `/admin/banks` bank registry list with search-first layout, white summary cards, comma-separated coverage visibility in the list, multi-bank selection, bulk collect across the selected banks' coverage items, FPDS-styled medium-width dialogs built on Shadcnblocks `offer-modal4` without the left rail, instant local modal open/close state with background detail hydration, EN/KO/JA bank source-language selection, auto-generated bank code, initial coverage selection during bank creation without a visible change-reason field, scheme-tolerant homepage URL handling, streamlined in-place bank detail editing with product-type-based coverage counts, no visible profile change-reason field, no coverage explainer paragraph, guarded bank deletion from the same detail modal, inline per-coverage add and collect controls, and generated-source drill-in that all stay within the list workflow
- `/admin/banks` collect actions now return quickly with queued run ids while homepage discovery, source materialization, and downstream collection continue on the server in the background; per-coverage queued feedback is intentionally terse, and no-detail or timeout outcomes are finalized in `/admin/runs`
- protected `/admin/banks/:bankCode` bank detail route now redirects into the primary `/admin/banks?bank=...` modal workflow for compatibility
- protected `/admin/source-catalog` and `/admin/source-catalog/:catalogItemId` now redirect into the bank-centered workflow for compatibility while the underlying source-catalog APIs remain live; the list modal workflow keeps open/close local and hydrates coverage detail through a small JSON proxy route
- the redirected source-catalog collect actions now share the same background-queued contract as `/admin/banks`, so operators can jump to `/admin/runs` instead of waiting for homepage discovery to finish inside the request
- protected `/admin/sources` generated source registry list with white summary cards, bank/country/product/status/role filters, Search actions, bounded table overflow inside the application shell, URL wrapping, yyyy-mm-dd hh:mm:ss updated timestamps, and source detail drill-in
- protected `/admin/sources/:sourceId` source detail route with operator-focused source identity, URL, role/status, verification timestamps, compact discovery summary, recent collection history, and admin-only soft removal for bad generated source details
- protected `/admin/product-types` product type registry with the same modal-first list workflow and white summary cards used by `/admin/banks`, searchable operator-managed definitions, AI-generated discovery keywords from the operator-entered display name and description, narrower add/detail dialogs, list-local add action, local-state modal create/detail editing, full create/edit/delete for operator-managed types, usage-safe delete guards, registry-backed coverage options inside `/admin/banks`, and dynamic-type onboarding that feeds homepage-first discovery plus the generic AI fallback path
- operator-facing delete confirmations use a compact shared destructive alert dialog instead of browser-native confirm popups, and successful product-type deletion closes the product-type detail modal before the list refreshes
- `WBS 5.12` locale rollout is implemented with pre-hydration EN/KO/JA document language, locale-preserving shell/queue/detail/run/usage navigation, translated core operator UI on Review Detail, Usage, and Source Detail, and locale-aware numbers/dates while evidence, source-derived content, ids, URLs, reason codes, and operator-entered values remain untouched
- middleware-based route gate backed by the shared session cookie contract, with Login and access-request Signup intentionally remaining anonymous routes
- the Login and Signup routes use the same secure two-zone Admin entrance, 44px form controls, live error/success feedback, and post-submit completion state; the authenticated shell uses actual route links for desktop modules and mobile bottom navigation rather than sidebar-group-only controls
- shared route loading/error recovery, global visible focus, reduced-motion behavior, 40px minimum compact controls, keyboard-accessible table scrollers, semantic status tokens, accessible dialogs, and clear empty/disabled/in-progress states form the Admin interaction baseline
- vendor-installed shadcn UI primitives under `src/components/ui/` plus edited Shadcnblocks-derived blocks under `src/components/`
- Tailwind 4 or PostCSS frontend foundation under `src/app/globals.css` and `postcss.config.mjs`
- the standalone TypeScript check now runs with `allowJs: true` in `tsconfig.json` so the current Next-generated `.next/types` route validators resolve cleanly during local QA and harness verification
- dashboard health is now a live observability route rather than a reserved placeholder, and it shares the same latest-successful-snapshot serving contract as the public `/products` and `/dashboard` surfaces
