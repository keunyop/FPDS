# FPDS Roadmap

Version: 1.0  
Date: 2026-03-29  
Status: Draft for Planning  
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/raid-log.md`
- `docs/00-governance/working-agreement.md`

## 0. Current Progress Snapshot

As of 2026-04-06, WBS 기준 현재 진행 상태는 아래와 같습니다.

| Metric | Value | Basis |
|---|---|---|
| Overall WBS Progress | 47.4% complete | 114개 WBS task 중 54개 `Completed` |
| Current Stage Progress | 100.0% complete | Stage 0 범위인 `0.x + 1.x` 54개 task 중 54개 `Completed` |
| Estimated Remaining Duration | about 124 working days | Stage 0 planning package completed, Stage 1~8 기본 일정 124일 |

계산 메모:
- 전체 진행률은 `Completed task count / 전체 WBS task count` 기준이다.
- 남은 기간은 현재 완료된 Stage 0 task 비율을 기준으로 Stage 0 3주 일정을 비례 환산했다.
- 이후 수치는 WBS 상태가 바뀔 때마다 함께 업데이트해야 한다.
- 2026-03-30 기준 WBS `1.1.1`~`1.1.5`가 `docs/02-requirements/scope-baseline.md` 생성과 함께 완료 처리되었다.
- 2026-03-30 기준 WBS `1.2.1`~`1.2.7`이 `docs/03-design/domain-model-canonical-schema.md` 생성과 함께 완료 처리되었다.
- 2026-03-31 기준 WBS `1.3.1`이 `docs/03-design/workflow-state-ingestion-design.md` 생성과 함께 완료 처리되었다.
- 2026-04-01 기준 WBS `1.3.2`~`1.3.5`가 `docs/03-design/review-run-publish-audit-state-design.md` 생성과 함께 완료 처리되었다.
- 2026-04-01 기준 WBS `1.4.1`이 `docs/03-design/system-context-diagram.md` 생성과 함께 완료 처리되었다.
- 2026-04-01 기준 WBS `1.4.2`가 `docs/03-design/erd-draft.md` 생성과 함께 완료 처리되었다.
- 2026-04-01 기준 WBS `1.4.3`~`1.4.6`이 storage/retrieval/aggregate/environment 설계 문서 생성과 함께 완료 처리되었다.
- 2026-04-01 기준 WBS `1.5.1`~`1.5.5`가 `docs/03-design/api-interface-contracts.md` 생성과 함께 완료 처리되었다.
- 2026-04-05 기준 WBS `1.6.1`~`1.6.7`이 `docs/03-design/security-access-control-design.md` 생성과 함께 완료 처리되었다.
- 2026-04-05 기준 WBS `1.7.1`이 `docs/03-design/product-grid-information-architecture.md` 생성과 함께 완료 처리되었다.
- 2026-04-05 기준 WBS `1.7.2`가 `docs/03-design/insight-dashboard-metric-definition.md` 생성과 함께 완료 처리되었다.
- 2026-04-05 기준 WBS `1.7.3`이 `docs/03-design/product-type-visualization-principles.md` 생성과 함께 완료 처리되었다.
- 2026-04-06 기준 WBS `1.7.4`가 `docs/03-design/admin-information-architecture.md` 생성과 함께 완료 처리되었다.
- 2026-04-06 기준 WBS `1.7.5`~`1.7.7`이 `docs/03-design/localization-governance-and-fallback-policy.md` 생성과 함께 완료 처리되었다.
- 2026-04-06 기준 WBS `1.8.1`이 `docs/01-planning/td-savings-source-inventory.md` 생성과 함께 완료 처리되었다.
- 2026-04-06 기준 WBS `1.8.2`가 `docs/01-planning/prototype-backlog.md` 생성과 함께 완료 처리되었다.
- 2026-04-06 기준 WBS `1.8.3`이 `docs/01-planning/prototype-acceptance-checklist.md` 생성과 함께 완료 처리되었다.
- 2026-04-06 기준 WBS `1.8.4`가 `docs/01-planning/prototype-spike-scope.md` 생성과 함께 완료 처리되었다.
- 2026-04-06 기준 WBS `1.8.5`가 `docs/01-planning/sprint-0-board.md` 생성과 함께 완료 처리되었다.
- 2026-04-06 기준 WBS `1.8.6`이 `docs/00-governance/gate-a-build-start-review-note.md` 생성과 함께 완료 처리되었다.
- 2026-04-06 기준 Gate A review는 최종 교차 검토 후 `Pass`로 승인되었다.
- 2026-04-06 기준 Stage 0는 문서 기준으로 마감되었고, Foundation/Prototype build는 `Next` 상태로 전환되었다.
- 2026-04-06 기준 Gate A `Pass`와 실제 구현 시작 승인은 분리되어 있으며, 구현은 별도 시작 지시 전까지 보류 상태다.
