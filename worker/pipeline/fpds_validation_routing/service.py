from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re

from .models import (
    ValidationEvidenceLink,
    ValidationInput,
    ValidationResult,
    ValidationRoutingConfig,
    ValidationSourceResult,
)
from .storage import ValidationRoutingStorageConfig

_ERROR_ISSUE_CODES = {
    "required_field_missing",
    "invalid_taxonomy_code",
    "invalid_numeric_range",
    "invalid_term_value",
    "inconsistent_cross_field_logic",
}
_NUMERIC_RANGE_FIELDS = {
    "monthly_fee",
    "public_display_fee",
    "minimum_balance",
    "minimum_deposit",
    "standard_rate",
    "promotional_rate",
    "public_display_rate",
}
_RATE_FIELDS = {"standard_rate", "promotional_rate", "public_display_rate"}
_FEE_FIELDS = {"monthly_fee", "public_display_fee"}
_SUMMARY_MESSAGES = {
    "required_field_missing": "One or more required fields are missing.",
    "invalid_taxonomy_code": "Product taxonomy did not match the active registry.",
    "invalid_numeric_range": "A numeric value was outside the allowed range.",
    "invalid_term_value": "The term value was not valid for canonical storage.",
    "conflicting_evidence": "Multiple evidence links disagree on the same field value.",
    "ambiguous_mapping": "A field could not be mapped with enough certainty.",
    "partial_source_failure": "The candidate was produced from partial or degraded source processing.",
    "inconsistent_cross_field_logic": "Cross-field rules were not internally consistent.",
    "low_confidence": "The overall source confidence was below the routing threshold.",
    "validation_error": "Validation produced one or more error-level issues.",
    "manual_sampling_review": "Prototype routing keeps all candidates in review.",
}


class ValidationRoutingService:
    def __init__(
        self,
        *,
        storage_config: ValidationRoutingStorageConfig,
        object_store,
        agent_name: str = "fpds-heuristic-validator-router",
        model_id: str = "heuristic-validator-router-v1",
    ) -> None:
        self.storage_config = storage_config
        self.object_store = object_store
        self.agent_name = agent_name
        self.model_id = model_id

    def validate_and_route_inputs(
        self,
        *,
        run_id: str,
        inputs: list[ValidationInput],
        taxonomy_registry: dict[str, set[str]],
        routing_config: ValidationRoutingConfig,
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> ValidationResult:
        source_results: list[ValidationSourceResult] = []
        partial_completion_flag = False

        for item in inputs:
            result = self._validate_single_input(
                run_id=run_id,
                item=item,
                taxonomy_registry=taxonomy_registry,
                routing_config=routing_config,
                correlation_id=correlation_id,
                request_id=request_id,
            )
            source_results.append(result)
            if result.validation_action == "failed":
                partial_completion_flag = True

        return ValidationResult(
            run_id=run_id,
            correlation_id=correlation_id,
            request_id=request_id,
            routing_mode=routing_config.routing_mode,
            source_results=source_results,
            partial_completion_flag=partial_completion_flag,
        )

    def _validate_single_input(
        self,
        *,
        run_id: str,
        item: ValidationInput,
        taxonomy_registry: dict[str, set[str]],
        routing_config: ValidationRoutingConfig,
        correlation_id: str | None,
        request_id: str | None,
    ) -> ValidationSourceResult:
        started_at = _utc_now_iso()
        validation_model_execution_id = _build_model_execution_id(run_id=run_id, candidate_id=item.candidate_id)
        try:
            candidate_before = dict(item.normalized_candidate_record)
            candidate_payload = dict(candidate_before.get("candidate_payload", {}))

            validation_issue_codes = _compute_validation_issue_codes(
                candidate_record=candidate_before,
                candidate_payload=candidate_payload,
                field_evidence_links=item.field_evidence_links,
                runtime_notes=item.runtime_notes,
                taxonomy_registry=taxonomy_registry,
            )
            validation_status = _resolve_validation_status(validation_issue_codes)
            source_confidence = _compute_source_confidence(
                candidate_record=candidate_before,
                candidate_payload=candidate_payload,
                field_evidence_links=item.field_evidence_links,
                validation_status=validation_status,
                validation_issue_codes=validation_issue_codes,
                runtime_notes=item.runtime_notes,
            )
            route_decision = _route_candidate(
                validation_status=validation_status,
                validation_issue_codes=validation_issue_codes,
                source_confidence=source_confidence,
                routing_config=routing_config,
            )
            review_task_id = _build_review_task_id(item.candidate_id) if route_decision["review_required"] else None
            issue_summary = _build_issue_summary(
                validation_issue_codes=validation_issue_codes,
                queue_reason_codes=route_decision["queue_reason_codes"],
            )

            updated_candidate_record = {
                "candidate_id": item.candidate_id,
                "candidate_state": route_decision["candidate_state"],
                "validation_status": validation_status,
                "source_confidence": source_confidence,
                "review_reason_code": route_decision["review_reason_code"],
                "validation_issue_codes": validation_issue_codes,
            }

            validation_storage_key = self.storage_config.build_validation_object_key(
                country_code=item.country_code,
                bank_code=item.bank_code,
                source_document_id=item.source_document_id,
                candidate_id=item.candidate_id,
            )
            metadata_storage_key = self.storage_config.build_metadata_object_key(
                country_code=item.country_code,
                bank_code=item.bank_code,
                source_document_id=item.source_document_id,
                candidate_id=item.candidate_id,
            )
            runtime_notes = list(item.runtime_notes)
            if route_decision["review_required"]:
                runtime_notes.append(
                    f"Candidate routed to review in `{routing_config.routing_mode}` mode with primary reason `{route_decision['review_reason_code']}`."
                )
            else:
                runtime_notes.append("Candidate met auto-validation policy and did not create a review task.")

            artifact_payload = _build_validation_artifact_payload(
                run_id=run_id,
                correlation_id=correlation_id,
                request_id=request_id,
                input_item=item,
                validation_model_execution_id=validation_model_execution_id,
                candidate_before=candidate_before,
                candidate_after={**candidate_before, **updated_candidate_record},
                issue_summary=issue_summary,
                review_task_id=review_task_id,
                routing_config=routing_config,
                runtime_notes=runtime_notes,
                started_at=started_at,
            )
            metadata_payload = {
                "candidate_id": item.candidate_id,
                "source_document_id": item.source_document_id,
                "snapshot_id": item.snapshot_id,
                "parsed_document_id": item.parsed_document_id,
                "validation_model_execution_id": validation_model_execution_id,
                "validation_storage_key": validation_storage_key,
                "metadata_storage_key": metadata_storage_key,
                "validation_status": validation_status,
                "validation_issue_codes": validation_issue_codes,
                "source_confidence": source_confidence,
                "candidate_state": route_decision["candidate_state"],
                "review_reason_code": route_decision["review_reason_code"],
                "queue_reason_codes": route_decision["queue_reason_codes"],
                "review_task_id": review_task_id,
                "runtime_notes": runtime_notes,
            }
            self.object_store.put_object_bytes(
                object_key=validation_storage_key,
                data=json.dumps(artifact_payload, indent=2, ensure_ascii=True).encode("utf-8"),
                content_type="application/json",
            )
            self.object_store.put_object_bytes(
                object_key=metadata_storage_key,
                data=json.dumps(metadata_payload, indent=2, ensure_ascii=True).encode("utf-8"),
                content_type="application/json",
            )

            completed_at = _utc_now_iso()
            model_execution_record = _build_model_execution_record(
                model_execution_id=validation_model_execution_id,
                run_id=run_id,
                source_document_id=item.source_document_id,
                execution_status="completed",
                started_at=started_at,
                completed_at=completed_at,
                agent_name=self.agent_name,
                model_id=self.model_id,
                execution_metadata={
                    "candidate_id": item.candidate_id,
                    "candidate_run_id": item.candidate_run_id,
                    "parsed_document_id": item.parsed_document_id,
                    "snapshot_id": item.snapshot_id,
                    "normalization_model_execution_id": item.normalization_model_execution_id,
                    "normalized_storage_key": item.normalized_storage_key,
                    "validation_storage_key": validation_storage_key,
                    "metadata_storage_key": metadata_storage_key,
                    "routing_mode": routing_config.routing_mode,
                    "validation_status": validation_status,
                    "validation_issue_codes": validation_issue_codes,
                    "source_confidence": source_confidence,
                    "candidate_state": route_decision["candidate_state"],
                    "review_reason_code": route_decision["review_reason_code"],
                    "queue_reason_codes": route_decision["queue_reason_codes"],
                    "review_task_id": review_task_id,
                    "field_evidence_link_count": len(item.field_evidence_links),
                    "runtime_notes": runtime_notes,
                },
            )
            usage_record = _build_usage_record(
                run_id=run_id,
                candidate_id=item.candidate_id,
                model_execution_id=validation_model_execution_id,
                recorded_at=completed_at,
                usage_metadata={
                    "usage_mode": "heuristic-no-llm-call",
                    "provider": "local",
                    "model_id": self.model_id,
                },
            )
            review_task_record = None
            if route_decision["review_required"]:
                review_task_record = {
                    "review_task_id": str(review_task_id),
                    "candidate_id": item.candidate_id,
                    "run_id": item.candidate_run_id,
                    "product_id": None,
                    "review_state": "queued",
                    "queue_reason_code": route_decision["review_reason_code"],
                    "issue_summary": issue_summary,
                }
            return ValidationSourceResult(
                source_id=item.source_id,
                source_document_id=item.source_document_id,
                snapshot_id=item.snapshot_id,
                parsed_document_id=item.parsed_document_id,
                candidate_id=item.candidate_id,
                candidate_run_id=item.candidate_run_id,
                validation_action="review_queued" if route_decision["review_required"] else "auto_validated",
                validation_model_execution_id=validation_model_execution_id,
                validation_storage_key=validation_storage_key,
                metadata_storage_key=metadata_storage_key,
                review_task_id=review_task_id,
                validation_status=validation_status,
                validation_issue_codes=validation_issue_codes,
                source_confidence=source_confidence,
                candidate_state=route_decision["candidate_state"],
                review_reason_code=route_decision["review_reason_code"],
                queue_reason_codes=route_decision["queue_reason_codes"],
                runtime_notes=runtime_notes,
                error_summary=None,
                candidate_update_record=updated_candidate_record,
                review_task_record=review_task_record,
                model_execution_record=model_execution_record,
                usage_record=usage_record,
                run_source_item_record=_build_run_source_item_record(
                    run_id=run_id,
                    item=item,
                    validation_model_execution_id=validation_model_execution_id,
                    validation_storage_key=validation_storage_key,
                    metadata_storage_key=metadata_storage_key,
                    validation_status=validation_status,
                    validation_issue_codes=validation_issue_codes,
                    source_confidence=source_confidence,
                    candidate_state=route_decision["candidate_state"],
                    review_reason_code=route_decision["review_reason_code"],
                    queue_reason_codes=route_decision["queue_reason_codes"],
                    review_task_id=review_task_id,
                    runtime_notes=runtime_notes,
                    correlation_id=correlation_id,
                    request_id=request_id,
                    stage_status="completed",
                    error_summary=None,
                ),
            )
        except Exception as exc:
            completed_at = _utc_now_iso()
            error_summary = str(exc)
            return ValidationSourceResult(
                source_id=item.source_id,
                source_document_id=item.source_document_id,
                snapshot_id=item.snapshot_id,
                parsed_document_id=item.parsed_document_id,
                candidate_id=item.candidate_id,
                candidate_run_id=item.candidate_run_id,
                validation_action="failed",
                validation_model_execution_id=validation_model_execution_id,
                validation_storage_key=None,
                metadata_storage_key=None,
                review_task_id=None,
                validation_status=None,
                validation_issue_codes=[],
                source_confidence=None,
                candidate_state=None,
                review_reason_code=None,
                queue_reason_codes=[],
                runtime_notes=[],
                error_summary=error_summary,
                candidate_update_record=None,
                review_task_record=None,
                model_execution_record=_build_model_execution_record(
                    model_execution_id=validation_model_execution_id,
                    run_id=run_id,
                    source_document_id=item.source_document_id,
                    execution_status="failed",
                    started_at=started_at,
                    completed_at=completed_at,
                    agent_name=self.agent_name,
                    model_id=self.model_id,
                    execution_metadata={
                        "candidate_id": item.candidate_id,
                        "candidate_run_id": item.candidate_run_id,
                        "parsed_document_id": item.parsed_document_id,
                        "snapshot_id": item.snapshot_id,
                        "normalization_model_execution_id": item.normalization_model_execution_id,
                        "normalized_storage_key": item.normalized_storage_key,
                        "error_summary": error_summary,
                    },
                ),
                usage_record=None,
                run_source_item_record=_build_run_source_item_record(
                    run_id=run_id,
                    item=item,
                    validation_model_execution_id=validation_model_execution_id,
                    validation_storage_key=None,
                    metadata_storage_key=None,
                    validation_status=None,
                    validation_issue_codes=[],
                    source_confidence=None,
                    candidate_state=None,
                    review_reason_code=None,
                    queue_reason_codes=[],
                    review_task_id=None,
                    runtime_notes=[],
                    correlation_id=correlation_id,
                    request_id=request_id,
                    stage_status="failed",
                    error_summary=error_summary,
                ),
            )


def _compute_validation_issue_codes(
    *,
    candidate_record: dict[str, object],
    candidate_payload: dict[str, object],
    field_evidence_links: list[ValidationEvidenceLink],
    runtime_notes: list[str],
    taxonomy_registry: dict[str, set[str]],
) -> list[str]:
    issues = set(str(item) for item in candidate_record.get("validation_issue_codes", []))

    required_identity = {
        "country_code": candidate_record.get("country_code"),
        "bank_code": candidate_record.get("bank_code"),
        "product_family": candidate_record.get("product_family"),
        "product_type": candidate_record.get("product_type"),
        "product_name": candidate_record.get("product_name"),
        "currency": candidate_record.get("currency"),
        "status": candidate_payload.get("status"),
    }
    if any(value in {None, ""} for value in required_identity.values()):
        issues.add("required_field_missing")

    product_type = _string_or_none(candidate_record.get("product_type"))
    subtype_code = _string_or_none(candidate_record.get("subtype_code"))
    if product_type not in taxonomy_registry:
        issues.add("invalid_taxonomy_code")
    elif subtype_code and subtype_code not in taxonomy_registry[product_type]:
        issues.add("invalid_taxonomy_code")

    source_language = _string_or_none(candidate_record.get("source_language"))
    if source_language and not _looks_like_language_code(source_language):
        issues.add("ambiguous_mapping")

    if not _looks_like_timestamp(_string_or_none(candidate_payload.get("last_verified_at"))):
        issues.add("required_field_missing")

    for field_name in _NUMERIC_RANGE_FIELDS:
        value = candidate_payload.get(field_name)
        if value in {None, ""}:
            continue
        decimal_value = _as_decimal(value)
        if decimal_value is None:
            issues.add("invalid_numeric_range")
            continue
        if field_name in _RATE_FIELDS and not (Decimal("0") <= decimal_value <= Decimal("100")):
            issues.add("invalid_numeric_range")
        if field_name not in _RATE_FIELDS and decimal_value < 0:
            issues.add("invalid_numeric_range")

    term_length_days = candidate_payload.get("term_length_days")
    if term_length_days not in {None, ""}:
        integer_value = _as_int(term_length_days)
        if integer_value is None or integer_value < 1:
            issues.add("invalid_term_value")

    if product_type == "chequing":
        if not any(candidate_payload.get(field_name) not in {None, ""} for field_name in (*_FEE_FIELDS, "fee_waiver_condition")):
            issues.add("required_field_missing")
    if product_type == "savings":
        if not any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
            issues.add("required_field_missing")
    if product_type == "gic":
        if not any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
            issues.add("required_field_missing")
        if candidate_payload.get("minimum_deposit") in {None, ""}:
            issues.add("required_field_missing")
        if candidate_payload.get("term_length_days") in {None, ""} and candidate_payload.get("term_length_text") in {None, ""}:
            issues.add("required_field_missing")

    if _truthy(candidate_payload.get("redeemable_flag")) and _truthy(candidate_payload.get("non_redeemable_flag")):
        issues.add("inconsistent_cross_field_logic")
    if product_type == "gic" and candidate_payload.get("minimum_balance") not in {None, ""} and candidate_payload.get("minimum_deposit") in {None, ""}:
        issues.add("inconsistent_cross_field_logic")

    conflicting_values: dict[str, set[str]] = {}
    for link in field_evidence_links:
        conflicting_values.setdefault(link.field_name, set()).add(link.candidate_value.strip())
    if any(len(values) > 1 for values in conflicting_values.values()):
        issues.add("conflicting_evidence")

    lowered_notes = " ".join(note.lower() for note in runtime_notes)
    if any(token in lowered_notes for token in ("partial", "source failure", "no evidence-linked")):
        issues.add("partial_source_failure")

    return sorted(issues)


def _resolve_validation_status(validation_issue_codes: list[str]) -> str:
    if any(item in _ERROR_ISSUE_CODES for item in validation_issue_codes):
        return "error"
    if validation_issue_codes:
        return "warning"
    return "pass"


def _compute_source_confidence(
    *,
    candidate_record: dict[str, object],
    candidate_payload: dict[str, object],
    field_evidence_links: list[ValidationEvidenceLink],
    validation_status: str,
    validation_issue_codes: list[str],
    runtime_notes: list[str],
) -> float:
    product_type = _string_or_none(candidate_record.get("product_type"))
    required_fields = [
        candidate_record.get("country_code"),
        candidate_record.get("bank_code"),
        candidate_record.get("product_family"),
        candidate_record.get("product_type"),
        candidate_record.get("product_name"),
        candidate_record.get("currency"),
        candidate_payload.get("status"),
        candidate_payload.get("last_verified_at"),
    ]
    completeness = sum(1 for item in required_fields if item not in {None, ""}) / len(required_fields)
    if product_type == "chequing" and any(candidate_payload.get(field_name) not in {None, ""} for field_name in (*_FEE_FIELDS, "fee_waiver_condition")):
        completeness = min(1.0, completeness + 0.10)
    if product_type == "savings" and any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
        completeness = min(1.0, completeness + 0.10)
    if product_type == "gic" and candidate_payload.get("minimum_deposit") not in {None, ""}:
        completeness = min(1.0, completeness + 0.10)

    evidence_average = sum(item.citation_confidence for item in field_evidence_links) / len(field_evidence_links) if field_evidence_links else 0.40
    evidence_coverage = min(1.0, len({item.field_name for item in field_evidence_links}) / 8)
    normalization_certainty = 0.92
    if candidate_record.get("subtype_code") == "other":
        normalization_certainty -= 0.10
    if "ambiguous_mapping" in validation_issue_codes:
        normalization_certainty -= 0.15
    parser_reliability = 0.95
    lowered_notes = " ".join(note.lower() for note in runtime_notes)
    if "partial" in lowered_notes or "source failure" in lowered_notes:
        parser_reliability -= 0.25
    if "no evidence-linked" in lowered_notes:
        parser_reliability -= 0.15

    score = (
        (0.28 * completeness)
        + (0.28 * evidence_average)
        + (0.16 * evidence_coverage)
        + (0.14 * normalization_certainty)
        + (0.14 * parser_reliability)
    )
    if validation_status == "warning":
        score -= 0.08
    if validation_status == "error":
        score -= 0.20
    if "conflicting_evidence" in validation_issue_codes:
        score -= 0.15
    if "partial_source_failure" in validation_issue_codes:
        score -= 0.08
    return round(max(0.0, min(0.99, score)), 4)


def _route_candidate(
    *,
    validation_status: str,
    validation_issue_codes: list[str],
    source_confidence: float,
    routing_config: ValidationRoutingConfig,
) -> dict[str, object]:
    queue_reason_codes: list[str] = []
    if validation_status == "error":
        queue_reason_codes.append("validation_error")
    for code in (
        "required_field_missing",
        "conflicting_evidence",
        "ambiguous_mapping",
        "partial_source_failure",
    ):
        if code in validation_issue_codes and code not in queue_reason_codes:
            queue_reason_codes.append(code)

    force_review = any(code in routing_config.force_review_issue_codes for code in validation_issue_codes)
    warning_requires_review = validation_status == "warning" and source_confidence < routing_config.review_warning_confidence_floor
    passes_phase1_auto = (
        source_confidence >= routing_config.auto_approve_min_confidence
        and validation_status != "error"
        and not force_review
        and "conflicting_evidence" not in validation_issue_codes
        and not warning_requires_review
    )

    if routing_config.routing_mode == "prototype":
        if "manual_sampling_review" not in queue_reason_codes:
            queue_reason_codes.append("manual_sampling_review")
        review_required = True
    else:
        if source_confidence < routing_config.auto_approve_min_confidence and "low_confidence" not in queue_reason_codes:
            queue_reason_codes.append("low_confidence")
        review_required = not passes_phase1_auto
        if review_required and not queue_reason_codes:
            queue_reason_codes.append("manual_sampling_review")

    review_reason_code = queue_reason_codes[0] if queue_reason_codes else None
    return {
        "review_required": review_required,
        "candidate_state": "in_review" if review_required else "auto_validated",
        "review_reason_code": review_reason_code,
        "queue_reason_codes": queue_reason_codes,
    }


def _build_issue_summary(
    *,
    validation_issue_codes: list[str],
    queue_reason_codes: list[str],
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    seen: set[str] = set()
    for code in [*validation_issue_codes, *queue_reason_codes]:
        if code in seen:
            continue
        seen.add(code)
        items.append(
            {
                "code": code,
                "severity": "error" if code in _ERROR_ISSUE_CODES or code == "validation_error" else "warning",
                "summary": _SUMMARY_MESSAGES.get(code, code.replace("_", " ")),
            }
        )
    return items


def _build_validation_artifact_payload(
    *,
    run_id: str,
    correlation_id: str | None,
    request_id: str | None,
    input_item: ValidationInput,
    validation_model_execution_id: str,
    candidate_before: dict[str, object],
    candidate_after: dict[str, object],
    issue_summary: list[dict[str, object]],
    review_task_id: str | None,
    routing_config: ValidationRoutingConfig,
    runtime_notes: list[str],
    started_at: str,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "correlation_id": correlation_id,
        "request_id": request_id,
        "source_id": input_item.source_id,
        "source_document_id": input_item.source_document_id,
        "snapshot_id": input_item.snapshot_id,
        "parsed_document_id": input_item.parsed_document_id,
        "candidate_id": input_item.candidate_id,
        "candidate_run_id": input_item.candidate_run_id,
        "normalization_model_execution_id": input_item.normalization_model_execution_id,
        "validation_model_execution_id": validation_model_execution_id,
        "started_at": started_at,
        "routing_config": {
            "routing_mode": routing_config.routing_mode,
            "auto_approve_min_confidence": routing_config.auto_approve_min_confidence,
            "review_warning_confidence_floor": routing_config.review_warning_confidence_floor,
            "force_review_issue_codes": sorted(routing_config.force_review_issue_codes),
        },
        "candidate_before": candidate_before,
        "candidate_after": candidate_after,
        "field_evidence_links": [
            {
                "field_name": link.field_name,
                "candidate_value": link.candidate_value,
                "evidence_chunk_id": link.evidence_chunk_id,
                "source_document_id": link.source_document_id,
                "citation_confidence": link.citation_confidence,
            }
            for link in input_item.field_evidence_links
        ],
        "issue_summary": issue_summary,
        "review_task_id": review_task_id,
        "runtime_notes": runtime_notes,
    }


def _build_model_execution_record(
    *,
    model_execution_id: str,
    run_id: str,
    source_document_id: str,
    execution_status: str,
    started_at: str,
    completed_at: str,
    agent_name: str,
    model_id: str,
    execution_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "model_execution_id": model_execution_id,
        "run_id": run_id,
        "source_document_id": source_document_id,
        "stage_name": "validation_routing",
        "agent_name": agent_name,
        "model_id": model_id,
        "execution_status": execution_status,
        "execution_metadata": execution_metadata,
        "started_at": started_at,
        "completed_at": completed_at,
    }


def _build_usage_record(
    *,
    run_id: str,
    candidate_id: str,
    model_execution_id: str,
    recorded_at: str,
    usage_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "llm_usage_id": _build_usage_id(model_execution_id),
        "model_execution_id": model_execution_id,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "provider_request_id": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "estimated_cost": "0.000000",
        "usage_metadata": usage_metadata,
        "recorded_at": recorded_at,
    }


def _build_run_source_item_record(
    *,
    run_id: str,
    item: ValidationInput,
    validation_model_execution_id: str,
    validation_storage_key: str | None,
    metadata_storage_key: str | None,
    validation_status: str | None,
    validation_issue_codes: list[str],
    source_confidence: float | None,
    candidate_state: str | None,
    review_reason_code: str | None,
    queue_reason_codes: list[str],
    review_task_id: str | None,
    runtime_notes: list[str],
    correlation_id: str | None,
    request_id: str | None,
    stage_status: str,
    error_summary: str | None,
) -> dict[str, object]:
    digest = sha256(f"{run_id}|{item.source_document_id}".encode("utf-8")).hexdigest()[:16]
    return {
        "run_source_item_id": f"rsi-{digest}",
        "run_id": run_id,
        "source_document_id": item.source_document_id,
        "selected_snapshot_id": item.snapshot_id,
        "stage_status": stage_status,
        "warning_count": 1 if runtime_notes else 0,
        "error_count": 1 if error_summary else 0,
        "error_summary": error_summary,
        "stage_metadata": {
            "validation_action": "failed" if stage_status == "failed" else ("review_queued" if review_task_id else "auto_validated"),
            "candidate_id": item.candidate_id,
            "candidate_run_id": item.candidate_run_id,
            "validation_model_execution_id": validation_model_execution_id,
            "normalization_model_execution_id": item.normalization_model_execution_id,
            "validation_storage_key": validation_storage_key,
            "metadata_storage_key": metadata_storage_key,
            "validation_status": validation_status,
            "validation_issue_codes": validation_issue_codes,
            "source_confidence": source_confidence,
            "candidate_state": candidate_state,
            "review_reason_code": review_reason_code,
            "queue_reason_codes": queue_reason_codes,
            "review_task_id": review_task_id,
            "runtime_notes": runtime_notes,
            "correlation_id": correlation_id,
            "request_id": request_id,
        },
    }


def _build_model_execution_id(*, run_id: str, candidate_id: str) -> str:
    digest = sha256(f"{run_id}|{candidate_id}|validation_routing".encode("utf-8")).hexdigest()[:16]
    return f"modelexec-{digest}"


def _build_usage_id(model_execution_id: str) -> str:
    digest = sha256(f"{model_execution_id}|llm_usage".encode("utf-8")).hexdigest()[:16]
    return f"usage-{digest}"


def _build_review_task_id(candidate_id: str) -> str:
    digest = sha256(f"{candidate_id}|review_task".encode("utf-8")).hexdigest()[:16]
    return f"review-{digest}"


def _string_or_none(value: object) -> str | None:
    if value in {None, ""}:
        return None
    return str(value).strip() or None


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value in {None, ""}:
        return False
    return str(value).strip().lower() == "true"


def _as_decimal(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _as_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return None


def _looks_like_language_code(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?", value.strip()))


def _looks_like_timestamp(value: str | None) -> bool:
    if value in {None, ""}:
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
