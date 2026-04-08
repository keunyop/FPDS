# Admin Auth Route Scaffold

Reserved routes:
- `POST /api/admin/auth/login`
- `POST /api/admin/auth/logout`
- `GET /api/admin/auth/session`

Baseline rules:
- human operator login only
- server-side session cookie
- no browser-held bearer token
- login provider intentionally not chosen yet
- runtime CSRF applies to authenticated write routes, not the anonymous login entrypoint

Follow-on:
- `4.1` admin login implementation
