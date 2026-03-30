# FPDS Project Execution Plan

Version: 1.0  
Date: 2026-03-28  
Basis: `FPDS_Requirements_Definition_v1_5.md`

---

## 1. Purpose

본 문서는 요구사항 정의서 리뷰 완료 이후, FPDS 프로젝트를 성공적으로 진행하기 위한 **실행 계획(Execution Plan)** 이다.

이 계획의 목적은 다음과 같다.

1. 요구사항 정의서를 실제 개발/운영 계획으로 전환한다.
2. Prototype → Phase 1 → Phase 2의 우선순위와 게이트를 명확히 한다.
3. 설계/개발/운영/보안/연계 항목의 책임과 순서를 분명히 한다.
4. Scope creep를 방지하고, 각 단계의 acceptance를 만족하는 데 집중한다.

---

## 2. Project Goal

FPDS 프로젝트의 핵심 목표는 아래와 같다.

- **Prototype**: 단일 은행/단일 상품유형 기준으로 end-to-end 기술 검증
- **Phase 1**: 캐나다 Big 5 수신상품 데이터 인프라 + 공개 Dashboard + 내부 Admin Console 구축
- **Phase 2**: 일본 Big 5 수신상품 확장 + 외부 SaaS/Open API 제공

즉, 본 프로젝트는 추천 서비스가 아니라 **검증 가능한 금융상품 데이터를 생산·운영·제공하는 플랫폼**을 만드는 것이다.

---

## 3. Success Criteria

프로젝트 성공은 아래 조건이 충족될 때로 정의한다.

### 3.1 Prototype Success
- TD Savings 대상 source 수집 성공
- evidence 저장 성공
- candidate 생성 성공
- 내부 결과 화면에서 확인 가능
- 최소 1회 end-to-end 성공 run 확보

### 3.2 Phase 1 Success
- 캐나다 Big 5 + 3개 상품군(Chequing / Savings / GIC) coverage 완료
- 공개 Product Grid 제공
- 공개 Insight Dashboard 제공
- Admin review queue / evidence trace / run status / change history 동작
- EN / KO / JA UI 동작
- BX-PF connector 구현
- LLM usage / cost monitoring 동작
- 운영 문서 및 환경 세팅 문서 완료

### 3.3 Operational Success
- 보안 기본 통제 적용
- 장애/오류 추적 가능
- review / publish / usage 이력 감사 가능
- 필수 open item이 설계 단계에서 닫힘
- 변경요청은 정식 change control 없이 범위에 추가되지 않음

---

## 4. Guiding Principles

1. **Evidence First**: 모든 구조화 결과는 source evidence와 연결 가능해야 한다.
2. **Prototype First**: 먼저 한 개 은행/한 개 상품유형에서 성공시킨 뒤 확장한다.
3. **Canonical Before Dashboard Polish**: 데이터 품질과 운영 흐름을 UI 장식보다 우선한다.
4. **Human Review by Design**: 애매한 결과는 자동 확정하지 않는다.
5. **Security by Default**: 인증/권한/검증/감사/비밀관리/보안헤더는 후순위가 아니다.
6. **Scope Discipline**: 추천, 사용자 개인화, 고급 시장 분석은 현재 범위에 넣지 않는다.

---

## 5. Recommended Delivery Model

프로젝트는 아래 5개 workstream으로 병행 진행한다.

### WS1. Product / PM
- 요구사항 기준선 관리
- scope / priority 결정
- acceptance 기준 관리
- decision log 및 open item closure 주관

### WS2. Architecture / Backend / Data
- canonical schema
- evidence / candidate / review / publish data model
- internal orchestration interface
- BX-PF connector 설계
- caching / indexing / retrieval strategy

### WS3. Crawling / Parsing / AI Pipeline
- source discovery
- snapshot / parsing / chunking
- extraction / normalization / validation
- confidence 기준 및 review routing
- LLM usage tracking

### WS4. Frontend / Admin / Dashboard
- Public dashboard
- Product grid
- Admin console
- review queue / trace viewer / run dashboard
- multilingual UI

### WS5. DevOps / Security / QA
- environments / secrets / CI/CD
- auth / RBAC / session / CORS / CSP / SSRF controls
- error tracking / monitoring / audit log
- test strategy / release readiness / operational docs

---

## 6. Roles and Ownership

> 실제 인력명은 추후 확정하되, 최소 아래 역할은 반드시 필요하다.

| Role | Primary Responsibility |
|---|---|
| Product Owner | scope, priority, acceptance, decision approval |
| Project Manager / Delivery Lead | 일정/리스크/의사결정 추적 |
| Tech Lead / Architect | 전체 기술 방향, 인터페이스, 설계 일관성 |
| Backend Engineer | API, DB, review/publish workflow |
| AI/Data Engineer | parsing, extraction, normalization, confidence routing |
| Frontend Engineer | public/admin UI, i18n, dashboard |
| DevOps/SRE | environments, deployment, secrets, monitoring, security baseline |
| QA / Reviewer | acceptance verification, regression, review workflow validation |
| Domain Reviewer | 상품 해석/정합성 검토, field mapping 확인 |

---

## 7. Governance Model

### 7.1 Meetings
- **주 1회 Steering / PO Sync**: 우선순위, 결정사항, 리스크
- **주 2회 Delivery Sync**: 진행상황, blocker, 다음 작업
- **주 1회 Design Review**: schema, API, security, BX-PF, dashboard
- **매 Sprint 종료 시 Demo + Acceptance Check**

### 7.2 Project Controls
- Decision Log 유지
- RAID Log(Risks, Assumptions, Issues, Dependencies) 유지
- Scope Change Request 절차 운영
- 각 단계 종료 시 Exit Gate 적용

### 7.3 Working Rules
- 요구사항 정의서가 기준 문서이다.
- open item이 닫히지 않은 상태에서는 해당 구현을 고정하지 않는다.
- dashboard 지표는 데이터 정의서 없이 먼저 만들지 않는다.
- UX 개선은 canonical data와 review flow 안정화 이후 진행한다.

---

## 8. Project Phases

## Phase 0. Mobilization & Detailed Design Closure

### Objective
개발 착수 전, 구현에 필요한 상세설계와 미결정 항목을 닫는다.

### Key Outputs
- 상세 아키텍처 다이어그램
- ERD / canonical schema 초안 확정
- API contract draft
- review state machine
- BX-PF interface contract draft
- security architecture note
- environment strategy(dev/stg/prod)
- sprint backlog for Prototype

### Must-Close Decisions
- exact BX-PF write contract and field mapping
- country-specific deposit subtype taxonomy
- confidence threshold
- field-level validation rules
- admin auth 전략(session cookie vs token)
- RBAC role matrix
- CORS allowlist policy
- crawler safe fetch / SSRF policy
- dashboard KPI formula
- scatter plot axis
- vector indexing starting point
- localization ownership

### Exit Criteria
- open items 중 Prototype/Phase 1 착수에 필요한 항목이 문서화됨
- 팀이 같은 데이터 모델/상태 모델/권한 모델을 보고 작업 가능
- Prototype backlog 확정

---

## Phase 1. Foundation Setup

### Objective
개발 기반을 먼저 안정화한다.

### Scope
- repository structure
- environment setup
- DB provisioning
- storage provisioning
- auth scaffold
- i18n scaffold (EN/KO/JA)
- monitoring / error tracking
- baseline security controls
- README / runbook skeleton

### Deliverables
- running dev environment
- CI/CD 기본 파이프라인
- DB migration 체계
- secrets management 적용
- Sentry(or equivalent) 연결
- base layout/public/admin route skeleton

### Exit Criteria
- 신규 개발자가 로컬 및 개발환경 실행 가능
- 필수 보안 baseline 적용 확인
- 장애/오류 로그 수집 가능

---

## Phase 2. Prototype Build (TD Savings)

### Objective
단일 은행·단일 상품유형으로 end-to-end 기술 가능성을 검증한다.

### Scope
- TD Savings source discovery
- snapshot/html/pdf capture
- parsing / chunking
- candidate generation
- canonical mapping
- basic validation / confidence
- minimal internal result viewer

### Deliverables
- source inventory
- prototype pipeline runbook
- first successful run result
- sample evidence linkage
- prototype demo
- prototype findings memo

### Exit Criteria
- 최소 1회 성공 run
- operator가 결과를 확인할 수 있음
- 주요 실패 원인과 보완점이 문서화됨
- Phase 1 확장 가능 여부 판단 가능

---

## Phase 3. Admin & Ops Core

### Objective
데이터를 “볼 수 있는 것”에서 끝내지 않고, 운영 가능한 형태로 만든다.

### Scope
- review queue
- evidence trace viewer
- run status
- change history
- llm usage tracking
- audit log skeleton
- review decision persistence

### Deliverables
- admin login
- review task workflow
- trace 화면
- run detail 화면
- change history 화면
- usage dashboard v1

### Exit Criteria
- operator가 candidate를 검토/승인/반려 가능
- trace 기반으로 근거 확인 가능
- usage, run, history 확인 가능

---

## Phase 4. Canada Big 5 Expansion

### Objective
Prototype을 실제 Phase 1 범위로 확장한다.

### Scope
- Big 5 source inventory completion
- Chequing / Savings / GIC coverage
- canonical subtype field mapping
- dashboard summary/ranking/scatter
- public product grid
- EN/KO/JA locale rendering
- cache / refresh strategy v1

### Deliverables
- Big 5 source registry
- per-bank / per-product parser rules
- public products API
- public dashboard APIs
- public dashboard UI
- trilingual rendering

### Exit Criteria
- Big 5 + 3개 상품군 coverage
- Product Grid 동작
- 의미 있는 ranking widget 최소 2개 + scatter plot 1개 제공
- 운영팀이 데이터와 화면을 함께 검토 가능

---

## Phase 5. BX-PF Publish Readiness & Hardening

### Objective
운영·연계·문서화까지 포함하여 Phase 1 납품/런칭 준비를 마친다.

### Scope
- BX-PF connector hardening
- publish pending / retry / reconciliation flow
- operational docs
- security hardening
- acceptance test
- launch checklist

### Deliverables
- BX-PF publish workflow
- reconciliation dashboard/status
- admin manual
- release notes
- acceptance evidence pack

### Exit Criteria
- BX-PF connector 구현 완료
- BX-PF 미연계 시에도 publish status 추적 가능
- 운영 문서/설치 문서 완료
- Phase 1 acceptance 충족

---

## Phase 6. Japan & External API (Phase 2)

### Objective
일본 Big 5와 외부 API 제공으로 확장한다.

### Scope
- Japan source inventory
- Japanese parsing/normalization
- locale-aware taxonomy mapping
- API auth / tenant scope / rate limit
- product search/detail/change API
- API docs (EN/JA, 가능 시 KO)

### Exit Criteria
- 일본어 source 처리 가능
- 외부 API auth / rate limit / audit separation 동작
- API 문서 제공 완료

---

## 9. Milestones

| Milestone | Description |
|---|---|
| M1 | 요구사항 리뷰 종료 및 실행계획 승인 |
| M2 | 상세설계 / open item closure 완료 |
| M3 | Foundation 완료 |
| M4 | Prototype end-to-end 성공 |
| M5 | Admin/Ops Core 완료 |
| M6 | Canada Big 5 public dashboard 완료 |
| M7 | BX-PF publish readiness 완료 |
| M8 | Phase 1 acceptance sign-off |
| M9 | Japan expansion 설계 및 source inventory 완료 |
| M10 | Phase 2 API acceptance sign-off |

---

## 10. Dependency Plan

### External Dependencies
- BX-PF interface / access / environment readiness
- source websites and PDF availability
- domain review availability
- 일본어 source 검수 인력 확보(Phase 2)

### Internal Dependencies
- architecture decisions
- auth / RBAC design
- dashboard KPI definition
- localization workflow ownership
- API policy and tenant strategy

### Dependency Rule
외부 의존성으로 인해 막히는 항목은 인터페이스 우선(interface-first) 방식으로 진행하고, 실제 연동은 conditional acceptance로 처리한다.

---

## 11. Risk Management Plan

| Risk | Why It Matters | Action |
|---|---|---|
| Source variability | 은행별 구조 차이 | source inventory + parser abstraction + review fallback |
| PDF parsing instability | PDF마다 구조가 다름 | snapshot 원본 저장 + parsed text 보존 + manual review fallback |
| BX-PF dependency | 외부 연계 미정 | interface-first + mock/stub + reconciliation model |
| Scope creep | dashboard/추천 확대 유혹 | scope board + formal change control |
| Cost drift | LLM/API/infra 비용 증가 | budget cap + usage dashboard + weekly cost review |
| Security gaps | admin/API/crawler 모두 노출면 존재 | security checklist + design review + pre-release hardening |
| Data quality inconsistency | confidence와 validation 기준 모호 | field-level rules + review playbook + sampling QA |

---

## 12. Quality Strategy

### 12.1 Test Layers
- schema validation test
- parser unit test
- normalization rule test
- API integration test
- UI smoke test
- security verification checklist
- acceptance scenario test

### 12.2 Data Quality Checks
- required field completeness
- evidence linkage availability
- suspicious value detection
- rate/fee/minimum balance sanity rules
- per-bank comparison sampling

### 12.3 Acceptance Review
각 milestone 종료 시 아래를 확인한다.
- 기능 동작 여부
- traceability
- 운영자 사용 가능성
- security baseline
- documentation completeness

---

## 13. Documentation Plan

프로젝트 중 반드시 유지할 문서는 아래와 같다.

- requirements definition (baseline)
- execution plan (본 문서)
- architecture decision record (ADR)
- decision log
- ERD / schema spec
- API spec
- security design note
- review playbook
- operations runbook
- release checklist
- acceptance evidence pack

---

## 14. Immediate Next Steps (Next 10 Business Days)

### Day 1-2
- 프로젝트 kickoff
- 요구사항 기준선 freeze
- decision log / RAID log 생성
- open item owner 지정

### Day 3-4
- architecture workshop
- ERD / state model / API draft 정리
- auth / RBAC / session 전략 결정
- crawler SSRF / egress 정책 결정

### Day 5-6
- dashboard KPI / scatter plot axis 결정
- subtype taxonomy 확정
- BX-PF field mapping 초안 작성
- vector/search starting point 결정

### Day 7-8
- environment / repo / branching / CI/CD setup
- DB / storage / secrets / monitoring setup
- i18n / public/admin skeleton 생성

### Day 9-10
- TD Savings source inventory 작성
- prototype backlog 확정
- first parser / snapshot spike 시작
- Sprint 1 plan 승인

---

## 15. Suggested Sprint Structure

### Sprint 0
- 상세설계, open item closure, foundation 준비

### Sprint 1
- prototype pipeline skeleton
- TD source capture / parsing

### Sprint 2
- candidate generation / internal viewer
- prototype acceptance

### Sprint 3
- admin auth / review queue / trace viewer

### Sprint 4
- run status / change history / llm usage tracking

### Sprint 5-6
- Big 5 / 3개 상품군 확장
- public grid / dashboard

### Sprint 7
- BX-PF connector / reconciliation / docs / UAT

> 실제 sprint 길이와 개수는 팀 규모와 병렬 개발 가능 인력에 따라 조정한다.

---

## 16. Stage Gates

### Gate A: Build Start Gate
- detailed design 완료
- Prototype backlog 확정
- 환경 준비 완료

### Gate B: Prototype Gate
- end-to-end 1회 성공
- 주요 기술 리스크 확인 및 대응계획 정리

### Gate C: Phase 1 Expansion Gate
- review / trace / run / usage core 준비 완료
- canonical schema 안정화

### Gate D: Release Gate
- acceptance criteria 충족
- 보안/운영/문서 준비 완료
- open critical issue = 0

---

## 17. What Must Not Happen

아래 상황은 프로젝트 실패 가능성을 크게 높인다.

- Prototype 성공 전에 Big 5 전체 확장부터 시도하는 것
- dashboard 시각화에 집중하고 canonical schema를 뒤로 미루는 것
- BX-PF 연계를 구현 후반까지 방치하는 것
- security를 출시 직전에만 다루는 것
- open item 미결 상태에서 개발자가 각자 다르게 구현하는 것
- 추천/개인화/고급 insight를 현재 범위에 슬그머니 포함하는 것

---

## 18. Final Recommendation

지금 시점에서 가장 먼저 해야 할 일은 **코딩 시작 자체가 아니라, 1) open item closure, 2) 상세설계 확정, 3) Prototype backlog 확정** 이다.

즉, 다음 순서는 아래와 같다.

1. 상세설계 워크숍 수행 (2 days)
2. open item owner와 due date 확정 (1 day)
3. Sprint 0 실행 (10 days)
4. Foundation 완료 (5 days)
5. TD Savings Prototype 성공 (10 days)
6. Admin/Ops Core 구축 (10 days)
7. Big 5 확장 및 Public Dashboard 완성 (10 days)
8. BX-PF publish readiness 및 acceptance sign-off (5 days)

이 순서를 지키면 현재 요구사항 정의서와 가장 정합적인 방식으로 프로젝트를 진행할 수 있다.

