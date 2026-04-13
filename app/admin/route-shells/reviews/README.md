# Review Queue Route Shell

Route: `/admin/reviews`

Purpose:
- reviewer work intake
- list active `queued` and `deferred` review tasks

Current scaffold:
- live route now exists under `app/admin/src/app/admin/reviews/page.tsx`
- current runtime includes active-state defaults, search, filters, sort, pagination, and a table-first reviewer intake surface
- review decisions now land on the live `/admin/reviews/:reviewTaskId` detail route
- full trace drilldown remains deferred to `4.4`
