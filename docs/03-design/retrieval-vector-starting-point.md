# FPDS Retrieval and Vector Starting Point

Version: 1.0
Date: 2026-04-01
Status: Approved Baseline for WBS 1.4.4
Source Documents:
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`
- `docs/01-planning/plan.md`
- `docs/01-planning/WBS.md`
- `docs/03-design/source-snapshot-evidence-storage-strategy.md`
- `docs/03-design/system-context-diagram.md`
- `docs/03-design/erd-draft.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/raid-log.md`

---

## Current Retrieval Supersession - 2026-08-13

Decision `D044` removes `evidence_chunk_embedding` and stops embedding writes.
The current worker always uses metadata/lexical retrieval over the bounded
evidence set. The pgvector design below is retained as historical exploration,
not as a live schema or runtime requirement.

---

## 1. Purpose

이 문서는 `WBS 1.4.4 retrieval/vector 시작점 결정`을 닫기 위한 기준 문서다.

목적:
- Phase 1에서 retrieval-ready evidence 위에 어떤 vector starting point를 둘지 결정한다.
- retrieval 범위를 어디까지로 제한할지 정한다.
- separate vector service 도입 전의 안전한 초기 아키텍처를 고정한다.

---

## 2. Decision

FPDS의 Phase 1 retrieval/vector starting point는 아래로 결정한다.

1. vector backend의 초기 선택은 `Postgres + pgvector`다.
2. vector scope는 `evidence_chunk` embedding과 retrieval metadata에 한정한다.
3. raw snapshot, parsed text full body, canonical product, publish data는 vector index 대상에서 제외한다.
4. retrieval path는 `metadata filter first + pgvector similarity second + excerpt return`의 hybrid baseline으로 둔다.
5. dev 또는 low-volume 환경에서 pgvector extension이 즉시 준비되지 않더라도 metadata-only retrieval fallback은 허용한다.

---

## 3. Why This Baseline

이 결정을 채택한 이유는 아래와 같다.

- PRD suggested stack이 Phase 1 starting point로 pgvector를 이미 권장하고 있다.
- Phase 1 요구사항은 evidence retrieval과 admin trace를 안정적으로 지원하는 것이지, 대규모 semantic search 플랫폼 구축이 아니다.
- separate vector service를 지금 도입하면 infra, ops, auth, cost 복잡도가 앞서간다.
- ERD와 system context가 이미 `evidence_chunk` 중심 retrieval 구조를 전제로 정리돼 있다.

---

## 4. Included Scope

### 4.1 Retrieval Target

초기 vectorization 대상은 아래로 한정한다.

- `evidence_chunk.evidence_excerpt` 또는 equivalent normalized chunk text
- chunk anchor metadata
- source language / bank / country / product type filter metadata

### 4.2 Retrieval Use Cases

이번 baseline이 지원해야 하는 use case는 아래다.

- extraction 단계에서 관련 evidence 후보 chunk 찾기
- validation/review 지원용 evidence recall
- admin trace drilldown의 chunk-level source lookup 보조

### 4.3 Explicitly Out of Scope

아래는 현재 starting point 범위 밖이다.

- public-facing semantic product search
- source snapshot binary 검색
- full parsed document embedding
- product-level recommendation embedding
- separate ANN cluster 또는 dedicated vector database

---

## 5. Retrieval Flow Baseline

권장 초기 흐름은 아래와 같다.

1. run/source/product-type/bank/country 기준으로 deterministic metadata filter를 먼저 건다.
2. filtered chunk 집합에 대해 pgvector similarity search를 적용한다.
3. top-K chunk 후보를 excerpt + anchor metadata와 함께 반환한다.
4. downstream extraction/validation은 최종 evidence 선택과 field linkage를 별도로 결정한다.

핵심 원칙:
- vector는 metadata filter를 대체하지 않는다.
- traceability를 위해 최종 출력은 항상 `evidence_chunk_id`와 anchor를 포함해야 한다.
- retrieval failure는 review fallback을 막아서는 안 된다.

---

## 6. Storage and Schema Boundary

### 6.1 Logical Placement

- `evidence_chunk`는 system of record다.
- vector embedding은 `evidence_chunk`의 보조 retrieval index다.
- canonical truth는 여전히 relational metadata와 object storage lineage에 있다.

### 6.2 Recommended Physical Pattern

권장 physical pattern:

- `evidence_chunk` metadata는 Postgres relational table
- chunk embedding vector는 same Postgres cluster의 `pgvector` column 또는 closely coupled side table
- exact index type와 dimension은 implementation 시점에 결정

### 6.3 Why Same-Store First

- 초기 ops 단순화
- transactional metadata proximity
- admin trace와 retrieval debug의 join simplicity
- Phase 1 scale에 맞는 현실적 starting point

---

## 7. Fallback and Evolution Rules

### 7.1 Fallback Rule

- pgvector가 준비되지 않은 환경에서는 metadata-only retrieval을 허용한다.
- 이 경우 extraction quality 저하는 review fallback으로 흡수한다.
- metadata-only mode는 Prototype/early dev unblock용이며 Phase 1 target architecture의 대체가 아니다.

### 7.2 Evolution Rule

아래 조건이 생기면 vector backend 분리를 검토할 수 있다.

- chunk volume이 Postgres index maintenance를 과도하게 압박하는 경우
- retrieval latency가 Phase 1 운영 허용 범위를 지속적으로 넘는 경우
- multi-tenant external API semantic retrieval이 실제로 필요해지는 경우
- embedding lifecycle와 cost control이 별도 pipeline을 요구하는 경우

---

## 8. Open Items Not Blocking This Decision

| Area | Open Item | Follow-Up | Why It Does Not Block 1.4.4 |
|---|---|---|---|
| Embedding Model | exact model id and dimension | implementation/config | backend starting point와 separate concern이다. |
| Re-ranking | lexical blend, reranker, threshold tuning | later tuning | initial hybrid baseline만 있으면 된다. |
| Infra | exact Postgres extension provisioning by env | `docs/03-design/environment-separation-strategy.md` and infra setup | logical choice는 먼저 고정 가능하다. |
| Cost Guardrail | embedding refresh policy and budget cap | later ops policy | architecture starting point를 막지 않는다. |

---

## 9. Interfaces and Follow-On Work Unlocked

- `1.5.3`: evidence retrieval interface shape 고정
- `3.4`: evidence retrieval 구조 구현
- `4.4`: trace viewer retrieval support
- `5.1`~`5.5`: Big 5 확장 시 chunk retrieval reuse

---

## 10. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| 1.4.4 | Sections 2-9 |

---

## 11. Change History

| Date | Change |
|---|---|
| 2026-04-01 | Initial retrieval/vector starting point decision created for WBS 1.4.4 |
| 2026-04-24 | Added implementation addendum for pgvector-backed evidence chunk embeddings and metadata-first vector-assisted retrieval |

---

## 12. Implementation Addendum - Evidence Chunk Vector Bootstrap

Status: Approved implementation direction for the first vector-assisted retrieval slice.

### 12.1 Scope

The first implementation slice uses `Postgres + pgvector` only as an evidence retrieval aid.

Included:
- `evidence_chunk` remains the system of record.
- vector storage is a side table keyed by `evidence_chunk_id`.
- vector-assisted retrieval applies deterministic metadata filters before vector ranking.
- vector output still returns `evidence_chunk_id`, excerpt, source references, and anchor metadata.
- if pgvector, the side table, or embedding rows are missing, retrieval falls back to `metadata-only`.

Excluded:
- public semantic product search
- recommendation or personalization
- canonical product embedding
- full parsed-document embedding
- separate vector service
- public exposure of evidence trace or vector metadata

### 12.2 Physical Storage

The implementation adds `evidence_chunk_embedding` through a follow-on migration.

Required fields:
- `evidence_chunk_embedding_id`
- `evidence_chunk_id`
- `vector_namespace`
- `embedding_model_id`
- `embedding_dimensions`
- `embedding_source`
- `embedding_source_text_hash`
- `embedding`
- `embedding_metadata`
- timestamps

The first committed vector shape is `vector(64)` for a deterministic lexical bootstrap embedding. This is intentionally small and local so worker tests and dev runs do not require a live embedding provider. A later production semantic embedding model may replace the model id and dimensions through a new migration and config update.

### 12.3 Retrieval Behavior

`retrieval_mode=vector-assisted` behaves as follows:

1. Resolve field-specific query text from the canonical field name and retrieval hints.
2. Apply metadata filters for parsed document, bank, country, language, source type, source document, and anchor type.
3. Use pgvector cosine distance to rank candidate chunks within the filtered set.
4. Blend vector score with existing lexical field scoring.
5. Return the same match contract used by metadata-only retrieval.

Fallback rule:
- If vector rows are unavailable, the worker returns `applied_retrieval_mode=metadata-only` with a runtime note.
- Fallback is not a failure because reviewability and evidence trace remain intact.

### 12.4 Efficiency Target

The expected benefit is not broad database speed alone. The target is higher-quality evidence selection before extraction:

- fewer irrelevant chunks sent to extraction
- better recall when banks use different wording for the same field
- lower noisy long-text carryover into normalized candidates
- fewer manual review cases caused by weak evidence linkage
- less per-bank keyword-rule expansion pressure as Big 5 coverage grows

### 12.5 Follow-Up Decision Points

The following remain explicit future decisions:

- production embedding provider and model id
- production embedding dimension and replacement migration
- embedding refresh policy when parsed chunks change
- quality thresholds for vector score vs lexical score
- whether admin trace search needs a separate operator-facing semantic lookup
