from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re

from worker.pipeline.fpds_ai_runtime import (
    configured_model_id,
    estimated_cost_usd,
    invoke_openai_json_schema,
    llm_provider_configured,
)
from worker.pipeline.fpds_evidence_retrieval.models import (
    EvidenceChunkCandidate,
    EvidenceMatch,
    EvidenceRetrievalRequest,
    MetadataFilters,
)
from worker.pipeline.fpds_evidence_retrieval.service import EvidenceRetrievalService

from .models import (
    EvidenceLinkDraft,
    ExtractedFieldCandidate,
    ExtractionDocumentContext,
    ExtractionInput,
    ExtractionResult,
    ExtractionSourceResult,
)
from .storage import ExtractionStorageConfig

_DEFAULT_EXTRACTABLE_FIELDS = (
    "product_name",
    "description_short",
    "monthly_fee",
    "public_display_fee",
    "fee_waiver_condition",
    "minimum_balance",
    "minimum_deposit",
    "standard_rate",
    "public_display_rate",
    "promotional_rate",
    "promotional_period_text",
    "introductory_rate_flag",
    "eligibility_text",
    "interest_calculation_method",
    "interest_payment_frequency",
    "tiered_rate_flag",
    "tier_definition_text",
    "withdrawal_limit_text",
    "registered_flag",
    "term_length_text",
    "term_length_days",
    "redeemable_flag",
    "non_redeemable_flag",
    "compounding_frequency",
    "payout_option",
    "registered_plan_supported",
    "included_transactions",
    "unlimited_transactions_flag",
    "interac_e_transfer_included",
    "overdraft_available",
    "cheque_book_info",
    "student_plan_flag",
    "newcomer_plan_flag",
    "notes",
)
_COMMON_DEFAULT_FIELDS = {
    "product_name",
    "description_short",
    "monthly_fee",
    "public_display_fee",
    "fee_waiver_condition",
    "minimum_balance",
    "minimum_deposit",
    "eligibility_text",
    "notes",
}
_PRODUCT_TYPE_DEFAULT_FIELDS = {
    "savings": _COMMON_DEFAULT_FIELDS
    | {
        "standard_rate",
        "public_display_rate",
        "promotional_rate",
        "promotional_period_text",
        "introductory_rate_flag",
        "interest_calculation_method",
        "interest_payment_frequency",
        "tiered_rate_flag",
        "tier_definition_text",
        "withdrawal_limit_text",
        "registered_flag",
    },
    "chequing": _COMMON_DEFAULT_FIELDS
    | {
        "included_transactions",
        "unlimited_transactions_flag",
        "interac_e_transfer_included",
        "overdraft_available",
        "cheque_book_info",
        "student_plan_flag",
        "newcomer_plan_flag",
    },
    "gic": _COMMON_DEFAULT_FIELDS
    | {
        "standard_rate",
        "public_display_rate",
        "promotional_rate",
        "promotional_period_text",
        "introductory_rate_flag",
        "term_length_text",
        "term_length_days",
        "redeemable_flag",
        "non_redeemable_flag",
        "compounding_frequency",
        "payout_option",
        "registered_plan_supported",
    },
}
_PERCENT_RE = re.compile(r"(?<!\d)(\d{1,2}(?:\.\d{1,4})?)\s*%")
_MONEY_RE = re.compile(r"\$\s?([0-9][0-9,]*(?:\.\d{1,2})?)")
_TERM_RE = re.compile(
    r"(?<!\d)(\d{1,3})\s*(?:-|\s)?\s*(day|days|month|months|year|years)\b"
    r"(?:\s*(?:to|-)\s*(\d{1,3})\s*(?:-|\s)?\s*(day|days|month|months|year|years)\b)?",
    re.IGNORECASE,
)
_WHITESPACE_RE = re.compile(r"\s+")
_CANONICAL_PRODUCT_TYPES = {"chequing", "savings", "gic"}
_TERM_CONTEXT_KEYWORDS = (
    "term",
    "terms",
    "maturity",
    "cashable",
    "redeemable",
    "gic",
    "certificate",
    "deposit",
    "investment",
    "principal",
    "payout",
)
_TERM_CONTEXT_BLOCKLIST = (
    "days old",
    "day old",
    "viewed online",
    "cheque image",
    "check image",
    "mobile app",
    "promo period",
    "promotional period",
    "introductory",
)
_GENERIC_TITLE_LINES = {
    "document",
    "benefits",
    "ratesandfees",
    "rates",
    "rates and fees",
    "fees",
    "interest",
    "mobile",
    "faq",
    "faqs",
    "features",
    "details",
    "overview",
    "open account",
    "more details",
    "learn more",
}
_GENERIC_TITLE_PREFIXES = (
    "what ",
    "how ",
    "why ",
    "can ",
    "do ",
    "sign up ",
    "register ",
    "complete ",
    "get ",
    "find out ",
    "compare ",
    "explore ",
    "ready to ",
    "open ",
    "apply ",
    "manage ",
    "pay ",
    "earn ",
)
_PRODUCT_TITLE_KEYWORDS = (
    "account",
    "accounts",
    "savings",
    "esavings",
    "chequing",
    "checking",
    "gic",
    "deposit",
    "banking",
    "package",
    "plan",
    "bundle",
    "cashable",
    "redeemable",
)


class ExtractionService:
    def __init__(
        self,
        *,
        storage_config: ExtractionStorageConfig,
        object_store,
        retrieval_service: EvidenceRetrievalService | None = None,
        agent_name: str = "fpds-heuristic-extractor",
        model_id: str = "heuristic-extractor-v1",
        extraction_fields: tuple[str, ...] = _DEFAULT_EXTRACTABLE_FIELDS,
    ) -> None:
        self.storage_config = storage_config
        self.object_store = object_store
        self.retrieval_service = retrieval_service or EvidenceRetrievalService()
        self.agent_name = agent_name
        self.model_id = model_id
        self.extraction_fields = extraction_fields

    def extract_documents(
        self,
        *,
        run_id: str,
        inputs: list[ExtractionInput],
        correlation_id: str | None = None,
        request_id: str | None = None,
        override_field_names: list[str] | None = None,
    ) -> ExtractionResult:
        source_results: list[ExtractionSourceResult] = []
        partial_completion_flag = False

        for item in inputs:
            result = self._extract_single_document(
                run_id=run_id,
                extraction_input=item,
                correlation_id=correlation_id,
                request_id=request_id,
                override_field_names=override_field_names,
            )
            source_results.append(result)
            if result.extraction_action == "failed":
                partial_completion_flag = True

        return ExtractionResult(
            run_id=run_id,
            correlation_id=correlation_id,
            request_id=request_id,
            source_results=source_results,
            partial_completion_flag=partial_completion_flag,
        )

    def _extract_single_document(
        self,
        *,
        run_id: str,
        extraction_input: ExtractionInput,
        correlation_id: str | None,
        request_id: str | None,
        override_field_names: list[str] | None,
    ) -> ExtractionSourceResult:
        context = extraction_input.context
        started_at = _utc_now_iso()
        model_execution_id = _build_model_execution_id(run_id, context.source_document_id, context.parsed_document_id)
        field_names = _resolve_field_names(
            context=context,
            override_field_names=override_field_names,
            default_fields=self.extraction_fields,
        )
        retrieval_request = EvidenceRetrievalRequest(
            correlation_id=correlation_id,
            run_id=run_id,
            parsed_document_id=context.parsed_document_id,
            field_names=field_names,
            metadata_filters=MetadataFilters(
                bank_code=context.bank_code,
                country_code=context.country_code,
                source_language=context.source_language,
            ),
            retrieval_mode="metadata-only",
            max_matches_per_field=3,
        )

        try:
            retrieval_result = self.retrieval_service.retrieve(
                request=retrieval_request,
                candidates=extraction_input.candidates,
            )
            extracted_fields = _extract_fields(
                context=context,
                candidates=extraction_input.candidates,
                matches=retrieval_result.matches,
                requested_fields=field_names,
            )
            runtime_notes = list(retrieval_result.runtime_notes)
            agent_name = self.agent_name
            model_id = self.model_id
            usage_metadata: dict[str, object] = {
                "usage_mode": "heuristic-no-llm-call",
                "provider": "local",
                "model_id": self.model_id,
            }
            prompt_tokens = 0
            completion_tokens = 0
            provider_request_id = None

            if _uses_dynamic_product_type(context):
                ai_fields, ai_notes, ai_usage = _extract_dynamic_fields_with_ai(
                    context=context,
                    candidates=extraction_input.candidates,
                    requested_fields=field_names,
                )
                runtime_notes.extend(ai_notes)
                if ai_fields:
                    extracted_fields = _merge_extracted_fields(base_fields=extracted_fields, ai_fields=ai_fields)
                if ai_usage:
                    agent_name = "fpds-dynamic-product-extractor"
                    model_id = str(ai_usage["model_id"])
                    prompt_tokens = int(ai_usage.get("prompt_tokens") or 0)
                    completion_tokens = int(ai_usage.get("completion_tokens") or 0)
                    provider_request_id = ai_usage.get("provider_request_id")
                    usage_metadata = {
                        "usage_mode": "openai-dynamic-product-extraction",
                        "provider": "openai",
                        "model_id": model_id,
                    }
            evidence_links = [
                EvidenceLinkDraft(
                    field_name=field.field_name,
                    candidate_value=_stringify_candidate_value(field.candidate_value),
                    evidence_chunk_id=str(field.evidence_chunk_id),
                    evidence_text_excerpt=str(field.evidence_text_excerpt),
                    source_document_id=field.source_document_id,
                    source_snapshot_id=field.source_snapshot_id,
                    citation_confidence=field.confidence,
                    model_execution_id=model_execution_id,
                    anchor_type=field.anchor_type,
                    anchor_value=field.anchor_value,
                    page_no=field.page_no,
                    chunk_index=field.chunk_index,
                )
                for field in extracted_fields
                if field.evidence_chunk_id is not None and field.evidence_text_excerpt is not None
            ]

            extracted_storage_key = self.storage_config.build_extracted_object_key(
                country_code=context.country_code,
                bank_code=context.bank_code,
                source_document_id=context.source_document_id,
                parsed_document_id=context.parsed_document_id,
            )
            metadata_storage_key = self.storage_config.build_metadata_object_key(
                country_code=context.country_code,
                bank_code=context.bank_code,
                source_document_id=context.source_document_id,
                parsed_document_id=context.parsed_document_id,
            )
            artifact_payload = _build_extracted_artifact_payload(
                context=context,
                run_id=run_id,
                correlation_id=correlation_id,
                request_id=request_id,
                field_names=field_names,
                retrieval_result=retrieval_result.to_dict(),
                extracted_fields=extracted_fields,
                evidence_links=evidence_links,
                model_execution_id=model_execution_id,
                agent_name=agent_name,
                model_id=model_id,
                started_at=started_at,
            )
            metadata_payload = _build_metadata_payload(
                context=context,
                model_execution_id=model_execution_id,
                extracted_storage_key=extracted_storage_key,
                metadata_storage_key=metadata_storage_key,
                extracted_fields=extracted_fields,
                evidence_links=evidence_links,
                runtime_notes=runtime_notes,
            )
            self.object_store.put_object_bytes(
                object_key=extracted_storage_key,
                data=json.dumps(artifact_payload, indent=2, ensure_ascii=True).encode("utf-8"),
                content_type="application/json",
            )
            self.object_store.put_object_bytes(
                object_key=metadata_storage_key,
                data=json.dumps(metadata_payload, indent=2, ensure_ascii=True).encode("utf-8"),
                content_type="application/json",
            )
            if not evidence_links:
                runtime_notes.append("No evidence-linked field candidates were extracted for this parsed document.")

            warning_count = 1 if runtime_notes else 0
            completed_at = _utc_now_iso()
            model_execution_record = _build_model_execution_record(
                model_execution_id=model_execution_id,
                run_id=run_id,
                source_document_id=context.source_document_id,
                execution_status="completed",
                agent_name=agent_name,
                model_id=model_id,
                started_at=started_at,
                completed_at=completed_at,
                execution_metadata={
                    "parsed_document_id": context.parsed_document_id,
                    "snapshot_id": context.snapshot_id,
                    "requested_fields": field_names,
                    "retrieval_mode": retrieval_result.applied_retrieval_mode,
                    "runtime_notes": runtime_notes,
                    "extracted_field_count": len(extracted_fields),
                    "evidence_link_count": len(evidence_links),
                    "extracted_storage_key": extracted_storage_key,
                    "metadata_storage_key": metadata_storage_key,
                },
            )
            usage_record = _build_usage_record(
                run_id=run_id,
                model_execution_id=model_execution_id,
                recorded_at=completed_at,
                usage_metadata=usage_metadata,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                provider_request_id=provider_request_id,
            )
            return ExtractionSourceResult(
                source_id=context.source_id,
                source_document_id=context.source_document_id,
                snapshot_id=context.snapshot_id,
                parsed_document_id=context.parsed_document_id,
                extraction_action="stored",
                model_execution_id=model_execution_id,
                extracted_storage_key=extracted_storage_key,
                metadata_storage_key=metadata_storage_key,
                extracted_fields=extracted_fields,
                evidence_links=evidence_links,
                runtime_notes=runtime_notes,
                error_summary=None,
                model_execution_record=model_execution_record,
                usage_record=usage_record,
                run_source_item_record=_build_run_source_item_record(
                    run_id=run_id,
                    context=context,
                    stage_status="completed",
                    warning_count=warning_count,
                    error_count=0,
                    error_summary=None,
                    stage_metadata={
                        "extraction_action": "stored",
                        "parsed_document_id": context.parsed_document_id,
                        "model_execution_id": model_execution_id,
                        "extracted_storage_key": extracted_storage_key,
                        "metadata_storage_key": metadata_storage_key,
                        "extracted_field_count": len(extracted_fields),
                        "evidence_link_count": len(evidence_links),
                        "runtime_notes": runtime_notes,
                        "correlation_id": correlation_id,
                        "request_id": request_id,
                    },
                ),
            )
        except Exception as exc:
            completed_at = _utc_now_iso()
            error_summary = str(exc)
            return ExtractionSourceResult(
                source_id=context.source_id,
                source_document_id=context.source_document_id,
                snapshot_id=context.snapshot_id,
                parsed_document_id=context.parsed_document_id,
                extraction_action="failed",
                model_execution_id=model_execution_id,
                extracted_storage_key=None,
                metadata_storage_key=None,
                extracted_fields=[],
                evidence_links=[],
                runtime_notes=[],
                error_summary=error_summary,
                model_execution_record=_build_model_execution_record(
                    model_execution_id=model_execution_id,
                    run_id=run_id,
                    source_document_id=context.source_document_id,
                    execution_status="failed",
                    agent_name=self.agent_name,
                    model_id=self.model_id,
                    started_at=started_at,
                    completed_at=completed_at,
                    execution_metadata={
                        "parsed_document_id": context.parsed_document_id,
                        "snapshot_id": context.snapshot_id,
                        "error_summary": error_summary,
                    },
                ),
                usage_record=None,
                run_source_item_record=_build_run_source_item_record(
                    run_id=run_id,
                    context=context,
                    stage_status="failed",
                    warning_count=0,
                    error_count=1,
                    error_summary=error_summary,
                    stage_metadata={
                        "extraction_action": "failed",
                        "parsed_document_id": context.parsed_document_id,
                        "model_execution_id": model_execution_id,
                        "correlation_id": correlation_id,
                        "request_id": request_id,
                    },
                ),
            )


def _resolve_field_names(
    *,
    context: ExtractionDocumentContext,
    override_field_names: list[str] | None,
    default_fields: tuple[str, ...],
) -> list[str]:
    if override_field_names:
        return sorted(dict.fromkeys(item.strip() for item in override_field_names if item.strip()))

    product_type = _infer_product_type(context)
    product_default_fields = _PRODUCT_TYPE_DEFAULT_FIELDS.get(product_type)
    fields: list[str] = []
    for field_name in default_fields:
        if product_default_fields is not None and field_name not in product_default_fields:
            continue
        if field_name not in fields:
            fields.append(field_name)
    for field_name in context.source_metadata.get("expected_fields", []):
        normalized = str(field_name).strip()
        if product_type in _CANONICAL_PRODUCT_TYPES and normalized not in default_fields:
            continue
        if product_default_fields is not None and normalized not in product_default_fields:
            continue
        if normalized and normalized not in fields:
            fields.append(normalized)
    return fields


def _extract_fields(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    matches: list[EvidenceMatch],
    requested_fields: list[str],
) -> list[ExtractedFieldCandidate]:
    extracted: list[ExtractedFieldCandidate] = [
        _build_derived_field(context=context, field_name="product_family", candidate_value="deposit", value_type="string"),
        _build_derived_field(context=context, field_name="product_type", candidate_value=_infer_product_type(context), value_type="string"),
        _build_derived_field(context=context, field_name="bank_code", candidate_value=context.bank_code, value_type="string"),
        _build_derived_field(context=context, field_name="country_code", candidate_value=context.country_code, value_type="string"),
        _build_derived_field(
            context=context,
            field_name="source_language",
            candidate_value=context.source_language or "und",
            value_type="string",
        ),
        _build_derived_field(context=context, field_name="currency", candidate_value=_infer_currency(context=context), value_type="string"),
    ]

    if "product_name" in requested_fields:
        title = _extract_document_title(context=context, candidates=candidates)
        if title:
            extracted.append(
                _build_derived_field(
                    context=context,
                    field_name="product_name",
                    candidate_value=title,
                    value_type="string",
                    extraction_method="derived_title",
                    confidence=0.88,
                )
            )
    if "description_short" in requested_fields:
        description = _extract_description(candidates)
        if description:
            extracted.append(
                _build_derived_field(
                    context=context,
                    field_name="description_short",
                    candidate_value=description,
                    value_type="string",
                    extraction_method="derived_description",
                    confidence=0.7,
                )
            )

    matches_by_field: dict[str, list[EvidenceMatch]] = {}
    for match in matches:
        matches_by_field.setdefault(match.field_name, []).append(match)

    candidate_map = {candidate.evidence_chunk_id: candidate for candidate in candidates}
    for field_name in requested_fields:
        if field_name in {
            "product_name",
            "description_short",
            "product_type",
            "product_family",
            "bank_code",
            "country_code",
            "source_language",
            "currency",
        }:
            continue
        extracted_field = _extract_from_matches(
            context=context,
            field_name=field_name,
            matches=matches_by_field.get(field_name, []),
            candidate_map=candidate_map,
        )
        if extracted_field is not None:
            extracted.append(extracted_field)

    return _dedupe_fields(extracted)


def _extract_from_matches(
    *,
    context: ExtractionDocumentContext,
    field_name: str,
    matches: list[EvidenceMatch],
    candidate_map: dict[str, EvidenceChunkCandidate],
) -> ExtractedFieldCandidate | None:
    for match in matches:
        if match.evidence_chunk_id not in candidate_map:
            continue
        candidate_value, value_type, extraction_method, field_metadata = _extract_candidate_value(
            context=context,
            field_name=field_name,
            excerpt=match.evidence_text_excerpt,
            anchor_value=match.anchor_value,
        )
        if candidate_value is None:
            continue
        confidence = round(min(0.99, max(0.55, match.score)), 4)
        return ExtractedFieldCandidate(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type=value_type,
            confidence=confidence,
            extraction_method=extraction_method,
            source_document_id=context.source_document_id,
            source_snapshot_id=context.snapshot_id,
            evidence_chunk_id=match.evidence_chunk_id,
            evidence_text_excerpt=match.evidence_text_excerpt,
            anchor_type=match.anchor_type,
            anchor_value=match.anchor_value,
            page_no=match.page_no,
            chunk_index=match.chunk_index,
            field_metadata={
                **field_metadata,
                "retrieval_mode": match.retrieval_mode,
                "matched_keywords": match.match_metadata.get("matched_keywords", []),
            },
        )
    return None


def _extract_candidate_value(
    *,
    context: ExtractionDocumentContext,
    field_name: str,
    excerpt: str,
    anchor_value: str | None,
) -> tuple[object | None, str, str, dict[str, object]]:
    text = excerpt.strip()
    lowered = text.lower()

    if field_name in {"monthly_fee", "public_display_fee", "minimum_balance", "minimum_deposit"}:
        money_value = _extract_money_value(context=context, field_name=field_name, text=text, lowered=lowered)
        return money_value, "decimal", "heuristic_money", {}

    if field_name in {"standard_rate", "public_display_rate", "promotional_rate"}:
        percent = _extract_percent_value(text)
        return percent, "decimal", "heuristic_percent", {}

    if field_name == "included_transactions":
        return _extract_included_transactions(text), "integer", "heuristic_transaction_count", {}

    if field_name in {"interest_payment_frequency", "compounding_frequency"}:
        return _detect_frequency(lowered), "string", "heuristic_frequency", {}

    if field_name == "interest_calculation_method":
        return _find_sentence(text, ("calculated", "daily closing balance", "calculation")), "string", "heuristic_sentence", {}

    if field_name == "term_length_text":
        return _extract_term_length_text(text), "string", "heuristic_term_text", {}

    if field_name == "term_length_days":
        return _extract_term_length_days(text), "integer", "heuristic_term_days", {}

    if field_name == "payout_option":
        return _extract_payout_option(lowered), "string", "heuristic_payout_option", {}

    if field_name in {
        "introductory_rate_flag",
        "tiered_rate_flag",
        "registered_flag",
        "redeemable_flag",
        "non_redeemable_flag",
        "registered_plan_supported",
        "unlimited_transactions_flag",
        "interac_e_transfer_included",
        "overdraft_available",
        "student_plan_flag",
        "newcomer_plan_flag",
    }:
        return _extract_boolean_flag(field_name=field_name, lowered=lowered, anchor_value=anchor_value), "boolean", "heuristic_flag", {}

    if field_name == "cheque_book_info":
        return _extract_cheque_book_info(text), "string", "heuristic_text", {}

    if field_name in {
        "fee_waiver_condition",
        "eligibility_text",
        "tier_definition_text",
        "withdrawal_limit_text",
        "notes",
        "promotional_period_text",
    }:
        if field_name == "fee_waiver_condition":
            waiver_condition = _extract_fee_waiver_condition(context=context, text=text)
            if waiver_condition:
                return waiver_condition, "string", "heuristic_fee_waiver", {}
            return None, "string", "heuristic_fee_waiver", {}
        text_value = _normalize_text(_find_sentence(text, ("eligible", "waive", "tier", "limit", "promo", "offer")) or text)
        return text_value[:280], "string", "heuristic_text", {}

    return _normalize_text(text)[:280], "string", "heuristic_text", {}


def _build_derived_field(
    *,
    context: ExtractionDocumentContext,
    field_name: str,
    candidate_value: object,
    value_type: str,
    extraction_method: str = "derived_context",
    confidence: float = 0.99,
) -> ExtractedFieldCandidate:
    return ExtractedFieldCandidate(
        field_name=field_name,
        candidate_value=candidate_value,
        value_type=value_type,
        confidence=confidence,
        extraction_method=extraction_method,
        source_document_id=context.source_document_id,
        source_snapshot_id=context.snapshot_id,
        evidence_chunk_id=None,
        evidence_text_excerpt=None,
        anchor_type=None,
        anchor_value=None,
        page_no=None,
        chunk_index=None,
        field_metadata={"derived_field": True},
    )


def _extract_document_title(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
) -> str | None:
    ranked_titles: list[tuple[float, int, int, str]] = []
    seen_titles: set[str] = set()

    for candidate in sorted(candidates, key=lambda item: (item.chunk_index, item.evidence_chunk_id)):
        lines = [line for line in candidate.evidence_excerpt.splitlines() if line.strip()]
        for line_index, line in enumerate(lines[:6]):
            normalized = _clean_title_candidate(line)
            if not normalized:
                continue
            lowered = normalized.lower()
            if lowered in seen_titles:
                continue
            seen_titles.add(lowered)
            score = _score_title_candidate(
                text=normalized,
                bank_code=context.bank_code,
                chunk_index=candidate.chunk_index,
                line_index=line_index,
            )
            ranked_titles.append((score, candidate.chunk_index, line_index, normalized))

        anchor_title = _anchor_value_to_title(candidate.anchor_value)
        if anchor_title:
            lowered_anchor = anchor_title.lower()
            if lowered_anchor not in seen_titles:
                seen_titles.add(lowered_anchor)
                score = _score_title_candidate(
                    text=anchor_title,
                    bank_code=context.bank_code,
                    chunk_index=candidate.chunk_index,
                    line_index=0,
                ) - 0.1
                ranked_titles.append((score, candidate.chunk_index, 0, anchor_title))

    if not ranked_titles:
        return None

    ranked_titles.sort(key=lambda item: (-item[0], item[1], item[2], len(item[3])))
    best_score, _, _, best_title = ranked_titles[0]
    if best_score <= 0:
        return None
    return best_title


def _score_title_candidate(*, text: str, bank_code: str, chunk_index: int, line_index: int) -> float:
    normalized = _normalize_text(text)
    lowered = normalized.lower()
    compacted = re.sub(r"[^a-z0-9]+", "", lowered)
    word_count = len(normalized.split())

    if len(normalized) < 4 or len(normalized) > 120:
        return -5.0

    score = 0.0
    if lowered in _GENERIC_TITLE_LINES or compacted in _GENERIC_TITLE_LINES:
        score -= 5.0
    if any(lowered.startswith(prefix) for prefix in _GENERIC_TITLE_PREFIXES):
        score -= 4.0
    if "?" in normalized:
        score -= 3.0
    if any(character in normalized for character in ".!,:;%$"):
        score -= 2.0
    if lowered.endswith(" features"):
        score -= 3.5
    if lowered.startswith("more great ") and lowered.endswith(" features"):
        score -= 2.0
    if word_count == 1:
        score -= 1.5
    elif 2 <= word_count <= 8:
        score += 1.0
    else:
        score -= min(2.0, (word_count - 8) * 0.35)

    has_product_keyword = any(keyword in lowered for keyword in _PRODUCT_TITLE_KEYWORDS)
    if has_product_keyword:
        score += 4.5
    else:
        score -= 3.5
    if bank_code.lower() in lowered:
        score += 0.6
    if normalized == normalized.upper() and len(normalized) > 8:
        score -= 1.5
    elif normalized[:1].isupper():
        score += 0.4

    score += max(0.0, 0.5 - (chunk_index * 0.08))
    score += max(0.0, 0.35 - (line_index * 0.12))
    return round(score, 4)


def _anchor_value_to_title(anchor_value: str | None) -> str | None:
    if anchor_value is None:
        return None
    normalized = _normalize_text(anchor_value.replace("-", " ").replace("_", " "))
    if not normalized or normalized.startswith("page "):
        return None
    return " ".join(part.capitalize() if part.islower() else part for part in normalized.split())


def _clean_title_candidate(value: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        return ""

    cleaned = normalized
    compacted = re.sub(r"[^a-z0-9]+", "", cleaned.lower())
    if compacted in _GENERIC_TITLE_LINES:
        return cleaned

    wrapper_patterns = (
        r"^benefits of (?:the )?(.+?)(?:\.)?$",
        r"^about (?:the )?(.+?)(?:\.)?$",
        r"^what (?:is|are) (?:the )?(.+?)(?:\?)?$",
        r"^explore the features of (?:the )?(.+)$",
        r"^full disclosure for (?:the )?(.+?)(?:\.)?$",
        r"^(.+?)\s+faqs$",
    )
    for pattern in wrapper_patterns:
        match = re.match(pattern, cleaned, flags=re.IGNORECASE)
        if match is None:
            continue
        candidate = _normalize_text(match.group(1))
        if candidate:
            return candidate
    return cleaned


def _extract_description(candidates: list[EvidenceChunkCandidate]) -> str | None:
    for candidate in sorted(candidates, key=lambda item: (item.chunk_index, item.evidence_chunk_id)):
        lines = [line.strip() for line in candidate.evidence_excerpt.splitlines() if line.strip()]
        if len(lines) >= 2:
            return _normalize_text(lines[1])[:240]
        normalized = _normalize_text(candidate.evidence_excerpt)
        if len(normalized) > 20:
            return normalized[:240]
    return None


def _infer_product_type(context: ExtractionDocumentContext) -> str:
    raw_value = str(context.source_metadata.get("product_type", "")).strip().lower()
    return raw_value or "deposit"


def _uses_dynamic_product_type(context: ExtractionDocumentContext) -> bool:
    product_type = _infer_product_type(context)
    if product_type in _CANONICAL_PRODUCT_TYPES:
        return False
    return bool(context.source_metadata.get("product_type_dynamic", True))


def _merge_extracted_fields(
    *,
    base_fields: list[ExtractedFieldCandidate],
    ai_fields: list[ExtractedFieldCandidate],
) -> list[ExtractedFieldCandidate]:
    ai_by_field = {field.field_name: field for field in ai_fields}
    merged: list[ExtractedFieldCandidate] = []
    for field in base_fields:
        if field.field_name in ai_by_field and field.evidence_chunk_id is not None:
            continue
        merged.append(ai_by_field.pop(field.field_name, field))
    merged.extend(ai_by_field.values())
    return _dedupe_fields(merged)


def _extract_dynamic_fields_with_ai(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: list[str],
) -> tuple[list[ExtractedFieldCandidate], list[str], dict[str, Any] | None]:
    if not llm_provider_configured():
        return [], ["Dynamic product extraction kept heuristic mode because the OpenAI provider or API key was not configured."], None

    candidate_map = {candidate.evidence_chunk_id: candidate for candidate in candidates}
    ai_requested_fields = [
        field_name
        for field_name in requested_fields
        if field_name
        not in {"product_family", "product_type", "bank_code", "country_code", "source_language", "currency"}
    ]
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "field_candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "field_name": {"type": "string"},
                        "candidate_value": {"type": "string"},
                        "value_type": {"type": "string", "enum": ["string", "decimal", "integer", "boolean"]},
                        "evidence_chunk_id": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["field_name", "candidate_value", "value_type", "evidence_chunk_id", "confidence"],
                },
            },
        },
        "required": ["summary", "field_candidates"],
    }
    try:
        response_payload, usage = invoke_openai_json_schema(
            model_id=configured_model_id(),
            instructions=(
                "You are the FPDS Extraction Agent for dynamic deposit product types. "
                "Read the product type definition and candidate evidence chunks, then extract only grounded field candidates. "
                "Do not invent values. Prefer exact values from one evidence chunk. "
                "If a field is not supported by the evidence, omit it."
            ),
            payload={
                "product_type": _infer_product_type(context),
                "product_type_name": context.source_metadata.get("product_type_name"),
                "product_type_description": context.source_metadata.get("product_type_description"),
                "expected_fields": list(context.source_metadata.get("expected_fields", [])),
                "requested_fields": ai_requested_fields,
                "candidate_chunks": [
                    {
                        "evidence_chunk_id": candidate.evidence_chunk_id,
                        "anchor_value": candidate.anchor_value,
                        "excerpt": candidate.evidence_excerpt[:1200],
                    }
                    for candidate in candidates[:12]
                ],
            },
            schema_name="dynamic_product_extraction",
            schema=schema,
        )
    except Exception as exc:
        return [], [f"Dynamic product extraction AI fallback was unavailable: {exc}"], None

    extracted_fields: list[ExtractedFieldCandidate] = []
    for item in response_payload.get("field_candidates", []):
        field_name = str(item.get("field_name") or "").strip()
        evidence_chunk_id = str(item.get("evidence_chunk_id") or "").strip()
        if field_name not in ai_requested_fields or evidence_chunk_id not in candidate_map:
            continue
        candidate = candidate_map[evidence_chunk_id]
        candidate_value = _coerce_ai_candidate_value(
            value=str(item.get("candidate_value") or ""),
            value_type=str(item.get("value_type") or "string"),
        )
        if candidate_value is None:
            continue
        extracted_fields.append(
            ExtractedFieldCandidate(
                field_name=field_name,
                candidate_value=candidate_value,
                value_type=str(item.get("value_type") or "string"),
                confidence=round(min(0.99, max(0.5, float(item.get("confidence") or 0.75))), 4),
                extraction_method="openai_dynamic_extractor",
                source_document_id=context.source_document_id,
                source_snapshot_id=context.snapshot_id,
                evidence_chunk_id=candidate.evidence_chunk_id,
                evidence_text_excerpt=candidate.evidence_excerpt,
                anchor_type=candidate.anchor_type,
                anchor_value=candidate.anchor_value,
                page_no=candidate.page_no,
                chunk_index=candidate.chunk_index,
                field_metadata={"dynamic_product_type": True},
            )
        )
    notes = []
    summary = str(response_payload.get("summary") or "").strip()
    if summary:
        notes.append(summary)
    if extracted_fields:
        notes.append(f"Dynamic product extraction AI supplemented {len(extracted_fields)} field candidate(s).")
    return extracted_fields, notes, usage


def _coerce_ai_candidate_value(*, value: str, value_type: str) -> object | None:
    normalized = value.strip()
    if not normalized:
        return None
    if value_type == "decimal":
        return _normalize_decimal(normalized.strip("%$ ").replace(",", ""))
    if value_type == "integer":
        try:
            return int(re.sub(r"[^0-9-]", "", normalized))
        except ValueError:
            return None
    if value_type == "boolean":
        lowered = normalized.lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
        return None
    return _normalize_text(normalized)[:280]


def _infer_currency(*, context: ExtractionDocumentContext) -> str:
    raw_currency = str(context.source_metadata.get("currency", "")).strip().upper()
    if raw_currency in {"CAD", "USD"}:
        return raw_currency

    context_text = " ".join(
        str(item or "")
        for item in (
            context.source_metadata.get("product_name"),
            context.source_metadata.get("source_name"),
            context.source_metadata.get("source_title"),
            context.source_metadata.get("url"),
            context.source_metadata.get("source_url"),
            context.source_id,
        )
    ).lower()
    if any(token in context_text for token in ("u.s. dollar", "us dollar", "usd", "us-prem-savings", "us premium savings", " us ")):
        return "USD"
    return "CAD"


def _extract_money_value(
    *,
    context: ExtractionDocumentContext,
    field_name: str,
    text: str,
    lowered: str,
) -> str | None:
    if field_name in {"monthly_fee", "public_display_fee"}:
        product_monthly_fee = _extract_bmo_chequing_product_monthly_fee(context=context, text=text)
        if product_monthly_fee is not None:
            return product_monthly_fee
        monthly_fee = _extract_monthly_fee_with_minimum_balance_waiver(text)
        if monthly_fee is not None:
            return monthly_fee
        if any(token in lowered for token in ("no monthly fee", "no monthly plan fee", "monthly fee: $0", "monthly fee\n$0")):
            return "0.00"
        if _matches_zero_money_label(
            text=text,
            label_patterns=(
                r"monthly\s+(?:plan\s+)?fee",
                r"plan\s+fee",
            ),
        ):
            return "0.00"
        return _extract_money_near_labels(
            text=text,
            label_patterns=(
                r"monthly\s+(?:plan\s+)?fee",
                r"plan\s+fee",
            ),
        )

    if field_name == "minimum_balance":
        waiver_balance = _extract_minimum_balance_for_fee_waiver(context=context, text=text)
        if waiver_balance is not None:
            return waiver_balance
        if _has_bmo_chequing_other_product_fee_waiver(context=context, text=text):
            return None
        if any(token in lowered for token in ("no minimum balance", "no minimum daily balance")):
            return "0.00"
        return _extract_money_near_labels(
            text=text,
            label_patterns=(
                r"minimum\s+daily\s+balance",
                r"minimum\s+balance",
            ),
        )

    if field_name == "minimum_deposit":
        if any(token in lowered for token in ("no minimum deposit", "no minimum opening deposit")):
            return "0.00"
        if _matches_zero_money_label(
            text=text,
            label_patterns=(
                r"minimum\s+opening\s+deposit",
                r"minimum\s+deposit",
                r"opening\s+deposit",
                r"initial\s+deposit",
            ),
        ):
            return "0.00"
        return _extract_money_near_labels(
            text=text,
            label_patterns=(
                r"minimum\s+opening\s+deposit",
                r"minimum\s+deposit",
                r"opening\s+deposit",
                r"initial\s+deposit",
            ),
        )

    return None


def _extract_monthly_fee_with_minimum_balance_waiver(text: str) -> str | None:
    match = _fee_waiver_pattern().search(text)
    if match is None:
        return None
    return _normalize_decimal(match.group("fee"))


def _extract_minimum_balance_for_fee_waiver(*, context: ExtractionDocumentContext, text: str) -> str | None:
    match = _fee_waiver_pattern().search(text)
    if match is None:
        return None
    if _is_bmo_chequing_other_product_fee_waiver(context=context, text=text, match=match):
        return None
    balance = match.group("balance_after_label") or match.group("balance_before_label")
    return _normalize_decimal(balance)


def _extract_fee_waiver_condition(*, context: ExtractionDocumentContext, text: str) -> str | None:
    match = _fee_waiver_pattern().search(text)
    if match is None:
        return None
    if _is_bmo_chequing_other_product_fee_waiver(context=context, text=text, match=match):
        return None
    fee = _normalize_decimal(match.group("fee"))
    balance = _normalize_decimal(match.group("balance_after_label") or match.group("balance_before_label"))
    return f"Monthly fee {fee} is waived to 0.00 with a {balance} minimum balance."


def _extract_bmo_chequing_product_monthly_fee(*, context: ExtractionDocumentContext, text: str) -> str | None:
    source_hint_by_id = {
        "BMO-CHQ-002": "practical",
        "BMO-CHQ-003": "plus",
        "BMO-CHQ-004": "performance",
        "BMO-CHQ-005": "premium",
        "BMO-CHQ-008": "air miles",
    }
    product_hint = source_hint_by_id.get(context.source_id)
    if product_hint is None:
        return None
    match = re.search(
        rf"\b{re.escape(product_hint)}\b[\s\S]{{0,80}}?\$\s?([0-9][0-9,]*(?:\.\d{{1,2}})?)\s*(?:per\s+month|/month|monthly)?",
        text,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    return _normalize_decimal(match.group(1))


def _is_bmo_chequing_other_product_fee_waiver(
    *,
    context: ExtractionDocumentContext,
    text: str,
    match: re.Match[str],
) -> bool:
    source_hint_by_id = {
        "BMO-CHQ-002": "practical",
        "BMO-CHQ-003": "plus",
        "BMO-CHQ-004": "performance",
        "BMO-CHQ-005": "premium",
        "BMO-CHQ-008": "air miles",
    }
    current_product_hint = source_hint_by_id.get(context.source_id)
    if current_product_hint is None:
        return False
    before_window = text[max(0, match.start() - 64) : match.start()].lower()
    other_product_hints = {item for item in source_hint_by_id.values() if item != current_product_hint}
    nearest_hint = None
    nearest_position = -1
    for hint in {current_product_hint, *other_product_hints}:
        position = before_window.rfind(hint)
        if position > nearest_position:
            nearest_hint = hint
            nearest_position = position
    if nearest_hint is None or nearest_hint == current_product_hint:
        return False
    return nearest_hint in other_product_hints


def _has_bmo_chequing_other_product_fee_waiver(*, context: ExtractionDocumentContext, text: str) -> bool:
    return any(
        _is_bmo_chequing_other_product_fee_waiver(context=context, text=text, match=match)
        for match in _fee_waiver_pattern().finditer(text)
    )


def _fee_waiver_pattern() -> re.Pattern[str]:
    return re.compile(
        r"\$\s?(?P<fee>[0-9][0-9,]*(?:\.\d{1,2})?)\s*"
        r"(?:(?:per\s+month|monthly)\s+)?or\s+\$0(?:\.00)?(?:\s*/\s*month|\s+per\s+month)?"
        r"\s+with\s+(?:a\s+)?(?:(?:min\.?|minimum)\s+(?:daily\s+)?\$\s?(?P<balance_after_label>[0-9][0-9,]*(?:\.\d{1,2})?)"
        r"(?:\s+balance)?|\$\s?(?P<balance_before_label>[0-9][0-9,]*(?:\.\d{1,2})?)\s+"
        r"(?:minimum\s+(?:daily\s+)?balance|balance))",
        flags=re.IGNORECASE,
    )


def _matches_zero_money_label(*, text: str, label_patterns: tuple[str, ...]) -> bool:
    for label_pattern in label_patterns:
        if re.search(
            rf"{label_pattern}[\s\S]{{0,32}}?(?:free|waived|included|no fee|\$0(?:\.00)?)",
            text,
            flags=re.IGNORECASE,
        ):
            return True
        if re.search(
            rf"(?:free|waived|included|no fee|\$0(?:\.00)?)[\s\S]{{0,48}}?{label_pattern}",
            text,
            flags=re.IGNORECASE,
        ):
            return True
    return False


def _extract_money_near_labels(*, text: str, label_patterns: tuple[str, ...]) -> str | None:
    for label_pattern in label_patterns:
        after_match = re.search(
            rf"{label_pattern}[\s\S]{{0,80}}?\$\s?([0-9][0-9,]*(?:\.\d{{1,2}})?)",
            text,
            flags=re.IGNORECASE,
        )
        if after_match is not None:
            return _normalize_decimal(after_match.group(1))

        before_match = re.search(
            rf"\$\s?([0-9][0-9,]*(?:\.\d{{1,2}})?)[\s\S]{{0,60}}?{label_pattern}",
            text,
            flags=re.IGNORECASE,
        )
        if before_match is not None:
            return _normalize_decimal(before_match.group(1))
    return None


def _extract_cheque_book_info(text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    patterns = (
        r"no fee for select cheques?",
        r"select cheques?.{0,36}?no fee",
        r"(?:one|first).{0,36}?cheque book",
        r"cheque book.{0,48}?(?:free|included|no fee)",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match is None:
            continue
        phrase = _normalize_text(match.group(0).strip(" -;,."))
        if phrase:
            return f"{phrase}."
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        if any(keyword in raw_sentence.lower() for keyword in ("cheque book", "select cheque", "select cheques")):
            return _normalize_text(raw_sentence)[:160]
    return None


def _extract_percent_value(text: str) -> str | None:
    match = _PERCENT_RE.search(text)
    if match is None:
        return None
    return _normalize_decimal(match.group(1))


def _extract_boolean_flag(*, field_name: str, lowered: str, anchor_value: str | None) -> bool | None:
    anchor = (anchor_value or "").lower()
    if field_name == "introductory_rate_flag":
        if any(token in lowered for token in ("promo", "promotional", "bonus", "introductory")):
            return True
        return None
    if field_name == "tiered_rate_flag":
        if "tier" in lowered or "tier" in anchor:
            return True
        return None
    if field_name == "registered_flag":
        if any(token in lowered for token in ("tfsa", "rrsp", "registered")):
            return True
        return None
    if field_name == "redeemable_flag":
        if any(token in lowered for token in ("non-redeemable", "non redeemable", "non cashable", "non-cashable")):
            return False
        if any(token in lowered for token in ("redeemable", "cashable", "early redemption")):
            return True
        return None
    if field_name == "non_redeemable_flag":
        if any(token in lowered for token in ("non-redeemable", "non redeemable", "non cashable", "non-cashable")):
            return True
        if "redeemable" in lowered or "cashable" in lowered:
            return False
        return None
    if field_name == "registered_plan_supported":
        if any(token in lowered for token in ("tfsa", "rrsp", "rrif", "resp", "registered plan", "registered account")):
            return True
        return None
    if field_name == "unlimited_transactions_flag":
        if "unlimited" in lowered and any(token in lowered for token in ("transaction", "debit", "banking")):
            return True
        return None
    if field_name == "interac_e_transfer_included":
        if any(token in lowered for token in ("interac e-transfer", "interac e transfer", "e-transfer", "etransfer")) and any(
            token in lowered for token in ("included", "free", "unlimited", "no fee", "waived", "enjoy", "per month")
        ):
            return True
        return None
    if field_name == "overdraft_available":
        if "overdraft" in lowered or "overdraft" in anchor:
            return True
        return None
    if field_name == "student_plan_flag":
        if _has_student_plan_context(lowered=lowered, anchor=anchor):
            return True
        return None
    if field_name == "newcomer_plan_flag":
        if _has_newcomer_plan_context(lowered=lowered, anchor=anchor):
            return True
        return None
    return None


def _has_student_plan_context(*, lowered: str, anchor: str) -> bool:
    if any(token in anchor for token in ("student", "youth")):
        return True
    return any(
        re.search(pattern, lowered)
        for pattern in (
            r"\bstudent(?:\s+\w+){0,2}\s+(?:chequing|checking|account|package|plan)\b",
            r"\byouth(?:\s+\w+){0,2}\s+(?:chequing|checking|account|package|plan)\b",
            r"\b(?:for|designed for|available to)\s+[^.]{0,60}\bstudents?\b",
        )
    )


def _has_newcomer_plan_context(*, lowered: str, anchor: str) -> bool:
    if any(token in anchor for token in ("newcomer", "new-to-canada")):
        return True
    return any(
        re.search(pattern, lowered)
        for pattern in (
            r"\bnewcomer(?:\s+\w+){0,2}\s+(?:chequing|checking|account|package|plan)\b",
            r"\bnew to canada\s+[^.]{0,80}\b(?:banking|chequing|checking|account|package|plan)\b",
            r"\b(?:for|designed for|available to)\s+[^.]{0,80}\bnewcomers?\b",
        )
    )


def _detect_frequency(lowered: str) -> str | None:
    if "paid monthly" in lowered or "monthly" in lowered:
        return "monthly"
    if "paid quarterly" in lowered or "quarterly" in lowered:
        return "quarterly"
    if "paid weekly" in lowered or "weekly" in lowered:
        return "weekly"
    if "paid annually" in lowered or "annually" in lowered or "yearly" in lowered:
        return "annually"
    if "semi-annually" in lowered:
        return "semi-annually"
    if "daily" in lowered:
        return "daily"
    return None


def _extract_term_length_text(text: str) -> str | None:
    match = _extract_term_match(text)
    if match is None:
        return None
    start_value, start_unit, end_value, end_unit = match.groups()
    normalized_start = f"{start_value} {_normalize_term_unit(start_unit)}"
    if end_value and end_unit:
        return f"{normalized_start} to {end_value} {_normalize_term_unit(end_unit)}"
    return normalized_start


def _extract_term_length_days(text: str) -> int | None:
    match = _extract_term_match(text)
    if match is None:
        return None
    start_value, start_unit, end_value, end_unit = match.groups()
    if end_value or end_unit:
        return None
    return _convert_term_to_days(start_value, start_unit)


def _extract_term_match(text: str) -> re.Match[str] | None:
    lowered = text.lower()
    for match in _TERM_RE.finditer(text):
        window_start = max(0, match.start() - 64)
        window_end = min(len(text), match.end() + 64)
        window = lowered[window_start:window_end]
        if any(token in window for token in _TERM_CONTEXT_BLOCKLIST):
            continue
        if any(token in window for token in _TERM_CONTEXT_KEYWORDS):
            return match
    return None


def _extract_payout_option(lowered: str) -> str | None:
    if "at maturity" in lowered:
        return "at_maturity"
    if "paid monthly" in lowered or "monthly interest" in lowered:
        return "monthly"
    if "paid quarterly" in lowered or "quarterly interest" in lowered:
        return "quarterly"
    if "semi-annually" in lowered or "paid semi-annually" in lowered:
        return "semi-annually"
    if "paid annually" in lowered or "annual interest" in lowered or "interest paid annually" in lowered:
        return "annually"
    return None


def _find_sentence(text: str, keywords: tuple[str, ...]) -> str | None:
    normalized = _normalize_text(text)
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        lowered = raw_sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            return raw_sentence
    return normalized if normalized else None


def _extract_included_transactions(text: str) -> int | None:
    lowered = text.lower()
    if "unlimited" in lowered and any(token in lowered for token in ("transaction", "debit", "banking")):
        return None
    patterns = (
        r"(?:includes?|included)\s+(\d{1,3})\s+(?:free\s+)?(?:transactions?|debits?|withdrawals?)",
        r"(\d{1,3})\s+(?:free\s+)?(?:transactions?|debits?|withdrawals?)\s+(?:included|per month|a month)",
        r"(\d{1,3})\s+(?:transactions?|debits?)\s+included",
        r"up\s+to\s+(\d{1,3})\s+[\w\s-]{0,80}?(?:transactions?|debits?|withdrawals?)",
    )
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match is None:
            continue
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def _normalize_term_unit(unit: str) -> str:
    normalized = unit.lower()
    if normalized.startswith("day"):
        return "day" if normalized == "day" else "days"
    if normalized.startswith("month"):
        return "month" if normalized == "month" else "months"
    if normalized.startswith("year"):
        return "year" if normalized == "year" else "years"
    return normalized


def _convert_term_to_days(value: str, unit: str) -> int | None:
    try:
        integer_value = int(value)
    except ValueError:
        return None
    normalized = unit.lower()
    if normalized.startswith("day"):
        return integer_value
    if normalized.startswith("month"):
        return integer_value * 30
    if normalized.startswith("year"):
        return integer_value * 365
    return None


def _normalize_text(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()


def _normalize_decimal(value: str) -> str:
    try:
        decimal_value = Decimal(value.replace(",", ""))
    except InvalidOperation:
        return value.replace(",", "")
    return f"{decimal_value:.2f}"


def _dedupe_fields(fields: list[ExtractedFieldCandidate]) -> list[ExtractedFieldCandidate]:
    seen: set[str] = set()
    ordered: list[ExtractedFieldCandidate] = []
    for field in fields:
        if field.field_name in seen:
            continue
        seen.add(field.field_name)
        ordered.append(field)
    return ordered


def _build_extracted_artifact_payload(
    *,
    context: ExtractionDocumentContext,
    run_id: str,
    correlation_id: str | None,
    request_id: str | None,
    field_names: list[str],
    retrieval_result: dict[str, object],
    extracted_fields: list[ExtractedFieldCandidate],
    evidence_links: list[EvidenceLinkDraft],
    model_execution_id: str,
    agent_name: str,
    model_id: str,
    started_at: str,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "correlation_id": correlation_id,
        "request_id": request_id,
        "source_id": context.source_id,
        "source_document_id": context.source_document_id,
        "snapshot_id": context.snapshot_id,
        "parsed_document_id": context.parsed_document_id,
        "model_execution_id": model_execution_id,
        "agent_name": agent_name,
        "model_id": model_id,
        "started_at": started_at,
        "schema_context": {
            "product_family": "deposit",
            "product_type": _infer_product_type(context),
            "source_language": context.source_language,
            "expected_fields": context.source_metadata.get("expected_fields", []),
            "product_type_name": context.source_metadata.get("product_type_name"),
            "product_type_description": context.source_metadata.get("product_type_description"),
            "product_type_dynamic": context.source_metadata.get("product_type_dynamic"),
        },
        "requested_fields": field_names,
        "retrieval_result": retrieval_result,
        "extracted_fields": [field.to_dict() for field in extracted_fields],
        "evidence_links": [link.to_dict() for link in evidence_links],
    }


def _build_metadata_payload(
    *,
    context: ExtractionDocumentContext,
    model_execution_id: str,
    extracted_storage_key: str,
    metadata_storage_key: str,
    extracted_fields: list[ExtractedFieldCandidate],
    evidence_links: list[EvidenceLinkDraft],
    runtime_notes: list[str],
) -> dict[str, object]:
    return {
        "source_id": context.source_id,
        "source_document_id": context.source_document_id,
        "snapshot_id": context.snapshot_id,
        "parsed_document_id": context.parsed_document_id,
        "model_execution_id": model_execution_id,
        "extracted_storage_key": extracted_storage_key,
        "metadata_storage_key": metadata_storage_key,
        "extracted_field_count": len(extracted_fields),
        "evidence_link_count": len(evidence_links),
        "runtime_notes": runtime_notes,
    }


def _build_model_execution_record(
    *,
    model_execution_id: str,
    run_id: str,
    source_document_id: str,
    execution_status: str,
    agent_name: str,
    model_id: str,
    started_at: str,
    completed_at: str,
    execution_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "model_execution_id": model_execution_id,
        "run_id": run_id,
        "source_document_id": source_document_id,
        "stage_name": "extraction",
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
    context: ExtractionDocumentContext,
    stage_status: str,
    warning_count: int,
    error_count: int,
    error_summary: str | None,
    stage_metadata: dict[str, object],
) -> dict[str, object]:
    digest = sha256(f"{run_id}|{context.source_document_id}".encode("utf-8")).hexdigest()[:16]
    return {
        "run_source_item_id": f"rsi-{digest}",
        "run_id": run_id,
        "source_document_id": context.source_document_id,
        "selected_snapshot_id": context.snapshot_id,
        "stage_status": stage_status,
        "warning_count": warning_count,
        "error_count": error_count,
        "error_summary": error_summary,
        "stage_metadata": stage_metadata,
    }


def _build_model_execution_id(run_id: str, source_document_id: str, parsed_document_id: str) -> str:
    digest = sha256(f"{run_id}|{source_document_id}|{parsed_document_id}|extraction".encode("utf-8")).hexdigest()[:16]
    return f"modelexec-{digest}"


def _build_usage_id(model_execution_id: str) -> str:
    digest = sha256(f"{model_execution_id}|llm_usage".encode("utf-8")).hexdigest()[:16]
    return f"usage-{digest}"


def _stringify_candidate_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
