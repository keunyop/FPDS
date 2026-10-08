# FPDS Codex Instructions

## Mandatory product collection rule — 2026-09-30

- Accuracy takes priority over coverage. Collect fewer verified facts; omit
  uncertain optional attributes and automatically exclude candidates missing
  proven identity, currency or comparison essentials.
- Required fields are the publication minimum, not a collection ceiling. Collect
  profile/registered typed optional facts when the same official evidence proves
  them. Omit uncertain optional facts; do not add searches, retries or human review
  solely for optional completeness. Preserve them through normalization.
- Public lists, comparisons and Home Top 5 use current required decision facts.
  Detail shows verified optional facts and omits unknown rows. Missing optional
  information must not become zero/false or a ranking penalty; preserve actual
  financial conditions and comparable-rate/term boundaries.
- Product collection must not depend on human review, edit-approval or a residual
  review queue. An AI confidence score cannot replace source evidence or bypass
  automatic validation. Preserve separate account/security approval controls.
- Use the shared field contract and exact financial units/types across products.
  Never infer missing values, false/zero or rate/term semantics. The explicitly
  approved undisclosed-currency defaults are CA/CAD and US/USD; preserve explicit
  currencies and reject conflicts. Checking transaction costs, GIC/CD withdrawal
  access/consequences and line-of-credit security are conditional essentials
  under the current collection policy. Do not make them optional to increase coverage.
- Read `docs/03-design/collection-accuracy-policy.md` for collection work. Add
  regression evidence before extending accepted patterns; update all gates and
  prompts together. The approved 355-product/470-review legacy data cutover was
  applied on 2026-09-30; preserve its history and do not restore manual review.
  The Product Owner reports the prior changes deployed. For recovery, diagnose
  preserved evidence before paid collection; preflight essential evidence, reuse
  identical current inputs, and bound batches/retries. Never restore historical
  facts merely to fill Public. Keep runtime deployment separate from data results.
  Legacy recovery is a bounded one-off data operation. Do not add a permanent
  recovery feature, menu or scheduler without a separate Product Owner request.

These instructions apply to the entire repository, including FPDS Admin and
FPDS Public.

## Post-MVP Scope And Authority

- The MVP is complete. Work on the recipient's requested localization, fixes
  and features. The latest Product Owner instruction defines scope, acceptance
  and authorization; current financial/security contracts apply within it.
- Do not add unrelated countries, product types, Public evidence exposure,
  personalized recommendations or external integrations without an actual request.
- Historical plans, WBS and MVP stage gates are not development prerequisites.
  If a current contract conflicts with the request, explain the concrete impact
  and resolve it before changing scope, security or canonical data.
- Existing authorization persists. Do not request approval again for authorized
  work. Collection runs, paid research, migrations, publication, deployments and
  external writes must remain within the explicitly authorized environment and scope.

## Read Only What The Task Needs

1. Read the [development guide](descent/FPDS_Admin_개발_가이드.md).
2. Read the README of each affected boundary: Admin, API, Worker, DB or Public.
3. Use [technical references](docs/README.md) for relevant contracts. Consult
   the journal, decision log and RAID log only when investigating related history,
   risks or previous decisions; do not read the entire history before each task.
4. For UI work, read the design index, FPDS design system, Stripe benchmark and
   relevant IA/localization documents. Read Shadcnblocks adoption, inventory and
   overrides when changing vendor-derived UI.
5. For harness/CI/test-workflow changes, read the harness engineering baseline.
   Use a task-specific skill from the development guide when useful.

## Work And Completion

- For substantive multi-step work, maintain root goal.md with scope, acceptance
  and verification. Inspect existing goals and preserve unrelated ownership and
  unfinished work; do not overwrite them. Re-read the goal after meaningful
  slices and before completion. Delete only when all of its work is complete.
- Inspect before editing, preserve unrelated changes and work in small,
  reversible slices. State low-risk assumptions. Ask only when missing input
  materially changes scope, security, external state or a costly decision.
- Keep data units, currency, rate semantics, term boundaries, original language,
  freshness and field-level evidence intact. Preserve migrations and regression
  fixtures. Never restore historical facts merely to fill Public.
- Keep Admin auth, roles, CSRF, country isolation, audit, safe-fetch/SSRF and
  private evidence boundaries. Public receives only approved active projections.
- Reuse semantic tokens and existing components. Preserve supported locales,
  keyboard access, visible focus, contrast, non-color state cues and reduced
  motion. Verify affected layouts at desktop, tablet and exact 390px width.
- Test affected behavior: success, boundary and failure for API/DB/financial
  work; loading, empty, error, permission, localization and responsive states
  for UI. A typecheck/build alone is insufficient for behavior changes.
- Use package README commands. Documentation-only work needs reference,
  encoding and diff checks, not unrelated application builds. Use repository
  harness checks for cross-cutting/harness changes. Run git diff --check.
- After a meaningful completed slice, add a short journal entry with outcome,
  key files, actual verification, limits and next action. Update only documents
  whose contract/workflow changed.
- Inspect the final diff and acceptance criteria. Report actual tests and limits;
  distinguish local code, serving deployment and published data.
