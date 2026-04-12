from __future__ import annotations

from dataclasses import dataclass

from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate


@dataclass(frozen=True)
class ExtractionDocumentContext:
    parsed_document_id: str
    source_document_id: str
    snapshot_id: str
    bank_code: str
    country_code: str
    source_type: str
    source_language: str
    source_metadata: dict[str, object]
    source_id: str | None = None


@dataclass(frozen=True)
class ExtractionInput:
    context: ExtractionDocumentContext
    candidates: list[EvidenceChunkCandidate]


@dataclass(frozen=True)
class ExtractedFieldCandidate:
    field_name: str
    candidate_value: object
    value_type: str
    confidence: float
    extraction_method: str
    source_document_id: str
    source_snapshot_id: str
    evidence_chunk_id: str | None
    evidence_text_excerpt: str | None
    anchor_type: str | None
    anchor_value: str | None
    page_no: int | None
    chunk_index: int | None
    field_metadata: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "field_name": self.field_name,
            "candidate_value": self.candidate_value,
            "value_type": self.value_type,
            "confidence": self.confidence,
            "extraction_method": self.extraction_method,
            "source_document_id": self.source_document_id,
            "source_snapshot_id": self.source_snapshot_id,
            "evidence_chunk_id": self.evidence_chunk_id,
            "evidence_text_excerpt": self.evidence_text_excerpt,
            "anchor_type": self.anchor_type,
            "anchor_value": self.anchor_value,
            "page_no": self.page_no,
            "chunk_index": self.chunk_index,
            "field_metadata": self.field_metadata,
        }


@dataclass(frozen=True)
class EvidenceLinkDraft:
    field_name: str
    candidate_value: str
    evidence_chunk_id: str
    evidence_text_excerpt: str
    source_document_id: str
    source_snapshot_id: str
    citation_confidence: float
    model_execution_id: str | None
    anchor_type: str | None
    anchor_value: str | None
    page_no: int | None
    chunk_index: int | None

    def to_dict(self) -> dict[str, object]:
        return {
            "field_name": self.field_name,
            "candidate_value": self.candidate_value,
            "evidence_chunk_id": self.evidence_chunk_id,
            "evidence_text_excerpt": self.evidence_text_excerpt,
            "source_document_id": self.source_document_id,
            "source_snapshot_id": self.source_snapshot_id,
            "citation_confidence": self.citation_confidence,
            "model_execution_id": self.model_execution_id,
            "anchor_type": self.anchor_type,
            "anchor_value": self.anchor_value,
            "page_no": self.page_no,
            "chunk_index": self.chunk_index,
        }


@dataclass(frozen=True)
class ExtractionSourceResult:
    source_id: str | None
    source_document_id: str
    snapshot_id: str
    parsed_document_id: str
    extraction_action: str
    model_execution_id: str
    extracted_storage_key: str | None
    metadata_storage_key: str | None
    extracted_fields: list[ExtractedFieldCandidate]
    evidence_links: list[EvidenceLinkDraft]
    runtime_notes: list[str]
    error_summary: str | None
    model_execution_record: dict[str, object]
    usage_record: dict[str, object] | None
    run_source_item_record: dict[str, object]


@dataclass(frozen=True)
class ExtractionResult:
    run_id: str
    correlation_id: str | None
    request_id: str | None
    source_results: list[ExtractionSourceResult]
    partial_completion_flag: bool

    def to_dict(self) -> dict[str, object]:
        stored_count = sum(1 for item in self.source_results if item.extraction_action == "stored")
        failed_count = sum(1 for item in self.source_results if item.extraction_action == "failed")
        extracted_field_count = sum(len(item.extracted_fields) for item in self.source_results)
        evidence_link_count = sum(len(item.evidence_links) for item in self.source_results)
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "partial_completion_flag": self.partial_completion_flag,
            "stats": {
                "source_total": len(self.source_results),
                "stored_count": stored_count,
                "failed_count": failed_count,
                "extracted_field_count": extracted_field_count,
                "evidence_link_count": evidence_link_count,
            },
            "source_results": [
                {
                    "source_id": item.source_id,
                    "source_document_id": item.source_document_id,
                    "snapshot_id": item.snapshot_id,
                    "parsed_document_id": item.parsed_document_id,
                    "extraction_action": item.extraction_action,
                    "model_execution_id": item.model_execution_id,
                    "extracted_storage_key": item.extracted_storage_key,
                    "metadata_storage_key": item.metadata_storage_key,
                    "runtime_notes": item.runtime_notes,
                    "error_summary": item.error_summary,
                    "extracted_fields": [field.to_dict() for field in item.extracted_fields],
                    "evidence_links": [link.to_dict() for link in item.evidence_links],
                    "run_source_item_record": item.run_source_item_record,
                }
                for item in self.source_results
            ],
        }
