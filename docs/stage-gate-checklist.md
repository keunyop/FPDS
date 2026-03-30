# FPDS Stage Gate Checklist

Version: 1.0  
Date: 2026-03-29  
Status: Active  
Source Documents:
- `docs/FPDS_Requirements_Definition_v1_5.md`
- `docs/plan.md`
- `docs/WBS.md`
- `docs/roadmap.md`
- `docs/decision-log.md`
- `docs/raid-log.md`
- `docs/working-agreement.md`

---

## 1. Purpose

이 문서는 FPDS의 Stage Gate 운영 기준과 체크리스트를 정의한다.

목적:
- 단계 전환 시 무엇이 완료되어야 하는지 명확히 한다.
- 설계 미완료 상태에서 구현이 시작되는 일을 막는다.
- acceptance, security, 운영 준비를 release 직전에 몰지 않도록 한다.
- Product Owner가 go/no-go 판단을 문서 기준으로 할 수 있게 한다.

---

## 2. Gate Operating Rules

1. 각 gate는 문서 기준으로 통과 여부를 판단한다.
2. gate를 통과하지 못하면 다음 stage는 시작하지 않는다.
3. `Conditional Pass`는 원칙적으로 허용하지 않는다.
4. High priority open issue가 gate 목적을 직접 막으면 통과할 수 없다.
5. gate 결과는 `Pass`, `Fail`, `Deferred` 중 하나로 남긴다.
6. gate 통과 후 WBS와 roadmap 상태를 즉시 업데이트한다.

---

## 3. Gate Summary

| Gate | Transition | Purpose | Decision Owner |
|---|---|---|---|
| Gate A | Detailed Design -> Foundation/Prototype Build | 개발 시작 가능 상태 확인 | Product Owner |
| Gate B | Prototype -> Admin/Ops Core | end-to-end feasibility 확인 | Product Owner |
| Gate C | Admin/Ops Core -> Canada Expansion | 운영 가능성 기반 확인 | Product Owner |
| Gate D | Phase 1 Build -> Release Readiness | 공개/운영/보안 준비 확인 | Product Owner |

---

## 4. Gate A Checklist

목적:
- 설계 패키지가 구현 가능한 수준으로 닫혔는지 확인한다.

필수 체크:
- Prototype 범위와 acceptance가 확정되어 있다.
- Phase 1 v1 범위와 non-goals가 문서로 고정되어 있다.
- canonical schema v1, taxonomy, validation/confidence 기준이 문서화되어 있다.
- end-to-end workflow와 state model이 정의되어 있다.
- ERD, source snapshot/evidence 전략, retrieval 시작점이 정의되어 있다.
- public/admin/BX-PF interface contract 초안이 존재한다.
- auth, RBAC, CORS, SSRF, session/CSRF/security headers 정책이 정의되어 있다.
- KPI, ranking, scatter axis, i18n ownership/fallback 정책이 정의되어 있다.
- Sprint 0 backlog와 Build Start Gate 점검 항목이 정리되어 있다.
- WBS `0.x`, `1.x`의 gate 차단 항목이 닫혀 있다.
- Product Owner가 개발 시작을 별도로 승인했다.

통과 산출물:
- Gate A review note
- updated WBS status
- updated roadmap status

Fail examples:
- open decision이 여전히 핵심 설계를 막는 경우
- auth/RBAC/security 방향이 미정인 경우
- Prototype acceptance가 합의되지 않은 경우

---

## 5. Gate B Checklist

목적:
- 최소 end-to-end prototype이 실제로 성립하는지 확인한다.

필수 체크:
- TD Savings source capture가 가능하다.
- snapshot, parsing, chunking, extraction, normalization, validation 흐름이 1회 이상 동작한다.
- evidence linkage가 확인 가능하다.
- review routing이 작동한다.
- prototype viewer 또는 동등한 검토 인터페이스가 있다.
- first end-to-end run evidence pack이 남아 있다.
- prototype findings memo가 작성되어 있다.
- Prototype 결과가 Big 5 확장 가치와 리스크를 설명한다.

통과 산출물:
- Prototype demo
- findings memo
- Gate B decision note

Fail examples:
- 핵심 필드 추출이 재현되지 않는 경우
- evidence-to-field trace가 불가능한 경우
- 수동 검토 없이는 결과 품질을 설명할 수 없는 경우

---

## 6. Gate C Checklist

목적:
- 운영 가능한 내부 관리 체계가 준비되었는지 확인한다.

필수 체크:
- admin login 및 권한 분리가 동작한다.
- review queue와 review decision flow가 동작한다.
- evidence trace viewer, run status, change history가 확인 가능하다.
- audit log baseline과 usage tracking이 존재한다.
- 운영 시나리오 QA가 수행되었다.
- Prototype 단계에서 발견된 핵심 리스크의 대응 방향이 정리되었다.

통과 산출물:
- Admin/Ops demo
- QA summary
- Gate C decision note

Fail examples:
- review 승인 흐름은 있으나 trace/audit이 없는 경우
- 운영자가 상태와 이력을 추적할 수 없는 경우
- auth/RBAC가 문서와 다르게 구현된 경우

---

## 7. Gate D Checklist

목적:
- Phase 1 공개와 운영을 시작할 준비가 되었는지 확인한다.

필수 체크:
- Canada Big 5 public catalog와 dashboard가 동작한다.
- KPI/ranking/scatter 산식이 실제 데이터와 정합성을 가진다.
- EN/KO/JA public/admin 경험이 기본 품질을 충족한다.
- BX-PF connector와 publish flow가 준비되어 있다.
- retry/reconciliation, publish monitor가 준비되어 있다.
- security hardening verification이 완료되어 있다.
- runbook, release checklist, acceptance evidence pack이 준비되어 있다.
- critical open issue가 0건이다.

통과 산출물:
- release checklist sign-off
- acceptance evidence pack
- Gate D decision note

Fail examples:
- 공개 기능은 있으나 publish 운영이 불안정한 경우
- security hardening 검증이 빠진 경우
- release evidence가 부족해 운영 인수 기준을 충족하지 못하는 경우

---

## 8. Gate Review Output Template

```md
Gate:
Date:
Result: Pass / Fail / Deferred
Summary:
Blocking Items:
Accepted Risks:
Follow-up Actions:
Approved By:
```

---

## 9. Definition of Done for WBS 0.5

`WBS 0.5 Stage gate 운영 기준 확정`은 아래 조건을 충족하면 완료로 본다.

- Gate A~D의 목적이 정리되어 있다.
- 각 gate별 필수 체크리스트가 정의되어 있다.
- gate decision owner와 결과 기록 방식이 정리되어 있다.
- fail 사례와 산출물이 명시되어 있다.
- WBS/roadmap 운영과 연결되는 업데이트 규칙이 포함되어 있다.

---

## 10. Change History

| Date | Change |
|---|---|
| 2026-03-29 | Initial stage gate checklist created |
