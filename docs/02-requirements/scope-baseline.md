  # FPDS Scope Baseline and Build Start Approval

Version: 1.0  
Date: 2026-03-30  
Status: Approved Baseline for WBS 1.1.1 - 1.1.5  
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/stage-gate-checklist.md`
- `docs/00-governance/working-agreement.md`

---

## 1. Purpose

이 문서는 FPDS의 범위 경계, 비범위 항목, Phase 1 release cutline, 개발 시작 승인 방식을 한 장으로 고정하기 위한 기준 문서다.

목적:
- Prototype과 Phase 1의 공식 범위를 다시 해석하지 않도록 한다.
- PRD의 non-goals를 구현 직전 기준선으로 재확인한다.
- `Must Have / Later` 구분을 통해 Phase 1 release cutline을 명확히 한다.
- Gate A 통과 이후 실제 개발 시작이 가능한 조건을 문서 기준으로 정의한다.

이 문서는 WBS `1.1.1`부터 `1.1.5`까지의 공식 산출물이다.

---

## 2. Baseline Decisions

본 문서는 아래 Product Owner 결정을 반영한다.

1. `1.1.3` 비범위 항목은 PRD의 전체 `Non-Goals` 목록을 공식 exclusion list로 사용한다.
2. `1.1.4` release cutline은 `Phase 1 release 기준 Must Have / Later`로 정의한다.
3. `1.1.5` 개발 시작 승인 방식은 `Gate A = Pass + Product Owner explicit approval`로 정의한다.

본 문서가 범위를 새로 확장하지는 않는다. 상위 문서의 내용을 현재 단계 실행 기준으로 고정하는 역할을 한다.

---

## 3. Prototype Scope Fixed

### 3.1 Official Prototype Boundary

Prototype 범위는 아래로 고정한다.

- 대상 은행: `TD Bank`
- 대상 상품군: `Savings Accounts`
- source 유형: 공개 웹페이지 또는 PDF
- 처리 범위: source discovery, snapshot 저장, parsing/chunking, extraction, normalization, validation의 기본 흐름
- 저장 범위: FPDS 내부 임시 저장소에 evidence와 canonical candidate 저장
- 확인 범위: read-only 성격의 `basic internal result viewer`에서 결과 확인 가능
- 성공 기준: 최소 1회 end-to-end 성공 run 확보

### 3.2 What Prototype Must Not Expand Into

Prototype 단계에서 아래 항목은 포함하지 않는다.

- Canada Big 5 전체 확장
- Chequing 또는 GIC 확장
- full admin console
- full review queue 운영화
- BX-PF actual publish flow
- public dashboard/public product grid 구현
- external API

### 3.3 Minimum Meaning of Basic Internal Result Viewer

Prototype의 `basic internal result viewer`는 아래 수준으로 정의한다.

- run 결과를 내부에서 읽기 전용으로 확인할 수 있다.
- 최소한 bank, product name, product type, 핵심 필드 일부, run 기준 결과 상태를 볼 수 있다.
- evidence-linked 결과를 사람이 검토할 수 있는 최소 수준의 확인 화면이면 충분하다.

아래 항목은 prototype viewer의 필수 범위가 아니다.

- admin login
- review queue 목록/처리
- change history 운영 화면
- BX-PF publish monitor
- usage dashboard

---

## 4. Phase 1 v1 Scope Fixed

### 4.1 Official Phase 1 Boundary

Phase 1 v1 범위는 아래로 고정한다.

- 대상 국가/기관: `Canada Big 5`
  - RBC
  - TD
  - BMO
  - Scotiabank
  - CIBC
- 대상 상품군:
  - Chequing
  - Savings
  - GIC / Term Deposits
- 사용자 표면:
  - Public Product Grid
  - Public Insight Dashboard
  - Admin Console

### 4.2 Supporting Capabilities Included in Phase 1 v1

Phase 1 v1은 단순 화면 범위만이 아니라 아래 운영 가능 범위를 함께 포함한다.

- evidence store
- parsing / chunking / change detection
- review queue
- evidence trace viewer
- run status / change history
- BX-PF connector interface 및 write-back readiness
- BX-PF 미연계 시 pending / retry / reconciliation 상태 추적
- LLM usage / token / cost tracking
- English / Korean / Japanese UI
- auth / RBAC / session / CORS / CSRF / CSP / SSRF를 포함한 security baseline

### 4.3 Phase 1 Boundary Clarification

Phase 1 v1 범위는 `Canada Big 5 + 3개 상품군 + Public/Admin`이라는 상위 경계를 기준으로 하되, 실제 release 가능한 제품으로 보기 위해 필요한 운영/보안/추적 기능까지 포함한 범위로 해석한다.

즉, 이 문서에서의 Phase 1 v1은 단순한 UX shell 범위가 아니라 PRD Phase 1 acceptance에 직접 연결되는 실행 범위다.

---

## 5. Official Non-Goals

FPDS의 현재 공식 비범위 항목은 PRD의 전체 `Non-Goals`를 그대로 따른다.

- 사용자 맞춤 추천
- eligibility / fit matching
- 금융기관 대상 market insight portal
- product map / market analysis / insight mart
- 계좌 개설 대행
- 오픈뱅킹 사용자 서비스
- 일본 전체 금융기관 확대
- 일본의 여신/카드 상품 확대
- 공개 사용자용 evidence trace 노출
- 결제/구독 기능

### 5.1 Interpretation Rule

위 항목은 구현 중 자동으로 다시 열지 않는다.

- 상세화가 필요한 경우: clarification으로 처리
- 범위를 실제로 늘리는 경우: scope change request로 처리
- Phase 2 기능을 Phase 1에 당기는 경우: 기본값은 `Later` 유지

---

## 6. Phase 1 Release Cutline

이 문서의 release cutline은 `Phase 1 release 기준 Must Have / Later`다.  
Phase 2는 계약 범위에 포함되지만, Phase 1 release cutline에서는 `Later`로 분리한다.

### 6.1 Must Have for Phase 1 Release

- Canada Big 5 deposit coverage
- Chequing / Savings / GIC support
- Public Product Grid
- Public Insight Dashboard
- review queue
- evidence trace viewer
- run status
- change history
- admin authentication and authorization baseline
- trilingual Public/Admin UI
- BX-PF connector interface and publish readiness
- publish pending / retry / reconciliation tracking
- LLM usage monitoring
- monitoring / error tracking baseline
- security baseline and release hardening checklist coverage
- Phase 1 acceptance evidence and operating documentation

### 6.2 Later Than Phase 1 Release

- Japan Big 5 deposit expansion
- Japanese source parsing and locale-specific taxonomy extension
- external SaaS/Open API
- external API auth / tenant isolation / rate limit / SLA
- multilingual external API docs
- personalized recommendation
- market insight portal / product map / advanced analytics
- public evidence exposure
- billing / subscription
- Japan full-market expansion
- loan / card expansion

### 6.3 Cutline Rule

`Must Have`에서 `Later`로 이동하거나, `Later`를 `Must Have`로 당기는 변경은 모두 scope change control 대상이다.

---

## 7. Build Start Approval Model

### 7.1 Approval Rule

개발 시작은 아래 두 조건이 모두 충족될 때만 가능하다.

1. `Gate A = Pass`
2. `Product Owner explicit approval`

둘 중 하나라도 빠지면 개발을 시작할 수 없다.

### 7.2 Meaning of `Gate A = Pass`

`Gate A = Pass`의 의미는 아래와 같다.

- Gate A checklist에서 설계/준비 상태를 직접 막는 항목이 모두 닫혀 있다.
- WBS `0.x`, `1.x` 중 Gate A 차단 항목이 `Completed` 또는 동등한 승인 상태다.
- scope, taxonomy/schema, workflow/state, architecture/storage, API/interface, security/access, UX/localization, prototype package가 구현 가능한 수준으로 문서화되어 있다.
- open item이 남아 있더라도 Gate A 목적을 직접 막지 않는 항목만 허용된다.

### 7.3 Build Start Sign-off Package

Product Owner가 Gate A와 개발 시작 여부를 판단하기 전에 최소 아래 문서 패키지를 기준으로 검토한다.

- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/raid-log.md`
- `docs/00-governance/working-agreement.md`
- `docs/00-governance/stage-gate-checklist.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/domain-model-canonical-schema.md`
- Gate A를 막는 상세 설계 문서 패키지

### 7.4 Approval Recording Rule

Gate A 결과와 실제 개발 시작 승인은 아래 방식으로 남긴다.

- Gate A review note 작성
- `docs/00-governance/decision-log.md`에 Gate A 결과 및 개발 시작 승인 결정을 기록
- `docs/01-planning/WBS.md`와 `docs/00-governance/roadmap.md` 상태 갱신

Gate A `Pass` 자체는 개발 시작 승인이 아니다.  
이 문서는 gate와 start approval의 기록 방식을 함께 정의한다.

---

## 8. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.1.1 | Section 3 Prototype Scope Fixed |
| 1.1.2 | Section 4 Phase 1 v1 Scope Fixed |
| 1.1.3 | Section 5 Official Non-Goals |
| 1.1.4 | Section 6 Phase 1 Release Cutline |
| 1.1.5 | Section 7 Build Start Approval Model |

---

## 9. Change History

| Date | Change |
|---|---|
| 2026-03-30 | Initial scope baseline created for WBS 1.1.1 - 1.1.5 |
| 2026-04-06 | Clarified that Gate A Pass and actual implementation start approval are separate controls |
