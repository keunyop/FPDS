# API Service

The live FastAPI application is entirely under `service/`. It owns anonymous
Public reads, authenticated Admin reads and mutations, session/CSRF/RBAC
enforcement, aggregate refresh, and worker launch integration.

Start with:

- `service/README.md` for runtime and endpoint guidance.
- `service/api_service/main.py` for route registration.
- `service/api_service/routers/` for route ownership.
- `service/tests/` for behavior and security coverage.

The authoritative interface description is
`docs/03-design/api-interface-contracts.md`; obsolete placeholder API
directories and partial route manifests are intentionally not retained.
