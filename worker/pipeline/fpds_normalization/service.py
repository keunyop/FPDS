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
from worker.pipeline.fpds_approval_policy import populated_dynamic_decision_fields
from worker.country_defaults import default_currency_for_country
from worker.pipeline.fpds_field_contract import (
    canonical_value_type,
    field_contract,
    field_contract_payload,
    mapping_contract_metadata,
    value_matches_contract,
)
from worker.pipeline.fpds_rate_safety import (
    advertised_promotional_total_rate,
    bounded_rate_evidence_context,
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
from .grounded_product_expansion import expand_grounded_product_inputs
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
_MAX_MONTHLY_ACCOUNT_FEE = Decimal("500")
_MAX_ANNUAL_CARD_FEE = Decimal("2000")
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
            grounded_product_items = expand_grounded_product_inputs(item)
            if grounded_product_items:
                for candidate_item in grounded_product_items:
                    result = self._normalize_single_input(
                        run_id=run_id,
                        item=candidate_item,
                        correlation_id=correlation_id,
                        request_id=request_id,
                    )
                    source_results.append(result)
                    if result.normalization_action == "failed":
                        partial_completion_flag = True
                continue
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
    currency = _coalesce_string(
        _field_value(extracted_by_field, "currency"),
        default_currency_for_country(country_code),
        "XXX",
    )
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
                **_official_grounding_mapping_metadata(field),
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
            **_official_grounding_mapping_metadata(field),
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
    dynamic_field_names: set[str] = set()
    if dynamic_product_type:
        dynamic_payload, dynamic_notes, dynamic_usage = _normalize_dynamic_fields_with_ai(
            item=item,
            extracted_by_field=extracted_by_field,
            candidate_payload=candidate_payload,
        )
        runtime_notes.extend(dynamic_notes)
        dynamic_candidate_payload = dict(dynamic_payload.get("candidate_payload", {}))
        dynamic_field_names = set(dynamic_candidate_payload)
        for field_name, value in dynamic_candidate_payload.items():
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
                **(
                    _official_grounding_mapping_metadata(extracted_field)
                    if extracted_field is not None
                    else {}
                ),
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
        # Numeric fields on operator-defined product types require exact
        # unit-bearing evidence whether introduced by extraction or the AI
        # mapping pass.
        dynamic_field_names.update(
            field_name
            for field_name in candidate_payload
            if (contract := field_contract(field_name)) is not None
            and contract.value_type in {"decimal", "integer"}
        )

    evidence_links_for_output = list(item.evidence_links)
    evidence_context_by_field = {
        field_name: " ".join(
            part
            for part in (field.anchor_value or "", field.evidence_text_excerpt or "")
            if part
        )
        for field_name, field in extracted_by_field.items()
    }
    for field_name in dynamic_field_names:
        contract = field_contract(field_name)
        if contract is None or contract.value_type not in {"decimal", "integer"}:
            continue
        evidence_context_by_field[field_name] = _find_dynamic_numeric_evidence_context(
            field_name=field_name,
            value=candidate_payload.get(field_name),
            evidence_links=item.evidence_links,
        )
    _clean_product_context_fields(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        normalized_values_for_links=normalized_values_for_links,
        field_mapping_metadata=field_mapping_metadata,
        runtime_notes=runtime_notes,
        evidence_context_by_field=evidence_context_by_field,
        evidence_excerpt_by_field={
            field_name: str(field.evidence_text_excerpt or "")
            for field_name, field in extracted_by_field.items()
        },
        enforce_percentage_evidence_grounding=(
            str(item.source_metadata.get("product_profile_expansion_mode") or "").strip().lower() != "fixture"
        ),
        expired_offer_present=any(
            expired_promotional_offer_end_date(link.evidence_text_excerpt) is not None
            for link in item.evidence_links
        ),
        dynamic_field_names=dynamic_field_names,
    )
    _clean_chequing_fee_waiver_consistency(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _align_minimum_balance_to_fee_waiver(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _align_public_display_fee(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
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
    _align_savings_labeled_header_standard_rate(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _align_gic_labeled_posted_and_promotional_rates(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _align_advertised_promotional_total(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _suppress_uncombined_savings_rate_boost(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _align_ongoing_additive_bonus_total(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _complete_gic_term_rate_table_from_split_evidence(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _align_gic_representative_rates_from_term_table(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _align_public_display_rate(
        product_type_family=product_type_family,
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )
    _align_promotional_period_from_evidence(
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
        runtime_notes=runtime_notes,
    )

    subtype_code, source_subtype_label = _infer_subtype_code(
        product_type=product_type_family,
        country_code=country_code,
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
    if dynamic_product_type and product_type_family not in {"chequing", "savings", "gic"}:
        _suppress_unverified_dynamic_fields(
            candidate_payload=candidate_payload,
            normalized_values_for_links=normalized_values_for_links,
            field_mapping_metadata=field_mapping_metadata,
            runtime_notes=runtime_notes,
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

    numeric_fields = set(_NUMERIC_FIELDS) | {
        field_name
        for field_name in candidate_payload
        if (contract := field_contract(field_name)) is not None and contract.value_type == "decimal"
    }
    for field_name in numeric_fields:
        value = candidate_payload.get(field_name)
        if value in {None, ""}:
            continue
        decimal_value = _as_decimal(value)
        if decimal_value is None:
            issues.append("invalid_numeric_range")
            continue
        contract = field_contract(field_name)
        is_rate = field_name in _RATE_FIELDS or (contract is not None and contract.unit == "percentage_points")
        is_annual_deposit_rate = field_name in _RATE_FIELDS or (
            product_type_family in {"chequing", "savings", "gic"}
            and contract is not None
            and contract.unit == "percentage_points"
            and field_name != "highest_rate"
        )
        is_fee = field_name in _FEE_FIELDS or (
            contract is not None and contract.unit == "currency_amount" and field_name.endswith("_fee")
        )
        if is_annual_deposit_rate and (
            decimal_value < Decimal("0")
            or canonical_deposit_rate_suppression_reason(value=decimal_value) is not None
        ):
            issues.append("invalid_numeric_range")
        if field_name == "highest_rate" and not (Decimal("0") <= decimal_value <= Decimal("100")):
            issues.append("invalid_numeric_range")
        if is_rate and not is_annual_deposit_rate and field_name != "highest_rate" and decimal_value >= Decimal("100"):
            issues.append("invalid_numeric_range")
        if not is_rate and decimal_value < 0:
            issues.append("invalid_numeric_range")
        fee_limit = _MAX_ANNUAL_CARD_FEE if field_name == "annual_fee" else _MAX_MONTHLY_ACCOUNT_FEE
        if is_fee and decimal_value >= fee_limit:
            issues.append("invalid_numeric_range")

    public_display_rate = _as_decimal(candidate_payload.get("public_display_rate"))
    if public_display_rate is not None and any(
        comparison_rate is not None and public_display_rate < comparison_rate
        for comparison_rate in (
            _as_decimal(candidate_payload.get("standard_rate")),
            _as_decimal(candidate_payload.get("promotional_rate")),
        )
    ):
        issues.append("inconsistent_cross_field_logic")

    advertised_total = next(
        (
            value
            for field_name in ("interest_rate_summary", "promotional_period_text")
            if (value := advertised_promotional_total_rate(str(candidate_payload.get(field_name) or ""))) is not None
        ),
        None,
    )
    if advertised_total is not None and any(
        comparison_rate is not None and comparison_rate != advertised_total
        for comparison_rate in (
            _as_decimal(candidate_payload.get("promotional_rate")),
            public_display_rate,
        )
    ):
        issues.append("inconsistent_cross_field_logic")

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
        if re.search(r"\bno[- ]fee\b", str(product_name or ""), flags=re.IGNORECASE) and any(
            fee is not None and fee > 0
            for fee in (
                _as_decimal(candidate_payload.get("monthly_fee")),
                _as_decimal(candidate_payload.get("public_display_fee")),
            )
        ):
            issues.append("inconsistent_cross_field_logic")
    if requiredness_type == "savings" and not golden_contract_candidate:
        if not any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS):
            issues.append("required_field_missing")
        if (
            candidate_payload.get("promotional_rate") not in {None, ""}
            and candidate_payload.get("standard_rate") in {None, ""}
            and candidate_payload.get("base_12_month_rate") in {None, ""}
        ):
            issues.append("required_field_missing")
    if requiredness_type == "gic" and not golden_contract_candidate:
        if (
            not any(candidate_payload.get(field_name) not in {None, ""} for field_name in _RATE_FIELDS)
            and not _has_dynamic_gic_rate_mechanism(candidate_payload)
        ):
            issues.append("required_field_missing")
        if candidate_payload.get("minimum_deposit") in {None, ""}:
            issues.append("required_field_missing")
        if (
            candidate_payload.get("term_length_days") in {None, ""}
            and candidate_payload.get("term_length_text") in {None, ""}
            and not _has_gic_term_evidence(candidate_payload)
        ):
            issues.append("required_field_missing")
        if _truthy(candidate_payload.get("redeemable_flag")) and _truthy(candidate_payload.get("non_redeemable_flag")):
            issues.append("inconsistent_cross_field_logic")
        if candidate_payload.get("minimum_balance") not in {None, ""} and candidate_payload.get("minimum_deposit") in {None, ""}:
            issues.append("inconsistent_cross_field_logic")
    if dynamic_product_type:
        populated_decision_fields = populated_dynamic_decision_fields(
            product_type=product_type,
            country_code=country_code,
            expected_fields=expected_fields or [],
            candidate_payload=candidate_payload,
        )
        contractless_meaningful_values = [
            value
            for field_name, value in candidate_payload.items()
            if field_name not in {"status", "last_verified_at", "bank_name", "product_name", "source_subtype_label", "subtype_code"}
        ]
        if not populated_decision_fields and (
            bool(expected_fields)
            or not any(_has_meaningful_value(value) for value in contractless_meaningful_values)
        ):
            issues.append("required_field_missing")
        if subtype_code in {None, ""}:
            issues.append("ambiguous_mapping")

    conflicting_fields = defaultdict(set)
    for link in evidence_links:
        conflicting_fields[link.field_name].add(link.candidate_value.strip())
    if not golden_contract_candidate and any(len(values) > 1 for values in conflicting_fields.values()):
        issues.append("conflicting_evidence")
    return sorted(dict.fromkeys(issues))


def _has_dynamic_gic_rate_mechanism(candidate_payload: dict[str, object]) -> bool:
    summary = str(candidate_payload.get("interest_rate_summary") or "").strip().lower()
    if not summary:
        return False
    return any(
        marker in summary
        for marker in (
            "variable interest rate",
            "variable rate",
            "variable return",
            "linked to changes",
            "linked to the performance",
            "return is linked",
            "based on a formula",
            "rate at time of purchase",
            "rates available at time of purchase",
            "current interest rate environment",
        )
    )


def _has_gic_term_evidence(candidate_payload: dict[str, object]) -> bool:
    """Accept a structured multi-term table in place of one scalar term."""

    rows = candidate_payload.get("term_rate_table")
    if not isinstance(rows, list):
        return False
    return any(
        isinstance(row, dict)
        and (
            row.get("term_label") not in {None, ""}
            or row.get("term_length_days") not in {None, ""}
        )
        for row in rows
    )


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


def _align_savings_labeled_header_standard_rate(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Recover an ongoing savings rate from a compact product-summary header."""

    if product_type_family != "savings":
        return
    pattern = re.compile(
        r"(?<![\d.])(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%\s*"
        r"(?:[^a-z0-9]{0,18})\s*(?:interest\s+rate|annual\s+percentage\s+yield|apy)\b[\s\S]{0,100}?"
        r"(?:monthly\s+(?:account\s+)?fee|minimum\s+balance|no\s+fees?|no\s+minimum\s+deposit)",
        flags=re.IGNORECASE,
    )
    ranked: list[tuple[float, int, NormalizationEvidenceLink, Decimal]] = []
    for link in evidence_links_for_output:
        text = _normalize_text(link.evidence_text_excerpt)
        for match in pattern.finditer(text):
            value = _as_decimal(match.group("rate"))
            if value is None:
                continue
            local_prefix = text[max(0, match.start() - 120):match.start()].lower()
            if any(
                marker in local_prefix
                for marker in (
                    "promotional rate",
                    "new client offer",
                    "welcome offer",
                    "limited-time offer",
                    "limited time offer",
                )
            ):
                continue
            local_context = text[max(0, match.start() - 80):min(len(text), match.end() + 130)]
            if canonical_deposit_rate_suppression_reason(value=value, context=local_context) is not None:
                continue
            ranked.append((float(link.citation_confidence), -match.start(), link, value))
    if not ranked:
        return
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    _, _, source_link, standard_rate = ranked[0]
    if _as_decimal(candidate_payload.get("standard_rate")) == standard_rate:
        return
    _replace_rate_value_from_link(
        field_name="standard_rate",
        value=standard_rate,
        source_link=source_link,
        normalization_method="savings_labeled_header_standard_rate_alignment",
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
    )
    runtime_notes.append(
        f"Aligned `standard_rate` to the explicitly labeled savings product-header rate `{float(standard_rate)}`."
    )


def _align_gic_labeled_posted_and_promotional_rates(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Align a GIC's exact promotional and posted rate labels from one excerpt."""

    if product_type_family != "gic":
        return
    selected: tuple[NormalizationEvidenceLink, Decimal, Decimal] | None = None
    for link in evidence_links_for_output:
        text = _normalize_text(
            " ".join(
                part
                for part in (str(link.candidate_value or ""), link.evidence_text_excerpt or "")
                if part
            )
        )
        if not re.search(
            r"\b(?:promotional|special|bonus)\s+rate\b|\b(?:prom)?otional\s+rate\b",
            text,
            flags=re.IGNORECASE,
        ):
            continue
        for posted_match in re.finditer(
            r"\bposted\s+rate\s*:?\s*(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
            text,
            flags=re.IGNORECASE,
        ):
            posted_rate = _as_decimal(posted_match.group("rate"))
            prefix = text[max(0, posted_match.start() - 220):posted_match.start()]
            promotional_matches = list(_PERCENT_RE.finditer(prefix))
            if posted_rate is None or not promotional_matches:
                continue
            promotional_rate = _as_decimal(promotional_matches[-1].group(1))
            if promotional_rate is None or promotional_rate < posted_rate:
                continue
            selected = (link, posted_rate, promotional_rate)
            break
        if selected is not None:
            break
    if selected is None:
        return
    source_link, posted_rate, promotional_rate = selected
    for field_name, value in (
        ("standard_rate", posted_rate),
        ("promotional_rate", promotional_rate),
        ("public_display_rate", promotional_rate),
    ):
        _replace_rate_value_from_link(
            field_name=field_name,
            value=value,
            source_link=source_link,
            normalization_method="labeled_gic_posted_promotional_alignment",
            candidate_payload=candidate_payload,
            field_mapping_metadata=field_mapping_metadata,
            normalized_values_for_links=normalized_values_for_links,
            evidence_links_for_output=evidence_links_for_output,
        )
    candidate_payload["introductory_rate_flag"] = True
    runtime_notes.append(
        "Aligned the GIC standard, promotional, and public rates from exact posted/promotional labels."
    )


def _align_advertised_promotional_total(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Prefer an explicitly advertised promotional total over additive components."""

    if product_type_family not in {"savings", "gic"}:
        return

    total_match = _find_advertised_promotional_total(evidence_links_for_output)
    labeled_match = _find_registration_scoped_promotional_rate(
        evidence_links_for_output,
        registered_product=_registered_savings_product_identity(candidate_payload.get("product_name")),
    )
    if labeled_match is not None:
        total_match = labeled_match
    additive_match = _find_additive_promotional_total(evidence_links_for_output)
    regular_match = None
    if additive_match is not None and (
        total_match is None or total_match[0] is additive_match[0]
    ):
        additive_link, additive_total, additive_regular = additive_match
        total_match = (additive_link, additive_total)
        regular_match = (additive_link, additive_regular)
    if total_match is None:
        return
    total_link, total_rate = total_match
    regular_match = (
        regular_match
        if additive_match is not None and total_match[0] is additive_match[0]
        else _find_regular_component_rate(evidence_links_for_output)
    )
    _replace_rate_value_from_link(
        field_name="promotional_rate",
        value=total_rate,
        source_link=total_link,
        normalization_method="advertised_promotional_total_alignment",
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
    )
    _replace_rate_value_from_link(
        field_name="public_display_rate",
        value=total_rate,
        source_link=total_link,
        normalization_method="advertised_promotional_total_alignment",
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
    )

    if regular_match is not None:
        regular_link, regular_rate = regular_match
        _replace_rate_value_from_link(
            field_name="standard_rate",
            value=regular_rate,
            source_link=regular_link,
            normalization_method="advertised_promotional_component_alignment",
            candidate_payload=candidate_payload,
            field_mapping_metadata=field_mapping_metadata,
            normalized_values_for_links=normalized_values_for_links,
            evidence_links_for_output=evidence_links_for_output,
        )
    elif (
        product_type_family == "savings"
        and _as_decimal(candidate_payload.get("standard_rate")) == total_rate
    ):
        candidate_payload.pop("standard_rate", None)
        normalized_values_for_links.pop("standard_rate", None)
        evidence_links_for_output[:] = [
            link for link in evidence_links_for_output if link.field_name != "standard_rate"
        ]
        metadata = dict(field_mapping_metadata.get("standard_rate") or {})
        metadata.update(
            {
                "normalized_value": None,
                "normalization_method": "promotional_total_standard_rate_safety",
                "suppressed_reason": "promotional_rate_not_ongoing_rate",
            }
        )
        field_mapping_metadata["standard_rate"] = metadata
        runtime_notes.append(
            "Suppressed a savings standard rate identical to the advertised promotion because no separate ongoing rate was found."
        )

    runtime_notes.append(
        f"Aligned the advertised promotional total and public display rate to `{float(total_rate)}`."
    )


def _suppress_uncombined_savings_rate_boost(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Do not publish an incremental APY boost as the total promotional APY."""

    if product_type_family != "savings" or _as_decimal(candidate_payload.get("promotional_rate")) is None:
        return
    mapping = dict(field_mapping_metadata.get("promotional_rate") or {})
    if mapping.get("normalization_method") in {
        "advertised_promotional_total_alignment",
        "advertised_promotional_component_alignment",
    }:
        return
    contexts = [
        _normalize_text(link.evidence_text_excerpt)
        for link in evidence_links_for_output
        if _normalize_text(link.evidence_text_excerpt)
    ]
    if not any(re.search(r"\b\d{1,2}(?:\.\d{1,4})?\s*%\s*(?:apy\s+)?rate\s+boost\b", text, re.IGNORECASE) for text in contexts):
        return
    promotional_rate = _as_decimal(candidate_payload.get("promotional_rate"))
    if any(advertised_promotional_total_rate(text) == promotional_rate for text in contexts):
        return

    for field_name in ("promotional_rate", "promotional_period_text", "introductory_rate_flag"):
        candidate_payload.pop(field_name, None)
        normalized_values_for_links.pop(field_name, None)
        field_mapping = dict(field_mapping_metadata.get(field_name) or {})
        field_mapping.update(
            {
                "normalized_value": None,
                "normalization_method": "incremental_rate_boost_safety",
                "suppressed_reason": "incremental_rate_boost_not_total_apy",
            }
        )
        field_mapping_metadata[field_name] = field_mapping
    evidence_links_for_output[:] = [
        link
        for link in evidence_links_for_output
        if link.field_name not in {"promotional_rate", "promotional_period_text", "introductory_rate_flag"}
    ]
    runtime_notes.append(
        "Omitted an incremental APY rate boost because the official page did not state the resulting total promotional APY."
    )


def _find_advertised_promotional_total(
    evidence_links: list[NormalizationEvidenceLink],
) -> tuple[NormalizationEvidenceLink, Decimal] | None:
    ranked: list[tuple[int, float, NormalizationEvidenceLink, Decimal]] = []
    for link in evidence_links:
        if str(link.field_name or "").strip().lower() not in {
            "interest_rate_summary",
            "promotional_period_text",
            "promotional_rate",
            "public_display_rate",
            "term_rate_table",
        }:
            continue
        text = _normalize_text(link.evidence_text_excerpt)
        value = advertised_promotional_total_rate(text)
        if value is None:
            continue
        lowered = text.lower()
        score = 20 if "total" in lowered else 18 if "earn up to" in lowered else 16
        ranked.append((score, float(link.citation_confidence), link, value))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    _, _, link, value = ranked[0]
    return link, value


def _registered_savings_product_identity(product_name: object) -> bool:
    normalized = _normalize_text(str(product_name or "")).lower()
    return bool(
        re.search(r"\b(?:registered|rrsp|rsp|rif|tfsa|fhsa|resp|rdsp|lira|lrif)\b", normalized)
    )


def _find_registration_scoped_promotional_rate(
    evidence_links: list[NormalizationEvidenceLink],
    *,
    registered_product: bool,
) -> tuple[NormalizationEvidenceLink, Decimal] | None:
    label = r"(?<!non[- ])registered" if registered_product else r"non[- ]registered"
    pattern = re.compile(
        rf"\b{label}\s+promotional\s+rate\b\D{{0,40}}(?P<rate>\d{{1,2}}(?:\.\d{{1,4}})?)\s*%"
        rf"|(?P<rate_first>\d{{1,2}}(?:\.\d{{1,4}})?)\s*%\s+{label}\s+promotional\s+rate\b",
        flags=re.IGNORECASE,
    )
    ranked: list[tuple[float, NormalizationEvidenceLink, Decimal]] = []
    for link in evidence_links:
        text = _normalize_text(link.evidence_text_excerpt)
        if not text or expired_promotional_offer_end_date(text) is not None:
            continue
        match = pattern.search(text)
        if match is None:
            continue
        value = _as_decimal(match.group("rate") or match.group("rate_first"))
        if value is None or canonical_deposit_rate_suppression_reason(value=value, context=text) is not None:
            continue
        ranked.append((float(link.citation_confidence), link, value))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    _, link, value = ranked[0]
    return link, value


def _find_regular_component_rate(
    evidence_links: list[NormalizationEvidenceLink],
) -> tuple[NormalizationEvidenceLink, Decimal] | None:
    ranked: list[tuple[float, NormalizationEvidenceLink, Decimal]] = []
    pattern = (
        r"\bregular\s+interest\s+rate\b\s*(?:of\s+)?(?:up\s+to\s+)?"
        r"(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%"
    )
    for link in evidence_links:
        text = _normalize_text(link.evidence_text_excerpt)
        lowered = text.lower()
        if not text or expired_promotional_offer_end_date(text) is not None:
            continue
        if not any(marker in lowered for marker in ("promotional", "promo", "bonus", "on top of")):
            continue
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match is None:
            continue
        value = _as_decimal(match.group("rate"))
        if value is None:
            continue
        if canonical_deposit_rate_suppression_reason(value=value, context=text) is not None:
            continue
        ranked.append((float(link.citation_confidence), link, value))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    _, link, value = ranked[0]
    return link, value


def _find_additive_promotional_total(
    evidence_links: list[NormalizationEvidenceLink],
) -> tuple[NormalizationEvidenceLink, Decimal, Decimal] | None:
    """Recover a time-limited total only from explicitly additive components."""

    promotional_pattern = re.compile(
        r"\b(?:promo(?:tional)?|bonus)\s+(?:interest\s+)?rate\b\D{0,45}"
        r"(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
        flags=re.IGNORECASE,
    )
    regular_pattern = re.compile(
        r"\bregular\s+(?:annual\s+)?interest\s+rate\b\s*(?:of\s+)?(?:up\s+to\s+)?"
        r"(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
        flags=re.IGNORECASE,
    )
    ranked: list[tuple[float, NormalizationEvidenceLink, Decimal, Decimal]] = []
    for link in evidence_links:
        text = _normalize_text(link.evidence_text_excerpt)
        lowered = text.lower()
        if expired_promotional_offer_end_date(text) is not None:
            continue
        if not any(marker in lowered for marker in ("earn both", "on top of", "in addition to", "plus the regular")):
            continue
        if not any(marker in lowered for marker in ("first 3 months", "first three months", "for 3 months", "promotional")):
            continue
        promotional_match = promotional_pattern.search(text)
        regular_match = regular_pattern.search(text)
        if promotional_match is None or regular_match is None:
            continue
        promotional = _as_decimal(promotional_match.group("rate"))
        regular = _as_decimal(regular_match.group("rate"))
        if promotional is None or regular is None or promotional <= 0 or regular < 0:
            continue
        total = promotional + regular
        if total <= 0 or total > Decimal("20"):
            continue
        ranked.append((float(link.citation_confidence), link, total, regular))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    _, link, total, regular = ranked[0]
    return link, total, regular


def _align_ongoing_additive_bonus_total(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Publish a grounded ongoing total when a page states regular + extra bonus.

    This is distinct from a time-limited acquisition promotion: the recurring
    regular rate remains ``standard_rate``, while ``public_display_rate`` may
    show the higher attainable ongoing rate under the stated program condition.
    """

    if product_type_family != "savings":
        return
    regular_pattern = re.compile(
        r"\bregular\s+(?:annual\s+)?interest\s+rate\b\D{0,45}(?P<regular>\d{1,2}(?:\.\d{1,4})?)\s*%",
        flags=re.IGNORECASE,
    )
    bonus_pattern = re.compile(
        r"\bbonus\s+interest\s+rate\b[\s\S]{0,90}?\b(?:earn\s+)?(?:an\s+)?(?:extra|additional)\s+"
        r"(?P<bonus>\d{1,2}(?:\.\d{1,4})?)\s*%",
        flags=re.IGNORECASE,
    )
    ranked: list[tuple[float, NormalizationEvidenceLink, Decimal, Decimal]] = []
    for link in evidence_links_for_output:
        text = _normalize_text(link.evidence_text_excerpt)
        lowered = text.lower()
        if any(
            marker in lowered
            for marker in ("limited time", "limited-time", "first 3 months", "welcome bonus", "promotional")
        ):
            continue
        regular_match = regular_pattern.search(text)
        bonus_match = bonus_pattern.search(text)
        if regular_match is None or bonus_match is None:
            continue
        regular = _as_decimal(regular_match.group("regular"))
        bonus = _as_decimal(bonus_match.group("bonus"))
        if regular is None or bonus is None or bonus <= 0:
            continue
        total = regular + bonus
        if total > Decimal("20"):
            continue
        ranked.append((float(link.citation_confidence), link, regular, total))
    if not ranked:
        return
    ranked.sort(key=lambda item: item[0], reverse=True)
    _, source_link, regular_rate, total_rate = ranked[0]
    _replace_rate_value_from_link(
        field_name="standard_rate",
        value=regular_rate,
        source_link=source_link,
        normalization_method="ongoing_additive_bonus_component_alignment",
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
    )
    _replace_rate_value_from_link(
        field_name="public_display_rate",
        value=total_rate,
        source_link=source_link,
        normalization_method="ongoing_additive_bonus_total_alignment",
        candidate_payload=candidate_payload,
        field_mapping_metadata=field_mapping_metadata,
        normalized_values_for_links=normalized_values_for_links,
        evidence_links_for_output=evidence_links_for_output,
    )
    runtime_notes.append(
        f"Aligned the ongoing additive bonus total to `{float(total_rate)}` while preserving regular rate `{float(regular_rate)}`."
    )


def _replace_rate_value_from_link(
    *,
    field_name: str,
    value: Decimal,
    source_link: NormalizationEvidenceLink,
    normalization_method: str,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
) -> None:
    normalized_value = float(value)
    candidate_payload[field_name] = normalized_value
    normalized_values_for_links[field_name] = normalized_value
    field_mapping_metadata[field_name] = {
        "source_field_name": source_link.field_name,
        "normalized_value": normalized_value,
        "normalization_method": normalization_method,
        "evidence_chunk_id": source_link.evidence_chunk_id,
    }
    evidence_links_for_output[:] = [
        link for link in evidence_links_for_output if link.field_name != field_name
    ]
    evidence_links_for_output.append(
        NormalizationEvidenceLink(
            field_name=field_name,
            candidate_value=_stringify(normalized_value),
            evidence_chunk_id=source_link.evidence_chunk_id,
            evidence_text_excerpt=source_link.evidence_text_excerpt,
            source_document_id=source_link.source_document_id,
            source_snapshot_id=source_link.source_snapshot_id,
            citation_confidence=source_link.citation_confidence,
            model_execution_id=source_link.model_execution_id,
            anchor_type=source_link.anchor_type,
            anchor_value=source_link.anchor_value,
            page_no=source_link.page_no,
            chunk_index=source_link.chunk_index,
        )
    )


def _align_public_display_rate(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Keep the public rate at least as high as its grounded regular/promo components."""

    if product_type_family not in {"savings", "gic"}:
        return
    grounded_rates = [
        (field_name, _as_decimal(candidate_payload.get(field_name)))
        for field_name in ("standard_rate", "promotional_rate")
    ]
    if product_type_family == "gic":
        table_rates = [
            _as_decimal(row.get("rate"))
            for row in (candidate_payload.get("term_rate_table") or [])
            if isinstance(row, dict)
        ]
        table_rates = [value for value in table_rates if value is not None]
        if table_rates:
            grounded_rates.append(("term_rate_table", max(table_rates)))
    grounded_rates = [(field_name, value) for field_name, value in grounded_rates if value is not None]
    if not grounded_rates:
        return
    source_field_name, display_floor = max(grounded_rates, key=lambda item: item[1])
    current_display = _as_decimal(candidate_payload.get("public_display_rate"))
    if current_display is not None and current_display >= display_floor:
        return

    normalized_display = float(display_floor)
    candidate_payload["public_display_rate"] = normalized_display
    normalized_values_for_links["public_display_rate"] = normalized_display
    source_mapping = field_mapping_metadata.get(source_field_name)
    field_mapping_metadata["public_display_rate"] = {
        "source_field_name": source_field_name,
        "normalized_value": normalized_display,
        "normalization_method": "canonical_public_display_rate_alignment",
        **(dict(source_mapping) if isinstance(source_mapping, dict) else {}),
    }
    field_mapping_metadata["public_display_rate"]["source_field_name"] = source_field_name
    field_mapping_metadata["public_display_rate"]["normalized_value"] = normalized_display
    field_mapping_metadata["public_display_rate"]["normalization_method"] = (
        "canonical_public_display_rate_alignment"
    )

    source_link = next(
        (link for link in evidence_links_for_output if link.field_name == source_field_name),
        None,
    )
    evidence_links_for_output[:] = [
        link for link in evidence_links_for_output if link.field_name != "public_display_rate"
    ]
    if source_link is not None:
        evidence_links_for_output.append(
            NormalizationEvidenceLink(
                field_name="public_display_rate",
                candidate_value=_stringify(normalized_display),
                evidence_chunk_id=source_link.evidence_chunk_id,
                evidence_text_excerpt=source_link.evidence_text_excerpt,
                source_document_id=source_link.source_document_id,
                source_snapshot_id=source_link.source_snapshot_id,
                citation_confidence=source_link.citation_confidence,
                model_execution_id=source_link.model_execution_id,
                anchor_type=source_link.anchor_type,
                anchor_value=source_link.anchor_value,
                page_no=source_link.page_no,
                chunk_index=source_link.chunk_index,
            )
        )
    runtime_notes.append(
        f"Aligned `public_display_rate` to grounded `{source_field_name}` value `{normalized_display}`."
    )


def _align_gic_representative_rates_from_term_table(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Use the disclosed 12-month row as the comparable standard for a multi-term GIC."""

    if product_type_family != "gic":
        return
    rows = [row for row in (candidate_payload.get("term_rate_table") or []) if isinstance(row, dict)]
    valid_rows = [row for row in rows if _as_decimal(row.get("rate")) is not None]
    if len(valid_rows) < 2:
        return
    one_year_row = next(
        (
            row
            for row in valid_rows
            if row.get("term_length_days") in {360, 365}
            or re.fullmatch(r"(?:12\s*months?|1(?:\.0)?\s*years?)", str(row.get("term_label") or "").strip(), flags=re.IGNORECASE)
        ),
        None,
    )
    if one_year_row is None:
        return
    one_year_rate = _as_decimal(one_year_row.get("rate"))
    if one_year_rate is None:
        return
    table_link = next(
        (link for link in evidence_links_for_output if link.field_name == "term_rate_table"),
        None,
    )
    changed_fields: list[str] = []
    for field_name in ("standard_rate", "base_12_month_rate"):
        if _as_decimal(candidate_payload.get(field_name)) == one_year_rate:
            continue
        if table_link is not None:
            _replace_rate_value_from_link(
                field_name=field_name,
                value=one_year_rate,
                source_link=table_link,
                normalization_method="gic_12_month_representative_rate_alignment",
                candidate_payload=candidate_payload,
                field_mapping_metadata=field_mapping_metadata,
                normalized_values_for_links=normalized_values_for_links,
                evidence_links_for_output=evidence_links_for_output,
            )
        else:
            normalized_value = float(one_year_rate)
            candidate_payload[field_name] = normalized_value
            normalized_values_for_links[field_name] = normalized_value
            field_mapping_metadata[field_name] = {
                "source_field_name": "term_rate_table",
                "normalized_value": normalized_value,
                "normalization_method": "gic_12_month_representative_rate_alignment",
            }
        changed_fields.append(field_name)
    if changed_fields:
        runtime_notes.append(
            "Aligned multi-term GIC representative rate fields to the disclosed 12-month term: "
            + ", ".join(f"`{field_name}`" for field_name in changed_fields)
            + "."
        )


def _complete_gic_term_rate_table_from_split_evidence(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Join table rows split across PDF pages when each row is directly labelled."""

    if product_type_family != "gic":
        return
    existing_table = candidate_payload.get("term_rate_table")
    rows = [dict(row) for row in existing_table if isinstance(row, dict)] if isinstance(existing_table, list) else []
    recovering_missing_table = len(rows) < 2
    target_identity = _normalized_product_identity_phrase(candidate_payload.get("product_name"))
    existing_keys = {
        (_as_int(row.get("term_length_days")), _as_decimal(row.get("rate")))
        for row in rows
    }
    added_links: list[NormalizationEvidenceLink] = []
    for link in evidence_links_for_output:
        excerpt = _normalize_text(link.evidence_text_excerpt)
        if recovering_missing_table and (
            not target_identity
            or target_identity not in _normalized_product_identity_phrase(excerpt)
        ):
            continue
        link_added = False
        for match in re.finditer(
            r"(?<![\d.])(?P<term>\d{1,3}(?:\.\d{1,2})?\s*(?:days?|months?|years?))"
            r"\s*(?:[†‡*^◊ⓘ]|\[[^\]]{0,30}\])*\s*"
            r"(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
            excerpt,
            flags=re.IGNORECASE,
        ):
            term_label = _normalize_text(match.group("term")).lower()
            term_length_days = _term_label_to_days(term_label)
            rate = _as_decimal(match.group("rate"))
            key = (term_length_days, rate)
            if term_length_days is None or rate is None or key in existing_keys:
                continue
            rows.append(
                {
                    "term_label": term_label,
                    "term_length_days": term_length_days,
                    "rate": float(rate),
                    "minimum_deposit": None,
                    "notes": None,
                }
            )
            existing_keys.add(key)
            link_added = True
        if link_added:
            added_links.append(link)

    if not added_links or (recovering_missing_table and len(rows) < 2):
        return
    rows.sort(key=lambda row: (_as_int(row.get("term_length_days")) or 10**9, str(row.get("term_label") or "")))
    candidate_payload["term_rate_table"] = rows
    normalized_values_for_links["term_rate_table"] = rows
    metadata = dict(field_mapping_metadata.get("term_rate_table") or {})
    metadata["normalized_value"] = rows
    metadata["normalization_method"] = "split_evidence_term_table_completion"
    field_mapping_metadata["term_rate_table"] = metadata
    known_chunks = {
        link.evidence_chunk_id
        for link in evidence_links_for_output
        if link.field_name == "term_rate_table"
    }
    for link in added_links:
        if link.evidence_chunk_id in known_chunks:
            continue
        known_chunks.add(link.evidence_chunk_id)
        evidence_links_for_output.append(
            NormalizationEvidenceLink(
                field_name="term_rate_table",
                candidate_value=_stringify(rows),
                evidence_chunk_id=link.evidence_chunk_id,
                evidence_text_excerpt=link.evidence_text_excerpt,
                source_document_id=link.source_document_id,
                source_snapshot_id=link.source_snapshot_id,
                citation_confidence=link.citation_confidence,
                model_execution_id=link.model_execution_id,
                anchor_type=link.anchor_type,
                anchor_value=link.anchor_value,
                page_no=link.page_no,
                chunk_index=link.chunk_index,
            )
        )
    runtime_notes.append(
        f"Completed the GIC term table from {len(added_links)} exact-product evidence chunk(s)."
    )


def _normalized_product_identity_phrase(value: object) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return " ".join(normalized.split())


def _align_promotional_period_from_evidence(
    *,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Recover a concise promo duration only when the rate evidence states it directly."""

    promotional_rate = _as_decimal(candidate_payload.get("promotional_rate"))
    if promotional_rate is None:
        return

    rate_pattern = re.escape(f"{promotional_rate.normalize():f}")
    selected: tuple[NormalizationEvidenceLink, str] | None = None
    for link in evidence_links_for_output:
        excerpt = _normalize_text(link.evidence_text_excerpt)
        if not excerpt or re.search(rf"(?<![\d.]){rate_pattern}0*\s*%", excerpt) is None:
            continue
        for match in re.finditer(
            r"\bfor\s+(?:the\s+)?(?:first\s+)?(?P<count>\d{1,3})\s+(?P<unit>days?|weeks?|months?)\b",
            excerpt,
            flags=re.IGNORECASE,
        ):
            local_context = excerpt[max(0, match.start() - 160):match.end() + 40].lower()
            if not any(
                marker in local_context
                for marker in (
                    "promotional rate",
                    "promo rate",
                    "special interest rate",
                    "introductory rate",
                    "welcome offer",
                    "earn ",
                    "interest rate",
                )
            ):
                continue
            count = int(match.group("count"))
            unit = match.group("unit").lower()
            if count == 1:
                unit = unit.rstrip("s")
            elif not unit.endswith("s"):
                unit += "s"
            selected = (link, f"{count} {unit}")
            break
        if selected is not None:
            break

    if selected is None:
        return

    source_link, period_text = selected
    for field_name, normalized_value in (
        ("promotional_period_text", period_text),
        ("introductory_rate_flag", True),
    ):
        candidate_payload[field_name] = normalized_value
        normalized_values_for_links[field_name] = normalized_value
        field_mapping_metadata[field_name] = {
            "source_field_name": source_link.field_name,
            "normalized_value": normalized_value,
            "normalization_method": "grounded_promotional_period_alignment",
            "evidence_chunk_id": source_link.evidence_chunk_id,
        }
        evidence_links_for_output[:] = [
            link for link in evidence_links_for_output if link.field_name != field_name
        ]
        evidence_links_for_output.append(
            NormalizationEvidenceLink(
                field_name=field_name,
                candidate_value=_stringify(normalized_value),
                evidence_chunk_id=source_link.evidence_chunk_id,
                evidence_text_excerpt=source_link.evidence_text_excerpt,
                source_document_id=source_link.source_document_id,
                source_snapshot_id=source_link.source_snapshot_id,
                citation_confidence=source_link.citation_confidence,
                model_execution_id=source_link.model_execution_id,
                anchor_type=source_link.anchor_type,
                anchor_value=source_link.anchor_value,
                page_no=source_link.page_no,
                chunk_index=source_link.chunk_index,
            )
        )
    runtime_notes.append(
        f"Recovered grounded promotional period `{period_text}` from the promotional-rate evidence."
    )


def _clean_chequing_fee_waiver_consistency(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Remove an adjacent plan's waiver when its base fee conflicts with the target."""

    if product_type_family != "chequing":
        return
    condition = _normalize_text(candidate_payload.get("fee_waiver_condition"))
    monthly_fee = _as_decimal(candidate_payload.get("monthly_fee"))
    if not condition or monthly_fee is None:
        return
    match = re.search(
        r"\bmonthly\s+fee\s+(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s+is\s+waived\s+to\s+0(?:\.00)?"
        r"\s+with\s+a\s+(?P<balance>\d[\d,]*(?:\.\d{1,2})?)\s+minimum\s+balance\b",
        condition,
        flags=re.IGNORECASE,
    )
    if match is None:
        return
    waiver_fee = _as_decimal(match.group("fee"))
    waiver_balance = _as_decimal(match.group("balance"))
    if waiver_fee is None or waiver_fee == monthly_fee:
        return

    if monthly_fee == 0 and waiver_fee > 0:
        aligned_fee = float(waiver_fee)
        waiver_link = next(
            (link for link in evidence_links_for_output if link.field_name == "fee_waiver_condition"),
            None,
        )
        for field_name in ("monthly_fee", "public_display_fee"):
            candidate_payload[field_name] = aligned_fee
            normalized_values_for_links[field_name] = aligned_fee
            metadata = dict(field_mapping_metadata.get(field_name) or {})
            metadata.update(
                {
                    "normalized_value": aligned_fee,
                    "normalization_method": "conditional_zero_base_fee_alignment",
                }
            )
            field_mapping_metadata[field_name] = metadata
            evidence_links_for_output[:] = [
                link for link in evidence_links_for_output if link.field_name != field_name
            ]
            if waiver_link is not None:
                evidence_links_for_output.append(
                    NormalizationEvidenceLink(
                        field_name=field_name,
                        candidate_value=str(aligned_fee),
                        evidence_chunk_id=waiver_link.evidence_chunk_id,
                        evidence_text_excerpt=waiver_link.evidence_text_excerpt,
                        source_document_id=waiver_link.source_document_id,
                        source_snapshot_id=waiver_link.source_snapshot_id,
                        citation_confidence=waiver_link.citation_confidence,
                        model_execution_id=waiver_link.model_execution_id,
                        anchor_type=waiver_link.anchor_type,
                        anchor_value=waiver_link.anchor_value,
                        page_no=waiver_link.page_no,
                        chunk_index=waiver_link.chunk_index,
                    )
                )
        runtime_notes.append(
            "Replaced a conditional zero outcome with the fee-waiver disclosure's positive recurring base fee."
        )
        return

    removed = ["fee_waiver_condition"]
    candidate_payload.pop("fee_waiver_condition", None)
    normalized_values_for_links.pop("fee_waiver_condition", None)
    field_mapping_metadata.pop("fee_waiver_condition", None)
    current_balance = _as_decimal(candidate_payload.get("minimum_balance"))
    if waiver_balance is not None and current_balance == waiver_balance:
        candidate_payload.pop("minimum_balance", None)
        normalized_values_for_links.pop("minimum_balance", None)
        field_mapping_metadata.pop("minimum_balance", None)
        removed.append("minimum_balance")
    evidence_links_for_output[:] = [
        link for link in evidence_links_for_output if link.field_name not in set(removed)
    ]
    runtime_notes.append(
        "Suppressed fee-waiver fields whose stated base fee conflicts with the target monthly fee: "
        + ", ".join(removed)
        + "."
    )


def _align_minimum_balance_to_fee_waiver(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Keep the minimum-balance scalar equal to its grounded fee-waiver threshold."""

    if product_type_family != "chequing":
        return
    condition = _normalize_text(candidate_payload.get("fee_waiver_condition"))
    match = re.search(
        r"\bwith\s+a\s+(?P<balance>\d[\d,]*(?:\.\d{1,2})?)\s+minimum\s+balance\b",
        condition,
        flags=re.IGNORECASE,
    )
    if match is None:
        return
    waiver_balance = _as_decimal(match.group("balance"))
    current_balance = _as_decimal(candidate_payload.get("minimum_balance"))
    if waiver_balance is None or waiver_balance <= 0 or current_balance == waiver_balance:
        return
    aligned_value = float(waiver_balance)
    candidate_payload["minimum_balance"] = aligned_value
    normalized_values_for_links["minimum_balance"] = aligned_value
    metadata = dict(field_mapping_metadata.get("minimum_balance") or {})
    metadata.update(
        {
            "normalized_value": aligned_value,
            "normalization_method": "fee_waiver_balance_alignment",
        }
    )
    field_mapping_metadata["minimum_balance"] = metadata
    waiver_link = next(
        (link for link in evidence_links_for_output if link.field_name == "fee_waiver_condition"),
        None,
    )
    evidence_links_for_output[:] = [
        link for link in evidence_links_for_output if link.field_name != "minimum_balance"
    ]
    if waiver_link is not None:
        evidence_links_for_output.append(
            NormalizationEvidenceLink(
                field_name="minimum_balance",
                candidate_value=str(aligned_value),
                evidence_chunk_id=waiver_link.evidence_chunk_id,
                evidence_text_excerpt=waiver_link.evidence_text_excerpt,
                source_document_id=waiver_link.source_document_id,
                source_snapshot_id=waiver_link.source_snapshot_id,
                citation_confidence=waiver_link.citation_confidence,
                model_execution_id=waiver_link.model_execution_id,
                anchor_type=waiver_link.anchor_type,
                anchor_value=waiver_link.anchor_value,
                page_no=waiver_link.page_no,
                chunk_index=waiver_link.chunk_index,
            )
        )
    runtime_notes.append(
        "Aligned `minimum_balance` to the explicit positive fee-waiver threshold."
    )


def _align_public_display_fee(
    *,
    product_type_family: str | None,
    candidate_payload: dict[str, object],
    field_mapping_metadata: dict[str, object],
    normalized_values_for_links: dict[str, object],
    evidence_links_for_output: list[NormalizationEvidenceLink],
    runtime_notes: list[str],
) -> None:
    """Use a directly grounded recurring fee as the public fee scalar."""

    if product_type_family != "chequing":
        return
    monthly_fee = _as_decimal(candidate_payload.get("monthly_fee"))
    public_fee = _as_decimal(candidate_payload.get("public_display_fee"))
    if monthly_fee is None or monthly_fee >= _MAX_MONTHLY_ACCOUNT_FEE or monthly_fee == public_fee:
        return
    source_link = next(
        (link for link in evidence_links_for_output if link.field_name == "monthly_fee"),
        None,
    )
    if source_link is None or not _is_direct_recurring_monthly_fee(
        value=monthly_fee,
        context=source_link.evidence_text_excerpt,
    ):
        return

    normalized_fee = float(monthly_fee)
    candidate_payload["public_display_fee"] = normalized_fee
    normalized_values_for_links["public_display_fee"] = normalized_fee
    field_mapping_metadata["public_display_fee"] = {
        "source_field_name": "monthly_fee",
        "normalized_value": normalized_fee,
        "normalization_method": "canonical_public_display_fee_alignment",
        "evidence_chunk_id": source_link.evidence_chunk_id,
        **mapping_contract_metadata("public_display_fee"),
    }
    evidence_links_for_output[:] = [
        link for link in evidence_links_for_output if link.field_name != "public_display_fee"
    ]
    evidence_links_for_output.append(
        NormalizationEvidenceLink(
            field_name="public_display_fee",
            candidate_value=_stringify(normalized_fee),
            evidence_chunk_id=source_link.evidence_chunk_id,
            evidence_text_excerpt=source_link.evidence_text_excerpt,
            source_document_id=source_link.source_document_id,
            source_snapshot_id=source_link.source_snapshot_id,
            citation_confidence=source_link.citation_confidence,
            model_execution_id=source_link.model_execution_id,
            anchor_type=source_link.anchor_type,
            anchor_value=source_link.anchor_value,
            page_no=source_link.page_no,
            chunk_index=source_link.chunk_index,
        )
    )
    runtime_notes.append(
        f"Aligned `public_display_fee` to directly grounded `monthly_fee` value `{normalized_fee}`."
    )


def _is_direct_recurring_monthly_fee(*, value: Decimal, context: str) -> bool:
    normalized = _normalize_text(context).lower()
    if not normalized:
        return False
    if value == 0:
        if re.search(
            r"\b(?:if|when|with|maintain|balance|waiv(?:e|ed|er)|rebate)\b",
            normalized,
        ):
            return False
        return bool(
            re.search(r"\bno\s+monthly(?:\s+(?:plan|account))?\s+fees?\b", normalized)
            or re.search(r"\bmonthly(?:\s+(?:plan|account))?\s+fees?\b\D{0,30}\$\s*0(?:\.00)?\b", normalized)
        )
    token = re.escape(f"{value:f}".rstrip("0").rstrip("."))
    return bool(
        re.search(
            rf"\bmonthly(?:\s+(?:plan|account))?\s+fees?\b[\s\S]{{0,80}}?\$\s*{token}(?![\d.])",
            normalized,
        )
        or re.search(
            rf"\$\s*{token}(?![\d.])\s*(?:per\s+month|/\s*month|monthly)\b",
            normalized,
        )
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
        "purchase_interest_rate": r"(?:current\s+interest\s+rate\s*\(\s*purchases?\s*\)|purchases?\s+(?:interest\s+)?rate|purchase\s+apr|apr\s+for\s+purchases?|annual\s+percentage\s+rate(?:\s*\(apr\))?(?:\s+for\s+purchases?)?)",
        "balance_transfer_rate": r"(?:interest\s+rate\s*\(\s*balance\s+transfers?|balance\s+transfers?\s+(?:interest\s+)?rate|balance\s+transfer\s+apr|apr\s+for\s+balance\s+transfers?|balance\s+transfers?\s+and\s+cash\s+advances?)",
        "cash_advance_rate": r"(?:cash\s+(?:advance\s+)?interest\s+rate|cash\s+advances?\s+(?:interest\s+)?rate|cash\s+advance\s+apr|apr\s+for\s+cash\s+advances?|balance\s+transfers?\s+and\s+cash\s+advances?)",
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
        window = bounded_rate_evidence_context(
            text,
            value_start=match.start(),
            value_end=match.end(),
        ).lower()
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
    if field_name in {"interest_rate", "mortgage_rate"} and _is_reference_rate_margin_only(
        field.evidence_text_excerpt
    ):
        return "reference_rate_margin_not_total_rate"
    if field_name == "term_rate_table" and expired_promotional_offer_end_date(field.evidence_text_excerpt) is not None:
        return "expired_promotional_offer"
    if (
        field_name == "term_rate_table"
        and product_type_family == "savings"
        and _has_rate_promotional_context(field.evidence_text_excerpt)
        and "premium period interest rate" not in str(field.evidence_text_excerpt or "").lower()
    ):
        return "savings_promotional_period_not_term_rate"
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


def _is_reference_rate_margin_only(text: str | None) -> bool:
    normalized = " ".join(str(text or "").split())
    has_margin_formula = re.search(
        r"\b(?:bank\s+)?prime(?:\s+rate)?\b\s*(?:\+|plus|-|minus)\s*\d{1,2}(?:\.\d{1,4})?\s*%",
        normalized,
        flags=re.IGNORECASE,
    ) is not None
    if not has_margin_formula:
        return False
    return re.search(
        r"\b(?:current|total|effective|annual)\s+(?:annual\s+)?(?:interest\s+)?rate\b\s*(?:is|of|:)?\s*"
        r"\d{1,2}(?:\.\d{1,4})?\s*%",
        normalized,
        flags=re.IGNORECASE,
    ) is None


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
    if any(
        token in lowered
        for token in (
            "bonus interest",
            "promo interest",
            "promo rate",
            "for 3 months",
            "for three months",
            "for the first",
            "limited-time",
            "limited time",
            "offer expires",
            "promotional",
            "special offer",
            "new client offer",
        )
    ):
        return True
    return bool(
        re.search(r"\b(?:for|during)\s+(?:the\s+)?(?:first\s+)?\d{1,3}[- ]?(?:days?|months?)\b", lowered)
        and any(marker in lowered for marker in ("rate", "interest", "offer", "boost", "earn"))
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
    discovery_metadata = source_metadata.get("discovery_metadata")
    if not isinstance(discovery_metadata, dict):
        return product_name

    normalized_product_name = re.sub(r"[^a-z0-9]+", "", str(product_name or "").lower())
    if normalized_product_name:
        for metadata_key in ("primary_heading", "page_title"):
            candidate = _clean_product_name_candidate(str(discovery_metadata.get(metadata_key) or ""))
            normalized_candidate = re.sub(r"[^a-z0-9]+", "", str(candidate or "").lower())
            if candidate and normalized_candidate == normalized_product_name and candidate != product_name:
                runtime_notes.append(
                    f"Restored official product_name formatting `{candidate}` from source discovery metadata `{metadata_key}`."
                )
                return candidate

    if not _looks_like_generic_product_name(product_name):
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
    if normalized in {
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
        "current gic interest rates",
        "current guaranteed investment interest rates",
    }:
        return True
    return any(
        re.search(pattern, normalized)
        for pattern in (
            r"^(?:the\s+)?(?:gic|term deposit)\s+(?:tab\s*le|calculator|selector|search(?: tool)?)$",
            r"^(?:rate|rates|term|terms)\s+(?:table|calculator|selector)$",
            r"^benefits of banking with\b",
            r"\bincluded with every\b",
            r"\breach your .+ faster\b",
            r"\bsave for (?:today|tomorrow)\b",
            r"\b(?:open|compare|choose|find|explore|discover) (?:an? |the |our )?.*(?:account|options|products?)\b",
        )
    )


def _clean_product_name_candidate(value: str) -> str | None:
    cleaned = value.split("|", 1)[0]
    cleaned = re.sub(r"\s+opens in\b.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ?.:-")
    cleaned = re.sub(r"\s*[ⓘℹ]\s*$", "", cleaned).strip(" ?.:-")
    if not cleaned:
        return None
    words = cleaned.split()
    half = len(words) // 2
    if len(words) >= 4 and len(words) % 2 == 0 and words[:half] == words[half:]:
        cleaned = " ".join(words[:half])
    return cleaned


def _clean_deposit_insurance_value(value: str) -> str:
    normalized = _normalize_text(value)
    division_member = re.search(
        r"(?P<sentence>[A-Z][A-Za-z0-9&.' -]{1,80}\s+is\s+a\s+division\s+of\s+"
        r"[A-Z][A-Za-z0-9&.' -]{1,60},\s+a\s+CDIC\s+member)\b",
        normalized,
    )
    if division_member is not None:
        sentence = _normalize_text(division_member.group("sentence"))
        sentence = re.sub(
            r"^(?:(?:GIC|term deposit|savings account|chequing account|checking account|credit card)\s+)+",
            "",
            sentence,
            flags=re.IGNORECASE,
        )
        return sentence.rstrip(".") + "."
    eligible = re.search(
        r"\beligible\s+(?:deposits?\s+are\s+)?(?:for\s+)?CDIC\s+(?:deposit\s+)?insurance\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if eligible is not None:
        return "Eligible for CDIC Insurance."
    membership = re.search(
        r"(?P<sentence>[A-Z][A-Za-z0-9&.'’\-]*(?:\s+[A-Z][A-Za-z0-9&.'’\-]*){0,7}\s+"
        r"(?:is|are)\s+(?:a\s+)?members?\s+of\s+(?:the\s+)?Canada\s+Deposit\s+Insurance\s+Corporation"
        r"(?:\s*\(CDIC\))?\.?)",
        normalized,
    )
    if membership is not None:
        sentence = _normalize_text(membership.group("sentence"))
        sentence = re.sub(
            r"^(?:(?:legal|book an appointment|schedule an appointment|contact us|open account)\s+)+",
            "",
            sentence,
            flags=re.IGNORECASE,
        )
        return sentence[:280]
    return normalized


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


def _suppress_unverified_dynamic_fields(
    *,
    candidate_payload: dict[str, object],
    normalized_values_for_links: dict[str, object],
    field_mapping_metadata: dict[str, object],
    runtime_notes: list[str],
) -> None:
    """Omit ungrounded dynamic attributes instead of publishing noisy guesses."""

    suppressed_fields: list[str] = []
    for field_name in list(candidate_payload):
        if field_name in _DYNAMIC_OPERATIONAL_FIELDS:
            continue
        metadata = field_mapping_metadata.get(field_name)
        mapping = metadata if isinstance(metadata, dict) else {}
        sources = mapping.get("official_web_sources")
        officially_grounded = (
            mapping.get("official_grounding_contract_version") == "collection-official-grounding-v2"
            and str(mapping.get("official_verification_status") or "") in {"match", "mismatch"}
            and bool(str(mapping.get("official_evidence_quote") or "").strip())
            and isinstance(sources, list)
            and any(isinstance(source, dict) and str(source.get("url") or "").strip() for source in sources)
        )
        if officially_grounded:
            continue
        candidate_payload.pop(field_name, None)
        normalized_values_for_links.pop(field_name, None)
        mapping.update(
            {
                "normalized_value": None,
                "normalization_method": "dynamic_official_grounding_filter",
                "suppressed_reason": "official_grounding_missing",
            }
        )
        field_mapping_metadata[field_name] = mapping
        suppressed_fields.append(field_name)
    if suppressed_fields:
        runtime_notes.append(
            "Omitted unverified dynamic-product fields pending official grounding: "
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
    evidence_excerpt_by_field: dict[str, str] | None = None,
    enforce_percentage_evidence_grounding: bool = True,
    expired_offer_present: bool = False,
    dynamic_field_names: set[str] | None = None,
) -> None:
    deposit_insurance = str(candidate_payload.get("deposit_insurance") or "").strip()
    if deposit_insurance:
        cleaned_insurance = _clean_deposit_insurance_value(deposit_insurance)
        if cleaned_insurance != deposit_insurance:
            candidate_payload["deposit_insurance"] = cleaned_insurance
            if normalized_values_for_links is not None:
                normalized_values_for_links["deposit_insurance"] = cleaned_insurance
            if field_mapping_metadata is not None:
                metadata = dict(field_mapping_metadata.get("deposit_insurance") or {})
                metadata["normalized_value"] = cleaned_insurance
                metadata["normalization_method"] = "bounded_deposit_insurance_sentence"
                field_mapping_metadata["deposit_insurance"] = metadata
            if runtime_notes is not None:
                runtime_notes.append("Reduced deposit-insurance copy to its exact membership statement.")

    description = str(candidate_payload.get("description_short") or "").strip()
    if description:
        cleaned_description = _strip_cross_product_description_sentences(
            _repair_flattened_customer_text(description)
        )
        if cleaned_description != description:
            if cleaned_description:
                candidate_payload["description_short"] = cleaned_description
                if normalized_values_for_links is not None:
                    normalized_values_for_links["description_short"] = cleaned_description
                if field_mapping_metadata is not None:
                    metadata = dict(field_mapping_metadata.get("description_short") or {})
                    metadata["normalized_value"] = cleaned_description
                    metadata["normalization_method"] = "cross_product_description_cleanup"
                    field_mapping_metadata["description_short"] = metadata
            else:
                candidate_payload.pop("description_short", None)
                if normalized_values_for_links is not None:
                    normalized_values_for_links.pop("description_short", None)
                if field_mapping_metadata is not None:
                    field_mapping_metadata.pop("description_short", None)
            if runtime_notes is not None:
                runtime_notes.append("Removed a cross-product sales sentence from the product description.")

    suppressed_fields: list[str] = []
    for field_name, value in list(candidate_payload.items()):
        if field_name in _CORE_FIELDS:
            continue
        evidence_context = (evidence_context_by_field or {}).get(field_name, "")
        should_suppress = _looks_like_non_rate_numeric_context(
            field_name=field_name,
            value=value,
            context=evidence_context,
            product_type_family=product_type_family,
        ) or _dynamic_numeric_value_is_ungrounded(
            field_name=field_name,
            value=value,
            context=evidence_context,
            dynamic_field_names=dynamic_field_names or set(),
        ) or _audience_flag_is_legal_enumeration(
            field_name=field_name,
            value=value,
            context=evidence_context,
        ) or _money_value_is_non_fee_context(
            field_name=field_name,
            value=value,
            context=evidence_context,
        ) or _field_is_comparison_calculator_copy(
            field_name=field_name,
            value=value,
            context=evidence_context,
        ) or _fee_value_is_plan_dependent(
            field_name=field_name,
            value=value,
            context=evidence_context,
        ) or _standard_rate_evidence_is_promotional(
            field_name=field_name,
            value=value,
            context=evidence_context,
        ) or (enforce_percentage_evidence_grounding and _percentage_value_absent_from_evidence(
            field_name=field_name,
            value=value,
            context=(evidence_excerpt_by_field or {}).get(field_name, ""),
        )) or _looks_like_other_product_section(context=evidence_context) or _looks_like_credit_card_field_mismatch(
            field_name=field_name,
            value=value,
            context=evidence_context,
            product_type_family=product_type_family,
            official_grounding_metadata=dict(
                (field_mapping_metadata or {}).get(field_name) or {}
            ),
        ) or _looks_like_unsupported_security_value(
            field_name=field_name,
            context=evidence_context,
        ) or _looks_like_offer_end_mapped_as_effective_date(
            field_name=field_name,
            context=evidence_context,
        ) or (
            product_type_family == "gic"
            and field_name
            in {
                "included_transactions",
                "unlimited_transactions_flag",
                "overdraft_available_flag",
                "withdrawal_limit_text",
            }
        )
        if isinstance(value, str):
            should_suppress = should_suppress or (
                _looks_like_navigation_contamination(value)
                or _looks_like_non_value_description(
                    field_name=field_name,
                    value=value,
                    product_type_family=product_type_family,
                    product_name=str(candidate_payload.get("product_name") or ""),
                )
                or _looks_like_non_value_rate(field_name=field_name, value=value)
                or _looks_like_non_value_eligibility(
                    field_name=field_name,
                    value=value,
                    product_name=str(candidate_payload.get("product_name") or ""),
                )
                or _looks_like_non_value_rewards(field_name=field_name, value=value)
                or _looks_like_expired_promotional_customer_field(
                    field_name=field_name,
                    value=value,
                    context=evidence_context,
                    expired_offer_present=expired_offer_present,
                )
                or _looks_like_invalid_field_type(field_name=field_name, value=value)
                or _looks_like_invalid_tax_benefit(field_name=field_name, value=value)
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
                    context=evidence_context,
                )
                or _looks_like_non_value_lending_field(
                    field_name=field_name,
                    value=value,
                    product_type_family=product_type_family,
                )
                or _looks_like_broad_page_copy(field_name=field_name, value=value)
                or _looks_like_gic_field_context_mismatch(
                    field_name=field_name,
                    value=value,
                    product_name=str(candidate_payload.get("product_name") or ""),
                    product_type_family=product_type_family,
                )
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
            "Suppressed ungrounded, wrong-type, cross-product, or navigation/marketing product fields: "
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
    _suppress_scalar_term_for_multi_term_table(
        candidate_payload=candidate_payload,
        normalized_values_for_links=normalized_values_for_links,
        field_mapping_metadata=field_mapping_metadata,
        runtime_notes=runtime_notes,
    )

    withdrawal_text = str(candidate_payload.get("withdrawal_limit_text") or "").strip()
    legal_prefix_cleaned = re.sub(
        r"^legal\s+\d+\s+symbol\s*\(optional\)\s+legal\s+text\s+",
        "",
        _normalize_text(withdrawal_text),
        flags=re.IGNORECASE,
    ).strip()
    if legal_prefix_cleaned and legal_prefix_cleaned != withdrawal_text:
        withdrawal_text = legal_prefix_cleaned
        candidate_payload["withdrawal_limit_text"] = legal_prefix_cleaned
        if normalized_values_for_links is not None:
            normalized_values_for_links["withdrawal_limit_text"] = legal_prefix_cleaned
        if field_mapping_metadata is not None and "withdrawal_limit_text" in field_mapping_metadata:
            metadata = dict(field_mapping_metadata["withdrawal_limit_text"] or {})
            metadata["normalized_value"] = legal_prefix_cleaned
            metadata["normalization_method"] = "legal_prefix_cleanup"
            field_mapping_metadata["withdrawal_limit_text"] = metadata
    included_and_additional_match = re.search(
        r"transactions?\s+included\s+per\s+month(?:\s+\d{1,2})?\s+(?P<count>\d{1,3})\s+"
        r"additional\s+transactions?(?:\s+\d{1,2})?\s+\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s+each",
        withdrawal_text,
        flags=re.IGNORECASE,
    )
    if included_and_additional_match is not None:
        count = int(included_and_additional_match.group("count"))
        noun = "transaction" if count == 1 else "transactions"
        fee = included_and_additional_match.group("fee").replace(",", "")
        cleaned_withdrawal = f"{count} {noun} per month included; additional transactions cost ${fee} each."
        candidate_payload["withdrawal_limit_text"] = cleaned_withdrawal
        if normalized_values_for_links is not None:
            normalized_values_for_links["withdrawal_limit_text"] = cleaned_withdrawal
        if field_mapping_metadata is not None and "withdrawal_limit_text" in field_mapping_metadata:
            metadata = dict(field_mapping_metadata["withdrawal_limit_text"] or {})
            metadata["normalized_value"] = cleaned_withdrawal
            metadata["normalization_method"] = "included_and_additional_transaction_cleanup"
            field_mapping_metadata["withdrawal_limit_text"] = metadata
        if runtime_notes is not None:
            runtime_notes.append("Reduced a broad account-fee table to its included and additional transaction rule.")
        withdrawal_text = cleaned_withdrawal
    withdrawal_match = re.search(
        r"\b(?:(?:one|1)\s+free\s+withdrawal(?:s)?\s+(?:a|per)\s+month|"
        r"(?:one|1)\s+(?:eligible\s+)?(?:debit\s+)?transaction\s+per\s+month\s+at\s+no\s+cost)\b",
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
    else:
        service_charge_match = re.search(
            r"\$\s*\d[\d,]*(?:\.\d{1,2})?\s+service\s+charge\s+per\s+debit\s+transaction",
            withdrawal_text,
            flags=re.IGNORECASE,
        )
        if service_charge_match is not None and len(withdrawal_text) > len(service_charge_match.group(0)) + 40:
            cleaned_withdrawal = _clean_text_value(service_charge_match.group(0)).capitalize() + "."
            candidate_payload["withdrawal_limit_text"] = cleaned_withdrawal
            if normalized_values_for_links is not None:
                normalized_values_for_links["withdrawal_limit_text"] = cleaned_withdrawal
            if field_mapping_metadata is not None and "withdrawal_limit_text" in field_mapping_metadata:
                metadata = dict(field_mapping_metadata["withdrawal_limit_text"] or {})
                metadata["normalized_value"] = cleaned_withdrawal
                metadata["normalization_method"] = "semantic_withdrawal_fee_cleanup"
                field_mapping_metadata["withdrawal_limit_text"] = metadata
            if runtime_notes is not None:
                runtime_notes.append("Reduced broad savings copy to the explicit per-debit service charge.")

    application_method = str(candidate_payload.get("application_method") or "").strip()
    application_match = re.search(
        r"\bapply\s+by\s+signing\s+on\s+to\s+online\s+banking\s+or\s+calling\s+(?:us\s+at\s+)?"
        r"(?P<phone>1[-\s]\d{3}[-\s]\d{3}[-\s]\d{4})",
        application_method,
        flags=re.IGNORECASE,
    )
    if application_match is not None and len(application_method) > len(application_match.group(0)) + 20:
        cleaned_application = _clean_text_value(application_match.group(0)).capitalize() + "."
        candidate_payload["application_method"] = cleaned_application
        if normalized_values_for_links is not None:
            normalized_values_for_links["application_method"] = cleaned_application
        if field_mapping_metadata is not None and "application_method" in field_mapping_metadata:
            metadata = dict(field_mapping_metadata["application_method"] or {})
            metadata["normalized_value"] = cleaned_application
            metadata["normalization_method"] = "semantic_application_method_cleanup"
            field_mapping_metadata["application_method"] = metadata
        if runtime_notes is not None:
            runtime_notes.append("Reduced repeated application CTA copy to the explicit channel and phone number.")
    else:
        channels: list[str] = []
        lowered_application = _normalize_text(application_method).lower()
        if re.search(
            r"\b(?:open|apply(?:\s+for)?|get)\s+(?:an?\s+)?(?:\w+\s+){0,3}?account\s+online\b|"
            r"\b(?:open|apply|get account)\s+online\b|\bonline\s+(?:application|account opening)\b|"
            r"\bopen\s+an?\s+account\b.{0,30}\bonline\b",
            lowered_application,
        ):
            channels.append("online")
        if any(
            marker in lowered_application
            for marker in (
                "book an appointment",
                "in person",
                "at the branch",
                "at a branch",
                "banking centre",
                "banking center",
            )
        ):
            channels.append("at a branch")
        if any(marker in lowered_application for marker in ("call us", "by phone", "phone us")):
            channels.append("by phone")
        channels = list(dict.fromkeys(channels))
        channel_only_cta = any(
            marker in lowered_application
            for marker in (
                "as little as",
                "nearest branch",
                "you can also apply",
                "open an account online",
                "apply for an account online",
            )
        )
        if channels and (len(application_method) >= 80 or len(channels) >= 2 or channel_only_cta):
            if len(channels) == 1:
                cleaned_application = channels[0].capitalize() + "."
            elif len(channels) == 2:
                cleaned_application = channels[0].capitalize() + f" or {channels[1]}."
            else:
                cleaned_application = ", ".join(channels[:-1]).capitalize() + f", or {channels[-1]}."
            candidate_payload["application_method"] = cleaned_application
            if normalized_values_for_links is not None:
                normalized_values_for_links["application_method"] = cleaned_application
            if field_mapping_metadata is not None and "application_method" in field_mapping_metadata:
                metadata = dict(field_mapping_metadata["application_method"] or {})
                metadata["normalized_value"] = cleaned_application
                metadata["normalization_method"] = "application_channel_cleanup"
                field_mapping_metadata["application_method"] = metadata
            if runtime_notes is not None:
                runtime_notes.append("Reduced repeated application CTA copy to explicit application channels.")

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

    if product_type_family == "savings":
        calculation_method = str(candidate_payload.get("interest_calculation_method") or "").strip()
        daily_monthly_match = re.search(
            r"interest (?:is )?calculated daily and paid monthly",
            calculation_method,
            flags=re.IGNORECASE,
        )
        if daily_monthly_match is not None:
            cleaned_method = "Interest is calculated daily and paid monthly."
            if calculation_method != cleaned_method:
                candidate_payload["interest_calculation_method"] = cleaned_method
                if normalized_values_for_links is not None:
                    normalized_values_for_links["interest_calculation_method"] = cleaned_method
                if field_mapping_metadata is not None:
                    metadata = dict(field_mapping_metadata.get("interest_calculation_method") or {})
                    metadata["normalized_value"] = cleaned_method
                    metadata["normalization_method"] = "daily_monthly_interest_method_cleanup"
                    field_mapping_metadata["interest_calculation_method"] = metadata
                if runtime_notes is not None:
                    runtime_notes.append("Reduced promotional or calculator prose to the exact daily/monthly interest method.")


def _percentage_value_absent_from_evidence(*, field_name: str, value: object, context: str) -> bool:
    contract = field_contract(field_name)
    if contract is None or contract.value_type != "decimal" or contract.unit != "percentage_points":
        return False
    if isinstance(value, bool):
        return True
    try:
        expected = Decimal(str(value).replace(",", "").strip())
    except InvalidOperation:
        return False
    normalized_context = _normalize_text(context)
    if not normalized_context:
        return False
    if expected == 0 and re.search(
        r"\b(?:no interest|non-interest[- ]bearing|does not pay interest|no interest (?:is )?payable)\b",
        normalized_context,
        flags=re.IGNORECASE,
    ):
        return False
    for match in re.finditer(r"(?<![\d.])(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%", normalized_context):
        try:
            if Decimal(match.group(1).replace(",", "")) == expected:
                return False
        except InvalidOperation:
            continue
    return True


def _standard_rate_evidence_is_promotional(*, field_name: str, value: object, context: str) -> bool:
    if field_name not in {"standard_rate", "base_12_month_rate"}:
        return False
    lowered = _normalize_text(context).lower()
    if not lowered:
        return False
    numeric_value = _as_decimal(value)
    if numeric_value is not None:
        value_pattern = re.escape(f"{numeric_value.normalize():f}")
        if re.search(
            rf"(?<![\d.]){value_pattern}0*\s*%\s*(?:[†‡*^◊ⓘ]|\[[^\]]{{0,30}}\])*\s*"
            r"(?:interest rate|annual percentage yield|apy)[\s\S]{0,100}?"
            r"(?:monthly fee|minimum balance|no fees?|no minimum deposit)",
            lowered,
            flags=re.IGNORECASE,
        ):
            # A compact product header can contain the ongoing rate and then a
            # separate limited-time offer. The labelled header value remains
            # the standard rate even though the evidence chunk contains both.
            return False
    if any(
        marker in lowered
        for marker in (
            "promotional rate",
            "promotional interest",
            "new client offer",
            "welcome offer",
            "special rate",
            "limited-time",
            "limited time",
        )
    ):
        return True
    return bool(
        re.search(r"\b(?:for|during)\s+(?:the\s+)?(?:first\s+)?\d{1,3}[- ]?(?:days?|months?)\b", lowered)
        and any(marker in lowered for marker in ("rate", "interest", "offer", "boost", "earn"))
    )


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


def _looks_like_non_value_description(
    *,
    field_name: str,
    value: str,
    product_type_family: str | None = None,
    product_name: str | None = None,
) -> bool:
    if field_name != "description_short":
        return False
    collapsed = " ".join(value.lower().split())
    if len(collapsed) < 220 and collapsed.rstrip().endswith(":"):
        return True
    normalized = collapsed.strip(" .:-|")
    if normalized in {"offer", "special offer", "welcome offer", "compare account", "compare accounts"}:
        return True
    if expired_promotional_offer_end_date(value) is not None:
        return True
    if len(normalized) <= 40 and re.fullmatch(r"\(?\s*(?:u\s*s\s*\$?\s*)?(?:gic|term deposit)\s*\)?", normalized):
        return True
    if re.search(r"\b(?:with|for|and|or|of|to)\s+(?:an?|the|your|our)$", normalized):
        return True
    if any(
        marker in normalized
        for marker in (
            "still not sure",
            "let us help you decide",
            "answer a few quick questions",
            "we'll recommend the best",
            "we’ll recommend the best",
            "help me choose tool",
        )
    ):
        return True
    if normalized.startswith(("open account", "chequing account open account", "checking account open account")):
        return True
    if sum(
        marker in normalized
        for marker in (
            "book now",
            "call us",
            "ready to answer your questions",
            "assist you in opening an account",
            "schedule an appointment",
        )
    ) >= 2:
        return True
    if (
        normalized.startswith(("monthly account fee", "account features", "account benefits"))
        and sum(
            marker in normalized
            for marker in (
                "monthly fee",
                "earn interest",
                "interest calculated",
                "foreign currency services",
                "competitive exchange rates",
            )
        ) >= 3
    ):
        return True
    if normalized.startswith(("to qualify for this offer", "to qualify for these offers")):
        return True
    if (
        any(
            marker in normalized
            for marker in (
                "introductory interest rate",
                "introductory purchase rate",
                "introductory balance-transfer",
                "introductory balance transfer",
            )
        )
        and re.search(r"\bfor\s+(?:the\s+)?first\s+\d{1,3}\s+months?\b", normalized)
    ):
        return True
    if (
        normalized.startswith("earn an additional")
        and "bonus" in normalized
        and re.search(r"\b(?:1[0-9]|2[0-4])(?:th|st|nd|rd)\s+month\b", normalized)
    ):
        return True
    if (
        re.search(r"\bfor\s+(?:the\s+)?first\s+\d{1,3}\s+months?\b", normalized)
        and any(marker in normalized for marker in ("not a current", "haven't held", "haven?셳 held", "last two years"))
    ):
        return True
    if "scene+ account may be closed" in normalized and "membership" in normalized:
        return True
    if "earn scene+ points" in normalized and "casa" in normalized and any(
        marker in normalized for marker in ("rent", "condo fees", "housing-related")
    ):
        return True
    if "waive the monthly account fee" in normalized and "minimum balance" in normalized:
        return True
    if "proof of enrolment" in normalized and re.search(r"\b(?:age\s+)?25\b", normalized):
        return True
    if re.fullmatch(
        r"you can open (?:this |your )?account (?:online|in branch|at a branch)[^.]*",
        normalized,
    ):
        return True
    if (
        "personal bank account to fund" in normalized
        and "need an account" in normalized
        and "apply for a personal bank account" in normalized
    ):
        return True
    if (
        normalized.startswith(("you can open this account", "you can open your account"))
        and "online" in normalized
        and any(marker in normalized for marker in ("at a branch", "in person", "banking centre", "banking center"))
    ):
        return True
    if (
        normalized.startswith(("open a ", "open an "))
        and "offer ends" in normalized
        and "qualifying" in normalized
        and any(marker in normalized for marker in (" and get ", " and receive ", "welcome offer"))
    ):
        return True
    if (
        any(marker in normalized for marker in ("sign in to online banking", "sign on to online banking"))
        and any(marker in normalized for marker in ("add the ", "open the ", "apply for "))
        and "account" in normalized
    ):
        return True
    if len(normalized) >= 220 and re.search(r"\b[a-z]{3,18}$", normalized) and not re.search(r"[.!?]$", normalized):
        # Parser-flattened cards can exceed the display field's hard limit.
        # A trailing partial clause is worse than omitting the summary and
        # allowing the complete hero sentence to win on the next collection.
        return True
    if re.search(
        r"\b[\w&.-]+[’']s\s+(?:u\.s\.?|canadian|foreign(?:\s+currency)?)\.?$",
        normalized,
        flags=re.IGNORECASE,
    ):
        return True
    if normalized.startswith("$") and sum(
        marker in normalized
        for marker in ("per transfer", "atm withdrawal", "global money transfer", "no fee")
    ) >= 2:
        return True
    if (
        "features details" in normalized
        and "monthly fee" in normalized
        and "interest rate" in normalized
    ) or "eligibility with plans" in normalized or "full disclosure for" in normalized:
        return True
    if re.search(r"\bexplained in\s+20\d{2}\b", normalized) or "we take a deeper look" in normalized:
        return True
    if "ratehub" in normalized and re.search(r"\bbest\s+(?:rrsp\s+)?savings account\b", normalized):
        return True
    normalized_product_name = _normalize_text(product_name).lower()
    cross_product_lead = re.match(
        r"^(?P<other>.{4,90}?\b(?:plan|account|card|mortgage|loan))\s+(?:discount|rebate)\b",
        normalized,
    )
    if (
        cross_product_lead is not None
        and normalized_product_name
        and normalized_product_name in normalized
        and normalized_product_name not in cross_product_lead.group("other")
        and any(marker in normalized for marker in ("also have", "also hold", "customers who", "clients who"))
    ):
        return True
    if "additional account benefits" in normalized and len(normalized) >= 140:
        return True
    if "pay your friends back or chip in for" in normalized:
        return True
    if normalized.startswith("explore offers") and any(
        marker in normalized for marker in ("kids & teens", "kids and teens", "children and youth")
    ):
        return True
    if (
        "manage your pre-authorized payments" in normalized
        and "switching to" in normalized
        and "another financial institution" in normalized
    ):
        return True
    if "promotional rate" in normalized and "when you also open" in normalized:
        return True
    if normalized.startswith(("account fees learn tips", "with you as you grow")):
        return True
    if (
        "learn tips to ensure you find the right account" in normalized
        or "options to help you reduce your everyday banking fees" in normalized
    ):
        return True
    if re.search(r"\bor in the case of\b[^.]{0,100}\bgic\b", normalized):
        return True
    if (
        "provide us with instructions" in normalized
        and "gic proceeds upon maturity" in normalized
    ):
        return True
    if normalized.startswith("symbol optional legal text"):
        return True
    if (
        "eligible pre-authorized transaction" in normalized
        and "at least $" in normalized
        and re.search(r"\b(?:months?|days?) in a row\b", normalized)
    ):
        return True
    if (
        "legal disclaimer" in normalized
        or normalized.startswith("legal bug")
        or normalized.startswith(("find a branch", "come see us", "here are some additional things you can do"))
        or (
            "offer expires" in normalized
            and "%" in normalized
            and re.search(r"\bfor\s+\d{1,3}\s+months?\b", normalized)
        )
    ):
        return True
    if (
        "registered accounts have no fees while your funds are with us" in normalized
        and any(marker in normalized for marker in ("transfer your funds", "fee will apply", "fair fees mean"))
    ):
        return True
    if (
        "gic interest calculator" in normalized
        and len(re.findall(r"\b\d{1,3}(?:\.\d{1,2})?\s*(?:days?|years?)\s+\d{1,2}(?:\.\d+)?\s*%", normalized)) >= 2
    ):
        return True
    if (
        " at a glance " in f" {normalized} "
        or (normalized.startswith("your ") and " account features " in normalized)
        or (normalized.startswith("no. ") and "monthly fee rebate" in normalized)
        or normalized.startswith("legal disclaimer")
        or (
            normalized.startswith("with ")
            and "eligible" in normalized
            and "bank account" in normalized
            and any(marker in normalized for marker in ("program", "rewards", "benefits"))
        )
    ):
        return True
    if "bundle to earn" in normalized and any(
        marker in normalized for marker in ("eligible credit card", "qualifying actions", "get approved")
    ):
        return True
    if (
        re.search(r"\bearn\s+up\s+to\s+\$\s*\d", normalized)
        and "bundle" in normalized
        and sum(marker in normalized for marker in ("banking package", "savings account", "chequing account", "credit card")) >= 2
    ):
        return True
    if (
        normalized.startswith("open your first ")
        and "make a deposit" in normalized
        and any(marker in normalized for marker in ("welcome bonus", "offer terms", "additional terms apply"))
    ):
        return True
    if (
        "eligible direct deposit" in normalized
        and re.search(r"\$\s*\d[\d,]*(?:\.\d{1,2})?\s+or\s+more", normalized)
        and re.search(r"\bfor\s+\d{1,3}\s+(?:straight\s+|consecutive\s+)?months?\b", normalized)
    ):
        return True
    if (
        re.search(r"\b(?:new to|new client|new customer)\b", normalized)
        and re.search(r"\b(?:special|promotional|introductory)\s+(?:interest\s+)?rate\b", normalized)
        and re.search(r"\bfor\s+(?:the\s+)?(?:first\s+)?\d{1,3}\s+(?:days?|weeks?|months?)\b", normalized)
        and any(marker in normalized for marker in ("open ", "apply", "offer"))
    ):
        return True
    if (
        "international student gic program" in normalized
        and any(marker in normalized for marker in ("before you arrive", "visa requirements"))
        and not any(marker in normalized_product_name for marker in ("international student", "student gic"))
    ):
        return True
    if (
        any(marker in normalized for marker in ("savings accounts for kids", "children's savings account", "children’s savings account"))
        and not any(
            marker in normalized_product_name
            for marker in ("kid", "child", "youth", "student", "young saver", "leo")
        )
    ):
        return True
    if (
        normalized.startswith(("do not need to save", "don't need to save", "don’t need to save"))
        and "need an account" in normalized
    ) or "for alternate solutions to help you with everyday banking" in normalized:
        return True
    if product_type_family == "chequing" and "savings account" in normalized and not any(
        marker in normalized for marker in ("chequing", "checking")
    ):
        return True
    if product_type_family == "savings" and any(
        marker in normalized for marker in ("chequing account", "checking account")
    ) and not any(marker in normalized for marker in ("savings", "interest rate")):
        return True
    if (
        normalized.startswith("accounts ")
        and normalized.count(" account") >= 2
        and not any(
            re.search(rf"\b{verb}\b", normalized)
            for verb in ("earn", "save", "grow", "enjoy", "offer", "provide", "include", "help")
        )
    ):
        return True
    return bool(
        re.match(r"^(?:accounts?|bank accounts?|chequing accounts?|savings accounts?)\b", normalized)
        and any(marker in normalized for marker in ("welcome offer", "special offer"))
    )


def _strip_cross_product_description_sentences(value: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", _normalize_text(value))
    kept: list[str] = []
    for sentence in sentences:
        normalized = sentence.lower().strip()
        cross_product_cta = bool(
            re.match(
                r"^(?:(?:if|when)\b[^,.]{0,100},\s*)?"
                r"(?:try|consider|explore|check out)\s+(?:our|the)\b[^.]{0,120}"
                r"\b(?:account|card|mortgage|loan|line of credit)\b",
                normalized,
            )
        )
        if not cross_product_cta:
            kept.append(sentence.strip())
    return " ".join(item for item in kept if item).strip()


def _repair_flattened_customer_text(value: str) -> str:
    """Repair a small set of high-confidence HTML/PDF span-boundary joins."""

    repairs = {
        "accountfor": "account for",
        "iteasier": "it easier",
        "thechance": "the chance",
        "growand": "grow and",
        "youopen": "you open",
        "aplace": "a place",
        "atany": "at any",
        "alittle": "a little",
    }

    def replace(match: re.Match[str]) -> str:
        replacement = repairs[match.group(0).lower()]
        return replacement[:1].upper() + replacement[1:] if match.group(0)[:1].isupper() else replacement

    pattern = r"\b(?:" + "|".join(re.escape(token) for token in repairs) + r")\b"
    return re.sub(pattern, replace, _normalize_text(value), flags=re.IGNORECASE)


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
    official_grounding_metadata: dict[str, object] | None = None,
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
        grounding = official_grounding_metadata or {}
        if (
            field_name == "purchase_interest_rate"
            and grounding.get("official_grounding_contract_version")
            == "collection-official-grounding-v2"
            and grounding.get("official_verification_status") == "match"
            and grounding.get("official_grounding_method")
            in {
                "deterministic_card_comparison_origin",
                "deterministic_sibling_product_block",
            }
            and not re.search(r"(?:cash\s+advance|balance\s+transfer)", context, flags=re.IGNORECASE)
        ):
            expected = Decimal(str(numeric_value))
            for observed in re.finditer(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%", context):
                if _as_decimal(observed.group(1)) != expected:
                    continue
                window = context[
                    max(0, observed.start() - 45):min(len(context), observed.end() + 45)
                ]
                if re.search(r"\binterest\s+rate\b", window, flags=re.IGNORECASE):
                    return False
        labels = {
            "purchase_interest_rate": r"(?:purchases?\s+(?:interest\s+)?rate|interest\s+rate\s*\(\s*purchases?\s*\)|purchase\s+apr|apr\s+for\s+purchases?|annual\s+percentage\s+rate(?:\s*\(apr\))?(?:\s+for\s+purchases?)?)",
            "balance_transfer_rate": r"(?:balance\s+transfers?\s+(?:interest\s+)?rate|balance\s+transfer\s+apr|apr\s+for\s+balance\s+transfers?|balance\s+transfers?\s+and\s+cash\s+advances?)",
            "cash_advance_rate": r"(?:cash\s+(?:advance\s+)?interest\s+rate|cash\s+advances?\s+(?:interest\s+)?rate|cash\s+advance\s+apr|apr\s+for\s+cash\s+advances?|balance\s+transfers?\s+and\s+cash\s+advances?)",
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


def _looks_like_non_rate_numeric_context(
    *,
    field_name: str,
    value: object,
    context: str,
    product_type_family: str | None = None,
) -> bool:
    normalized_field = field_name.strip().lower()
    if not (normalized_field.endswith("_rate") or normalized_field in {"rate", "mortgage_rate", "interest_rate"}):
        return False
    if isinstance(value, str) and not re.fullmatch(r"\s*\d{1,3}(?:\.\d+)?\s*%?\s*", value):
        return False
    if field_name in {"interest_rate", "mortgage_rate"} and _is_reference_rate_margin_only(context):
        return True
    suppression_reason = canonical_deposit_rate_suppression_reason(value=value, context=context)
    if (
        suppression_reason == "implausible_annual_deposit_rate"
        and product_type_family in {"credit-card", "mortgage", "personal-loan", "line-of-credit"}
    ):
        suppression_reason = None
    return suppression_reason is not None or _looks_like_unresolved_placeholder(context)


def _dynamic_numeric_value_is_ungrounded(
    *,
    field_name: str,
    value: object,
    context: str,
    dynamic_field_names: set[str],
) -> bool:
    if field_name not in dynamic_field_names:
        return False
    contract = field_contract(field_name)
    if contract is None or contract.value_type not in {"decimal", "integer"}:
        return False
    return not _normalize_text(context)


def _find_dynamic_numeric_evidence_context(
    *,
    field_name: str,
    value: object,
    evidence_links: list[NormalizationEvidenceLink],
) -> str:
    """Find exact unit-bearing evidence for an AI-introduced numeric field."""

    contract = field_contract(field_name)
    if contract is None or contract.value_type not in {"decimal", "integer"}:
        return ""
    try:
        expected = Decimal(str(value).replace(",", "").replace("$", "").replace("%", "").strip())
    except InvalidOperation:
        return ""
    matches: list[str] = []
    for link in evidence_links:
        text = _normalize_text(link.evidence_text_excerpt)
        if not text:
            continue
        if contract.unit == "percentage_points":
            value_matches = any(
                _as_decimal(match.group(1)) == expected
                for match in re.finditer(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%", text)
            )
        elif contract.unit == "currency_amount":
            value_matches = any(
                _as_decimal(match.group(1).replace(",", "")) == expected
                for match in re.finditer(r"(?:\$|\u20ac|\u00a3)\s*(\d[\d,]*(?:\.\d{1,2})?)", text)
            )
            if expected == 0 and field_name.endswith("_fee"):
                value_matches = value_matches or re.search(r"\b(?:no|zero)\s+(?:annual\s+|monthly\s+)?fees?\b", text, flags=re.IGNORECASE) is not None
        else:
            value_matches = re.search(rf"(?<![\d.]){re.escape(format(expected, 'f'))}(?![\d.])", text) is not None
        if value_matches:
            matches.append(f"{link.anchor_value or ''} {text}".strip())
    return " ".join(matches)


def _money_value_is_non_fee_context(*, field_name: str, value: object, context: str) -> bool:
    if field_name not in _FEE_FIELDS:
        return False
    try:
        expected = Decimal(str(value).replace(",", "").strip())
    except InvalidOperation:
        return False
    normalized = _normalize_text(context).lower()
    if not normalized:
        return False
    for match in re.finditer(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", normalized):
        try:
            observed = Decimal(match.group(1).replace(",", ""))
        except InvalidOperation:
            continue
        if observed != expected:
            continue
        window = normalized[max(0, match.start() - 90) : min(len(normalized), match.end() + 90)]
        if any(
            marker in window
            for marker in (
                "direct deposit",
                "eligible deposit",
                "deposit today",
                "gift card",
                "cash bonus",
                "welcome bonus",
                "additional bonus",
                "purchase of",
                "spend $",
            )
        ):
            return True
    return False


def _field_is_comparison_calculator_copy(*, field_name: str, value: object, context: str) -> bool:
    if field_name not in {"minimum_balance", "interest_calculation_method"}:
        return False
    normalized = _normalize_text(context).lower()
    if not normalized:
        return False
    comparison_markers = (
        "choose up to 4 banks to compare",
        "this calculator is for illustrative purposes only",
        "rates of the selected banks",
        "similar products at the select banks",
        "national average is based on",
    )
    if not any(marker in normalized for marker in comparison_markers):
        return False
    if field_name == "interest_calculation_method":
        return True
    expected = _as_decimal(value)
    if expected is None:
        return False
    for match in re.finditer(
        r"minimum balance of(?: at least)?\s*\$\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)",
        normalized,
        flags=re.IGNORECASE,
    ):
        if _as_decimal(match.group("amount").replace(",", "")) == expected:
            return True
    return False


def _fee_value_is_plan_dependent(*, field_name: str, value: object, context: str) -> bool:
    """Reject a zero scalar when the product says its fee comes from a plan.

    A broad FAQ chunk may mention a sibling account with no monthly fee after
    stating that the target account's fee depends on its paired bank plan.
    The scalar field cannot faithfully encode that plan-dependent outcome.
    """

    if field_name not in _FEE_FIELDS:
        return False
    try:
        if Decimal(str(value).replace(",", "").strip()) != 0:
            return False
    except InvalidOperation:
        return False
    normalized = _normalize_text(context).lower()
    plan_match = re.search(
        r"\bfee\s+based\s+on\s+(?:bank\s+)?plan\s+limits\b|"
        r"\b(?:monthly\s+)?fees?\s+(?:will\s+)?depend(?:s)?\s+on\s+(?:the\s+)?(?:bank\s+)?plan\b|"
        r"\bthis\s+will\s+depend\s+on\s+the\s+bank\s+plan\b",
        normalized,
    )
    if plan_match is None:
        return False
    no_fee_match = re.search(r"\b(?:no|zero)\s+monthly\s+fees?\b|\bmonthly\s+fees?\s*\$?0(?:\.00)?\b", normalized)
    return no_fee_match is None or plan_match.start() < no_fee_match.start()


def _looks_like_invalid_field_type(*, field_name: str, value: str) -> bool:
    normalized_field = field_name.strip().lower()
    if normalized_field.endswith("_flag") or normalized_field in {"secured_flag", "redeemable_flag"}:
        return value.strip().lower() not in {"true", "false", "yes", "no", "1", "0"}
    return False


def _looks_like_invalid_tax_benefit(*, field_name: str, value: str) -> bool:
    if field_name != "tax_benefits":
        return False
    normalized = " ".join(value.lower().split())
    tax_markers = (
        "tax-free",
        "tax free",
        "tax-deferred",
        "tax deferred",
        "tax sheltered",
        "tax deduction",
        "taxable income",
        "tax benefit",
        "withholding tax",
        "income tax",
        "not taxed",
    )
    if not any(marker in normalized for marker in tax_markers):
        return True
    return any(marker in normalized for marker in ("special rate", "promotional rate", "new client offer"))


def _looks_like_unresolved_placeholder(value: str) -> bool:
    normalized = value.lower()
    return bool(
        re.search(
            r"(?:\{\{|\}\}|\$\{|rds%|%rate\b|\[object object\]"
            r"|(?<![a-z0-9])(?:\$\s*)?[x*]{2,}(?:\.[x*]+)?\s*%?(?![a-z0-9]))",
            normalized,
        )
    )


def _looks_like_wrong_frequency_context(*, field_name: str, value: str, context: str) -> bool:
    if field_name not in {"compounding_frequency", "interest_payment_frequency", "payout_option"}:
        return False
    normalized_value = value.strip().lower()
    normalized_context = " ".join(context.lower().split())
    option_markers = {
        "monthly": r"\bmonthly\b",
        "quarterly": r"\bquarterly\b",
        "semi-annually": r"\bsemi[- ]annually\b",
        "annually": r"\bannually\b|\bannual interest\b",
        "at_maturity": r"\bat maturity\b",
    }
    stated_options = {
        name for name, pattern in option_markers.items() if re.search(pattern, normalized_context)
    }
    if len(stated_options) >= 2 and normalized_value in stated_options:
        return True
    if normalized_value not in {"weekly", "biweekly", "bi-weekly", "monthly", "semi-monthly"}:
        return False
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
    context: str = "",
) -> bool:
    if field_name != "application_method":
        return False
    normalized = " ".join(value.lower().split())
    normalized_context = " ".join(context.lower().replace("_", " ").split())
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
    if (
        any(marker in normalized for marker in ("mobile app", "online banking", "abm", "access card", "cheques"))
        and any(
            marker in normalized_context
            for marker in ("funds can be accessed", "access your funds", "ways to access")
        )
        and not any(
            marker in normalized
            for marker in ("apply", "application", "open", "book an appointment", "speak to", "talk to")
        )
    ):
        return True
    if len(normalized) >= 180 and sum(
        marker in normalized
        for marker in ("interest rates", "resources", "legal", "about our", "sign on", "rate (%)", "apy (%)")
    ) >= 3:
        # A valid application method is an actionable channel, not a flattened
        # page span that happens to contain an Apply CTA near its end.
        return True
    if sum(
        marker in normalized
        for marker in (
            "monthly fee",
            "transactions included",
            "interest calculated",
            "paper or online statement",
            "minimum balance",
            "compare account",
        )
    ) >= 3:
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
    combined = f"{normalized_context} {normalized}"
    if product_type_family == "line-of-credit" and any(
        marker in combined
        for marker in ("government-guaranteed student loan", "government guaranteed student loan", "ministère", "student aid office")
    ):
        return True
    if product_type_family == "mortgage" and any(
        marker in combined for marker in ("open an account online", "business account", "business banking account")
    ) and "apply for a mortgage" not in normalized:
        return True
    if product_type_family == "personal-loan" and re.search(r"\bcar loans?\b", combined) and not re.search(
        r"\bpersonal loans?\b", normalized
    ):
        return True
    return False


def _looks_like_unsupported_security_value(*, field_name: str, context: str) -> bool:
    if field_name not in {"secured_flag", "security_requirement", "collateral_text"}:
        return False
    normalized = " ".join(context.lower().split())
    return not any(
        marker in normalized
        for marker in (
            "secured",
            "unsecured",
            "security requirement",
            "collateral",
            "guarantor",
            "co-signer",
            "cosigner",
            "pledge",
            "lien",
            "down payment",
        )
    )


def _looks_like_offer_end_mapped_as_effective_date(*, field_name: str, context: str) -> bool:
    if field_name != "effective_date":
        return False
    normalized = " ".join(context.lower().split())
    return any(
        marker in normalized
        for marker in ("offer valid until", "offer ends", "offer expires", "promotion ends", "promotion expires")
    )


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
    if field_name == "fees_text" and not any(marker in normalized for marker in ("fee", "charge", "cost")):
        return True
    if field_name == "fees_text" and any(
        marker in normalized for marker in ("penalty free", "penalty-free", "without penalty", "prepay", "repay")
    ) and not any(marker in normalized for marker in ("fee", "$")):
        return True
    if field_name == "monthly_payment_text" and any(
        marker in normalized for marker in ("calculate", "calculator", "see how much", "estimate your")
    ) and not re.search(r"(?:\$|\b\d[\d,.]*\b|weekly|biweekly|bi-weekly|monthly)", normalized):
        return True
    if field_name == "monthly_payment_text" and not re.search(r"\b(?:payment|payments|repayment|repay)\b", normalized):
        return True
    if field_name == "minimum_payment_text" and not (
        re.search(r"\b(?:minimum\s+payment|payment|payments|pay\s+at\s+least|repayment|repay)\b", normalized)
        or re.search(r"\b(?:interest[- ]only|interest\s+and\s+principal|principal\s+and\s+interest)\b", normalized)
    ):
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
    lowered = normalized.lower()
    if field_name == "application_method" and normalized.lower().startswith("how do i apply"):
        return True
    if field_name == "notes" and normalized.lower().startswith(
        ("legal footnote", "legal disclaimer", "footnote details")
    ):
        return True
    if field_name == "notes" and (
        "other conditions and exceptions may apply" in lowered
        or ("due to system limitations" in lowered and "bundling" in lowered)
        or ("refer to" in lowered and "for full details" in lowered)
        or "for alternate solutions to help you with everyday banking" in lowered
    ):
        return True
    if field_name == "withdrawal_limit_text" and lowered.strip(" .:-") in {"withdrawal fee", "withdrawal fees"}:
        return True
    if field_name == "interest_calculation_method" and not any(
        marker in lowered
        for marker in (
            "calculated",
            "calculation",
            "accrues",
            "compounded",
            "paid monthly",
            "paid annually",
            "daily closing balance",
            "rate paid depends",
        )
    ):
        return True
    if field_name == "tier_definition_text" and (
        sum(marker in lowered for marker in ("monthly account fee", "free debit", "foreign exchange", "no fee for")) >= 2
        and len(re.findall(r"\d{1,3}(?:\.\d+)?\s*%", lowered)) < 2
    ):
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
        "tax_benefits",
        "term_length_text",
        "prepayment_privileges",
    }
    if field_name == "deposit_insurance" and sum(
        marker in normalized.lower()
        for marker in ("contact us", "abm locator", "rates", "careers", "community", "get our app", "connect with us")
    ) >= 3:
        return True
    if field_name == "deposit_insurance" and "canada deposit insurance corporation" in lowered and sum(
        marker in lowered
        for marker in (
            "more account information",
            "summary of account fees",
            "savings account interest rates",
            "branch locator",
            "regulatory information",
        )
    ) >= 2:
        return True
    return len(normalized) >= 240 and field_name in concise_fields


def _looks_like_gic_field_context_mismatch(
    *, field_name: str, value: str, product_name: str, product_type_family: str | None
) -> bool:
    if product_type_family != "gic" or field_name != "tax_benefits":
        return False
    normalized = " ".join(value.lower().split())
    identity = " ".join(product_name.lower().split())
    navigation_markers = (
        "bank accounts",
        "credit cards",
        "mortgages",
        "personal loans",
        "investments",
        "contact us",
        "about us",
        "legal",
    )
    if sum(marker in normalized for marker in navigation_markers) >= 3:
        return True
    retirement_identity = any(marker in identity for marker in ("rsp", "rrsp", "rif", "retirement"))
    retirement_context = any(
        marker in normalized for marker in ("rsp", "rrsp", "rif", "retirement", "tax-deferred", "tax sheltered")
    )
    if retirement_identity and any(marker in normalized for marker in ("tfsa", "tax-free")) and not retirement_context:
        return True
    tfsa_identity = any(marker in identity for marker in ("tfsa", "tax-free"))
    if tfsa_identity and retirement_context and not any(marker in normalized for marker in ("tfsa", "tax-free")):
        return True
    return False


def _duplicated_page_copy_fields(candidate_payload: dict[str, object]) -> set[str]:
    by_value: dict[str, list[str]] = {}
    for field_name, value in candidate_payload.items():
        if not isinstance(value, str):
            continue
        normalized = " ".join(value.lower().split()).strip(" .:;|-_")
        if len(normalized) < 80:
            continue
        by_value.setdefault(normalized, []).append(field_name)
    duplicated: set[str] = set()
    for field_names in by_value.values():
        if len(field_names) < 2:
            continue
        if "description_short" in field_names:
            duplicated.update(field_name for field_name in field_names if field_name != "description_short")
        else:
            duplicated.update(field_names)
    return duplicated


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
    boundary_tolerances = [max(7, round(duration * 0.08)) for duration in durations]
    if any(abs(numeric_days - duration) <= tolerance for duration, tolerance in zip(durations, boundary_tolerances)):
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


def _suppress_scalar_term_for_multi_term_table(
    *,
    candidate_payload: dict[str, object],
    normalized_values_for_links: dict[str, object] | None,
    field_mapping_metadata: dict[str, object] | None,
    runtime_notes: list[str] | None,
) -> None:
    rows = candidate_payload.get("term_rate_table")
    if not isinstance(rows, list):
        return
    distinct_terms = {
        (row.get("term_length_days"), str(row.get("term_label") or "").strip().lower())
        for row in rows
        if isinstance(row, dict)
        and (row.get("term_length_days") not in {None, ""} or row.get("term_label"))
    }
    if len(distinct_terms) < 2:
        return
    term_text = str(candidate_payload.get("term_length_text") or "").strip()
    declared_durations = re.findall(
        r"(?<!\d)\d{1,3}\s*(?:day|days|month|months|year|years)\b",
        term_text,
        flags=re.IGNORECASE,
    )
    if len(declared_durations) != 1:
        return
    removed: list[str] = []
    for field_name in ("term_length_days", "term_length_text"):
        if field_name not in candidate_payload:
            continue
        candidate_payload.pop(field_name, None)
        if normalized_values_for_links is not None:
            normalized_values_for_links.pop(field_name, None)
        if field_mapping_metadata is not None:
            metadata = dict(field_mapping_metadata.get(field_name) or {})
            metadata.update(
                {
                    "normalized_value": None,
                    "normalization_method": "multi_term_table_scalar_safety",
                    "suppressed_reason": "single_term_scalar_in_multi_term_product",
                }
            )
            field_mapping_metadata[field_name] = metadata
        removed.append(field_name)
    if removed and runtime_notes is not None:
        runtime_notes.append(
            "Suppressed a single-term scalar because the same product publishes a multi-term rate table."
        )


def _looks_like_non_value_eligibility(
    *, field_name: str, value: str, product_name: str | None = None
) -> bool:
    if field_name not in {"eligibility", "eligibility_text"}:
        return False
    normalized = " ".join(value.lower().split())
    truncated_program_definition = (
        len(normalized) >= 80
        and not re.search(r"[.!?]$", normalized)
        and re.search(r"\b(?:by having|with|from) an eligible$", normalized) is not None
    )
    application_or_program_instructions = any(
        marker in normalized
        for marker in (
            "to apply, you’ll need",
            "to apply, you'll need",
            "automatically apply the highest value rebate",
            "activate the value program",
            "eligible for one fee-waiver",
        )
    )
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
    eligibility_criteria = any(
        marker in normalized
        for marker in (
            "must ",
            "requires ",
            "eligible if",
            "at least",
            "minimum ",
            "resident",
            "income",
            "credit score",
            "age of majority",
            "canadian citizen",
        )
    )
    rate_or_insurance_card = not eligibility_criteria and (
        "%" in normalized
        or "eligible for cdic coverage" in normalized
        or "eligible for cdic insurance" in normalized
        or "deposit insurance" in normalized
    )
    application_cta = not eligibility_criteria and bool(
        re.fullmatch(
            r"(?:how to apply\s*)?(?:talk|speak) to an? (?:scotia )?advisor(?:\s+book an appointment)?",
            normalized.strip(" .:-"),
        )
    )
    cross_product_offer = not eligibility_criteria and (
        any(
            marker in normalized
            for marker in ("eligible credit card", "eligible chequing account", "eligible savings account")
        )
        and any(
            marker in normalized
            for marker in ("qualifying transaction", "qualifying condition", "cash bonus", "bundle bonus")
        )
    )
    cross_product_application = not eligibility_criteria and "eligible credit card" in normalized and "then apply" in normalized
    direct_deposit_offer = "eligible direct deposit" in normalized and (
        re.search(r"\bfor\s+\d{1,3}\s+(?:straight\s+|consecutive\s+)?months?\b", normalized) is not None
        or any(marker in normalized for marker in ("welcome offer", "cash bonus", "gift card", "offer ends"))
    )
    generic_cash_offer = (
        any(marker in normalized for marker in ("cash bonus bundle offer", "cash bonus", "welcome offer"))
        and any(marker in normalized for marker in ("qualifying transactions", "offer period", "offer terms"))
    )
    promotional_transaction_criteria = any(
        marker in normalized
        for marker in (
            "only the following visa debit transaction types are eligible",
            "list of eligible direct deposits and pre-authorized transactions",
            "list of eligible direct deposits and preauthorized transactions",
        )
    )
    ancillary_product_offer = (
        "to qualify" in normalized
        and (
            ("mortgage" in normalized and any(marker in normalized for marker in ("preferred mortgage rate", "preauthorized mortgage payment")))
            or ("fee waiver" in normalized and "account holder" in normalized)
        )
    )
    overdraft_feature = (
        "eligible for overdraft protection" in normalized
        and not eligibility_criteria
    )
    brokerage_benefit = (
        "account holders" in normalized
        and "commission" in normalized
        and any(marker in normalized for marker in ("trades", "trading", "brokerage"))
    )
    acquisition_offer_criteria = any(
        marker in normalized
        for marker in (
            "the offer is available to new",
            "offer is only applicable",
            "qualifying conditions",
            "promotional rate will apply",
        )
    ) and any(marker in normalized for marker in ("offer", "promotional rate", "eligible savings account"))
    acquisition_offer_criteria = acquisition_offer_criteria or bool(
        re.search(r"\b(?:the\s+[^.]{0,90}\s+)?offer\b[^.]{0,60}\bavailable to new\b", normalized)
        and any(
            marker in normalized
            for marker in ("client number", "within 60 days", "primary account holder", "eligible savings account")
        )
    )
    promotional_history_criteria = any(
        marker in normalized
        for marker in (
            "preceding the offer period",
            "not eligible for this bonus",
            "haven't had",
            "haven’t had",
            "held either account within",
        )
    ) and any(marker in normalized for marker in ("offer", "bonus", "promo", "promotional"))
    promotional_history_criteria = promotional_history_criteria or (
        "offer eligibility" in normalized
        and "previously" in normalized
        and "cardholder" in normalized
        and re.search(r"\bpast\s+\d{1,2}\s+years?\b", normalized) is not None
    )
    rewards_platform_usage = (
        "scene+" in normalized
        and "casa" in normalized
        and any(marker in normalized for marker in ("rent", "condo fees", "housing-related bill"))
    )
    product_feature_list = (
        "guaranteed rate for your entire term" in normalized
        and "principal is always guaranteed" in normalized
        and any(marker in normalized for marker in ("compound automatically", "registered and non-registered plans"))
    )
    dated_account_offer = re.search(
        r"\bto qualify(?: for (?:this|the|these) offers?)?,?\s+(?:make sure to\s+)?open\s+a\s+new\b"
        r"[\s\S]{0,180}?\bbetween\s+[a-z]+\s+\d{1,2},\s+20\d{2}\s+and\s+[a-z]+\s+\d{1,2},\s+20\d{2}",
        normalized,
    ) is not None
    normalized_product_name = " ".join(str(product_name or "").lower().split())
    audience_sibling = (
        any(
            marker in normalized
            for marker in ("international student", "visa requirements", "before you arrive in canada")
        )
        and not any(
            marker in normalized_product_name
            for marker in ("international student", "student gic", "student program")
        )
    )
    generic_marketing = not eligibility_criteria and any(
        marker in normalized
        for marker in (
            "great option when you need",
            "focus on your",
            "make it happen",
            "hassle-free",
            "qualifying actions apply",
            "take advantage of offers and perks",
            "bundle with any eligible",
            "then apply and get approved for any eligible",
            "suitable for applicants who want",
            "right for you if you want",
        )
    )
    generic_marketing = generic_marketing or (
        normalized.count("want to") >= 2
        and not any(
            marker in normalized
            for marker in ("must ", "resident", "minimum income", "credit score", "age of majority")
        )
    )
    rewards_example = not eligibility_criteria and (
        any(marker in normalized for marker in ("eligible purchase", "eligible grocery", "eligible gas"))
        and any(marker in normalized for marker in ("point", "reward", "cash back", "cashback", "earn"))
    )
    return (
        calculator_cta
        or estimate_output
        or rate_or_insurance_card
        or application_cta
        or cross_product_offer
        or cross_product_application
        or direct_deposit_offer
        or generic_cash_offer
        or promotional_transaction_criteria
        or ancillary_product_offer
        or overdraft_feature
        or brokerage_benefit
        or acquisition_offer_criteria
        or promotional_history_criteria
        or rewards_platform_usage
        or product_feature_list
        or dated_account_offer
        or audience_sibling
        or generic_marketing
        or rewards_example
        or application_or_program_instructions
        or truncated_program_definition
        or len(normalized) < 120 and (
        normalized.startswith("and ")
        or "we understand that" in normalized
        or normalized in {"learn more", "get started", "contact us"}
        )
    )


def _audience_flag_is_legal_enumeration(*, field_name: str, value: object, context: str) -> bool:
    if field_name not in {"student_plan_flag", "newcomer_plan_flag"} or not _truthy(value):
        return False
    normalized = _normalize_text(context).lower()
    return bool(
        re.search(
            r"\b(?:means|includes?)\s+(?:any\s+of\s+)?(?:the\s+)?following\s+accounts?\b",
            normalized,
        )
        and any(marker in normalized for marker in ("offer eligibility", "offer exclusions", "package bonus"))
    )


def _looks_like_non_value_rewards(*, field_name: str, value: str) -> bool:
    if field_name != "rewards_summary":
        return False
    normalized = _normalize_text(value).lower()
    promotional = any(
        marker in normalized
        for marker in ("welcome offer", "bonus points", "bonus scene+", "first 3 months", "first 6 months", "first 14 months")
    )
    ongoing = (
        re.search(r"\b(?:earn|get)\s+(?:up to\s+)?\d+(?:\.\d+)?\s*(?:%|points?)\b[^.]{0,120}\b(?:per|on)\b", normalized)
        is not None
        or any(marker in normalized for marker in ("on every purchase", "on all other eligible", "cash back on eligible"))
    )
    truncated = re.search(
        r"\b(?:o|ot|oth|elig|eligi|purch|purcha)$",
        normalized,
    ) is not None
    return (promotional and not ongoing) or truncated


def _looks_like_expired_promotional_customer_field(
    *,
    field_name: str,
    value: str,
    context: str,
    expired_offer_present: bool,
) -> bool:
    if field_name not in {"description_short", "eligibility_text", "notes", "promotional_period_text", "rewards_summary"}:
        return False
    if expired_promotional_offer_end_date(value) is not None or expired_promotional_offer_end_date(context) is not None:
        return True
    if not expired_offer_present:
        return False
    normalized = _normalize_text(f"{value} {context}").lower()
    if field_name == "eligibility_text" and re.search(r"\bto qualify\b[\s\S]{0,120}?\bopen\s+a\s+new\b", normalized):
        return True
    return any(
        marker in normalized
        for marker in (
            "special offer", "welcome offer", "introductory", "bonus points", "bonus scene+",
            "for the first 3 months", "for the first 6 months", "for the first 9 months", "first 14 months",
        )
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
                "Never map cashback, rewards, prepayment, equity, down-payment, instalment-plan, transaction-fee, or ATM/ABM assessment percentages to generic annual rate fields. "
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
    country_code: str | None,
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
        domestic_currency = default_currency_for_country(country_code)
        if currency and domestic_currency and currency != domestic_currency:
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
    identity_text = str(candidate_payload.get("product_name") or "").lower()
    if "student" in identity_text or "youth" in identity_text or _truthy(candidate_payload.get("student_plan_flag")):
        tags.append("student")
    if "newcomer" in identity_text or _truthy(candidate_payload.get("newcomer_plan_flag")):
        tags.append("newcomer")
    if "senior" in identity_text:
        tags.append("senior")
    if any(
        token in identity_text
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
        r"(?P<term>\d{1,3}(?:\.\d{1,2})?\s*(?:day|days|month|months|year|years))\s*[:\-]?\s*(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
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
    match = re.search(
        r"(?<![\d.])(\d{1,3}(?:\.\d{1,2})?)\s*(day|days|month|months|year|years)\b",
        term_label,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    value = _as_decimal(match.group(1))
    if value is None:
        return None
    unit = match.group(2).lower()
    if unit.startswith("day"):
        days = value
    elif unit.startswith("month"):
        days = value * Decimal("30")
    elif unit.startswith("year"):
        days = value * Decimal("365")
    else:
        return None
    if days != days.to_integral_value():
        days = (days + Decimal("0.5")).to_integral_value()
    return int(days)


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


def _official_grounding_mapping_metadata(field: NormalizationExtractedField) -> dict[str, object]:
    metadata = field.field_metadata if isinstance(field.field_metadata, dict) else {}
    if metadata.get("official_grounding_contract_version") != "collection-official-grounding-v2":
        return {}
    return {
        "official_grounding_contract_version": "collection-official-grounding-v2",
        "official_grounding_method": metadata.get("official_grounding_method"),
        "official_verification_status": metadata.get("official_verification_status"),
        "official_web_sources": list(metadata.get("official_web_sources") or []),
        "official_evidence_quote": metadata.get("evidence_quote"),
        "official_rationale": metadata.get("rationale"),
    }


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
