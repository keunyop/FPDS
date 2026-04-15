# Admin App Surface

Use this area for authenticated operator-facing pages.

Planned scope:
- review queue
- review detail and trace
- runs
- change history
- audit log
- publish monitor
- usage and health surfaces

Current scaffold:
- `routes.manifest.json` lists the reserved admin routes and visibility expectations.
- `route-shells/` keeps the original route-by-route design placeholders.
- the live Next.js admin package for `WBS 4.1` to `4.10` now lives alongside this scaffold under `src/`.
- future admin surfaces should follow the template-first baseline from `docs/03-design/fpds-design-system.md` and `docs/03-design/fpds_design_system_stripe_benchmark.md`.

Current runtime:
- `/admin/login` login screen
- protected `/admin` overview entry
- protected `/admin/reviews` review queue with active-state defaults, search, filters, sort, and pagination
- protected `/admin/reviews/:reviewTaskId` review detail route with field-selectable evidence trace, model-run context, action history, and approve/reject/defer/edit-approve controls
- protected `/admin/runs` run list with status filters, partial-completion triage, and stable drill-in links
- protected `/admin/runs/:runId` run detail route with stage summary, source processing summary, related review-task links, and usage summary
- protected `/admin/changes` change history route with canonical chronology, changed-field summaries, review/run drilldowns, and manual-override audit context
- protected `/admin/audit` audit log route with append-only chronology, actor and target context, request metadata, and review/run drilldowns
- protected `/admin/usage` usage dashboard v1 with search, provider/stage filters, scope coverage summaries, by-model/by-agent/by-run concentration, trend deltas, and richer anomaly drilldowns
- `WBS 5.12` locale rollout is now implemented with EN/KO/JA locale switching on the admin shell and login surface, locale-preserving protected-route navigation, and locale-aware operator-facing labels while keeping evidence and source-derived content untouched
- middleware-based route gate backed by the shared session cookie contract
- Shadcnblocks-based admin login and shell built on `components.json`, `radix-nova`, and app-local shadcn semantic variables
- vendor-installed shadcn UI primitives under `src/components/ui/` plus edited Shadcnblocks-derived blocks under `src/components/`
- Tailwind 4 or PostCSS frontend foundation under `src/app/globals.css` and `postcss.config.mjs`
- the standalone TypeScript check now runs with `allowJs: true` in `tsconfig.json` so the current Next-generated `.next/types` route validators resolve cleanly during local QA and harness verification
