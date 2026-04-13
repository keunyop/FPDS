# Review Detail Route Shell

Route: `/admin/reviews/:reviewTaskId`

Purpose:
- review decision surface
- field-level evidence and trace viewer entrypoint

Current scaffold:
- a live review-detail route now exists under `app/admin/src/app/admin/reviews/[reviewTaskId]/page.tsx`
- the current runtime includes candidate summary, field-selectable normalized fields, trace drilldown, model-run references, decision form, override diff preview, and action history through `WBS 4.4`
