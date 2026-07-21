from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any

from worker.pipeline.fpds_ai_runtime import (
    configured_model_id,
    estimated_cost_usd,
    invoke_openai_json_schema,
    llm_provider_configured,
)
from worker.pipeline.fpds_field_contract import (
    canonical_value_type,
    field_contract,
    field_contract_payload,
    mapping_contract_metadata,
    value_matches_contract,
)
from worker.pipeline.fpds_rate_safety import (
    canonical_deposit_rate_suppression_reason,
    expired_promotional_offer_end_date,
)

from .models import (
    NormalizationEvidenceLink,
    NormalizationExtractedField,
    NormalizationInput,
    NormalizationResult,
    NormalizationSourceResult,
)
from .product_profile_expansion import expand_profile_product_inputs, should_suppress_unprofiled_profile_input
from .storage import NormalizationStorageConfig

_ACTIVE_PRODUCT_TYPES = {"chequing", "savings", "gic"}
_SUBTYPE_REGISTRY = {
    "chequing": {"standard", "package", "interest_bearing", "premium", "other"},
    "savings": {"standard", "high_interest", "youth", "foreign_currency", "other"},
    "gic": {"redeemable", "non_redeemable", "market_linked", "other"},
}
_RATE_FIELDS = {"standard_rate", "base_12_month_rate", "promotional_rate", "public_display_rate"}
_FEE_FIELDS = {"monthly_fee", "public_display_fee"}
_NUMERIC_FIELDS = _RATE_FIELDS | _FEE_FIELDS | {"minimum_balance", "minimum_deposit"}
_JSON_FIELDS = {"term_rate_table"}
_DEPOSIT_GOLDEN_REQUIRED_PAYLOAD_FIELDS = (
    "bank_name",
    "product_name",
    "product_page_url",
    "signup_amount",
    "eligibility",
    "application_method",
    "deposit_insurance",
)
_DEPOSIT_GOLDEN_RATE_FIELDS = ("highest_rate", "base_12_month_rate")
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
_DYNAMIC_OPERATIONAL_FIELDS = {
    "status",
    "last_verified_at",
    "bank_name",
    "product_name",
    "source_subtype_label",
    "subtype_code",
}
_DATE_RE = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")
_PERCENT_RE = re.compile(r"(?<!\d)(\d{1,2}(?:\.\d{1,4})?)\s*%")
_RATE_CONTEXT_FIELDS = {
    "account_interest_rates",
    "cashable_gic_rates",
    "gic_rates",
    "interest_rate_summary",
    "market_growth_gic_rates",
    "maximum_return",
    "minimum_guaranteed_return",
    "non_cashable_gic_rates",
    "non_redeemable_gic_rates",
    "promotional_rate",
    "public_display_rate",
    "rate_tiers",
    "redeemable_gic_rates",
    "savings_account_rates",
    "savings_rate_table",
    "standard_rate",
    "base_12_month_rate",
    "term_deposit_rates",
    "term_rate_table",
    "tier_definition_text",
}


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
            expanded_items = expand_profile_product_inputs(item)
            if not expanded_items and should_suppress_unprofiled_profile_input(item):
                continue
            for candidate_item in expanded_items or [item]:
                result = self._normalize_single_input(
                    run_id=run_id,
                    item=candidate_item,
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
            candidate_key=item.candidate_key,
        )
        try:
            candidate_id = _build_candidate_id(
                run_id=run_id,
                source_document_id=item.source_document_id,
                parsed_document_id=item.parsed_document_id,
                candidate_key=item.candidate_key,
            )
            normalized_candidate_record, evidence_links, runtime_notes, normalization_meta = _normalize_candidate(
                run_id=run_id,
                candidate_id=candidate_id,
                normalization_model_execution_id=normalization_model_execution_id,
                item=item,
            )
            agent_name = str(normalization_meta.get("agent_name") or self.agent_name)
            model_id = str(normalization_meta.get("model_id") or self.model_id)
            usage_metadata = dict(normalization_meta.get("usage_metadata") or {
                "usage_mode": "heuristic-no-llm-call",
                "provider": "local",
                "model_id": self.model_id,
            })
            prompt_tokens = int(normalization_meta.get("prompt_tokens") or 0)
            completion_tokens = int(normalization_meta.get("completion_tokens") or 0)
            provider_request_id = normalization_meta.get("provider_request_id")
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
                agent_name=agent_name,
                model_id=model_id,
                execution_metadata={
                    "candidate_id": candidate_id,
                    "candidate_key": item.candidate_key,
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
                usage_metadata=usage_metadata,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                provider_request_id=provider_request_id,
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
                        "candidate_key": item.candidate_key,
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
) -> tuple[dict[str, object], list[dict[str, object]], list[str], dict[str, object]]:
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
    dynamic_product_type = _uses_dynamic_product_type(product_type=product_type, item=item)
    product_type_family = _canonical_product_type_family(product_type)
    product_name = _refine_product_name_from_source_metadata(
        product_name=_coalesce_string(_field_value(extracted_by_field, "product_name")),
        source_metadata=item.source_metadata,
        runtime_notes=runtime_notes,
    )
    source_language = _coalesce_string(_field_value(extracted_by_field, "source_language"), item.source_language, "und")
    currency = _coalesce_string(_field_value(extracted_by_field, "currency"), "CAD")
    candidate_payload: dict[str, object] = {
        "status": "active",
        "last_verified_at": _utc_now_iso(),
        "bank_name": _bank_name_for_code(bank_code),
        "product_name": product_name,
    }
    field_mapping_metadata: dict[str, object] = {}
    normalized_values_for_links: dict[str, object] = {}

    for field_name, field in extracted_by_field.items():
        rate_suppression_reason = _rate_field_suppression_reason(
            field_name=field_name,
            field=field,
            product_type_family=product_type_family,
        )
        if rate_suppression_reason is not None:
            field_mapping_metadata[field_name] = {
                "source_field_name": field_name,
                "normalized_value": None,
                "value_type": field.value_type,
                "extraction_method": field.extraction_method,
                "extraction_confidence": field.confidence,
                "evidence_chunk_id": field.evidence_chunk_id,
                "normalization_method": "canonical_rate_safety_filter",
                "suppressed_reason": rate_suppression_reason,
            }
            runtime_notes.append(
                f"Suppressed `{field_name}` value `{field.candidate_value}` because it is not a canonical annual deposit rate: {rate_suppression_reason}."
            )
            continue
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
            **mapping_contract_metadata(field_name),
        }
        if field_name in _CORE_FIELDS:
            continue
        candidate_payload[field_name] = normalized_value

    normalization_meta: dict[str, object] = {
        "agent_name": "fpds-heuristic-normalizer",
        "model_id": "heuristic-normalizer-v1",
        "usage_metadata": {
            "usage_mode": "heuristic-no-llm-call",
            "provider": "local",
            "model_id": "heuristic-normalizer-v1",
        },
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "provider_request_id": None,
    }
    dynamic_payload: dict[str, Any] = {}
    if dynamic_product_type:
        dynamic_payload, dynamic_notes, dynamic_usage = _normalize_dynamic_fields_with_ai(
            item=item,
            extracted_by_field=extracted_by_field,
            candidate_payload=candidate_payload,
        )
        runtime_notes.extend(dynamic_notes)
        for field_name, value in dynamic_payload.get("candidate_payload", {}).items():
            candidate_payload[field_name] = value
            normalized_values_for_links[field_name] = value
            extracted_field = extracted_by_field.get(field_name)
            field_mapping_metadata[field_name] = {
                "source_field_name": field_name,
                "normalized_value": value,
                "value_type": canonical_value_type(field_name),
                "extraction_method": extracted_field.extraction_method if extracted_field is not None else "openai_dynamic_normalizer",
                "extraction_confidence": extracted_field.confidence if extracted_field is not None else None,
                "evidence_chunk_id": extracted_field.evidence_chunk_id if extracted_field is not None else None,
                "normalization_method": "dynamic_ai_canonical_mapping",
                **mapping_contract_metadata(field_name),
            }
        if dynamic_payload.get("product_name") not in {None, ""}:
            product_name = _coalesce_string(dynamic_payload.get("product_name"), product_name)
            candidate_payload["product_name"] = product_name
        if dynamic_usage:
            normalization_meta = {
                "agent_name": "fpds-dynamic-product-normalizer",
                "model_id": str(dynamic_usage["model_id"]),
                "usage_metadata": {
                    "usage_mode": "openai-dynamic-product-normalization",
                    "provider": "openai",
                    "model_id": str(dynamic_usage["model_id"]),
                },
                "prompt_tokens": int(dynamic_usage.get("prompt_tokens") or 0),
                "completion_tokens": int(dynamic_usage.get("completion_tokens") or 0),
                "provider_request_id": dynamic_usage.get("provider_request_id"),
            }

        _enforce_dynamic_field_contract(
            expected_fields=item.source_metadata.get("expected_fields", []),
            candidate_payload=candidate_payload,
            normalized_values_for_links=normalized_values_for_links,
            field_mapping_metadata=field_mapping_metadata,
            runtime_notes=runtime_notes,
        )

    evidence_links_for_output = list(item.evidence_links)
    _clean_product_context_fields(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        normalized_values_for_links=normalized_values_for_links,
        field_mapping_metadata=field_mapping_metadata,
        runtime_notes=runtime_notes,
        evidence_context_by_field={
            field_name: " ".join(
                part
                for part in (field.anchor_value or "", field.evidence_text_excerpt or "")
                if part
            )
            for field_name, field in extracted_by_field.items()
        },
    )
    _apply_credit_card_labeled_fallback(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    alias_field = _apply_product_type_aliases(product_type_family=product_type_family, candidate_payload=candidate_payload, runtime_notes=runtime_notes)
    if alias_field is not None and candidate_payload.get("minimum_deposit") not in {None, ""}:
        normalized_values_for_links["minimum_deposit"] = candidate_payload["minimum_deposit"]
        field_mapping_metadata["minimum_deposit"] = {
            "source_field_name": alias_field,
            "normalized_value": candidate_payload["minimum_deposit"],
            "normalization_method": "gic_minimum_deposit_alias_mapping",
        }
        alias_link = next((link for link in item.evidence_links if link.field_name == alias_field), None)
        if alias_link is not None:
            evidence_links_for_output.append(
                NormalizationEvidenceLink(
                    field_name="minimum_deposit",
                    candidate_value=_stringify(candidate_payload["minimum_deposit"]),
                    evidence_chunk_id=alias_link.evidence_chunk_id,
                    evidence_text_excerpt=alias_link.evidence_text_excerpt,
                    source_document_id=alias_link.source_document_id,
                    source_snapshot_id=alias_link.source_snapshot_id,
                    citation_confidence=alias_link.citation_confidence,
                    model_execution_id=alias_link.model_execution_id,
                    anchor_type=alias_link.anchor_type,
                    anchor_value=alias_link.anchor_value,
                    page_no=alias_link.page_no,
                    chunk_index=alias_link.chunk_index,
                )
            )

    _apply_rate_evidence_fallback(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )

    subtype_code, source_subtype_label = _infer_subtype_code(
        product_type=product_type_family,
        currency=currency,
        candidate_payload=candidate_payload,
    )
    if dynamic_product_type:
        subtype_code = str(dynamic_payload.get("subtype_code") or subtype_code or "other")
        source_subtype_label = _coalesce_string(dynamic_payload.get("source_subtype_label"), source_subtype_label, product_name)
    if source_subtype_label is not None:
        runtime_notes.append("Subtype could not be mapped confidently and was normalized to `other` while preserving source_subtype_label.")
    candidate_payload["source_subtype_label"] = source_subtype_label
    candidate_payload["subtype_code"] = subtype_code
    field_mapping_metadata["subtype_code"] = {
        "normalized_value": subtype_code,
        "source_field_name": "product_name",
        "normalization_method": "heuristic_subtype_inference",
        "source_subtype_label": source_subtype_label,
    }
    _resolve_gic_redeemability_flags(
        product_type_family=product_type_family,
        subtype_code=subtype_code,
        candidate_payload=candidate_payload,
        normalized_values_for_links=normalized_values_for_links,
        field_mapping_metadata=field_mapping_metadata,
        runtime_notes=runtime_notes,
    )
    candidate_payload["target_customer_tags"] = _infer_target_customer_tags(candidate_payload)
    if _truthy(candidate_payload.get("student_plan_flag")) or "student" in candidate_payload["target_customer_tags"]:
        candidate_payload["student_plan_flag"] = True
    if _truthy(candidate_payload.get("newcomer_plan_flag")) or "newcomer" in candidate_payload["target_customer_tags"]:
        candidate_payload["newcomer_plan_flag"] = True
    _clean_promotional_period_fields(candidate_payload)
    candidate_payload["effective_date"] = _normalize_effective_date(candidate_payload.get("effective_date"), candidate_payload.get("notes"))
    _apply_field_qualifier_notes(
        product_type_family=product_type_family,
        currency=currency,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
    )

    validation_issue_codes = _compute_validation_issue_codes(
        product_type=product_type,
        product_type_family=product_type_family,
        subtype_code=subtype_code,
        product_name=product_name,
        country_code=country_code,
        bank_code=bank_code,
        product_family=product_family,
        source_language=source_language,
        currency=currency,
        candidate_payload=candidate_payload,
        evidence_links=item.evidence_links,
        dynamic_product_type=dynamic_product_type,
        expected_fields=[str(field_name) for field_name in item.source_metadata.get("expected_fields", [])],
    )
    validation_status = _resolve_validation_status(validation_issue_codes)
    source_confidence = _compute_source_confidence(
        validation_status=validation_status,
        validation_issue_codes=validation_issue_codes,
        candidate_payload=candidate_payload,
        evidence_links=item.evidence_links,
        product_type=product_type,
        product_type_family=product_type_family,
        product_name=product_name,
        currency=currency,
        dynamic_product_type=dynamic_product_type,
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
        evidence_links=evidence_links_for_output,
    )
    return candidate_record, field_evidence_link_records, runtime_notes, normalization_meta


def _compute_validation_issue_codes(
    *,
    product_type: str | None,
    product_type_family: str | None,
    subtype_code: str | None,
    product_name: str | None,
    country_code: str | None,
    bank_code: str | None,
    product_family: str | None,
    source_language: str | None,
    currency: str | None,
    candidate_payload: dict[str, object],
    evidence_links: list[NormalizationEvidenceLink],
    dynamic_product_type: bool = False,
    expected_fields: list[str] | None = None,
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
    if not dynamic_product_type and product_type not in _ACTIVE_PRODUCT_TYPES:
        issues.append("invalid_taxonomy_code")
    if not dynamic_product_type and subtype_code and product_type in _SUBTYPE_REGISTRY and subtype_code not in _SUBTYPE_REGISTRY[product_type]:
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
        if field_name in _RATE_FIELDS and (
            decimal_value < Decimal("0")
            or canonical_deposit_rate_suppression_reason(value=decimal_value) is not None
        ):
            issues.append("invalid_numeric_range")
        if field_name not in _RATE_FIELDS and decimal_value < 0:
            issues.append("invalid_numeric_range")

    if any(not value_matches_contract(field_name, value) for field_name, value in candidate_payload.items()):
        issues.append("invalid_field_type")

    term_length_days = candidate_payload.get("term_length_days")
    if term_length_days not in {None, ""}:
        integer_value = _as_int(term_length_days)
        if integer_value is None or integer_value < 1:
            issues.append("invalid_term_value")

    requiredness_type = product_type_family or product_type
    golden_contract_candidate = _meets_deposit_golden_contract(
        product_type=product_type,
        product_type_family=product_type_family,
        product_name=product_name,
        currency=currency,
        candidate_payload=candidate_payload,
        dynamic_product_type=dynamic_product_type,
    )
    if requiredness_type == "chequing" and not golden_contract_candidate:
        if not any(candidate_payload.get(field_name) not in {None, ""} for field_name in (*_FEE_FIELDS, "fee_waiver_condition")):
            issues.append("required_field_missing")
    if requiredness_type == "savings" and not golden_contract_candidate:
        if not any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
            issues.append("required_field_missing")
    if requiredness_type == "gic" and not golden_contract_candidate:
        if not any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
            issues.append("required_field_missing")
        if candidate_payload.get("minimum_deposit") in {None, ""}:
            issues.append("required_field_missing")
        if candidate_payload.get("term_length_days") in {None, ""} and candidate_payload.get("term_length_text") in {None, ""}:
            issues.append("required_field_missing")
        if _truthy(candidate_payload.get("redeemable_flag")) and _truthy(candidate_payload.get("non_redeemable_flag")):
            issues.append("inconsistent_cross_field_logic")
        if candidate_payload.get("minimum_balance") not in {None, ""} and candidate_payload.get("minimum_deposit") in {None, ""}:
            issues.append("inconsistent_cross_field_logic")
    if dynamic_product_type:
        non_core_fields = [
            value
            for field_name, value in candidate_payload.items()
            if field_name not in {"status", "last_verified_at", "bank_name", "product_name", "source_subtype_label", "subtype_code"}
        ]
        if not any(_has_meaningful_value(value) for value in non_core_fields):
            issues.append("required_field_missing")
        if subtype_code in {None, ""}:
            issues.append("ambiguous_mapping")
        if any(
            candidate_payload.get(field_name) in {None, ""}
            for field_name in _dynamic_priority_fields(product_type=product_type, expected_fields=expected_fields or [])
        ):
            issues.append("required_field_missing")

    conflicting_fields = defaultdict(set)
    for link in evidence_links:
        conflicting_fields[link.field_name].add(link.candidate_value.strip())
    if not golden_contract_candidate and any(len(values) > 1 for values in conflicting_fields.values()):
        issues.append("conflicting_evidence")
    return sorted(dict.fromkeys(issues))


def _dynamic_priority_fields(*, product_type: str | None, expected_fields: list[str]) -> list[str]:
    normalized_type = str(product_type or "").strip().lower()
    priority = {
        "credit-card": {"product_name", "annual_fee", "purchase_interest_rate"},
        "mortgage": {"product_name", "mortgage_rate", "rate_type", "term_length_text"},
        "personal-loan": {"product_name", "interest_rate", "loan_amount_text", "term_length_text"},
        "line-of-credit": {"product_name", "interest_rate", "credit_limit_text", "secured_flag"},
    }.get(normalized_type, {"product_name"})
    return [field_name for field_name in expected_fields if field_name in priority]


def _apply_rate_evidence_fallback(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    if product_type_family not in {"savings", "gic"}:
        return
    if any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
        return

    match = _find_rate_evidence_fallback_match(evidence_links_for_output)
    if match is None:
        return

    percentages = _extract_rate_percentages(
        match.evidence_text_excerpt,
        product_type_family=product_type_family,
    )
    if not percentages:
        return

    unique_percentages = sorted(set(percentages))
    standard_rate = unique_percentages[0]
    public_display_rate = unique_percentages[-1]
    if _has_rate_promotional_context(match.evidence_text_excerpt):
        field_values = {
            "promotional_rate": public_display_rate,
            "public_display_rate": public_display_rate,
        }
    else:
        field_values = {
            "standard_rate": standard_rate,
            "public_display_rate": public_display_rate,
        }
    if len(unique_percentages) > 1 and "promotional_rate" not in field_values:
        field_values["promotional_rate"] = public_display_rate

    for field_name, value in field_values.items():
        normalized = float(value)
        candidate_payload[field_name] = normalized
        normalized_values_for_links[field_name] = normalized
        field_mapping_metadata[field_name] = {
            "source_field_name": match.field_name,
            "normalized_value": normalized,
            "normalization_method": "rate_evidence_fallback",
            "evidence_chunk_id": match.evidence_chunk_id,
        }
        evidence_links_for_output.append(
            NormalizationEvidenceLink(
                field_name=field_name,
                candidate_value=_stringify(normalized),
                evidence_chunk_id=match.evidence_chunk_id,
                evidence_text_excerpt=match.evidence_text_excerpt,
                source_document_id=match.source_document_id,
                source_snapshot_id=match.source_snapshot_id,
                citation_confidence=min(0.85, match.citation_confidence),
                model_execution_id=match.model_execution_id,
                anchor_type=match.anchor_type,
                anchor_value=match.anchor_value,
                page_no=match.page_no,
                chunk_index=match.chunk_index,
            )
        )

    runtime_notes.append(
        f"Supplemented missing rate fields from `{match.field_name}` evidence using generic rate evidence fallback."
    )


def _apply_credit_card_labeled_fallback(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    if product_type_family != "credit-card":
        return

    field_labels = {
        "purchase_interest_rate": r"(?:current\s+interest\s+rate\s*\(\s*purchases?\s*\)|purchases?\s+(?:interest\s+)?rate)",
        "balance_transfer_rate": r"(?:interest\s+rate\s*\(\s*balance\s+transfers?|balance\s+transfers?\s+(?:interest\s+)?rate|balance\s+transfers?\s+and\s+cash\s+advances?)",
        "cash_advance_rate": r"(?:cash\s+advances?\s+(?:interest\s+)?rate|balance\s+transfers?\s+and\s+cash\s+advances?)",
    }
    supplemented: list[str] = []
    for field_name, label_pattern in field_labels.items():
        if candidate_payload.get(field_name) not in {None, ""}:
            continue
        match = _find_fixed_credit_card_rate_evidence(
            evidence_links=evidence_links_for_output,
            label_pattern=label_pattern,
        )
        if match is None:
            continue
        evidence_link, rate = match
        candidate_payload[field_name] = rate
        normalized_values_for_links[field_name] = rate
        field_mapping_metadata[field_name] = {
            "source_field_name": evidence_link.field_name,
            "normalized_value": rate,
            "normalization_method": "credit_card_labeled_rate_fallback",
            "evidence_chunk_id": evidence_link.evidence_chunk_id,
            **mapping_contract_metadata(field_name),
        }
        evidence_links_for_output.append(
            NormalizationEvidenceLink(
                field_name=field_name,
                candidate_value=_stringify(rate),
                evidence_chunk_id=evidence_link.evidence_chunk_id,
                evidence_text_excerpt=evidence_link.evidence_text_excerpt,
                source_document_id=evidence_link.source_document_id,
                source_snapshot_id=evidence_link.source_snapshot_id,
                citation_confidence=min(0.9, evidence_link.citation_confidence),
                model_execution_id=evidence_link.model_execution_id,
                anchor_type=evidence_link.anchor_type,
                anchor_value=evidence_link.anchor_value,
                page_no=evidence_link.page_no,
                chunk_index=evidence_link.chunk_index,
            )
        )
        supplemented.append(field_name)
    if supplemented:
        runtime_notes.append(
            "Supplemented fixed credit-card rates only from explicit adjacent field labels: "
            + ", ".join(sorted(supplemented))
            + "."
        )


def _find_fixed_credit_card_rate_evidence(
    *,
    evidence_links: list[NormalizationEvidenceLink],
    label_pattern: str,
) -> tuple[NormalizationEvidenceLink, float] | None:
    for link in evidence_links:
        text = str(link.evidence_text_excerpt or "")
        for match in re.finditer(
            rf"{label_pattern}(?P<between>[\s\S]{{0,150}}?)(?P<rate>\d{{1,2}}(?:\.\d{{1,4}})?)\s*%",
            text,
            flags=re.IGNORECASE,
        ):
            local_context = (match.group("between") + text[match.end("rate"):match.end("rate") + 50]).lower()
            if re.search(r"(?:\+\s*(?:the\s+)?(?:bank\s+)?prime|prime\s+rate)", local_context):
                continue
            return link, float(match.group("rate"))
    return None


def _find_rate_evidence_fallback_match(
    evidence_links: list[NormalizationEvidenceLink],
) -> NormalizationEvidenceLink | None:
    ranked: list[tuple[int, float, NormalizationEvidenceLink]] = []
    for link in evidence_links:
        if expired_promotional_offer_end_date(link.evidence_text_excerpt) is not None:
            continue
        percentages = _extract_rate_percentages(link.evidence_text_excerpt)
        if not percentages:
            continue
        field_name = str(link.field_name or "").strip().lower()
        anchor_value = str(link.anchor_value or "").strip().lower()
        text = _normalize_text(link.evidence_text_excerpt).lower()
        score = 0
        if field_name in _RATE_CONTEXT_FIELDS:
            score += 5
        if "rate" in field_name:
            score += 2
        if any(token in anchor_value for token in ("rate", "interest", "return", "yield")):
            score += 2
        if any(token in text for token in ("interest rate", "annual interest", "posted rate", "return", "yield")):
            score += 2
        if any(token in text for token in ("principal protection", "100% reimbursed", "unauthorized transactions")):
            score -= 6
        if score <= 0:
            continue
        ranked.append((score, float(link.citation_confidence), link))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return ranked[0][2]


def _extract_rate_percentages(
    text: str | None,
    *,
    product_type_family: str | None = None,
) -> list[Decimal]:
    if not text:
        return []
    values: list[Decimal] = []
    for match in _PERCENT_RE.finditer(text):
        window_start = max(0, match.start() - 90)
        window_end = min(len(text), match.end() + 90)
        window = text[window_start:window_end].lower()
        if not any(token in window for token in ("interest", "rate", "return", "yield", "bonus")):
            continue
        if any(token in window for token in ("100% reimbursed", "unauthorized transactions", "principal protection")):
            continue
        if canonical_deposit_rate_suppression_reason(value=match.group(1), context=window) is not None:
            continue
        if product_type_family == "gic" and _rate_evidence_is_account_context(
            value=match.group(1),
            context=text,
        ):
            continue
        value = _as_decimal(match.group(1))
        if value is None:
            continue
        values.append(value)
    return values


def _rate_field_suppression_reason(
    *,
    field_name: str,
    field: NormalizationExtractedField,
    product_type_family: str | None = None,
) -> str | None:
    if field_name == "term_rate_table" and expired_promotional_offer_end_date(field.evidence_text_excerpt) is not None:
        return "expired_promotional_offer"
    if field_name not in _RATE_FIELDS:
        return None
    generic_reason = canonical_deposit_rate_suppression_reason(
        value=field.candidate_value,
        context=field.evidence_text_excerpt,
    )
    if generic_reason is not None:
        return generic_reason
    if product_type_family == "gic" and _rate_evidence_is_account_context(
        value=field.candidate_value,
        context=field.evidence_text_excerpt,
    ):
        return "other_product_rate_context"
    return None


def _rate_evidence_is_account_context(*, value: object, context: str | None) -> bool:
    normalized_context = " ".join(str(context or "").lower().split())
    normalized_value = str(value).replace("%", "").strip()
    if not normalized_context or not normalized_value:
        return False
    account_markers = ("personal account", "savings account", "chequing account", "checking account", "direct deposit")
    for match in re.finditer(re.escape(normalized_value), normalized_context):
        window = normalized_context[max(0, match.start() - 150): min(len(normalized_context), match.end() + 150)]
        if any(marker in window for marker in account_markers) and not any(
            marker in window for marker in ("gic rate", "gic rates", "guaranteed investment certificate", "term deposit rate")
        ):
            return True
    return False


def _has_rate_promotional_context(text: str | None) -> bool:
    lowered = str(text or "").lower()
    return any(
        token in lowered
        for token in (
            "bonus interest",
            "for 3 months",
            "for three months",
            "for the first",
            "limited-time",
            "limited time",
            "offer expires",
            "promotional",
            "special offer",
        )
    )


def _resolve_validation_status(validation_issue_codes: list[str]) -> str:
    error_issue_codes = {
        "required_field_missing",
        "invalid_taxonomy_code",
        "invalid_numeric_range",
        "invalid_term_value",
        "inconsistent_cross_field_logic",
    }
    if any(item in error_issue_codes for item in validation_issue_codes):
        return "error"
    if validation_issue_codes:
        return "warning"
    return "pass"


def _has_meaningful_value(value: object) -> bool:
    return value not in (None, "", [], {})


def _meets_deposit_golden_contract(
    *,
    product_type: str | None,
    product_type_family: str | None,
    product_name: str | None,
    currency: str | None,
    candidate_payload: dict[str, object],
    dynamic_product_type: bool,
) -> bool:
    if dynamic_product_type:
        return False
    if (product_type_family or _canonical_product_type_family(product_type)) not in {"chequing", "savings", "gic"}:
        return False
    required_identity = (
        product_type,
        product_name,
        currency,
        candidate_payload.get("status"),
        candidate_payload.get("last_verified_at"),
    )
    if any(value in {None, ""} for value in required_identity):
        return False
    if any(field_name not in candidate_payload for field_name in _DEPOSIT_GOLDEN_REQUIRED_PAYLOAD_FIELDS):
        return False

    tags = candidate_payload.get("tags")
    if not isinstance(tags, list) or not tags:
        return False
    term_rates = candidate_payload.get("term_rates")
    if not isinstance(term_rates, list):
        return False
    if any(field_name not in candidate_payload for field_name in _DEPOSIT_GOLDEN_RATE_FIELDS):
        return False
    return True


def _refine_product_name_from_source_metadata(
    *,
    product_name: str | None,
    source_metadata: dict[str, object],
    runtime_notes: list[str],
) -> str | None:
    if not _looks_like_generic_product_name(product_name):
        return product_name

    discovery_metadata = source_metadata.get("discovery_metadata")
    if not isinstance(discovery_metadata, dict):
        return product_name

    for metadata_key in ("primary_heading", "page_title"):
        candidate = _clean_product_name_candidate(str(discovery_metadata.get(metadata_key) or ""))
        if candidate and not _looks_like_generic_product_name(candidate):
            runtime_notes.append(
                f"Replaced generic product_name `{product_name}` with `{candidate}` from source discovery metadata `{metadata_key}`."
            )
            return candidate
    return product_name


def _looks_like_generic_product_name(value: object) -> bool:
    normalized = re.sub(r"\s+", " ", str(value or "").strip().lower())
    return normalized in {
        "",
        "account",
        "accounts",
        "bank account",
        "bank accounts",
        "banking",
        "personal banking",
        "savings",
        "savings accounts",
        "chequing",
        "chequing accounts",
        "gic",
        "gics",
        "gic / term deposit",
        "term deposit",
        "term deposits",
        "credit card",
        "credit cards",
        "mortgage",
        "mortgages",
        "residential mortgage",
        "residential mortgages",
        "personal loan",
        "personal loans",
        "line of credit",
        "lines of credit",
    }


def _clean_product_name_candidate(value: str) -> str | None:
    cleaned = value.split("|", 1)[0]
    cleaned = re.sub(r"\s+opens in\b.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ?.:-")
    if not cleaned:
        return None
    words = cleaned.split()
    half = len(words) // 2
    if len(words) >= 4 and len(words) % 2 == 0 and words[:half] == words[half:]:
        cleaned = " ".join(words[:half])
    return cleaned


def _compute_source_confidence(
    *,
    validation_status: str,
    validation_issue_codes: list[str],
    candidate_payload: dict[str, object],
    evidence_links: list[NormalizationEvidenceLink],
    product_type: str | None,
    product_type_family: str | None,
    product_name: str | None,
    currency: str | None,
    dynamic_product_type: bool = False,
) -> float:
    required_values = [product_type, product_name, currency, candidate_payload.get("status"), candidate_payload.get("last_verified_at")]
    completeness = sum(1 for item in required_values if item not in {None, ""}) / len(required_values)
    requiredness_type = product_type_family or product_type
    golden_contract_candidate = _meets_deposit_golden_contract(
        product_type=product_type,
        product_type_family=product_type_family,
        product_name=product_name,
        currency=currency,
        candidate_payload=candidate_payload,
        dynamic_product_type=dynamic_product_type,
    )
    if golden_contract_candidate:
        completeness = 1.0
    if requiredness_type == "chequing" and any(candidate_payload.get(field_name) not in {None, ""} for field_name in (*_FEE_FIELDS, "fee_waiver_condition")):
        completeness = min(1.0, completeness + 0.15)
    if requiredness_type == "savings" and any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
        completeness = min(1.0, completeness + 0.15)
    if (
        requiredness_type == "gic"
        and any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS)
        and candidate_payload.get("minimum_deposit") not in {None, ""}
        and any(candidate_payload.get(field_name) not in {None, ""} for field_name in ("term_length_days", "term_length_text"))
    ):
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
    if golden_contract_candidate and validation_status == "pass" and not validation_issue_codes:
        score = max(score, 0.88)
    if dynamic_product_type:
        score = min(score - 0.08, 0.74)
    return round(max(0.0, min(0.99, score)), 4)


def _build_field_evidence_link_records(
    *,
    candidate_id: str,
    normalized_values_for_links: dict[str, object],
    source_document_id: str,
    evidence_links: list[NormalizationEvidenceLink],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for link in evidence_links:
        if link.field_name not in normalized_values_for_links:
            continue
        candidate_value = normalized_values_for_links[link.field_name]
        field_evidence_link_id = _build_field_evidence_link_id(candidate_id, link.field_name, link.evidence_chunk_id)
        if field_evidence_link_id in seen_ids:
            continue
        seen_ids.add(field_evidence_link_id)
        records.append(
            {
                "field_evidence_link_id": field_evidence_link_id,
                "candidate_id": candidate_id,
                "product_version_id": None,
                "evidence_chunk_id": link.evidence_chunk_id,
                "source_document_id": link.source_document_id or source_document_id,
                "field_name": link.field_name,
                "candidate_value": _stringify(candidate_value),
                "citation_confidence": round(link.citation_confidence, 4),
            }
    )
    return records


def _uses_dynamic_product_type(*, product_type: str | None, item: NormalizationInput) -> bool:
    if not product_type:
        return bool(item.source_metadata.get("product_type_dynamic"))
    if product_type in _ACTIVE_PRODUCT_TYPES:
        return False
    return bool(item.source_metadata.get("product_type_dynamic", True))


def _canonical_product_type_family(product_type: str | None) -> str | None:
    normalized = str(product_type or "").strip().lower()
    if normalized in _ACTIVE_PRODUCT_TYPES:
        return normalized
    if any(token in normalized for token in ("gic", "term-deposit", "term_deposit", "term deposit")):
        return "gic"
    if "savings" in normalized or "saving" in normalized:
        return "savings"
    if "chequing" in normalized or "checking" in normalized:
        return "chequing"
    if normalized in {"credit-card", "mortgage", "personal-loan", "line-of-credit"}:
        return normalized
    if "credit card" in normalized:
        return "credit-card"
    if "mortgage" in normalized:
        return "mortgage"
    if "line of credit" in normalized or "heloc" in normalized:
        return "line-of-credit"
    if "loan" in normalized:
        return "personal-loan"
    return None


def _enforce_dynamic_field_contract(
    *,
    expected_fields: object,
    candidate_payload: dict[str, object],
    normalized_values_for_links: dict[str, object],
    field_mapping_metadata: dict[str, object],
    runtime_notes: list[str],
) -> None:
    allowed_fields = {
        str(field_name).strip()
        for field_name in expected_fields if str(field_name).strip()
    } if isinstance(expected_fields, (list, tuple, set)) else set()
    if not allowed_fields:
        return
    allowed_fields.update(_DYNAMIC_OPERATIONAL_FIELDS)
    suppressed_fields = [
        field_name
        for field_name in candidate_payload
        if field_name not in allowed_fields
    ]
    for field_name in suppressed_fields:
        candidate_payload.pop(field_name, None)
        normalized_values_for_links.pop(field_name, None)
        metadata = dict(field_mapping_metadata.get(field_name) or {})
        metadata.update(
            {
                "normalized_value": None,
                "normalization_method": "dynamic_product_field_contract",
                "suppressed_reason": "field_not_registered_for_product_type",
            }
        )
        field_mapping_metadata[field_name] = metadata
    if suppressed_fields:
        runtime_notes.append(
            "Suppressed fields outside the registered product-type contract: "
            + ", ".join(sorted(suppressed_fields))
            + "."
        )


def _clean_product_context_fields(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    normalized_values_for_links: dict[str, object] | None = None,
    field_mapping_metadata: dict[str, object] | None = None,
    runtime_notes: list[str] | None = None,
    evidence_context_by_field: dict[str, str] | None = None,
) -> None:
    suppressed_fields: list[str] = []
    for field_name, value in list(candidate_payload.items()):
        if field_name in _CORE_FIELDS:
            continue
        evidence_context = (evidence_context_by_field or {}).get(field_name, "")
        should_suppress = _looks_like_non_rate_numeric_context(
            field_name=field_name,
            value=value,
            context=evidence_context,
        ) or _looks_like_other_product_section(context=evidence_context) or _looks_like_credit_card_field_mismatch(
            field_name=field_name,
            value=value,
            context=evidence_context,
            product_type_family=product_type_family,
        )
        if isinstance(value, str):
            should_suppress = should_suppress or (
                _looks_like_navigation_contamination(value)
                or _looks_like_non_value_rate(field_name=field_name, value=value)
                or _looks_like_non_value_eligibility(field_name=field_name, value=value)
                or _looks_like_invalid_field_type(field_name=field_name, value=value)
                or _looks_like_unresolved_placeholder(value)
                or _looks_like_wrong_frequency_context(
                    field_name=field_name,
                    value=value,
                    context=evidence_context,
                )
                or _looks_like_invalid_payment_frequency(field_name=field_name, value=value)
                or _looks_like_invalid_amortization(field_name=field_name, value=value)
                or _looks_like_invalid_application_method(
                    field_name=field_name,
                    value=value,
                    product_type_family=product_type_family,
                )
                or _looks_like_non_value_lending_field(
                    field_name=field_name,
                    value=value,
                    product_type_family=product_type_family,
                )
                or _looks_like_broad_page_copy(field_name=field_name, value=value)
            )
        if should_suppress:
            candidate_payload.pop(field_name, None)
            if normalized_values_for_links is not None:
                normalized_values_for_links.pop(field_name, None)
            if field_mapping_metadata is not None:
                field_mapping_metadata.pop(field_name, None)
            suppressed_fields.append(field_name)

    if suppressed_fields and runtime_notes is not None:
        runtime_notes.append(
            "Suppressed navigation or marketing copy that was incorrectly mapped as product data: "
            + ", ".join(sorted(suppressed_fields))
            + "."
        )

    if product_type_family == "credit-card" and isinstance(candidate_payload.get("eligibility_text"), str):
        eligibility = str(candidate_payload["eligibility_text"])
        cleaned_eligibility = re.sub(
            r"\s+(?:to\s+qualify|to\s+take\s+advantage),?\s+you\s+must\s+not\s+"
            r"(?:currently\s+)?(?:hold|have)[\s\S]{0,160}?past\s+\d+\s+months?\.?",
            "",
            eligibility,
            flags=re.IGNORECASE,
        ).strip()
        if cleaned_eligibility != eligibility and cleaned_eligibility:
            candidate_payload["eligibility_text"] = cleaned_eligibility
            if normalized_values_for_links is not None:
                normalized_values_for_links["eligibility_text"] = cleaned_eligibility
            if field_mapping_metadata is not None and "eligibility_text" in field_mapping_metadata:
                metadata = dict(field_mapping_metadata["eligibility_text"] or {})
                metadata["normalized_value"] = cleaned_eligibility
                metadata["normalization_method"] = "credit_card_offer_eligibility_cleanup"
                field_mapping_metadata["eligibility_text"] = metadata
            if runtime_notes is not None:
                runtime_notes.append("Removed acquisition-offer history conditions from ongoing card eligibility.")

    duplicated_fields = _duplicated_page_copy_fields(candidate_payload)
    for field_name in duplicated_fields:
        candidate_payload.pop(field_name, None)
        if normalized_values_for_links is not None:
            normalized_values_for_links.pop(field_name, None)
        if field_mapping_metadata is not None:
            field_mapping_metadata.pop(field_name, None)
    if duplicated_fields and runtime_notes is not None:
        runtime_notes.append(
            "Suppressed duplicated page copy mapped to multiple fields: "
            + ", ".join(sorted(duplicated_fields))
            + "."
        )

    _suppress_inconsistent_term_length(
        candidate_payload=candidate_payload,
        normalized_values_for_links=normalized_values_for_links,
        field_mapping_metadata=field_mapping_metadata,
        runtime_notes=runtime_notes,
    )

    withdrawal_text = str(candidate_payload.get("withdrawal_limit_text") or "").strip()
    withdrawal_match = re.search(
        r"\b(?:one|1)\s+free\s+withdrawal(?:s)?\s+(?:a|per)\s+month\b",
        withdrawal_text,
        flags=re.IGNORECASE,
    )
    if withdrawal_match is not None and len(withdrawal_text) > len(withdrawal_match.group(0)) + 40:
        cleaned_withdrawal = _clean_text_value(withdrawal_match.group(0)).capitalize() + "."
        candidate_payload["withdrawal_limit_text"] = cleaned_withdrawal
        if normalized_values_for_links is not None:
            normalized_values_for_links["withdrawal_limit_text"] = cleaned_withdrawal
        if field_mapping_metadata is not None and "withdrawal_limit_text" in field_mapping_metadata:
            metadata = dict(field_mapping_metadata["withdrawal_limit_text"] or {})
            metadata["normalized_value"] = cleaned_withdrawal
            metadata["normalization_method"] = "semantic_withdrawal_limit_cleanup"
            field_mapping_metadata["withdrawal_limit_text"] = metadata
        if runtime_notes is not None:
            runtime_notes.append("Reduced broad savings copy to the explicit monthly free-withdrawal limit.")

    if product_type_family == "gic":
        description = str(candidate_payload.get("description_short") or "").strip()
        if description and _gic_text_conflicts_with_product_context(description):
            candidate_payload.pop("description_short", None)

        eligibility = str(candidate_payload.get("eligibility_text") or "").strip()
        lowered_eligibility = eligibility.lower()
        if lowered_eligibility.startswith("what you need to know") and "type cashable access" in lowered_eligibility:
            candidate_payload.pop("eligibility_text", None)

        calculation_method = str(candidate_payload.get("interest_calculation_method") or "").strip()
        if calculation_method:
            simple_interest_match = re.search(
                r"simple interest is calculated and paid at maturity",
                calculation_method,
                flags=re.IGNORECASE,
            )
            if simple_interest_match is not None:
                candidate_payload["interest_calculation_method"] = _clean_text_value(simple_interest_match.group(0))


def _looks_like_navigation_contamination(value: str) -> bool:
    normalized = " ".join(value.lower().split())
    if normalized in {
        "home",
        "go to main content",
        "go to page content",
        "skip to main content",
        "document go to main content",
        "document go to page content",
        "document skip to main content",
        "learn more",
        "read more",
    }:
        return True
    if any(marker in normalized for marker in ("go to main content", "skip to main content")) and len(normalized) < 120:
        return True
    if normalized.startswith("document ") and len(normalized.split()) <= 4:
        return True
    if len(normalized) < 140:
        return False
    navigation_markers = (
        "main navigation",
        "online banking",
        "find an atm",
        "find a branch",
        "about us",
        "contact us",
        "frequently asked questions",
        "calculators",
        "forms and documents",
        "credit cards",
        "chequing accounts",
        "savings accounts",
        "personal loans",
        "mortgages",
        "find your bdm",
        "get started",
        "tools and support",
        "advisor access",
        "marketing material",
        "workflows",
        "our accounts",
        "investment accounts",
        "mortgage loan calculator",
        "mortgage rates",
        "faqs",
        "investor relations",
        "careers",
        "bug bounty",
        "public accountability statement",
        "community news",
        "privacy & legal",
        "accessibility",
    )
    return sum(marker in normalized for marker in navigation_markers) >= 3


def _looks_like_other_product_section(*, context: str) -> bool:
    normalized = " ".join(context.lower().replace("-", " ").replace("_", " ").split())
    return any(
        marker in normalized
        for marker in (
            "our other products",
            "our other investment products",
            "other banking products",
            "related products",
        )
    )


def _looks_like_credit_card_field_mismatch(
    *,
    field_name: str,
    value: object,
    context: str,
    product_type_family: str | None,
) -> bool:
    if product_type_family != "credit-card":
        return False
    normalized_context = " ".join(context.lower().split())
    if field_name == "annual_fee" and str(value).strip() in {"0", "0.0", "0.00"}:
        secondary_zero = re.search(
            r"annual fee for (?:the )?(?:authorized|additional|secondary|second) (?:card|cardholder)[^$]{0,35}\$\s*0\b",
            normalized_context,
        )
        primary_zero = re.search(
            r"annual fee(?: for (?:the )?(?:primary )?cardholder)?[^$\n]{0,30}\$\s*0\b",
            context,
            flags=re.IGNORECASE,
        )
        return secondary_zero is not None and primary_zero is None
    if field_name in {"purchase_interest_rate", "balance_transfer_rate", "cash_advance_rate"}:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return True
        labels = {
            "purchase_interest_rate": r"(?:purchases?\s+(?:interest\s+)?rate|interest\s+rate\s*\(\s*purchases?\s*\))",
            "balance_transfer_rate": r"(?:balance\s+transfers?\s+(?:interest\s+)?rate|balance\s+transfers?\s+and\s+cash\s+advances?)",
            "cash_advance_rate": r"(?:cash\s+advances?\s+(?:interest\s+)?rate|balance\s+transfers?\s+and\s+cash\s+advances?)",
        }
        value_pattern = re.escape(f"{numeric_value:g}")
        match = re.search(
            rf"{labels[field_name]}[\s\S]{{0,150}}?{value_pattern}\s*%",
            context,
            flags=re.IGNORECASE,
        )
        if match is None:
            return True
        local_context = context[match.start():match.end() + 50].lower()
        return re.search(r"(?:\+\s*(?:the\s+)?(?:bank\s+)?prime|prime\s+rate)", local_context) is not None
    if field_name == "rewards_summary":
        low_rate_identity = any(marker in normalized_context for marker in ("lowest rate card", "low-interest credit card", "pay off your balance faster"))
        rewards_evidence = any(marker in normalized_context for marker in ("reward", "points", "cash back", "cashback"))
        return low_rate_identity and not rewards_evidence
    return False


def _looks_like_non_value_rate(*, field_name: str, value: str) -> bool:
    normalized_field = field_name.strip().lower()
    if not (normalized_field.endswith("_rate") or normalized_field in {"rate", "mortgage_rate", "interest_rate"}):
        return False
    normalized_value = " ".join(value.split())
    if len(normalized_value) >= 180:
        return True
    if len(normalized_value) < 45:
        return False
    if normalized_field == "post_maturity_interest_rate" and len(normalized_value) >= 160:
        return not re.search(r"(?:%|\bprime\b)", normalized_value, flags=re.IGNORECASE)
    return not re.search(r"(?:\d|%|\bprime\b)", normalized_value, flags=re.IGNORECASE)


def _looks_like_non_rate_numeric_context(*, field_name: str, value: object, context: str) -> bool:
    normalized_field = field_name.strip().lower()
    if not (normalized_field.endswith("_rate") or normalized_field in {"rate", "mortgage_rate", "interest_rate"}):
        return False
    if isinstance(value, str) and not re.fullmatch(r"\s*\d{1,3}(?:\.\d+)?\s*%?\s*", value):
        return False
    return (
        canonical_deposit_rate_suppression_reason(value=value, context=context) is not None
        or _looks_like_unresolved_placeholder(context)
    )


def _looks_like_invalid_field_type(*, field_name: str, value: str) -> bool:
    normalized_field = field_name.strip().lower()
    if normalized_field.endswith("_flag") or normalized_field in {"secured_flag", "redeemable_flag"}:
        return value.strip().lower() not in {"true", "false", "yes", "no", "1", "0"}
    return False


def _looks_like_unresolved_placeholder(value: str) -> bool:
    normalized = value.lower()
    return bool(re.search(r"(?:\{\{|\}\}|\$\{|rds%|%rate\b|\[object object\])", normalized))


def _looks_like_wrong_frequency_context(*, field_name: str, value: str, context: str) -> bool:
    if field_name not in {"compounding_frequency", "interest_payment_frequency"}:
        return False
    normalized_value = value.strip().lower()
    if normalized_value not in {"weekly", "biweekly", "bi-weekly", "monthly", "semi-monthly"}:
        return False
    normalized_context = " ".join(context.lower().split())
    return "payment frequency" in normalized_context and not any(
        marker in normalized_context
        for marker in ("interest payment", "interest is paid", "interest compounded", "interest compounds")
    )


def _looks_like_invalid_payment_frequency(*, field_name: str, value: str) -> bool:
    if field_name != "payment_frequency":
        return False
    normalized = " ".join(value.lower().split())
    if len(normalized) > 100 or any(marker in normalized for marker in ("calculator", "prepayment", "pre-payment", "special offers")):
        return True
    frequency_markers = ("weekly", "biweekly", "bi-weekly", "semi-monthly", "monthly", "accelerated")
    return not any(marker in normalized for marker in frequency_markers)


def _looks_like_invalid_amortization(*, field_name: str, value: str) -> bool:
    if field_name != "amortization_text":
        return False
    normalized = " ".join(value.lower().split())
    if len(normalized) > 160:
        return True
    return re.search(r"\b\d{1,3}\s*(?:year|years|month|months)\b", normalized) is None


def _looks_like_invalid_application_method(
    *,
    field_name: str,
    value: str,
    product_type_family: str | None,
) -> bool:
    if field_name != "application_method":
        return False
    normalized = " ".join(value.lower().split())
    if any(
        marker in normalized
        for marker in (
            "must be registered for online",
            "need to register",
            "sign on to online banking",
            "sign in to online banking",
        )
    ):
        return True
    if product_type_family in {"gic", "credit-card", "mortgage", "personal-loan", "line-of-credit"}:
        targets_bank_account = any(
            marker in normalized for marker in ("bank account", "chequing account", "savings account")
        )
        mentions_current_product = any(
            marker in normalized
            for marker in ("gic", "investment", "credit card", "mortgage", "loan", "line of credit")
        )
        if targets_bank_account and not mentions_current_product:
            return True
    return False


def _looks_like_non_value_lending_field(
    *,
    field_name: str,
    value: str,
    product_type_family: str | None,
) -> bool:
    if product_type_family not in {"credit-card", "mortgage", "personal-loan", "line-of-credit"}:
        return False
    normalized = " ".join(value.lower().split())
    if field_name == "monthly_payment_text" and re.fullmatch(
        r"monthly fees?\s*(?:free|\$?0(?:\.00)?)", normalized
    ):
        return True
    if field_name == "fees_text" and normalized in {"monthly fees free", "monthly fee free"}:
        return True
    if field_name == "fees_text" and any(
        marker in normalized for marker in ("penalty free", "penalty-free", "without penalty", "prepay", "repay")
    ) and not any(marker in normalized for marker in ("fee", "$")):
        return True
    if field_name == "monthly_payment_text" and any(
        marker in normalized for marker in ("calculate", "calculator", "see how much", "estimate your")
    ) and not re.search(r"(?:\$|\b\d[\d,.]*\b|weekly|biweekly|bi-weekly|monthly)", normalized):
        return True
    if field_name == "loan_amount_text" and len(normalized) > 100:
        return re.search(r"(?:\$|\b\d[\d,.]*\b|\bminimum\b|\bmaximum\b|\bup to\b)", normalized) is None
    if field_name in {"security_requirement", "collateral_text"}:
        if normalized in {
            "security requirement",
            "security requirements",
            "collateral",
            "what collateral is required",
            "is collateral required",
        }:
            return True
        navigation_markers = (
            "document",
            "rates",
            "contact us",
            "search",
            "login",
            "log in",
            "go to homepage",
            "online banking",
        )
        return sum(marker in normalized for marker in navigation_markers) >= 3
    if field_name == "prepayment_privileges":
        return not any(
            marker in normalized
            for marker in ("prepay", "pre-pay", "prepayment", "pre-payment", "repay", "penalty", "privilege")
        )
    return False


def _looks_like_broad_page_copy(*, field_name: str, value: str) -> bool:
    normalized = " ".join(value.split())
    if field_name == "application_method" and normalized.lower().startswith("how do i apply"):
        return True
    concise_fields = {
        "fees_text",
        "minimum_payment_text",
        "credit_limit_text",
        "monthly_payment_text",
        "rate_type",
        "payment_frequency",
        "security_requirement",
        "collateral_text",
        "deposit_insurance",
        "term_length_text",
        "prepayment_privileges",
    }
    return len(normalized) >= 240 and field_name in concise_fields


def _duplicated_page_copy_fields(candidate_payload: dict[str, object]) -> set[str]:
    by_value: dict[str, list[str]] = {}
    for field_name, value in candidate_payload.items():
        if not isinstance(value, str):
            continue
        normalized = " ".join(value.lower().split())
        if len(normalized) < 120:
            continue
        by_value.setdefault(normalized, []).append(field_name)
    return {
        field_name
        for field_names in by_value.values()
        if len(field_names) >= 2
        for field_name in field_names
    }


def _suppress_inconsistent_term_length(
    *,
    candidate_payload: dict[str, object],
    normalized_values_for_links: dict[str, object] | None,
    field_mapping_metadata: dict[str, object] | None,
    runtime_notes: list[str] | None,
) -> None:
    term_days = candidate_payload.get("term_length_days")
    term_text = str(candidate_payload.get("term_length_text") or "")
    if term_days in {None, ""} or not term_text:
        return
    try:
        numeric_days = int(str(term_days))
    except (TypeError, ValueError):
        return
    durations: list[int] = []
    for amount, unit in re.findall(r"(?<!\d)(\d{1,3})\s*(day|days|month|months|year|years)\b", term_text, flags=re.IGNORECASE):
        value = int(amount)
        lowered_unit = unit.lower()
        durations.append(value if lowered_unit.startswith("day") else value * 30 if lowered_unit.startswith("month") else value * 365)
    if not durations:
        return
    minimum_days = min(durations)
    maximum_days = max(durations)
    tolerance = max(7, round(minimum_days * 0.08))
    if minimum_days - tolerance <= numeric_days <= maximum_days + max(7, round(maximum_days * 0.08)):
        return
    candidate_payload.pop("term_length_days", None)
    if normalized_values_for_links is not None:
        normalized_values_for_links.pop("term_length_days", None)
    if field_mapping_metadata is not None:
        metadata = dict(field_mapping_metadata.get("term_length_days") or {})
        metadata.update(
            {
                "normalized_value": None,
                "normalization_method": "cross_field_term_safety",
                "suppressed_reason": "term_days_conflict_with_term_text",
            }
        )
        field_mapping_metadata["term_length_days"] = metadata
    if runtime_notes is not None:
        runtime_notes.append(
            f"Suppressed `term_length_days` value `{numeric_days}` because it conflicts with `{term_text}`."
        )


def _looks_like_non_value_eligibility(*, field_name: str, value: str) -> bool:
    if field_name not in {"eligibility", "eligibility_text"}:
        return False
    normalized = " ".join(value.lower().split())
    calculator_cta = "calculator" in normalized and any(
        marker in normalized
        for marker in ("calculate", "find out how much", "may qualify to borrow", "estimate how much")
    ) and not any(
        marker in normalized
        for marker in ("must ", "requires ", "eligible if", "at least", "minimum ", "resident", "income", "credit score")
    )
    estimate_output = any(
        marker in normalized
        for marker in ("receive an estimate", "get an estimate", "estimate for the total")
    ) and "eligible" in normalized and not any(
        marker in normalized
        for marker in ("must ", "requires ", "eligible if", "at least", "minimum ", "resident", "income", "credit score")
    )
    return calculator_cta or estimate_output or len(normalized) < 120 and (
        normalized.startswith("and ")
        or "we understand that" in normalized
        or normalized in {"learn more", "get started", "contact us"}
    )


def _apply_product_type_aliases(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    runtime_notes: list[str],
) -> str | None:
    if product_type_family != "gic" or candidate_payload.get("minimum_deposit") not in {None, ""}:
        return None
    for alias_field in ("minimum_investment", "minimum_balance"):
        alias_value = candidate_payload.get(alias_field)
        if alias_value in {None, ""}:
            continue
        decimal_value = _parse_canonical_decimal(field_name="minimum_deposit", value=alias_value)
        if decimal_value is None:
            continue
        candidate_payload["minimum_deposit"] = float(decimal_value)
        runtime_notes.append(
            f"Mapped `{alias_field}` to `minimum_deposit` for GIC requiredness because the source uses investment/deposit wording."
        )
        return alias_field
    return None


def _gic_text_conflicts_with_product_context(text: str) -> bool:
    lowered = text.lower()
    if any(token in lowered for token in ("gic", "term deposit", "guaranteed investment certificate")):
        return False
    return any(
        token in lowered
        for token in (
            "mutual fund",
            "mutual funds",
            "account conversion",
            "credit card",
            "mortgage",
            "chequing",
            "checking",
            "loan",
        )
    )


def _clean_text_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ;.")


def _normalize_dynamic_fields_with_ai(
    *,
    item: NormalizationInput,
    extracted_by_field: dict[str, NormalizationExtractedField],
    candidate_payload: dict[str, object],
) -> tuple[dict[str, Any], list[str], dict[str, Any] | None]:
    if not llm_provider_configured():
        return {}, ["Dynamic product normalization kept heuristic mode because the OpenAI provider or API key was not configured."], None

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "product_name": {"type": "string"},
            "subtype_code": {"type": "string"},
            "source_subtype_label": {"type": "string"},
            "normalized_fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "field_name": {"type": "string"},
                        "value_type": {"type": "string", "enum": ["string", "decimal", "integer", "boolean", "json"]},
                        "candidate_value": {"type": "string"},
                    },
                    "required": ["field_name", "value_type", "candidate_value"],
                },
            },
        },
        "required": ["summary", "product_name", "subtype_code", "source_subtype_label", "normalized_fields"],
    }
    try:
        response_payload, usage = invoke_openai_json_schema(
            model_id=configured_model_id(),
            instructions=(
                "You are the FPDS Normalization Agent for operator-defined financial product types. "
                "Map extracted fields into a conservative canonical candidate payload. "
                "Keep only values grounded in the extracted inputs and return only fields listed in expected_fields. "
                "Never map cashback, rewards, prepayment, equity, down-payment, or instalment-plan percentages to generic annual rate fields. "
                "Boolean fields must remain booleans, and navigation or whole-page marketing copy must be omitted. "
                "Use subtype_code `other` unless the subtype is obvious from the product definition and extracted evidence."
            ),
            payload={
                "product_type": item.source_metadata.get("product_type"),
                "product_type_name": item.source_metadata.get("product_type_name"),
                "product_type_description": item.source_metadata.get("product_type_description"),
                "fallback_policy": item.source_metadata.get("fallback_policy"),
                "expected_fields": list(item.source_metadata.get("expected_fields", [])),
                "field_contract": field_contract_payload(list(item.source_metadata.get("expected_fields", []))),
                "extracted_fields": [
                    {
                        "field_name": field.field_name,
                        "candidate_value": str(field.candidate_value),
                        "value_type": field.value_type,
                        "confidence": field.confidence,
                    }
                    for field in extracted_by_field.values()
                ],
                "current_candidate_payload": candidate_payload,
            },
            schema_name="dynamic_product_normalization",
            schema=schema,
        )
    except Exception as exc:
        return {}, [f"Dynamic product normalization AI fallback was unavailable: {exc}"], None

    normalized_payload: dict[str, object] = {}
    expected_fields = {
        str(field_name).strip()
        for field_name in item.source_metadata.get("expected_fields", [])
        if str(field_name).strip()
    }
    for item_payload in response_payload.get("normalized_fields", []):
        field_name = str(item_payload.get("field_name") or "").strip()
        if not field_name or expected_fields and field_name not in expected_fields:
            continue
        raw_value = str(item_payload.get("candidate_value") or "")
        if field_name in _RATE_FIELDS and "term_rate_table" in expected_fields:
            term_rows = _normalize_term_rate_table(raw_value)
            if term_rows and len(term_rows) > 1:
                normalized_payload["term_rate_table"] = term_rows
                continue
        normalized_value = _normalize_field_value(
            field_name=field_name,
            value=raw_value,
            value_type=str(item_payload.get("value_type") or "string"),
        )
        if normalized_value is None:
            continue
        normalized_payload[field_name] = normalized_value
    notes = []
    summary = str(response_payload.get("summary") or "").strip()
    if summary:
        notes.append(summary)
    if normalized_payload:
        notes.append(f"Dynamic product normalization AI mapped {len(normalized_payload)} canonical field(s).")
    return {
        "product_name": _coalesce_string(response_payload.get("product_name")),
        "subtype_code": _coalesce_string(response_payload.get("subtype_code"), "other"),
        "source_subtype_label": _coalesce_string(response_payload.get("source_subtype_label")),
        "candidate_payload": normalized_payload,
    }, notes, usage


def _infer_subtype_code(
    *,
    product_type: str | None,
    currency: str | None,
    candidate_payload: dict[str, object],
) -> tuple[str | None, str | None]:
    if product_type is None:
        return None, None
    text = " ".join(
        str(candidate_payload.get(field_name, ""))
        for field_name in (
            "product_name",
            "description_short",
            "notes",
            "eligibility_text",
            "cheque_book_info",
            "cashability",
            "term_options",
            "tier_definition_text",
            "withdrawal_limit_text",
            "interest_calculation_method",
        )
    ).lower()
    product_name = _coalesce_string(candidate_payload.get("product_name"))
    headline_text = " ".join(
        str(candidate_payload.get(field_name, ""))
        for field_name in (
            "product_name",
            "description_short",
        )
    ).lower()
    if product_type == "savings":
        if currency and currency != "CAD":
            return "foreign_currency", None
        if any(token in text for token in ("premium", "high interest", "hisa")):
            return "high_interest", None
        if any(token in text for token in ("student", "youth")):
            return "youth", None
        return "standard", None
    if product_type == "chequing":
        if _has_positive_rate(candidate_payload):
            return "interest_bearing", None
        if any(token in headline_text for token in ("premium", "vip", "ultimate", "signature", "all-inclusive", "all inclusive")):
            return "premium", None
        included_transactions = _as_int(candidate_payload.get("included_transactions"))
        if (
            any(token in text for token in ("package", "bundle", "bundled"))
            or _truthy(candidate_payload.get("unlimited_transactions_flag"))
            or _truthy(candidate_payload.get("interac_e_transfer_included"))
            or (included_transactions is not None and included_transactions >= 25)
        ):
            return "package", None
        return "standard", None
    if product_type == "gic":
        if any(token in text for token in ("market linked", "market smart", "index linked", "equity linked")):
            return "market_linked", None
        if "non-redeemable" in text or "non redeemable" in text or "non-cashable" in text or "non cashable" in text:
            return "non_redeemable", None
        if "redeemable" in text or "cashable" in text or "flexible gic" in text:
            return "redeemable", None
        return "other", product_name
    return "other", product_name


def _resolve_gic_redeemability_flags(
    *,
    product_type_family: str | None,
    subtype_code: str | None,
    candidate_payload: dict[str, object],
    normalized_values_for_links: dict[str, object],
    field_mapping_metadata: dict[str, object],
    runtime_notes: list[str],
) -> None:
    if product_type_family != "gic":
        return
    if not (_truthy(candidate_payload.get("redeemable_flag")) and _truthy(candidate_payload.get("non_redeemable_flag"))):
        return

    signal = _gic_redeemability_signal(subtype_code=subtype_code, candidate_payload=candidate_payload)
    if signal == "redeemable":
        _set_gic_redeemability_flags(
            redeemable=True,
            non_redeemable=False,
            normalized_values_for_links=normalized_values_for_links,
            field_mapping_metadata=field_mapping_metadata,
            candidate_payload=candidate_payload,
            source_signal=signal,
        )
    elif signal == "non_redeemable":
        _set_gic_redeemability_flags(
            redeemable=False,
            non_redeemable=True,
            normalized_values_for_links=normalized_values_for_links,
            field_mapping_metadata=field_mapping_metadata,
            candidate_payload=candidate_payload,
            source_signal=signal,
        )
    else:
        for field_name in ("redeemable_flag", "non_redeemable_flag"):
            candidate_payload.pop(field_name, None)
            normalized_values_for_links.pop(field_name, None)
            field_mapping_metadata.pop(field_name, None)

    runtime_notes.append(
        "Resolved conflicting GIC redeemability flags from product-level subtype, name, or tag signals instead of broad family-page evidence."
    )


def _gic_redeemability_signal(*, subtype_code: str | None, candidate_payload: dict[str, object]) -> str | None:
    if subtype_code in {"redeemable", "non_redeemable"}:
        return subtype_code
    if subtype_code == "market_linked":
        return None

    signal_text = _product_signal_text(
        candidate_payload,
        field_names=("product_name", "source_subtype_label", "tags"),
    )
    if any(token in signal_text for token in ("cashable or non redeemable", "redeemable or non redeemable")):
        return None
    if any(token in signal_text for token in ("non redeemable", "non cashable")):
        return "non_redeemable"
    if any(token in signal_text for token in ("redeemable", "cashable", "flexible gic")):
        return "redeemable"
    return None


def _set_gic_redeemability_flags(
    *,
    redeemable: bool,
    non_redeemable: bool,
    normalized_values_for_links: dict[str, object],
    field_mapping_metadata: dict[str, object],
    candidate_payload: dict[str, object],
    source_signal: str,
) -> None:
    resolved_values = {
        "redeemable_flag": redeemable,
        "non_redeemable_flag": non_redeemable,
    }
    for field_name, resolved_value in resolved_values.items():
        candidate_payload[field_name] = resolved_value
        field_mapping_metadata[field_name] = {
            **dict(field_mapping_metadata.get(field_name) or {}),
            "normalized_value": resolved_value,
            "normalization_method": "gic_redeemability_conflict_resolution",
            "source_signal": source_signal,
        }
        if resolved_value:
            normalized_values_for_links[field_name] = resolved_value
        else:
            normalized_values_for_links.pop(field_name, None)


def _product_signal_text(candidate_payload: dict[str, object], *, field_names: tuple[str, ...]) -> str:
    values: list[str] = []
    for field_name in field_names:
        value = candidate_payload.get(field_name)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        else:
            values.append(str(value or ""))
    return re.sub(r"[\W_]+", " ", " ".join(values).lower()).strip()


def _infer_target_customer_tags(candidate_payload: dict[str, object]) -> list[str]:
    tags: list[str] = []
    merged_text = " ".join(str(candidate_payload.get(field_name, "")) for field_name in ("product_name", "description_short", "notes", "eligibility_text")).lower()
    if "student" in merged_text or "youth" in merged_text or _truthy(candidate_payload.get("student_plan_flag")):
        tags.append("student")
    if "newcomer" in merged_text or _truthy(candidate_payload.get("newcomer_plan_flag")):
        tags.append("newcomer")
    if "senior" in merged_text:
        tags.append("senior")
    if any(
        token in merged_text
        for token in (
            "business account",
            "business banking",
            "small business",
            "for businesses",
            "business clients",
            "business owners",
        )
    ):
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
    if value is None or value == "":
        return None
    if field_name in _JSON_FIELDS:
        return _normalize_term_rate_table(value)
    if field_name in _NUMERIC_FIELDS:
        decimal_value = _parse_canonical_decimal(field_name=field_name, value=value)
        return float(decimal_value) if decimal_value is not None else None
    value_type = canonical_value_type(field_name, value_type)
    if value_type == "boolean":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() == "true"
    if value_type == "integer":
        integer_value = _as_int(value)
        return integer_value if integer_value is not None else None
    if value_type == "decimal":
        decimal_value = _as_decimal(value)
        return float(decimal_value) if decimal_value is not None else None
    if value_type == "json":
        return _normalize_term_rate_table(value) if field_name == "term_rate_table" else value
    return str(value).strip()


def _normalize_term_rate_table(value: object) -> list[dict[str, object]] | None:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = _parse_term_rate_text(value)
    else:
        parsed = value
    if not isinstance(parsed, list):
        return None

    rows: list[dict[str, object]] = []
    seen: set[tuple[object, object, object]] = set()
    for item in parsed:
        if not isinstance(item, dict):
            continue
        term_label = _normalize_text(item.get("term_label")) or None
        term_length_days = _as_int(item.get("term_length_days"))
        if term_length_days is None and term_label:
            term_length_days = _term_label_to_days(term_label)
        rate_decimal = _parse_canonical_decimal(field_name="base_12_month_rate", value=item.get("rate"))
        minimum_deposit_decimal = _parse_canonical_decimal(field_name="minimum_deposit", value=item.get("minimum_deposit"))
        notes = _normalize_text(item.get("notes")) or None
        if term_label is None and term_length_days is None and rate_decimal is None:
            continue
        key = (term_label, term_length_days, float(rate_decimal) if rate_decimal is not None else None)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "term_label": term_label,
                "term_length_days": term_length_days,
                "rate": float(rate_decimal) if rate_decimal is not None else None,
                "minimum_deposit": float(minimum_deposit_decimal) if minimum_deposit_decimal is not None else None,
                "notes": notes,
            }
        )
    return rows[:24] or None


def _parse_term_rate_text(value: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    pattern = re.compile(
        r"(?P<term>\d{1,3}\s*(?:day|days|month|months|year|years))\s*[:\-]?\s*(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(value):
        rows.append(
            {
                "term_label": match.group("term"),
                "rate": match.group("rate"),
                "notes": None,
            }
        )
    return rows


def _apply_field_qualifier_notes(
    *,
    product_type_family: str | None,
    currency: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
) -> None:
    rate_fields = {
        field_name
        for field_name in candidate_payload
        if field_contract(field_name) is not None and field_contract(field_name).unit == "percentage_points"
    }
    for field_name in rate_fields:
        parts = ["Stored as percentage points"]
        if candidate_payload.get("term_rate_table") and field_name != "term_rate_table":
            parts.append("term-specific rates are listed separately")
        if candidate_payload.get("introductory_rate_flag") is True:
            period = str(candidate_payload.get("promotional_period_text") or "").strip()
            parts.append(f"promotional rate{f' ({period})' if period else ''}")
        if product_type_family == "savings":
            method = str(candidate_payload.get("interest_calculation_method") or "").strip()
            frequency = str(candidate_payload.get("interest_payment_frequency") or "").strip()
            if method:
                parts.append(method)
            if frequency:
                parts.append(f"interest paid {frequency.lower()}")
        _set_field_note(field_mapping_metadata, field_name, "; ".join(parts) + ".")

    if candidate_payload.get("term_rate_table"):
        parts = ["Each row stores an annual percentage-point rate for its stated term"]
        if candidate_payload.get("non_redeemable_flag") is True:
            parts.append("product is non-redeemable")
        compounding = str(candidate_payload.get("compounding_frequency") or "").strip()
        payout = str(candidate_payload.get("payout_option") or "").strip()
        if compounding:
            parts.append(f"compounding: {compounding}")
        if payout:
            parts.append(f"payout: {payout}")
        _set_field_note(field_mapping_metadata, "term_rate_table", "; ".join(parts) + ".")

    fee_waiver = str(candidate_payload.get("fee_waiver_condition") or "").strip()
    if fee_waiver:
        for field_name in ("monthly_fee", "public_display_fee"):
            if field_name in candidate_payload:
                _set_field_note(field_mapping_metadata, field_name, f"Fee may be waived when this condition is met: {fee_waiver}")

    if candidate_payload.get("minimum_deposit") is not None:
        _set_field_note(field_mapping_metadata, "minimum_deposit", f"Minimum deposit in {currency or 'the product currency'}.")


def _set_field_note(field_mapping_metadata: dict[str, object], field_name: str, note: str) -> None:
    metadata = dict(field_mapping_metadata.get(field_name) or {})
    metadata.update(mapping_contract_metadata(field_name))
    metadata["field_note"] = note[:500]
    field_mapping_metadata[field_name] = metadata


def _term_label_to_days(term_label: str) -> int | None:
    if re.search(r"\d{1,3}\s*(?:-|–|—|to)\s*\d{1,3}\s*days?\b", term_label, flags=re.IGNORECASE):
        return None
    match = re.search(r"(?<!\d)(\d{1,3})\s*(day|days|month|months|year|years)\b", term_label, flags=re.IGNORECASE)
    if match is None:
        return None
    value = _as_int(match.group(1))
    if value is None:
        return None
    unit = match.group(2).lower()
    if unit.startswith("day"):
        return value
    if unit.startswith("month"):
        return value * 30
    if unit.startswith("year"):
        return value * 365
    return None


def _parse_canonical_decimal(*, field_name: str, value: object) -> Decimal | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float):
        return Decimal(str(value))

    normalized = str(value).strip()
    if not normalized:
        return None
    lowered = normalized.lower()
    if field_name in _FEE_FIELDS and any(token in lowered for token in ("no fee", "no monthly fee", "fees no fees", "fee-free", "free")):
        return Decimal("0")

    compact = normalized.replace(",", "").replace("$", "").replace("%", "").strip()
    compact = re.sub(r"\b(?:cad|cdn|dollars?)\b", "", compact, flags=re.IGNORECASE).strip()
    compact = re.sub(r"\s+", "", compact)
    try:
        return Decimal(compact)
    except (InvalidOperation, ValueError):
        return None


def _clean_promotional_period_fields(candidate_payload: dict[str, object]) -> None:
    value = candidate_payload.get("promotional_period_text")
    if value in {None, ""}:
        return
    text = str(value).strip()
    lowered = text.lower()
    period_tokens = (
        "limited time",
        "until ",
        "through ",
        "expires",
        "expiry",
        "for the first",
        "for first",
        "introductory period",
        "promotional period",
        "months",
        "days",
        "weeks",
        "from ",
        " to ",
    )
    if lowered.startswith("why choose") or not any(token in lowered for token in period_tokens):
        candidate_payload.pop("promotional_period_text", None)


def _field_value(extracted_by_field: dict[str, NormalizationExtractedField], field_name: str) -> object | None:
    field = extracted_by_field.get(field_name)
    if field is None:
        return None
    return field.candidate_value


def _as_decimal(value: object) -> Decimal | None:
    return _parse_canonical_decimal(field_name="standard_rate", value=value)


def _as_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _coalesce_string(*values: object) -> str | None:
    for value in values:
        if value is None:
            continue
        normalized = str(value).strip()
        if normalized:
            return normalized
    return None


def _normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _looks_like_language_code(value: str) -> bool:
    normalized = value.strip()
    return bool(re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?", normalized))


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value in {None, ""}:
        return False
    return str(value).strip().lower() == "true"


def _has_positive_rate(candidate_payload: dict[str, object]) -> bool:
    for field_name in _RATE_FIELDS:
        decimal_value = _as_decimal(candidate_payload.get(field_name))
        if decimal_value is not None and decimal_value > 0:
            return True
    return False


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
        "normalized_source_url": item.normalized_source_url,
        "candidate_key": item.candidate_key,
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
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    provider_request_id: str | None = None,
) -> dict[str, object]:
    return {
        "llm_usage_id": _build_usage_id(model_execution_id),
        "model_execution_id": model_execution_id,
        "run_id": run_id,
        "candidate_id": None,
        "provider_request_id": provider_request_id,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost": estimated_cost_usd(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
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
            "candidate_key": item.candidate_key,
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


def _build_candidate_id(*, run_id: str, source_document_id: str, parsed_document_id: str, candidate_key: str | None = None) -> str:
    key = candidate_key or "default"
    digest = sha256(f"{run_id}|{source_document_id}|{parsed_document_id}|{key}|candidate".encode("utf-8")).hexdigest()[:16]
    return f"cand-{digest}"


def _build_model_execution_id(*, run_id: str, source_document_id: str, parsed_document_id: str, candidate_key: str | None = None) -> str:
    key = candidate_key or "default"
    digest = sha256(f"{run_id}|{source_document_id}|{parsed_document_id}|{key}|normalization".encode("utf-8")).hexdigest()[:16]
    return f"modelexec-{digest}"


def _build_field_evidence_link_id(candidate_id: str, field_name: str, evidence_chunk_id: str) -> str:
    digest = sha256(f"{candidate_id}|{field_name}|{evidence_chunk_id}".encode("utf-8")).hexdigest()[:16]
    return f"fel-{digest}"


def _build_usage_id(model_execution_id: str) -> str:
    digest = sha256(f"{model_execution_id}|llm_usage".encode("utf-8")).hexdigest()[:16]
    return f"usage-{digest}"


def _stringify(value: object) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
