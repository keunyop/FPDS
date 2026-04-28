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
- protected `/admin` dashboard entry with a breadcrumb-led header, operator greeting, compact attention metrics, and admin-only signup approval only when pending requests exist
- protected admin menu bodies now share a compact breadcrumb-led header pattern such as `Operations > Runs`, with large route-introduction cards and slice-boundary explainer banners removed from the live route surfaces
- protected `/admin` admin-only access-request approval panel for pending signup requests
- protected `/admin/reviews` review queue with active-state defaults, search, filters, sort, and pagination
- protected `/admin/reviews/:reviewTaskId` review detail route with field-selectable evidence trace, model-run context, action history, a dedicated approved-product-name input for safer rename corrections, and approve/reject/defer/edit-approve controls; already-approved and already-edited tasks now reopen into `Edit & approve` for follow-up operator corrections
- protected `/admin/runs` run list with status filters, partial-completion triage, and stable drill-in links
- protected `/admin/runs/:runId` run detail route with stage summary, source processing summary, related review-task links, usage summary, and a `Retry run` action for supported failed collection runs
- protected `/admin/changes` change history route with canonical chronology, changed-field summaries, review/run drilldowns, and manual-override audit context
- protected `/admin/audit` audit log route with append-only chronology, actor and target context, request metadata, and review/run drilldowns
- protected `/admin/usage` usage dashboard v1 with search, provider/stage filters, scope coverage summaries, by-model/by-agent/by-run concentration, trend deltas, and richer anomaly drilldowns
- protected `/admin/health/dashboard` dashboard health route with aggregate freshness, serving fallback, queue visibility, stale or failed state explanation, and a manual retry action
- protected `/admin/banks` bank registry list with search-first layout, white summary cards, comma-separated coverage visibility in the list, multi-bank selection, bulk collect across the selected banks' coverage items, FPDS-styled medium-width dialogs built on Shadcnblocks `offer-modal4` without the left rail, instant local modal open/close state with background detail hydration, EN/KO/JA bank source-language selection, auto-generated bank code, initial coverage selection during bank creation without a visible change-reason field, scheme-tolerant homepage URL handling, streamlined in-place bank detail editing with product-type-based coverage counts and no visible profile change-reason field, guarded bank deletion from the same detail modal, inline per-coverage add and collect controls, and generated-source drill-in that all stay within the list workflow
- `/admin/banks` collect actions now return quickly with queued run ids while homepage discovery, source materialization, and downstream collection continue on the server in the background; no-detail or timeout outcomes are now finalized in `/admin/runs`
- protected `/admin/banks/:bankCode` bank detail route now redirects into the primary `/admin/banks?bank=...` modal workflow for compatibility
- protected `/admin/source-catalog` and `/admin/source-catalog/:catalogItemId` now redirect into the bank-centered workflow for compatibility while the underlying source-catalog APIs remain live; the list modal workflow keeps open/close local and hydrates coverage detail through a small JSON proxy route
- the redirected source-catalog collect actions now share the same background-queued contract as `/admin/banks`, so operators can jump to `/admin/runs` instead of waiting for homepage discovery to finish inside the request
- protected `/admin/sources` generated source registry list with white summary cards, bank/country/product/status/role filters, and read-only drill-in
- protected `/admin/sources/:sourceId` source detail route with read-only metadata visibility, persisted discovery explainability for generated sources, and recent collection history
- protected `/admin/product-types` product type registry with the same modal-first list workflow and white summary cards used by `/admin/banks`, searchable operator-managed definitions, AI-generated discovery keywords from the operator-entered display name and description, narrower add/detail dialogs, list-local add action, local-state modal create/detail editing, full create/edit/delete for operator-managed types, usage-safe delete guards, registry-backed coverage options inside `/admin/banks`, and dynamic-type onboarding that feeds homepage-first discovery plus the generic AI fallback path
- operator-facing delete confirmations use a compact shared destructive alert dialog instead of browser-native confirm popups, and successful product-type deletion closes the product-type detail modal before the list refreshes
- `WBS 5.12` locale rollout is now implemented with EN/KO/JA locale switching on the admin shell and login surface, locale-preserving protected-route navigation, locale-aware operator-facing labels across the main dashboard, signup approval, review queue, run status, product types, banks, generated sources, source catalog, change history, audit log, run detail, and dashboard health surfaces, while keeping evidence, source-derived content, ids, URLs, and operator-entered registry values untouched
- middleware-based route gate backed by the shared session cookie contract
- Shadcnblocks-based admin login and an `application-shell5` collapsible admin shell built on `components.json`, `radix-nova`, app-local shadcn semantic variables, route-group switching, an active-section title plus desktop collapse control in the sidebar header, a footer user menu with placeholder account entry plus icon-led sign-out, locale-preserving navigation, and value-based sidebar active styling so idle rows stay neutral until hovered or actually selected
- vendor-installed shadcn UI primitives under `src/components/ui/` plus edited Shadcnblocks-derived blocks under `src/components/`
- Tailwind 4 or PostCSS frontend foundation under `src/app/globals.css` and `postcss.config.mjs`
- the standalone TypeScript check now runs with `allowJs: true` in `tsconfig.json` so the current Next-generated `.next/types` route validators resolve cleanly during local QA and harness verification
- dashboard health is now a live observability route rather than a reserved placeholder, and it shares the same latest-successful-snapshot serving contract as the public `/products` and `/dashboard` surfaces
