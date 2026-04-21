# Dashboard Health Route Shell

Route: `/admin/health/dashboard`

Purpose:
- inspect public aggregate freshness and serving health

Current runtime:
- live Next.js route now exists in `app/admin/src/app/admin/health/dashboard/`
- shows latest successful serving snapshot, queued or in-progress refresh work, stale or failed state, and manual retry
