# Shared Config

Use this area for shared config contracts and environment loading helpers.

Current baseline:
- [../../docs/03-design/dev-prod-environment-spec.md](../../docs/03-design/dev-prod-environment-spec.md) defines the tracked config contract for `dev` and `prod`.
- [../../.env.dev.example](../../.env.dev.example) is the starting point for local or shared `dev`.
- [../../.env.prod.example](../../.env.prod.example) is the placeholder-only inventory for `prod`.

Rules:
- Keep real secrets out of git. Only placeholder-only example files are tracked.
- Treat local development as a form of `dev`, not as a third environment.
- Keep browser-facing origins, private worker/storage settings, and BX-PF credentials separated by environment.
- Real BX-PF write-back is `prod` only. `dev` stays `mock` or `disabled`.

WBS follow-on:
- `2.3` DB and migration baseline consumes the database contract from the env spec.
- `2.4` object storage setup consumes the storage and evidence prefix contract.
- `2.5` auth scaffold consumes the session and CSRF secret contract.
- `2.7` monitoring baseline consumes the monitoring provider and DSN contract.
- `2.8` security baseline consumes the origin, cookie, and crawler fetch contract.
