# Internal API Boundary

Use this area for private orchestration interfaces between API, workers, and schedulers.

Planned rules:
- not browser-facing
- carries `run_id` and `correlation_id`
- passes DB/object reference ids instead of raw artifacts when possible

No interface implementation is added in WBS `2.1`.
