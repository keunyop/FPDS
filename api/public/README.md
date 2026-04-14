# Public API Boundary

Use this area for `/api/public/*` endpoints.

Live scope:
- products
- filters
- dashboard summary
- dashboard rankings
- dashboard scatter

Current implementation:
- `route-manifest.json` lists the reserved anonymous read-only public routes.
- the live FastAPI service under `api/service/` now serves:
  - `GET /api/public/products`
  - `GET /api/public/filters`
  - `GET /api/public/dashboard-summary`
  - `GET /api/public/dashboard-rankings`
  - `GET /api/public/dashboard-scatter`
- the current `5.8` implementation derives filtered dashboard responses from the latest successful `public_product_projection` snapshot so grid and dashboard can share the same request-time filter vocabulary.
