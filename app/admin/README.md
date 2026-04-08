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
- `route-shells/` holds route-by-route placeholders without locking a framework router.

No runtime auth or page implementation is added yet.
