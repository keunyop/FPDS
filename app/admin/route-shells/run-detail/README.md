# Run Detail Route Shell

Route: `/admin/runs/:runId`

Purpose:
- diagnose a single run
- link to related review tasks and usage summary

Current runtime:
- protected run detail is live
- source processing summary, error summary, related review tasks, and usage summary are implemented in `src/app/admin/runs/[runId]`
