# Shared Observability

Use this area for logging, correlation, error tracking, and usage-related helpers shared by API and workers.

Current baseline:
- [../../docs/03-design/monitoring-error-tracking-baseline.md](../../docs/03-design/monitoring-error-tracking-baseline.md) defines the shared observability contract.
- [error-envelope.example.json](error-envelope.example.json) shows the safe browser-facing error response shape.
- [structured-log-event.example.json](structured-log-event.example.json) shows the structured internal event shape.

Rules:
- treat `request_id`, `correlation_id`, and `run_id` as separate fields with different scopes
- keep browser-facing error responses controlled and traceable
- avoid stack traces, secrets, raw SQL, private paths, and raw storage URLs in user-facing responses
- keep monitoring provider selection in env, not hard-coded in shared helpers

WBS follow-on:
- `2.7` monitoring and error tracking baseline consumes the env observability contract
- `4.5` run status can use the same error summary vocabulary
- `4.8` usage tracking should share `run_id` and `correlation_id`
- `7.8` external API monitoring and audit separation should extend, not replace, this baseline
