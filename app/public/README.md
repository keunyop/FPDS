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
- `/dashboard` remains a lightweight placeholder until `WBS 5.10` implements the real dashboard UI
- the public app uses the same `radix-nova` style family as the admin app, but with a more relaxed public layout rhythm
