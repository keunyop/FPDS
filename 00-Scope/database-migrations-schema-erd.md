# FPDS Admin DB migration, schema, ERD 인수인계

상태: 저장소 migration 전수 목록 + shared dev 실측 schema

기준일: 2026-08-29

Database: Supabase-hosted PostgreSQL, schema public

## 1. 읽는 법과 안전 경계

- migration의 원본 권위는 db/migrations/*.sql이다.
- 이 문서의 shared dev 상태는 2026-08-29에 BEGIN READ ONLY로 조회했다.
- 저장소에 파일이 있다는 사실과 특정 DB에 적용됐다는 사실을 구분한다.
- migration_history만으로 증명할 수 없는 data migration은 임의로
  적용됐다고 가정하지 않는다.
- 이 문서는 schema와 관계를 설명한다. DB URL, role password, pool
  credential 또는 실제 customer/evidence 값은 포함하지 않는다.
- production 적용 전에는 별도 backup, restore rehearsal, migration review와
  승인된 배포 절차가 필요하다.

## 2. 현재 버전 요약

| 항목 | 2026-08-29 확인 결과 |
|---|---|
| 저장소 migration 파일 | 44개, 0001부터 0044까지 연속 |
| shared dev 최신 history | 0044_remove_admin_collection_scheduler.sql |
| shared dev history row | 40개 |
| public base table | 31개 |
| public compatibility view | 2개: audit_event, llm_usage_record |
| 현재 제거된 historical table | evidence_chunk_embedding, dashboard_metric_snapshot, dashboard_ranking_snapshot, dashboard_scatter_snapshot |
| 현재 retrieval | metadata-scored evidence; 0012의 pgvector side table은 0040에서 제거 |
| 현재 aggregate read | public_product_projection에서 request-time 파생 |

### 확인된 migration drift

1. 0013_operator_managed_product_types.sql은 적용 시 history row를 남겨야
   하지만 shared dev history에 없다.
2. shared dev product_type_registry에 built_in_flag가 남아 있어 0013의
   DROP COLUMN 효과도 현재 존재하지 않는다. 과거 실행 여부를 단정하지
   않고, 인수 전 reviewed migration
   reconciliation이 필요하다.
3. 0009, 0014, 0015는 SQL 자체가 migration_history를 기록하지 않는다.
   - 0009: 일회성 candidate name backfill의 실행 여부를 history로 증명할
     수 없다.
   - 0014: 목표인 Canada deposit taxonomy 14개 행은 현재 존재하지만 0001
     seed와도 동일하므로 0014 실행 여부 자체는 판별할 수 없다.
   - 0015: 목표 policy-auto-approve-min-confidence-v2, value 0.82는 현재
     active 상태로 확인됐다.

현재 version을 0044라고 부를 수는 있지만, 인수 완료 판정은 0013 drift를
해결하고 fresh replay와 live schema가 일치할 때만 한다.

## 3. Migration 전수 목록

상태 값:

- 기록됨: shared dev migration_history에서 확인
- 효과 확인/history 없음: SQL은 history를 남기지 않지만 목표 상태 확인
- 판정 불가/history 없음: SQL이 history를 남기지 않고 실행 여부를 안전하게
  추론할 수 없음
- 현재 효과 없음/history 없음: history와 현재 schema 양쪽에서 목표 효과가
  확인되지 않음

### 0001-0011

| No. | 파일 | 목적 | shared dev |
|---|---|---|---|
| 0001 | 0001_initial_baseline.sql | core schema, Canada bank/taxonomy, processing policy seed | 기록됨 |
| 0002 | 0002_admin_auth.sql | user account, server session, login attempt | 기록됨 |
| 0003 | 0003_aggregate_refresh.sql | aggregate run, Public projection, 최초 dashboard snapshot schema | 기록됨; dashboard tables는 0040에서 제거 |
| 0004 | 0004_source_registry_admin.sql | source_registry_item과 scope/index | 기록됨 |
| 0005 | 0005_source_registry_unique_scope_fix.sql | source uniqueness에 product type 포함 | 기록됨 |
| 0006 | 0006_bank_catalog_management.sql | bank homepage 관리 필드와 source catalog coverage | 기록됨 |
| 0007 | 0007_dynamic_product_type_onboarding.sql | product_type_registry | 기록됨 |
| 0008 | 0008_discovery_metadata_persistence.sql | source_registry_item.discovery_metadata | 기록됨 |
| 0009 | 0009_backfill_review_edit_approved_candidate_product_name.sql | 최신 edit-approve 이름을 candidate와 payload에 backfill | 판정 불가/history 없음 |
| 0010 | 0010_aggregate_refresh_queue.sql | aggregate refresh request queue | 기록됨 |
| 0011 | 0011_admin_signup_requests.sql | login_id auth 변경과 승인형 signup request | 기록됨 |

### 0012-0024

| No. | 파일 | 목적 | shared dev |
|---|---|---|---|
| 0012 | 0012_evidence_chunk_embeddings.sql | pgvector evidence embedding side table | 기록됨; table은 0040에서 제거 |
| 0013 | 0013_operator_managed_product_types.sql | built_in_flag 제거와 모든 Product Type의 operator-managed 전환 | 현재 효과 없음/history 없음 |
| 0014 | 0014_canonical_deposit_taxonomy_backfill.sql | Canada chequing/savings/GIC subtype 14행 복원 | 효과 확인/history 없음 |
| 0015 | 0015_phase1_review_confidence_policy.sql | auto-approve confidence 0.82 policy v2 | 효과 확인/history 없음 |
| 0016 | 0016_auto_promotion_aggregate_trigger.sql | candidate auto-promotion aggregate trigger 허용 | 기록됨 |
| 0017 | 0017_canonical_identity_alias_repair.sql | bank/Product Type identity alias repair | 기록됨 |
| 0018 | 0018_canonical_source_document_identity_repair.sql | alias repair 후 source document identity 정렬 | 기록됨 |
| 0019 | 0019_canada_lending_product_types.sql | Canada card/mortgage/personal loan/LOC Product Type와 taxonomy | 기록됨 |
| 0020 | 0020_canada_recognized_banks_full_coverage.sql | Canada bank/logo와 전체 Product Type coverage baseline | 기록됨 |
| 0021 | 0021_vancity_credit_union_full_coverage.sql | Vancity와 전체 active Product Type coverage | 기록됨 |
| 0022 | 0022_bank_logo_asset_refresh.sql | 공식 logo asset 갱신 | 기록됨 |
| 0023 | 0023_versioned_parsed_documents.sql | snapshot별 parser version immutable parse 허용 | 기록됨 |
| 0024 | 0024_deposit_field_contract_defaults.sql | deposit expected field contract 정렬 | 기록됨 |

### 0025-0034

| No. | 파일 | 목적 | shared dev |
|---|---|---|---|
| 0025 | 0025_country_scoped_admin.sql | country registry, country-bound session/run, composite country-bank integrity | 기록됨 |
| 0026 | 0026_country_registry_management.sql | country English fallback name과 lookup index | 기록됨 |
| 0027 | 0027_standalone_ai_operations.sql | run 없는 operational model execution/usage 허용 | 기록됨; usage table은 0040에서 view로 대체 |
| 0028 | 0028_source_catalog_coverage_evidence.sql | coverage source URL 보존 | 기록됨 |
| 0029 | 0029_collection_ai_autopilot_policy.sql | collection-time AI remediation와 grounding threshold | 기록됨 |
| 0030 | 0030_collection_approval_field_policy.sql | approval denominator를 identity+decision field로 변경 | 기록됨 |
| 0031 | 0031_catalog_coverage_route_evidence.sql | consumer-brand route evidence와 not-offered metadata | 기록됨 |
| 0032 | 0032_comparison_grade_collection_quality.sql | comparison-grade approval/field policy | 기록됨 |
| 0033 | 0033_essential_field_low_touch_publication.sql | type별 essential field와 complete grounding publication | 기록됨 |
| 0034 | 0034_country_product_market_profiles.sql | US market profile, source metadata, wrong-role cleanup | 기록됨 |

### 0035-0044

| No. | 파일 | 목적 | shared dev |
|---|---|---|---|
| 0035 | 0035_collection_publication_automation.sql | historical recurring collection/recovery policy 도입 | 기록됨; recurring policy는 0044에서 제거 |
| 0036 | 0036_us_pricing_evidence_companions.sql | US pricing companion과 card APR summary field | 기록됨 |
| 0037 | 0037_us_pricing_companion_scope_cleanup.sql | generic online-banking agreement 비활성화 | 기록됨 |
| 0038 | 0038_us_cross_product_support_cleanup.sql | card scope의 vehicle-loan supporting source 비활성화 | 기록됨 |
| 0039 | 0039_us_credit_card_apr_range_contract.sql | qualified Purchase APR range를 preferred requirement로 설정 | 기록됨 |
| 0040 | 0040_bounded_operational_storage.sql | audit/usage/embedding/dashboard physical table 제거, compatibility view와 bounded retention | 기록됨 |
| 0041 | 0041_vancity_official_product_routes.sql | Vancity 7개 Product Type 공식 family hub 고정 | 기록됨 |
| 0042 | 0042_three_bank_partial_run_scope_hardening.sql | Bridgewater/EQ/Fairstone verified route와 unsupported scope 비활성화 | 기록됨 |
| 0043 | 0043_generic_zero_detail_scope_quarantine.sql | verified route 고정과 zero-detail blanket coverage quarantine | 기록됨 |
| 0044 | 0044_remove_admin_collection_scheduler.sql | recurring collection/recovery policy row 제거, 수동 collection 경계 | 기록됨 |

### 적용 확인 query

실제 DB URL은 shell history나 문서에 붙여 넣지 않고 승인된 환경변수로
주입한다.

~~~sql
BEGIN READ ONLY;
SELECT migration_name, applied_at
FROM migration_history
ORDER BY applied_at, migration_name;
COMMIT;
~~~

fresh DB에는 db/README.md의 순서대로 0001부터 0044까지 적용한다. 단,
0013 drift를 확인한 뒤 migration을 재실행할지 별도 corrective migration을
만들지는 DBA/Product Owner 승인으로 결정한다.

## 4. 현재 physical schema

표기:

- PK: primary key
- FK: foreign key
- UQ: unique key
- 물음표가 붙은 열은 nullable
- jsonb는 빠르게 변하는 candidate, policy, metadata payload를 보존한다.
- 아래 열은 information_schema를 shared dev에서 읽기 전용 조회한 결과다.

### 4.1 기준·정책·인증

| Table | Key/관계 | 현재 열 |
|---|---|---|
| migration_history | PK migration_name | migration_name text; applied_at timestamptz |
| country_registry | PK country_code | country_code text; status text; display_order integer; country_name text; created_at, updated_at timestamptz |
| bank | PK bank_code; FK country_code → country_registry; UQ country_code+bank_code | bank_code text; country_code text; bank_name text; status text; homepage_url?, normalized_homepage_url?, source_language text; managed_flag boolean; change_reason?; logo_url?, logo_alt_text?; created_at, updated_at timestamptz |
| taxonomy_registry | PK taxonomy_id; UQ country_code+product_family+product_type+subtype_code | taxonomy_id text; country_code text; product_family text; product_type text; subtype_code text; display_order integer; active_flag boolean; notes?; created_at, updated_at timestamptz |
| product_type_registry | PK product_type_code | product_type_code text; product_family text; display_name text; description text; status text; **built_in_flag boolean**; managed_flag boolean; discovery_keywords jsonb; expected_fields jsonb; fallback_policy text; created_at, updated_at timestamptz |
| processing_policy_config | PK policy_config_id | policy_config_id text; policy_key text; version_no integer; policy_value jsonb; active_flag boolean; created_by?, notes?; created_at timestamptz |
| user_account | PK user_id; unique login_id/email 규칙은 migration constraint 참조 | user_id text; login_id text; email?; display_name text; role text; account_status text; password_hash text; password_algorithm text; failed_login_count integer; last_login_failed_at?, locked_until?, last_login_succeeded_at? timestamptz; password_changed_at, created_at, updated_at timestamptz |
| user_signup_request | PK signup_request_id; FK reviewed_by_user_id/approved_user_id → user_account | signup_request_id text; login_id text; display_name text; password_hash text; password_algorithm text; request_status text; reviewed_role?, review_reason?; requested_at timestamptz; reviewed_at? timestamptz; reviewed_by_user_id?, approved_user_id?; created_at, updated_at timestamptz |
| admin_auth_session | PK auth_session_id; FK user_id → user_account; FK country_code → country_registry | auth_session_id text; user_id text; country_code text; session_token_hash text; csrf_token?; session_status text; issued_at, last_seen_at, idle_expires_at, absolute_expires_at timestamptz; revoked_at? timestamptz; revoked_reason?, ip_address?, user_agent?; created_at timestamptz |
| auth_login_attempt | PK login_attempt_id; FK user_id → user_account | login_attempt_id text; login_id?; email text; user_id?; ip_address?; attempt_outcome text; failure_reason_code?; attempted_at timestamptz |

product_type_registry.built_in_flag는 0013이 제거해야 하는 drift 열이다.
runtime API response는 이 열을 사용하지 않지만 fresh replay와 shared dev
schema 불일치가 남으므로 인수 전 정리한다.

### 4.2 Source registry·ingestion·evidence

| Table | Key/관계 | 현재 열 |
|---|---|---|
| source_registry_catalog_item | PK catalog_item_id; FK bank_code 및 country_code+bank_code → bank; UQ country+bank+product_type | catalog_item_id text; bank_code text; country_code text; product_type text; status text; change_reason?; coverage_source_url?, normalized_coverage_source_url?; coverage_source_metadata jsonb; created_at, updated_at timestamptz |
| source_registry_item | PK source_id; FK bank_code 및 country_code+bank_code → bank | source_id text; bank_code text; country_code text; product_type text; product_key?; source_name text; source_url text; normalized_url text; source_type text; discovery_role text; status text; priority text; source_language text; purpose text; expected_fields jsonb; seed_source_flag boolean; last_verified_at?, last_seen_at? timestamptz; redirect_target_url?; alias_urls jsonb; change_reason?; discovery_metadata jsonb; created_at, updated_at timestamptz |
| ingestion_run | PK run_id; FK country_code → country_registry; self-FK retry_of_run_id/retried_by_run_id | run_id text; country_code text; run_state text; trigger_type text; triggered_by?; source_scope_count, source_success_count, source_failure_count, candidate_count, review_queued_count integer; error_summary?; partial_completion_flag boolean; retry_of_run_id?, retried_by_run_id?; run_metadata jsonb; started_at timestamptz; completed_at? timestamptz |
| source_document | PK source_document_id; FK bank_code 및 country_code+bank_code → bank | source_document_id text; bank_code text; country_code text; normalized_source_url text; source_type text; source_language text; registry_managed_flag boolean; source_metadata jsonb; discovered_at, created_at, updated_at timestamptz |
| source_snapshot | PK snapshot_id; FK source_document_id → source_document | snapshot_id text; source_document_id text; object_storage_key text; content_type text; checksum text; fingerprint text; fetch_status text; response_metadata jsonb; retention_class text; fetched_at, created_at timestamptz |
| run_source_item | PK run_source_item_id; FK run_id → ingestion_run; FK source_document_id → source_document; FK selected_snapshot_id → source_snapshot | run_source_item_id text; run_id text; source_document_id text; selected_snapshot_id?; stage_status text; warning_count, error_count integer; error_summary?; stage_metadata jsonb; created_at, updated_at timestamptz |
| parsed_document | PK parsed_document_id; FK snapshot_id → source_snapshot; UQ snapshot_id+parser_version | parsed_document_id text; snapshot_id text; parsed_storage_key text; parser_version text; parse_quality_note?; parser_metadata jsonb; retention_class text; parsed_at, created_at timestamptz |
| evidence_chunk | PK evidence_chunk_id; FK parsed_document_id → parsed_document | evidence_chunk_id text; parsed_document_id text; chunk_index integer; anchor_type text; anchor_value?; page_no? integer; source_language text; chunk_char_start?, chunk_char_end? integer; evidence_excerpt text; retrieval_metadata jsonb; created_at timestamptz |
| model_execution | PK model_execution_id; FK run_id → ingestion_run; FK source_document_id → source_document | model_execution_id text; run_id?; source_document_id?; stage_name text; agent_name text; model_id text; execution_status text; execution_metadata jsonb; started_at timestamptz; completed_at? timestamptz |

### 4.3 Candidate·review·canonical

| Table | Key/관계 | 현재 열 |
|---|---|---|
| normalized_candidate | PK candidate_id; FK run_id → ingestion_run; FK source_document_id → source_document; FK model_execution_id → model_execution; FK bank/country+bank → bank | candidate_id text; run_id text; source_document_id text; model_execution_id?; candidate_state text; validation_status text; source_confidence numeric; review_reason_code?; country_code text; bank_code text; product_family text; product_type text; subtype_code?; product_name text; source_language text; currency text; validation_issue_codes jsonb; candidate_payload jsonb; field_mapping_metadata jsonb; created_at, updated_at timestamptz |
| review_task | PK review_task_id; UQ candidate_id; FK candidate_id → normalized_candidate; FK run_id → ingestion_run; FK product_id → canonical_product | review_task_id text; candidate_id text; run_id text; product_id?; review_state text; queue_reason_code text; issue_summary jsonb; created_at, updated_at timestamptz |
| review_decision | PK review_decision_id; FK review_task_id → review_task | review_decision_id text; review_task_id text; actor_user_id?; action_type text; reason_code?, reason_text?, diff_summary?; override_payload jsonb; decided_at timestamptz |
| canonical_product | PK product_id; FK bank/country+bank → bank | product_id text; bank_code text; country_code text; product_family text; product_type text; subtype_code?; product_name text; source_language text; currency text; status text; current_version_no integer; last_verified_at timestamptz; last_changed_at? timestamptz; current_snapshot_payload jsonb; created_at, updated_at timestamptz |
| product_version | PK product_version_id; FK product_id → canonical_product; UQ approved_candidate_id → normalized_candidate | product_version_id text; product_id text; approved_candidate_id?; version_no integer; version_status text; normalized_payload jsonb; approved_at timestamptz; superseded_at? timestamptz; created_at timestamptz |
| field_evidence_link | PK field_evidence_link_id; FK candidate_id → normalized_candidate; FK product_version_id → product_version; FK evidence_chunk_id → evidence_chunk; FK source_document_id → source_document | field_evidence_link_id text; candidate_id?; product_version_id?; evidence_chunk_id text; source_document_id text; field_name text; candidate_value text; citation_confidence numeric; created_at timestamptz |
| change_event | PK change_event_id; FK product_id → canonical_product; FK product_version_id → product_version; FK run_id → ingestion_run; FK review_task_id → review_task | change_event_id text; product_id text; product_version_id?; run_id?; review_task_id?; event_type text; event_reason_code?; event_metadata jsonb; detected_at timestamptz |

field_evidence_link는 candidate_id 또는 product_version_id 중 정확히 하나만
가리키는 check constraint를 유지한다. review_decision.actor_user_id는 현재
물리 FK가 아니므로 actor trace 정책을 application/운영 절차와 함께 검토한다.

### 4.4 Aggregate·projection·publish

| Table | Key/관계 | 현재 열 |
|---|---|---|
| aggregate_refresh_run | PK snapshot_id; FK triggered_by_run_id → ingestion_run | snapshot_id text; triggered_by_run_id?; refresh_scope text; country_code text; filter_scope jsonb; refresh_status text; source_change_cutoff_at? timestamptz; attempted_at timestamptz; refreshed_at? timestamptz; stale_flag boolean; error_summary?; refresh_metadata jsonb; created_at timestamptz |
| aggregate_refresh_request | PK aggregate_refresh_request_id; FK requested_by_user_id → user_account; FK review_task_id → review_task; FK product_id → canonical_product; FK snapshot_id → aggregate_refresh_run ON DELETE SET NULL | aggregate_refresh_request_id text; refresh_scope text; country_code text; request_status text; trigger_reason text; requested_by_user_id?, requested_by_label?, review_task_id?, product_id?; request_metadata jsonb; requested_at timestamptz; started_at?, completed_at? timestamptz; snapshot_id?, error_summary?; created_at timestamptz |
| public_product_projection | composite PK snapshot_id+product_id; FK snapshot_id → aggregate_refresh_run ON DELETE CASCADE; FK product_id → canonical_product; FK bank/country+bank → bank | snapshot_id text; product_id text; bank_code text; bank_name text; country_code text; product_family text; product_type text; subtype_code?; product_name text; source_language text; currency text; status text; public_display_rate?, public_display_fee?, monthly_fee?, effective_fee?, minimum_balance?, minimum_deposit? numeric; term_length_days? integer; product_highlight_badge_code?; target_customer_tags jsonb; fee_bucket?, minimum_balance_bucket?, minimum_deposit_bucket?, term_bucket?; last_verified_at?, last_changed_at? timestamptz; refresh_metadata jsonb; created_at timestamptz |
| publish_item | PK publish_item_id; FK product_version_id → product_version | publish_item_id text; product_version_id text; target_system_code text; publish_state text; pending_reason_code?; target_environment text; target_master_id?; target_metadata jsonb; created_at, updated_at timestamptz |
| publish_attempt | PK publish_attempt_id; FK publish_item_id → publish_item | publish_attempt_id text; publish_item_id text; attempt_no integer; attempt_result_state text; error_code?, response_summary?; response_metadata jsonb; attempted_at timestamptz |

publish_item/publish_attempt는 BX-PF readiness history 구조다. 현재 dev의
BX-PF mode는 mock이며 이 테이블의 존재가 live write-back 승인을 의미하지
않는다.

### 4.5 Compatibility view와 제거된 구조

| Relation | 현재 동작 |
|---|---|
| audit_event view | 0040이 physical table을 제거했다. 항상 0행이며 write trigger가 obsolete log write를 discard한다. |
| llm_usage_record view | 0040이 physical table을 제거했다. 항상 0행이며 write trigger가 obsolete usage write를 discard한다. |
| evidence_chunk_embedding | 0012가 만들었으나 0040에서 제거됐다. 현재 schema에 없다. |
| dashboard_metric_snapshot | 0003이 만들었으나 0040에서 제거됐다. |
| dashboard_ranking_snapshot | 0003이 만들었으나 0040에서 제거됐다. |
| dashboard_scatter_snapshot | 0003이 만들었으나 0040에서 제거됐다. |

model_execution은 현재 bounded AI result/cache lineage를 보존한다.
독립 token/cost ledger와 독립 audit ledger는 현재 운영 계약이 아니다.

## 5. ERD

ERD는 물리 FK를 기준으로 업무 영역별로 나눴다. taxonomy/product type code
참조처럼 application이 검증하지만 물리 FK가 아닌 관계는 선으로 표시하지
않았다.

### 5.1 Country·auth·registry

~~~mermaid
erDiagram
    COUNTRY_REGISTRY {
        text country_code PK
        text status
        text country_name
    }
    BANK {
        text bank_code PK
        text country_code FK
        text bank_name
    }
    USER_ACCOUNT {
        text user_id PK
        text login_id
        text role
        text account_status
    }
    USER_SIGNUP_REQUEST {
        text signup_request_id PK
        text reviewed_by_user_id FK
        text approved_user_id FK
    }
    ADMIN_AUTH_SESSION {
        text auth_session_id PK
        text user_id FK
        text country_code FK
    }
    AUTH_LOGIN_ATTEMPT {
        text login_attempt_id PK
        text user_id FK
    }
    SOURCE_REGISTRY_CATALOG_ITEM {
        text catalog_item_id PK
        text bank_code FK
        text country_code
        text product_type
    }
    SOURCE_REGISTRY_ITEM {
        text source_id PK
        text bank_code FK
        text country_code
        text product_type
    }
    PRODUCT_TYPE_REGISTRY {
        text product_type_code PK
    }
    TAXONOMY_REGISTRY {
        text taxonomy_id PK
    }

    COUNTRY_REGISTRY ||--o{ BANK : owns
    COUNTRY_REGISTRY ||--o{ ADMIN_AUTH_SESSION : scopes
    USER_ACCOUNT ||--o{ ADMIN_AUTH_SESSION : has
    USER_ACCOUNT o|--o{ AUTH_LOGIN_ATTEMPT : identifies
    USER_ACCOUNT o|--o{ USER_SIGNUP_REQUEST : reviews
    BANK ||--o{ SOURCE_REGISTRY_CATALOG_ITEM : has_coverage
    BANK ||--o{ SOURCE_REGISTRY_ITEM : has_sources
~~~

### 5.2 Ingestion·snapshot·evidence

~~~mermaid
erDiagram
    COUNTRY_REGISTRY {
        text country_code PK
    }
    BANK {
        text bank_code PK
        text country_code FK
    }
    INGESTION_RUN {
        text run_id PK
        text country_code FK
        text retry_of_run_id FK
        text retried_by_run_id FK
    }
    SOURCE_DOCUMENT {
        text source_document_id PK
        text bank_code FK
        text country_code
    }
    SOURCE_SNAPSHOT {
        text snapshot_id PK
        text source_document_id FK
        text object_storage_key
    }
    RUN_SOURCE_ITEM {
        text run_source_item_id PK
        text run_id FK
        text source_document_id FK
        text selected_snapshot_id FK
    }
    PARSED_DOCUMENT {
        text parsed_document_id PK
        text snapshot_id FK
        text parser_version
    }
    EVIDENCE_CHUNK {
        text evidence_chunk_id PK
        text parsed_document_id FK
    }
    MODEL_EXECUTION {
        text model_execution_id PK
        text run_id FK
        text source_document_id FK
    }

    COUNTRY_REGISTRY ||--o{ INGESTION_RUN : scopes
    BANK ||--o{ SOURCE_DOCUMENT : owns
    INGESTION_RUN ||--o{ RUN_SOURCE_ITEM : selects
    SOURCE_DOCUMENT ||--o{ RUN_SOURCE_ITEM : participates
    SOURCE_DOCUMENT ||--o{ SOURCE_SNAPSHOT : captured_as
    SOURCE_SNAPSHOT o|--o{ RUN_SOURCE_ITEM : selected_by
    SOURCE_SNAPSHOT ||--o{ PARSED_DOCUMENT : parsed_by_version
    PARSED_DOCUMENT ||--o{ EVIDENCE_CHUNK : contains
    INGESTION_RUN o|--o{ MODEL_EXECUTION : executes
    SOURCE_DOCUMENT o|--o{ MODEL_EXECUTION : grounds
    INGESTION_RUN o|--o{ INGESTION_RUN : retries
~~~

### 5.3 Candidate·review·canonical·publish

~~~mermaid
erDiagram
    INGESTION_RUN {
        text run_id PK
    }
    SOURCE_DOCUMENT {
        text source_document_id PK
    }
    MODEL_EXECUTION {
        text model_execution_id PK
    }
    NORMALIZED_CANDIDATE {
        text candidate_id PK
        text run_id FK
        text source_document_id FK
        text model_execution_id FK
    }
    REVIEW_TASK {
        text review_task_id PK
        text candidate_id FK
        text run_id FK
        text product_id FK
    }
    REVIEW_DECISION {
        text review_decision_id PK
        text review_task_id FK
    }
    CANONICAL_PRODUCT {
        text product_id PK
        text bank_code FK
    }
    PRODUCT_VERSION {
        text product_version_id PK
        text product_id FK
        text approved_candidate_id FK
    }
    EVIDENCE_CHUNK {
        text evidence_chunk_id PK
    }
    FIELD_EVIDENCE_LINK {
        text field_evidence_link_id PK
        text candidate_id FK
        text product_version_id FK
        text evidence_chunk_id FK
        text source_document_id FK
    }
    CHANGE_EVENT {
        text change_event_id PK
        text product_id FK
        text product_version_id FK
        text run_id FK
        text review_task_id FK
    }
    PUBLISH_ITEM {
        text publish_item_id PK
        text product_version_id FK
    }
    PUBLISH_ATTEMPT {
        text publish_attempt_id PK
        text publish_item_id FK
    }

    INGESTION_RUN ||--o{ NORMALIZED_CANDIDATE : produces
    SOURCE_DOCUMENT ||--o{ NORMALIZED_CANDIDATE : defines
    MODEL_EXECUTION o|--o{ NORMALIZED_CANDIDATE : supports
    NORMALIZED_CANDIDATE ||--o| REVIEW_TASK : may_queue
    REVIEW_TASK ||--o{ REVIEW_DECISION : records
    CANONICAL_PRODUCT o|--o{ REVIEW_TASK : continuity_target
    CANONICAL_PRODUCT ||--o{ PRODUCT_VERSION : versions
    NORMALIZED_CANDIDATE o|--o| PRODUCT_VERSION : approved_as
    NORMALIZED_CANDIDATE o|--o{ FIELD_EVIDENCE_LINK : cites
    PRODUCT_VERSION o|--o{ FIELD_EVIDENCE_LINK : cites
    EVIDENCE_CHUNK ||--o{ FIELD_EVIDENCE_LINK : supports
    SOURCE_DOCUMENT ||--o{ FIELD_EVIDENCE_LINK : originates
    CANONICAL_PRODUCT ||--o{ CHANGE_EVENT : changes
    PRODUCT_VERSION o|--o{ CHANGE_EVENT : version_context
    INGESTION_RUN o|--o{ CHANGE_EVENT : run_context
    REVIEW_TASK o|--o{ CHANGE_EVENT : review_context
    PRODUCT_VERSION ||--o{ PUBLISH_ITEM : queues
    PUBLISH_ITEM ||--o{ PUBLISH_ATTEMPT : attempts
~~~

### 5.4 Aggregate projection

~~~mermaid
erDiagram
    USER_ACCOUNT {
        text user_id PK
    }
    INGESTION_RUN {
        text run_id PK
    }
    REVIEW_TASK {
        text review_task_id PK
    }
    CANONICAL_PRODUCT {
        text product_id PK
    }
    BANK {
        text bank_code PK
    }
    AGGREGATE_REFRESH_REQUEST {
        text aggregate_refresh_request_id PK
        text requested_by_user_id FK
        text review_task_id FK
        text product_id FK
        text snapshot_id FK
    }
    AGGREGATE_REFRESH_RUN {
        text snapshot_id PK
        text triggered_by_run_id FK
        text country_code
    }
    PUBLIC_PRODUCT_PROJECTION {
        text snapshot_id PK
        text product_id PK
        text bank_code FK
        text country_code
    }

    USER_ACCOUNT o|--o{ AGGREGATE_REFRESH_REQUEST : requests
    REVIEW_TASK o|--o{ AGGREGATE_REFRESH_REQUEST : triggers
    CANONICAL_PRODUCT o|--o{ AGGREGATE_REFRESH_REQUEST : targets
    AGGREGATE_REFRESH_REQUEST o{--o| AGGREGATE_REFRESH_RUN : completes_as
    INGESTION_RUN o|--o{ AGGREGATE_REFRESH_RUN : triggers
    AGGREGATE_REFRESH_RUN ||--o{ PUBLIC_PRODUCT_PROJECTION : snapshots
    CANONICAL_PRODUCT ||--o{ PUBLIC_PRODUCT_PROJECTION : projects
    BANK ||--o{ PUBLIC_PRODUCT_PROJECTION : labels
~~~

## 6. 인수인계 DB 체크리스트

- [ ] 0013 drift의 원인과 corrective 적용 방식을 DBA/Product Owner가
      승인했다.
- [ ] 0009, 0014, 0015처럼 history를 남기지 않는 migration의 증적 방식을
      정하고 future migration은 일관되게 기록한다.
- [ ] 깨끗한 빈 PostgreSQL에 0001→0044를 순서대로 적용하고 schema diff가
      승인된 target과 일치한다.
- [ ] 의뢰자 소유 dev/prod Supabase/PostgreSQL project, role, pool, credential,
      backup/PITR와 비용 계정이 분리됐다.
- [ ] application, migration, backup, read-only support role을 최소 권한으로
      분리했다.
- [ ] TLS connection, connection limit, timeout, maintenance window와 pool
      mode를 기록했다.
- [ ] 암호화 backup을 별도 target에 실제 restore하고 table/row count와 핵심
      canonical/aggregate 데이터를 대조했다.
- [ ] object_storage_key가 가리키는 private S3 object count/hash를 DB와
      함께 reconciliation했다.
- [ ] audit_event와 llm_usage_record가 physical ledger가 아닌 discard-only
      compatibility view임을 운영자와 보안 담당자가 승인했다.
- [ ] BX-PF가 mock이며 publish table 존재가 live write 권한을 뜻하지
      않음을 확인했다.
- [ ] schema-only dump와 migration history export에 owner, ACL, credential,
      customer/evidence 원문이 포함되지 않았는지 검사했다.

## 7. 받아야 할 DB 증거 파일

의뢰자 제한 저장소의 03-Data-And-Recovery 아래에 보관한다.

| 파일 위치 | 내용 |
|---|---|
| 00-db-migration-and-schema-readme.md | 이 문서의 승인된 release 사본 또는 링크 |
| 01-migration-history.csv | environment, migration_name, applied_at의 비밀 없는 export |
| 02-schema-only.sql | pg_dump --schema-only --no-owner --no-privileges 결과 |
| 03-schema-diff.txt | fresh replay와 target DB schema 비교 결과 |
| 04-encrypted-backup-manifest.md | backup ID, 암호화, 보관 위치 참조, hash, 생성자 |
| 05-restore-reconciliation.xlsx | restore target, table/row count, object count/hash, 차이 승인 |
| 06-db-roles-and-access.pdf | role matrix, MFA/SSO, break-glass, 회수 증거 |
| 07-pitr-and-rollback-report.md | PITR/restore point와 application rollback rehearsal |

실제 dump, DB URL, password와 evidence data는 Git에 넣지 않는다.

## 8. 근거와 재검증 명령

Repository 근거:

- db/migrations/0001_initial_baseline.sql부터
  db/migrations/0044_remove_admin_collection_scheduler.sql
- db/README.md
- docs/03-design/db-migration-baseline.md
- docs/03-design/domain-model-canonical-schema.md
- api/service/api_service/db.py
- worker의 각 persistence module

읽기 전용 schema 재검증:

~~~sql
BEGIN READ ONLY;

SELECT table_type, table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_type, table_name;

SELECT
    c.conrelid::regclass::text AS table_name,
    c.contype,
    c.conname,
    pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint AS c
JOIN pg_namespace AS n ON n.oid = c.connamespace
WHERE n.nspname = 'public'
  AND c.contype IN ('p', 'f')
ORDER BY c.conrelid::regclass::text, c.conname;

COMMIT;
~~~

schema-only export 예시:

~~~powershell
pg_dump $env:FPDS_DATABASE_URL --schema=public --schema-only --no-owner --no-privileges --file 02-schema-only.sql
~~~

이 명령은 승인된 제한 작업 디렉터리에서만 실행하고 output을 Git에
commit하지 않는다.
