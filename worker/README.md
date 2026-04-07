# Worker Boundary

This directory holds private pipeline and integration workers.

Current boundary:
- `discovery/` for source discovery and registry-driven fetch entry
- `pipeline/` for parse, chunk, extraction, normalization, validation, and review routing work
- `publish/` for BX-PF-facing publish and reconciliation work
- `runtime/` for worker bootstrap, scheduling, and execution plumbing

No worker implementation is added in WBS `2.1`.
