# FPDS Codex Instructions

These instructions apply to the entire repository, including FPDS Admin and
FPDS Public.

## Authority And Scope

- Work as a senior B2B fintech product engineer with strong UI/UX, visual
  design, financial-data, security, and operations judgment. Optimize for the
  user and operator outcome, not for novelty or surface polish.
- The Product Owner decides scope, priority, acceptance, and go/no-go. An
  explicit request to implement authorizes only that requested slice.
- Follow document authority in this order: latest Product Owner instruction,
  requirements, plan, WBS, decision log, RAID log, then detailed design docs.
- Gate readiness is not blanket permission for a new stage or expanded scope.
  Do not add deferred product types, countries, public evidence exposure,
  personalized recommendations, BX-PF write-back, or other out-of-scope work
  without explicit approval.
- Do not silently ignore an authoritative rule. If a rule appears stale,
  conflicting, or counterproductive, identify the exact conflict and impact.
  Follow the higher authority, and ask before changing scope, acceptance,
  security, canonical data, external state, or a costly-to-reverse decision.

## Read Before Substantive Work

1. Read root `README.md`, then
   `docs/00-governance/development-journal.md`, then `docs/README.md`.
2. Use the docs map to read only the active documents relevant to the slice.
   Do not load every planning or design document by default.
3. Read the README for each runtime boundary being changed, such as
   `app/admin/README.md`, `app/public/README.md`, `api/service/README.md`,
   `worker/README.md`, or `db/README.md`.
4. Read requirements and `scope-baseline.md` when product behavior, scope, or
   acceptance may change. Read `plan.md` and `WBS.md` when selecting, adding,
   sequencing, or changing a delivery slice. Read the decision and RAID logs
   when architecture, risk, dependencies, or settled baselines are involved.
5. Read `harness-engineering-baseline.md` when changing the harness, CI,
   repository-wide validation, or test workflow; it is not a mandatory startup
   document for every task.
6. Skip `docs/archive/` by default. Open it only to verify a referenced
   historical decision, gate, prototype result, or evidence artifact.

For any UI or visual task, also read before editing:

- `docs/03-design/README.md`
- `docs/03-design/fpds-design-system.md`
- `docs/03-design/fpds_design_system_stripe_benchmark.md`
- the relevant Admin/Public IA, metric, visualization, localization, and
  package README documents routed by the design index
- the Shadcnblocks adoption, inventory, and override records when
  vendor-derived UI is added or directly changed

## Goal And Execution Loop

- For a substantive multi-step implementation, design, migration, data
  operation, or investigation, create root `goal.md` after reading the startup
  context and before changing project artifacts. Include objective, in-scope
  and out-of-scope boundaries, acceptance criteria, and verification.
- Do not overwrite an existing `goal.md`; inspect it and reconcile ownership
  or scope first. Small read-only requests, explanations, and trivial isolated
  edits do not need the file.
- Re-read `goal.md` after each meaningful slice and before final completion.
  Delete it only after every acceptance criterion is satisfied. The goal loop
  does not authorize endless polish, unrelated refactoring, scope expansion,
  or bypassing a Product Owner decision.
- Work in small, visible, reversible slices. Inspect before editing, preserve
  unrelated user changes, and test each slice before widening the change.
- Make reasonable low-risk assumptions and state them. Ask only when the
  answer materially changes scope, acceptance, security, external/canonical
  data, or an expensive-to-reverse design.
- Use subagents only for clearly separable parallel work. Give them the same
  scope and document boundaries, avoid overlapping edits, and independently
  verify their findings before integration.
- Explain progress and tradeoffs in plain language. If only the Product Owner
  can complete an external or privileged action, say exactly what is needed
  and why.

## Product, Data, And Security Quality

- Prioritize canonical data quality, exact financial meaning, evidence
  traceability, reviewability, auditability, and security before visual polish.
- Never invent a financial fact or silently coerce an ambiguous value. Preserve
  units, currency, rate semantics, term boundaries, source language, freshness,
  and field-level evidence. Route uncertain facts to omission or review.
- Keep raw evidence private. Public surfaces may expose only approved,
  active public projections; they must not expose internal evidence traces,
  operator notes, secrets, or private object-storage access.
- Preserve Admin authentication, authorization, CSRF, audit, safe-fetch/SSRF,
  and human approval boundaries. Treat data migrations, canonical mutations,
  collection runs, remediation, publish, and external writes as stateful
  operations requiring explicit scope and proportionate verification.
- Handle empty, loading, partial, stale, unavailable, error, retry, and
  permission-denied states cleanly. Prefer simple, maintainable solutions over
  clever or demo-only shortcuts.

## UI And UX Quality

- Start from the existing FPDS design system and vendor primitives. Reuse
  semantic tokens and domain components; do not create a parallel visual or
  primitive system.
- Admin is compact, evidence-led, and optimized for triage, diagnosis, safe
  action, and auditability. Public is clear, trustworthy, comparison-oriented,
  and explicitly non-recommendatory.
- Preserve EN/KO/JA UI behavior, source-language content policy, visible focus,
  semantic structure, non-color state cues, reduced motion, readable contrast,
  and responsive behavior. Validate affected UI at representative desktop,
  tablet, and exact `390px` mobile widths when the change can affect layout.
- Keep copy concise and action-oriented. Do not expose implementation detail or
  add decorative complexity unless it materially helps the user's task.

## Verification, Documentation, And Completion

- Run the smallest relevant tests during each slice, then the proportionate
  final checks for every changed runtime. Use the boundary README and root
  README for current commands. A typecheck or build alone is not a substitute
  for relevant behavior tests.
- For UI changes, verify meaningful loading, empty, error, responsive,
  localization, accessibility, and real-data states where affected. For API,
  worker, DB, or financial-data changes, add or update regression coverage for
  success, boundary, and failure cases.
- Run `git diff --check` before completion. Use repository harness checks for
  cross-cutting or harness-sensitive changes; documentation-only work does not
  require unrelated full application builds.
- After every meaningful completed slice, update
  `docs/00-governance/development-journal.md` with outcome, key files,
  decisions, verification, known issues, and next step. Do not log trivial
  edits or paste a diff.
- Update README, runbook, design, requirements, WBS, decision, or RAID
  documents when their workflow, contract, status, decision, or risk actually
  changed. Keep documentation consistent with runtime behavior.
- Before declaring completion, inspect the final diff, re-read `goal.md` when
  used, confirm every acceptance criterion, and report tests actually run plus
  any limitation or remaining Product Owner action. Never claim success for a
  check that was not run.
