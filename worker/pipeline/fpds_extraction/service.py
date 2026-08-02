from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from worker.pipeline.fpds_ai_runtime import (
    configured_model_id,
    estimated_cost_usd,
    invoke_openai_json_schema,
    llm_provider_configured,
)
from worker.country_defaults import default_currency_for_country
from worker.pipeline.fpds_field_contract import canonical_value_type, field_contract, field_contract_payload
from worker.pipeline.fpds_evidence_retrieval.models import (
    EvidenceChunkCandidate,
    EvidenceMatch,
    EvidenceRetrievalRequest,
    MetadataFilters,
)
from worker.pipeline.fpds_evidence_retrieval.service import EvidenceRetrievalService
from worker.pipeline.fpds_rate_safety import (
    bounded_rate_evidence_context,
    canonical_deposit_rate_suppression_reason,
)

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
    "base_12_month_rate",
    "public_display_rate",
    "promotional_rate",
    "promotional_period_text",
    "introductory_rate_flag",
    "eligibility_text",
    "application_method",
    "post_maturity_interest_rate",
    "tax_benefits",
    "deposit_insurance",
    "term_rate_table",
    "interest_rate_summary",
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
    "transaction_fee",
    "additional_transaction_fee",
    "unlimited_transactions_flag",
    "interac_e_transfer_included",
    "overdraft_available",
    "cheque_book_info",
    "student_plan_flag",
    "newcomer_plan_flag",
    "notes",
)
_AI_SAFE_RATE_FIELDS = {
    "standard_rate",
    "base_12_month_rate",
    "promotional_rate",
    "public_display_rate",
    "highest_rate",
}
_AI_SAFE_MONTHLY_FEE_FIELDS = {"monthly_fee", "public_display_fee"}
_COMMON_DEFAULT_FIELDS = {
    "product_name",
    "description_short",
    "monthly_fee",
    "public_display_fee",
    "fee_waiver_condition",
    "minimum_balance",
    "minimum_deposit",
    "eligibility_text",
    "application_method",
    "tax_benefits",
    "deposit_insurance",
    "notes",
}
_PRODUCT_TYPE_DEFAULT_FIELDS = {
    "savings": _COMMON_DEFAULT_FIELDS
    | {
        "standard_rate",
        "base_12_month_rate",
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
        "term_rate_table",
        "included_transactions",
        "unlimited_transactions_flag",
        "transaction_fee",
        "additional_transaction_fee",
        "interac_e_transfer_included",
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
        "base_12_month_rate",
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
        "post_maturity_interest_rate",
        "term_rate_table",
        "interest_rate_summary",
    },
}
_PERCENT_RE = re.compile(r"(?<!\d)(\d{1,2}(?:\.\d{1,4})?)\s*%")
_MONEY_RE = re.compile(r"[$€£]\s?([0-9][0-9,]*(?:\.\d{1,2})?)")
_TERM_RE = re.compile(
    r"(?<![\d.])(\d{1,3}(?:\.\d{1,2})?)\s*(?:-|\s)?\s*(day|days|month|months|year|years)\b"
    r"(?:\s*(?:to|-)\s*(\d{1,3}(?:\.\d{1,2})?)\s*(?:-|\s)?\s*(day|days|month|months|year|years)\b)?",
    re.IGNORECASE,
)
_TERM_RATE_ROW_RE = re.compile(
    r"(?P<term>\d{1,3}(?:\.\d{1,2})?\s*(?:days|months|years|day|month|year))\b"
    r"(?P<body>[^%\n\r]{0,120}?)"
    r"(?P<rate>(?<![\d.,])\d{1,2}(?:\.\d{1,4})?)\s*%",
    re.IGNORECASE,
)
_RATE_TERM_ROW_RE = re.compile(
    r"(?P<rate>(?<![\d.,])\d{1,2}(?:\.\d{1,4})?)\s*%"
    r"(?P<body>[^%\n\r]{0,120}?)"
    r"(?P<term>\d{1,3}(?:\.\d{1,2})?\s*(?:days|months|years|day|month|year))\b",
    re.IGNORECASE,
)
_TERM_RATE_APY_ROW_RE = re.compile(
    r"(?P<term>\d{1,3}(?:\.\d{1,2})?\s*(?:days|months|years|day|month|year))\b"
    r"(?P<body_before_rate>[^%\n\r]{0,100}?)"
    r"(?P<rate>(?<![\d.,])\d{1,2}(?:\.\d{1,4})?)\s*%"
    r"(?P<body_before_apy>[^%\n\r]{0,40}?)"
    r"(?P<apy>(?<![\d.,])\d{1,2}(?:\.\d{1,4})?)\s*%",
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
_BMO_CHEQUING_SOURCE_HINTS = {
    "BMO-CHQ-002": "practical",
    "BMO-CHQ-003": "plus",
    "BMO-CHQ-004": "performance",
    "BMO-CHQ-005": "premium",
    "BMO-CHQ-008": "air miles",
}
_BMO_SAVINGS_PRODUCT_TERMS = {
    "BMO-SAV-002": ("savings amplifier account", "savings amplifier"),
    "BMO-SAV-003": ("savings builder account", "savings builder"),
    "BMO-SAV-004": ("premium rate savings account", "premium rate savings"),
    "BMO-SAV-005": (
        "u.s. dollar premium rate savings account",
        "u.s. dollar premium rate savings",
        "u.s dollar premium rate savings account",
        "u.s dollar premium rate savings",
    ),
}
_BMO_SAVINGS_SOURCE_TITLES = {
    "BMO-SAV-002": "Savings Amplifier Account",
    "BMO-SAV-003": "Savings Builder Account",
    "BMO-SAV-004": "Premium Rate Savings Account",
    "BMO-SAV-005": "U.S. Dollar Premium Rate Savings Account",
}
_CIBC_SAVINGS_SOURCE_TITLES = {
    "CIBC-SAV-002": "CIBC eAdvantage Savings Account",
    "CIBC-SAV-003": "CIBC US$ Personal Account",
}
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
    "include in any bank plan",
    "add to any bank plan",
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
    "include ",
    "add to ",
)
_SUPPORTING_EXTRACTABLE_FIELDS = {
    "interest_rate_summary",
    "savings_account_rates",
    "rate_tiers",
    "base_12_month_rate",
    "term_rate_table",
    "post_maturity_interest_rate",
}
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
_NAVIGATION_NOISE_MARKERS = (
    "all chequing accounts",
    "all savings accounts",
    "credit cards overview",
    "mortgages overview",
    "loans overview",
    "banking fees and agreements",
    "book an appointment",
)
_GENERIC_BANKING_INFO_MARKERS = (
    "important banking info",
    "report a lost or stolen card",
    "banking services",
    "banking agreements",
    "cross border banking",
)
_NON_PRODUCT_DOCUMENT_TITLE_MARKERS = (
    "account agreement",
    "banking agreement",
    "disclosure statement",
    "fee schedule",
    "online banking service agreement",
    "privacy policy",
    "service agreement",
    "terms and conditions",
)
_NON_PRODUCT_DOCUMENT_TITLE_PATTERNS = (
    re.compile(
        r"\b(?:account|banking|cardholder|credit card|deposit|electronic banking|online banking|"
        r"service|user)\s+agreements?\b",
        flags=re.IGNORECASE,
    ),
    re.compile(r"\bagreements?\s+(?:and|&)\s+disclosures?\b", flags=re.IGNORECASE),
    re.compile(
        r"\b(?:account|banking|cardholder|credit card|deposit|fee|product|rate)\s+disclosures?\b",
        flags=re.IGNORECASE,
    ),
    re.compile(r"\b(?:fee|rate)\s+schedules?\b", flags=re.IGNORECASE),
    re.compile(r"\b(?:cookie|privacy)\s+(?:notices?|polic(?:y|ies))\b", flags=re.IGNORECASE),
    re.compile(r"\b(?:legal notices?|terms of (?:service|use))\b", flags=re.IGNORECASE),
)
_NON_PRODUCT_ACTION_TITLE_PATTERNS = (
    re.compile(
        r"^(?:apply(?:\s+now)?|calculate|compare|contact|enroll(?:\s+now)?|find|"
        r"get started|learn more|log in|schedule|sign in|try)\b",
        flags=re.IGNORECASE,
    ),
    re.compile(r"\b(?:calculator|made simple)\b", flags=re.IGNORECASE),
    re.compile(r"^(?:account|banking|card|loan|mortgage)\s+options?\b", flags=re.IGNORECASE),
)
_PRODUCT_PROFILE_CONFLICT_KEYWORDS = {
    "gic": (
        "chequing",
        "checking",
        "savings account",
        "savings accounts",
        "credit card",
        "credit cards",
        "mortgage",
        "mortgages",
        "loan",
        "loans",
        "mutual fund",
        "mutual funds",
        "account conversion",
    ),
    "savings": (
        "chequing",
        "checking",
        "credit card",
        "credit cards",
        "mortgage",
        "mortgages",
        "gic",
        "term deposit",
        "mutual fund",
        "mutual funds",
        "stock trading",
        "online trading",
        "investor's edge",
        "portfolio",
    ),
    "chequing": (
        "savings account",
        "savings accounts",
        "credit card",
        "credit cards",
        "mortgage",
        "mortgages",
        "gic",
        "term deposit",
        "mutual fund",
        "mutual funds",
        "stock trading",
        "online trading",
        "investor's edge",
        "portfolio",
    ),
}


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

            ai_usage: dict[str, Any] | None = None
            if _uses_official_ai_grounding(context) and llm_provider_configured():
                ai_fields, ai_notes, ai_usage = _extract_official_fields_with_ai(
                    context=context,
                    candidates=extraction_input.candidates,
                    requested_fields=field_names,
                    collected_fields=extracted_fields,
                )
                runtime_notes.extend(ai_notes)
                if ai_fields:
                    extracted_fields = _merge_extracted_fields(base_fields=extracted_fields, ai_fields=ai_fields)
                if ai_usage:
                    agent_name = "fpds-official-product-grounding-agent"
                    model_id = str(ai_usage["model_id"])
                    prompt_tokens = int(ai_usage.get("prompt_tokens") or 0)
                    completion_tokens = int(ai_usage.get("completion_tokens") or 0)
                    provider_request_id = ai_usage.get("provider_request_id")
                    usage_metadata = {
                        "usage_mode": "openai-official-product-grounding",
                        "provider": "openai",
                        "model_id": model_id,
                        "require_web_search": True,
                        "official_domain_allowlist": _official_domain_allowlist(context),
                        "official_web_sources": list(ai_usage.get("web_search_sources") or []),
                    }
            elif _uses_dynamic_product_type(context):
                runtime_notes.append(
                    "Dynamic product extraction kept heuristic mode because the OpenAI provider or API key was not configured."
                )
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
                    "official_grounding_contract_version": (
                        "collection-official-grounding-v1" if ai_usage else None
                    ),
                    "official_domain_allowlist": (
                        _official_domain_allowlist(context) if ai_usage else []
                    ),
                    "official_web_sources": (
                        list(ai_usage.get("web_search_sources") or []) if ai_usage else []
                    ),
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
    product_type_family = _canonical_product_type_family(product_type)
    product_default_fields = _PRODUCT_TYPE_DEFAULT_FIELDS.get(product_type) or _PRODUCT_TYPE_DEFAULT_FIELDS.get(product_type_family or "")
    fields: list[str] = []
    for field_name in default_fields:
        if product_default_fields is not None and field_name not in product_default_fields:
            continue
        if field_name not in fields:
            fields.append(field_name)
    for field_name in context.source_metadata.get("expected_fields", []):
        normalized = str(field_name).strip()
        registered_contract = field_contract(normalized)
        if (
            product_type in _CANONICAL_PRODUCT_TYPES
            and normalized not in default_fields
            and normalized not in _SUPPORTING_EXTRACTABLE_FIELDS
            and registered_contract is None
        ):
            continue
        if (
            product_type in _CANONICAL_PRODUCT_TYPES
            and product_default_fields is not None
            and normalized not in product_default_fields
            and normalized not in _SUPPORTING_EXTRACTABLE_FIELDS
            and registered_contract is None
        ):
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
    product_family = _infer_product_family(context)
    extracted: list[ExtractedFieldCandidate] = [
        _build_derived_field(context=context, field_name="product_family", candidate_value=product_family, value_type="string"),
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
        description = _extract_description(context=context, candidates=candidates)
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

    extracted_product_name = next(
        (
            str(field.candidate_value)
            for field in extracted
            if field.field_name == "product_name" and str(field.candidate_value).strip()
        ),
        None,
    )
    scoped_context = context
    if extracted_product_name is not None:
        scoped_context = replace(
            context,
            source_metadata={**context.source_metadata, "product_name": extracted_product_name},
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
            context=scoped_context,
            field_name=field_name,
            matches=matches_by_field.get(field_name, []),
            candidate_map=candidate_map,
        )
        if extracted_field is not None:
            extracted.append(extracted_field)

    _append_monthly_fee_fallback(
        context=scoped_context,
        candidates=candidates,
        requested_fields=requested_fields,
        extracted_fields=extracted,
    )
    _append_fee_waiver_fallback(
        context=scoped_context,
        candidates=candidates,
        requested_fields=requested_fields,
        extracted_fields=extracted,
    )
    _append_included_transactions_fallback(
        context=scoped_context,
        candidates=candidates,
        requested_fields=requested_fields,
        extracted_fields=extracted,
    )
    _append_unlimited_transactions_fallback(
        context=scoped_context,
        candidates=candidates,
        requested_fields=requested_fields,
        extracted_fields=extracted,
    )
    _append_minimum_deposit_fallback(
        context=scoped_context,
        candidates=candidates,
        requested_fields=requested_fields,
        extracted_fields=extracted,
    )
    _append_labeled_numeric_extension_fallback(
        context=scoped_context,
        candidates=candidates,
        requested_fields=requested_fields,
        extracted_fields=extracted,
    )
    _append_rate_fallback_fields(
        context=scoped_context,
        candidates=candidates,
        requested_fields=requested_fields,
        extracted_fields=extracted,
    )
    _append_promotional_period_fallback(
        context=scoped_context,
        candidates=candidates,
        requested_fields=requested_fields,
        extracted_fields=extracted,
    )
    return _dedupe_fields(extracted)


def _extract_from_matches(
    *,
    context: ExtractionDocumentContext,
    field_name: str,
    matches: list[EvidenceMatch],
    candidate_map: dict[str, EvidenceChunkCandidate],
) -> ExtractedFieldCandidate | None:
    extracted_options: list[tuple[int, int, float, ExtractedFieldCandidate]] = []
    for match in matches:
        if match.evidence_chunk_id not in candidate_map:
            continue
        if _mentions_named_other_product_without_target(
            context=context,
            excerpt=match.evidence_text_excerpt,
        ):
            continue
        scoped_excerpt, identity_score = _scope_excerpt_to_product_identity(
            context=context,
            excerpt=match.evidence_text_excerpt,
        )
        candidate_value, value_type, extraction_method, field_metadata = _extract_candidate_value(
            context=context,
            field_name=field_name,
            excerpt=scoped_excerpt,
            anchor_value=match.anchor_value,
        )
        if candidate_value is None:
            continue
        if not _ai_candidate_value_is_contract_safe(
            field_name=field_name,
            value=candidate_value,
        ):
            continue
        confidence = round(min(0.99, max(0.55, match.score)), 4)
        extracted_field = ExtractedFieldCandidate(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type=value_type,
            confidence=confidence,
            extraction_method=extraction_method,
            source_document_id=context.source_document_id,
            source_snapshot_id=context.snapshot_id,
            evidence_chunk_id=match.evidence_chunk_id,
            evidence_text_excerpt=scoped_excerpt,
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
        if field_name == "term_rate_table" and isinstance(candidate_value, list):
            extracted_options.append((identity_score, len(candidate_value), match.score, extracted_field))
            continue
        semantic_score = _field_evidence_semantic_score(
            field_name=field_name,
            candidate_value=candidate_value,
            excerpt=scoped_excerpt,
        )
        extracted_options.append((identity_score, semantic_score, match.score, extracted_field))
    if extracted_options:
        if field_name == "term_rate_table":
            identity_backed = [item for item in extracted_options if item[0] > 0]
            ranked_options = identity_backed or extracted_options
            ranked_options.sort(key=lambda item: (item[1], item[0], item[2]), reverse=True)
            return ranked_options[0][3]
        extracted_options.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        return extracted_options[0][3]
    return None


_NAMED_BANK_PRODUCT_RE = re.compile(
    r"\b(?:RBC|Royal\s+Bank|BMO|Bank\s+of\s+Montreal|CIBC|TD|Toronto[- ]Dominion|"
    r"Scotiabank|Scotia|Simplii|Tangerine|Oaken)\b"
    r"[\s\S]{0,120}?\b(?:accounts?|banking|GICs?|Mastercard|Visa|credit\s+cards?|"
    r"mortgages?|lines?\s+of\s+credit|personal\s+loans?)\b",
    re.IGNORECASE,
)


def _mentions_named_other_product_without_target(
    *, context: ExtractionDocumentContext, excerpt: str
) -> bool:
    """Reject a field excerpt explicitly naming another bank product.

    Detail pages frequently embed comparison cards and legal footnotes for
    adjacent products. An unnamed fee/rate row can still belong to the target,
    but a row that names a bank product is safe only when the target identity
    also appears in the same evidence excerpt.
    """

    normalized_excerpt = _normalize_text(excerpt).lower()
    target_terms = _source_product_identity_terms(context)
    if any(term in normalized_excerpt for term in target_terms):
        return False
    for match in _NAMED_BANK_PRODUCT_RE.finditer(excerpt):
        named_value = _normalize_text(match.group(0)).lower().strip(" .,:;|/")
        generic_value = re.sub(
            r"\b(?:rbc|royal bank|bmo|bank of montreal|cibc|td|toronto[- ]dominion|"
            r"scotiabank|scotia|simplii|tangerine|oaken|personal|retail|eligible|banking|"
            r"bank|accounts?|chequing|checking|savings?|gics?|guaranteed investment certificates?|"
            r"term deposits?|mastercard|visa|credit cards?|mortgages?|lines? of credit|personal loans?)\b",
            " ",
            named_value,
        )
        # A brand followed only by a generic product category (for example
        # `Scotiabank chequing accounts`) is not a named sibling product. Such
        # category copy commonly appears inside a target product's own
        # balance-waiver disclosure and must not veto its labelled fee row.
        if not re.sub(r"[^a-z0-9]+", "", generic_value):
            continue
        return True
    return False


def _append_included_transactions_fallback(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: set[str],
    extracted_fields: list[ExtractedFieldCandidate],
) -> None:
    """Recover an explicit monthly/debit count when retrieval missed its chunk."""

    if "included_transactions" not in requested_fields:
        return
    existing_transactions = next(
        (item for item in extracted_fields if item.field_name == "included_transactions"),
        None,
    )
    if existing_transactions is not None:
        grounded_value = _extract_included_transactions(existing_transactions.evidence_text_excerpt or "")
        try:
            existing_value = int(str(existing_transactions.candidate_value))
        except (TypeError, ValueError):
            existing_value = None
        if grounded_value == existing_value:
            return
        # A model/regex can accidentally read a fee decimal tail or an HTML
        # footnote as the transaction count.  Discard it so the evidence-wide
        # fallback can recover the explicitly labelled monthly count.
        extracted_fields.remove(existing_transactions)
    ranked: list[tuple[int, int, int, EvidenceChunkCandidate, str, int]] = []
    for candidate in candidates:
        if _mentions_named_other_product_without_target(
            context=context,
            excerpt=candidate.evidence_excerpt,
        ):
            continue
        scoped_excerpt, identity_score = _scope_excerpt_to_product_identity(
            context=context,
            excerpt=candidate.evidence_excerpt,
        )
        value = _extract_included_transactions(scoped_excerpt)
        if value is None:
            continue
        lowered = _normalize_text(scoped_excerpt).lower()
        semantic_score = 0
        if re.search(rf"\b{value}\s+(?:included\s+)?(?:debit\s+)?transactions?\b", lowered):
            semantic_score += 5
        if any(marker in lowered for marker in ("each month", "per month", "a month", "included debit")):
            semantic_score += 4
        ranked.append(
            (
                identity_score,
                semantic_score,
                -candidate.chunk_index,
                candidate,
                scoped_excerpt,
                value,
            )
        )
    if not ranked:
        return
    ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    _, _, _, match, excerpt, value = ranked[0]
    extracted_fields.append(
        ExtractedFieldCandidate(
            field_name="included_transactions",
            candidate_value=value,
            value_type="integer",
            confidence=0.78,
            extraction_method="heuristic_transaction_count_fallback",
            source_document_id=context.source_document_id,
            source_snapshot_id=context.snapshot_id,
            evidence_chunk_id=match.evidence_chunk_id,
            evidence_text_excerpt=excerpt,
            anchor_type=match.anchor_type,
            anchor_value=match.anchor_value,
            page_no=match.page_no,
            chunk_index=match.chunk_index,
            field_metadata={"transaction_count_fallback": True},
        )
    )


def _append_unlimited_transactions_fallback(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: set[str],
    extracted_fields: list[ExtractedFieldCandidate],
) -> None:
    """Recover an explicit account-wide unlimited statement missed by retrieval."""

    if "unlimited_transactions_flag" not in requested_fields or any(
        item.field_name == "unlimited_transactions_flag" for item in extracted_fields
    ):
        return
    ranked: list[tuple[int, int, int, EvidenceChunkCandidate, str]] = []
    for candidate in candidates:
        if _mentions_named_other_product_without_target(context=context, excerpt=candidate.evidence_excerpt):
            continue
        scoped_excerpt, identity_score = _scope_excerpt_to_product_identity(
            context=context,
            excerpt=candidate.evidence_excerpt,
        )
        lowered = _normalize_text(scoped_excerpt).lower()
        if not _has_account_wide_unlimited_transactions(lowered):
            continue
        semantic_score = 4
        if re.search(r"\bunlimited\s+(?:everyday\s+banking\s+|debit\s+|banking\s+)?transactions?\b", lowered):
            semantic_score += 8
        ranked.append((identity_score, semantic_score, -candidate.chunk_index, candidate, scoped_excerpt))
    if not ranked:
        return
    ranked.sort(key=lambda item: (item[1], item[0], item[2]), reverse=True)
    _, _, _, match, excerpt = ranked[0]
    extracted_fields.append(
        ExtractedFieldCandidate(
            field_name="unlimited_transactions_flag",
            candidate_value=True,
            value_type="boolean",
            confidence=0.84,
            extraction_method="heuristic_unlimited_transactions_fallback",
            source_document_id=context.source_document_id,
            source_snapshot_id=context.snapshot_id,
            evidence_chunk_id=match.evidence_chunk_id,
            evidence_text_excerpt=excerpt,
            anchor_type=match.anchor_type,
            anchor_value=match.anchor_value,
            page_no=match.page_no,
            chunk_index=match.chunk_index,
            field_metadata={"unlimited_transactions_fallback": True},
        )
    )


def _append_monthly_fee_fallback(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: set[str],
    extracted_fields: list[ExtractedFieldCandidate],
) -> None:
    """Recover a strongly labelled base account fee missed by field retrieval."""

    requested_fee_fields = {"monthly_fee", "public_display_fee"} & set(requested_fields)
    for item in list(extracted_fields):
        if item.field_name not in requested_fee_fields:
            continue
        try:
            is_zero = Decimal(str(item.candidate_value)) == 0
        except InvalidOperation:
            is_zero = False
        normalized_excerpt = _normalize_text(item.evidence_text_excerpt or "").lower()
        try:
            numeric_value = Decimal(str(item.candidate_value))
        except InvalidOperation:
            numeric_value = None
        if (
            (is_zero and _is_conditional_no_fee_offer(normalized_excerpt, context=context))
            or (numeric_value is not None and numeric_value >= Decimal("500"))
            or _money_value_has_non_fee_context(value=item.candidate_value, context=normalized_excerpt)
        ):
            # Zero is the waived outcome, not the recurring base fee.  Remove
            # it before scanning the source for a strongly labelled base fee.
            extracted_fields.remove(item)
    existing_fields = {item.field_name for item in extracted_fields}
    missing_fee_fields = requested_fee_fields - existing_fields
    if not missing_fee_fields:
        return

    ranked: list[tuple[int, int, int, EvidenceChunkCandidate, str, str]] = []
    for candidate in candidates:
        if _mentions_named_other_product_without_target(
            context=context,
            excerpt=candidate.evidence_excerpt,
        ):
            continue
        scoped_excerpt, identity_score = _scope_excerpt_to_product_identity(
            context=context,
            excerpt=candidate.evidence_excerpt,
        )
        lowered = _normalize_text(scoped_excerpt).lower()
        value = _extract_money_value(
            context=context,
            field_name="monthly_fee",
            text=scoped_excerpt,
            lowered=lowered,
        )
        if value is None:
            continue
        semantic_score = _field_evidence_semantic_score(
            field_name="monthly_fee",
            candidate_value=value,
            excerpt=scoped_excerpt,
        )
        if re.search(r"\bmonthly\s+(?:account\s+|plan\s+)?fees?\b", lowered):
            semantic_score += 8
        ranked.append(
            (
                identity_score,
                semantic_score,
                -candidate.chunk_index,
                candidate,
                scoped_excerpt,
                value,
            )
        )
    if not ranked:
        return
    # A strongly labelled base-fee row can omit the product title, while an
    # FAQ/benefit paragraph repeats the title beside a discount. Semantic fee
    # evidence therefore outranks identity after named-other-product vetoes.
    ranked.sort(key=lambda item: (item[1], item[0], item[2]), reverse=True)
    _, _, _, match, excerpt, value = ranked[0]
    for field_name in sorted(missing_fee_fields):
        extracted_fields.append(
            ExtractedFieldCandidate(
                field_name=field_name,
                candidate_value=value,
                value_type="decimal",
                confidence=0.82,
                extraction_method="heuristic_monthly_fee_fallback",
                source_document_id=context.source_document_id,
                source_snapshot_id=context.snapshot_id,
                evidence_chunk_id=match.evidence_chunk_id,
                evidence_text_excerpt=excerpt,
                anchor_type=match.anchor_type,
                anchor_value=match.anchor_value,
                page_no=match.page_no,
                chunk_index=match.chunk_index,
                field_metadata={"monthly_fee_fallback": True},
            )
        )


def _append_minimum_deposit_fallback(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: set[str],
    extracted_fields: list[ExtractedFieldCandidate],
) -> None:
    """Recover an explicitly labelled opening investment missed by retrieval."""

    if "minimum_deposit" not in requested_fields:
        return
    existing_minimum = next(
        (item for item in extracted_fields if item.field_name == "minimum_deposit"),
        None,
    )
    if existing_minimum is not None and not re.search(
        r"(?:for|with)\s+(?:the\s+)?monthly\s+interest\s+payment\s+option|"
        r"clients?\s+who\s+wish\s+to\s+receive\s+interest\s+monthly",
        existing_minimum.evidence_text_excerpt,
        flags=re.IGNORECASE,
    ):
        return
    ranked: list[tuple[int, int, int, EvidenceChunkCandidate, str, str]] = []
    for candidate in candidates:
        if _mentions_named_other_product_without_target(context=context, excerpt=candidate.evidence_excerpt):
            continue
        scoped_excerpt, identity_score = _scope_excerpt_to_product_identity(
            context=context,
            excerpt=candidate.evidence_excerpt,
        )
        excerpt = scoped_excerpt
        # Some detail pages place their terms table before a repeated product
        # heading. Identity scoping then starts at that later heading and used
        # to discard an otherwise unambiguous labelled minimum. Retain the
        # whole chunk only when it contains the target identity and a single
        # explicit minimum label; multiple minima still use the tighter scope.
        explicit_minimum_labels = re.findall(
            r"\bminimum\s+(?:opening\s+)?(?:deposit|investment)\b|\bopening\s+deposit\b",
            candidate.evidence_excerpt,
            flags=re.IGNORECASE,
        )
        if identity_score > 0 and len(explicit_minimum_labels) == 1:
            excerpt = candidate.evidence_excerpt
        lowered = _normalize_text(excerpt).lower()
        value = _extract_money_value(
            context=context,
            field_name="minimum_deposit",
            text=excerpt,
            lowered=lowered,
        )
        if value is None:
            continue
        semantic_score = 0
        if re.search(
            r"\bminimum\s+(?:opening\s+)?(?:deposit|investment)\b|\bopening\s+deposit\b",
            lowered,
        ):
            semantic_score += 10
        money_values = re.findall(r"\$\s*\d[\d,]*(?:\.\d{1,2})?", excerpt)
        if len(money_values) >= 3:
            semantic_score += 6
        if len(money_values) <= 2 and re.search(
            r"(?:for|with)\s+(?:the\s+)?monthly\s+interest\s+payment\s+option|"
            r"clients?\s+who\s+wish\s+to\s+receive\s+interest\s+monthly",
            lowered,
        ):
            semantic_score -= 10
        ranked.append(
            (
                identity_score,
                semantic_score,
                -candidate.chunk_index,
                candidate,
                excerpt,
                value,
            )
        )
    if not ranked:
        return
    identity_backed = [item for item in ranked if item[0] > 0]
    ranked_options = identity_backed or ranked
    ranked_options.sort(key=lambda item: (item[1], item[0], item[2]), reverse=True)
    _, _, _, match, excerpt, value = ranked_options[0]
    if existing_minimum is not None:
        extracted_fields.remove(existing_minimum)
    extracted_fields.append(
        ExtractedFieldCandidate(
            field_name="minimum_deposit",
            candidate_value=value,
            value_type="decimal",
            confidence=0.82,
            extraction_method="heuristic_minimum_deposit_fallback",
            source_document_id=context.source_document_id,
            source_snapshot_id=context.snapshot_id,
            evidence_chunk_id=match.evidence_chunk_id,
            evidence_text_excerpt=excerpt,
            anchor_type=match.anchor_type,
            anchor_value=match.anchor_value,
            page_no=match.page_no,
            chunk_index=match.chunk_index,
            field_metadata={
                "minimum_deposit_fallback": True,
                "replaced_conditional_option_minimum": existing_minimum is not None,
            },
        )
    )


def _append_fee_waiver_fallback(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: list[str] | set[str],
    extracted_fields: list[ExtractedFieldCandidate],
) -> None:
    requested = {"minimum_balance", "fee_waiver_condition"}.intersection(requested_fields)
    existing = {item.field_name for item in extracted_fields}
    missing = requested - existing
    if not missing:
        return
    ranked: list[tuple[int, int, EvidenceChunkCandidate, str, str, str]] = []
    for candidate in candidates:
        if _mentions_named_other_product_without_target(context=context, excerpt=candidate.evidence_excerpt):
            continue
        scoped_excerpt, identity_score = _scope_excerpt_to_product_identity(
            context=context,
            excerpt=candidate.evidence_excerpt,
        )
        balance = _extract_minimum_balance_for_fee_waiver(context=context, text=scoped_excerpt)
        condition = _extract_fee_waiver_condition(context=context, text=scoped_excerpt)
        if balance is None or condition is None:
            continue
        lowered = _normalize_text(scoped_excerpt).lower()
        semantic_score = 10 if "monthly" in lowered and any(
            marker in lowered for marker in ("waiv", "pay no", "rebated", "or $0", "or €0", "or £0")
        ) else 0
        ranked.append((semantic_score, identity_score, candidate, scoped_excerpt, balance, condition))
    if not ranked:
        return
    ranked.sort(key=lambda item: (item[0], item[1], -item[2].chunk_index), reverse=True)
    _, _, match, excerpt, balance, condition = ranked[0]
    values: dict[str, tuple[object, str]] = {
        "minimum_balance": (balance, "decimal"),
        "fee_waiver_condition": (condition, "string"),
    }
    for field_name in sorted(missing):
        value, value_type = values[field_name]
        extracted_fields.append(
            ExtractedFieldCandidate(
                field_name=field_name,
                candidate_value=value,
                value_type=value_type,
                confidence=0.82,
                extraction_method="heuristic_fee_waiver_fallback",
                source_document_id=context.source_document_id,
                source_snapshot_id=context.snapshot_id,
                evidence_chunk_id=match.evidence_chunk_id,
                evidence_text_excerpt=excerpt,
                anchor_type=match.anchor_type,
                anchor_value=match.anchor_value,
                page_no=match.page_no,
                chunk_index=match.chunk_index,
                field_metadata={"fee_waiver_fallback": True},
            )
        )


def _append_labeled_numeric_extension_fallback(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: set[str],
    extracted_fields: list[ExtractedFieldCandidate],
) -> None:
    """Recover explicitly labelled profile-specific numeric rate/fee fields.

    Source profiles legitimately extend the shared schema with fields such as
    ``regular_interest_rate``, ``smart_interest_rate`` and
    ``transaction_fee``. Retrieval or AI can miss these values even when the
    official detail page contains an exact label. Scan the bounded evidence
    set, but accept only a value adjacent to the requested field's own label.
    """

    existing_fields = {item.field_name for item in extracted_fields}
    extension_fields = {
        field_name
        for field_name in set(requested_fields) - existing_fields
        if _is_numeric_extension_field(field_name)
    }
    for field_name in sorted(extension_fields):
        ranked: list[tuple[int, int, int, EvidenceChunkCandidate, str, str, str]] = []
        for candidate in candidates:
            if _mentions_named_other_product_without_target(context=context, excerpt=candidate.evidence_excerpt):
                continue
            scoped_excerpt, identity_score = _scope_excerpt_to_product_identity(
                context=context,
                excerpt=candidate.evidence_excerpt,
            )
            value, value_type, extraction_method, _ = _extract_candidate_value(
                context=context,
                field_name=field_name,
                excerpt=scoped_excerpt,
                anchor_value=candidate.anchor_value,
            )
            if value is None or value_type != "decimal":
                continue
            semantic_score = _numeric_extension_label_score(field_name=field_name, text=scoped_excerpt)
            if semantic_score <= 0:
                continue
            ranked.append(
                (
                    semantic_score,
                    identity_score,
                    -candidate.chunk_index,
                    candidate,
                    scoped_excerpt,
                    str(value),
                    extraction_method,
                )
            )
        if not ranked:
            continue
        ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        _, _, _, match, excerpt, value, extraction_method = ranked[0]
        extracted_fields.append(
            ExtractedFieldCandidate(
                field_name=field_name,
                candidate_value=value,
                value_type="decimal",
                confidence=0.82,
                extraction_method=f"{extraction_method}_fallback",
                source_document_id=context.source_document_id,
                source_snapshot_id=context.snapshot_id,
                evidence_chunk_id=match.evidence_chunk_id,
                evidence_text_excerpt=excerpt,
                anchor_type=match.anchor_type,
                anchor_value=match.anchor_value,
                page_no=match.page_no,
                chunk_index=match.chunk_index,
                field_metadata={"labeled_numeric_extension_fallback": True},
            )
        )


def _scope_excerpt_to_product_identity(
    *, context: ExtractionDocumentContext, excerpt: str
) -> tuple[str, int]:
    excerpt = _truncate_cross_product_section(excerpt)
    normalized_excerpt = _normalize_text(excerpt).lower()
    terms = _source_product_identity_terms(context)
    matching_terms = [term for term in terms if term in normalized_excerpt]
    if not matching_terms:
        return excerpt, 0
    best_term = max(matching_terms, key=len)
    identity_start = excerpt.lower().find(best_term)
    if identity_start < 0:
        return excerpt, len(best_term)
    scoped = excerpt[identity_start:]
    cross_sell = re.search(
        r"\b(?:explore|compare|discover|view)\s+(?:our\s+)?other\s+(?:banking\s+)?(?:accounts?|products?|options?)\b",
        scoped,
        flags=re.IGNORECASE,
    )
    if cross_sell is not None:
        scoped = scoped[:cross_sell.start()]
    return scoped or excerpt, min(100, len(best_term))


def _truncate_cross_product_section(excerpt: str) -> str:
    """Stop a product excerpt when a FAQ or CTA switches to a product lineup."""

    boundaries = (
        r"\bwhat\s+(?:types?\s+of|other)\s+[^?]{0,80}?(?:accounts?|products?)\s+does\s+[^?]{1,60}?\s+offer\s*\?",
        r"\b(?:explore|compare|discover|view)\s+(?:our\s+)?other\s+(?:banking\s+)?(?:accounts?|products?|options?)\b",
    )
    starts = [
        match.start()
        for pattern in boundaries
        if (match := re.search(pattern, excerpt, flags=re.IGNORECASE)) is not None
    ]
    if not starts:
        return excerpt
    scoped = excerpt[: min(starts)].rstrip()
    return scoped or excerpt


def _source_product_identity_terms(context: ExtractionDocumentContext) -> tuple[str, ...]:
    raw_values = [
        context.source_metadata.get("product_name"),
        context.source_metadata.get("source_name"),
        context.source_metadata.get("source_title"),
        context.source_metadata.get("page_title"),
        context.source_metadata.get("primary_heading"),
    ]
    discovery_metadata = context.source_metadata.get("discovery_metadata")
    if isinstance(discovery_metadata, dict):
        raw_values.extend((discovery_metadata.get("primary_heading"), discovery_metadata.get("page_title")))
    for url_key in ("url", "source_url", "resolved_url"):
        raw_url = str(context.source_metadata.get(url_key) or "").strip()
        if raw_url:
            raw_values.append(raw_url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").replace("_", " "))
    if isinstance(discovery_metadata, dict):
        resolved_url = str(discovery_metadata.get("resolved_url") or "").strip()
        if resolved_url:
            raw_values.append(resolved_url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").replace("_", " "))
    terms: set[str] = set()
    for raw_value in raw_values:
        cleaned = _clean_title_candidate(str(raw_value or ""))
        normalized = _normalize_text(cleaned).lower()
        normalized = re.sub(r"\s*\|.*$", "", normalized).strip()
        if len(normalized) >= 10 and not _looks_like_marketing_or_family_title(normalized):
            terms.add(normalized)
        # Product pages and comparison tables often shorten a full heading such
        # as "Performance Chequing Account" to just "Performance".  Preserve
        # that distinctive token so an unrelated audience offer elsewhere on
        # the same page cannot outrank the product's own fee/rate row.
        distinctive = re.sub(
            r"\b(?:bmo|rbc|td|cibc|scotiabank|scotia|simplii|tangerine|oaken|bank|financial|"
            r"chequing|checking|savings?|accounts?|credit|cards?|gics?|term|deposits?|canada|"
            r"low|fee|high|interest|rate|rates|unlimited|transactions?)\b",
            " ",
            normalized,
        )
        distinctive_punctuated = _normalize_text(distinctive).strip(" .,:;|/")
        distinctive_words = _normalize_text(re.sub(r"[^a-z0-9]+", " ", distinctive))
        for distinctive_term in (distinctive_punctuated, distinctive_words):
            if len(distinctive_term) >= 4 and distinctive_term not in {"personal", "everyday", "premium rate"}:
                terms.add(distinctive_term)
    return tuple(sorted(terms, key=len, reverse=True))


def _field_evidence_semantic_score(*, field_name: str, candidate_value: object, excerpt: str) -> int:
    lowered = _normalize_text(excerpt).lower()
    score = 0
    if field_name in {"monthly_fee", "public_display_fee"}:
        if re.search(r"\bstandard monthly fee\b|\bmonthly (?:account )?fee\s*(?:is|:)", lowered):
            score += 8
        if any(marker in lowered for marker in ("as low as", "rebate", "eligible for no monthly fee")):
            score -= 5
        try:
            if Decimal(str(candidate_value)) == 0 and any(marker in lowered for marker in ("as low as", "rebate")):
                score -= 10
            if Decimal(str(candidate_value)) == 0 and _is_conditional_no_fee_offer(lowered):
                score -= 14
        except InvalidOperation:
            pass
    if field_name == "unlimited_transactions_flag" and "unlimited debit transactions" in lowered:
        score += 8
    if field_name == "promotional_rate":
        if "total interest rate including promo" in lowered:
            score += 14
        if re.search(
            r"\bearn(?:\s+up\s+to)?\s+(?:a\s+savings\s+rate\s+of\s+)?\d{1,2}(?:\.\d+)?\s*%",
            lowered,
        ) and any(
            marker in lowered for marker in ("first 3 months", "for the first", "limited time", "limited-time")
        ):
            score += 10
        if any(marker in lowered for marker in ("extra", "additional", "bonus interest rate")) and not any(
            marker in lowered for marker in ("total interest rate", "promotional interest rate")
        ):
            score -= 5
    if field_name == "public_display_rate":
        if any(marker in lowered for marker in ("total interest rate including promo", "earn up to")):
            score += 12
        if "interest rate with bonus" in lowered:
            score += 9
        if any(marker in lowered for marker in ("extra", "additional")) and "total interest rate" not in lowered:
            score -= 4
    if field_name == "eligibility_text":
        if re.search(r"\b(?:eligibility|here(?:'s| is) how to qualify)\b", lowered):
            score += 8
        if (
            re.search(r"\bmaintain\s+an?\s+eligible\b", lowered)
            and re.search(r"\bcomplete\s+at\s+least\s+\d{1,2}\s+(?:out\s+)?of\s+(?:the\s+)?\d{1,2}\s+qualifying\b", lowered)
        ):
            score += 16
        if "could earn" in lowered and "when you start with an eligible" in lowered:
            score -= 4
    return score


def _append_rate_fallback_fields(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: list[str] | set[str] | None = None,
    extracted_fields: list[ExtractedFieldCandidate],
) -> None:
    existing_rate_fields = {
        field.field_name
        for field in extracted_fields
        if field.field_name in {"standard_rate", "public_display_rate", "promotional_rate"}
    }
    existing_standard = next(
        (field for field in extracted_fields if field.field_name == "standard_rate"),
        None,
    )
    standard_is_promotional = bool(
        existing_standard is not None
        and _is_promotional_rate_context(
            _normalize_text(existing_standard.evidence_text_excerpt or "").lower()
        )
    )
    if (
        existing_rate_fields
        and ("standard_rate" not in existing_rate_fields or standard_is_promotional)
        and (requested_fields is None or "standard_rate" in requested_fields)
    ):
        standard_match = _find_labeled_standard_rate_fallback(
            context=context,
            candidates=candidates,
        )
        if standard_match is not None:
            match, value = standard_match
            if existing_standard is not None:
                extracted_fields.remove(existing_standard)
            extracted_fields.append(
                ExtractedFieldCandidate(
                    field_name="standard_rate",
                    candidate_value=value,
                    value_type="decimal",
                    confidence=0.84,
                    extraction_method="heuristic_labeled_standard_rate_fallback",
                    source_document_id=context.source_document_id,
                    source_snapshot_id=context.snapshot_id,
                    evidence_chunk_id=match.evidence_chunk_id,
                    evidence_text_excerpt=match.evidence_excerpt,
                    anchor_type=match.anchor_type,
                    anchor_value=match.anchor_value,
                    page_no=match.page_no,
                    chunk_index=match.chunk_index,
                    field_metadata={"labeled_standard_rate_fallback": True},
                )
            )
    if (
        existing_rate_fields
        and "promotional_rate" not in existing_rate_fields
        and (requested_fields is None or "promotional_rate" in requested_fields)
    ):
        promotional_match = _find_advertised_promotional_rate_fallback(
            context=context,
            candidates=candidates,
        )
        if promotional_match is not None:
            match, value = promotional_match
            extracted_fields.append(
                ExtractedFieldCandidate(
                    field_name="promotional_rate",
                    candidate_value=value,
                    value_type="decimal",
                    confidence=0.82,
                    extraction_method="heuristic_advertised_promotional_rate_fallback",
                    source_document_id=context.source_document_id,
                    source_snapshot_id=context.snapshot_id,
                    evidence_chunk_id=match.evidence_chunk_id,
                    evidence_text_excerpt=match.evidence_excerpt,
                    anchor_type=match.anchor_type,
                    anchor_value=match.anchor_value,
                    page_no=match.page_no,
                    chunk_index=match.chunk_index,
                    field_metadata={"advertised_promotional_rate_fallback": True},
                )
            )
    if existing_rate_fields:
        return
    product_type_family = _canonical_product_type_family(_infer_product_type(context))
    if product_type_family not in {"savings", "gic"}:
        return
    product_name = next((str(field.candidate_value) for field in extracted_fields if field.field_name == "product_name"), "")
    terms = _rate_fallback_product_terms(product_name=product_name, context=context)
    match = _find_rate_fallback_candidate(candidates=candidates, terms=terms, product_type_family=product_type_family)
    if match is None:
        return
    percentages = _extract_rate_context_percentages(match.evidence_excerpt)
    if not percentages:
        return

    unique_percentages = sorted(set(percentages))
    public_display_rate = unique_percentages[-1]
    is_promotional = _is_promotional_rate_context(match.evidence_excerpt.lower())
    field_values: dict[str, Decimal] = {"public_display_rate": public_display_rate}
    if is_promotional:
        field_values["promotional_rate"] = public_display_rate
    else:
        field_values["standard_rate"] = unique_percentages[0]

    for field_name, value in field_values.items():
        extracted_fields.append(
            ExtractedFieldCandidate(
                field_name=field_name,
                candidate_value=_normalize_decimal(str(value)),
                value_type="decimal",
                confidence=0.78,
                extraction_method="heuristic_rate_context_fallback",
                source_document_id=context.source_document_id,
                source_snapshot_id=context.snapshot_id,
                evidence_chunk_id=match.evidence_chunk_id,
                evidence_text_excerpt=match.evidence_excerpt,
                anchor_type=match.anchor_type,
                anchor_value=match.anchor_value,
                page_no=match.page_no,
                chunk_index=match.chunk_index,
                field_metadata={
                    "rate_context_fallback": True,
                    "product_terms": list(terms),
                },
            )
        )


def _append_promotional_period_fallback(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: list[str] | set[str],
    extracted_fields: list[ExtractedFieldCandidate],
) -> None:
    if "promotional_period_text" not in requested_fields:
        return
    existing_fields = {field.field_name for field in extracted_fields}
    if "promotional_period_text" in existing_fields or "promotional_rate" not in existing_fields:
        return
    ranked: list[tuple[int, int, EvidenceChunkCandidate, str]] = []
    for candidate in candidates:
        if _mentions_named_other_product_without_target(
            context=context,
            excerpt=candidate.evidence_excerpt,
        ):
            continue
        value = _extract_promotional_period_text(
            context=context,
            text=candidate.evidence_excerpt,
        )
        if value is None:
            continue
        scoped_excerpt, identity_score = _scope_excerpt_to_product_identity(
            context=context,
            excerpt=candidate.evidence_excerpt,
        )
        promo_score = 4 if _PERCENT_RE.search(value) is not None else 0
        if any(marker in value.lower() for marker in ("welcome offer", "new client", "special interest rate")):
            promo_score += 3
        ranked.append((identity_score + promo_score, -candidate.chunk_index, candidate, value))
    if not ranked:
        return
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    _, _, candidate, value = ranked[0]
    extracted_fields.append(
        ExtractedFieldCandidate(
            field_name="promotional_period_text",
            candidate_value=value,
            value_type="string",
            confidence=0.82,
            extraction_method="heuristic_promotional_period_fallback",
            source_document_id=context.source_document_id,
            source_snapshot_id=context.snapshot_id,
            evidence_chunk_id=candidate.evidence_chunk_id,
            evidence_text_excerpt=candidate.evidence_excerpt,
            anchor_type=candidate.anchor_type,
            anchor_value=candidate.anchor_value,
            page_no=candidate.page_no,
            chunk_index=candidate.chunk_index,
            field_metadata={"promotional_period_fallback": True},
        )
    )


def _find_labeled_standard_rate_fallback(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
) -> tuple[EvidenceChunkCandidate, str] | None:
    """Recover an explicitly labelled ongoing rate when a promo was found first."""

    ranked: list[tuple[int, int, int, EvidenceChunkCandidate, str]] = []
    for candidate in candidates:
        if _mentions_named_other_product_without_target(
            context=context,
            excerpt=candidate.evidence_excerpt,
        ):
            continue
        scoped_excerpt, identity_score = _scope_excerpt_to_product_identity(
            context=context,
            excerpt=candidate.evidence_excerpt,
        )
        normalized = _normalize_text(scoped_excerpt)
        lowered = normalized.lower()
        label_score = 0
        if re.search(r"\bthereafter\b\D{0,40}\d{1,2}(?:\.\d{1,4})?\s*%", normalized, flags=re.IGNORECASE):
            label_score = 14
        elif re.search(
            r"\b(?:regular|standard|ongoing|base)\s+(?:annual\s+)?interest\s+rate\b",
            lowered,
        ):
            label_score = 12
        elif re.search(
            r"\bafter\s+(?:the\s+)?(?:promotional|promotion|promo|offer)\s+period\b",
            lowered,
        ):
            label_score = 11
        elif re.search(
            r"(?<![\d.])\d{1,2}(?:\.\d{1,4})?\s*%\s*[†*^]?\s*(?:annual\s+)?interest\s+rate\b|"
            r"\b(?:our\s+)?rates?\s+(?:are|is)\s+(?:great\s+)?at\s+\d{1,2}(?:\.\d{1,4})?\s*%|"
            r"\binterest\s+rate\s+of\s+\d{1,2}(?:\.\d{1,4})?\s*%",
            normalized,
            flags=re.IGNORECASE,
        ):
            # Product hero cards commonly place the numeric value immediately
            # before the generic "Interest rate" label. This is the ongoing
            # rate even when a separate offer card appears later in the chunk.
            label_score = 10
        if label_score == 0:
            continue
        value = _extract_standard_rate_value(scoped_excerpt)
        if value is None:
            continue
        ranked.append((label_score, identity_score, -candidate.chunk_index, candidate, value))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    _, _, _, candidate, value = ranked[0]
    return candidate, value


def _find_advertised_promotional_rate_fallback(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
) -> tuple[EvidenceChunkCandidate, str] | None:
    ranked: list[tuple[int, int, EvidenceChunkCandidate, str]] = []
    for candidate in candidates:
        if _mentions_named_other_product_without_target(
            context=context,
            excerpt=candidate.evidence_excerpt,
        ):
            continue
        value = _extract_promotional_rate_value(context=context, text=candidate.evidence_excerpt)
        if value is None:
            continue
        semantic_score = _field_evidence_semantic_score(
            field_name="promotional_rate",
            candidate_value=value,
            excerpt=candidate.evidence_excerpt,
        )
        # A component labelled merely as "bonus interest" is not the total
        # rate advertised to customers. Require explicit total/earn language.
        if semantic_score < 10:
            continue
        ranked.append((semantic_score, -candidate.chunk_index, candidate, value))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    _, _, candidate, value = ranked[0]
    return candidate, value


def _rate_fallback_product_terms(*, product_name: str, context: ExtractionDocumentContext) -> tuple[str, ...]:
    raw_terms = [
        product_name,
        str(context.source_metadata.get("product_name") or ""),
        str(context.source_metadata.get("page_title") or ""),
        str(context.source_metadata.get("primary_heading") or ""),
    ]
    terms: set[str] = set()
    for raw_term in raw_terms:
        normalized = _normalize_text(raw_term).lower()
        if not normalized:
            continue
        normalized = normalized.replace("esavings", "savings")
        terms.add(normalized)
        simplified = re.sub(
            r"\b(?:rbc|td|bmo|cibc|scotiabank|scotia|royal|bank|account|accounts|canada|trust)\b",
            " ",
            normalized,
        )
        simplified = _normalize_text(simplified)
        if len(simplified) >= 6:
            terms.add(simplified)
        if " savings" in simplified:
            prefix = simplified.split(" savings", 1)[0].strip()
            if len(prefix) >= 6:
                terms.add(prefix)
        if " gic" in simplified:
            prefix = simplified.split(" gic", 1)[0].strip()
            if len(prefix) >= 6:
                terms.add(prefix)
    return tuple(sorted(terms, key=len, reverse=True))


def _find_rate_fallback_candidate(
    *,
    candidates: list[EvidenceChunkCandidate],
    terms: tuple[str, ...],
    product_type_family: str,
) -> EvidenceChunkCandidate | None:
    ranked: list[tuple[int, int, EvidenceChunkCandidate]] = []
    for candidate in candidates:
        percentages = _extract_rate_context_percentages(candidate.evidence_excerpt)
        if not percentages:
            continue
        normalized = _normalize_text(candidate.evidence_excerpt).lower().replace("esavings", "savings")
        anchor = str(candidate.anchor_value or "").lower()
        if any(token in normalized for token in ("100% reimbursed", "unauthorized transactions", "principal protection")):
            continue
        score = 0
        if any(term and term in normalized for term in terms):
            score += 5
        if any(token in normalized for token in ("interest rate", "posted rate", "annual interest", "bonus interest")):
            score += 3
        if any(token in anchor for token in ("rate", "interest", "return", "yield")):
            score += 2
        if product_type_family == "gic" and "gic" in normalized:
            score += 1
        if product_type_family == "savings" and "savings" in normalized:
            score += 1
        if score < 5:
            continue
        ranked.append((score, -candidate.chunk_index, candidate))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return ranked[0][2]


def _extract_rate_context_percentages(text: str) -> list[Decimal]:
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
        try:
            values.append(Decimal(match.group(1)))
        except InvalidOperation:
            continue
    return values


def _extract_candidate_value(
    *,
    context: ExtractionDocumentContext,
    field_name: str,
    excerpt: str,
    anchor_value: str | None,
) -> tuple[object | None, str, str, dict[str, object]]:
    text = excerpt.strip()
    lowered = text.lower()
    if _is_generic_banking_info_text(text):
        return None, "string", "heuristic_noise_filter", {"suppressed_reason": "generic_banking_info_navigation"}
    if _is_noise_for_product_context(context=context, text=text):
        return None, "string", "heuristic_noise_filter", {"suppressed_reason": "cross_product_navigation_noise"}
    if field_name == "eligibility_text" and _is_audience_specific_sibling_eligibility(
        context=context,
        text=text,
    ):
        return None, "string", "heuristic_noise_filter", {"suppressed_reason": "audience_specific_sibling_program"}

    if field_name in {"monthly_fee", "public_display_fee", "minimum_balance", "minimum_deposit"}:
        money_value = _extract_money_value(context=context, field_name=field_name, text=text, lowered=lowered)
        return money_value, "decimal", "heuristic_money", {}

    if field_name in {"transaction_fee", "additional_transaction_fee"}:
        transaction_fee = _extract_transaction_fee(
            text=text,
            require_additional=field_name == "additional_transaction_fee",
        )
        return transaction_fee, "decimal", "heuristic_transaction_fee", {}

    if field_name == "promotional_rate" and not _has_product_promotional_context(context=context, text=text):
        return None, "decimal", "heuristic_percent", {}

    if field_name == "base_12_month_rate":
        return _extract_base_12_month_rate(text), "decimal", "heuristic_12_month_percent", {}

    if field_name in {"standard_rate", "public_display_rate", "promotional_rate"}:
        if field_name == "standard_rate":
            percent = _extract_standard_rate_value(text)
        elif field_name == "promotional_rate":
            percent = _extract_promotional_rate_value(context=context, text=text)
        else:
            percent = _extract_public_display_rate_value(context=context, text=text)
        return percent, "decimal", "heuristic_percent", {}

    if field_name in {
        "purchase_interest_rate",
        "cash_advance_rate",
        "balance_transfer_rate",
        "mortgage_rate",
        "interest_rate",
    }:
        if field_name in {"interest_rate", "mortgage_rate"} and _is_reference_rate_margin_only(text):
            return None, "decimal", "heuristic_labeled_rate", {"suppressed_reason": "reference_rate_margin_not_total_rate"}
        return _extract_labeled_extension_rate(field_name=field_name, text=text), "decimal", "heuristic_labeled_rate", {}

    if field_name == "annual_fee":
        return _extract_labeled_extension_fee(field_name=field_name, text=text), "decimal", "heuristic_labeled_fee", {}

    if _is_numeric_extension_field(field_name):
        contract = field_contract(field_name)
        if contract is not None and contract.unit == "percentage_points":
            if field_name in {"interest_rate", "mortgage_rate"} and _is_reference_rate_margin_only(text):
                return None, "decimal", "heuristic_labeled_rate", {"suppressed_reason": "reference_rate_margin_not_total_rate"}
            return _extract_labeled_extension_rate(field_name=field_name, text=text), "decimal", "heuristic_labeled_rate", {}
        if contract is not None and contract.unit == "currency_amount":
            return _extract_labeled_extension_fee(field_name=field_name, text=text), "decimal", "heuristic_labeled_fee", {}

    if field_name == "term_rate_table":
        table_rows = _extract_term_rate_table(text)
        return table_rows, "json", "heuristic_term_rate_table", {}

    if field_name == "interest_rate_summary":
        return _extract_interest_rate_summary(text), "string", "heuristic_rate_summary", {}

    if field_name == "included_transactions":
        return _extract_included_transactions(text), "integer", "heuristic_transaction_count", {}

    if field_name in {"interest_payment_frequency", "compounding_frequency"}:
        return _detect_frequency(lowered), "string", "heuristic_frequency", {}

    if field_name == "interest_calculation_method":
        return _extract_interest_calculation_method(text), "string", "heuristic_sentence", {}

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
        return _extract_boolean_flag(
            context=context,
            field_name=field_name,
            text=text,
            lowered=lowered,
            anchor_value=anchor_value,
        ), "boolean", "heuristic_flag", {}

    if field_name == "cheque_book_info":
        return _extract_cheque_book_info(text), "string", "heuristic_text", {}

    if field_name in {
        "fee_waiver_condition",
        "eligibility_text",
        "application_method",
        "post_maturity_interest_rate",
        "tax_benefits",
        "deposit_insurance",
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
        if field_name == "eligibility_text":
            eligibility_text = _extract_eligibility_text(text)
            return eligibility_text, "string", "heuristic_eligibility_text", {}
        if field_name == "application_method":
            return _extract_application_method(text), "string", "heuristic_application_method", {}
        if field_name == "post_maturity_interest_rate":
            return _extract_post_maturity_interest_rate(text), "string", "heuristic_post_maturity_interest_rate", {}
        if field_name == "tax_benefits":
            if not _source_is_registered_product(context):
                return None, "string", "heuristic_tax_benefits", {"suppressed_reason": "sibling_registered_product_navigation"}
            return _extract_tax_benefits(context=context, text=text), "string", "heuristic_tax_benefits", {}
        if field_name == "deposit_insurance":
            return _extract_deposit_insurance(text), "string", "heuristic_deposit_insurance", {}
        if field_name == "tier_definition_text":
            return _extract_tier_definition_text(text), "string", "heuristic_text", {}
        if field_name == "withdrawal_limit_text":
            return _extract_withdrawal_limit_text(context=context, text=text), "string", "heuristic_text", {}
        if field_name == "notes":
            return _extract_notes_text(text), "string", "heuristic_text", {}
        if field_name == "promotional_period_text":
            return _extract_promotional_period_text(context=context, text=text), "string", "heuristic_text", {}
        text_value = _normalize_text(_find_sentence(text, ("eligible", "waive", "tier", "limit", "promo", "offer")) or text)
        return text_value[:280], "string", "heuristic_text", {}

    return _normalize_text(text)[:280], "string", "heuristic_text", {}


def _is_audience_specific_sibling_eligibility(*, context: ExtractionDocumentContext, text: str) -> bool:
    lowered = _normalize_text(text).lower()
    audience_match = re.search(r"\b(?:international\s+students?|students?|newcomers?)\b", lowered)
    if audience_match is None or _source_identity_contains_audience(
        context=context,
        audience=audience_match.group(0),
    ):
        return False
    return any(
        marker in lowered
        for marker in (
            "student gic program",
            "international student program",
            "meet visa requirements",
            "before you arrive in canada",
            "newcomer program",
        )
    )


def _is_numeric_extension_field(field_name: str) -> bool:
    contract = field_contract(field_name)
    return (
        contract is not None
        and contract.value_type == "decimal"
        and field_name not in {
            "monthly_fee",
            "public_display_fee",
            "minimum_balance",
            "minimum_deposit",
            "standard_rate",
            "base_12_month_rate",
            "public_display_rate",
            "promotional_rate",
            "highest_rate",
            "annual_fee",
            "purchase_interest_rate",
            "cash_advance_rate",
            "balance_transfer_rate",
            "mortgage_rate",
            "interest_rate",
        }
    )


def _numeric_extension_labels(field_name: str) -> tuple[str, ...]:
    label = re.sub(r"\s+", " ", field_name.replace("_", " ")).strip()
    labels = [label]
    if label.endswith(" rate"):
        labels.append(label.removesuffix(" rate"))
    if field_name in {"transaction_fee", "additional_transaction_fee"}:
        labels.extend(("fee for transactions", "transactions fee", "transaction fee"))
        if field_name == "transaction_fee":
            labels.append("transactions")
    if field_name == "balance_transfer_rate":
        labels.extend(("balance transfer", "balance transfers"))
    return tuple(dict.fromkeys(item for item in labels if item))


def _numeric_extension_label_score(*, field_name: str, text: str) -> int:
    lowered = _normalize_text(text).lower()
    labels = _numeric_extension_labels(field_name)
    return max((len(label.split()) for label in labels if re.search(rf"\b{re.escape(label)}\b", lowered)), default=0)


def _extract_labeled_extension_rate(*, field_name: str, text: str) -> str | None:
    normalized = _normalize_text(text)
    for label in _numeric_extension_labels(field_name):
        patterns = [
            rf"\b{re.escape(label)}\b[\s\S]{{0,180}}?(?P<rate>\d{{1,2}}(?:\.\d{{1,4}})?)\s*%",
        ]
        if field_name == "balance_transfer_rate":
            patterns.append(
                rf"(?P<rate>\d{{1,2}}(?:\.\d{{1,4}})?)\s*%[\s\S]{{0,90}}?\b{re.escape(label)}\b"
            )
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if match is None:
                continue
            rate = match.group("rate")
            rate_context = bounded_rate_evidence_context(
                text=normalized,
                value_start=match.start("rate"),
                value_end=match.end("rate"),
            )
            if canonical_deposit_rate_suppression_reason(value=rate, context=rate_context) is None:
                return _normalize_decimal(rate)
    return None


def _is_reference_rate_margin_only(text: str) -> bool:
    normalized = _normalize_text(text)
    has_margin_formula = re.search(
        r"\b(?:bank\s+)?prime(?:\s+rate)?\b\s*(?:\+|plus|-|minus)\s*\d{1,2}(?:\.\d{1,4})?\s*%",
        normalized,
        flags=re.IGNORECASE,
    ) is not None
    if not has_margin_formula:
        return False
    has_explicit_total = re.search(
        r"\b(?:current|total|effective|annual)\s+(?:annual\s+)?(?:interest\s+)?rate\b\s*(?:is|of|:)?\s*"
        r"\d{1,2}(?:\.\d{1,4})?\s*%",
        normalized,
        flags=re.IGNORECASE,
    ) is not None
    return not has_explicit_total


def _extract_labeled_extension_fee(*, field_name: str, text: str) -> str | None:
    normalized = _normalize_text(text)
    for label in _numeric_extension_labels(field_name):
        escaped_label = re.escape(label)
        patterns = (
            rf"\b{escaped_label}\b[\s\S]{{0,50}}?\$\s*(?P<fee>\d{{1,3}}(?:,\d{{3}})*(?:\.\d{{1,2}})?)",
            rf"\$\s*(?P<fee>\d{{1,3}}(?:,\d{{3}})*(?:\.\d{{1,2}})?)[\s\S]{{0,35}}?\b{escaped_label}\b",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if match is None:
                continue
            context_window = normalized[max(0, match.start() - 80):min(len(normalized), match.end() + 80)].lower()
            if any(marker in context_window for marker in ("gift", "welcome bonus", "cash bonus", "minimum deposit")):
                continue
            return _normalize_decimal(match.group("fee"))
    return None


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
    if context.source_id in _CIBC_SAVINGS_SOURCE_TITLES:
        return _CIBC_SAVINGS_SOURCE_TITLES[context.source_id]

    authoritative_title = _authoritative_discovery_product_title(context)
    if authoritative_title is not None:
        return authoritative_title

    ranked_titles: list[tuple[float, int, int, str]] = []
    seen_titles: set[str] = set()

    for metadata_title in _source_metadata_title_candidates(context):
        cleaned_title = _clean_title_candidate(metadata_title)
        if not cleaned_title:
            continue
        lowered_title = cleaned_title.lower()
        if lowered_title in seen_titles or _title_conflicts_with_product_context(context=context, title=cleaned_title):
            continue
        seen_titles.add(lowered_title)
        score = _score_title_candidate(
            text=cleaned_title,
            bank_code=context.bank_code,
            chunk_index=0,
            line_index=0,
        ) + 0.25
        ranked_titles.append((score, 0, 0, cleaned_title))

    for candidate in sorted(candidates, key=lambda item: (item.chunk_index, item.evidence_chunk_id)):
        if _is_noise_for_product_context(context=context, text=candidate.evidence_excerpt):
            continue
        lines = [line for line in candidate.evidence_excerpt.splitlines() if line.strip()]
        for line_index, line in enumerate(lines[:6]):
            normalized = _clean_title_candidate(line)
            if not normalized:
                continue
            lowered = normalized.lower()
            if lowered in seen_titles or _title_conflicts_with_product_context(context=context, title=normalized):
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
    title = " ".join(part.capitalize() if part.islower() else part for part in normalized.split())
    return _restore_us_dollar_text(title)


def _clean_title_candidate(value: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        return ""

    cleaned = _strip_title_action_copy(_restore_us_dollar_text(normalized))
    if _looks_like_non_product_document_title(cleaned):
        return ""
    if any(pattern.search(cleaned) is not None for pattern in _NON_PRODUCT_ACTION_TITLE_PATTERNS):
        return ""
    cleaned = re.sub(
        r"(?:\s+\|\s+(?:(?:BMO|CIBC|RBC|Royal Bank|Scotiabank|Simplii Financial|Tangerine|TD|Oaken Financial)(?:\s+Canada)?|Investments|Bank Accounts?))+$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"^(?:accounts?|investments?)\s+(?=.+\b(?:account|gic|certificate|card|mortgage|loan)\b)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    # Component-driven pages can expose an HTML footnote icon as an enclosed
    # Unicode number (for example `⑩` or `㈢`) at the end of a valid heading.
    # It is not product identity and would break later evidence scoping.
    cleaned = re.sub(r"[\s\u2460-\u24ff\u3200-\u32ff]+$", "", cleaned).strip()
    compacted = re.sub(r"[^a-z0-9]+", "", cleaned.lower())
    if compacted in _GENERIC_TITLE_LINES:
        return cleaned

    wrapper_patterns = (
        r"^benefits of (?:the )?(.+?)(?:\.)?$",
        r"^about (?:the )?(.+?)(?:\.)?$",
        r"^what (?:is|are) (?:the )?(.+?)(?:\?)?$",
        r"^explore the (?:features|fees) (?:of|for) (?:the )?(.+)$",
        r"^full disclosure for (?:the )?(.+?)(?:\.)?$",
        r"^(.+?)\s+faqs$",
    )
    for pattern in wrapper_patterns:
        match = re.match(pattern, cleaned, flags=re.IGNORECASE)
        if match is None:
            continue
        candidate = _normalize_text(match.group(1))
        if candidate:
            return _restore_us_dollar_text(candidate)
    return cleaned


def _strip_title_action_copy(value: str) -> str:
    cleaned = _normalize_text(value)
    cleaned = re.sub(
        r"(?:\s*[:|]\s+|\s+[-\u2013\u2014]\s+)"
        r"(?:apply|compare|explore|get started|learn|open|view)\b.*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    open_now_match = re.match(r"^open now\s*[-:\u2013\u2014]\s*(.+)$", cleaned, flags=re.IGNORECASE)
    if open_now_match is not None:
        cleaned = _normalize_text(open_now_match.group(1))
    open_product_match = re.match(
        r"^open\s+(?:a|an|the)\s+(.+?)(?:\s+(?:online|today))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if open_product_match is not None:
        candidate = _normalize_text(open_product_match.group(1))
        if any(keyword in candidate.lower() for keyword in _PRODUCT_TITLE_KEYWORDS):
            cleaned = candidate
    return cleaned


def _looks_like_non_product_document_title(value: str) -> bool:
    normalized = _normalize_text(value)
    if not normalized:
        return False
    lowered = normalized.lower()
    return (
        any(marker in lowered for marker in _NON_PRODUCT_DOCUMENT_TITLE_MARKERS)
        or any(pattern.search(normalized) is not None for pattern in _NON_PRODUCT_DOCUMENT_TITLE_PATTERNS)
    )


def _extract_description(*, context: ExtractionDocumentContext, candidates: list[EvidenceChunkCandidate]) -> str | None:
    ranked: list[tuple[int, int, str]] = []
    for candidate in sorted(candidates, key=lambda item: (item.chunk_index, item.evidence_chunk_id)):
        if _is_cross_product_navigation_noise(candidate.evidence_excerpt):
            continue
        if _is_noise_for_product_context(context=context, text=candidate.evidence_excerpt):
            continue
        lines = [line.strip() for line in candidate.evidence_excerpt.splitlines() if line.strip()]
        for line_index in range(1, len(lines)):
            if _description_line_is_boundary(lines[line_index]):
                continue
            description_parts = [lines[line_index]]
            for continuation in lines[line_index + 1 :]:
                if re.search(r"[.!?:]$", description_parts[-1]):
                    break
                if _description_line_is_boundary(continuation):
                    break
                description_parts.append(continuation)
                if re.search(r"[.!?:]$", continuation):
                    break
            description = _bounded_description_text(" ".join(description_parts))
            if description is None:
                continue
            if _looks_like_navigation_description(description) or _looks_like_non_product_summary(
                context=context,
                value=description,
            ) or _description_conflicts_with_product_context(
                context=context, description=description
            ):
                continue
            lowered = description.lower()
            score = 0
            if len(description) >= 45:
                score += 3
            if re.search(r"[.!?:]$", description):
                score += 2
            if any(marker in lowered for marker in (" account", " gic", " mortgage", " credit card", " loan")):
                score += 3
            if any(
                re.search(rf"\b{verb}\b", lowered)
                for verb in ("save", "grow", "earn", "enjoy", "offer", "provide", "include", "help", "give", "make", "can", "have")
            ):
                score += 3
            if any(marker in lowered for marker in ("special offer", "new client offer", "learn more", "accept all", "cookies")):
                score -= 12
            if score >= 6:
                ranked.append((score, -candidate.chunk_index, description))
        normalized = _normalize_text(candidate.evidence_excerpt)
        if (
            len(normalized) > 20
            and not _looks_like_navigation_description(normalized)
            and not _looks_like_non_product_summary(context=context, value=normalized)
            and not _description_conflicts_with_product_context(context=context, description=normalized)
        ):
            bounded_normalized = _bounded_description_text(normalized)
            if bounded_normalized is not None:
                ranked.append((1, -candidate.chunk_index, bounded_normalized))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return ranked[0][2]


def _bounded_description_text(value: str, *, max_length: int = 240) -> str | None:
    """Return complete customer-facing copy without cutting a flattened clause."""

    normalized = _normalize_text(value)
    if len(normalized) <= max_length:
        return normalized
    prefix = normalized[:max_length]
    sentence_ends = [match.end() for match in re.finditer(r"[.!?](?=\s|$)", prefix)]
    if sentence_ends and sentence_ends[-1] >= 60:
        return prefix[: sentence_ends[-1]].strip()
    return None


def _description_line_is_boundary(value: str) -> bool:
    normalized = _normalize_text(value).lower().strip(" .:-|†*^")
    if not normalized:
        return True
    if _looks_like_navigation_description(value):
        return True
    if re.fullmatch(r"(?:[$€£]\s*)?\d[\d,.]*\s*%?", normalized):
        return True
    if re.fullmatch(r"(?:interest rate|monthly fee|minimum balance|minimum deposit|special offer|limited-time offer)", normalized):
        return True
    if any(
        marker in normalized
        for marker in (
            "feedback",
            "accept all",
            "manage preferences",
            "privacy preference",
            "open an account",
            "open account",
            "purchase gic",
            "call 1-",
            "learn more",
            "still not sure",
            "let us help you decide",
            "answer a few quick questions",
        )
    ):
        return True
    if normalized.endswith("?") and len(normalized) <= 100:
        return True
    return False


def _authoritative_discovery_product_title(context: ExtractionDocumentContext) -> str | None:
    discovery_metadata = context.source_metadata.get("discovery_metadata")
    if not isinstance(discovery_metadata, dict):
        return None
    heading = _clean_title_candidate(str(discovery_metadata.get("primary_heading") or ""))
    page_title = _clean_title_candidate(str(discovery_metadata.get("page_title") or ""))
    for candidate, counterpart in ((heading, page_title), (page_title, heading)):
        if not candidate or _looks_like_marketing_or_family_title(candidate):
            continue
        candidate_key = re.sub(r"[^a-z0-9]+", " ", candidate.lower()).strip()
        counterpart_key = re.sub(r"[^a-z0-9]+", " ", counterpart.lower()).strip()
        has_product_identity = any(keyword in candidate_key for keyword in _PRODUCT_TITLE_KEYWORDS)
        corroborated = bool(counterpart_key) and (
            candidate_key in counterpart_key or counterpart_key in candidate_key
        )
        if has_product_identity and corroborated:
            return candidate
    try:
        ai_score = float(discovery_metadata.get("ai_parallel_score") or 0)
    except (TypeError, ValueError):
        ai_score = 0.0
    page_reason_codes = {
        str(item).strip().lower()
        for item in discovery_metadata.get("page_evidence_reason_codes", [])
        if str(item).strip()
    }
    ai_role = str(discovery_metadata.get("ai_predicted_role") or "").lower()
    candidate_origin = str(discovery_metadata.get("candidate_origin") or "").lower()
    if (
        page_title
        and not _title_conflicts_with_product_context(context=context, title=page_title)
        and ai_role in {"detail", "supporting_html"}
        and ai_score >= 8
        and str(discovery_metadata.get("ai_confidence_band") or "").lower() == "high"
        and "location_access_gate" in page_reason_codes
        and "structured_component_evidence" in page_reason_codes
        and "title_semantic_match" in page_reason_codes
        and (ai_role == "detail" or candidate_origin == "verified_coverage_source")
    ):
        return page_title
    if (
        heading
        and not _looks_like_marketing_or_family_title(heading)
        and str(discovery_metadata.get("ai_predicted_role") or "").lower() == "detail"
        and str(discovery_metadata.get("ai_confidence_band") or "").lower() == "high"
        and ai_score >= 8
        and context.bank_code.lower() in heading.lower()
        and 2 <= len(heading.split()) <= 10
    ):
        # A high-confidence product-detail H1 is authoritative when the SEO
        # title is audience/marketing copy rather than a corroborating name.
        return heading
    return None


def _looks_like_marketing_or_family_title(value: str) -> bool:
    lowered = _normalize_text(value).lower()
    return any(
        re.search(pattern, lowered)
        for pattern in (
            r"^benefits of banking with\b",
            r"\bincluded with every\b",
            r"\breach your .+ faster\b",
            r"\bsave for (?:today|tomorrow)\b",
            r"\b(?:open|compare|choose|find|explore|discover) (?:an? |the |our )?(?:bank |savings |chequing |checking |credit card |mortgage )?(?:account|accounts|options|products?)\b",
        )
    )


def _looks_like_navigation_description(value: str) -> bool:
    normalized = _normalize_text(value).lower().strip(" .:-|")
    if normalized in {
        "menu", "accounts", "bank accounts", "banking", "investments", "investment", "navigation skipped", "save", "savings",
        "chequing", "chequing accounts", "checking accounts", "credit cards", "mortgages", "loans", "personal banking",
        "overviewfees and details", "overview fees and details", "overview fees details", "offer", "special offer",
        "compare account", "compare accounts",
    }:
        return True
    if normalized.startswith(("menu ", "document ", "bank accounts ", "investments ", "personal banking ")):
        return True
    if re.match(r"^(?:accounts?|bank accounts?|chequing accounts?|savings accounts?)\b", normalized) and any(
        marker in normalized for marker in ("welcome offer", "special offer")
    ):
        return True
    if re.fullmatch(r"monthly\s+(?:account\s+)?fee\s*:?\s*\$?\s*\d[\d,.]*(?:\s*(?:/|per)\s*month)?", normalized):
        return True
    return _is_generic_banking_info_text(value) or _is_cross_product_navigation_noise(value)


def _looks_like_non_product_summary(*, context: ExtractionDocumentContext, value: str) -> bool:
    """Reject CTAs, comparison fragments, and adjacent-product copy as descriptions."""

    normalized = _normalize_text(value).lower().strip(" .:-|")
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
    if normalized.startswith(("to qualify for this offer", "to qualify for these offers")):
        return True
    if re.fullmatch(
        r"you can open (?:this |your )?account (?:online|in branch|at a branch)[^.]*",
        normalized,
    ):
        return True
    if (
        any(marker in normalized for marker in ("sign in to online banking", "sign on to online banking"))
        and any(marker in normalized for marker in ("add the ", "open the ", "apply for "))
        and "account" in normalized
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
    if "promotional rate" in normalized and "when you also open" in normalized:
        return True
    if normalized.startswith(("account fees learn tips", "with you as you grow")):
        return True
    if re.search(r"\bor in the case of\b[^.]{0,100}\bgic\b", normalized):
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

    profile = _semantic_product_profile(context)
    if profile == "chequing" and "savings account" in normalized and not any(
        marker in normalized for marker in ("chequing", "checking")
    ):
        return True
    if profile == "savings" and any(marker in normalized for marker in ("chequing account", "checking account")) and not any(
        marker in normalized for marker in ("savings", "interest rate")
    ):
        paired_account_context = any(
            marker in normalized
            for marker in ("pairs seamlessly", "paired with", "pair with", "linked to", "in one plan")
        )
        if not paired_account_context:
            return True
    return False


def _infer_product_type(context: ExtractionDocumentContext) -> str:
    raw_value = str(context.source_metadata.get("product_type", "")).strip().lower()
    return raw_value or "deposit"


def _infer_product_family(context: ExtractionDocumentContext) -> str:
    raw_value = str(context.source_metadata.get("product_family", "")).strip().lower().replace("_", "-")
    if raw_value in {"deposit", "lending"}:
        return raw_value
    product_type = _infer_product_type(context)
    if product_type in _CANONICAL_PRODUCT_TYPES or _canonical_product_type_family(product_type) is not None:
        return "deposit"
    if any(
        token in product_type
        for token in (
            "credit-card",
            "credit_card",
            "mortgage",
            "loan",
            "line-of-credit",
            "line_of_credit",
            "heloc",
        )
    ):
        return "lending"
    return "deposit"


def _uses_dynamic_product_type(context: ExtractionDocumentContext) -> bool:
    product_type = _infer_product_type(context)
    if product_type in _CANONICAL_PRODUCT_TYPES:
        return False
    discovery_role = str(context.source_metadata.get("discovery_role") or "").strip().lower()
    if discovery_role in {"supporting_html", "supporting_pdf", "linked_pdf", "entry"}:
        return False
    return bool(context.source_metadata.get("product_type_dynamic", True))


def _uses_official_ai_grounding(context: ExtractionDocumentContext) -> bool:
    discovery_role = str(context.source_metadata.get("discovery_role") or "detail").strip().lower()
    if discovery_role != "detail":
        return False
    return bool(_official_domain_allowlist(context))


def _official_domain_allowlist(context: ExtractionDocumentContext) -> list[str]:
    configured = context.source_metadata.get("official_domain_allowlist")
    values = list(configured) if isinstance(configured, (list, tuple, set)) else []
    values.extend(
        str(context.source_metadata.get(key) or "")
        for key in ("normalized_source_url", "source_url")
    )
    domains: list[str] = []
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
        host = (parsed.hostname or "").strip(".").lower()
        if host.startswith("www."):
            host = host[4:]
        if host and "." in host and host not in domains:
            domains.append(host)
    return domains[:20]


def _canonical_product_type_family(product_type: str | None) -> str | None:
    normalized = str(product_type or "").strip().lower()
    if normalized in _CANONICAL_PRODUCT_TYPES:
        return normalized
    if any(token in normalized for token in ("gic", "term-deposit", "term_deposit", "term deposit")):
        return "gic"
    if "savings" in normalized or "saving" in normalized:
        return "savings"
    if "chequing" in normalized or "checking" in normalized:
        return "chequing"
    return None


def _source_metadata_title_candidates(context: ExtractionDocumentContext) -> list[str]:
    candidates: list[str] = []
    if context.source_id in _BMO_SAVINGS_SOURCE_TITLES:
        candidates.append(_BMO_SAVINGS_SOURCE_TITLES[context.source_id])
    if context.source_id in _CIBC_SAVINGS_SOURCE_TITLES:
        candidates.append(_CIBC_SAVINGS_SOURCE_TITLES[context.source_id])
    for key in ("product_name", "source_name", "source_title", "page_title", "primary_heading"):
        value = str(context.source_metadata.get(key) or "").strip()
        if value:
            candidates.append(value)
    discovery_metadata = context.source_metadata.get("discovery_metadata")
    if isinstance(discovery_metadata, dict):
        for key in ("primary_heading", "page_title"):
            value = str(discovery_metadata.get(key) or "").strip()
            if value:
                candidates.append(value)
    return candidates


def _is_noise_for_product_context(*, context: ExtractionDocumentContext, text: str) -> bool:
    profile = _semantic_product_profile(context)
    if profile is None:
        return False
    lowered = text.lower()
    profile_hits = _profile_keyword_hits(profile=profile, text=lowered)
    if profile in {"chequing", "savings"} and profile_hits == 0 and any(
        marker in lowered
        for marker in (
            "stock and etf",
            "stock trading",
            "online trading",
            "investor's edge",
            "mutual fund",
            "portfolio management",
            "management expense ratio",
        )
    ):
        return True
    if not _is_cross_product_navigation_noise(text):
        return False
    conflict_hits = sum(1 for token in _PRODUCT_PROFILE_CONFLICT_KEYWORDS.get(profile, ()) if token in lowered)
    if conflict_hits >= 2:
        return True
    return conflict_hits > profile_hits


def _is_cross_product_navigation_noise(text: str) -> bool:
    lowered = text.lower()
    marker_hits = sum(1 for marker in _NAVIGATION_NOISE_MARKERS if marker in lowered)
    product_category_hits = sum(
        1
        for category in ("chequing", "savings", "credit cards", "mortgages", "loans", "investing")
        if category in lowered
    )
    return marker_hits >= 2 and product_category_hits >= 3


def _is_generic_banking_info_text(text: str) -> bool:
    normalized = _normalize_text(text)
    lowered = normalized.lower()
    marker_hits = sum(1 for marker in _GENERIC_BANKING_INFO_MARKERS if marker in lowered)
    if lowered.startswith("important banking info"):
        return True
    has_product_signal = any(
        token in lowered
        for token in (
            "$",
            "%",
            "monthly fee",
            "minimum balance",
            "unlimited transactions",
            "interac",
            "chequing account",
            "savings account",
        )
    )
    return marker_hits >= 2 and not has_product_signal


def _description_conflicts_with_product_context(*, context: ExtractionDocumentContext, description: str) -> bool:
    if not description:
        return False
    profile = _semantic_product_profile(context)
    if profile is None:
        return False
    lowered = description.lower()
    if _profile_keyword_hits(profile=profile, text=lowered):
        return False
    if profile == "savings" and any(
        marker in lowered for marker in ("pairs seamlessly", "paired with", "pair with", "linked to", "in one plan")
    ):
        return False
    return any(token in lowered for token in _PRODUCT_PROFILE_CONFLICT_KEYWORDS.get(profile, ()))


def _title_conflicts_with_product_context(*, context: ExtractionDocumentContext, title: str) -> bool:
    profile = _semantic_product_profile(context)
    if profile is None:
        return False
    lowered = title.lower()
    if _profile_keyword_hits(profile=profile, text=lowered):
        return False
    return any(token in lowered for token in _PRODUCT_PROFILE_CONFLICT_KEYWORDS.get(profile, ()))


def _semantic_product_profile(context: ExtractionDocumentContext) -> str | None:
    merged = " ".join(
        str(item or "")
        for item in (
            context.source_metadata.get("product_type"),
            context.source_metadata.get("product_type_name"),
            context.source_metadata.get("product_type_description"),
            " ".join(str(keyword) for keyword in context.source_metadata.get("discovery_keywords", []) or []),
        )
    ).lower()
    if any(token in merged for token in ("gic", "term deposit", "guaranteed investment certificate")):
        return "gic"
    if any(token in merged for token in ("savings", "saving account", "interest savings")):
        return "savings"
    if any(token in merged for token in ("chequing", "checking", "bank account", "transaction account")):
        return "chequing"
    return None


def _profile_keyword_hits(*, profile: str, text: str) -> int:
    if profile == "gic":
        return sum(1 for token in ("gic", "term deposit", "guaranteed investment certificate") if token in text)
    if profile == "savings":
        return sum(1 for token in ("savings", "saving account", "interest rate") if token in text)
    if profile == "chequing":
        return sum(1 for token in ("chequing", "checking", "transaction") if token in text)
    return 0


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


def _extract_official_fields_with_ai(
    *,
    context: ExtractionDocumentContext,
    candidates: list[EvidenceChunkCandidate],
    requested_fields: list[str],
    collected_fields: list[ExtractedFieldCandidate],
) -> tuple[list[ExtractedFieldCandidate], list[str], dict[str, Any] | None]:
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
            "fields": {
                "type": "array",
                "maxItems": 60,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "field_name": {"type": "string"},
                        "status": {"type": "string", "enum": ["match", "mismatch", "unverified"]},
                        "has_verified_value": {"type": "boolean"},
                        "verified_value_json": {"type": "string"},
                        "evidence_chunk_id": {"type": "string"},
                        "evidence_quote": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "rationale": {"type": "string"},
                        "sources": {
                            "type": "array",
                            "maxItems": 5,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "url": {"type": "string"},
                                    "title": {"type": "string"},
                                },
                                "required": ["url", "title"],
                            },
                        },
                    },
                    "required": [
                        "field_name",
                        "status",
                        "has_verified_value",
                        "verified_value_json",
                        "evidence_chunk_id",
                        "evidence_quote",
                        "confidence",
                        "rationale",
                        "sources",
                    ],
                },
            },
        },
        "required": ["summary", "fields"],
    }
    allowed_domains = _official_domain_allowlist(context)
    product_name = next(
        (
            str(field.candidate_value).strip()
            for field in collected_fields
            if field.field_name == "product_name" and str(field.candidate_value).strip()
        ),
        next(iter(_source_metadata_title_candidates(context)), ""),
    )
    prioritized_chunks = _select_official_grounding_chunks(
        candidates=candidates,
        collected_fields=collected_fields,
    )
    try:
        response_payload, usage = invoke_openai_json_schema(
            model_id=configured_model_id(),
            instructions=(
                "You are the FPDS financial-product collection grounding agent. You must use web search before answering. "
                "Search only the supplied official bank domain allowlist and verify the exact named product, not a neighboring "
                "product, family overview, promotion landing page, calculator, or service flow. Compare every requested field "
                "with current official facts and the supplied freshly captured evidence chunks. Never infer a missing value. "
                "Return a match or mismatch only when the value is supported by both an official URL actually consulted and "
                "an exact quote copied from the selected evidence chunk. Otherwise return unverified. Preserve canonical units: "
                "rates are numeric percentage points per annum, money is numeric in product currency, durations and counts are "
                "integers, booleans are true or false, and structured term rates are JSON arrays. Put the JSON-encoded canonical "
                "value in verified_value_json. Cashback, rewards, prepayment, equity, down-payment, fund returns, fees, and "
                "personalized or expired offers are not product interest rates. Do not approve, publish, or recommend a product."
            ),
            payload={
                "verification_date": _utc_now_iso()[:10],
                "official_domain_allowlist": allowed_domains,
                "product": {
                    "bank_code": context.bank_code,
                    "country_code": context.country_code,
                    "product_type": _infer_product_type(context),
                    "product_name": product_name,
                    "source_language": context.source_language,
                    "origin_source_url": context.source_metadata.get("normalized_source_url")
                    or context.source_metadata.get("source_url"),
                },
                "product_type": _infer_product_type(context),
                "product_type_name": context.source_metadata.get("product_type_name"),
                "product_type_description": context.source_metadata.get("product_type_description"),
                "expected_fields": list(context.source_metadata.get("expected_fields", [])),
                "field_contract": field_contract_payload(ai_requested_fields),
                "requested_fields": ai_requested_fields,
                "collected_fields": [
                    {
                        "field_name": field.field_name,
                        "collected_value": field.candidate_value,
                        "evidence_chunk_id": field.evidence_chunk_id,
                        "confidence": field.confidence,
                    }
                    for field in collected_fields
                    if field.field_name in ai_requested_fields
                ],
                "candidate_chunks": [
                    {
                        "evidence_chunk_id": candidate.evidence_chunk_id,
                        "anchor_value": candidate.anchor_value,
                        "excerpt": candidate.evidence_excerpt[:1800],
                    }
                    for candidate in prioritized_chunks
                ],
            },
            schema_name="collection_official_product_grounding",
            schema=schema,
            web_search_allowed_domains=allowed_domains,
            require_web_search=True,
        )
    except Exception as exc:
        return [], [f"Official product grounding was unavailable; collection kept evidence-first extraction: {exc}"], None

    provider_sources = _filter_official_web_sources(
        list(usage.get("web_search_sources") or []),
        allowed_domains=allowed_domains,
    )
    provider_source_by_url = {item["url"]: item for item in provider_sources}
    extracted_fields: list[ExtractedFieldCandidate] = []
    seen_fields: set[str] = set()
    for item in response_payload.get("fields", []):
        field_name = str(item.get("field_name") or "").strip()
        if field_name in seen_fields:
            continue
        seen_fields.add(field_name)
        evidence_chunk_id = str(item.get("evidence_chunk_id") or "").strip()
        if field_name not in ai_requested_fields or evidence_chunk_id not in candidate_map:
            continue
        if str(item.get("status") or "unverified") not in {"match", "mismatch"}:
            continue
        if not bool(item.get("has_verified_value")):
            continue
        candidate = candidate_map[evidence_chunk_id]
        evidence_quote = str(item.get("evidence_quote") or "").strip()
        if not _exact_quote_is_grounded(quote=evidence_quote, excerpt=candidate.evidence_excerpt):
            continue
        cited_sources = _validated_field_sources(
            item.get("sources"),
            provider_source_by_url=provider_source_by_url,
            allowed_domains=allowed_domains,
        )
        if not cited_sources:
            continue
        try:
            verified_value = json.loads(str(item.get("verified_value_json") or ""))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        candidate_value = _coerce_ai_candidate_value(
            field_name=field_name,
            value=_json_value_for_coercion(verified_value),
            value_type=canonical_value_type(field_name),
        )
        if candidate_value is None:
            continue
        extracted_fields.append(
            ExtractedFieldCandidate(
                field_name=field_name,
                candidate_value=candidate_value,
                value_type=canonical_value_type(field_name, str(item.get("value_type") or "string")),
                confidence=round(min(0.99, max(0.5, float(item.get("confidence") or 0.75))), 4),
                extraction_method="openai_official_grounding",
                source_document_id=context.source_document_id,
                source_snapshot_id=context.snapshot_id,
                evidence_chunk_id=candidate.evidence_chunk_id,
                evidence_text_excerpt=candidate.evidence_excerpt,
                anchor_type=candidate.anchor_type,
                anchor_value=candidate.anchor_value,
                page_no=candidate.page_no,
                chunk_index=candidate.chunk_index,
                field_metadata={
                    "official_grounding_contract_version": "collection-official-grounding-v1",
                    "official_verification_status": str(item.get("status")),
                    "official_web_sources": cited_sources,
                    "evidence_quote": evidence_quote[:500],
                    "rationale": str(item.get("rationale") or "")[:600],
                    "dynamic_product_type": _uses_dynamic_product_type(context),
                },
            )
        )
    notes = []
    summary = str(response_payload.get("summary") or "").strip()
    if summary:
        notes.append(summary)
    if extracted_fields:
        notes.append(
            f"Official-domain AI grounding verified or corrected {len(extracted_fields)} evidence-linked field candidate(s)."
        )
    usage = {
        **usage,
        "web_search_sources": provider_sources,
        "official_domain_allowlist": allowed_domains,
    }
    return extracted_fields, notes, usage


def _select_official_grounding_chunks(
    *,
    candidates: list[EvidenceChunkCandidate],
    collected_fields: list[ExtractedFieldCandidate],
) -> list[EvidenceChunkCandidate]:
    candidate_by_id = {candidate.evidence_chunk_id: candidate for candidate in candidates}
    selected: list[EvidenceChunkCandidate] = []
    seen: set[str] = set()
    for field in collected_fields:
        evidence_chunk_id = str(field.evidence_chunk_id or "")
        candidate = candidate_by_id.get(evidence_chunk_id)
        if candidate is None or evidence_chunk_id in seen:
            continue
        selected.append(candidate)
        seen.add(evidence_chunk_id)
    for candidate in candidates:
        if candidate.evidence_chunk_id in seen:
            continue
        selected.append(candidate)
        seen.add(candidate.evidence_chunk_id)
        if len(selected) >= 24:
            break
    return selected[:24]


def _filter_official_web_sources(
    sources: list[object],
    *,
    allowed_domains: list[str],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            continue
        url = _canonical_official_source_url(source.get("url"))
        if (
            not url
            or url in seen
            or not _url_matches_official_domains(url, allowed_domains=allowed_domains)
        ):
            continue
        seen.add(url)
        output.append(
            {
                "url": url,
                "title": _normalize_text(str(source.get("title") or url))[:300],
            }
        )
    return output[:100]


def _validated_field_sources(
    value: object,
    *,
    provider_source_by_url: dict[str, dict[str, str]],
    allowed_domains: list[str],
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    output: list[dict[str, str]] = []
    seen: set[str] = set()
    for source in value[:5]:
        if not isinstance(source, dict):
            continue
        url = _canonical_official_source_url(source.get("url"))
        provider_source = provider_source_by_url.get(url)
        if (
            provider_source is None
            or url in seen
            or not _url_matches_official_domains(url, allowed_domains=allowed_domains)
        ):
            continue
        seen.add(url)
        output.append(provider_source)
    return output


def _url_matches_official_domains(url: str, *, allowed_domains: list[str]) -> bool:
    host = (urlsplit(url).hostname or "").lower().strip(".")
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)


def _canonical_official_source_url(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlsplit(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


def _exact_quote_is_grounded(*, quote: str, excerpt: str) -> bool:
    normalized_quote = _normalize_text(quote).casefold()
    normalized_excerpt = _normalize_text(excerpt).casefold()
    return len(normalized_quote) >= 8 and normalized_quote in normalized_excerpt


def _json_value_for_coercion(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def _ai_candidate_value_is_contract_safe(*, field_name: str, value: object) -> bool:
    contract = field_contract(field_name)
    if contract is None:
        return True
    if contract.value_type == "decimal":
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return False
        if not decimal_value.is_finite():
            return False
        if decimal_value < 0:
            return False
        if contract.unit == "percentage_points":
            max_rate = Decimal("25") if field_name in _AI_SAFE_RATE_FIELDS else Decimal("100")
            if decimal_value >= max_rate:
                return False
        if field_name in _AI_SAFE_MONTHLY_FEE_FIELDS and decimal_value > Decimal("500"):
            return False
    if contract.value_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0
    if contract.value_type == "boolean":
        return isinstance(value, bool)
    if contract.value_type == "json" and field_name == "term_rate_table":
        return isinstance(value, list)
    if contract.value_type == "string":
        return isinstance(value, str) and bool(value.strip())
    return True


def _coerce_ai_candidate_value(*, field_name: str, value: str, value_type: str) -> object | None:
    normalized = value.strip()
    if not normalized:
        return None
    value_type = canonical_value_type(field_name, value_type)
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
    if value_type == "json":
        try:
            return json.loads(normalized)
        except json.JSONDecodeError:
            return None
    return _normalize_text(normalized)[:280]


def _infer_currency(*, context: ExtractionDocumentContext) -> str:
    raw_currency = str(context.source_metadata.get("currency", "")).strip().upper()
    if re.fullmatch(r"[A-Z]{3}", raw_currency):
        return raw_currency

    discovery_metadata = context.source_metadata.get("discovery_metadata")
    discovery_values: tuple[object, ...] = ()
    if isinstance(discovery_metadata, dict):
        discovery_values = (
            discovery_metadata.get("primary_heading"),
            discovery_metadata.get("page_title"),
            discovery_metadata.get("resolved_url"),
        )

    context_text = " ".join(
        str(item or "")
        for item in (
            context.source_metadata.get("product_name"),
            context.source_metadata.get("source_name"),
            context.source_metadata.get("source_title"),
            context.source_metadata.get("url"),
            context.source_metadata.get("source_url"),
            context.source_id,
            *discovery_values,
        )
    ).lower()
    currency_markers = {
        "USD": (
            "u.s. dollar",
            "u s dollar",
            "us dollar",
            "us$",
            "u.s.$",
            "usd",
            "us-dollar",
            "us-prem-savings",
            "us premium savings",
            "bmo-sav-005",
        ),
        "EUR": ("euro account", "euro savings", "euro esavings", "euro deposit", " eur ", "/euro-", "-eur-"),
        "GBP": ("british pound", "pound esavings", "pound sterling", "gbp", "sterling account"),
        "HKD": ("hong kong dollar", "hkd"),
        "CNY": ("chinese yuan", "renminbi", "cny", "rmb account"),
        "JPY": ("japanese yen", "jpy", "yen account"),
    }
    padded_context = f" {context_text} "
    for currency_code, markers in currency_markers.items():
        if any(marker in padded_context for marker in markers):
            return currency_code
    if re.search(r"\bu\.?s\.?(?:\s+|[-_/]).{0,30}\b(?:savings|account|deposit)\b", context_text):
        return "USD"
    return default_currency_for_country(context.country_code) or "XXX"


def _extract_money_value(
    *,
    context: ExtractionDocumentContext,
    field_name: str,
    text: str,
    lowered: str,
) -> str | None:
    if field_name in {"monthly_fee", "public_display_fee"}:
        if (
            "overdraft protection" in lowered
            and any(token in lowered for token in ("monthly fixed fee", "overdraft fee", "service fee"))
            and not any(token in lowered for token in ("account monthly fee", "monthly account fee", "monthly plan fee"))
        ):
            return None
        has_no_monthly_fee = bool(
            re.search(r"\bno[-\s]+monthly(?:[-\s]+(?:plan|account))?[-\s]+fees?\b", lowered)
            or any(token in lowered for token in ("monthly fee: $0", "monthly fee\n$0"))
        )
        if has_no_monthly_fee and not _is_conditional_no_fee_offer(lowered, context=context):
            return "0.00"
        standard_monthly_fee = _extract_standard_monthly_fee(text)
        if standard_monthly_fee is not None:
            return standard_monthly_fee
        identity_monthly_fee = _extract_identity_scoped_monthly_fee(context=context, text=text)
        if identity_monthly_fee is not None:
            return identity_monthly_fee
        product_monthly_fee = _extract_bmo_chequing_product_monthly_fee(context=context, text=text)
        if product_monthly_fee is not None:
            return product_monthly_fee
        monthly_fee = _extract_monthly_fee_with_minimum_balance_waiver(text)
        if monthly_fee is not None:
            return monthly_fee
        if has_no_monthly_fee:
            return None
        labeled_fee = _extract_money_near_labels(
            text=text,
            label_patterns=(
                r"monthly\s+(?:(?:plan|account)\s+)?fees?",
                r"plan\s+fees?",
            ),
        )
        if (
            labeled_fee is not None
            and Decimal(labeled_fee) == 0
            and _is_conditional_no_fee_offer(lowered, context=context)
        ):
            return None
        if labeled_fee is not None and _money_value_has_non_fee_context(
            value=labeled_fee,
            context=lowered,
        ):
            labeled_fee = None
        if labeled_fee is not None and Decimal(labeled_fee) < Decimal("500"):
            return labeled_fee
        if _matches_zero_money_label(
            text=text,
            label_patterns=(
                r"monthly\s+(?:(?:plan|account)\s+)?fees?",
                r"plan\s+fees?",
            ),
        ):
            if _is_conditional_no_fee_offer(lowered, context=context):
                return None
            return "0.00"
        return None

    if field_name == "minimum_balance":
        product_minimum_balance = _extract_bmo_chequing_product_minimum_balance(context=context, text=text)
        if product_minimum_balance is not None:
            return product_minimum_balance
        waiver_balance = _extract_minimum_balance_for_fee_waiver(context=context, text=text)
        if waiver_balance is not None:
            return waiver_balance
        if _has_no_minimum_balance(lowered):
            return "0.00"
        if _has_bmo_chequing_other_product_fee_waiver(context=context, text=text):
            return None
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
                r"minimum\s+investment",
                r"opening\s+deposit",
                r"initial\s+deposit",
            ),
        ):
            return "0.00"
        reversed_label_match = re.search(
            r"(?:minimum(?:\s+of)?\s+\$\s*(?P<leading>\d[\d,]*(?:\.\d{1,2})?)\s+(?:deposit|investment)"
            r"|\$\s*(?P<trailing>\d[\d,]*(?:\.\d{1,2})?)\s+minimum\s+(?:deposit|investment))",
            text,
            flags=re.IGNORECASE,
        )
        if reversed_label_match is not None:
            return _normalize_decimal((reversed_label_match.group("leading") or reversed_label_match.group("trailing")).replace(",", ""))
        as_little_as_match = re.search(
            r"\b(?:start|open|invest)\b[^$€£]{0,60}?\bas\s+little\s+as\s+[$€£]\s*"
            r"(?P<amount>\d[\d,]*(?:\.\d{1,2})?)",
            text,
            flags=re.IGNORECASE,
        )
        if as_little_as_match is not None:
            return _normalize_decimal(as_little_as_match.group("amount").replace(",", ""))
        return _extract_money_near_labels(
            text=text,
            label_patterns=(
                r"minimum\s+opening\s+deposit",
                r"minimum\s+deposit",
                r"minimum\s+investment",
                r"opening\s+deposit",
                r"initial\s+deposit",
            ),
        )

    return None


def _extract_monthly_fee_with_minimum_balance_waiver(text: str) -> str | None:
    inline_values = _extract_inline_or_zero_balance_waiver_values(text)
    if inline_values is not None:
        return inline_values[0]
    match = _fee_waiver_pattern().search(text)
    if match is not None:
        return _normalize_decimal(match.group("fee"))
    reverse_values = _extract_no_fee_if_balance_values(text)
    return reverse_values[0] if reverse_values is not None else None


def _extract_standard_monthly_fee(text: str) -> str | None:
    patterns = (
        r"standard\s+monthly\s+(?:account\s+)?fee(?:\s+for\s+[^.$]{0,100})?\s+(?:is|of|:)\s*\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)",
        r"monthly\s+(?:account\s+)?fee\s*:\s*\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)",
        r"\bmonthly\s+(?:account\s+)?fee\s+(?:is|of)\s*\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match is None:
            continue
        value = _normalize_decimal(match.group("fee"))
        if Decimal(value) <= Decimal("500"):
            return value
    return None


def _extract_minimum_balance_for_fee_waiver(*, context: ExtractionDocumentContext, text: str) -> str | None:
    inline_values = _extract_inline_or_zero_balance_waiver_values(text)
    if inline_values is not None:
        return inline_values[1]
    match = _fee_waiver_pattern().search(text)
    if match is None:
        rebated_values = _extract_rebated_fee_balance_values(text)
        if rebated_values is not None:
            return rebated_values[1]
        reverse_values = _extract_no_fee_if_balance_values(text)
        if reverse_values is not None:
            return reverse_values[1]
        return _extract_balance_from_waiver_language(text)
    if _is_bmo_chequing_other_product_fee_waiver(context=context, text=text, match=match):
        return None
    balance = match.group("balance_after_label") or match.group("balance_before_label")
    return _normalize_decimal(balance)


def _extract_fee_waiver_condition(*, context: ExtractionDocumentContext, text: str) -> str | None:
    temporal_condition = _extract_temporal_fee_waiver_condition(text)
    if temporal_condition is not None:
        return temporal_condition
    non_balance_condition = _extract_non_balance_fee_waiver_condition(text)
    if non_balance_condition is not None:
        return non_balance_condition
    inline_values = _extract_inline_or_zero_balance_waiver_values(text)
    if inline_values is not None:
        fee, balance = inline_values
        return f"Monthly fee {fee} is waived to 0.00 with a {balance} minimum balance."
    match = _fee_waiver_pattern().search(text)
    if match is None:
        rebated_values = _extract_rebated_fee_balance_values(text)
        if rebated_values is not None:
            fee, balance = rebated_values
            return f"Monthly fee {fee} is waived to 0.00 with a {balance} minimum balance."
        reverse_values = _extract_no_fee_if_balance_values(text)
        if reverse_values is None:
            return None
        fee, balance = reverse_values
        return f"Monthly fee {fee} is waived to 0.00 with a {balance} minimum balance."
    if _is_bmo_chequing_other_product_fee_waiver(context=context, text=text, match=match):
        return None
    fee = _normalize_decimal(match.group("fee"))
    balance = _normalize_decimal(match.group("balance_after_label") or match.group("balance_before_label"))
    return f"Monthly fee {fee} is waived to 0.00 with a {balance} minimum balance."


def _extract_non_balance_fee_waiver_condition(text: str) -> str | None:
    normalized = _normalize_text(text)
    match = re.search(
        r"(?:monthly\s+(?:account\s+)?fee\s*)?\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s*"
        r"\(\s*\$\s*0(?:\.00)?\s+if\s+(?P<condition>[^)]{10,700})\)",
        normalized,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    condition = _normalize_text(match.group("condition")).strip(" .")
    if not any(
        marker in condition.lower()
        for marker in (
            "guaranteed income supplement",
            "beneficiary",
            "registered disability savings plan",
            "indigenous",
            "newcomer",
            "receiving",
        )
    ):
        return None
    fee = _normalize_decimal(match.group("fee"))
    return f"Monthly fee {fee} is waived to 0.00 if {condition}."[:500]


def _extract_temporal_fee_waiver_condition(text: str) -> str | None:
    normalized = _normalize_text(text)
    duration = re.search(
        r"(?:\b(?:pay|get|enjoy|receive)?\s*(?:a\s+)?no[- ]monthly(?:[- ]+(?:plan|account))?[- ]fee|"
        r"\$\s*0(?:\.00)?\s+monthly(?:\s+(?:plan|account))?\s+fee)\s+"
        r"for\s+(?:the\s+)?(?:first\s+)?(?P<count>\d{1,3}|one|two|three|six|twelve)\s+"
        r"(?P<unit>months?|years?)\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if duration is not None:
        count = duration.group("count").lower()
        unit = duration.group("unit").lower()
        return f"Monthly fee is waived for {count} {unit}."
    age = re.search(
        r"\bno[- ]monthly(?:[- ]+(?:plan|account))?[- ]fee\s+until\s+(?:the\s+)?age\s+(?:of\s+)?(?P<age>\d{1,3})\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if age is not None:
        return f"Monthly fee is waived until age {age.group('age')}."
    study = re.search(
        r"\b(?:continue\s+to\s+)?pay\s+no\s+monthly(?:\s+(?:plan|account))?\s+fee\s+"
        r"for\s+as\s+long\s+as\s+you\s+study\s+full[- ]time\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if study is not None:
        return "Monthly fee is waived while studying full-time."
    return None


def _extract_bmo_chequing_product_monthly_fee(*, context: ExtractionDocumentContext, text: str) -> str | None:
    product_hint = _BMO_CHEQUING_SOURCE_HINTS.get(context.source_id)
    segment = _extract_bmo_chequing_product_segment(context=context, text=text)
    if product_hint is None or segment is None:
        return None
    patterns = (
        rf"\b{re.escape(product_hint)}\b[\s\S]{{0,120}}?\$\s?(?P<fee>[0-9][0-9,]*(?:\.\d{{1,2}})?)\s*(?:per\s+month|/month|monthly)\b",
        rf"\b{re.escape(product_hint)}\b[\s\S]{{0,180}}?monthly\s+(?:(?:plan|account)\s+)?fee[\s\S]{{0,40}}?\$\s?(?P<fee>[0-9][0-9,]*(?:\.\d{{1,2}})?)",
    )
    for pattern in patterns:
        match = re.search(pattern, segment, flags=re.IGNORECASE)
        if match is None:
            continue
        value = _normalize_decimal(match.group("fee"))
        if Decimal(value) <= Decimal("500"):
            return value
    return None


def _is_conditional_no_fee_offer(
    lowered_text: str,
    *,
    context: ExtractionDocumentContext | None = None,
) -> bool:
    """Identify a waived/promotional zero rather than the account's base fee."""

    if re.search(r"\bfor\s+(?:the\s+)?(?:first\s+)?(?:\d+|one|two|three|six|twelve)\s+(?:months?|years?)\b", lowered_text):
        return True
    audience_match = re.search(r"\b(?:newcomers?|students?|kids?|teens?|youth|seniors?|indigenous|defen[cs]e)\b", lowered_text)
    if audience_match is not None and not _source_identity_contains_audience(context=context, audience=audience_match.group(0)):
        return True
    if re.search(
        r"\bno\s+monthly(?:\s+(?:plan|account))?\s+fees?\s+(?:if|when|provided|provided\s+that)\b",
        lowered_text,
    ):
        return True
    if re.search(
        r"\bno\s+monthly(?:\s+(?:plan|account))?\s+fees?\s+with\s+(?:an?\s+)?"
        r"minimum(?:\s+daily(?:\s+closing)?)?\s+(?:account\s+)?balance\b",
        lowered_text,
    ):
        return True
    if re.search(
        r"\$\s*\d[\d,]*(?:\.\d{1,2})?\s+or\s+\$\s*0(?:\.00)?[\s\S]{0,100}?"
        r"\bminimum\s+(?:daily\s+)?(?:account\s+)?balance\b",
        lowered_text,
    ):
        return True
    return any(
            marker in lowered_text
            for marker in (
                "eligible for no monthly fee",
                "fee rebate",
                "monthly fee rebate",
                "fee is waived",
                "fee waived",
                "waive the monthly",
                "welcome offer",
                "limited-time offer",
            )
        )


def _source_identity_contains_audience(*, context: ExtractionDocumentContext | None, audience: str) -> bool:
    if context is None:
        return False
    normalized_audience = audience.lower()
    audience_aliases = {
        "kid": ("kid", "teen", "youth", "under 25", "under-25"),
        "teen": ("kid", "teen", "youth", "under 25", "under-25"),
        "youth": ("kid", "teen", "youth", "under 25", "under-25"),
        "student": ("student",),
        "newcomer": ("newcomer", "new to canada", "foreign worker"),
        "senior": ("senior",),
        "indigenous": ("indigenous",),
        "defence": ("defence", "defense", "military"),
        "defense": ("defence", "defense", "military"),
    }
    alias_key = next((key for key in audience_aliases if normalized_audience.startswith(key)), normalized_audience)
    aliases = audience_aliases.get(alias_key, (normalized_audience,))
    discovery_metadata = context.source_metadata.get("discovery_metadata")
    discovery_values = discovery_metadata.values() if isinstance(discovery_metadata, dict) else ()
    identity = " ".join(
        str(value or "")
        for value in (
            context.source_metadata.get("product_name"),
            context.source_metadata.get("source_name"),
            context.source_metadata.get("source_title"),
            context.source_metadata.get("page_title"),
            context.source_metadata.get("primary_heading"),
            context.source_metadata.get("url"),
            context.source_metadata.get("source_url"),
            *discovery_values,
        )
    ).lower()
    return any(alias in identity for alias in aliases)


def _extract_balance_from_waiver_language(text: str) -> str | None:
    normalized = _normalize_text(text)
    patterns = (
        r"\b(?:keep|maintain|hold(?:ing)?)(?:\s+and\s+maintain)?[^$€£]{0,60}?(?:at\s+least\s+)?[$€£]\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)[\s\S]{0,100}?\bwaiv(?:e|ed|es|ing)\b[^.]{0,40}?\bmonthly\b[^.]{0,20}?\bfee\b",
        r"\bwaiv(?:e|ed|es|ing)\b[^.]{0,40}?\bmonthly\b[^.]{0,20}?\bfee\b[\s\S]{0,140}?\b(?:keep|maintain|hold(?:ing)?)[^$€£]{0,60}?[$€£]\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)",
        r"\bpay\s+no\s+monthly\s+(?:account\s+)?fees?\b[\s\S]{0,100}?\b(?:keep|maintain|hold(?:ing)?)[^$€£]{0,60}?[$€£]\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match is not None:
            return _normalize_decimal(match.group("balance"))
    return None


def _extract_identity_scoped_monthly_fee(*, context: ExtractionDocumentContext, text: str) -> str | None:
    """Prefer a recurring fee stated next to the target product identity."""

    lowered = text.lower()
    for identity in _source_product_identity_terms(context):
        position = lowered.find(identity)
        if position < 0:
            continue
        segment = text[position : position + 220]
        for pattern in (
            r"\bmonthly\s+(?:(?:plan|account)\s+)?fees?\b[^$]{0,50}?\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)",
            r"\bmonthly\s+(?:plan\s+)?fees?\s+of\s+\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)",
            r"\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s*(?:per\s+month|/\s*month|monthly)\b",
        ):
            match = re.search(pattern, segment, flags=re.IGNORECASE)
            if match is None:
                continue
            if any(marker in match.group(0).lower() for marker in ("discount", "rebate", "refund", "reimburse")):
                continue
            value = _normalize_decimal(match.group("fee"))
            if _money_value_has_non_fee_context(value=value, context=segment.lower()):
                continue
            if Decimal(value) < Decimal("500"):
                return value
    return None


def _money_value_has_non_fee_context(*, value: object, context: str) -> bool:
    try:
        expected = Decimal(str(value).replace(",", "").strip())
    except InvalidOperation:
        return False
    for match in re.finditer(r"\$\s*(\d[\d,]*(?:\.\d{1,2})?)", context):
        try:
            observed = Decimal(match.group(1).replace(",", ""))
        except InvalidOperation:
            continue
        if observed != expected:
            continue
        window = context[max(0, match.start() - 90) : min(len(context), match.end() + 90)]
        if re.search(r"\b(?:get|earn|receive)\s+\$\s*\d[\d,]*(?:\.\d{1,2})?\s+cash\b", window):
            return True
        if any(
            marker in window
            for marker in (
                "welcome bonus",
                "cash bonus",
                "additional bonus",
                "fee discount",
                "monthly account fee discount",
                "monthly fee discount",
                "fee rebate",
                "fee refund",
                "fee reimbursement",
                "gift card",
                "direct deposit",
                "eligible deposit",
                "purchase",
                "spend $",
            )
        ):
            return True
    return False


def _has_no_minimum_balance(lowered_text: str) -> bool:
    normalized = lowered_text.replace("’", "'")
    normalized = normalized.replace("‘", "'").replace("ʼ", "'").replace("´", "'")
    return bool(
        any(token in normalized for token in ("no minimum balance", "no minimum daily balance"))
        or re.search(
            r"\b(?:do|does)(?:\s+not|n't)\s+need\s+to\s+(?:keep|maintain|have)\s+(?:a\s+)?minimum(?:\s+daily)?\s+balance\b",
            normalized,
        )
        or re.search(r"\bthere(?:'s|\s+is)\s+no\s+minimum(?:\s+daily)?\s+balance\b", normalized)
    )


def _extract_bmo_chequing_product_minimum_balance(*, context: ExtractionDocumentContext, text: str) -> str | None:
    segment = _extract_bmo_chequing_product_segment(context=context, text=text)
    if segment is None:
        return None
    for match in re.finditer(
        r"\$\s?(?P<balance>[0-9][0-9,]*(?:\.\d{1,2})?)[^$]{0,80}?"
        r"(?:minimum\s+daily\s+balance|minimum\s+balance)",
        segment,
        flags=re.IGNORECASE,
    ):
        return _normalize_decimal(match.group("balance"))
    match = re.search(
        r"(?:minimum\s+daily\s+balance|minimum\s+balance)[\s\S]{0,80}?"
        r"\$\s?(?P<balance>[0-9][0-9,]*(?:\.\d{1,2})?)",
        segment,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    return _normalize_decimal(match.group("balance"))


def _extract_bmo_chequing_product_segment(*, context: ExtractionDocumentContext, text: str) -> str | None:
    current_hint = _BMO_CHEQUING_SOURCE_HINTS.get(context.source_id)
    if current_hint is None:
        return None
    current_match = _find_bmo_chequing_product_hint(text=text, hint=current_hint)
    if current_match is None:
        return None
    segment_end = len(text)
    for hint in set(_BMO_CHEQUING_SOURCE_HINTS.values()) - {current_hint}:
        other_match = _find_bmo_chequing_product_hint(text=text[current_match.end() :], hint=hint)
        if other_match is not None:
            segment_end = min(segment_end, current_match.end() + other_match.start())
    return text[current_match.start() : segment_end]


def _find_bmo_chequing_product_hint(*, text: str, hint: str) -> re.Match[str] | None:
    return re.search(
        rf"\b{re.escape(hint)}\b(?=\s*(?:chequing|account|\$))",
        text,
        flags=re.IGNORECASE,
    )


def _is_bmo_chequing_other_product_fee_waiver(
    *,
    context: ExtractionDocumentContext,
    text: str,
    match: re.Match[str],
) -> bool:
    current_product_hint = _BMO_CHEQUING_SOURCE_HINTS.get(context.source_id)
    if current_product_hint is None:
        return False
    before_window = text[max(0, match.start() - 64) : match.start()].lower()
    other_product_hints = {item for item in _BMO_CHEQUING_SOURCE_HINTS.values() if item != current_product_hint}
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
        r"[$€£]\s?(?P<fee>[0-9][0-9,]*(?:\.\d{1,2})?)(?:\s*(?:CAD|USD|EUR|GBP))?\s*"
        r"(?:(?:per\s+month|monthly)\s+)?or\s+[$€£]0(?:\.00)?(?:\s*/\s*month|\s+per\s+month)?"
        r"\s+with\s+(?:a\s+)?(?:(?:min\.?|minimum)\s+(?:daily\s+)?[$€£]\s?(?P<balance_after_label>[0-9][0-9,]*(?:\.\d{1,2})?)"
        r"(?:\s+balance)?|[$€£]\s?(?P<balance_before_label>[0-9][0-9,]*(?:\.\d{1,2})?)\s+"
        r"(?:minimum\s+(?:daily\s+)?balance|balance))",
        flags=re.IGNORECASE,
    )


def _extract_inline_or_zero_balance_waiver_values(text: str) -> tuple[str, str] | None:
    """Read a base fee and the balance-qualified zero shown in one disclosure."""

    match = re.search(
        r"\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s+or\s+\$\s*0(?:\.00)?\s*"
        r"\(?\s*with\s+(?:a\s+)?minimum\s+(?:daily\s+)?(?:account\s+)?balance"
        r"(?:\s+of)?\s+\$\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)",
        _normalize_text(text),
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    return (
        _normalize_decimal(match.group("fee")),
        _normalize_decimal(match.group("balance")),
    )


def _extract_rebated_fee_balance_values(text: str) -> tuple[str, str] | None:
    """Read a base fee followed by a separately worded balance rebate."""

    match = re.search(
        r"[$€£]\s?(?P<fee>[0-9][0-9,]*(?:\.\d{1,2})?)(?:\s*(?:CAD|USD|EUR|GBP))?\s*(?:per\s+month|monthly)?\s*"
        r"or\s+[$€£]0(?:\.00)?[\s,;:\-]{0,20}(?:monthly\s+)?(?:account\s+)?fee\s+"
        r"(?:is\s+)?(?:rebated|waived)[^$€£]{0,180}?[$€£]\s?(?P<balance>[0-9][0-9,]*(?:\.\d{1,2})?)",
        _normalize_text(text),
        flags=re.IGNORECASE,
    )
    if match is not None:
        return (_normalize_decimal(match.group("fee")), _normalize_decimal(match.group("balance")))

    # Some comparison/detail cards separate the displayed `$X or $0` fee from
    # the following sentence that explains how to waive it by holding a
    # balance. Keep the two facts together without requiring one bank's exact
    # punctuation or the word "rebated".
    normalized = _normalize_text(text)
    fee_match = re.search(
        r"\bmonthly\s+(?:(?:plan|account)\s+)?fees?\b[^$€£]{0,40}?"
        r"[$€£]\s?(?P<fee>[0-9][0-9,]*(?:\.\d{1,2})?)(?:\s*(?:CAD|USD|EUR|GBP))?\s*or\s*[$€£]0(?:\.00)?",
        normalized,
        flags=re.IGNORECASE,
    )
    balance = _extract_balance_from_waiver_language(normalized)
    if fee_match is None or balance is None:
        return None
    return (_normalize_decimal(fee_match.group("fee")), balance)


def _extract_no_fee_if_balance_values(text: str) -> tuple[str, str] | None:
    """Read fee waivers phrased as free-if-balanced, then state the base fee.

    Many bank pages lead with the waived price and place the actual monthly fee in
    a parenthetical.  Treating the first zero as the product fee reverses the
    economic meaning of the disclosure.
    """

    normalized = _normalize_text(text)
    if not re.search(r"\bno\s+monthly(?:\s+plan)?\s+fee\b", normalized, flags=re.IGNORECASE):
        return None
    balance_match = re.search(
        r"(?:minimum\s+(?:daily\s+(?:closing\s+)?)?balance(?:\s+of)?\s*\$\s?(?P<after>[0-9][0-9,]*(?:\.\d{1,2})?)"
        r"|\$\s?(?P<before>[0-9][0-9,]*(?:\.\d{1,2})?)\s+minimum\s+(?:daily\s+(?:closing\s+)?)?balance)",
        normalized,
        flags=re.IGNORECASE,
    )
    if balance_match is None:
        return None
    fee_match = re.search(
        r"\$\s?(?P<fee>[0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:/\s*month|per\s+month|monthly)\s+(?:plan\s+)?fee",
        normalized[balance_match.end() :],
        flags=re.IGNORECASE,
    )
    if fee_match is None:
        return None
    return (
        _normalize_decimal(fee_match.group("fee")),
        _normalize_decimal(balance_match.group("after") or balance_match.group("before")),
    )


def _matches_zero_money_label(*, text: str, label_patterns: tuple[str, ...]) -> bool:
    normalized_text = _normalize_text(text).lower()
    for label_pattern in label_patterns:
        if "fee" in label_pattern and any(
            marker in normalized_text
            for marker in ("as low as $0", "as low as 0", "after rebate", "monthly fee rebate")
        ):
            continue
        if "fee" in label_pattern and re.search(
            r"\bwaiv(?:e|ed|er|ing)?\b.{0,80}\b(?:if|when|with|minimum|eligible|maintain|balance)\b",
            normalized_text,
        ):
            continue
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
            rf"{label_pattern}[\s\S]{{0,80}}?[$€£]\s?([0-9][0-9,]*(?:\.\d{{1,2}})?)",
            text,
            flags=re.IGNORECASE,
        )
        if after_match is not None:
            intervening = text[after_match.start() : after_match.start(1)].lower()
            normalized_value = _normalize_decimal(after_match.group(1))
            if "fee" in label_pattern and (
                any(token in intervening for token in ("minimum balance", "daily closing balance", "waiv", "rebate", "discount", "refund", "reimburse", "credit", "direct deposit", "deposit", "gift card", "purchase", "spend"))
                or Decimal(normalized_value) > Decimal("500")
                or (Decimal(normalized_value) == 0 and any(marker in text.lower() for marker in ("as low as", "rebate")))
            ):
                pass
            else:
                return normalized_value

        label_match = re.search(label_pattern, text, flags=re.IGNORECASE)
        if label_match is None:
            continue
        before_window = text[max(0, label_match.start() - 80) : label_match.start()]
        money_matches = list(_MONEY_RE.finditer(before_window))
        if money_matches:
            trailing_context = before_window[money_matches[-1].end() :].lower()
            normalized_value = _normalize_decimal(money_matches[-1].group(1))
            if "fee" in label_pattern and (
                any(token in trailing_context for token in ("minimum balance", "daily closing balance", "waiv", "rebate", "discount", "refund", "reimburse", "credit", "annual", "direct deposit", "deposit", "gift card", "purchase", "spend", "or more"))
                or Decimal(normalized_value) > Decimal("500")
                or (Decimal(normalized_value) == 0 and any(marker in text.lower() for marker in ("as low as", "rebate")))
            ):
                continue
            return normalized_value
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
    for match in _PERCENT_RE.finditer(text):
        window = _rate_percentage_context_window(text=text, start=match.start(), end=match.end())
        if canonical_deposit_rate_suppression_reason(value=match.group(1), context=window) is not None:
            continue
        return _normalize_decimal(match.group(1))
    return None


def _extract_standard_rate_value(text: str) -> str | None:
    normalized = _normalize_text(text)
    for pattern in (
        r"\bthereafter\b\D{0,40}(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
        r"\bregular interest rate\b\D{0,50}(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
        r"(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%\s*[†*^]?\s*(?:annual\s+)?interest\s+rate\b",
        r"\b(?:our\s+)?rates?\s+(?:are|is)\s+(?:great\s+)?at\s+(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
        r"\binterest\s+rate\s+of\s+(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
    ):
        direct_match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if direct_match is not None:
            return _normalize_decimal(direct_match.group("rate"))
    for match in _PERCENT_RE.finditer(text):
        window = _rate_percentage_context_window(text=text, start=match.start(), end=match.end())
        lowered_window = window.lower()
        if canonical_deposit_rate_suppression_reason(value=match.group(1), context=window) is not None:
            continue
        if _is_promotional_rate_context(lowered_window) and not any(
            marker in lowered_window
            for marker in (
                "regular interest rate",
                "standard interest rate",
                "current annual interest rate",
                "base interest rate",
                "after the promotional period",
                "after the offer period",
            )
        ):
            continue
        return _normalize_decimal(match.group(1))
    return None


def _extract_promotional_rate_value(*, context: ExtractionDocumentContext, text: str) -> str | None:
    normalized = _normalize_text(text)
    for pattern in (
        r"\btotal interest rate including promo(?:tional)?(?: interest)?\b\D{0,80}(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
        r"\bearn\s+up\s+to\s+(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%\D{0,80}\b(?:first\s+\d+\s+months?|limited[- ]time)\b",
        r"\bearn\s+(?:a\s+)?savings rate of\s+(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%\D{0,80}\blimited[- ]time\b",
        r"\bpromotional interest rate\b\s*(?:would be|is|of|:)\s*(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
        r"\bfirst\s+\d{1,3}\s+(?:days?|months?)\b\D{0,40}(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
    ):
        direct_match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if direct_match is not None:
            return _normalize_decimal(direct_match.group("rate"))
    registered_product = _source_is_registered_product(context)
    lowered_normalized = normalized.lower()
    if (
        not registered_product
        and "registered promotional rate" in lowered_normalized
        and not re.search(r"\bnon[ -]?registered promotional rate\b", lowered_normalized)
    ):
        return None
    label_patterns = (
        (r"registered promotional rate",) if registered_product else
        (r"non[ -]?registered promotional rate", r"non[ -]?registered offer rate")
    )
    for label_pattern in label_patterns:
        match = re.search(
            rf"{label_pattern}.{{0,80}}?(?P<rate>\d{{1,2}}(?:\.\d{{1,4}})?)\s*%",
            normalized,
            flags=re.IGNORECASE,
        )
        if match is not None:
            return _normalize_decimal(match.group("rate"))
    return _extract_percent_value(text)


def _extract_public_display_rate_value(*, context: ExtractionDocumentContext, text: str) -> str | None:
    normalized = _normalize_text(text)
    if _has_product_promotional_context(context=context, text=text):
        promotional = _extract_promotional_rate_value(context=context, text=text)
        if promotional is not None:
            return promotional
    for pattern in (
        r"\bannual interest rate with bonus interest(?: rate)?\b\D{0,80}(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
        r"\b(?:earn|rate of)\s+up\s+to\s+(?P<rate>\d{1,2}(?:\.\d{1,4})?)\s*%",
    ):
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match is not None:
            return _normalize_decimal(match.group("rate"))
    return _extract_percent_value(text)


def _extract_boolean_flag(
    *,
    context: ExtractionDocumentContext,
    field_name: str,
    text: str,
    lowered: str,
    anchor_value: str | None,
) -> bool | None:
    anchor = (anchor_value or "").lower()
    if field_name == "introductory_rate_flag":
        if _has_product_promotional_context(context=context, text=text):
            return True
        return None
    if field_name == "tiered_rate_flag":
        if "tier" in lowered or "tier" in anchor:
            return True
        return None
    if field_name == "registered_flag":
        if any(token in lowered for token in ("tfsa", "rrsp", "registered")) and (
            _source_is_registered_product(context) or _has_registered_product_availability_context(lowered)
        ):
            return True
        return None
    if field_name == "redeemable_flag":
        if any(token in lowered for token in ("non-redeemable", "non redeemable", "non cashable", "non-cashable")):
            return False
        if _cashable_only_at_maturity(lowered):
            return False
        if any(token in lowered for token in ("redeemable", "cashable", "early redemption")):
            return True
        return None
    if field_name == "non_redeemable_flag":
        if any(token in lowered for token in ("non-redeemable", "non redeemable", "non cashable", "non-cashable")):
            return True
        if _cashable_only_at_maturity(lowered):
            return True
        if "redeemable" in lowered or "cashable" in lowered:
            return False
        return None
    if field_name == "registered_plan_supported":
        if _source_is_registered_product(context) or _has_registered_product_availability_context(lowered):
            return True
        return None
    if field_name == "unlimited_transactions_flag":
        if re.search(r"\bfor accounts? that (?:do|does) not (?:provide|include|offer|have)\s+unlimited\b", lowered):
            return None
        if re.search(
            r"\b(?:does?|do|will|may|are|is)\s+not\s+(?:provide|include|offer|have)?\s*unlimited\b",
            lowered,
        ) or re.search(r"\bnot\s+unlimited\b", lowered):
            return False
        if _has_account_wide_unlimited_transactions(lowered):
            return True
        if re.search(
            r"\b\d{1,3}\s+(?:free\s+|included\s+)?(?:debit\s+transactions?|debits|banking\s+transactions?|transactions?)"
            r"(?:\s+(?:of\s+any\s+kind|included))?(?:\s*(?:/|per)\s*month)?\b",
            lowered,
        ):
            return False
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
        has_plan_context = _has_student_plan_context(lowered=lowered, anchor=anchor)
        if has_plan_context and (
            _source_identity_has_audience(
                context=context,
                audience_terms=("student", "youth"),
            )
            or _excerpt_explicitly_links_current_product_to_audience(
                context=context,
                lowered=lowered,
                audience_terms=("student", "students", "youth", "24 and younger"),
            )
        ):
            return True
        return None
    if field_name == "newcomer_plan_flag":
        has_plan_context = _has_newcomer_plan_context(lowered=lowered, anchor=anchor)
        if has_plan_context and (
            _source_identity_has_audience(
                context=context,
                audience_terms=("newcomer", "new to canada"),
            )
            or _excerpt_explicitly_links_current_product_to_audience(
                context=context,
                lowered=lowered,
                audience_terms=("newcomer", "newcomers", "new to canada"),
            )
        ):
            return True
        return None
    return None


def _source_identity_has_audience(*, context: ExtractionDocumentContext, audience_terms: tuple[str, ...]) -> bool:
    identity_text = " ".join(
        str(value or "")
        for value in (
            *_source_metadata_title_candidates(context),
            context.source_metadata.get("product_key"),
            context.source_metadata.get("normalized_source_url"),
        )
    ).lower()
    return any(term in identity_text for term in audience_terms)


def _excerpt_explicitly_links_current_product_to_audience(
    *,
    context: ExtractionDocumentContext,
    lowered: str,
    audience_terms: tuple[str, ...],
) -> bool:
    """Accept explicit current-product audience benefits without sibling-card leakage."""

    identity_text = " ".join(_source_metadata_title_candidates(context)).lower()
    requested_newcomer = any(term in {"newcomer", "newcomers", "new to canada"} for term in audience_terms)
    requested_student = any(term in {"student", "students", "youth", "24 and younger"} for term in audience_terms)
    identity_has_newcomer = any(term in identity_text for term in ("newcomer", "new to canada"))
    identity_has_student = any(term in identity_text for term in ("student", "youth"))
    if requested_newcomer and identity_has_student and not identity_has_newcomer:
        return False
    if requested_student and identity_has_newcomer and not identity_has_student:
        return False
    if (
        re.search(
            r"\b(?:means|includes?)\s+(?:any\s+of\s+)?(?:the\s+)?following\s+accounts?\b",
            lowered,
        )
        and any(term in lowered for term in audience_terms)
        and any(marker in lowered for marker in ("offer eligibility", "offer exclusions", "package bonus"))
    ):
        # Long legal chunks can place the audience account hundreds of
        # characters after the definition lead-in. It is still an enumerated
        # sibling name, not evidence that the current product serves that
        # audience.
        return False

    generic_tokens = {
        "account", "accounts", "bank", "banking", "canada", "chequing", "checking",
        "credit", "financial", "personal", "royal", "savings", "the",
        *re.findall(r"[a-z0-9]+", context.bank_code.lower()),
    }
    identity_tokens: set[str] = set()
    for raw_value in _source_metadata_title_candidates(context):
        value = str(raw_value or "").split("|", 1)[0].lower()
        identity_tokens.update(
            token
            for token in re.findall(r"[a-z0-9]+", value)
            if len(token) >= 4 and token not in generic_tokens
        )
    if not identity_tokens:
        return False
    entitlement_markers = (
        "eligible", "for full-time", "for students", "no monthly fee", "no monthly fees",
        "fee waived", "waiver", "24 and younger", "first year", "designed for", "available to",
    )
    for audience_term in audience_terms:
        for audience_match in re.finditer(re.escape(audience_term), lowered):
            list_prefix = lowered[max(0, audience_match.start() - 600):audience_match.start()]
            if re.search(
                r"\b(?:means|includes?)\s+(?:any\s+of\s+)?(?:the\s+)?following\s+accounts?\b[\s\S]{0,520}$",
                list_prefix,
            ):
                # Legal offer definitions enumerate historical/current account
                # names. Merely appearing in that list does not make the
                # target account a student/newcomer product.
                continue
            window = lowered[max(0, audience_match.start() - 240):audience_match.end() + 240]
            if any(token in window for token in identity_tokens) and any(
                marker in window for marker in entitlement_markers
            ):
                return True
    return False


def _has_student_plan_context(*, lowered: str, anchor: str) -> bool:
    combined_text = f"{anchor} {lowered}"
    return any(
        re.search(pattern, combined_text)
        for pattern in (
            r"\bstudent(?:\s+\w+){0,2}\s+(?:chequing|checking|account|package|plan)\b",
            r"\byouth(?:\s+\w+){0,2}\s+(?:chequing|checking|account|package|plan)\b",
            r"\b(?:for|designed for|available to)\s+[^.]{0,60}\bstudents?\b",
        )
    )


def _has_newcomer_plan_context(*, lowered: str, anchor: str) -> bool:
    combined_text = f"{anchor} {lowered}"
    return any(
        re.search(pattern, combined_text)
        for pattern in (
            r"\bnewcomer(?:\s+\w+){0,2}\s+(?:chequing|checking|account|package|plan)\b",
            r"\bnew to canada\s+[^.]{0,80}\b(?:banking|chequing|checking|account|package|plan)\b",
            r"\b(?:for|designed for|available to)\s+[^.]{0,80}\bnewcomers?\b",
            r"\b(?:eligible\s+)?newcomers?\b[^.]{0,80}\b(?:first year|waiver|no monthly fee)\b",
        )
    )


def _detect_frequency(lowered: str) -> str | None:
    if "paid monthly" in lowered or "interest is paid monthly" in lowered or "monthly interest" in lowered:
        return "monthly"
    if "paid quarterly" in lowered or "quarterly" in lowered:
        return "quarterly"
    if "paid weekly" in lowered or "weekly" in lowered:
        return "weekly"
    if "paid annually" in lowered or "annually" in lowered or "yearly" in lowered:
        return "annually"
    if "semi-annually" in lowered:
        return "semi-annually"
    if "paid daily" in lowered or "daily payment" in lowered:
        return "daily"
    return None


def _is_promotional_rate_context(lowered: str) -> bool:
    if any(
        token in lowered
        for token in (
            "introductory rate",
            "introductory interest",
            "promotional rate",
            "promotional interest",
            "for 3 months",
            "for three months",
            "first 3 months",
            "first three months",
            "for the first",
            "special rate",
            "limited time",
            "limited-time",
            "offer expires",
            "new client offer",
            "welcome offer",
            "boosted rate",
        )
    ):
        return True
    if re.search(r"\b(?:for|during)\s+(?:the\s+)?(?:first\s+)?\d{1,3}[- ]?(?:days?|months?)\b", lowered) and any(
        marker in lowered for marker in ("rate", "interest", "offer", "boost", "earn")
    ):
        return True
    if re.search(r"\b\d{1,3}[- ]month\s+(?:rate|offer|boost)\b", lowered):
        return True
    return any(token in lowered for token in ("bonus rate", "bonus interest")) and any(
        marker in lowered
        for marker in ("offer", "welcome", "limited time", "limited-time", "for the first", "first 3 months")
    )


def _has_product_promotional_context(*, context: ExtractionDocumentContext, text: str) -> bool:
    lowered = text.lower()
    if not _is_promotional_rate_context(lowered):
        return False
    current_terms = _source_product_terms(context)
    other_terms = [
        term
        for source_id, terms in _BMO_SAVINGS_PRODUCT_TERMS.items()
        if source_id != context.source_id
        for term in terms
    ]
    has_concrete_offer = _PERCENT_RE.search(text) is not None or any(
        token in lowered
        for token in ("for 3 months", "for three months", "for the first", "offer expires", "until ")
    )
    if not current_terms:
        return has_concrete_offer

    found_current_promo = False
    found_other_only_promo = False
    normalized = _normalize_text(text).lower()
    promo_patterns = (
        "introductory rate",
        "introductory interest",
        "promotional rate",
        "promotional interest",
        "bonus rate",
        "bonus interest",
        "special rate",
        "limited time",
    )
    for promo_pattern in promo_patterns:
        for match in re.finditer(re.escape(promo_pattern), normalized):
            window = normalized[max(0, match.start() - 80) : min(len(normalized), match.end() + 80)]
            has_current_term = any(term in window for term in current_terms)
            has_other_term = any(term in window for term in other_terms)
            if has_current_term:
                found_current_promo = True
            elif has_other_term:
                found_other_only_promo = True
    if found_current_promo:
        return True
    if found_other_only_promo:
        return False
    return has_concrete_offer


def _source_product_terms(context: ExtractionDocumentContext) -> tuple[str, ...]:
    terms = list(_BMO_SAVINGS_PRODUCT_TERMS.get(context.source_id, ()))
    for key in ("product_name", "source_name", "source_title", "page_title", "primary_heading"):
        value = _normalize_text(str(context.source_metadata.get(key) or "")).lower()
        if value and value not in terms:
            terms.append(value)
    return tuple(terms)


def _extract_term_length_text(text: str) -> str | None:
    term_list = re.search(
        r"(?P<terms>\b\d{1,2}(?:\s*,\s*\d{1,2}){2,}(?:\s*,?\s*(?:and|or)\s*\d{1,2})?\s*[- ]?year\s+terms?\b)",
        _normalize_text(text),
        flags=re.IGNORECASE,
    )
    if term_list is not None:
        return _normalize_text(term_list.group("terms"))
    match = _extract_term_match(text)
    if match is None:
        return None
    start_value, start_unit, end_value, end_unit = match.groups()
    normalized_start = f"{start_value} {_normalize_term_unit(start_unit)}"
    if end_value and end_unit:
        return f"{normalized_start} to {end_value} {_normalize_term_unit(end_unit)}"
    return normalized_start


def _extract_term_length_days(text: str) -> int | None:
    if re.search(
        r"\b\d{1,2}(?:\s*,\s*\d{1,2}){2,}(?:\s*,?\s*(?:and|or)\s*\d{1,2})?\s*[- ]?year\s+terms?\b",
        _normalize_text(text),
        flags=re.IGNORECASE,
    ):
        return None
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


def _extract_base_12_month_rate(text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    for row in _extract_term_rate_table(normalized) or []:
        term_label = str(row.get("term_label") or "").lower()
        term_length_days = row.get("term_length_days")
        if row.get("rate") and (term_length_days in {360, 365} or "12 month" in term_label or "1 year" in term_label):
            return str(row["rate"])
    for match in _PERCENT_RE.finditer(normalized):
        window_start = max(0, match.start() - 120)
        window_end = min(len(normalized), match.end() + 120)
        window = normalized[window_start:window_end].lower()
        if not any(token in window for token in ("12 month", "12-month", "1 year", "1-year", "one year")):
            continue
        if not any(token in window for token in ("rate", "interest", "annual")):
            continue
        if any(token in window for token in ("bonus", "promo", "promotional", "introductory")):
            continue
        if canonical_deposit_rate_suppression_reason(value=match.group(1), context=window) is not None:
            continue
        return _normalize_decimal(match.group(1))
    return None


def _extract_term_rate_table(text: str) -> list[dict[str, object]] | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    minimum_deposit = _extract_explicit_term_table_minimum_deposit(normalized)
    apy_rows = _extract_term_rate_apy_rows(normalized=normalized, minimum_deposit=minimum_deposit)
    if len(apy_rows) >= 2:
        return apy_rows[:24]
    term_first_rows = _extract_term_rate_rows(
        normalized=normalized,
        row_pattern=_TERM_RATE_ROW_RE,
        minimum_deposit=minimum_deposit,
    )
    rate_first_rows = _extract_term_rate_rows(
        normalized=normalized,
        row_pattern=_RATE_TERM_ROW_RE,
        minimum_deposit=minimum_deposit,
    )
    # Prefer the orientation that produces the most complete adjacent pairs. A
    # rate-first table otherwise makes the term-first pattern shift every rate
    # forward by one row. Ties intentionally preserve the established
    # term-first behavior.
    first_rate = _PERCENT_RE.search(normalized)
    first_term = _TERM_RE.search(normalized)
    rate_first_on_tie = bool(
        first_rate is not None
        and first_term is not None
        and first_rate.start() < first_term.start()
    )
    rows = (
        rate_first_rows
        if len(rate_first_rows) > len(term_first_rows)
        or (len(rate_first_rows) == len(term_first_rows) and rate_first_on_tie)
        else term_first_rows
    )
    return rows[:24] or None


def _extract_term_rate_apy_rows(
    *,
    normalized: str,
    minimum_deposit: str | None,
) -> list[dict[str, object]]:
    first_term = _TERM_RE.search(normalized)
    header_end = first_term.start() if first_term is not None else min(len(normalized), 240)
    header = normalized[:header_end].lower()
    if not re.search(r"\brate\s*\(%?\)?[\s\S]{0,40}\bapy\s*\(%?\)?", header):
        return []
    rows: list[dict[str, object]] = []
    seen_terms: set[str] = set()
    for match in _TERM_RATE_APY_ROW_RE.finditer(normalized):
        term_label = _normalize_text(match.group("term")).lower()
        if term_label in seen_terms:
            continue
        apy = _normalize_decimal(match.group("apy"))
        context = _rate_percentage_context_window(
            text=normalized,
            start=match.start("apy"),
            end=match.end("apy"),
            radius=140,
        )
        if canonical_deposit_rate_suppression_reason(value=apy, context=context) is not None:
            continue
        seen_terms.add(term_label)
        rows.append(
            {
                "term_label": term_label,
                "term_length_days": _term_label_to_days(term_label),
                "rate": apy,
                "minimum_deposit": minimum_deposit,
                "notes": "APY",
            }
        )
    return rows


def _extract_term_rate_rows(
    *,
    normalized: str,
    row_pattern: re.Pattern[str],
    minimum_deposit: str | None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for match in row_pattern.finditer(normalized):
        term_label = _normalize_text(match.group("term")).lower()
        rate = _normalize_decimal(match.group("rate"))
        window = _rate_percentage_context_window(
            text=normalized,
            start=match.start("rate"),
            end=match.end("rate"),
            radius=140,
        )
        if canonical_deposit_rate_suppression_reason(value=rate, context=window) is not None:
            continue
        key = (term_label, rate)
        if key in seen:
            continue
        seen.add(key)
        term_length_days = _term_label_to_days(term_label)
        rows.append(
            {
                "term_label": term_label,
                "term_length_days": term_length_days,
                "rate": rate,
                "minimum_deposit": minimum_deposit,
                "notes": None,
            }
        )
    return rows


def _extract_explicit_term_table_minimum_deposit(text: str) -> str | None:
    patterns = (
        r"\bminimum\s+(?:deposit|investment|balance|amount)\b[^$€£\d]{0,30}[$€£]\s?([0-9][0-9,]*(?:\.\d{1,2})?)",
        r"[$€£]\s?([0-9][0-9,]*(?:\.\d{1,2})?)[^\w]{0,12}\bminimum\s+(?:deposit|investment|balance|amount)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match is not None:
            return _normalize_decimal(match.group(1))
    return None


def _term_label_to_days(term_label: str) -> int | None:
    match = _TERM_RE.search(term_label)
    if match is None:
        return None
    start_value, start_unit, end_value, _ = match.groups()
    if end_value:
        return None
    return _convert_term_to_days(start_value, start_unit)


def _extract_application_method(text: str) -> str | None:
    normalized = _normalize_text(text)
    if any(
        marker in normalized.lower()
        for marker in (
            "activate a visa",
            "activate an american express",
            "activate your card",
            "online activation page",
            "insert your card and enter your pin",
        )
    ):
        return None
    direct_apply = re.search(
        r"\bapply\s+by\s+(?P<method>[\s\S]{1,180}?)(?=\s+(?:interest\s+rates?|resources|legal|benefits?)\b|$)",
        normalized,
        flags=re.IGNORECASE,
    )
    if direct_apply is not None:
        return _normalize_text(f"Apply by {direct_apply.group('method')}").rstrip(" .")[:280]
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        lowered = raw_sentence.lower()
        if any(
            marker in lowered
            for marker in (
                "must be registered for online",
                "need to register",
                "sign on to online banking",
                "sign in to online banking",
            )
        ):
            continue
        has_action = bool(
            re.search(
                r"\b(?:apply|open\s+(?:an\s+)?account|purchase|book\s+an\s+appointment)\b",
                lowered,
            )
        )
        has_channel = any(token in lowered for token in ("online", "branch", "mobile app", "phone", "appointment"))
        if has_action and has_channel:
            if any(
                marker in lowered
                for marker in (
                    "redeem your",
                    "gift certificate",
                    "cash back certificate",
                    "using the mobile app to redeem",
                )
            ):
                continue
            action_match = re.search(
                r"\b(?:apply|open\s+(?:an\s+)?account|purchase|book\s+an\s+appointment)\b",
                lowered,
            )
            channel_match = re.search(r"\b(?:online|branch|mobile\s+app|phone|appointment)\b", lowered)
            if action_match is None or channel_match is None or abs(channel_match.start() - action_match.start()) > 120:
                continue
            return _normalize_text(raw_sentence)[:280]
    return None


def _extract_post_maturity_interest_rate(text: str) -> str | None:
    normalized = _normalize_text(text)
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        lowered = raw_sentence.lower()
        has_post_maturity_action = any(
            token in lowered
            for token in ("after maturity", "post-maturity", "post maturity", "renewal", "renewed", "reinvest")
        )
        has_at_maturity_rate = "at maturity" in lowered and "rate" in lowered
        if (has_post_maturity_action or has_at_maturity_rate) and any(
            token in lowered for token in ("interest", "rate", "renew", "reinvest")
        ):
            return _normalize_text(raw_sentence)[:280]
    return None


def _extract_tax_benefits(*, context: ExtractionDocumentContext, text: str) -> str | None:
    normalized = _normalize_text(text)
    product_type = _canonical_product_type_family(_infer_product_type(context))
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        sentence = raw_sentence.strip()
        lowered = sentence.lower()
        if not any(
            keyword in lowered
            for keyword in ("tax free", "tax-free", "tax deferred", "tax-deferred", "tfsa", "rrsp", "tax benefit")
        ):
            continue
        if product_type == "savings" and any(token in lowered for token in (" gic", "guaranteed investment")):
            continue
        if product_type == "gic" and "savings account" in lowered:
            continue
        if _sentence_mentions_other_product_only(context=context, lowered_sentence=lowered):
            continue
        return _normalize_text(sentence)[:280]
    return None


def _extract_promotional_period_text(*, context: ExtractionDocumentContext, text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    registered_product = _source_is_registered_product(context)
    has_plan_specific_terms = "registered promotional rate" in normalized.lower()
    if not has_plan_specific_terms:
        parenthetical_months = re.search(
            r"\b\d{1,3}\s*days?\s*\(\s*(?P<count>\d{1,3})\s*months?\s*\)",
            normalized,
            flags=re.IGNORECASE,
        )
        if parenthetical_months is not None and _is_promotional_rate_context(normalized.lower()):
            return f"{parenthetical_months.group('count')} months"
        explicit_duration = re.search(
            r"\b(?:for|during)\s+(?:the\s+)?(?:first\s+)?(?P<count>\d{1,3})\s*(?P<unit>days?|weeks?|months?)\b",
            normalized,
            flags=re.IGNORECASE,
        )
        if explicit_duration is not None:
            window_start = max(0, explicit_duration.start() - 140)
            window_end = min(len(normalized), explicit_duration.end() + 80)
            if _is_promotional_rate_context(normalized[window_start:window_end].lower()):
                count = explicit_duration.group("count")
                unit = explicit_duration.group("unit").lower()
                return f"{count} {unit}"
    best: tuple[int, int, str] | None = None
    for index, raw_sentence in enumerate(re.split(r"(?<=[.!?])\s+", normalized)):
        sentence = raw_sentence.strip()
        lowered = sentence.lower()
        if not sentence or not _is_promotional_rate_context(lowered):
            continue
        if re.search(
            r"\b(?:for|during)\s+(?:the\s+)?(?:first\s+)?\d{1,3}\s*(?:days?|weeks?|months?)\b|"
            r"\b\d{1,3}\s*(?:days?|weeks?|months?)\b|\buntil\s+|\bthrough\s+|\bexpires?\b",
            lowered,
        ) is None:
            continue
        explicitly_non_registered = "non-registered" in lowered or "non registered" in lowered
        explicitly_registered = not explicitly_non_registered and bool(re.search(r"\bregistered\b", lowered))
        if registered_product and explicitly_non_registered:
            continue
        if not registered_product and explicitly_registered:
            continue
        score = 0
        if registered_product and explicitly_registered:
            score += 5
        if not registered_product and explicitly_non_registered:
            score += 5
        if _PERCENT_RE.search(sentence) is not None:
            score += 3
        if any(token in lowered for token in ("promotional rate", "special rate", "new client offer", "offer")):
            score += 2
        ranked = (score, -index, _normalize_text(sentence)[:280])
        if best is None or ranked > best:
            best = ranked
    return best[2] if best is not None else None


def _extract_deposit_insurance(text: str) -> str | None:
    normalized = _normalize_text(text)
    full_name_membership = re.search(
        r"(?P<sentence>[A-Z][A-Za-z0-9&.'’\-]*(?:\s+[A-Z][A-Za-z0-9&.'’\-]*){0,7}\s+"
        r"(?:is|are)\s+(?:a\s+)?members?\s+of\s+(?:the\s+)?Canada\s+Deposit\s+Insurance\s+Corporation"
        r"(?:\s*\(CDIC\))?\.?)",
        normalized,
    )
    if full_name_membership is not None:
        sentence = _normalize_text(full_name_membership.group("sentence"))
        sentence = re.sub(
            r"^(?:(?:legal|book an appointment|schedule an appointment|contact us|open account)\s+)+",
            "",
            sentence,
            flags=re.IGNORECASE,
        )
        return sentence[:280]
    explicit_membership = re.search(
        r"(?P<sentence>[A-Z][A-Za-z0-9&.'’]*(?:\s+[A-Z][A-Za-z0-9&.'’]*){0,6}\s+is\s+(?:a|an|the)\s+[^.]{0,220}?"
        r"\b(?:CDIC\s+member|member\s+of\s+CDIC)\b[^.]{0,80}\.?)",
        normalized,
    )
    if explicit_membership is not None:
        return _normalize_text(explicit_membership.group("sentence"))[:280]
    candidate = _extract_limited_sentence(
        text,
        ("cdic", "deposit insurance", "insured", "canada deposit insurance corporation"),
    )
    if candidate is None:
        return None
    lowered = candidate.lower()
    if "cdic" in lowered and not any(
        marker in lowered
        for marker in (
            "deposit",
            "insured",
            "insurance",
            "coverage",
            "covered",
            "eligible",
            "member of cdic",
            "cdic member",
        )
    ):
        return None
    return candidate


def _extract_limited_sentence(text: str, keywords: tuple[str, ...]) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        sentence = raw_sentence.strip()
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            return _normalize_text(sentence)[:280]
    return None


def _find_sentence(text: str, keywords: tuple[str, ...]) -> str | None:
    normalized = _normalize_text(text)
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        lowered = raw_sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            return raw_sentence
    return normalized if normalized else None


def _restore_us_dollar_text(value: str) -> str:
    return re.sub(r"\bU\s*S\s+Dollar\b", "U.S. Dollar", value, flags=re.IGNORECASE)


def _extract_interest_calculation_method(text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        sentence = raw_sentence.strip()
        lowered = sentence.lower()
        if any(token in lowered for token in ("calculated", "daily closing balance", "calculation", "daily interest")):
            daily_interest_match = re.search(r"earn\s+daily\s+interest\s+on\s+every\s+dollar", sentence, flags=re.IGNORECASE)
            if daily_interest_match is not None:
                return _normalize_text(daily_interest_match.group(0))
            calculation_start = re.search(r"\binterest\s+is\s+calculated\b", sentence, flags=re.IGNORECASE)
            if calculation_start is not None:
                return _normalize_text(sentence[calculation_start.start():])[:280]
            return _normalize_text(sentence)[:280]
    return None


def _extract_interest_rate_summary(text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        sentence = raw_sentence.strip()
        lowered = sentence.lower()
        if not any(marker in lowered for marker in ("rate", "return", "interest")):
            continue
        if any(
            marker in lowered
            for marker in (
                "variable interest rate",
                "variable return",
                "linked to changes",
                "linked to the performance",
                "return is linked",
                "based on a formula",
                "rate at time of purchase",
                "rates available at time of purchase",
                "current interest rate environment",
            )
        ) or re.search(
            r"\b(?:bank\s+)?prime(?:\s+rate)?\b\s*(?:\+|plus|-|minus)\s*\d{1,2}(?:\.\d{1,4})?\s*%",
            sentence,
            flags=re.IGNORECASE,
        ):
            return _normalize_text(sentence)[:280]
    return None


def _extract_eligibility_text(text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None

    lowered_text = normalized.lower()
    if any(
        marker in lowered_text
        for marker in (
            "to apply, you’ll need",
            "to apply, you'll need",
            "automatically apply the highest value rebate",
            "activate the value program",
            "eligible for one fee-waiver",
        )
    ):
        return None
    if (
        any(marker in lowered_text for marker in ("cash bonus bundle offer", "cash bonus", "welcome offer"))
        and any(marker in lowered_text for marker in ("qualifying transactions", "offer period", "offer terms"))
    ):
        return None
    if re.search(
        r"\bto qualify(?: for (?:this|the|these) offers?)?,?\s+(?:make sure to\s+)?open\s+a\s+new\b"
        r"[\s\S]{0,180}?\bbetween\s+[a-z]+\s+\d{1,2},\s+20\d{2}\s+and\s+[a-z]+\s+\d{1,2},\s+20\d{2}",
        lowered_text,
    ):
        return None
    if (
        "eligible for overdraft protection" in lowered_text
        and not any(marker in lowered_text for marker in ("must ", "resident", "age of majority", "years or older"))
    ):
        return None
    if (
        "account holders" in lowered_text
        and "commission" in lowered_text
        and any(marker in lowered_text for marker in ("trades", "trading", "brokerage"))
    ):
        return None
    eligible_account = re.search(
        r"maintain\s+an?\s+eligible\s+(?P<account>[a-z0-9 .&'’*-]{2,60}?account)\b",
        normalized,
        flags=re.IGNORECASE,
    )
    qualifying_transactions = re.search(
        r"complete\s+at\s+least\s+(?P<required>\d{1,2})\s+(?:out\s+)?of\s+(?:the\s+)?"
        r"(?P<total>\d{1,2})\s+qualifying\s+(?:monthly\s+)?transactions?",
        normalized,
        flags=re.IGNORECASE,
    )
    if eligible_account is not None and qualifying_transactions is not None:
        account = _normalize_text(eligible_account.group("account"))
        return (
            f"Maintain an eligible {account} and complete at least "
            f"{qualifying_transactions.group('required')} of {qualifying_transactions.group('total')} "
            "qualifying monthly transactions."
        )
    if lowered_text.startswith("what you need to know") and "type cashable access" in lowered_text:
        return None
    if any(
        marker in lowered_text
        for marker in (
            "heading south of the border",
            "travel with ease",
            "tools and resources provide the information you need",
            "other u.s. cross-border banking solutions",
        )
    ):
        return None

    table_match = re.search(
        r"eligibility\s+with\s+plans?(?:\s*\*\d+)?\s+(?P<value>can\s+be\s+included\s+in\s+any\s+bank\s+plan)",
        normalized,
        flags=re.IGNORECASE,
    )
    if table_match is not None:
        return _normalize_text(table_match.group("value")).capitalize()

    resident_majority_match = re.search(
        r"(?P<value>you(?:'re|\s+are)\s+a\s+canadian\s+resident\s+and\s+"
        r"you(?:'ve|\s+have)\s+reached\s+the\s+age\s+o(?:f)?\s*majority\s+"
        r"in\s+your\s+province\s+or\s+territory)",
        normalized,
        flags=re.IGNORECASE,
    )
    if resident_majority_match is not None:
        value = _normalize_text(resident_majority_match.group("value")).strip(" .")
        return re.sub(r"\bage\s+o(?:f)?\s*majority\b", "age of majority", value, flags=re.IGNORECASE)

    resident_age_match = re.search(
        r"(?P<value>you(?:'|’)re\s+a\s+canadian\s+resident\s+and\s+you(?:'|’)ve\s+reached\s+the\s+age\s+of\s+majority[^.]*)(?:\.|$)",
        normalized,
        flags=re.IGNORECASE,
    )
    if resident_age_match is not None:
        return _normalize_text(resident_age_match.group("value")).strip(" .")

    best: tuple[int, int, str] | None = None
    for index, raw_sentence in enumerate(re.split(r"(?<=[.!?])\s+", normalized)):
        sentence = raw_sentence.strip()
        if not sentence:
            continue
        if "?" in sentence:
            continue
        lowered = sentence.lower()
        if any(
            marker in lowered
            for marker in (
                "commitment on low-cost and no-cost accounts",
                "commitment on low cost and no cost accounts",
            )
        ):
            continue
        if (
            any(marker in lowered for marker in ("monthly fee", "fee rebate", "value program", "seniors rebate"))
            and any(marker in lowered for marker in ("rebate", "discount", "pay as low as", "as low as"))
            and not any(marker in lowered for marker in ("resident", "age of majority", "years or older", "must be"))
        ):
            continue
        if (
            re.search(r"\b(?:apply|open)\b", lowered)
            and any(marker in lowered for marker in ("online", "mobile app", "branch", "appointment", "by phone"))
            and not any(
                marker in lowered
                for marker in ("eligible", "qualify", "resident", "age of", "years or older", "must ", "required")
            )
        ):
            continue
        if any(
            token in lowered
            for token in (
                "eligible deposits",
                "eligible transactions",
                "deposit insurance",
                "insured by cdic",
                "cdic eligible",
                "eligible for cdic insurance",
                "eligible for cdic coverage",
                "canada deposit insurance corporation",
                "referral link",
                "refer a friend",
                "unique referral",
            )
        ):
            continue
        if re.search(r"\bmust\s+maintain\s+(?:a\s+)?minimum\b", lowered):
            continue
        if "overdraft protection" in lowered and any(
            marker in lowered for marker in ("subject to approval", "apply", "qualify", "credit approval")
        ):
            continue
        if "shell go+ account" in lowered or "loyalty account" in lowered:
            continue
        has_structural_eligibility = any(
            marker in lowered
            for marker in (
                "must ",
                "required",
                "requirement",
                "resident",
                "age of majority",
                "years or older",
                "do not need",
                "don't need",
            )
        )
        if not has_structural_eligibility and (
            any(marker in lowered for marker in ("eligible purchase", "eligible grocery", "eligible gas"))
            and any(marker in lowered for marker in ("point", "reward", "cash back", "cashback", "earn"))
        ):
            continue
        if (
            any(
                marker in lowered
                for marker in ("qualify for this offer", "qualify for these offers", "to qualify, open a new", "to qualify, apply")
            )
            and any(marker in lowered for marker in ("offer", "bonus", "between ", "eligible purchases"))
        ):
            continue
        if (
            any(marker in lowered for marker in ("eligible credit card", "eligible chequing account", "eligible savings account"))
            and any(marker in lowered for marker in ("qualifying transaction", "qualifying condition", "cash bonus", "bundle bonus"))
        ):
            # Cross-product acquisition bundles describe how to earn an offer,
            # not who can open the product represented by this page.
            continue
        if "eligible credit card" in lowered and "then apply" in lowered:
            continue
        if "eligible direct deposit" in lowered and (
            re.search(r"\bfor\s+\d{1,3}\s+(?:straight\s+|consecutive\s+)?months?\b", lowered)
            or any(marker in lowered for marker in ("welcome offer", "cash bonus", "gift card", "offer ends"))
        ):
            continue
        if re.fullmatch(
            r"(?:how to apply\s*)?(?:talk|speak) to an? (?:scotia )?advisor(?:\s+book an appointment)?",
            lowered.strip(" .:-"),
        ):
            continue
        score = 0
        if any(token in lowered for token in ("eligible", "eligibility", "qualify", "qualified")):
            score += 4
        if any(token in lowered for token in ("resident", "residents", "aged ", "years or older", "age of")):
            score += 3
        if "canadian resident" in lowered:
            score += 4
        if any(token in lowered for token in ("must ", "required", "requirement", "do not need", "don't need")):
            score += 3
        if any(token in lowered for token in ("to apply", "can apply", "apply online", "to open", "can open")):
            score += 2
        if any(token in lowered for token in ("under the age of majority", "under age", "minor")):
            score -= 4
        if any(
            token in lowered
            for token in (
                "terms and conditions",
                "offers or promotions",
                "bonus miles",
                "points you earn",
                "earn per transaction",
                "limited time",
                "limited-time",
                "special offer",
            )
        ):
            score -= 5
        if score <= 0:
            continue
        candidate = _normalize_text(sentence).strip(" .")
        prefix_split = re.match(r"^[^:]{4,80}\baccount:\s+(?P<value>.+)$", candidate, flags=re.IGNORECASE)
        if prefix_split is not None:
            candidate = _normalize_text(prefix_split.group("value")).strip(" .")
        ranked = (score, -index, candidate[:280])
        if best is None or ranked > best:
            best = ranked
    if best is None:
        return None
    return best[2]


def _source_is_registered_product(context: ExtractionDocumentContext) -> bool:
    product_text = " ".join(
        str(context.source_metadata.get(key) or "").lower()
        for key in ("product_type", "product_type_name", "product_name", "source_name", "page_title", "primary_heading")
    )
    return re.search(r"\b(?:tfsa|rrsp|rrif|resp|rsp|rif|registered)\b", product_text) is not None


def _has_registered_product_availability_context(lowered: str) -> bool:
    return re.search(
        r"\b(?:(?:also\s+)?available\s+(?:as|in|for)|eligible\s+for|may\s+be\s+held\s+in|can\s+be\s+held\s+in)\s+"
        r"(?:an?\s+)?(?:tfsa|rrsp|rrif|resp|registered(?:\s+(?:plan|account))?)\b",
        lowered,
    ) is not None


def _cashable_only_at_maturity(lowered: str) -> bool:
    return re.search(r"\b(?:cashable|redeemable)\s+(?:only\s+)?(?:at|upon)\s+maturity\b", lowered) is not None


def _extract_tier_definition_text(text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    if _contains_unresolved_rate_placeholder(normalized):
        return None
    tier_table_start = re.search(r"\bdaily closing balance tiers?\b", normalized, flags=re.IGNORECASE)
    if tier_table_start is not None:
        tier_text = normalized[tier_table_start.start() :]
        tier_text = re.split(
            r"\b(?:how the boosted rate works|additional terms|choose up to|similar accounts?)\b",
            tier_text,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        if len(_PERCENT_RE.findall(tier_text)) >= 2 and re.search(r"[$€£]\s?[0-9]", tier_text):
            return _normalize_text(tier_text)[:500]
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        sentence = raw_sentence.strip()
        lowered = sentence.lower()
        has_grounded_tier_values = bool(_PERCENT_RE.search(sentence) or re.search(r"[$€£]\s?[0-9]", sentence))
        if "tier" in lowered and has_grounded_tier_values and any(token in lowered for token in ("rate", "balance", "earn")):
            return _normalize_text(sentence)[:280]
        if re.search(r"\$\s?[0-9][^.;]{0,80}?\bearn(?:s)?\b[^.;]{0,80}?%", sentence, flags=re.IGNORECASE):
            return _normalize_text(sentence)[:280]
    return None


def _contains_unresolved_rate_placeholder(text: str) -> bool:
    lowered = text.lower()
    return "rds%rate[" in lowered or re.search(r"\brate\[[0-9]+\]\.", lowered) is not None


def _extract_withdrawal_limit_text(*, context: ExtractionDocumentContext, text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    included_then_fee_match = re.search(
        r"(?P<included>(?:one|1)\s+(?:eligible\s+)?(?:debit\s+)?transaction\s+per\s+month\s+at\s+no\s+cost)"
        r"[\s\S]{0,180}?"
        r"(?P<fee>\$\s*[0-9]+(?:\.[0-9]{1,2})?\s+(?:fee\s+)?(?:for|per)\s+each\s+additional\s+"
        r"(?:debit|withdrawal|transaction|transfer\s+out))",
        normalized,
        flags=re.IGNORECASE,
    )
    if included_then_fee_match is not None:
        included = _normalize_text(included_then_fee_match.group("included"))
        fee = _normalize_text(included_then_fee_match.group("fee"))
        return f"{included.capitalize()}. {fee[0].upper() + fee[1:]}."
    included_only_match = re.search(
        r"(?P<included>(?:one|1)\s+(?:eligible\s+)?(?:debit\s+)?transaction\s+per\s+month\s+at\s+no\s+cost)",
        normalized,
        flags=re.IGNORECASE,
    )
    if included_only_match is not None:
        return _normalize_text(included_only_match.group("included")).capitalize() + "."
    table_match = re.search(
        r"number\s+of\s+transactions\s+per\s+month\s+(?P<value>transactions\s+based\s+on\s+plan\s+limits)",
        normalized,
        flags=re.IGNORECASE,
    )
    if table_match is not None:
        return f"Number of transactions per month: {_normalize_text(table_match.group('value'))}."
    withdrawal_fee_match = re.search(
        r"\bwithdrawal\s*[:|\-]?\s*\$\s*(?P<fee>[0-9]+(?:\.[0-9]{1,2})?)\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if withdrawal_fee_match is not None:
        return f"Withdrawal fee: ${withdrawal_fee_match.group('fee')}."
    if re.search(
        r"\btransaction\s+limits?\s+are\s+shared\s+(?:among|between)\s+(?:these|the)\s+two\s+accounts\b",
        normalized,
        flags=re.IGNORECASE,
    ):
        return "Transaction limits depend on and are shared with the paired account's bank plan."
    best: tuple[int, int, str] | None = None
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        sentence = raw_sentence.strip()
        lowered = sentence.lower()
        if not sentence or "?" in sentence or lowered.startswith(("what are ", "how do ", "can i ")):
            continue
        if any(marker in lowered for marker in ("calculations are estimates", "estimator tool", "assuming no withdrawals")):
            continue
        if any(
            marker in lowered
            for marker in ("try our ", "check out our ", "day-to-day banking", "everyday banking needs")
        ):
            continue
        if _sentence_mentions_other_product_only(context=context, lowered_sentence=lowered):
            continue
        has_withdrawal_signal = any(
            token in lowered
            for token in (
                "withdrawal",
                "withdrawals",
                "transactions per month",
                "transaction limit",
                "debit transaction",
                "additional transactions",
                "transfers out",
                "transfer out",
            )
        )
        if not has_withdrawal_signal:
            continue
        has_constraint_signal = any(
            token in lowered
            for token in (
                "cost", "fee", "additional", "limit", "per month", "not available", "unavailable",
                "cannot", "can't", "only", "included", "free withdrawal", "maximum", "minimum withdrawal",
                "no cash", "transfers out",
            )
        )
        if not has_constraint_signal:
            continue
        score = 0
        if any(token in lowered for token in ("withdrawal", "withdrawals")):
            score += 4
        if any(token in lowered for token in ("cost", "costs", "fee", "fees", "additional")):
            score += 3
        if any(token in lowered for token in ("transaction limit", "transactions per month")):
            score += 2
        if "debit transaction" in lowered:
            score += 1
        if score <= 0:
            continue
        candidate = _normalize_text(sentence)[:280]
        ranked = (score, -len(candidate), candidate)
        if best is None or ranked > best:
            best = ranked
    if best is None:
        return None
    return best[2]


def _extract_transaction_fee(*, text: str, require_additional: bool = False) -> str | None:
    normalized = _normalize_text(text)
    patterns = (
        r"\badditional\s+(?:debit\s+)?transactions?(?:\s+\d{1,3})?\s+\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s+each\b",
        r"\badditional\s+(?:debit\s+)?transactions?[^$]{0,90}?\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s+per\s+transaction\b",
        r"\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s+(?:for\s+each|per)\s+additional\s+(?:debit\s+)?(?:transaction|withdrawal|transfer)\b",
        r"\btransaction\s+fees?(?:\s+\d{1,3})?\s+\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s+each\b",
        r"\bfee\s+for\s+transactions?\s*[:|\-]?\s*\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s*(?:each|per\s+transaction)?\b",
        r"\btransactions?\s*[:|\-]?\s*\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s*(?:each|per\s+transaction)\b",
        r"\b(?:withdrawal|transaction)\s*(?:fee)?\s*[:|\-]\s*\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match is None:
            continue
        if require_additional and "additional" not in match.group(0).lower():
            continue
        return _normalize_decimal(match.group("fee").replace(",", ""))
    return None


def _sentence_mentions_other_product_only(*, context: ExtractionDocumentContext, lowered_sentence: str) -> bool:
    current_terms = _source_product_terms(context)
    if not current_terms:
        return False
    other_terms = [
        term
        for source_id, terms in _BMO_SAVINGS_PRODUCT_TERMS.items()
        if source_id != context.source_id
        for term in terms
    ]
    return any(term in lowered_sentence for term in other_terms) and not any(term in lowered_sentence for term in current_terms)


def _extract_notes_text(text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None
    lowered = normalized.lower()
    if any(
        marker in lowered
        for marker in ("use cookies", "tracking tools", "webforms", "privacy preferences", "digital properties")
    ):
        return None
    if lowered.startswith("what are ") or lowered.startswith("how do "):
        return None
    if "features details" in lowered and any(token in lowered for token in ("monthly account fee", "interest rate", "eligibility with plans")):
        return None
    for raw_sentence in re.split(r"(?<=[.!?])\s+", normalized):
        sentence = raw_sentence.strip()
        sentence_lowered = sentence.lower()
        if any(token in sentence_lowered for token in ("note", "disclosure", "important")):
            return _normalize_text(sentence)[:280]
    return None


def _extract_included_transactions(text: str) -> int | None:
    lowered = text.lower()
    if _has_account_wide_unlimited_transactions(lowered):
        return None
    # Product comparison tables commonly put HTML footnote numbers on the
    # label line and the real value on the following line.  Read the standalone
    # value line first instead of treating a footnote or a fee decimal tail as
    # the count.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if not re.search(r"\btransactions?\b", line, flags=re.IGNORECASE):
            continue
        if not re.search(r"\b(?:included\s+per\s+month|per\s+month|included)\b", line, flags=re.IGNORECASE):
            continue
        for following in lines[index + 1:index + 3]:
            if match := re.fullmatch(r"(?P<count>\d{1,3})", following):
                return int(match.group("count"))
    patterns = (
        r"(?<![\d.$])(\d{1,3})(?![\d.])\s+(?:debit\s+)?(?:transactions?|debits?)"
        r"(?:\s+(?:legal\s+(?:disclaimer|bug)|footnote)\s*\d{1,3})?\s*(?:/|per)\s*month",
        r"(?<![\d.$])(\d{1,3})(?![\d.])\s+(?:debit\s+)?transactions?"
        r"[^a-z0-9$]{0,32}included\s+(?:each|per)\s+month",
        r"(?<![\d.$])(\d{1,3})(?![\d.])\s+(?:free\s+)?(?:debit\s+)?transactions?"
        r"(?:\s+\d{1,2})?\s+per\s+month",
        r"(?:includes?|included)\s+(?<![\d.$])(\d{1,3})(?![\d.])\s+(?:free\s+)?(?:transactions?|debits?|withdrawals?)",
        r"(?<![\d.$])(\d{1,3})(?![\d.])\s+included\s+(?:debit\s+)?transactions?",
        r"(?<![\d.$])(\d{1,3})(?![\d.])\s+(?:debit\s+)?transactions?\s+each\s+month",
        r"(?<![\d.$])(\d{1,3})(?![\d.])\s+(?:free\s+)?(?:transactions?|debits?|withdrawals?)\s+(?:included|(?:/|per)\s*month|a month)",
        r"(?<![\d.$])(\d{1,3})(?![\d.])\s+(?:transactions?|debits?)\s+included",
        r"up\s+to\s+(?<![\d.$])(\d{1,3})(?![\d.])(?!\s+(?:days?|months?|years?))\s+[\w\s-]{0,80}?(?:transactions?|debits?|withdrawals?)",
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


def _has_account_wide_unlimited_transactions(text: str) -> bool:
    """Recognize account-wide unlimited banking, excluding channel perks."""

    normalized = _normalize_text(text).lower()
    if re.search(
        r"\btransactions?\b[^a-z]{0,32}(?:included\s+)?per\s+month\b[^a-z]{0,32}unlimited\b",
        normalized,
    ):
        return True
    if re.search(
        r"\btransactions?(?:\s+\d{1,2})?\s+included\s+per\s+month"
        r"(?:\s+\d{1,2})?\s+unlimited\b",
        normalized,
    ):
        return True
    if re.search(r"\bunlimited\s+(?:everyday\s+)?(?:debit\s+|banking\s+)?transactions?\b", normalized):
        return True
    activity_list = re.search(
        r"\bunlimited\b[\s\S]{0,120}?\bdebit\s+purchases?\b[\s\S]{0,80}?"
        r"\bbill\s+payments?\b[\s\S]{0,80}?\bwithdrawals?\b",
        normalized,
    )
    if activity_list is not None:
        return True
    return False


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
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    normalized = unit.lower()
    if normalized.startswith("day"):
        days = decimal_value
    elif normalized.startswith("month"):
        days = decimal_value * Decimal("30")
    elif normalized.startswith("year"):
        days = decimal_value * Decimal("365")
    else:
        return None
    if days != days.to_integral_value():
        days = (days + Decimal("0.5")).to_integral_value()
    return int(days)


def _normalize_text(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()


def _normalize_decimal(value: str) -> str:
    try:
        decimal_value = Decimal(value.replace(",", ""))
    except InvalidOperation:
        return value.replace(",", "")
    return f"{decimal_value:.2f}"


def _rate_percentage_context_window(*, text: str, start: int, end: int, radius: int = 100) -> str:
    window_start = max(0, start - radius)
    window_end = min(len(text), end + radius)
    return text[window_start:window_end].lower()


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
    product_family = _infer_product_family(context)
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
            "product_family": product_family,
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
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
