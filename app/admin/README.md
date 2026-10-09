# FPDS Admin

## Product Type collection targets - 2026-10-04

Product Type detail groups protected identity/currency and alternative/conditional
financial requirements, then manages typed additional fields as required,
optional or outside the target list. Only admins can edit; read-only operators
can inspect. Settings apply to the session country and the next collection plan;
CA and US overrides remain separate. Verified optional facts encountered in the
same official evidence remain preserved; unknown values are omitted.

Apply migration `0047_product_type_collection_fields.sql` before deploying the
API/Worker and Admin together. Local verification does not apply live settings,
start collection, publish data or deploy the runtime.



Current optional collection rule (2026-10-01): required facts determine publication;
profile and explicitly registered typed optional facts are also extracted when
proven by the same captured/consulted official evidence. Missing optional entries
are omitted without extra searches, retries or human review. Normalization preserves
verified optional values even for older source field lists. Collection-runtime
deployment is required; this change performs no live recollection or data writes.

## Product collection workflow — 2026-09-30

Daily work is Overview, Runs and Banks. Collection automatically accepts proven
facts or excludes candidates. Runs show automatic exclusions. Review has moved
to More tools as read-only history; the detail route has no approval/edit/defer
or AI action, and list rows have no bulk selection. Signup approval remains.
Earlier reviewer workflow descriptions are historical for product collection.
See [policy](../../docs/03-design/collection-accuracy-policy.md).

This package is the authenticated operator workspace. It keeps collection,
review, and canonical-change context private while the Public package
reads only approved projections.

For current operator flows, read the
[Admin manual](../../descent/FPDS_Admin_사용자_매뉴얼.md). For localization, feature
changes and AI skills, start with the
[development guide](../../descent/FPDS_Admin_개발_가이드.md).

## Operator Workflow

Daily work is Overview, Runs and Banks:

1. **Overview** — inspect collection failures, public-data health and signup requests.
2. **Runs** — inspect queued/discovering/collecting and terminal outcomes, automatic
   exclusions and source errors. Use Search or safe 15-second Auto refresh;
   Advanced filters start collapsed.
3. **Banks** — manage banks and coverage, then launch normal/detailed collection.
   First-time eligible scopes require precision discovery; skipped scopes keep
   terminal Runs and an exclusion reason.

The operator selects an active working country at login. The API owns that
country in the server session; confirmed switching returns to Overview in the
same language, so country-owned detail/filter context does not cross countries.
Authenticated locale selection and logout live in the sidebar Account menu.

More tools contains read-only Review history, Sources, Product Types, Changes,
Countries and Public Health. Countries and signup approval are admin-only.
Historical Review list/detail preserve private evidence and decisions but offer
no approve/reject/defer/edit-approve, AI Verify or bulk actions. New collection
automatically accepts or excludes candidates without creating review tasks.

Existing Bank/Source Catalog page URLs remain compatibility redirects; their
proxy APIs are still used by Banks. Anonymous Public feedback belongs to the
separate Public application.

## Code Map

```text
src/app/admin/                    route composition and internal proxy handlers
src/components/fpds/admin/        Admin shell and workflow/domain surfaces
src/components/ui/                reusable vendor UI primitives
src/lib/admin-api.ts              server-side Admin API client and response types
src/lib/admin-i18n.ts             locale-preserving URLs and Admin translations
middleware.ts                     protected-route session gate
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
- Keep platform-wide account administration and the shared Product Type
  definition registry separate from country-owned bank, source, collection,
  review, and product data. Market approval profiles are country/type-specific.
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
- Keep `/admin/source-catalog/*` proxy handlers: Banks collection uses them even
  though the matching page routes redirect.
- Treat `has_completed_collection` as server-owned history. Offer explicit
  precision rediscovery for every active coverage, including a held first-time
  scope; the API still enforces required initial discovery. Inactive coverage
  cannot collect until it is explicitly restored.
- Render collection `skipped_items` in EN/KO/JA with the actual created-run count,
  reasons and precision-rediscovery guidance. All-skipped requests retain terminal
  Runs; already active preparations reuse their existing work without duplicates.
  Mixed selections report both queued and excluded work.
  Revalidation checks fresh evidence and cannot bypass automatic financial gates.
- Keep `data-admin-dirty` and mutation-pending signals so automatic refresh
  pauses during edits, dialogs, and writes.

## Current Capability Boundaries

- API mutations for registries, collection, Runs retry and Public Health retry
  require `admin`; `read_only` has no mutation rights. Countries and signup
  approval are admin-only. Historical product-review mutations are retired.
- Sources are inspectable and support admin-only soft removal. Their direct
  create/update APIs return `405`; bank coverage owns configuration.
- Collection is operator-initiated. Evidence validation, qualified candidate
  promotion and aggregate refresh run automatically within that workflow.
  No human product review, Review AI autopilot or recurring collection scheduler
  is part of current collection.
- There is no standalone Product Record, Publish Monitor, Audit, Usage, global
  search, localization-health, or existing-account-management page.

## Vercel Deployment

Current deployed Admin: https://fpds-three.vercel.app. Production API Admin
origin settings must use that exact origin. Server hosting instructions are in
the [persistent API/Worker guide](../../api/service/PERSISTENT_HOST.md).

Use a separate Next.js Vercel project with Root Directory `app/admin`, Node 24
and the package's frozen pnpm lockfile. Install/build explicitly run
`npx --yes pnpm@10.33.0`; no repository-root Corepack discovery is required.
The root Vercel project remains FastAPI.
See the [Admin Vercel deployment guide](VERCEL.md) for exact project/environment
settings, Preview isolation, smoke checks, collection-host limits and rollback.

`FPDS_ADMIN_API_ORIGIN` is server-only. Browser countries/login/signup/logout
use the bounded same-origin `/api/admin/auth/[action]` handlers, so session/CSRF
cookies belong to the Admin host even when API and Admin use separate domains.
API roles, country isolation and CSRF remain authoritative. Hosted configuration
requires an explicit remote HTTPS origin. Web deployment alone does not move the
current long-running API/Worker collection process to Vercel.

## Local Commands

From this directory:

```powershell
pnpm install --frozen-lockfile
pnpm run dev
pnpm run typecheck
pnpm run test
pnpm run build
```

Admin runs on `http://localhost:3001`. Copy `.env.example` to the appropriate
local environment file and follow the root README for the API/database startup
order.

## Handover Hardening

- The environment badge comes from the authenticated API session's environment
  (dev/prod), never from the Next.js build mode. An older API without this field
  shows an unknown mark.
- Overview counts the union of failed and partial runs across all default run
  states, including completed partial runs, once per run. Its Runs link keeps
  completed partial runs reachable.
- Login return destinations stay under the same-origin /admin path and keep
  the selected locale.
- Logout sends the session CSRF token, has a 15-second timeout, and returns to
  Login only after success. Failures remain visible with a localized retry
  message because the session may still be active.
- The Account menu contains working locale and logout controls; the disabled
  account-settings placeholder is removed. Account lifecycle tooling is pending
  explicit approval; see descent/02-release-readiness.md at repository root.
- Web responses set frame-ancestor/object/base restrictions, frame denial,
  nosniff, and referrer policy. API headers do not protect the separate web
  document. TLS/HSTS and production cookie behavior still require deployment UAT.
- The test script uses the installed Node TypeScript support (verified on Node
  24.13.0) for auth success/failure, safe navigation, and environment regressions.

## Collection Run visibility - 2026-10-02

The Product Owner supersedes D-089's deferred Run creation. Banks Collect
registers every eligible bank/type Run before committing and starting background
work, returns `workflow_state=queued` and its actual `run_ids`. Runs display
Queued, Discovering sources, Collecting, Skipped, Completed or Failed in EN/KO/JA.
Known preflight exclusions get terminal skipped Runs; active reservations never
create duplicates. Discovery/access failures finish the registered Run without
creating candidates or weakening collection gates. Existing older plans remain
compatible with deferred preparation.

Runs offers safe 15-second Auto refresh and Search. Polling pauses for hidden
pages, dialogs, focused inputs, unsaved filters and pending mutations. Advanced
filters start collapsed and indicate applied filters. Banks uses Search, shows
eligible published-product counts beside generated sources and omits per-type
preparation/View run clutter. Bank/type identity, Run IDs and exclusion reasons
remain visible; filters support the added preparation states. Database lifecycle
values remain `started/completed/failed/retried`, refined by private collection
phase metadata. The existing `started`/`completed` filters include their child
preparation states for compatibility.

Retry returns the queued replacement ID immediately. The original failed/partial
outcome is preserved until the replacement actually begins collecting. Coverage
changes and transient preparation failures remain visible as failed attempts;
structural exclusions remain skipped. Inactive coverage requires restoration;
precision rediscovery and all financial/security boundaries remain unchanged.
Deploy API/collection runner and Admin together; no live collection or deployment
was performed in this implementation slice.

## Conditional transaction, withdrawal and security requirements - 2026-10-01

The shared market profile v7 restores checking transaction costs, GIC/CD early-access rules and consequences, and line-of-credit security. Unlimited checking needs no excess fee; explicitly blocked early withdrawal needs no penalty value; explicit unsecured status is valid. Collection prompts expose grouped alternatives and conditions. Automatic acceptance/exclusion remains the only product workflow; no new Admin action or review queue is added.

The Public API rechecks affected snapshot-pinned versions under the current contract, including older receipts, and exposes numeric `transaction_fee`/`additional_transaction_fee`. Country counts use the same eligible products. Shared Public metrics show checking transaction costs and both GIC access and consequences in all supported locales. Deploy API/worker before Public; previous cached responses can remain until normal expiry. Read-only current-data assessment: 5 eligible of 24 active products, 19 needing evidence. No live mutations, paid collection or deployment were performed in this implementation slice.
