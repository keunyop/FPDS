# FPDS Admin

This package is the authenticated operator workspace. It keeps collection,
review, and canonical-change context private while the Public package
reads only approved projections.

## Operator Workflow

The shell puts four daily tasks first:

1. **Overview** — see only work that needs attention.
2. **Review** — inspect flagged fields, evidence, AI verification, and record a
   guarded decision.
3. **Runs** — find failed or partial collection work and inspect or retry it.
4. **Banks** — add banks manually or through grounded AI research, manage
   coverage, and launch collection. A bank/Product Type with no completed run
   always performs precision source discovery. Completed items expose a
   normal/detailed collection toggle; normal collection uses the current active
   source scope, while detailed collection requests precision rediscovery.

Before entering the workspace, the operator selects an enabled working country
on the login form. The API persists that ISO alpha-2 code in the server-side
session, and the shell keeps it visible in the header. The country owns the
scope of reads and writes, but the operator can switch to another active
country from the header. A switch is confirmed, updates the server-side
session, and returns to Overview in the same language so detail/filter state
does not cross countries.

The sidebar keeps less frequent tools available: Sources, Product Types,
Countries, Changes, Feedback, and Public Health. Feedback is a read-only,
country-scoped inbox for anonymous Public product-error and site-feedback
submissions, with type/category/search filters and immutable product context.
Countries is visible
only to administrators and uses a prepared ISO list: activation adds a login
country, while reversible deactivation preserves history and protects the
current/last active country. Existing Bank and Source Catalog detail URLs
remain compatibility redirects; their APIs are still live.
Authenticated language selection lives in the sidebar Account menu rather than
the global header. Login and Signup use the same EN/KO/JA dropdown pattern as a
standalone control, and every locale change preserves the current route and
non-locale query state.

Review Detail follows one short decision path: candidate identity and three key
facts, recommended action, source check, flagged fields, then the guarded
decision. `Source check` is expanded initially because provenance is required
for a safe review. Product facts, other collected fields, advanced overrides,
decision notes, diff, evidence trace, and audit context remain available through
collapsed disclosure. AI verification opens only for active verification or an
attention state; its `Official sources` list stays collapsed until requested.
This presentation does not change correction, CSRF, RBAC, audit, canonical, or
publication boundaries.

Review Queue search, reset, page-size changes, pagination, and visible auto
refresh update only the results region through the authenticated same-origin
Admin proxy. Page size is selectable as `20`, `50`, or `100` with `20` as the
default. The active search/filter/sort/page state remains in the URL and is
carried into Review Detail, so Back, Reject, and Defer return to the same queue
context.

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
Banks list rows, AI-onboarding results, and bank-detail previews reuse
`src/components/fpds/admin/bank-logo-mark.tsx`: every asset keeps its aspect
ratio inside the same unframed `48x24` image viewport and `56x40` layout slot.

## Safety Boundaries

- Preserve EN/KO/JA locale query propagation and source-language content.
- Never treat a client query parameter as the Admin country authority. Reads
  and writes derive country from the authenticated server-side session.
- Keep header switching limited to active countries and CSRF-protected,
  and redirected to Overview rather than preserving a country-owned route.
- Keep platform-wide account administration conceptually separate
  from country-owned bank, source, collection, review, and product data.
- Keep `Add banks with AI` admin-only and tied to the displayed server-session
  country. Its result must retain clickable ranking/homepage/coverage evidence
  and must not imply that product collection or Public release has occurred.
- Keep Banks workflow logos on the shared fixed-footprint mark; do not size
  individual bank assets ad hoc or reintroduce a visible logo frame.
- Treat country removal as reversible deactivation. Never physically delete a
  country row or accept a free-form country identity from the browser.
- Preserve session cookies, CSRF headers, RBAC, proxy status/body forwarding,
  query parameter names, and mutation timeout behavior.
- Keep Review Queue query fields allowlisted and accept detail return context
  only for the same-origin `/admin/reviews` route.
- Do not expose evidence, review state, or private source traces to Public.
- Keep Feedback reads scoped to the authenticated session country. Feedback
  does not mutate canonical product data or create a Review decision.
- Keep `/admin/source-catalog/*` proxy handlers: Banks collection uses them even
  though the matching page routes redirect.
- Treat `has_completed_collection` as server-owned history. The UI may request
  precision rediscovery for completed items, but it must not provide a way to
  bypass required first-time discovery. Mixed bulk selections apply the option
  only to completed items.
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
