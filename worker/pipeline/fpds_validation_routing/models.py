from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationArtifactLookup:
    source_document_id: str
    snapshot_id: str
    parsed_document_id: str
    normalization_model_execution_id: str
    normalized_storage_key: str
    normalization_metadata_storage_key: str | None
    bank_code: str
    country_code: str
    source_type: str
    source_language: str
    source_metadata: dict[str, object]


@dataclass(frozen=True)
class ValidationEvidenceLink:
    field_evidence_link_id: str | None
    candidate_id: str | None
    product_version_id: str | None
    evidence_chunk_id: str
    source_document_id: str
    field_name: str
    candidate_value: str
    citation_confidence: float


@dataclass(frozen=True)
class ValidationRoutingConfig:
    routing_mode: str
    auto_approve_min_confidence: float
    review_warning_confidence_floor: float
    force_review_issue_codes: set[str]


@dataclass(frozen=True)
class ValidationInput:
    source_id: str | None
    source_document_id: str
    snapshot_id: str
    parsed_document_id: str
    candidate_id: str
    candidate_run_id: str
    normalization_model_execution_id: str
    normalized_storage_key: str
    metadata_storage_key: str | None
    bank_code: str
    country_code: str
    source_type: str
    source_language: str
    source_metadata: dict[str, object]
    normalized_candidate_record: dict[str, object]
    field_evidence_links: list[ValidationEvidenceLink]
    runtime_notes: list[str]


@dataclass(frozen=True)
class ValidationSourceResult:
    source_id: str | None
    source_document_id: str
    snapshot_id: str
    parsed_document_id: str
    candidate_id: str
    candidate_run_id: str
    validation_action: str
    validation_model_execution_id: str
    validation_storage_key: str | None
    metadata_storage_key: str | None
    review_task_id: str | None
    validation_status: str | None
    validation_issue_codes: list[str]
    source_confidence: float | None
    candidate_state: str | None
    review_reason_code: str | None
    queue_reason_codes: list[str]
    runtime_notes: list[str]
    error_summary: str | None
    candidate_update_record: dict[str, object] | None
    review_task_record: dict[str, object] | None
    model_execution_record: dict[str, object]
    usage_record: dict[str, object] | None
    run_source_item_record: dict[str, object]


@dataclass(frozen=True)
class ValidationResult:
    run_id: str
    correlation_id: str | None
    request_id: str | None
    routing_mode: str
    source_results: list[ValidationSourceResult]
    partial_completion_flag: bool

    def to_dict(self) -> dict[str, object]:
        queued_count = sum(1 for item in self.source_results if item.validation_action == "review_queued")
        auto_validated_count = sum(1 for item in self.source_results if item.validation_action == "auto_validated")
        failed_count = sum(1 for item in self.source_results if item.validation_action == "failed")
        review_task_count = sum(1 for item in self.source_results if item.review_task_record is not None)
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "routing_mode": self.routing_mode,
            "partial_completion_flag": self.partial_completion_flag,
            "stats": {
                "source_total": len(self.source_results),
                "queued_count": queued_count,
                "auto_validated_count": auto_validated_count,
                "failed_count": failed_count,
                "review_task_count": review_task_count,
            },
            "source_results": [
                {
                    "source_id": item.source_id,
                    "source_document_id": item.source_document_id,
                    "snapshot_id": item.snapshot_id,
                    "parsed_document_id": item.parsed_document_id,
                    "candidate_id": item.candidate_id,
                    "candidate_run_id": item.candidate_run_id,
                    "validation_action": item.validation_action,
                    "validation_model_execution_id": item.validation_model_execution_id,
                    "validation_storage_key": item.validation_storage_key,
                    "metadata_storage_key": item.metadata_storage_key,
                    "review_task_id": item.review_task_id,
                    "validation_status": item.validation_status,
                    "validation_issue_codes": item.validation_issue_codes,
                    "source_confidence": item.source_confidence,
                    "candidate_state": item.candidate_state,
                    "review_reason_code": item.review_reason_code,
                    "queue_reason_codes": item.queue_reason_codes,
                    "runtime_notes": item.runtime_notes,
                    "error_summary": item.error_summary,
                    "run_source_item_record": item.run_source_item_record,
                }
                for item in self.source_results
            ],
        }
