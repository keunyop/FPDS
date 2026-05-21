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
- `/dashboard` renders a simplified public Home view with a short headline, market greeting, polished KPI cards, and a `Top 5 Interest Rate` comparison table with links into the Deposit catalog and product detail pages
- `/products` renders the simplified Deposit catalog against `GET /api/public/products` and `GET /api/public/filters`, with compact collapsible filter controls, official bank-page actions placed in the top-right of product cards when available, comparison-focused metric cards, and no product-card Changed/Verified date footer
- `/products/[productId]` renders public product facts from `GET /api/public/products/:productId` and provides a direct official bank product-page action when the public projection has a URL
- `/methodology` renders the public data-boundary and metric notes without exposing evidence traces or source excerpts
- the public header shows a simple FPDS logo mark, a medium-weight `FPDS` brand title, Home, Deposit, a disabled Loan entry, and a dropdown language selector; Methodology remains available by route but is no longer a top-level header menu item
- `WBS 5.11` is now implemented with URL-based shared scope preservation across sibling navigation plus dashboard-to-grid drill-in links from ranking rows
- `WBS 5.12` is now implemented with EN/KO/JA locale switching, locale-preserving sibling navigation, locale-aware page metadata, and locale-aware labels or freshness copy while keeping source-derived product content in its original language
- `WBS 5.13` is now implemented with locale-aware methodology/freshness wording on the public surface, while `/products` now keeps catalog chrome minimal and leaves detailed data-boundary copy to `/methodology`
- public-owned date and freshness timestamp displays use fixed `yyyy-mm-dd` and `yyyy-mm-dd hh:mm` formatting instead of locale-specific long date strings
- the public app uses the same `radix-nova` style family as the admin app, with `@shadcnblocks/dashboard10`-installed chart/table primitives adapted through FPDS-owned domain components
