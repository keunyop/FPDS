---
name: fpds-database-change
description: FPDS Admin 관련 PostgreSQL schema, SQL migration, persistence와 데이터 보존 계약의 변경을 준비하고 격리 환경에서 검증할 때 사용한다. live migration, 복구나 canonical mutation의 권한을 자동으로 부여하지 않는다.
---

# FPDS DB 변경 준비와 검증

## 대상과 읽기

경로는 FPDS repository root 기준이다. AGENTS.md와 root README → docs/00-governance/development-journal.md → docs/README.md를 읽고 db/README.md, docs/03-design/db-migration-baseline.md, docs/03-design/domain-model-canonical-schema.md, docs/03-design/bounded-data-retention-policy.md를 확인한다. 실제 DB 접속 전 대상 환경과 허용 side-effect를 확인한다. 접속 비밀값을 출력하지 않는다.

00-Scope/database-migrations-schema-erd.md는 날짜별 환경 관찰이다. migration SQL 원본, 실제 적용 history, 실제 schema를 각각 대조한다. 필요 시 decision/RAID와 관련 API/Worker README를 읽는다. 현재 source는 0047까지지만 다음 번호는 작업 시 다시 확인한다.

## 변경 준비

- 기존 migration을 수정하거나 누락 번호를 추측해서 채우지 않는다. 다음 승인된 순서의 SQL로 schema delta를 작성한다.
- source migration에 historical seed가 있어도 기존 live DB 전체 replay를 기본값으로 삼지 않는다. 빈 registry 자동 복구를 구현하지 않는다.
- country-scoped uniqueness/index/FK, stable opaque IDs, jsonb type/constraint, canonical version/history와 field-linked evidence를 보존한다.
- 영향을 받는 API/Worker read/write/type 계약, transaction/lock, rollout 순서와 compatibility를 설명한다.
- schema 적용과 canonical/account/source registry data mutation을 구분한다. unrelated records를 정리하거나 기본값으로 금융 사실을 생성하지 않는다.

0040 이후 audit_event/llm_usage_record는 discard-only compatibility view이며 physical ledger가 아니다. metadata retrieval이 현재 기준이며 embedding side table을 복원하지 않는다. durable review_decision/change_event와 source/field evidence는 보존한다. 보존 함수 실행과 기존 evidence 삭제는 명시적 maintenance 범위가 필요하다.

## 적용과 복구 검증

코드 준비 요청이면 SQL, 적용 전 조건, schema/contract post-check, rollback 또는 forward-fix/restore 계획을 reviewable 결과로 만든다. live 적용이 이미 허용된 경우 해당 대상 범위에서 진행하며 구현 승인만으로 production 권한을 확대하지 않는다.

승인된 격리 dev DB에서는 fresh replay/upgrade 경로, schema diff, success/boundary/failure constraints와 영향 persistence transaction을 검증한다. 실제 PostgreSQL 검증 전 mock 테스트를 DB 적용 성공으로 표현하지 않는다. destructive/costly-to-reverse change는 Product Owner의 구체적 scope와 복구 경계를 적용한다.

migration 파일 검토는 actual data result와 분리한다. application rollout 전에 schema prerequisite을 명시한다. source의 0047은 Product Type country-keyed collection policy를 추가하며 matching API/Worker/Admin보다 먼저 적용되어야 한다.

## 결과

DDL/persistence diff, migration 번호·대상, 실행/미실행 항목, before/after schema 관찰, data-preservation 근거, 배포·복구 한계를 보고한다. db/README.md 및 실제 달라진 인계 inventory/계약/journal/이번 goal slice를 갱신하고 git diff --check를 실행한다. production 인수/restore/GO는 descent의 운영 인수 기준을 유지한다.
