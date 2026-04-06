# FPDS Detailed WBS

Version: 1.0  
Date: 2026-03-29  
Based on:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`

---

## 1. Executive Summary

두 문서를 기준으로 보면, **지금 당장 진행해야 하는 일은 개발 착수가 아니라 상세 설계 마감과 미결정 항목 종료**입니다.

현재 우선순위는 아래 3가지입니다.

1. `Open Items for Detailed Design`를 모두 닫는다.
2. Build Start Gate를 통과할 수준으로 설계 문서를 고정한다.
3. Prototype 착수용 backlog와 acceptance 기준을 확정한다.

즉, 지금 단계의 공식 목표는 **코드 작성이 아니라 "개발을 시작해도 되는 상태"를 만드는 것**입니다.

---

## 2. What We Should Do Next

지금 바로 시작해야 하는 순서는 아래가 가장 맞습니다.

1. workflow/state model과 change/review lifecycle을 확정한다.
2. ERD, evidence 저장 전략, retrieval 시작점을 설계한다.
3. BX-PF write contract와 public/admin/internal API draft를 정리한다.
4. 인증/권한, 보안 정책, public/admin/API 경계를 설계한다.
5. TD Savings source inventory와 prototype backlog/acceptance를 고정한다.

중요 원칙:
- **개발 시작 금지**: 모든 계획/설계 완료 후 Product Owner가 명시적으로 시작 승인할 때까지 구현하지 않는다.
- **Prototype First**: Big 5 확장은 Prototype 성공 이후에만 진행한다.
- **Canonical Before UI Polish**: 스키마와 검증 규칙이 먼저다.
- **Security by Default**: 보안은 릴리스 직전 hardening 항목이 아니라 설계 단계부터 포함한다.

---

## 3. WBS Management Rules

### 3.1 Status Definitions

| Status | Meaning |
|---|---|
| `Now` | 지금 즉시 진행해야 하는 작업 |
| `Completed` | 완료되어 결과물이 생성된 작업 |
| `Next` | 설계 마감 후 바로 이어지는 작업 |
| `Blocked` | 명시적 개발 승인 전에는 착수하지 않는 작업 |
| `Later` | Phase 2 또는 후속 확장 작업 |

### 3.2 Recommended Roles

| Role | Responsibility |
|---|---|
| Product Owner | 우선순위, 범위, 승인, 최종 결정 |
| Tech Lead / Architect | 전체 설계, 기술 방향, 인터페이스 정합성 |
| Backend Engineer | API, DB, workflow, publish 흐름 |
| AI/Data Engineer | source, parsing, extraction, normalization |
| Frontend Engineer | public/admin UI, dashboard, i18n |
| DevOps / Security | 환경, secret, 배포, 모니터링, 보안 baseline |
| QA / Reviewer | acceptance, regression, 운영 시나리오 검증 |
| Domain Reviewer | 금융상품 taxonomy, field 해석, 품질 검증 |

---

## 4. Milestones and Gates

| Milestone | Description | Gate Condition |
|---|---|---|
| M1 | 요구사항/실행계획 검토 완료 | 본 WBS 승인 |
| M2 | 상세 설계 마감 | Gate A 통과 |
| M3 | Foundation 완료 | 환경/보안/기본 골격 준비 완료 |
| M4 | Prototype E2E 성공 | Gate B 통과 |
| M5 | Admin/Ops Core 완료 | Gate C 통과 |
| M6 | Canada Big 5 Public Release Ready | Phase 1 acceptance 충족 |
| M7 | BX-PF Publish Readiness 완료 | 운영/문서/재처리 체계 준비 완료 |
| M8 | Phase 2 Japan/API Ready | Phase 2 acceptance 충족 |

### Gate A. Build Start Gate
- detailed design 완료
- prototype backlog 확정
- 개발 환경/작업 방식 준비 완료

### Gate B. Prototype Gate
- TD Savings 기준 end-to-end 1회 이상 성공
- evidence linkage, canonical mapping, 내부 확인 UI 검증 완료

### Gate C. Phase 1 Expansion Gate
- review queue / trace / run history / usage tracking 준비 완료
- canonical schema와 검증 규칙 안정화 완료

### Gate D. Release Gate
- acceptance criteria 충족
- 보안/운영/문서 준비 완료
- critical issue 0건

---

## 5. Detailed WBS

## WBS 0. Program Governance and Control

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 0.1 | Completed | 프로젝트 운영 방식 확정 | working agreement, sync cadence, 보고 방식 | Product Owner, Tech Lead | 없음 |
| 0.2 | Completed | Decision Log 생성 | `docs/00-governance/decision-log.md` 초안 | Product Owner, Tech Lead | 0.1 |
| 0.3 | Completed | RAID Log 생성 | `docs/00-governance/raid-log.md` 초안 | Product Owner, Tech Lead | 0.1 |
| 0.4 | Completed | Scope change control 규칙 확정 | `docs/00-governance/scope-change-control.md` | Product Owner | 0.1 |
| 0.5 | Completed | Stage gate 운영 기준 확정 | `docs/00-governance/stage-gate-checklist.md` | Product Owner, QA | 0.4 |
| 0.6 | Completed | milestone tracking 체계 확정 | `docs/00-governance/milestone-tracker.md` | Delivery Lead | 0.5 |

## WBS 1. Detailed Design Closure

### 1.1 Scope and Product Boundary

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 1.1.1 | Completed | Prototype 범위 고정 | `docs/02-requirements/scope-baseline.md` Section 3 | Product Owner, Tech Lead | 0.2 |
| 1.1.2 | Completed | Phase 1 v1 범위 고정 | `docs/02-requirements/scope-baseline.md` Section 4 | Product Owner | 1.1.1 |
| 1.1.3 | Completed | 비범위 항목 재확인 | `docs/02-requirements/scope-baseline.md` Section 5 | Product Owner | 1.1.2 |
| 1.1.4 | Completed | release cutline 정의 | `docs/02-requirements/scope-baseline.md` Section 6 | Product Owner, Tech Lead | 1.1.3 |
| 1.1.5 | Completed | 승인 방식 정의 | `docs/02-requirements/scope-baseline.md` Section 7 | Product Owner | 1.1.4 |

### 1.2 Domain Model and Canonical Schema

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 1.2.1 | Completed | Canada deposit taxonomy 확정 | `docs/03-design/domain-model-canonical-schema.md` Section 3 | Domain Reviewer, Tech Lead | 1.1.2 |
| 1.2.2 | Completed | canonical product schema v1 설계 | `docs/03-design/domain-model-canonical-schema.md` Section 4 | Tech Lead, Backend | 1.2.1 |
| 1.2.3 | Completed | source-derived 필드 정책 정의 | `docs/03-design/domain-model-canonical-schema.md` Section 4.7 | Tech Lead | 1.2.2 |
| 1.2.4 | Completed | field-level validation rules 정의 | `docs/03-design/domain-model-canonical-schema.md` Section 5 | Backend, Domain Reviewer | 1.2.2 |
| 1.2.5 | Completed | confidence scoring/routing 기준 정의 | `docs/03-design/domain-model-canonical-schema.md` Section 6 | AI/Data, Tech Lead | 1.2.4 |
| 1.2.6 | Completed | change event model 정의 | `docs/03-design/domain-model-canonical-schema.md` Section 7 | Backend | 1.2.2 |
| 1.2.7 | Completed | Japan 확장 대비 schema 확인 | `docs/03-design/domain-model-canonical-schema.md` Section 8 | Tech Lead | 1.2.2 |

### 1.3 Workflow and State Design

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 1.3.1 | Completed | end-to-end ingestion flow 상세화 | `docs/03-design/workflow-state-ingestion-design.md` Sections 2-9 | Tech Lead, AI/Data | 1.2.2 |
| 1.3.2 | Completed | review state machine 정의 | `docs/03-design/review-run-publish-audit-state-design.md` Section 3 | Backend | 1.3.1 |
| 1.3.3 | Completed | run lifecycle 정의 | `docs/03-design/review-run-publish-audit-state-design.md` Section 4 | Backend | 1.3.1 |
| 1.3.4 | Completed | publish lifecycle 정의 | `docs/03-design/review-run-publish-audit-state-design.md` Section 5 | Backend | 1.3.1 |
| 1.3.5 | Completed | audit trail scope 정의 | `docs/03-design/review-run-publish-audit-state-design.md` Section 6 | Backend, Security | 1.3.2 |

### 1.4 Architecture and Data Storage Design

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 1.4.1 | Completed | 시스템 컨텍스트 다이어그램 작성 | `docs/03-design/system-context-diagram.md` Sections 2-7 | Tech Lead | 1.3.1 |
| 1.4.2 | Completed | ERD 초안 작성 | `docs/03-design/erd-draft.md` Sections 2-8 | Backend | 1.2.2 |
| 1.4.3 | Completed | source snapshot/evidence 저장 전략 확정 | `docs/03-design/source-snapshot-evidence-storage-strategy.md` Sections 2-10 | AI/Data, Backend | 1.4.2 |
| 1.4.4 | Completed | retrieval/vector 시작점 결정 | `docs/03-design/retrieval-vector-starting-point.md` Sections 2-9 | Tech Lead, AI/Data | 1.4.3 |
| 1.4.5 | Completed | aggregate/cache refresh 전략 정의 | `docs/03-design/aggregate-cache-refresh-strategy.md` Sections 2-9 | Backend | 1.4.2 |
| 1.4.6 | Completed | 환경 분리 전략 정리 | `docs/03-design/environment-separation-strategy.md` Sections 2-9 | DevOps | 1.4.1 |

### 1.5 API and Interface Contracts

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 1.5.1 | Completed | public API contract 정의 | `docs/03-design/api-interface-contracts.md` Section 4 | Backend, Frontend | 1.2.2 |
| 1.5.2 | Completed | admin API contract 정의 | `docs/03-design/api-interface-contracts.md` Section 5 | Backend, Frontend | 1.3.2 |
| 1.5.3 | Completed | internal orchestration interface 정의 | `docs/03-design/api-interface-contracts.md` Section 6 | Tech Lead | 1.3.1 |
| 1.5.4 | Completed | BX-PF write contract 초안 작성 | `docs/03-design/api-interface-contracts.md` Section 7 | Backend, Tech Lead | 1.2.2 |
| 1.5.5 | Completed | external SaaS/Open API 초안 작성 | `docs/03-design/api-interface-contracts.md` Section 8 | Backend | 1.5.1 |

### 1.6 Security and Access Control Design

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 1.6.1 | Completed | admin auth 방식 결정 | `docs/03-design/security-access-control-design.md` Section 3 | Product Owner, Tech Lead, Security | 1.5.2 |
| 1.6.2 | Completed | RBAC 설계 | `docs/03-design/security-access-control-design.md` Section 4 | Security, Tech Lead | 1.6.1 |
| 1.6.3 | Completed | external API auth 방향 정의 | `docs/03-design/security-access-control-design.md` Section 5 | Security, Backend | 1.5.5 |
| 1.6.4 | Completed | CORS/origin 정책 정의 | `docs/03-design/security-access-control-design.md` Section 6 | Security | 1.4.6 |
| 1.6.5 | Completed | crawler safe fetch / SSRF 정책 정의 | `docs/03-design/security-access-control-design.md` Section 7 | Security, AI/Data | 1.4.1 |
| 1.6.6 | Completed | session/CSRF/security headers 정책 정의 | `docs/03-design/security-access-control-design.md` Section 8 | Security | 1.6.1 |
| 1.6.7 | Completed | secret rotation and audit scope 정의 | `docs/03-design/security-access-control-design.md` Section 9 | DevOps, Security | 1.6.6 |

### 1.7 Public/Admin UX and Localization Design

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 1.7.1 | Completed | Product Grid 정보 구조 설계 | `docs/03-design/product-grid-information-architecture.md` Sections 2-13 | Frontend, Product Owner | 1.5.1 |
| 1.7.2 | Completed | Insight Dashboard metric 정의 | `docs/03-design/insight-dashboard-metric-definition.md` Sections 2-10 | Product Owner, Frontend, Backend | 1.4.5 |
| 1.7.3 | Completed | product-type별 시각화 원칙 확정 | `docs/03-design/product-type-visualization-principles.md` Sections 2-10 | Product Owner, Frontend | 1.7.2 |
| 1.7.4 | Now | admin 정보 구조 설계 | review queue, trace viewer, run detail, usage dashboard 레이아웃 | Frontend | 1.5.2 |
| 1.7.5 | Now | i18n resource ownership 정의 | EN/KO/JA 번역 주체와 리뷰 방식 | Product Owner, Frontend | 1.7.1 |
| 1.7.6 | Now | locale fallback 정책 정의 | label fallback, source-derived text 처리 원칙 | Frontend, Product Owner | 1.7.5 |
| 1.7.7 | Later | Japanese glossary 정책 정의 | 용어집 owner 및 유지 규칙 | Product Owner | 1.7.6 |

### 1.8 Prototype Planning Package

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 1.8.1 | Now | TD Savings source inventory 작성 | 대상 URL/PDF 목록, 예상 필드, 위험도 | AI/Data | 1.1.1 |
| 1.8.2 | Now | prototype backlog 분해 | user story/task list, 우선순위 | Tech Lead, Backend, AI/Data | 1.3.1 |
| 1.8.3 | Now | prototype acceptance checklist 고정 | 성공 기준, 데모 기준, 실패 시 보완 판단 기준 | Product Owner, QA | 1.8.2 |
| 1.8.4 | Now | Spike 범위 정의 | parser/snapshot 실험 범위와 종료 조건 | Tech Lead, AI/Data | 1.8.1 |
| 1.8.5 | Now | Sprint 0 작업판 확정 | 설계 마감용 태스크 보드 | Delivery Lead | 1.8.2 |
| 1.8.6 | Now | Build Start Gate 검토 | 개발 시작 승인 전 점검표 | Product Owner, Tech Lead | 1.8.3 |

## WBS 2. Foundation Setup

> 상태: `Blocked`  
> 조건: Gate A 통과 후, Product Owner의 명시적 개발 시작 승인 필요

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 2.1 | Blocked | repo 구조 생성 | app/api/worker/shared/docs 구조 | Tech Lead | Gate A |
| 2.2 | Blocked | 환경 분리 및 env 템플릿 구성 | dev/prod env spec | DevOps | 2.1 |
| 2.3 | Blocked | DB 및 migration baseline 준비 | 초기 schema migration | Backend | 1.4.2 |
| 2.4 | Blocked | object storage/evidence bucket 준비 | snapshot/chunk 저장소 | DevOps | 1.4.3 |
| 2.5 | Blocked | auth scaffold 구성 | admin auth 기본 구조 | Backend | 1.6.1 |
| 2.6 | Blocked | i18n scaffold 구성 | EN/KO/JA locale skeleton | Frontend | 1.7.5 |
| 2.7 | Blocked | monitoring/error tracking baseline 구성 | Sentry or equivalent | DevOps | 2.1 |
| 2.8 | Blocked | security baseline 적용 | headers, secret handling, access boundary | Security, DevOps | 1.6.6 |
| 2.9 | Blocked | public/admin route skeleton 준비 | empty shell routes | Frontend | 2.1 |
| 2.10 | Blocked | CI/CD 기본 파이프라인 준비 | lint/typecheck/build/test baseline | DevOps | 2.1 |

## WBS 3. Prototype Build - TD Savings

> 상태: `Blocked`  
> 조건: Gate A 통과 후 착수

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 3.1 | Blocked | source discovery 구현 | TD Savings source capture | AI/Data | 1.8.1, 2.4 |
| 3.2 | Blocked | snapshot 수집 구현 | HTML/PDF snapshot 저장 | AI/Data | 3.1 |
| 3.3 | Blocked | parsing/chunking 구현 | parsed text + chunk metadata | AI/Data | 3.2 |
| 3.4 | Blocked | evidence retrieval 구조 구현 | field-to-evidence 연결 구조 | AI/Data, Backend | 3.3 |
| 3.5 | Blocked | extraction flow 구현 | 구조화 candidate 생성 | AI/Data | 3.4 |
| 3.6 | Blocked | normalization mapping 구현 | canonical schema 매핑 | Backend, AI/Data | 3.5 |
| 3.7 | Blocked | validation/confidence routing 구현 | review 대상 분기 규칙 반영 | Backend, AI/Data | 3.6 |
| 3.8 | Blocked | internal result viewer 구현 | prototype 확인 UI | Frontend | 3.7 |
| 3.9 | Blocked | first end-to-end run 실행 | 성공 run evidence pack | QA, Tech Lead | 3.8 |
| 3.10 | Blocked | prototype findings memo 작성 | 확장 가능성/제약/보완 항목 정리 | Tech Lead | 3.9 |

## WBS 4. Admin and Ops Core

> 상태: `Blocked`  
> 조건: Prototype 성공 후 착수

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 4.1 | Blocked | admin login 구현 | 보호된 admin 진입 | Backend, Frontend | 2.5 |
| 4.2 | Blocked | review queue 구현 | 목록/상태/검색/정렬 | Backend, Frontend | 1.3.2 |
| 4.3 | Blocked | review decision flow 구현 | approve/reject/edit approve | Backend | 4.2 |
| 4.4 | Blocked | evidence trace viewer 구현 | source, chunk, mapping, model run 표시 | Frontend, Backend | 3.4 |
| 4.5 | Blocked | run status 화면 구현 | run list/detail/error summary | Frontend, Backend | 1.3.3 |
| 4.6 | Blocked | change history 화면 구현 | change event 조회 | Frontend, Backend | 1.2.6 |
| 4.7 | Blocked | audit log baseline 구현 | review/auth/publish 이력 저장 | Backend, Security | 1.3.5 |
| 4.8 | Blocked | LLM usage tracking 구현 | run/agent/model별 usage 저장 | Backend, AI/Data | 1.5.3 |
| 4.9 | Blocked | usage dashboard v1 구현 | token/cost trend 화면 | Frontend, Backend | 4.8 |
| 4.10 | Blocked | 운영 시나리오 QA | review->approve->history 검증 | QA | 4.3, 4.4, 4.5 |

## WBS 5. Phase 1 Canada Expansion and Public Experience

> 상태: `Blocked`  
> 조건: Prototype 성공 + Admin/Ops Core 안정화 후 착수

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 5.1 | Blocked | Big 5 source registry 완성 | RBC/TD/BMO/Scotiabank/CIBC source 목록 | AI/Data | 1.1.2 |
| 5.2 | Blocked | Chequing parser 확장 | product type coverage | AI/Data | 5.1 |
| 5.3 | Blocked | Savings parser 확장 | product type coverage | AI/Data | 5.1 |
| 5.4 | Blocked | GIC/Term parser 확장 | product type coverage | AI/Data | 5.1 |
| 5.5 | Blocked | per-bank normalization rule 보강 | bank별 예외 처리 | Backend, AI/Data | 5.2, 5.3, 5.4 |
| 5.6 | Blocked | aggregate dataset 생성 | KPI/ranking/scatter 원천 데이터 | Backend | 1.7.2 |
| 5.7 | Blocked | public products API 구현 | grid/filter/sort 조회 API | Backend | 1.5.1 |
| 5.8 | Blocked | dashboard APIs 구현 | summary/ranking/scatter API | Backend | 5.6 |
| 5.9 | Blocked | Product Grid UI 구현 | public catalog 화면 | Frontend | 1.7.1, 5.7 |
| 5.10 | Blocked | Insight Dashboard UI 구현 | KPI, ranking, scatter 화면 | Frontend | 1.7.2, 5.8 |
| 5.11 | Blocked | grid/dashboard cross-filter 적용 | 필터 상태 공유 | Frontend | 5.9, 5.10 |
| 5.12 | Blocked | EN/KO/JA locale 적용 | public/admin trilingual UI | Frontend | 1.7.5 |
| 5.13 | Blocked | freshness/metric note 표기 | methodology/freshness 노출 | Frontend, Backend | 5.8 |
| 5.14 | Blocked | responsive QA 수행 | desktop/tablet/mobile 검증 | QA | 5.9, 5.10 |

## WBS 6. BX-PF Publish Readiness and Release Hardening

> 상태: `Blocked`  
> 조건: Phase 1 핵심 기능 안정화 후 착수

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 6.1 | Blocked | BX-PF connector 구현 | interface-first connector | Backend | 1.5.4 |
| 6.2 | Blocked | approved product publish flow 구현 | approve 후 publish queue 연결 | Backend | 6.1, 4.3 |
| 6.3 | Blocked | pending/retry/reconciliation 구현 | 실패 복구 및 상태 추적 | Backend | 6.2 |
| 6.4 | Blocked | publish monitor UI 구현 | admin publish status 화면 | Frontend | 6.3 |
| 6.5 | Blocked | 보안 하드닝 검증 | authz, CORS, CSRF, SSRF, headers 점검 | Security, QA | 5.14 |
| 6.6 | Blocked | 운영 runbook 작성 | 장애 대응/재처리/권한 운영 문서 | Tech Lead, DevOps | 6.3 |
| 6.7 | Blocked | release checklist 작성 | Phase 1 release checklist | QA, Product Owner | 6.5, 6.6 |
| 6.8 | Blocked | acceptance evidence pack 준비 | 데모 자료, 테스트 결과, 운영 체크 | QA | 6.7 |

## WBS 7. Phase 2 Japan Expansion and External API

> 상태: `Later`

| WBS ID | Status | Task | Key Output | Owner | Dependency |
|---|---|---|---|---|---|
| 7.1 | Later | Japan Big 5 최종 대상 확정 | 기관 목록과 source inventory | Product Owner, Domain Reviewer | 1.2.7 |
| 7.2 | Later | Japanese source parsing 설계/구현 | locale-aware parser | AI/Data | 7.1 |
| 7.3 | Later | 일본 taxonomy 매핑 | locale subtype mapping | Domain Reviewer, Backend | 7.2 |
| 7.4 | Later | external API auth 구현 | tenant/client auth | Backend, Security | 1.6.3 |
| 7.5 | Later | external search/detail/change API 구현 | `/api/v1/products`, `/changes` 등 | Backend | 1.5.5 |
| 7.6 | Later | API rate limit/SLA 운영체계 구현 | usage policy enforcement | Backend, DevOps | 7.4 |
| 7.7 | Later | API docs 작성 | EN/JA 우선 문서 | Backend, Product Owner | 7.5 |
| 7.8 | Later | API monitoring/audit separation 구현 | tenant별 usage/error 추적 | DevOps, Backend | 7.5 |

---

## 6. Immediate Action Backlog

아래 항목은 **지금 바로 진행 가능한 실제 업무 목록**입니다.  
단, 이 단계는 설계/계획 작업이며 구현 작업이 아닙니다.

| Priority | Task | Expected Result |
|---|---|---|
| P0 | review state machine 확정 | review queue와 승인 흐름을 고정 |
| P0 | run/publish lifecycle 확정 | 운영/배포 상태 추적 기준 통일 |
| P0 | ERD 초안 작성 | DB/migration/interface 기준 마련 |
| P0 | BX-PF write contract 초안 확정 | 나중에 연동 때문에 되돌아가지 않도록 방지 |
| P0 | admin auth / RBAC / security 정책 확정 | 보안을 설계 초기부터 반영 |
| P0 | KPI/ranking/scatter 정의 확정 | dashboard를 숫자 기준 없이 만들지 않도록 방지 |
| P1 | i18n ownership / fallback 정책 확정 | EN/KO/JA 운영 품질 확보 |
| P1 | TD Savings source inventory 작성 | Prototype 준비 완료 |
| P1 | Sprint 0 backlog 확정 | Gate A 통과 준비 |

---

## 7. Open Decisions to Close Before Coding

아래 항목은 개발 시작 전에 닫아야 합니다.

| Decision Area | Decision Needed | Why It Must Be Closed First |
|---|---|---|
| BX-PF | exact write contract and field mapping | publish 흐름 재작업 방지 |
| Auth | admin session vs token | 보안 구조와 구현 방식 결정 |
| RBAC | role matrix와 승인 권한 범위 | 운영 리스크 방지 |
| Security | CORS, SSRF, CSP, CSRF 정책 | public/admin/api 경계 보호 |
| Dashboard | KPI, ranking, scatter axis 정의 | UI가 임의 계산으로 흐르는 것 방지 |
| Localization | ownership, fallback, glossary | 다국어 운영 일관성 확보 |
| Search/Retrieval | vector indexing starting point | evidence retrieval 구조 결정 |
| Phase 2 API | auth, tenant scope, rate limit | 이후 API 설계 충돌 방지 |

---

## 8. Recommended Sequence

1. scope baseline 및 canonical schema baseline 승인 반영
2. workflow/state, ERD, interface draft 작성
3. prototype backlog와 acceptance 확정
4. Build Start Gate 점검
5. Product Owner의 명시적 개발 시작 승인
6. 승인 이후에만 Foundation 착수

---

## 9. Explicit Hold Rule

이 문서 기준으로 아래 작업은 **보류**합니다.

- 실제 애플리케이션 코드 작성
- parser/crawler/DB/API 구현
- public/admin UI 구현
- BX-PF connector 구현
- 외부 API 구현

위 항목은 모두 **설계 완료 + Gate A 통과 + Product Owner 명시 승인 후** 시작합니다.
