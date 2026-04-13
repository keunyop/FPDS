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

Current runtime:
- `/admin/login` login screen
- protected `/admin` overview entry
- middleware-based route gate backed by the shared session cookie contract
- shared-design-token-driven admin shell aligned to the refreshed FPDS benchmark
- local `src/app/theme.css` mirrors the shared token export because the Next.js app cannot import workspace-level global CSS directly during production build
