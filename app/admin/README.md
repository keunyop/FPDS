# Admin App Surface

Use this area for authenticated operator-facing pages.

Planned scope:
- review queue
- review detail and trace
- runs
- change history
- publish monitor
- usage and health surfaces

Current scaffold:
- `routes.manifest.json` lists the reserved admin routes and visibility expectations.
- `route-shells/` keeps the original route-by-route design placeholders.
- the live Next.js admin package for `WBS 4.1` now lives alongside this scaffold under `src/`.
- future admin surfaces should follow the template-first baseline from `docs/03-design/fpds-design-system.md` and `docs/03-design/fpds_design_system_stripe_benchmark.md`.

Current runtime:
- `/admin/login` login screen
- protected `/admin` overview entry
- middleware-based route gate backed by the shared session cookie contract
- Shadcnblocks-based admin login and shell built on `components.json`, `radix-nova`, and app-local shadcn semantic variables
- vendor-installed shadcn UI primitives under `src/components/ui/` plus edited Shadcnblocks-derived blocks under `src/components/`
- Tailwind 4 or PostCSS frontend foundation under `src/app/globals.css` and `postcss.config.mjs`
