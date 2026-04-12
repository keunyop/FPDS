# App Surface

This directory holds browser-facing FPDS surfaces.

Current boundary:
- `public/` for anonymous public experience
- `admin/` for authenticated operator experience
- `prototype/` for the read-only prototype result viewer used before full admin ops scope

This is a vendor-neutral skeleton for WBS `2.1`.
Current implementation note:
- `app/prototype/index.html` now implements the WBS `3.8` read-only internal result viewer
- public and admin route implementation still start in later WBS items
