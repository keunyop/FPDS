# Admin Auth Route Scaffold

Reserved routes:
- `POST /api/admin/auth/login`
- `POST /api/admin/auth/logout`
- `GET /api/admin/auth/session`

Baseline rules:
- human operator login only
- server-side session cookie
- no browser-held bearer token
- DB-backed user accounts
- runtime CSRF applies to authenticated write routes, not the anonymous login entrypoint

Follow-on:
- runtime implementation now lives in `api/service/api_service/main.py`
- future authenticated write routes can reuse the stored session and CSRF token model
