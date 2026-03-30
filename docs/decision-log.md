# FPDS Decision Log

Version: 1.0  
Date: 2026-03-29  
Status: Active  
Source Documents:
- `docs/FPDS_Requirements_Definition_v1_5.md`
- `docs/plan.md`
- `docs/WBS.md`

---

## 1. Purpose

이 문서는 FPDS 프로젝트의 주요 의사결정을 한 곳에 기록하기 위한 기준 문서입니다.

목적:
- 이미 합의된 결정을 다시 논쟁하지 않도록 한다.
- 설계와 구현이 서로 다른 가정을 사용하지 않도록 한다.
- open item과 확정 item을 명확히 구분한다.
- 이후 ADR, schema spec, API spec, security note의 기준 문서로 사용한다.

---

## 2. How To Use

새 의사결정이 생기면 아래 원칙으로 기록합니다.

1. 결정이 확정되면 즉시 이 문서에 추가한다.
2. 아직 닫히지 않은 항목은 `Open`으로 남기고, 확정되면 `Decided`로 바꾼다.
3. 하나의 결정은 한 문장으로 짧게 쓰고, 이유는 별도 컬럼에 남긴다.
4. 관련 영향 범위가 있으면 반드시 `Affected Areas`에 적는다.
5. 문서나 회의에서 번복되면 기존 결정을 삭제하지 말고 superseded 상태로 남긴다.

Status meaning:
- `Decided`: 확정됨
- `Open`: 아직 결정 필요
- `Superseded`: 이전 결정, 더 최신 결정으로 대체됨

---

## 3. Decision Register

| ID | Date | Status | Area | Decision | Rationale | Affected Areas | Source |
|---|---|---|---|---|---|---|---|
| D-001 | 2026-03-28 | Decided | Product Boundary | 현재 프로젝트의 대상은 MyBank 추천 서비스가 아니라 FPDS 데이터 플랫폼이다. | 범위 확장을 막고 플랫폼 구축에 집중하기 위해 | scope, architecture, roadmap | PRD 2.3, 23 |
| D-002 | 2026-03-28 | Decided | Delivery Stages | 본 프로젝트는 Prototype, Phase 1, Phase 2의 3단계 범위로 관리한다. | 단계별 성공 기준과 게이트를 분리하기 위해 | planning, milestones, acceptance | PRD 1, 7 / Plan 8 |
| D-003 | 2026-03-28 | Decided | Prototype Scope | Prototype은 TD Bank의 Savings Accounts 단일 범위로 end-to-end feasibility를 검증한다. | 가장 작은 범위로 기술 가능성을 먼저 검증하기 위해 | prototype, backlog, acceptance | PRD 4.1, 7.1, 18.1 / Plan 3.1, 8 |
| D-004 | 2026-03-28 | Decided | Phase 1 Scope | Phase 1 범위는 Canada Big 5의 Chequing, Savings, GIC/Term Deposits와 Public Dashboard, Admin Console이다. | 초기 공개 가치와 운영 가능성을 동시에 확보하기 위해 | roadmap, parser coverage, UI scope | PRD 4.1, 7.2, 18.2 |
| D-005 | 2026-03-28 | Decided | Phase 2 Scope | Phase 2 범위는 Japan Big 5 deposit expansion과 External SaaS/Open API이다. | 국제 확장과 외부 제공 기능은 Phase 1 이후로 분리하기 위해 | roadmap, API, localization | PRD 4.1, 7.3, 18.3 |
| D-006 | 2026-03-28 | Decided | Non-Goals | personalized recommendation, public evidence exposure, billing/subscription은 현재 범위에서 제외한다. | scope creep를 막고 핵심 데이터 인프라에 집중하기 위해 | product, UI, business model | PRD 3.2, 4.2, 19.2 |
| D-007 | 2026-03-28 | Decided | Product Principles | Evidence First, Human Review by Design, Canonical Before Consumer Features를 핵심 원칙으로 채택한다. | 데이터 신뢰성과 운영성을 제품의 중심에 두기 위해 | data model, workflow, review | PRD 6 / Plan 4 |
| D-008 | 2026-03-28 | Decided | Public Experience | Phase 1 공개 화면은 Product Catalog Grid와 Insight Dashboard를 모두 포함한다. | 단순 목록이 아니라 비교 가능한 공개 경험을 제공하기 위해 | public UI, dashboard APIs | PRD 8.1, 11.1, 11.2 |
| D-009 | 2026-03-28 | Decided | Public Access | Public dashboard는 익명 사용자에게 로그인 없이 제공한다. | 공개 배포 목적과 시장 가시성 확보를 위해 | auth boundary, public routes | PRD FR-PUB-001 |
| D-010 | 2026-03-28 | Decided | Admin Access | Admin 기능은 별도 인증이 필요한 내부 운영 영역으로 유지한다. | review, trace, publish, usage 데이터 보호를 위해 | auth, RBAC, admin routes | PRD 5.1, FR-ADM-001 |
| D-011 | 2026-03-28 | Decided | Localization | Public/Admin UI는 EN/KO/JA 3개 언어를 지원한다. | 공개 서비스와 운영 도구를 다국어 기반으로 준비하기 위해 | i18n, content ops, QA | PRD 1, 6, 8.1, 8.2 |
| D-012 | 2026-03-28 | Decided | Localization Policy | product name, description, conditions 같은 source-derived product data는 locale별 번역 필드로 복제하지 않고 source language 값으로 유지한다. | 원문 보존과 데이터 왜곡 방지를 위해 | schema, UI copy, localization | PRD FR-PUB-017, 14.6, Appendix A |
| D-013 | 2026-03-28 | Decided | Source of Truth | evidence, parsed text, run/review/usage/audit 데이터는 FPDS가 소유하고, approved normalized product master는 BX-PF를 target master store로 본다. | 운영 데이터와 마스터 데이터의 역할을 분리하기 위해 | data architecture, publish flow | PRD 6, 16.1 |
| D-014 | 2026-03-28 | Decided | BX-PF Integration | BX-PF connector는 Phase 1 필수 범위이며, write-back은 환경/조건 충족 시 acceptance에 포함한다. | 나중에 붙이는 연동이 아니라 초기 설계 대상이기 때문 | interface design, acceptance, release | PRD 6, 18.2, Appendix A |
| D-015 | 2026-03-28 | Decided | Security Baseline | 보안은 추후 hardening 항목이 아니라 설계 초기부터 auth, RBAC, CORS, CSRF, CSP, SSRF, secrets 정책을 포함해 설계한다. | public/admin/API/crawler가 모두 존재하는 구조이기 때문 | architecture, infra, API, QA | PRD 6, 8.8, 14.3 / Plan 4, 5, 8 |
| D-016 | 2026-03-28 | Decided | Delivery Order | Prototype First 원칙을 적용하고, Prototype 성공 전 Big 5 전체 확장으로 가지 않는다. | 가장 작은 성공 단위로 리스크를 줄이기 위해 | sequencing, milestone planning | Plan 4, 17, 18 / PRD 21 |
| D-017 | 2026-03-29 | Decided | Current Priority | 현재 우선순위는 open item closure, detailed design completion, prototype backlog finalization이다. | plan과 WBS 모두 코딩보다 설계 마감을 먼저 요구하기 때문 | current execution, WBS | Plan 18 / WBS 1, 6, 8 |
| D-018 | 2026-03-29 | Decided | Build Hold Rule | Product Owner가 명시적으로 개발 시작을 승인하기 전까지 구현 작업은 시작하지 않는다. | 설계 완료 전 조기 구현으로 인한 재작업을 방지하기 위해 | all implementation streams | WBS 2, 9 |

---

## 4. Open Decisions

아래 항목은 이미 상위 문서에서 `open item`으로 식별되었고, 아직 확정되지 않았습니다.

| ID | Date | Status | Area | Decision Needed | Why It Matters | Source |
|---|---|---|---|---|---|---|
| O-001 | 2026-03-29 | Open | BX-PF | exact BX-PF write contract and field mapping | publish workflow와 acceptance 기준을 결정 | PRD 22 / WBS 1.5.4 |
| O-002 | 2026-03-29 | Open | Taxonomy | country-specific deposit subtype taxonomy | parser/schema/dashboard 기준을 통일 | PRD 22 / WBS 1.2.1 |
| O-003 | 2026-03-29 | Open | Validation | confidence threshold and field-level validation rules | review routing 품질에 직접 영향 | PRD 22 / WBS 1.2.4, 1.2.5 |
| O-004 | 2026-03-29 | Open | Auth | admin auth는 session cookie 기반인지 token 기반인지 | 보안 구조와 구현 방식에 영향 | PRD 22 / WBS 1.6.1 |
| O-005 | 2026-03-29 | Open | RBAC | role matrix와 승인 권한 범위 | 운영 리스크와 감사 범위 결정 | PRD 22 / WBS 1.6.2 |
| O-006 | 2026-03-29 | Open | Security | CORS allowlist, crawler SSRF/egress 정책 | public/admin/api/crawler 경계 보호 | PRD 22 / WBS 1.6.4, 1.6.5 |
| O-007 | 2026-03-29 | Open | Dashboard | KPI formula, ranking 기준, scatter axis | dashboard 의미와 비교 품질 결정 | PRD 22 / WBS 1.7.2, 1.7.3 |
| O-008 | 2026-03-29 | Open | Retrieval | vector indexing implementation detail | evidence retrieval 구조 시작점 결정 | PRD 22 / WBS 1.4.4 |
| O-009 | 2026-03-29 | Open | Localization | UI localization ownership and Japanese fallback/glossary ownership | 다국어 운영 일관성에 영향 | PRD 22 / WBS 1.7.5, 1.7.7 |
| O-010 | 2026-03-29 | Open | External API | API auth, tenant isolation, rate limit/SLA | Phase 2 API 기반 정책 결정 | PRD 22 / WBS 1.6.3, 1.5.5 |

## 4.1 Additional Decided Items

| ID | Date | Status | Area | Decision | Rationale | Affected Areas | Source |
|---|---|---|---|---|---|---|---|
| D-019 | 2026-03-29 | Decided | Governance Model | FPDS는 working agreement 기준으로 Product Owner 승인 중심, 문서 우선, gate 기반 방식으로 운영한다. | 협업 방식과 문서 우선순위를 고정해 후속 문서와 실행의 기준을 만들기 위해 | governance, reporting, approvals | `docs/working-agreement.md` |
| D-020 | 2026-03-29 | Decided | Staffing Model | Phase 1 완료 시점까지는 Product Owner + Codex 2인 체제로 계획하고, Phase 2 시작 시 추가 인력 1명을 투입해 3인 체제로 운영한다. | 일정 추정과 단계별 병렬 처리 한계를 현실적으로 반영하기 위해 | roadmap, staffing, schedule planning, phase sequencing | `docs/roadmap.md` |
| D-021 | 2026-03-29 | Decided | Scope Governance | FPDS의 범위 변경은 change request와 Product Owner 승인 없이는 공식 범위에 반영하지 않는다. | scope creep를 통제하고 문서 기준 실행을 유지하기 위해 | scope control, WBS, roadmap, approvals | `docs/scope-change-control.md` |
| D-022 | 2026-03-29 | Decided | Stage Gate Governance | FPDS는 Gate A~D 체크리스트 기준으로 단계 전환을 판단하고, gate 통과 전 다음 단계 구현에 착수하지 않는다. | 설계 미완료 상태의 조기 구현과 단계 전환 착시를 방지하기 위해 | stage transition, approvals, roadmap, WBS | `docs/stage-gate-checklist.md` |
| D-023 | 2026-03-29 | Decided | Milestone Tracking Model | FPDS의 milestone due date는 공식 실행 시작 전까지 relative week 기준으로 관리하고, 공식 시작일 확정 후 absolute date를 추가한다. | 아직 build start date가 확정되지 않은 상태에서도 일정 추적을 가능하게 하기 위해 | milestone tracking, roadmap, WBS, governance | `docs/milestone-tracker.md` |
| D-024 | 2026-03-30 | Decided | Scope Baseline | WBS 1.1.1~1.1.5의 공식 기준 문서는 `docs/scope-baseline.md`로 고정한다. | Prototype/Phase 1 범위, 비범위, cutline, 개발 시작 승인 방식을 한 장으로 고정하기 위해 | scope baseline, release cutline, approvals | `docs/scope-baseline.md` |
| D-025 | 2026-03-30 | Decided | Non-Goals Baseline | 공식 비범위 목록은 WBS의 예시 3개가 아니라 PRD 전체 `Non-Goals` 목록으로 운영한다. | 구현 직전 scope creep를 막고 exclusion list를 완전한 형태로 고정하기 위해 | scope control, roadmap, WBS, change control | `docs/scope-baseline.md`, PRD 3.2, 4.2 |
| D-026 | 2026-03-30 | Decided | Release Cutline | release cutline은 `Phase 1 release 기준 Must Have / Later`로 관리하며, Phase 2는 계약 범위이지만 Phase 1 release cutline에서는 `Later`로 분리한다. | 계약 범위와 단기 release cutline을 분리해 build sequencing을 명확히 하기 위해 | release planning, WBS, roadmap, change control | `docs/scope-baseline.md` |
| D-027 | 2026-03-30 | Decided | Build Start Approval | 개발 시작 조건은 `Gate A blocker closed + Product Owner explicit approval`로 정의한다. | 설계 차단 항목이 닫히지 않은 상태에서의 조기 구현을 막기 위해 | gate governance, implementation start, approvals | `docs/scope-baseline.md`, `docs/stage-gate-checklist.md` |

---

## 5. Change History

| Date | Change |
|---|---|
| 2026-03-29 | Initial decision log created from PRD, plan, and WBS baseline |
| 2026-03-29 | Added governance model decision linked to working agreement |
| 2026-03-29 | Added staffing model decision linked to roadmap planning |
| 2026-03-29 | Added scope governance and stage gate governance decisions |
| 2026-03-29 | Added milestone tracking model decision |
| 2026-03-30 | Added scope baseline, non-goals baseline, Phase 1 release cutline, and build-start approval decisions |
