from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re

from .models import (
    NormalizationEvidenceLink,
    NormalizationExtractedField,
    NormalizationInput,
    NormalizationResult,
    NormalizationSourceResult,
)
from .storage import NormalizationStorageConfig

_ACTIVE_PRODUCT_TYPES = {"chequing", "savings", "gic"}
_SUBTYPE_REGISTRY = {
    "chequing": {"standard", "student", "newcomer", "premium", "other"},
    "savings": {"standard", "high_interest", "youth", "foreign_currency", "other"},
    "gic": {"redeemable", "non_redeemable", "market_linked", "other"},
}
_RATE_FIELDS = {"standard_rate", "promotional_rate", "public_display_rate"}
_FEE_FIELDS = {"monthly_fee", "public_display_fee"}
_NUMERIC_FIELDS = _RATE_FIELDS | _FEE_FIELDS | {"minimum_balance", "minimum_deposit"}
_CORE_FIELDS = {
    "country_code",
    "bank_code",
    "product_family",
    "product_type",
    "subtype_code",
    "product_name",
    "source_language",
    "currency",
}
_DATE_RE = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")


class NormalizationService:
    def __init__(
        self,
        *,
        storage_config: NormalizationStorageConfig,
        object_store,
        agent_name: str = "fpds-heuristic-normalizer",
        model_id: str = "heuristic-normalizer-v1",
    ) -> None:
        self.storage_config = storage_config
        self.object_store = object_store
        self.agent_name = agent_name
        self.model_id = model_id

    def normalize_inputs(
        self,
        *,
        run_id: str,
        inputs: list[NormalizationInput],
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> NormalizationResult:
        source_results: list[NormalizationSourceResult] = []
        partial_completion_flag = False

        for item in inputs:
            result = self._normalize_single_input(
                run_id=run_id,
                item=item,
                correlation_id=correlation_id,
                request_id=request_id,
            )
            source_results.append(result)
            if result.normalization_action == "failed":
                partial_completion_flag = True

        return NormalizationResult(
            run_id=run_id,
            correlation_id=correlation_id,
            request_id=request_id,
            source_results=source_results,
            partial_completion_flag=partial_completion_flag,
        )

    def _normalize_single_input(
        self,
        *,
        run_id: str,
        item: NormalizationInput,
        correlation_id: str | None,
        request_id: str | None,
    ) -> NormalizationSourceResult:
        started_at = _utc_now_iso()
        normalization_model_execution_id = _build_model_execution_id(
            run_id=run_id,
            source_document_id=item.source_document_id,
            parsed_document_id=item.parsed_document_id,
        )
        try:
            candidate_id = _build_candidate_id(
                run_id=run_id,
                source_document_id=item.source_document_id,
                parsed_document_id=item.parsed_document_id,
            )
            normalized_candidate_record, evidence_links, runtime_notes = _normalize_candidate(
                run_id=run_id,
                candidate_id=candidate_id,
                normalization_model_execution_id=normalization_model_execution_id,
                item=item,
            )
            normalized_storage_key = self.storage_config.build_normalized_object_key(
                country_code=item.country_code,
                bank_code=item.bank_code,
                source_document_id=item.source_document_id,
                candidate_id=candidate_id,
            )
            metadata_storage_key = self.storage_config.build_metadata_object_key(
                country_code=item.country_code,
                bank_code=item.bank_code,
                source_document_id=item.source_document_id,
                candidate_id=candidate_id,
            )
            artifact_payload = _build_normalized_artifact_payload(
                candidate_id=candidate_id,
                run_id=run_id,
                item=item,
                normalized_candidate_record=normalized_candidate_record,
                evidence_links=evidence_links,
                normalization_model_execution_id=normalization_model_execution_id,
                started_at=started_at,
                runtime_notes=runtime_notes,
                correlation_id=correlation_id,
                request_id=request_id,
            )
            metadata_payload = {
                "candidate_id": candidate_id,
                "source_document_id": item.source_document_id,
                "snapshot_id": item.snapshot_id,
                "parsed_document_id": item.parsed_document_id,
                "normalization_model_execution_id": normalization_model_execution_id,
                "normalized_storage_key": normalized_storage_key,
                "metadata_storage_key": metadata_storage_key,
                "validation_status": normalized_candidate_record["validation_status"],
                "validation_issue_codes": normalized_candidate_record["validation_issue_codes"],
                "source_confidence": normalized_candidate_record["source_confidence"],
                "field_evidence_link_count": len(evidence_links),
                "runtime_notes": runtime_notes,
            }
            self.object_store.put_object_bytes(
                object_key=normalized_storage_key,
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
                model_execution_id=normalization_model_execution_id,
                run_id=run_id,
                source_document_id=item.source_document_id,
                execution_status="completed",
                started_at=started_at,
                completed_at=completed_at,
                agent_name=self.agent_name,
                model_id=self.model_id,
                execution_metadata={
                    "candidate_id": candidate_id,
                    "parsed_document_id": item.parsed_document_id,
                    "snapshot_id": item.snapshot_id,
                    "extraction_model_execution_id": item.extraction_model_execution_id,
                    "input_extracted_storage_key": item.extracted_storage_key,
                    "normalized_storage_key": normalized_storage_key,
                    "normalized_metadata_storage_key": metadata_storage_key,
                    "validation_status": normalized_candidate_record["validation_status"],
                    "validation_issue_codes": normalized_candidate_record["validation_issue_codes"],
                    "source_confidence": normalized_candidate_record["source_confidence"],
                    "field_evidence_link_count": len(evidence_links),
                    "runtime_notes": runtime_notes,
                },
            )
            usage_record = _build_usage_record(
                run_id=run_id,
                model_execution_id=normalization_model_execution_id,
                recorded_at=completed_at,
                usage_metadata={
                    "usage_mode": "heuristic-no-llm-call",
                    "provider": "local",
                    "model_id": self.model_id,
                },
            )
            return NormalizationSourceResult(
                source_id=item.source_id,
                source_document_id=item.source_document_id,
                snapshot_id=item.snapshot_id,
                parsed_document_id=item.parsed_document_id,
                extraction_model_execution_id=item.extraction_model_execution_id,
                normalization_action="stored",
                candidate_id=candidate_id,
                normalization_model_execution_id=normalization_model_execution_id,
                normalized_storage_key=normalized_storage_key,
                metadata_storage_key=metadata_storage_key,
                validation_status=str(normalized_candidate_record["validation_status"]),
                validation_issue_codes=list(normalized_candidate_record["validation_issue_codes"]),
                source_confidence=float(normalized_candidate_record["source_confidence"]),
                runtime_notes=runtime_notes,
                error_summary=None,
                normalized_candidate_record=normalized_candidate_record,
                field_evidence_link_records=evidence_links,
                model_execution_record=model_execution_record,
                usage_record=usage_record,
                run_source_item_record=_build_run_source_item_record(
                    run_id=run_id,
                    item=item,
                    candidate_id=candidate_id,
                    normalization_model_execution_id=normalization_model_execution_id,
                    normalized_storage_key=normalized_storage_key,
                    metadata_storage_key=metadata_storage_key,
                    validation_status=str(normalized_candidate_record["validation_status"]),
                    validation_issue_codes=list(normalized_candidate_record["validation_issue_codes"]),
                    source_confidence=float(normalized_candidate_record["source_confidence"]),
                    field_evidence_link_count=len(evidence_links),
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
            return NormalizationSourceResult(
                source_id=item.source_id,
                source_document_id=item.source_document_id,
                snapshot_id=item.snapshot_id,
                parsed_document_id=item.parsed_document_id,
                extraction_model_execution_id=item.extraction_model_execution_id,
                normalization_action="failed",
                candidate_id=None,
                normalization_model_execution_id=normalization_model_execution_id,
                normalized_storage_key=None,
                metadata_storage_key=None,
                validation_status=None,
                validation_issue_codes=[],
                source_confidence=None,
                runtime_notes=[],
                error_summary=error_summary,
                normalized_candidate_record=None,
                field_evidence_link_records=[],
                model_execution_record=_build_model_execution_record(
                    model_execution_id=normalization_model_execution_id,
                    run_id=run_id,
                    source_document_id=item.source_document_id,
                    execution_status="failed",
                    started_at=started_at,
                    completed_at=completed_at,
                    agent_name=self.agent_name,
                    model_id=self.model_id,
                    execution_metadata={
                        "parsed_document_id": item.parsed_document_id,
                        "snapshot_id": item.snapshot_id,
                        "extraction_model_execution_id": item.extraction_model_execution_id,
                        "error_summary": error_summary,
                    },
                ),
                usage_record=None,
                run_source_item_record=_build_run_source_item_record(
                    run_id=run_id,
                    item=item,
                    candidate_id=None,
                    normalization_model_execution_id=normalization_model_execution_id,
                    normalized_storage_key=None,
                    metadata_storage_key=None,
                    validation_status=None,
                    validation_issue_codes=[],
                    source_confidence=None,
                    field_evidence_link_count=0,
                    runtime_notes=[],
                    correlation_id=correlation_id,
                    request_id=request_id,
                    stage_status="failed",
                    error_summary=error_summary,
                ),
            )


def _normalize_candidate(
    *,
    run_id: str,
    candidate_id: str,
    normalization_model_execution_id: str,
    item: NormalizationInput,
) -> tuple[dict[str, object], list[dict[str, object]], list[str]]:
    extracted_by_field = {field.field_name: field for field in item.extracted_fields}
    runtime_notes = list(item.runtime_notes)

    country_code = _coalesce_string(
        _field_value(extracted_by_field, "country_code"),
        item.country_code,
        str(item.schema_context.get("country_code", "")) or None,
    )
    bank_code = _coalesce_string(_field_value(extracted_by_field, "bank_code"), item.bank_code)
    product_family = _coalesce_string(
        _field_value(extracted_by_field, "product_family"),
        str(item.schema_context.get("product_family", "")) or None,
        "deposit",
    )
    product_type = _coalesce_string(
        _field_value(extracted_by_field, "product_type"),
        str(item.schema_context.get("product_type", "")) or None,
        str(item.source_metadata.get("product_type", "")) or None,
    )
    product_name = _coalesce_string(_field_value(extracted_by_field, "product_name"))
    source_language = _coalesce_string(_field_value(extracted_by_field, "source_language"), item.source_language, "und")
    currency = _coalesce_string(_field_value(extracted_by_field, "currency"), "CAD")
    subtype_code, source_subtype_label = _infer_subtype_code(
        product_type=product_type,
        currency=currency,
        product_name=product_name,
        description_short=_coalesce_string(_field_value(extracted_by_field, "description_short")),
        notes=_coalesce_string(_field_value(extracted_by_field, "notes")),
    )
    if source_subtype_label is not None:
        runtime_notes.append("Subtype could not be mapped confidently and was normalized to `other` while preserving source_subtype_label.")

    candidate_payload: dict[str, object] = {
        "status": "active",
        "source_subtype_label": source_subtype_label,
        "last_verified_at": _utc_now_iso(),
        "bank_name": _bank_name_for_code(bank_code),
        "product_name": product_name,
    }
    field_mapping_metadata: dict[str, object] = {}
    normalized_values_for_links: dict[str, object] = {}

    for field_name, field in extracted_by_field.items():
        normalized_value = _normalize_field_value(field_name=field_name, value=field.candidate_value, value_type=field.value_type)
        normalized_values_for_links[field_name] = normalized_value
        field_mapping_metadata[field_name] = {
            "source_field_name": field_name,
            "normalized_value": normalized_value,
            "value_type": field.value_type,
            "extraction_method": field.extraction_method,
            "extraction_confidence": field.confidence,
            "evidence_chunk_id": field.evidence_chunk_id,
            "normalization_method": "heuristic_canonical_mapping",
        }
        if field_name in _CORE_FIELDS:
            continue
        candidate_payload[field_name] = normalized_value

    candidate_payload["subtype_code"] = subtype_code
    field_mapping_metadata["subtype_code"] = {
        "normalized_value": subtype_code,
        "source_field_name": "product_name",
        "normalization_method": "heuristic_subtype_inference",
        "source_subtype_label": source_subtype_label,
    }
    candidate_payload["target_customer_tags"] = _infer_target_customer_tags(candidate_payload)
    candidate_payload["effective_date"] = _normalize_effective_date(candidate_payload.get("effective_date"), candidate_payload.get("notes"))

    validation_issue_codes = _compute_validation_issue_codes(
        product_type=product_type,
        subtype_code=subtype_code,
        product_name=product_name,
        country_code=country_code,
        bank_code=bank_code,
        product_family=product_family,
        source_language=source_language,
        currency=currency,
        candidate_payload=candidate_payload,
        evidence_links=item.evidence_links,
    )
    validation_status = _resolve_validation_status(validation_issue_codes)
    source_confidence = _compute_source_confidence(
        validation_status=validation_status,
        validation_issue_codes=validation_issue_codes,
        candidate_payload=candidate_payload,
        evidence_links=item.evidence_links,
        product_type=product_type,
        product_name=product_name,
        currency=currency,
    )

    candidate_record = {
        "candidate_id": candidate_id,
        "run_id": run_id,
        "source_document_id": item.source_document_id,
        "model_execution_id": normalization_model_execution_id,
        "candidate_state": "draft",
        "validation_status": validation_status,
        "source_confidence": source_confidence,
        "review_reason_code": None,
        "country_code": country_code,
        "bank_code": bank_code,
        "product_family": product_family,
        "product_type": product_type,
        "subtype_code": subtype_code,
        "product_name": product_name,
        "source_language": source_language,
        "currency": currency,
        "validation_issue_codes": validation_issue_codes,
        "candidate_payload": candidate_payload,
        "field_mapping_metadata": field_mapping_metadata,
    }
    field_evidence_link_records = _build_field_evidence_link_records(
        candidate_id=candidate_id,
        normalized_values_for_links=normalized_values_for_links,
        source_document_id=item.source_document_id,
        evidence_links=item.evidence_links,
    )
    return candidate_record, field_evidence_link_records, runtime_notes


def _compute_validation_issue_codes(
    *,
    product_type: str | None,
    subtype_code: str | None,
    product_name: str | None,
    country_code: str | None,
    bank_code: str | None,
    product_family: str | None,
    source_language: str | None,
    currency: str | None,
    candidate_payload: dict[str, object],
    evidence_links: list[NormalizationEvidenceLink],
) -> list[str]:
    issues: list[str] = []
    required_identity = {
        "country_code": country_code,
        "bank_code": bank_code,
        "product_family": product_family,
        "product_type": product_type,
        "product_name": product_name,
        "currency": currency,
    }
    if any(value in {None, ""} for value in required_identity.values()):
        issues.append("required_field_missing")
    if product_type not in _ACTIVE_PRODUCT_TYPES:
        issues.append("invalid_taxonomy_code")
    if subtype_code and product_type in _SUBTYPE_REGISTRY and subtype_code not in _SUBTYPE_REGISTRY[product_type]:
        issues.append("invalid_taxonomy_code")
    if source_language and not _looks_like_language_code(source_language):
        issues.append("ambiguous_mapping")

    for field_name in _NUMERIC_FIELDS:
        value = candidate_payload.get(field_name)
        if value in {None, ""}:
            continue
        decimal_value = _as_decimal(value)
        if decimal_value is None:
            issues.append("invalid_numeric_range")
            continue
        if field_name in _RATE_FIELDS and not (Decimal("0") <= decimal_value <= Decimal("100")):
            issues.append("invalid_numeric_range")
        if field_name not in _RATE_FIELDS and decimal_value < 0:
            issues.append("invalid_numeric_range")

    if product_type == "savings":
        if not any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
            issues.append("required_field_missing")

    conflicting_fields = defaultdict(set)
    for link in evidence_links:
        conflicting_fields[link.field_name].add(link.candidate_value.strip())
    if any(len(values) > 1 for values in conflicting_fields.values()):
        issues.append("conflicting_evidence")
    return sorted(dict.fromkeys(issues))


def _resolve_validation_status(validation_issue_codes: list[str]) -> str:
    error_issue_codes = {"required_field_missing", "invalid_taxonomy_code", "invalid_numeric_range"}
    if any(item in error_issue_codes for item in validation_issue_codes):
        return "error"
    if validation_issue_codes:
        return "warning"
    return "pass"


def _compute_source_confidence(
    *,
    validation_status: str,
    validation_issue_codes: list[str],
    candidate_payload: dict[str, object],
    evidence_links: list[NormalizationEvidenceLink],
    product_type: str | None,
    product_name: str | None,
    currency: str | None,
) -> float:
    required_values = [product_type, product_name, currency, candidate_payload.get("status"), candidate_payload.get("last_verified_at")]
    completeness = sum(1 for item in required_values if item not in {None, ""}) / len(required_values)
    if product_type == "savings" and any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
        completeness = min(1.0, completeness + 0.15)
    evidence_average = sum(item.citation_confidence for item in evidence_links) / len(evidence_links) if evidence_links else 0.45
    evidence_coverage = min(1.0, len(evidence_links) / 8)
    score = (0.45 * evidence_average) + (0.35 * completeness) + (0.20 * evidence_coverage)
    if validation_status == "warning":
        score -= 0.10
    if validation_status == "error":
        score -= 0.25
    if "conflicting_evidence" in validation_issue_codes:
        score -= 0.15
    return round(max(0.0, min(0.99, score)), 4)


def _build_field_evidence_link_records(
    *,
    candidate_id: str,
    normalized_values_for_links: dict[str, object],
    source_document_id: str,
    evidence_links: list[NormalizationEvidenceLink],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for link in evidence_links:
        if link.field_name not in normalized_values_for_links:
            continue
        candidate_value = normalized_values_for_links[link.field_name]
        records.append(
            {
                "field_evidence_link_id": _build_field_evidence_link_id(candidate_id, link.field_name, link.evidence_chunk_id),
                "candidate_id": candidate_id,
                "product_version_id": None,
                "evidence_chunk_id": link.evidence_chunk_id,
                "source_document_id": source_document_id,
                "field_name": link.field_name,
                "candidate_value": _stringify(candidate_value),
                "citation_confidence": round(link.citation_confidence, 4),
            }
        )
    return records


def _infer_subtype_code(
    *,
    product_type: str | None,
    currency: str | None,
    product_name: str | None,
    description_short: str | None,
    notes: str | None,
) -> tuple[str | None, str | None]:
    if product_type is None:
        return None, None
    text = " ".join(item for item in [product_name, description_short, notes] if item).lower()
    if product_type == "savings":
        if currency and currency != "CAD":
            return "foreign_currency", None
        if any(token in text for token in ("premium", "high interest", "hisa")):
            return "high_interest", None
        if any(token in text for token in ("student", "youth")):
            return "youth", None
        return "standard", None
    if product_type == "chequing":
        if "student" in text:
            return "student", None
        if "newcomer" in text:
            return "newcomer", None
        if "premium" in text or "all-inclusive" in text:
            return "premium", None
        return "standard", None
    if product_type == "gic":
        if "market linked" in text or "index linked" in text:
            return "market_linked", None
        if "redeemable" in text:
            return "redeemable", None
        if "non-redeemable" in text:
            return "non_redeemable", None
        return "other", product_name
    return "other", product_name


def _infer_target_customer_tags(candidate_payload: dict[str, object]) -> list[str]:
    tags: list[str] = []
    merged_text = " ".join(str(candidate_payload.get(field_name, "")) for field_name in ("product_name", "description_short", "notes", "eligibility_text")).lower()
    if "student" in merged_text or "youth" in merged_text:
        tags.append("student")
    if "newcomer" in merged_text:
        tags.append("newcomer")
    if "senior" in merged_text:
        tags.append("senior")
    if "business" in merged_text:
        tags.append("business")
    return tags


def _normalize_effective_date(value: object, notes_value: object) -> str | None:
    candidate_texts = [str(item) for item in [value, notes_value] if item not in {None, ""}]
    for text in candidate_texts:
        match = _DATE_RE.search(text)
        if match is None:
            continue
        try:
            parsed = datetime.strptime(match.group(1), "%B %d, %Y")
        except ValueError:
            continue
        return parsed.date().isoformat()
    if value in {None, ""}:
        return None
    return str(value)


def _normalize_field_value(*, field_name: str, value: object, value_type: str) -> object:
    if value in {None, ""}:
        return None
    if value_type == "boolean":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() == "true"
    if value_type == "decimal":
        decimal_value = _as_decimal(value)
        return float(decimal_value) if decimal_value is not None else None
    return str(value).strip()


def _field_value(extracted_by_field: dict[str, NormalizationExtractedField], field_name: str) -> object | None:
    field = extracted_by_field.get(field_name)
    if field is None:
        return None
    return field.candidate_value


def _as_decimal(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _coalesce_string(*values: object) -> str | None:
    for value in values:
        if value is None:
            continue
        normalized = str(value).strip()
        if normalized:
            return normalized
    return None


def _looks_like_language_code(value: str) -> bool:
    normalized = value.strip()
    return bool(re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?", normalized))


def _bank_name_for_code(bank_code: str | None) -> str | None:
    if bank_code == "TD":
        return "TD Bank"
    return bank_code


def _build_normalized_artifact_payload(
    *,
    candidate_id: str,
    run_id: str,
    item: NormalizationInput,
    normalized_candidate_record: dict[str, object],
    evidence_links: list[dict[str, object]],
    normalization_model_execution_id: str,
    started_at: str,
    runtime_notes: list[str],
    correlation_id: str | None,
    request_id: str | None,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "run_id": run_id,
        "correlation_id": correlation_id,
        "request_id": request_id,
        "source_id": item.source_id,
        "source_document_id": item.source_document_id,
        "snapshot_id": item.snapshot_id,
        "parsed_document_id": item.parsed_document_id,
        "extraction_model_execution_id": item.extraction_model_execution_id,
        "normalization_model_execution_id": normalization_model_execution_id,
        "started_at": started_at,
        "normalized_candidate": normalized_candidate_record,
        "field_evidence_links": evidence_links,
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
        "stage_name": "normalization",
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
    model_execution_id: str,
    recorded_at: str,
    usage_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "llm_usage_id": _build_usage_id(model_execution_id),
        "model_execution_id": model_execution_id,
        "run_id": run_id,
        "candidate_id": None,
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
    item: NormalizationInput,
    candidate_id: str | None,
    normalization_model_execution_id: str,
    normalized_storage_key: str | None,
    metadata_storage_key: str | None,
    validation_status: str | None,
    validation_issue_codes: list[str],
    source_confidence: float | None,
    field_evidence_link_count: int,
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
            "normalization_action": "failed" if stage_status == "failed" else "stored",
            "candidate_id": candidate_id,
            "normalization_model_execution_id": normalization_model_execution_id,
            "extraction_model_execution_id": item.extraction_model_execution_id,
            "normalized_storage_key": normalized_storage_key,
            "metadata_storage_key": metadata_storage_key,
            "validation_status": validation_status,
            "validation_issue_codes": validation_issue_codes,
            "source_confidence": source_confidence,
            "field_evidence_link_count": field_evidence_link_count,
            "runtime_notes": runtime_notes,
            "correlation_id": correlation_id,
            "request_id": request_id,
        },
    }


def _build_candidate_id(*, run_id: str, source_document_id: str, parsed_document_id: str) -> str:
    digest = sha256(f"{run_id}|{source_document_id}|{parsed_document_id}|candidate".encode("utf-8")).hexdigest()[:16]
    return f"cand-{digest}"


def _build_model_execution_id(*, run_id: str, source_document_id: str, parsed_document_id: str) -> str:
    digest = sha256(f"{run_id}|{source_document_id}|{parsed_document_id}|normalization".encode("utf-8")).hexdigest()[:16]
    return f"modelexec-{digest}"


def _build_field_evidence_link_id(candidate_id: str, field_name: str, evidence_chunk_id: str) -> str:
    digest = sha256(f"{candidate_id}|{field_name}|{evidence_chunk_id}".encode("utf-8")).hexdigest()[:16]
    return f"fel-{digest}"


def _build_usage_id(model_execution_id: str) -> str:
    digest = sha256(f"{model_execution_id}|llm_usage".encode("utf-8")).hexdigest()[:16]
    return f"usage-{digest}"


def _stringify(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
