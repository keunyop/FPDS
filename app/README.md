# Browser Apps

FPDS keeps its browser surfaces in separate packages so public data exposure and
operator authentication cannot drift into one runtime.

- `admin/` — authenticated operator workflows on port `3001`.
- `public/` — anonymous approved-data experience on port `3000`.
- `prototype/` — retained read-only result viewer used by the worker exporter.

Each live package owns its App Router routes, route manifest, dependencies,
environment example, and verification commands. See the package README before
changing a surface.
