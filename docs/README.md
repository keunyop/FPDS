# FPDS Docs Map

Version: 1.0
Date: 2026-04-06
Status: Active Navigation Index

---

## 1. Purpose

이 문서는 `docs` 폴더의 분류 기준과 주요 문서 위치를 빠르게 찾기 위한 인덱스다.

원칙:
- `00-governance`: 운영 규칙, 승인 기록, 상태 추적, 의사결정 로그
- `01-planning`: 실행 순서, backlog, inventory, sprint 준비 문서
- `02-requirements`: 요구사항 기준선과 범위 고정 문서
- `03-design`: 아키텍처, 데이터 모델, 정책, 인터페이스 설계 문서

---

## 2. Folder Classification

### 2.1 `docs/00-governance`

역할:
- 프로젝트 운영 기준
- gate / approval / review 기록
- decision / risk / milestone / roadmap 추적

주요 문서:
- `working-agreement.md`
- `scope-change-control.md`
- `stage-gate-checklist.md`
- `decision-log.md`
- `raid-log.md`
- `roadmap.md`
- `milestone-tracker.md`
- `gate-a-build-start-review-note.md`
- `gate-b-prototype-review-note.md`
- `codex-internet-domain-allowlist.md`
- `harness-engineering-baseline.md`
- `development-journal.md`
- `pre-development-owner-preparation-guide.md`
- `pre-development-owner-preparation-guide.md`

### 2.2 `docs/01-planning`

역할:
- WBS와 실행 계획
- prototype 준비물
- source inventory / backlog / sprint board

주요 문서:
- `plan.md`
- `WBS.md`
- `canada-big5-source-registry.md`
- `td-savings-source-inventory.md`
- `prototype-backlog.md`
- `prototype-acceptance-checklist.md`
- `prototype-findings-memo.md`
- `prototype-spike-scope.md`
- `sprint-0-board.md`
- `evidence/2026-04-11-first-successful-run/evidence-pack.md`

### 2.3 `docs/02-requirements`

역할:
- 상위 요구사항과 공식 범위 기준선

주요 문서:
- `FPDS_Requirements_Definition_v1_5.md`
- `scope-baseline.md`

### 2.4 `docs/03-design`

역할:
- 구현 전 상세 설계 패키지
- schema, workflow, security, IA, API, storage, localization 기준

주요 문서:
- `domain-model-canonical-schema.md`
- `workflow-state-ingestion-design.md`
- `review-run-publish-audit-state-design.md`
- `system-context-diagram.md`
- `erd-draft.md`
- `source-snapshot-evidence-storage-strategy.md`
- `source-registry-refresh-and-approval-policy.md`
- `retrieval-vector-starting-point.md`
- `aggregate-cache-refresh-strategy.md`
- `environment-separation-strategy.md`
- `dev-prod-environment-spec.md`
- `db-migration-baseline.md`
- `object-storage-evidence-bucket-baseline.md`
- `api-interface-contracts.md`
- `security-access-control-design.md`
- `fpds-design-system.md`
- `fpds_design_system_stripe_benchmark.md`
- `product-grid-information-architecture.md`
- `insight-dashboard-metric-definition.md`
- `product-type-visualization-principles.md`
- `admin-information-architecture.md`
- `localization-governance-and-fallback-policy.md`
- `shadcnblocks-adoption-log.md`
- `shadcnblocks-block-inventory.md`
- `ui-override-register.md`

---

## 3. Retrieval Order

문서를 읽을 때는 아래 순서를 권장한다.

1. `docs/02-requirements`
2. `docs/00-governance`
3. `docs/01-planning`
4. `docs/03-design`

실행 직전 검토 순서:

1. `scope-baseline.md`
2. `stage-gate-checklist.md`
3. `WBS.md`
4. `roadmap.md`
5. `milestone-tracker.md`
6. `gate-a-build-start-review-note.md`
7. 필요한 prototype/design supporting docs

---

## 5. Change History

| Date | Change |
|---|---|
| 2026-04-06 | Added root-level docs map and confirmed current folder classification is valid without file moves |
| 2026-04-13 | Added the Canada Big 5 source registry baseline document to the planning index |
