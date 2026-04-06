# FPDS RAID Log

Version: 1.0  
Date: 2026-03-29  
Status: Active  
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 FPDS 프로젝트의 `R`isk, `A`ssumption, `I`ssue, `D`ependency를 한 곳에서 관리하기 위한 기준 문서입니다.

목적:
- 주요 리스크를 늦지 않게 발견하고 대응한다.
- 아직 검증되지 않은 가정을 명시적으로 관리한다.
- 진행을 막는 이슈를 빠르게 드러낸다.
- 외부/내부 의존성을 추적해 일정 착시를 줄인다.

---

## 2. Status Rules

### 2.1 Priority

- `High`: 일정, 범위, 품질, 보안에 직접 영향
- `Medium`: 조기 대응이 필요하지만 즉시 차단 수준은 아님
- `Low`: 추적은 필요하지만 현재 진행을 막지는 않음

### 2.2 State

- `Open`: 아직 해결/검증되지 않음
- `Monitoring`: 주기적으로 추적 중
- `Mitigated`: 대응책이 마련되어 영향이 줄어듦
- `Closed`: 더 이상 추적이 필요하지 않음

---

## 3. Risks

| ID | Priority | State | Risk | Impact | Mitigation / Next Action | Owner | Source |
|---|---|---|---|---|---|---|---|
| R-001 | High | Open | Source 구조가 은행별/국가별로 달라 parsing 품질 편차가 클 수 있다. | extraction, normalization, 일정 지연 | source inventory와 parser abstraction을 먼저 두고 review fallback 유지 | Tech Lead, AI/Data | PRD 20 / Plan 11 |
| R-002 | High | Open | PDF parsing 품질이 불안정해 핵심 필드 추출 정확도가 흔들릴 수 있다. | prototype 성공 가능성, 데이터 품질 | snapshot 원본 보존, parsed text 저장, manual review fallback 유지 | AI/Data | PRD 20 / Plan 11 |
| R-003 | High | Open | BX-PF 연동 계약/환경이 늦어지면 Phase 1 acceptance가 흔들릴 수 있다. | publish workflow, acceptance, 일정 | interface-first 설계, mock/stub, reconciliation metadata 준비 | Backend, Tech Lead | PRD 20, 22 / Plan 10, 11 |
| R-004 | High | Closed | open item 미해결 상태에서 구현을 시작하면 재작업이 커질 수 있다. | 일정 지연, 설계 충돌 | Gate A Pass 승인으로 상세 설계 패키지, 승인 기록, next-stage readiness가 모두 고정되었다. 실제 구현 시작은 별도 start approval로 통제되므로 조기 구현 리스크는 gate governance로 닫혔다. | Product Owner, Tech Lead | Plan 16, 18 / WBS 8, 9 / `docs/00-governance/gate-a-build-start-review-note.md` |
| R-005 | High | Mitigated | 보안 정책을 뒤로 미루면 auth, API, crawler 경계에서 구조적 결함이 생길 수 있다. | 보안 취약점, 재설계 비용 | `docs/03-design/security-access-control-design.md`에서 auth/RBAC/CORS/CSRF/CSP/SSRF/secrets baseline을 고정했다. | Security, Tech Lead | PRD 14.3 / Plan 4, 11 / `docs/03-design/security-access-control-design.md` |
| R-006 | Medium | Monitoring | 캐나다와 일본 상품 taxonomy 차이로 canonical schema 확장 시 충돌이 생길 수 있다. | Phase 2 확장성 저하 | core canonical + locale subtype mapping 전략 유지 | Domain Reviewer, Tech Lead | PRD 20, 22 |
| R-007 | Medium | Closed | dashboard metric 정의 없이 UI 설계를 앞서가면 의미 없는 비교 화면이 나올 수 있다. | 사용자 가치 저하, 재작업 | `docs/03-design/insight-dashboard-metric-definition.md`에서 KPI, ranking, scatter preset baseline과 30일 recent-change window를 확정했다. | Product Owner, Frontend, Backend | PRD 6, 22 / `docs/03-design/insight-dashboard-metric-definition.md` |
| R-008 | Medium | Monitoring | LLM/API/infra 비용이 초기 예상보다 빠르게 증가할 수 있다. | 운영 비용 증가 | usage dashboard, weekly cost review, stage별 cap 운영 | Product Owner, Backend | PRD 20 / Plan 11 |
| R-009 | Medium | Closed | 다국어 운영 ownership이 불명확하면 EN/KO/JA 품질이 일관되지 않을 수 있다. | public/admin UX 품질 저하 | `docs/03-design/localization-governance-and-fallback-policy.md`에서 ownership, reference locale, fallback, glossary governance를 고정했다. | Product Owner, Frontend | PRD 14.6, 22 / `docs/03-design/localization-governance-and-fallback-policy.md` |
| R-010 | Medium | Mitigated | Prototype 전에 Big 5 전체 커버리지로 범위가 커지면 일정과 품질이 동시에 흔들릴 수 있다. | scope creep, 일정 지연 | `docs/02-requirements/scope-baseline.md` 기준으로 Prototype/Phase 1 경계를 고정하고 change control로 관리 | Product Owner | PRD 21 / Plan 4, 17, 18 / `docs/02-requirements/scope-baseline.md` |
| R-011 | High | Open | Phase 1까지 2인 체제로 운영되므로 설계, 구현, QA, 문서화 병렬 처리 폭이 제한되어 일정 압박이 커질 수 있다. | Phase 1 일정 지연, multitasking overload, 품질 저하 위험 | 단계별 scope 고정, gate discipline 유지, 문서 선행, 병목 조기 식별 | Product Owner, Tech Lead | `docs/00-governance/roadmap.md` |

---

## 4. Assumptions

| ID | Priority | State | Assumption | Validation Needed | Owner | Source |
|---|---|---|---|---|---|---|
| A-001 | High | Monitoring | TD Savings는 Prototype용 source로 충분한 구조와 증빙을 제공한다. | `docs/01-planning/td-savings-source-inventory.md`에서 public HTML/PDF source set은 확인되었고, parser feasibility는 spike로 계속 검증한다. | AI/Data | PRD 4.1, 18.1 / Plan 8, 14 / `docs/01-planning/td-savings-source-inventory.md` |
| A-002 | High | Open | Canada Big 5 deposit products는 현재 범위에서 현실적인 Phase 1 커버리지다. | source availability와 parsing 난이도 확인 | Product Owner, AI/Data | PRD 4.1, 18.2 |
| A-003 | Medium | Open | Next.js + Postgres + Supabase Auth + S3 계열 구성이 Phase 1 속도와 운영성에 적합하다. | architecture workshop에서 재확인 | Tech Lead | PRD 15.2 |
| A-004 | Medium | Closed | pgvector를 초기 retrieval starting point로 써도 Phase 1 요구 수준에는 충분하다. | `docs/03-design/retrieval-vector-starting-point.md`에서 Phase 1 baseline으로 확정되었다. | Tech Lead, AI/Data | PRD 15.2, 22 / `docs/03-design/retrieval-vector-starting-point.md` |
| A-005 | High | Open | BX-PF는 approved normalized product master의 target store 역할을 계속 유지한다. | BX-PF 계약/환경 확인 | Product Owner, Tech Lead | PRD 6, 16.1 |
| A-006 | Medium | Monitoring | Public/Admin UI의 EN/KO/JA 3개 언어 운영이 현재 팀 체계로 감당 가능하다. | localization ownership은 확정되었지만 실제 구현/운영 부하는 아직 검증 전이다. | Product Owner | PRD 1, 6, 14.6 / `docs/03-design/localization-governance-and-fallback-policy.md` |
| A-007 | Medium | Monitoring | Product Grid와 Insight Dashboard는 동일 filter scope를 공유해도 UX 복잡도가 관리 가능하다. | metric vocabulary baseline은 닫혔지만 exact click/state choreography는 `5.11`에서 추가 검증이 필요하다. | Frontend, Product Owner | PRD FR-PUB-012 / `docs/03-design/product-grid-information-architecture.md`, `docs/03-design/insight-dashboard-metric-definition.md` |
| A-008 | Medium | Open | Phase 2 시작 시점에 추가 인력 1명이 실제로 투입 가능하다. | staffing plan 확정 및 onboarding timing 확인 필요 | Product Owner | `docs/00-governance/roadmap.md` |

---

## 5. Issues

| ID | Priority | State | Issue | Current Impact | Next Action | Owner | Source |
|---|---|---|---|---|---|---|---|
| I-001 | High | Closed | exact BX-PF write contract and field mapping이 아직 미확정이다. | `docs/03-design/api-interface-contracts.md` Section 7에서 adapter-facing contract 초안이 확정되었다. | Backend, Tech Lead | PRD 22 / `docs/03-design/api-interface-contracts.md` |
| I-002 | High | Closed | country-specific deposit subtype taxonomy가 아직 미확정이다. | schema/parser/dashboard 기준 불안정 | `docs/03-design/domain-model-canonical-schema.md` Section 3에서 Canada deposit taxonomy와 extensible registry rule을 고정했다. | Domain Reviewer, Tech Lead | `docs/03-design/domain-model-canonical-schema.md` / WBS 1.2.1 |
| I-003 | High | Closed | confidence threshold와 field-level validation rules가 아직 미확정이다. | review queue 기준 불명확 | `docs/03-design/domain-model-canonical-schema.md` Sections 5-6에서 validation matrix와 config-backed confidence policy를 고정했다. | Backend, AI/Data | `docs/03-design/domain-model-canonical-schema.md` / WBS 1.2.4, 1.2.5 |
| I-004 | High | Closed | admin auth 방식(session vs token)이 아직 미확정이다. | auth/RBAC/CSRF 설계 지연 | `docs/03-design/security-access-control-design.md`에서 session cookie baseline을 고정했다. | Product Owner, Security | PRD 22 / `docs/03-design/security-access-control-design.md` |
| I-005 | High | Closed | RBAC role matrix와 승인 권한 범위가 아직 미확정이다. | admin workflow 설계 지연 | `docs/03-design/security-access-control-design.md`에서 human 3-role matrix를 고정했다. | Security, Tech Lead | PRD 22 / `docs/03-design/security-access-control-design.md` |
| I-006 | Medium | Closed | CORS allowlist와 crawler SSRF/egress 정책이 아직 미확정이다. | security architecture note 미완성 | `docs/03-design/security-access-control-design.md`에서 browser origin policy와 bank-scoped safe fetch baseline을 고정했다. | Security | PRD 22 / `docs/03-design/security-access-control-design.md` |
| I-007 | Medium | Closed | dashboard KPI formula, ranking 기준, scatter axis가 아직 미확정이다. | public dashboard 정보 구조 고정 불가 | `docs/03-design/insight-dashboard-metric-definition.md`에서 KPI/ranking/scatter preset baseline을 고정했다. | Product Owner, Frontend, Backend | PRD 22 / `docs/03-design/insight-dashboard-metric-definition.md` |
| I-008 | Medium | Closed | localization ownership과 Japanese fallback/glossary ownership이 아직 미확정이다. | EN/KO/JA 운영 정책 미완성 | `docs/03-design/localization-governance-and-fallback-policy.md`에서 ownership, fallback, glossary rule을 고정했다. | Product Owner, Frontend | PRD 22 / `docs/03-design/localization-governance-and-fallback-policy.md` |

---

## 6. Dependencies

| ID | Priority | State | Dependency | Dependency Type | Impacted Work | Next Action | Owner | Source |
|---|---|---|---|---|---|---|---|---|
| D-001 | High | Monitoring | BX-PF interface / access / environment readiness | External | Phase 1 publish readiness, acceptance | interface-first로 설계하고 mock/stub 준비 | Product Owner, Backend | Plan 10 |
| D-002 | High | Monitoring | Source websites와 PDF의 안정적 접근 가능성 | External | prototype, Canada expansion, Japan expansion | TD Savings inventory baseline은 고정되었고, spike에서 fetch/parse 안정성을 계속 점검한다. | AI/Data | Plan 10 / PRD 4.1 / `docs/01-planning/td-savings-source-inventory.md` |
| D-003 | Medium | Open | Domain reviewer의 taxonomy 및 field mapping 검토 가능 여부 | External/Internal | schema, validation, subtype 정의 | review cadence와 owner 지정 필요 | Product Owner | Plan 10 |
| D-004 | High | Closed | Architecture decisions의 선행 확정 | Internal | ERD, API, security, backlog | Gate A review 기준으로 상세 설계 패키지와 prototype planning package가 구현 가능한 수준으로 고정되었다. | Tech Lead | Plan 10, 18 / `docs/00-governance/gate-a-build-start-review-note.md` |
| D-005 | High | Closed | Auth / RBAC design의 선행 확정 | Internal | admin security, API boundary, session strategy | `docs/03-design/security-access-control-design.md` 기준으로 후속 구현/검증을 진행할 수 있다. | Security, Tech Lead | Plan 10, 14 / `docs/03-design/security-access-control-design.md` |
| D-006 | Medium | Closed | Dashboard KPI definition의 선행 확정 | Internal | public dashboard IA, API, UX | `docs/03-design/insight-dashboard-metric-definition.md` 기준으로 aggregate/API/UI alignment를 진행할 수 있다. | Product Owner, Backend | Plan 10, 14 / `docs/03-design/insight-dashboard-metric-definition.md` |
| D-007 | Medium | Closed | Localization workflow ownership의 선행 확정 | Internal | i18n 운영, QA, public/admin copy | `docs/03-design/localization-governance-and-fallback-policy.md` 기준으로 ownership, review, fallback baseline을 적용할 수 있다. | Product Owner | Plan 10 / PRD 22 / `docs/03-design/localization-governance-and-fallback-policy.md` |
| D-008 | Medium | Open | API policy and tenant strategy의 선행 확정 | Internal | Phase 2 external API | Phase 2 설계에서 정책 확정 | Product Owner, Backend | Plan 10 / PRD 22 |

---

## 7. RAID Review Cadence

- Steering / PO Sync: High priority RAID 항목 검토
- Delivery Sync: Open issue와 dependency 상태 갱신
- Design Review: Risk mitigation과 assumption validation 상태 확인
- Gate Review: Gate A~D 진입 전 High/Open 항목 재확인

---

## 8. Change History

| Date | Change |
|---|---|
| 2026-03-29 | Initial RAID log created from PRD, plan, WBS, and decision log baseline |
| 2026-03-29 | Added staffing-related risk and assumption aligned with roadmap planning |
| 2026-03-30 | Updated scope-creep risk to Mitigated after scope baseline and release cutline approval |
| 2026-03-30 | Closed taxonomy and validation/confidence issues after canonical schema baseline approval |
| 2026-04-05 | Closed auth/RBAC/CORS/SSRF issues and dependency after security baseline approval |
| 2026-04-05 | Closed dashboard KPI/ranking/scatter metric-definition risk, issue, and dependency after Insight Dashboard baseline approval |
| 2026-04-06 | Closed localization ownership/fallback/glossary risk, issue, and dependency after localization governance baseline approval |
| 2026-04-06 | Moved TD Savings prototype-source assumption to Monitoring after source inventory baseline completion |
| 2026-04-06 | Mitigated design-before-build and security-delay risks and closed architecture-decision dependency after Gate A review package completion |
| 2026-04-06 | Closed the design-before-build risk after final Gate A Pass approval |
