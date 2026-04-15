# Public App Surface

Use this area for the public Product Grid and Insight Dashboard experience.

Planned scope:
- anonymous browser UI
- public product grid
- public dashboard
- locale-aware public rendering

Current scaffold:
- `routes.manifest.json` lists the reserved public routes.
- `route-shells/` holds route-by-route placeholders for the future public runtime.
- the future public runtime should follow the Next.js + Shadcnblocks template-first baseline from `docs/03-design/fpds-design-system.md` and `docs/03-design/fpds_design_system_stripe_benchmark.md`.

Current runtime:
- a live Next.js public package now lives under `src/`
- `/` redirects to `/products`
- `/products` renders the `WBS 5.9` Product Grid UI against `GET /api/public/products` and `GET /api/public/filters`
- `/dashboard` now renders the `WBS 5.10` Insight Dashboard UI against `GET /api/public/dashboard-summary`, `GET /api/public/dashboard-rankings`, `GET /api/public/dashboard-scatter`, and `GET /api/public/filters`
- `WBS 5.11` is now implemented with URL-based shared scope preservation across sibling navigation plus dashboard-to-grid drill-in links from breakdowns, ranking rows, and scatter points
- `WBS 5.12` is now implemented with EN/KO/JA locale switching, locale-preserving sibling navigation, locale-aware page metadata, and locale-aware labels or freshness copy while keeping source-derived product content in its original language
- `WBS 5.13` is now implemented with locale-aware methodology/freshness note cards on `/products`, richer public methodology note wording on `/dashboard`, and refreshed public note copy that explains snapshot timing, metric semantics, exclusion rules, and public evidence boundaries
- the public app uses the same `radix-nova` style family as the admin app, but with a more relaxed public layout rhythm
