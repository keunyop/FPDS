# Shared Security

Use this area for shared security primitives, policy contracts, and future runtime helpers.

Current scaffold:
- `auth-session.contract.json` defines the vendor-neutral admin session baseline.
- `rbac-role-matrix.json` captures the `admin`, `reviewer`, and `read_only` action matrix.
- `browser-security-policy.json` captures the baseline header, cookie, CORS, and admin browser rules.
- `safe-fetch-policy.example.json` captures the crawler allowlist and SSRF guard baseline.
- `secret-inventory.example.json` captures the minimum secret rotation and audit inventory.

Rules:
- Keep the auth scaffold human-operator focused. Browser admin auth uses server-side sessions, not browser-held bearer tokens.
- Keep runtime provider choice open. Do not lock an auth vendor or web framework in this folder.
- Treat public, admin, internal, and worker boundaries as separate trust zones.
- Keep raw object paths, storage keys, and private network fetches out of browser-facing surfaces.

WBS follow-on:
- `2.5` auth scaffold
- `2.8` security baseline
- `4.1` admin login implementation
- `6.5` release hardening verification
