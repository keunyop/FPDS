# Shared Modules

This directory holds cross-surface modules reused by app, API, and workers.

Current boundary:
- `config/` shared config shape and environment readers
- `contracts/` shared request, response, and orchestration contracts
- `design/` shared design bridge artifacts, template-adoption notes, and UI vocabulary
- `domain/` canonical schema, validation, and business vocabulary
- `i18n/` localization resources and helpers
- `observability/` logging, error, and usage helpers
- `security/` shared security primitives and policy helpers

No runtime implementation is added in WBS `2.1`.
