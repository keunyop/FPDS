# FPDS Decision Log

Version: 1.0
Date: 2026-03-29
Status: Active
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
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
| O-001 | 2026-03-29 | Superseded | BX-PF | Closed by D-048 | publish workflow와 acceptance 기준을 결정 | `docs/03-design/api-interface-contracts.md` / WBS 1.5.4 |
| O-002 | 2026-03-29 | Superseded | Taxonomy | Closed by D-028 and D-029 | parser/schema/dashboard 기준을 통일 | `docs/03-design/domain-model-canonical-schema.md` / WBS 1.2.1, 1.2.2 |
| O-003 | 2026-03-29 | Superseded | Validation | Closed by D-030 | review routing 품질에 직접 영향 | `docs/03-design/domain-model-canonical-schema.md` / WBS 1.2.4, 1.2.5 |
| O-004 | 2026-03-29 | Superseded | Auth | Closed by D-050 | 보안 구조와 구현 방식에 영향 | PRD 22 / WBS 1.6.1 |
| O-005 | 2026-03-29 | Superseded | RBAC | Closed by D-051 | 운영 리스크와 감사 범위 결정 | PRD 22 / WBS 1.6.2 |
| O-006 | 2026-03-29 | Superseded | Security | Closed by D-053 and D-054 | public/admin/api/crawler 경계 보호 | PRD 22 / WBS 1.6.4, 1.6.5 |
| O-007 | 2026-03-29 | Superseded | Dashboard | Closed by D-058 and D-059 | dashboard 의미와 비교 품질 결정 | `docs/03-design/insight-dashboard-metric-definition.md`, `docs/03-design/product-type-visualization-principles.md` / WBS 1.7.3 |
| O-008 | 2026-03-29 | Superseded | Retrieval | Closed by D-042 | evidence retrieval 구조 시작점 결정 | `docs/03-design/retrieval-vector-starting-point.md` / WBS 1.4.4 |
| O-009 | 2026-03-29 | Superseded | Localization | Closed by D-061, D-062, and D-063 | 다국어 운영 일관성에 영향 | PRD 22 / WBS 1.7.5, 1.7.7 |
| O-010 | 2026-03-29 | Open | External API | exact auth mechanism, tenant isolation enforcement, rate limit/SLA | Phase 2 API 기반 정책 결정 | PRD 22 / WBS 1.6.3, 7.6 |

## 4.1 Additional Decided Items

| ID | Date | Status | Area | Decision | Rationale | Affected Areas | Source |
|---|---|---|---|---|---|---|---|
| D-019 | 2026-03-29 | Decided | Governance Model | FPDS는 working agreement 기준으로 Product Owner 승인 중심, 문서 우선, gate 기반 방식으로 운영한다. | 협업 방식과 문서 우선순위를 고정해 후속 문서와 실행의 기준을 만들기 위해 | governance, reporting, approvals | `docs/00-governance/working-agreement.md` |
| D-020 | 2026-03-29 | Decided | Staffing Model | Phase 1 완료 시점까지는 Product Owner + Codex 2인 체제로 계획하고, Phase 2 시작 시 추가 인력 1명을 투입해 3인 체제로 운영한다. | 일정 추정과 단계별 병렬 처리 한계를 현실적으로 반영하기 위해 | roadmap, staffing, schedule planning, phase sequencing | `docs/00-governance/roadmap.md` |
| D-021 | 2026-03-29 | Decided | Scope Governance | FPDS의 범위 변경은 change request와 Product Owner 승인 없이는 공식 범위에 반영하지 않는다. | scope creep를 통제하고 문서 기준 실행을 유지하기 위해 | scope control, WBS, roadmap, approvals | `docs/00-governance/scope-change-control.md` |
| D-022 | 2026-03-29 | Decided | Stage Gate Governance | FPDS는 Gate A~D 체크리스트 기준으로 단계 전환을 판단하고, gate 통과 전 다음 단계 구현에 착수하지 않는다. | 설계 미완료 상태의 조기 구현과 단계 전환 착시를 방지하기 위해 | stage transition, approvals, roadmap, WBS | `docs/00-governance/stage-gate-checklist.md` |
| D-023 | 2026-03-29 | Decided | Milestone Tracking Model | FPDS의 milestone due date는 공식 실행 시작 전까지 relative week 기준으로 관리하고, 공식 시작일 확정 후 absolute date를 추가한다. | 아직 build start date가 확정되지 않은 상태에서도 일정 추적을 가능하게 하기 위해 | milestone tracking, roadmap, WBS, governance | `docs/00-governance/milestone-tracker.md` |
| D-024 | 2026-03-30 | Decided | Scope Baseline | WBS 1.1.1~1.1.5의 공식 기준 문서는 `docs/02-requirements/scope-baseline.md`로 고정한다. | Prototype/Phase 1 범위, 비범위, cutline, 개발 시작 승인 방식을 한 장으로 고정하기 위해 | scope baseline, release cutline, approvals | `docs/02-requirements/scope-baseline.md` |
| D-025 | 2026-03-30 | Decided | Non-Goals Baseline | 공식 비범위 목록은 WBS의 예시 3개가 아니라 PRD 전체 `Non-Goals` 목록으로 운영한다. | 구현 직전 scope creep를 막고 exclusion list를 완전한 형태로 고정하기 위해 | scope control, roadmap, WBS, change control | `docs/02-requirements/scope-baseline.md`, PRD 3.2, 4.2 |
| D-026 | 2026-03-30 | Decided | Release Cutline | release cutline은 `Phase 1 release 기준 Must Have / Later`로 관리하며, Phase 2는 계약 범위이지만 Phase 1 release cutline에서는 `Later`로 분리한다. | 계약 범위와 단기 release cutline을 분리해 build sequencing을 명확히 하기 위해 | release planning, WBS, roadmap, change control | `docs/02-requirements/scope-baseline.md` |
| D-027 | 2026-03-30 | Decided | Build Start Approval | 개발 시작 조건은 `Gate A = Pass + Product Owner explicit approval`로 정의한다. | 설계 차단 항목이 닫히지 않은 상태에서의 조기 구현을 막기 위해 | gate governance, implementation start, approvals | `docs/02-requirements/scope-baseline.md`, `docs/00-governance/stage-gate-checklist.md` |
| D-028 | 2026-03-30 | Decided | Taxonomy Model | `product_type`와 `subtype_code`는 country-aware registry 기반 관리형 code로 운영하며, Phase 1 Canada deposit v1 taxonomy는 `chequing`, `savings`, `gic` core type과 extensible subtype registry로 정의한다. | 나라별 상품 분류 확장성과 Phase 1 canonical stability를 함께 확보하기 위해 | taxonomy, schema, parser mapping, dashboard | `docs/03-design/domain-model-canonical-schema.md` |
| D-029 | 2026-03-30 | Decided | Canonical Schema Policy | source-derived product fields는 source language 단일 값으로 유지하고, display/resource label은 별도 localization resource로 관리한다. | 원문 보존과 canonical data, localization boundary를 분리하기 위해 | schema, localization, UI, API | `docs/03-design/domain-model-canonical-schema.md`, D-012 |
| D-030 | 2026-03-30 | Decided | Validation and Confidence Policy | field-level validation rule은 canonical schema 문서 기준으로 고정하고, confidence threshold는 외부 설정값으로 운영하며 Prototype은 전량 review, Phase 1은 policy + config 기준 auto-approve를 허용한다. | review routing 품질을 유지하면서 threshold 변경 비용을 낮추기 위해 | validation, review routing, operations | `docs/03-design/domain-model-canonical-schema.md` |
| D-031 | 2026-03-30 | Decided | Change Event Model | canonical change event는 `New`, `Updated`, `Discontinued`, `Reclassified`, `ManualOverride`를 공식 event type으로 사용한다. | change history, review, publish, audit 흐름을 공통 모델로 맞추기 위해 | change history, audit, publish, admin UX | `docs/03-design/domain-model-canonical-schema.md` |
| D-032 | 2026-03-31 | Decided | Review Queue Unit | ingestion workflow의 review queue 생성 단위는 `candidate` 기준으로 정의한다. | PRD의 review item 구조와 trace/review 흐름을 가장 직접적으로 연결하기 위해 | workflow, admin API, trace viewer, review state | `docs/03-design/workflow-state-ingestion-design.md` |
| D-033 | 2026-03-31 | Decided | Retry Model | ingestion retry 기본 모델은 `source/stage 단위 재시도 + run partial completion 허용 + publish 별도 retry/reconciliation`으로 정의한다. | partial failure를 격리하고 run 전체 재실행을 기본값으로 강제하지 않기 위해 | workflow, run lifecycle, publish lifecycle, operations | `docs/03-design/workflow-state-ingestion-design.md` |
| D-034 | 2026-03-31 | Decided | Source Identity Policy | source identity는 `bank_code + normalized_source_url + source_type`를 기본 키로 하고, `checksum/fingerprint`는 change detection과 idempotency 판단에 사용한다. | source deduplication과 content change detection을 분리해 재수집 안정성을 높이기 위해 | discovery, snapshot, change detection, idempotency | `docs/03-design/workflow-state-ingestion-design.md` |
| D-035 | 2026-03-31 | Decided | Retrieval Boundary | `1.3.1`에서는 retrieval-ready evidence 저장까지를 고정하고, vector index 구현 상세는 `WBS 1.4.4`에서 결정한다. | workflow 상세화와 vector backend 선택 결정을 분리해 Gate A 문서 진행을 막지 않기 위해 | workflow, evidence storage, retrieval design | `docs/03-design/workflow-state-ingestion-design.md` |
| D-036 | 2026-03-31 | Decided | Publish Boundary | `1.3.1`에서는 BX-PF publish를 `interface-first + publish state 중심`으로 정의하고, exact write contract와 field mapping은 `WBS 1.5.4`에서 닫는다. | ingestion 흐름 고정과 BX-PF 상세 계약 결정을 분리하기 위해 | workflow, publish lifecycle, BX-PF contract | `docs/03-design/workflow-state-ingestion-design.md` |
| D-037 | 2026-04-01 | Decided | Review State Machine | review task state는 `queued`, `approved`, `rejected`, `edited`, `deferred`로 정의하고, `approved/rejected/edited`는 terminal, `deferred`는 requeue 가능한 open state로 정의한다. | PRD review action과 candidate-unit review queue를 충돌 없이 연결하는 baseline을 고정하기 위해 | workflow, admin API, review queue, change history, audit | `docs/03-design/review-run-publish-audit-state-design.md` |
| D-038 | 2026-04-01 | Decided | Run Lifecycle | run lifecycle은 `started`, `completed`, `failed`, `retried`로 정의하고, partial source/stage failure는 `completed + partial_completion_flag`로 표현하며 retry는 별도 run link로 추적한다. | partial failure 허용, run status, retry boundary를 한 모델로 정리하기 위해 | workflow, run history, admin UI, operations | `docs/03-design/review-run-publish-audit-state-design.md` |
| D-039 | 2026-04-01 | Decided | Publish Lifecycle | publish tracker state는 `pending`, `published`, `retry`, `reconciliation`으로 정의하고, publish failure가 canonical approval을 롤백하지 않는 것을 기본 원칙으로 한다. | BX-PF contract 미확정 상태에서도 publish readiness와 retry/reconciliation 추적을 가능하게 하기 위해 | publish monitor, reconciliation, BX-PF readiness | `docs/03-design/review-run-publish-audit-state-design.md` |
| D-040 | 2026-04-01 | Decided | Audit Trail Scope | audit baseline은 review/run/publish/auth/config/usage event를 포함하고, actor, target, state diff, reason, correlation metadata를 필수로 남긴다. exact retention duration은 후속 security policy에서 닫는다. | WBS 1.3.5 범위에서 event taxonomy와 required audit payload를 먼저 고정하기 위해 | audit log, security, admin history, runbook | `docs/03-design/review-run-publish-audit-state-design.md` |
| D-041 | 2026-04-01 | Decided | Evidence Storage Strategy | raw snapshot과 parsed text full body는 private object storage에 두고, source/snapshot/parsed/chunk metadata와 field evidence link는 FPDS DB에 둔다. | object artifact와 운영 조회 메타데이터의 책임을 분리해 traceability와 reprocessing을 동시에 만족시키기 위해 | storage, trace viewer, evidence retrieval, retry | `docs/03-design/source-snapshot-evidence-storage-strategy.md` |
| D-042 | 2026-04-01 | Decided | Retrieval Starting Point | Phase 1 retrieval/vector starting point는 `Postgres + pgvector`로 두고, 범위는 `evidence_chunk` embedding과 retrieval metadata에 한정한다. | separate vector service 복잡도를 미루면서 Phase 1 evidence retrieval 요구를 충족하기 위해 | retrieval, AI pipeline, evidence architecture, cost/ops | `docs/03-design/retrieval-vector-starting-point.md` |
| D-043 | 2026-04-01 | Decided | Aggregate Refresh Strategy | public grid와 dashboard aggregate는 canonical write 이후 asynchronous refresh로 갱신하고, latest successful snapshot serving과 TTL-based API cache invalidation을 기본으로 한다. | public read 성능과 canonical write 안정성을 분리하면서 freshness 추적을 가능하게 하기 위해 | dashboard, public APIs, metric health, cache | `docs/03-design/aggregate-cache-refresh-strategy.md` |
| D-044 | 2026-04-01 | Decided | Environment Separation | 현재 공식 환경 모델은 `dev/prod`로 두고, public/admin surface와 private worker/storage/data boundary를 분리한다. `stg`는 필요 시 후속 확장 환경으로 추가한다. | 1인 개발자 운영 복잡도를 낮추면서도 CORS, SSRF, secret, BX-PF integration, object storage access 정책이 같은 trust model을 참조하도록 만들기 위해 | infra, security, worker boundary, deployment, env setup | `docs/03-design/environment-separation-strategy.md` |
| D-045 | 2026-04-01 | Decided | Public API Contract | public route baseline은 `/api/public/products`, `/filters`, `/dashboard-summary`, `/dashboard-rankings`, `/dashboard-scatter`로 두고 공통 filter scope와 freshness metadata를 공유한다. | public grid와 dashboard가 같은 aggregate/product projection vocabulary를 사용하도록 만들기 위해 | public UI, dashboard, aggregate APIs, caching | `docs/03-design/api-interface-contracts.md` |
| D-046 | 2026-04-01 | Decided | Admin API Contract | admin route baseline은 review task, product, run, change history, BX-PF publish, usage, dashboard health를 포함하고, trace viewer는 evidence summary를 제공하되 raw object artifact direct exposure는 금지한다. | review/run/publish/usage 운영 화면이 같은 admin data contract를 참조하도록 만들기 위해 | admin UI, review queue, operations, trace viewer | `docs/03-design/api-interface-contracts.md` |
| D-047 | 2026-04-01 | Decided | Internal Orchestration Interface | internal orchestration은 browser route가 아닌 private service boundary로 두고, discovery, retrieval, normalization, review queue, usage capture 계약은 `run_id`와 `correlation_id`를 공유한다. | worker pipeline과 API server가 같은 orchestration vocabulary로 연결되도록 만들기 위해 | worker pipeline, retry, observability, usage capture | `docs/03-design/api-interface-contracts.md` |
| D-048 | 2026-04-01 | Decided | BX-PF Adapter Contract | BX-PF exact remote schema 대신 FPDS publish service와 connector 사이의 adapter-facing request/response contract를 먼저 고정하고, publish state 매핑은 `applied/duplicate/retryable_error/contract_error/ambiguous` 기준으로 정한다. | external dependency 미확정 상태에서도 connector와 publish state machine을 구현 가능하게 만들기 위해 | publish connector, reconciliation, retry, target mapping | `docs/03-design/api-interface-contracts.md` |
| D-049 | 2026-04-01 | Decided | External API Draft | Phase 2 external API draft baseline은 `/api/v1/products`, `/products/:id`, `/banks`, `/changes`로 두고, tenant scope는 credential-bound context를 기본으로 한다. exact credential type은 후속 security 결정으로 남긴다. | Phase 2 resource model을 먼저 고정해 auth/rate limit 상세와 분리하기 위해 | SaaS API, tenant isolation, versioning, client integration | `docs/03-design/api-interface-contracts.md` |
| D-050 | 2026-04-05 | Decided | Admin Auth | admin human auth는 same-origin admin web + BFF 전제를 두고 server-side session cookie baseline으로 고정한다. | 브라우저 기반 운영 콘솔과 CSRF/session 보호를 가장 직접적으로 맞추기 위해 | admin login, session model, CSRF, auth scaffold | `docs/03-design/security-access-control-design.md` |
| D-051 | 2026-04-05 | Decided | Human RBAC | human admin RBAC baseline은 `admin`, `reviewer`, `read_only` 3개 역할로 둔다. | 운영 권한을 단순하게 유지하면서도 최소 권한 원칙을 적용하기 위해 | admin routes, review flow, audit visibility, privilege change | `docs/03-design/security-access-control-design.md` |
| D-052 | 2026-04-05 | Decided | External API Auth | Phase 2 external API auth baseline은 `tenant-bound API key`로 둔다. | server-to-server 소비 모델과 tenant isolation, usage/audit 분리를 단순하게 맞추기 위해 | external API, tenant scope, credential lifecycle, audit | `docs/03-design/security-access-control-design.md` |
| D-053 | 2026-04-05 | Decided | CORS Policy | browser-facing API CORS는 allowlist-only로 운영하고, admin API는 credentialed exact-origin allowlist만 허용한다. | wildcard를 피하고 public/admin browser trust boundary를 명확히 하기 위해 | public API, admin API, env config, preflight handling | `docs/03-design/security-access-control-design.md` |
| D-054 | 2026-04-05 | Decided | Crawler Safe Fetch | crawler는 등록된 은행만 fetch 대상이 될 수 있고, 해당 은행의 허용 도메인 내부에서는 자유롭게 crawling할 수 있다. | SSRF와 cross-domain drift를 막으면서도 은행 사이트 내부 탐색 자유도를 확보하기 위해 | crawler, source inventory, SSRF, safe fetch policy | `docs/03-design/security-access-control-design.md` |
| D-055 | 2026-04-05 | Decided | Session and Browser Security | admin cookie는 `HttpOnly`, `prod Secure`, `SameSite=Lax`를 baseline으로 두고, cookie-authenticated admin write에는 CSRF 보호와 security header baseline을 적용한다. | session auth 결정과 브라우저 보안 통제를 한 묶음으로 고정하기 위해 | admin API, frontend security, hardening, QA | `docs/03-design/security-access-control-design.md` |
| D-056 | 2026-04-05 | Decided | Secret Rotation and Audit | secret은 environment-separated owner/cadence 기준으로 관리하고 issuance, rotation, revocation, access grant를 모두 audit 대상에 포함한다. | credential 운영과 감사 추적을 구현 이후 hardening이 아니라 baseline 운영 정책으로 고정하기 위해 | DevOps, secrets, audit, external API key lifecycle, BX-PF credential | `docs/03-design/security-access-control-design.md` |
| D-057 | 2026-04-05 | Decided | Product Grid IA | Public Product Grid baseline은 sticky filter bar, result summary row, sort toolbar, card grid, page-based pagination, dashboard sibling navigation으로 구성한다. | public 사용자가 상세 페이지 없이도 빠르게 탐색하고 필터링할 수 있는 최소 정보 구조를 먼저 고정하기 위해 | public UI, public products API, i18n labels, responsive QA | `docs/03-design/product-grid-information-architecture.md` |
| D-058 | 2026-04-05 | Decided | Insight Dashboard Metrics | Public Insight Dashboard baseline은 4개 headline KPI, bank/type composition breakdown, ranking widget catalog, scatter preset catalog로 고정한다. `recently changed` window는 공식 `30일`로 정의한다. | dashboard aggregate, API, UI가 같은 metric vocabulary와 eligibility rule을 참조하도록 만들기 위해 | public dashboard, aggregate snapshots, public APIs, methodology/freshness note | `docs/03-design/insight-dashboard-metric-definition.md` |
| D-059 | 2026-04-05 | Decided | Product-Type Visualization | public dashboard와 product grid의 시각화 emphasis는 `chequing=fee/balance`, `savings=rate/balance`, `gic=rate/term/deposit` 원칙으로 고정하고, mixed-type scope에서는 type-specific scatter를 기본 노출하지 않는다. Phase 1 `chequing` comparative chart는 synthetic convenience metric 없이 `minimum_balance`를 공식 축으로 사용한다. | product type 의미와 맞지 않는 비교를 방지하면서도 기존 ranking/scatter catalog 안에서 UI 기본값을 일관되게 정하기 위해 | public dashboard, product grid, chart defaults, widget priority, methodology copy | `docs/03-design/product-type-visualization-principles.md` |
| D-060 | 2026-04-06 | Decided | Admin Information Architecture | Admin Console baseline은 Overview, Review Queue, Review Detail/Trace, Runs, Change History, Publish Monitor, LLM Usage, Dashboard Health를 분리된 운영 surface로 두고, global search와 contextual drilldown으로 연결한다. Canonical product는 primary nav가 아니라 contextual diagnostic surface로 둔다. | review, run, change, publish, usage, health를 서로 다른 운영 단위로 분리해 triage와 diagnosis 흐름을 단순하게 유지하기 위해 | admin UI, admin routing, review flow, observability, responsive design | `docs/03-design/admin-information-architecture.md` |
| D-061 | 2026-04-06 | Decided | Localization Ownership | UI localization resource의 reference locale은 `en`으로 두고, Product Owner가 locale policy와 copy sign-off owner, Frontend Engineer가 resource key와 implementation steward를 맡는다. | fallback 기준축과 EN/KO/JA resource 운영 책임을 명확히 해 i18n 품질과 release 판단 기준을 안정화하기 위해 | i18n, public/admin copy, QA, locale resource management | `docs/03-design/localization-governance-and-fallback-policy.md` |
| D-062 | 2026-04-06 | Decided | Locale Fallback Policy | UI label은 `selected locale -> en -> safe fallback` 체인을 따르고, source-derived product/evidence text는 번역 fallback 대신 원문 유지 원칙을 따른다. runtime machine translation은 baseline fallback 수단으로 사용하지 않는다. | blank label과 데이터 왜곡을 동시에 피하면서 public/admin/API surface가 같은 locale boundary를 따르도록 만들기 위해 | localization, public/admin UX, API labels, source-language handling | `docs/03-design/localization-governance-and-fallback-policy.md` |
| D-063 | 2026-04-06 | Decided | Japanese Glossary Governance | Japanese glossary는 non-source UI terminology만 다루며, Product Owner가 policy owner, Frontend Engineer가 glossary steward, Domain Reviewer가 금융 용어 consult 역할을 맡는다. brand/product proper noun과 source-derived text는 glossary 번역 대상에서 제외한다. | Phase 2 Japan 확장 전에도 terminology drift를 방지하고 locale-aware taxonomy/display label의 일관성을 유지하기 위해 | localization, taxonomy labels, admin/public UI, phase 2 readiness | `docs/03-design/localization-governance-and-fallback-policy.md` |
| D-064 | 2026-04-06 | Decided | Prototype Source Inventory | TD Savings prototype source baseline은 TD Canada Trust public savings list/detail pages 4개, current rates/fees HTML 2개, governing PDF 6개로 고정한다. Prototype registry는 English public source만 seed로 사용하고, promotion/authenticated/compare flows는 canonical crawl target에서 제외한다. | prototype-first 원칙에 맞게 discovery 범위를 좁히고, safe fetch 정책과 spike 대상을 evidence-rich public source set으로 고정하기 위해 | source registry, crawler allowlist, prototype backlog, spike, acceptance | `docs/01-planning/td-savings-source-inventory.md` |
| D-065 | 2026-04-06 | Decided | Prototype Backlog Baseline | Prototype backlog는 `foundation minimum -> source ingestion core -> reviewability surface -> demo and learning closure` 4개 P0 lane으로 운영하고, Gate B 직결 범위는 `PB-01`~`PB-08`로 고정한다. auth/review queue 운영화/publish/public/i18n work는 Prototype backlog에서 제외한다. | feasibility 검증에 필요한 최소 build sequence를 명확히 하고, Sprint 0와 Gate B 준비가 같은 작업 구조를 참조하도록 만들기 위해 | sprint planning, build sequencing, prototype scope control, Gate B readiness | `docs/01-planning/prototype-backlog.md` |
| D-066 | 2026-04-06 | Decided | Codex Internet Allowlist | FPDS용 Codex 환경은 `무제한` 대신 공식 은행 source, OpenAI, npm, GitHub, 필요 시 vendor docs만 포함하는 allowlist 기반 인터넷 접근을 기본으로 한다. 초기값은 `td.com`, OpenAI 공식 도메인, GitHub, npm registry로 두고, Canada Big 5 확장 시 공식 은행 도메인을 단계적으로 추가한다. | Codex 인터넷 접근을 프로젝트 필요 범위에 맞게 최소화해 보안 위험을 줄이면서도 source verification과 개발 작업을 막지 않기 위해 | Codex environment, source verification, dependency access, security posture | `docs/00-governance/codex-internet-domain-allowlist.md` |
| D-067 | 2026-04-06 | Decided | Prototype Acceptance Baseline | Prototype acceptance는 `완전 자동화`가 아니라 `3개 target product coverage + source type coverage + evidence-linked reviewability + findings memo`를 증명하는 것으로 정의한다. ancillary field 누락이나 일부 P1 supporting source 실패는 conditional pass로 수용할 수 있다. | Gate B 성공 조건을 feasibility와 reviewability 중심으로 고정해 Prototype의 범위를 과도하게 넓히지 않기 위해 | Gate B, prototype demo, findings memo, evidence pack, backlog done definition | `docs/01-planning/prototype-acceptance-checklist.md` |
| D-068 | 2026-04-06 | Decided | Prototype Spike Scope | Prototype spike는 `TD-SAV-004`, `TD-SAV-007`, `TD-SAV-008`을 primary target으로 두고 snapshot viability, parse/evidence anchor quality, key field extraction feasibility, special-case review path를 검증한다. | 가장 위험한 HTML/PDF source를 먼저 검증해 parser/evidence feasibility 리스크를 조기에 줄이기 위해 | spike planning, RAID validation, prototype sequencing, source risk retirement | `docs/01-planning/prototype-spike-scope.md` |
| D-069 | 2026-04-06 | Decided | Sprint 0 Ready Board | Sprint 0는 active execution report가 아니라 `Gate A Pass` 이후 즉시 참조할 ready board로 관리하고, foundation minimum과 source ingestion core를 우선순위화한다. | 조기 구현 리스크를 막으면서도 Gate A 통과 직후 실행 순서를 명확히 해 single-developer 흐름을 부드럽게 유지하기 위해 | build-start governance, sprint planning, foundation sequencing, prototype execution order | `docs/01-planning/sprint-0-board.md` |
| D-070 | 2026-04-06 | Superseded | Gate A Review Outcome | `2026-04-06` initial Gate A review 결과는 `Deferred`로 기록되었다. 설계 패키지와 Build Start Sign-off Package는 준비되었지만, 당시에는 `Product Owner explicit approval`이 아직 기록되지 않았다. | first review 시점의 상태를 보존하고, 후속 승인 결정과 구분하기 위해 | gate governance, build-start approval, roadmap, WBS stage transition | `docs/00-governance/gate-a-build-start-review-note.md` |
| D-071 | 2026-04-06 | Decided | Gate A Approval | final cross-document consistency review에서 Gate A blocker가 없음을 재확인했고, Product Owner approval을 반영해 Gate A를 `Pass`로 승인한다. Foundation과 Prototype build stage는 `Next` 상태로 전환하지만, 실제 구현 시작은 별도 실행 시작 지시 전까지 보류한다. | deferred review 결과와 최종 승인 결정을 분리해 기록하고, 문서 패키지 완결성과 stage transition 상태를 현재 기준으로 고정하기 위해 | gate governance, milestone tracking, roadmap, WBS stage transition | `docs/00-governance/gate-a-build-start-review-note.md`, `docs/00-governance/milestone-tracker.md`, `docs/01-planning/WBS.md` |
| D-072 | 2026-04-07 | Decided | Harness Engineering | repository harness baseline은 `AGENTS.md`, staged-only pre-commit, report-only cleanup audit, and repository-wide CI checks로 시작한다. product implementation은 이 harness work로 자동 시작되지 않는다. | WBS 2와 WBS 3 착수 전에 workflow guardrail, 문서 정합성 점검, 조용한 성공/실패 시 알림 규칙을 먼저 고정하기 위해 | engineering workflow, hooks, CI, documentation, build-start discipline | `docs/00-governance/harness-engineering-baseline.md` |
| D-073 | 2026-04-07 | Decided | Implementation Memory | 의미 있는 구현 slice가 끝날 때마다 다음 Codex 세션이 코드 전체를 다시 읽지 않고 이어갈 수 있도록 development journal entry를 남긴다. entry는 goal, outcome, key files, decisions, verification, next step을 포함한다. | chat history 의존도를 줄이고 repo 문서만으로 재진입과 handoff가 가능하게 만들기 위해 | engineering workflow, documentation, handoff, resume efficiency | `docs/00-governance/development-journal.md`, `docs/00-governance/harness-engineering-baseline.md` |
| D-074 | 2026-04-07 | Decided | Calendar Schedule Baseline | 공식 실행 캘린더는 `2026-04-07`을 시작점으로 두고, `Phase 1 development complete = 2026-05-04`, `Phase 1 testing start = 2026-05-05`, `Phase 2 all development and testing complete = 2026-07-31`로 고정한다. WBS task due date와 milestone calendar due는 이 기준으로 갱신한다. | relative week 기반 계획을 실제 실행 달력으로 전환하고, 향후 task due date와 milestone due date를 같은 절대 일정 기준으로 관리하기 위해 | WBS scheduling, milestone tracking, roadmap, delivery governance | `docs/01-planning/WBS.md`, `docs/00-governance/milestone-tracker.md`, `docs/00-governance/roadmap.md` |

| D-075 | 2026-04-07 | Decided | Dev and Prod Env Template Baseline | WBS `2.2` baseline uses tracked placeholder-only example files `.env.dev.example` and `.env.prod.example` plus a repo-level env spec. `dev` remains the only local development environment shape, and real BX-PF credentials and write-back are `prod` only. | environment separation was already approved at the design level, but follow-on foundation work needs a concrete minimum config contract for DB, storage, origins, session security, crawler policy, monitoring, LLM, and BX-PF without committing secrets or locking the runtime to one framework too early. | env config, secret handling, local bootstrap, WBS 2.2, future scaffolds | `docs/03-design/dev-prod-environment-spec.md`, `.env.dev.example`, `.env.prod.example`, `shared/config/README.md` |

---

| D-076 | 2026-04-07 | Decided | SQL-First DB Migration Baseline | WBS `2.3` uses a Postgres-first, SQL-first migration baseline in-repo. The first migration creates the core ingestion, evidence, candidate, review, canonical, publish, usage, audit, taxonomy, and processing-policy tables, while keeping ids as application-generated `text` and deferring `pgvector`, auth-vendor tables, and dashboard tables to later work. | the ERD and workflow baselines were already closed, but implementation needed a concrete initial schema that could move forward without prematurely locking the project to one ORM or framework. | database baseline, migrations, prototype readiness, WBS 2.3, future scaffolds | `docs/03-design/db-migration-baseline.md`, `db/migrations/0001_initial_baseline.sql`, `db/README.md` |
| D-077 | 2026-04-07 | Decided | Private Object Storage Baseline | WBS `2.4` uses a private, S3-compatible object storage baseline with separate `dev` and `prod` buckets as the preferred shape, `{env}/...` key separation as the fallback minimum, and browser-facing surfaces blocked from direct raw object access. The tracked baseline adds storage layout examples, env keys for object subtree names and private-access mode, and a repo-level storage contract for snapshots and parsed artifacts. | the storage strategy was already approved at the design level, but prototype ingestion work needed a concrete bucket and object-key baseline before snapshot capture and parsing could be implemented without path drift or accidental public exposure. | object storage, evidence lineage, private access, env contract, WBS 2.4, prototype readiness | `docs/03-design/object-storage-evidence-bucket-baseline.md`, `storage/object-layout.example.json`, `storage/README.md`, `.env.dev.example`, `.env.prod.example` |
| D-078 | 2026-04-07 | Decided | Monitoring and Error Tracking Baseline | WBS `2.7` uses a provider-neutral observability contract with separate `request_id`, `correlation_id`, and `run_id`, controlled browser-facing error envelopes, structured internal events, env-driven provider selection, and `sentry` as the current preferred production provider label. | prototype and Phase 1 work need diagnosable failures before runtime framework details are locked, and the PRD requires controlled error responses plus traceable correlation metadata without exposing secrets or internal paths. | observability, prototype diagnosis, run status, error handling, env contract, WBS 2.7 | `docs/03-design/monitoring-error-tracking-baseline.md`, `shared/observability/README.md`, `shared/observability/error-envelope.example.json`, `shared/observability/structured-log-event.example.json` |
| D-079 | 2026-04-07 | Decided | Foundation CI/CD Baseline | WBS `2.10` uses a GitHub Actions foundation pipeline that reuses repository PowerShell entrypoints for repo doctor, env/observability contract validation, conditional package-script checks, and report-only cleanup audit. Deployment automation remains intentionally deferred until real infrastructure, secrets, and promotion policy are approved. | the repo already had harness CI, but foundation work needed a concrete local-and-CI baseline that can run now without forcing a framework or deployment platform choice too early. | CI, local validation parity, future package scripts, documentation, WBS 2.10 | `docs/00-governance/foundation-ci-cd-baseline.md`, `.github/workflows/harness.yml`, `scripts/harness/invoke-foundation-checks.ps1`, `scripts/harness/validate-foundation-baseline.ps1`, `scripts/harness/invoke-project-checks.ps1` |

## 5. Change History

| Date | Change |
|---|---|
| 2026-03-29 | Initial decision log created from PRD, plan, and WBS baseline |
| 2026-03-29 | Added governance model decision linked to working agreement |
| 2026-03-29 | Added staffing model decision linked to roadmap planning |
| 2026-03-29 | Added scope governance and stage gate governance decisions |
| 2026-03-29 | Added milestone tracking model decision |
| 2026-03-30 | Added scope baseline, non-goals baseline, Phase 1 release cutline, and build-start approval decisions |
| 2026-03-30 | Added taxonomy model, canonical schema policy, validation/confidence policy, and change event model decisions |
| 2026-03-31 | Added ingestion workflow decisions for review unit, retry model, source identity, retrieval boundary, and publish boundary |
| 2026-04-01 | Added review state machine, run lifecycle, publish lifecycle, and audit trail scope decisions |
| 2026-04-01 | Added evidence storage, retrieval starting point, aggregate refresh, and environment separation decisions |
| 2026-04-01 | Added public/admin/internal/BX-PF/external API contract decisions |
| 2026-04-05 | Closed admin auth, RBAC, CORS, crawler safe fetch, browser security, and secret rotation decisions |
| 2026-04-05 | Added Product Grid information architecture baseline decision |
| 2026-04-05 | Closed dashboard KPI/ranking/scatter metric baseline with the Insight Dashboard metric definition decision |
| 2026-04-05 | Closed product-type-aware visualization defaults and mixed-type dashboard behavior with the visualization principles decision |
| 2026-04-06 | Added admin information architecture baseline decision and closed WBS 1.7.4 |
| 2026-04-06 | Closed localization ownership, fallback, and Japanese glossary open item with localization governance baseline decisions |
| 2026-04-06 | Added TD Savings prototype source inventory baseline decision and closed WBS 1.8.1 |
| 2026-04-06 | Added prototype backlog baseline decision and closed WBS 1.8.2 |
| 2026-04-06 | Added Codex internet allowlist baseline for FPDS project environment |
| 2026-04-06 | Added prototype acceptance, spike scope, and Sprint 0 ready board baselines and closed WBS 1.8.3~1.8.5 |
| 2026-04-06 | Added Gate A build-start review outcome and closed WBS 1.8.6 review task |
| 2026-04-06 | Superseded the initial Deferred Gate A result and recorded final Gate A Pass approval |
| 2026-04-07 | Added harness engineering baseline decision for staged-only pre-commit, report-only cleanup audit, and CI checks |
| 2026-04-07 | Added implementation memory decision and development journal baseline for resume-friendly handoff |
| 2026-04-07 | Added absolute calendar schedule baseline for WBS and milestone due date tracking |
| 2026-04-07 | Added dev and prod env template baseline decision for WBS 2.2 |
| 2026-04-07 | Added SQL-first DB migration baseline decision for WBS 2.3 |
| 2026-04-07 | Added private object storage baseline decision for WBS 2.4 |
| 2026-04-07 | Added monitoring and error tracking baseline decision for WBS 2.7 |
| 2026-04-07 | Added foundation CI/CD baseline decision for WBS 2.10 |
