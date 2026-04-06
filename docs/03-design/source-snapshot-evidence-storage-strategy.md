# FPDS Source Snapshot and Evidence Storage Strategy

Version: 1.0  
Date: 2026-04-01  
Status: Approved Baseline for WBS 1.4.3  
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/system-context-diagram.md`
- `docs/03-design/erd-draft.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/review-run-publish-audit-state-design.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

이 문서는 `WBS 1.4.3 source snapshot/evidence 저장 전략 확정`을 닫기 위한 기준 문서다.

목적:
- raw snapshot, parsed text, chunk metadata의 저장 경계를 고정한다.
- object storage와 relational metadata store의 책임 분리를 명확히 한다.
- admin trace, retrieval, change detection, auditability를 만족하는 최소 저장 전략을 정의한다.

이 문서는 논리/운영 저장 전략을 정의한다.  
exact bucket policy, object lifecycle rule, encryption setting, retention day 수치, vendor-specific storage class는 후속 infra/security 설정에서 구체화한다.

---

## 2. Baseline Decisions Carried Forward

본 문서는 아래 확정사항을 반영한다.

1. FPDS는 source snapshot, parsed text, evidence chunk를 소유한다.
2. source identity는 `bank_code + normalized_source_url + source_type`를 기본 키로 본다.
3. content identity는 `checksum/fingerprint`로 추적한다.
4. public evidence exposure는 비범위이며, evidence 접근은 admin trace와 internal workflow에 한정한다.
5. retrieval boundary는 retrieval-ready evidence 저장까지를 우선 고정하고, vector detail은 별도 후속 설계에서 다룬다.

---

## 3. Storage Principles

1. **Object for Full Artifact, DB for Operational Metadata**: raw snapshot과 parsed text 본문은 object storage에 두고, 운영 조회/추적에 필요한 식별자와 메타데이터는 DB에 둔다.
2. **Evidence First**: canonical field trace가 가능하도록 chunk metadata와 excerpt는 DB에서 직접 조회 가능해야 한다.
3. **Idempotent Reuse**: 동일 `source identity + fingerprint`는 중복 snapshot 생성을 피할 수 있어야 한다.
4. **Trace Without Public Exposure**: evidence는 저장하되 공개 사용자에게 직접 노출하지 않는다.
5. **Retention Hook Before Retention Policy**: exact 보관기간이 아직 미확정이어도 later archival/purge를 위한 분류 필드는 먼저 둔다.

---

## 4. Storage Boundary by Artifact

| Artifact | System of Record | Recommended Storage | Why |
|---|---|---|---|
| source identity / discovery metadata | FPDS DB | relational row | dedupe, run scoping, admin search 기준이기 때문이다. |
| raw HTML/PDF snapshot | FPDS object storage | immutable object | 원문 보존과 추후 재파싱을 위해서다. |
| fetch metadata / checksum / fingerprint | FPDS DB | relational row | idempotency와 failure analysis에 필요하다. |
| parsed text full body | FPDS object storage | immutable object or object-backed blob | 재파싱 없이 downstream 재사용하기 위해서다. |
| parse metadata | FPDS DB | relational row | parser version, quality note, trace에 필요하다. |
| evidence chunk metadata | FPDS DB | relational row | retrieval filter, trace viewer, review UI에 직접 필요하다. |
| evidence chunk excerpt | FPDS DB | inline text | admin trace와 field evidence link 조회를 가볍게 만들기 위해서다. |
| field-to-evidence link | FPDS DB | relational row | candidate/product traceability의 핵심이기 때문이다. |

---

## 5. Canonical Storage Layout

### 5.1 Relational Metadata Layer

아래 엔터티는 DB에 저장하는 것을 baseline으로 본다.

- `source_document`
- `run_source_item`
- `source_snapshot`
- `parsed_document`
- `evidence_chunk`
- `field_evidence_link`

필수 메타데이터 예시:
- identity: `source_document_id`, `snapshot_id`, `parsed_document_id`, `evidence_chunk_id`
- lineage: `source_document_id -> snapshot_id -> parsed_document_id -> evidence_chunk_id`
- auditability: created/parsed/fetched timestamp, parser version, fetch status
- retrievalability: page/section anchor, chunk index, excerpt, source language
- idempotency: checksum, fingerprint

### 5.2 Object Storage Layer

object storage에 저장하는 baseline artifact는 아래와 같다.

- raw HTML body
- raw PDF binary
- parsed text full body
- optional parser intermediate artifact

권장 object key shape:

```text
{env}/snapshots/{country_code}/{bank_code}/{source_document_id}/{snapshot_id}/raw
{env}/parsed/{country_code}/{bank_code}/{source_document_id}/{parsed_document_id}/parsed.txt
{env}/parsed/{country_code}/{bank_code}/{source_document_id}/{parsed_document_id}/metadata.json
```

위 key shape는 논리 예시다.  
exact file naming, compression, checksum placement는 infra implementation에서 바뀔 수 있다.

---

## 6. Chunk and Evidence Strategy

### 6.1 Chunk Persistence Baseline

`evidence_chunk`는 아래 필드를 최소로 가져야 한다.

- `parsed_document_id`
- `chunk_index`
- `anchor_type`
- `anchor_value`
- `page_no` if applicable
- `evidence_excerpt`
- `source_language`
- `chunk_char_start`
- `chunk_char_end`

### 6.2 Why Excerpt Lives in DB

excerpt를 DB에 직접 두는 baseline 이유는 아래와 같다.

- admin trace viewer에서 object fetch 없이 빠르게 표시할 수 있다.
- field_evidence_link가 chunk의 핵심 부분을 직접 인용할 수 있다.
- retrieval/vector backend가 바뀌어도 trace UX가 깨지지 않는다.

### 6.3 What Does Not Need Inline DB Storage

아래는 object-backed reference로 충분하다.

- full raw HTML/PDF body
- parsed text full body
- parser intermediate diagnostic blob
- future embedding payload raw artifact

---

## 7. Integrity, Access, and Retention Baseline

### 7.1 Integrity Rules

- `source_snapshot` row는 checksum/fingerprint를 반드시 가진다.
- object key와 DB metadata row는 immutable lineage를 유지해야 한다.
- parsed artifact는 `snapshot_id` 기준으로 파생됨을 추적해야 한다.
- chunk는 `parsed_document_id` 없이는 존재할 수 없다.

### 7.2 Access Boundary

- public web/API는 raw snapshot, parsed text, evidence chunk object에 직접 접근하지 않는다.
- admin trace와 internal workflow만 evidence metadata와 excerpt를 조회한다.
- object storage는 signed internal access 또는 equivalent private access를 기본으로 한다.

### 7.3 Retention Baseline

- exact retention 기간은 아직 닫지 않는다.
- raw snapshot, parsed text, evidence metadata에는 later archival/purge를 위한 `retention_class` 또는 equivalent hook를 둘 수 있어야 한다.
- Phase 1 baseline에서는 short TTL로 자동 삭제하지 않는 것을 기본 원칙으로 본다.

---

## 8. Failure and Reprocessing Rules

- fetch 실패는 source 단위 retry 대상이다.
- parse 실패가 있어도 이미 저장된 raw snapshot은 재사용 가능해야 한다.
- 동일 fingerprint면 downstream 재생성 없이 기존 snapshot/parsed/chunk를 재사용할 수 있다.
- chunk regeneration이 필요하면 기존 parsed artifact lineage를 유지하면서 새 `parsed_document` 또는 equivalent version으로 분기할 수 있어야 한다.

---

## 9. Open Items Not Blocking This Strategy

| Area | Open Item | Follow-Up WBS | Why It Does Not Block 1.4.3 |
|---|---|---|---|
| Encryption | KMS/provider-specific encryption detail | later infra/security setup | object vs metadata boundary는 먼저 고정 가능하다. |
| Retention | exact day count, archive tier, purge schedule | later security/ops | retention hook만 먼저 두면 된다. |
| Egress Security | exact SSRF allowlist, private IP deny detail | `1.6.5` | storage layout과 network policy는 분리 가능하다. |
| Vendor Detail | S3-compatible provider, bucket class, compression policy | implementation stage | logical storage strategy만 먼저 고정하면 된다. |

---

## 10. Interfaces and Follow-On Work Unlocked

- `1.4.4`: retrieval/vector 대상 artifact 범위 고정
- `1.5.2`: admin trace API payload source 정리
- `1.5.3`: internal evidence retrieval interface 정리
- `2.4`: object storage/evidence bucket 준비
- `3.2`: snapshot 수집 구현
- `3.3`: parsing/chunking 구현
- `4.4`: evidence trace viewer 구현

---

## 11. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.4.3 | Sections 2-10 |

---

## 12. Change History

| Date | Change |
|---|---|
| 2026-04-01 | Initial source snapshot and evidence storage strategy created for WBS 1.4.3 |
