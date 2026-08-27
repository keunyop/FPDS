# FPDS RAID Log

Version: 2.0
Date: 2026-04-22
Status: Active current baseline
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/WBS.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/working-agreement.md`

---

## 1. Purpose

This file keeps only the active risks, assumptions, issues, and dependencies that still matter for current execution.

Rules:
- keep it short and current
- remove closed items once they stop shaping execution
- avoid turning this file into a full history dump
- use the development journal for slice-level detail

---

## 2. Current Risks

| ID | Priority | State | Risk | Current Response | Owner |
|---|---|---|---|---|---|
| R-001 | High | Open | Bank source structure and customer decision semantics vary by country, bank, and product type. Legal-bank homepages may delegate retail products to a separate consumer brand, while one official parent domain may also host explicit routes for several countries, so discovery, extraction, and normalization quality can drift or cross-contaminate during expansion. | Resolve one versioned country-product profile at every collection/publication gate; hard-veto explicit other-market paths/locales, subdomains, and country-code TLDs even on shared domains; require bounded first-collection precision discovery, keep every homepage/hub/registry-detail/candidate expansion capped and observable, and let subsequent standard collection reuse only an active detail scope; keep evidence-first review fallback, evidence-bound consumer-brand routes, one-shot stale-coverage repair, authoritative discovery identity, omission of ungrounded attributes, and schema-aligned validation active. Require an explicit profile/fixture slice before widening a new market. | Tech Lead, AI/Data |
| R-002 | High | Open | PDF-heavy sources can still produce unstable parse quality and weak field extraction. | Preserve raw artifacts, keep supporting-merge and manual review options available, and verify PDF-heavy banks explicitly. | AI/Data |
| R-003 | High | Open | BX-PF environment or contract readiness can still delay true publish readiness. | Keep interface-first behavior, mock-safe dev posture, and explicit pending or retry semantics until live readiness is confirmed. | Product Owner, Backend |
| R-004 | Medium | Open | Public aggregate refresh, snapshot freshness, and canonical truth can drift if queue or retry behavior regresses or scheduled collection is intentionally paused. | Keep dashboard health visibility, retry flow, and latest-successful serving fallback in place. During the initial Vercel Public-read period, display only the existing completed snapshot and perform an explicit manual refresh before freshness becomes release-relevant. | Backend |
| R-005 | Medium | Open | LLM, browser automation, source collection, and queue-remediation costs may grow faster than expected during cross-bank hardening. | Keep official grounding to one call per detail candidate plus one bounded residual-review attempt, cap autopilot candidates per run, reuse completed assessments, and inspect bounded model/run metadata plus operational health before widening the cap. | Product Owner, Backend |
| R-006 | High | Open | Delivery capacity remains tight relative to ongoing data, UI, QA, and docs work. | Keep slices small, protect scope boundaries, and avoid reopening settled baselines without clear value. | Product Owner, Tech Lead |
| R-007 | High | Monitoring | The live SwitchaBank Public site reaches Vercel API Preview/Production environments that temporarily share the development database, coupling anonymous read traffic, authenticated API operations, development work, capacity, and incident impact. | Treat this as a Product Owner-approved temporary exception only: keep Vercel scheduling disabled, use separate Preview/Production auth secrets, route browser reads through the Public BFF, avoid Vercel Admin operations, monitor public-read behavior, and move Production to a separately provisioned database before the coupling becomes release-critical. | Product Owner, Backend |

---

## 3. Current Assumptions

| ID | Priority | State | Assumption | What Still Needs Validation | Owner |
|---|---|---|---|---|---|
| A-001 | High | Monitoring | Canada Big 5 deposit products remain a realistic Phase 1 coverage target with the current registry-driven approach. | Continued bank-by-bank collection and parser hardening. | Product Owner, AI/Data |
| A-002 | Medium | Monitoring | EN/KO/JA public and admin UI remains supportable within current team capacity. | Ongoing translation, QA, and copy ownership pressure as public scope grows. | Product Owner |
| A-003 | Medium | Monitoring | Shared filter vocabulary between Product Grid and Insight Dashboard remains usable as scope grows. | Continued UX validation as more product types and edge cases accumulate. | Frontend, Product Owner |
| A-004 | High | Open | BX-PF will remain the intended target store for approved normalized products in Phase 1. | Contract, environment, and real write readiness. | Product Owner, Tech Lead |
| A-005 | Medium | Monitoring | The initial Vercel API may serve the latest completed Public snapshot without automatic collection for a bounded period. | Product Owner confirmation of acceptable snapshot age before Public launch and an explicit manual-refresh plan when freshness becomes necessary. | Product Owner, Backend |

---

## 4. Current Issues

| ID | Priority | State | Issue | Current Impact | Next Action | Owner |
|---|---|---|---|---|---|---|
| I-001 | High | Monitoring | Some banks split comparison facts across a product detail page and separate official pricing/disclosure pages; live search may identify the broader fact without producing a field-level quote from the freshly captured detail snapshot. | Generic exact-product supporting merge now carries grounded lending rate summaries and companions plus US CD early-withdrawal penalties, while incomplete approval/Public exposure remains blocked. Banks whose dynamic pages still cannot yield a persisted quote remain in Review. | Add reproducible official source-role patterns to the country profile and supporting bundle one bank pattern at a time; never promote a broader live-search fact without a persisted exact quote. | AI/Data, Backend |
| I-002 | Medium | Monitoring | Historical migrations still seed broad baseline catalog rows on a fresh database, but migration 0043 now immediately applies an evidence-qualified fail-closed gate. | Fresh and existing databases retain history while catalog scopes without a verified route, active detail source, or successful non-empty collection are inactive and cannot be scheduled; false negatives remain possible until an operator re-verifies coverage. | Monitor quarantined scopes and reactivate only after an auditable official coverage route is verified; do not infer product retirement from quarantine. | AI/Data, Backend |
| I-003 | Medium | Open | Several active governance docs outside this slice still contain old encoding or readability problems. | Some startup docs are harder to inspect from the shell than they should be. | Clean remaining active docs in later docs-hygiene slices. | Tech Lead |

---

## 5. Current Dependencies

| ID | Priority | State | Dependency | Impacted Work | Current Handling | Owner |
|---|---|---|---|---|---|---|
| D-001 | High | Monitoring | BX-PF access, contract confidence, and production environment readiness | publish readiness, Gate D, release operations | Keep Phase 1 work interface-first until live readiness is explicit. | Product Owner, Backend |
| D-002 | High | Monitoring | Stable access to bank websites and PDFs | collection quality, parsing, evidence capture | Keep bounded fetching, registry governance, and source-specific hardening active. Browser-enabled domains use format-aware DOM discovery and PDF/DOM snapshot fallback only on the validated official URL and exact bank allowlist; non-product corporate reports remain excluded. Preserve structured CMS identity/condition relationships where flattening loses meaning, and hard-block explicitly dated rate evidence older than the governed five-year safety ceiling. | AI/Data |
| D-003 | Medium | Open | Domain review bandwidth for taxonomy and field interpretation edge cases | normalization quality, validation rules, public semantics | Escalate only when bank-specific ambiguity blocks canonical decisions. | Product Owner |
| D-004 | Medium | Open | Phase 2 external API policy and tenant model remain undecided | later API work only | Leave this closed out of current Phase 1 implementation unless scope changes. | Product Owner, Backend |

---

## 6. Review Rule

Review this file when:
- a risk becomes release-relevant
- a long-lived issue starts blocking active WBS work
- a dependency changes stage readiness
- a supposedly closed item becomes active again

If an item is no longer shaping decisions, remove it.

---

## 7. Change History

| Date | Change |
|---|---|
| 2026-08-08 | Updated I-001 for cross-page lending disclosure capture after Chase/Citi comparison-quality RCA; approval and Public projection now fail closed on incomplete comparison contracts |
| 2026-08-09 | Added country-product profile mitigation to R-001 and moved I-001 to Monitoring after exact-product lending/CD supporting merge was implemented |
| 2026-08-15 | Updated D-002 for format-aware browser recovery after Vancity `429` RCA and aligned R-005 with bounded post-`0040` observability |
| 2026-08-15 | Updated D-002 for Vancity structured-CMS evidence preservation and materially stale dated-rate blocking |
| 2026-08-22 | Updated R-004 and added A-005 for the explicitly scheduler-disabled Vercel Public-read period |
| 2026-08-22 | Added R-007 for the Product Owner-approved temporary dev database reuse by Vercel Preview and Production |
| 2026-08-22 | Updated R-007 after the live Bankompare Public deployment began routing anonymous reads through the API-backed BFF |
| 2026-08-24 | Added then removed D-005 after the Product Owner supplied the GA4 ID and Production deployment/live request verification completed |
| 2026-04-22 | Rewrote the RAID log as a short current-baseline document and removed stale closed design-stage items from the default path |
