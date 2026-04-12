from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParseSourceSnapshot:
    snapshot_id: str
    source_document_id: str
    object_storage_key: str
    content_type: str
    source_language: str
    bank_code: str
    country_code: str
    source_id: str | None = None


@dataclass(frozen=True)
class ExistingParsedDocumentRecord:
    parsed_document_id: str
    snapshot_id: str
    parsed_storage_key: str
    parser_version: str
    parse_quality_note: str | None
    parser_metadata: dict[str, object]
    retention_class: str
    parsed_at: str
    chunk_count: int


@dataclass(frozen=True)
class ParsedSegment:
    anchor_type: str
    anchor_value: str | None
    page_no: int | None
    text: str
    char_start: int
    char_end: int


@dataclass(frozen=True)
class ParsedArtifact:
    parser_name: str
    parser_version: str
    full_text: str
    parse_quality_note: str | None
    parser_metadata: dict[str, object]
    segments: list[ParsedSegment]


@dataclass(frozen=True)
class EvidenceChunkRecord:
    evidence_chunk_id: str
    parsed_document_id: str
    chunk_index: int
    anchor_type: str
    anchor_value: str | None
    page_no: int | None
    source_language: str
    chunk_char_start: int
    chunk_char_end: int
    evidence_excerpt: str
    retrieval_metadata: dict[str, object]

    def to_record(self) -> dict[str, object]:
        return {
            "evidence_chunk_id": self.evidence_chunk_id,
            "parsed_document_id": self.parsed_document_id,
            "chunk_index": self.chunk_index,
            "anchor_type": self.anchor_type,
            "anchor_value": self.anchor_value,
            "page_no": self.page_no,
            "source_language": self.source_language,
            "chunk_char_start": self.chunk_char_start,
            "chunk_char_end": self.chunk_char_end,
            "evidence_excerpt": self.evidence_excerpt,
            "retrieval_metadata": self.retrieval_metadata,
        }


@dataclass(frozen=True)
class ParseChunkSourceResult:
    source_id: str | None
    source_document_id: str
    snapshot_id: str
    parse_action: str
    parsed_document_id: str | None
    parsed_storage_key: str | None
    metadata_storage_key: str | None
    chunk_count: int
    parse_quality_note: str | None
    error_summary: str | None
    parsed_document_record: dict[str, object] | None
    evidence_chunk_records: list[dict[str, object]]
    run_source_item_record: dict[str, object]


@dataclass(frozen=True)
class ParseChunkResult:
    run_id: str
    correlation_id: str | None
    request_id: str | None
    source_results: list[ParseChunkSourceResult]
    partial_completion_flag: bool

    def to_dict(self) -> dict[str, object]:
        stored_count = sum(1 for item in self.source_results if item.parse_action == "stored")
        reused_count = sum(1 for item in self.source_results if item.parse_action == "reused")
        failed_count = sum(1 for item in self.source_results if item.parse_action == "failed")
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "partial_completion_flag": self.partial_completion_flag,
            "stats": {
                "source_total": len(self.source_results),
                "stored_count": stored_count,
                "reused_count": reused_count,
                "failed_count": failed_count,
            },
            "source_results": [
                {
                    "source_id": item.source_id,
                    "source_document_id": item.source_document_id,
                    "snapshot_id": item.snapshot_id,
                    "parse_action": item.parse_action,
                    "parsed_document_id": item.parsed_document_id,
                    "parsed_storage_key": item.parsed_storage_key,
                    "metadata_storage_key": item.metadata_storage_key,
                    "chunk_count": item.chunk_count,
                    "parse_quality_note": item.parse_quality_note,
                    "error_summary": item.error_summary,
                    "run_source_item_record": item.run_source_item_record,
                }
                for item in self.source_results
            ],
        }
