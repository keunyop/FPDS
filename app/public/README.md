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
- `/` redirects to `/dashboard` so FPDS opens on the public Home view
- `/dashboard` renders a simplified public Home view with current scope, freshness, product count, bank count, peak rate, top deposit comparisons, and links into the Deposit catalog
- `/products` renders the `WBS 5.9` Product Grid UI against `GET /api/public/products` and `GET /api/public/filters`
- `/methodology` renders the public data-boundary and metric notes without exposing evidence traces or source excerpts
- the public header shows `FPDS`, Home, Deposit, a disabled Loan entry, and a dropdown language selector; Methodology remains available by route but is no longer a top-level header menu item
- `WBS 5.11` is now implemented with URL-based shared scope preservation across sibling navigation plus dashboard-to-grid drill-in links from ranking rows
- `WBS 5.12` is now implemented with EN/KO/JA locale switching, locale-preserving sibling navigation, locale-aware page metadata, and locale-aware labels or freshness copy while keeping source-derived product content in its original language
- `WBS 5.13` is now implemented with locale-aware methodology/freshness note cards on `/products`, richer public methodology note wording on `/dashboard`, and refreshed public note copy that explains snapshot timing, metric semantics, exclusion rules, and public evidence boundaries
- public-owned date and freshness timestamp displays use fixed `yyyy-mm-dd` and `yyyy-mm-dd hh:mm` formatting instead of locale-specific long date strings
- the public app uses the same `radix-nova` style family as the admin app, with `@shadcnblocks/dashboard10`-installed chart/table primitives adapted through FPDS-owned domain components
