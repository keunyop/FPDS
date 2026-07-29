# FPDS Admin

This package is the authenticated operator workspace. It keeps collection,
review, canonical-change, and audit context private while the Public package
reads only approved projections.

## Operator Workflow

The shell puts four daily tasks first:

1. **Overview** — see only work that needs attention.
2. **Review** — inspect flagged fields, evidence, AI verification, and record a
   guarded decision.
3. **Runs** — find failed or partial collection work and inspect or retry it.
4. **Banks** — manage bank coverage and launch collection.

The sidebar keeps less frequent tools available: Sources, Product Types,
Changes, Audit Log, Usage, and Public Health. Existing Bank and Source Catalog
detail URLs remain compatibility redirects; their APIs are still live.

## Code Map

```text
src/app/admin/                    route composition and internal proxy handlers
src/components/fpds/admin/        Admin shell and workflow/domain surfaces
src/components/ui/                reusable vendor UI primitives
src/lib/admin-api.ts              server-side Admin API client and response types
src/lib/admin-i18n.ts             locale-preserving URLs and Admin translations
src/middleware.ts                 protected-route session gate
routes.manifest.json              current page-route-to-file map
```

The shared shell is `src/components/fpds/admin/admin-shell.tsx`. Numbered
vendor-derived blocks were renamed after adaptation so handoff readers see
their FPDS role first; vendor provenance remains recorded in the design logs.

## Safety Boundaries

- Preserve EN/KO/JA locale query propagation and source-language content.
- Preserve session cookies, CSRF headers, RBAC, proxy status/body forwarding,
  query parameter names, and mutation timeout behavior.
- Do not expose evidence, review state, or private source traces to Public.
- Keep `/admin/source-catalog/*` proxy handlers: Banks collection uses them even
  though the matching page routes redirect.
- Keep `data-admin-dirty` and mutation-pending signals so automatic refresh
  pauses during edits, dialogs, and writes.

## Local Commands

From this directory:

```powershell
pnpm install --frozen-lockfile
pnpm run dev
pnpm run typecheck
pnpm run build
```

Admin runs on `http://localhost:3001`. Copy `.env.example` to the appropriate
local environment file and follow the root README for the API/database startup
order.
