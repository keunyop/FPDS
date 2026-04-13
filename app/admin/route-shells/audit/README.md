# Audit Log Route Shell

Route: `/admin/audit`

Purpose:
- inspect append-only audit events over time
- drill back into review or run context when audit history explains an operator action

Current scaffold:
- protected route is live in `src/app/admin/audit/page.tsx`
- table-first chronology, filters, actor and target context, request metadata, and review or run drilldowns landed in `4.7`
