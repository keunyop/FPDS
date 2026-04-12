from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetadataFilters:
    bank_code: str | None = None
    country_code: str | None = None
    source_language: str | None = None
    source_types: tuple[str, ...] = ()
    source_document_ids: tuple[str, ...] = ()
    anchor_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceRetrievalRequest:
    correlation_id: str | None
    run_id: str
    parsed_document_id: str
    field_names: list[str]
    metadata_filters: MetadataFilters
    retrieval_mode: str
    max_matches_per_field: int = 5


@dataclass(frozen=True)
class EvidenceChunkCandidate:
    evidence_chunk_id: str
    parsed_document_id: str
    chunk_index: int
    anchor_type: str
    anchor_value: str | None
    page_no: int | None
    source_language: str
    evidence_excerpt: str
    retrieval_metadata: dict[str, object]
    source_document_id: str
    source_snapshot_id: str
    bank_code: str
    country_code: str
    source_type: str


@dataclass(frozen=True)
class EvidenceMatch:
    evidence_chunk_id: str
    field_name: str
    score: float
    retrieval_mode: str
    evidence_text_excerpt: str
    source_document_id: str
    source_snapshot_id: str
    model_execution_id: str | None
    parsed_document_id: str
    anchor_type: str
    anchor_value: str | None
    page_no: int | None
    chunk_index: int
    match_metadata: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "evidence_chunk_id": self.evidence_chunk_id,
            "field_name": self.field_name,
            "score": self.score,
            "retrieval_mode": self.retrieval_mode,
            "evidence_text_excerpt": self.evidence_text_excerpt,
            "source_document_id": self.source_document_id,
            "source_snapshot_id": self.source_snapshot_id,
            "model_execution_id": self.model_execution_id,
            "parsed_document_id": self.parsed_document_id,
            "anchor_type": self.anchor_type,
            "anchor_value": self.anchor_value,
            "page_no": self.page_no,
            "chunk_index": self.chunk_index,
            "match_metadata": self.match_metadata,
        }


@dataclass(frozen=True)
class EvidenceRetrievalResult:
    correlation_id: str | None
    run_id: str
    parsed_document_id: str
    requested_retrieval_mode: str
    applied_retrieval_mode: str
    matches: list[EvidenceMatch]
    runtime_notes: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "correlation_id": self.correlation_id,
            "run_id": self.run_id,
            "parsed_document_id": self.parsed_document_id,
            "requested_retrieval_mode": self.requested_retrieval_mode,
            "applied_retrieval_mode": self.applied_retrieval_mode,
            "runtime_notes": self.runtime_notes,
            "matches": [match.to_dict() for match in self.matches],
        }


@dataclass(frozen=True)
class ParsedDocumentLookup:
    parsed_document_id: str
    source_document_id: str
    snapshot_id: str
