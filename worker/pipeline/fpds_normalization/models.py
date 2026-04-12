from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizationExtractedField:
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


@dataclass(frozen=True)
class NormalizationEvidenceLink:
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


@dataclass(frozen=True)
class NormalizationArtifactLookup:
    source_document_id: str
    snapshot_id: str
    parsed_document_id: str
    extraction_model_execution_id: str
    extracted_storage_key: str
    extraction_metadata_storage_key: str | None
    bank_code: str
    country_code: str
    source_type: str
    source_language: str
    source_metadata: dict[str, object]


@dataclass(frozen=True)
class NormalizationInput:
    source_id: str | None
    source_document_id: str
    snapshot_id: str
    parsed_document_id: str
    extraction_model_execution_id: str
    extracted_storage_key: str
    metadata_storage_key: str | None
    bank_code: str
    country_code: str
    source_type: str
    source_language: str
    source_metadata: dict[str, object]
    schema_context: dict[str, object]
    extracted_fields: list[NormalizationExtractedField]
    evidence_links: list[NormalizationEvidenceLink]
    runtime_notes: list[str]


@dataclass(frozen=True)
class NormalizationSourceResult:
    source_id: str | None
    source_document_id: str
    snapshot_id: str
    parsed_document_id: str
    extraction_model_execution_id: str
    normalization_action: str
    candidate_id: str | None
    normalization_model_execution_id: str
    normalized_storage_key: str | None
    metadata_storage_key: str | None
    validation_status: str | None
    validation_issue_codes: list[str]
    source_confidence: float | None
    runtime_notes: list[str]
    error_summary: str | None
    normalized_candidate_record: dict[str, object] | None
    field_evidence_link_records: list[dict[str, object]]
    model_execution_record: dict[str, object]
    usage_record: dict[str, object] | None
    run_source_item_record: dict[str, object]


@dataclass(frozen=True)
class NormalizationResult:
    run_id: str
    correlation_id: str | None
    request_id: str | None
    source_results: list[NormalizationSourceResult]
    partial_completion_flag: bool

    def to_dict(self) -> dict[str, object]:
        stored_count = sum(1 for item in self.source_results if item.normalization_action == "stored")
        failed_count = sum(1 for item in self.source_results if item.normalization_action == "failed")
        evidence_link_count = sum(len(item.field_evidence_link_records) for item in self.source_results)
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "partial_completion_flag": self.partial_completion_flag,
            "stats": {
                "source_total": len(self.source_results),
                "stored_count": stored_count,
                "failed_count": failed_count,
                "candidate_count": stored_count,
                "field_evidence_link_count": evidence_link_count,
            },
            "source_results": [
                {
                    "source_id": item.source_id,
                    "source_document_id": item.source_document_id,
                    "snapshot_id": item.snapshot_id,
                    "parsed_document_id": item.parsed_document_id,
                    "extraction_model_execution_id": item.extraction_model_execution_id,
                    "normalization_action": item.normalization_action,
                    "candidate_id": item.candidate_id,
                    "normalization_model_execution_id": item.normalization_model_execution_id,
                    "normalized_storage_key": item.normalized_storage_key,
                    "metadata_storage_key": item.metadata_storage_key,
                    "validation_status": item.validation_status,
                    "validation_issue_codes": item.validation_issue_codes,
                    "source_confidence": item.source_confidence,
                    "runtime_notes": item.runtime_notes,
                    "error_summary": item.error_summary,
                    "field_evidence_link_count": len(item.field_evidence_link_records),
                    "run_source_item_record": item.run_source_item_record,
                }
                for item in self.source_results
            ],
        }
