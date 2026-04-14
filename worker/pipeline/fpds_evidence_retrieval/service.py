from __future__ import annotations

import os
import re

from .models import (
    EvidenceChunkCandidate,
    EvidenceMatch,
    EvidenceRetrievalRequest,
    EvidenceRetrievalResult,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_FIELD_HINTS: dict[str, tuple[str, ...]] = {
    "monthly_fee": ("monthly fee", "account fee", "service fee", "fee"),
    "public_display_fee": ("monthly fee", "account fee", "fee"),
    "fee_waiver_condition": ("fee waiver", "waive fee", "waived", "maintain balance"),
    "minimum_balance": ("minimum balance", "maintain balance", "minimum daily balance"),
    "minimum_deposit": ("minimum deposit", "opening deposit", "deposit amount"),
    "standard_rate": ("standard rate", "interest rate", "regular rate", "annual rate"),
    "promotional_rate": ("promotional rate", "bonus rate", "promo rate", "special rate"),
    "public_display_rate": ("interest rate", "rate", "earn", "%"),
    "promotional_period_text": ("promo period", "offer ends", "promotional period", "for the first"),
    "introductory_rate_flag": ("introductory", "promotional", "bonus"),
    "eligibility_text": ("eligible", "eligibility", "qualify", "who can apply"),
    "interest_calculation_method": ("calculated daily", "daily closing balance", "interest is calculated"),
    "interest_payment_frequency": ("paid monthly", "monthly", "interest is paid", "payment frequency"),
    "tiered_rate_flag": ("tiered", "tiers", "interest rate tiers"),
    "tier_definition_text": ("tier", "tiers", "balance range"),
    "withdrawal_limit_text": ("withdrawal", "withdrawals", "debit transaction", "transaction limit"),
    "registered_flag": ("tfsa", "rrsp", "registered"),
    "term_length_text": ("term", "term length", "year term", "month term", "days"),
    "term_length_days": ("term", "year", "month", "days"),
    "redeemable_flag": ("redeemable", "cashable", "early redemption"),
    "non_redeemable_flag": ("non-redeemable", "non redeemable", "non-cashable", "non cashable"),
    "compounding_frequency": ("compounded", "compounding", "compound interest"),
    "payout_option": ("paid monthly", "paid annually", "at maturity", "interest paid"),
    "registered_plan_supported": ("tfsa", "rrsp", "rrif", "registered plan", "registered account"),
    "included_transactions": ("transactions included", "debits included", "transactions per month", "free transactions"),
    "unlimited_transactions_flag": ("unlimited transactions", "unlimited debits", "unlimited banking"),
    "interac_e_transfer_included": ("interac e-transfer", "e-transfer included", "free e-transfer"),
    "overdraft_available": ("overdraft", "overdraft protection"),
    "cheque_book_info": ("cheque book", "cheques", "checks"),
    "student_plan_flag": ("student", "student banking", "youth"),
    "newcomer_plan_flag": ("newcomer", "new to canada"),
    "description_short": ("account", "savings", "earn", "designed for"),
    "notes": ("note", "additional information", "important", "conditions apply"),
}


class EvidenceRetrievalService:
    def retrieve(
        self,
        *,
        request: EvidenceRetrievalRequest,
        candidates: list[EvidenceChunkCandidate],
    ) -> EvidenceRetrievalResult:
        applied_mode, runtime_notes = _resolve_retrieval_mode(request.retrieval_mode)
        filtered_candidates = [candidate for candidate in candidates if _matches_metadata_filters(candidate, request)]

        matches: list[EvidenceMatch] = []
        for field_name in request.field_names:
            ranked = sorted(
                (
                    _build_match(
                        field_name=field_name,
                        candidate=candidate,
                        retrieval_mode=applied_mode,
                    )
                    for candidate in filtered_candidates
                ),
                key=lambda item: (-item.score, item.chunk_index, item.evidence_chunk_id),
            )
            selected = [item for item in ranked if item.score > 0][: request.max_matches_per_field]
            matches.extend(selected)

        return EvidenceRetrievalResult(
            correlation_id=request.correlation_id,
            run_id=request.run_id,
            parsed_document_id=request.parsed_document_id,
            requested_retrieval_mode=request.retrieval_mode,
            applied_retrieval_mode=applied_mode,
            matches=matches,
            runtime_notes=runtime_notes,
        )


def _build_match(
    *,
    field_name: str,
    candidate: EvidenceChunkCandidate,
    retrieval_mode: str,
) -> EvidenceMatch:
    keywords = _build_keywords(field_name)
    excerpt_text = candidate.evidence_excerpt.lower()
    anchor_text = (candidate.anchor_value or "").lower()
    excerpt_tokens = set(_tokenize(candidate.evidence_excerpt))
    keyword_tokens = set(token for keyword in keywords for token in _tokenize(keyword))

    overlap_tokens = sorted(excerpt_tokens & keyword_tokens)
    overlap_score = min(0.55, len(overlap_tokens) * 0.12)
    phrase_hits = [keyword for keyword in keywords if " " in keyword and keyword in excerpt_text]
    phrase_score = min(0.25, len(phrase_hits) * 0.12)
    anchor_hits = [keyword for keyword in keywords if keyword in anchor_text]
    anchor_score = min(0.1, len(anchor_hits) * 0.05)
    lexical_signal_bonus = _field_signal_bonus(field_name=field_name, excerpt_text=excerpt_text)
    score = round(min(0.99, overlap_score + phrase_score + anchor_score + lexical_signal_bonus), 4)

    return EvidenceMatch(
        evidence_chunk_id=candidate.evidence_chunk_id,
        field_name=field_name,
        score=score,
        retrieval_mode=retrieval_mode,
        evidence_text_excerpt=candidate.evidence_excerpt,
        source_document_id=candidate.source_document_id,
        source_snapshot_id=candidate.source_snapshot_id,
        model_execution_id=None,
        parsed_document_id=candidate.parsed_document_id,
        anchor_type=candidate.anchor_type,
        anchor_value=candidate.anchor_value,
        page_no=candidate.page_no,
        chunk_index=candidate.chunk_index,
        match_metadata={
            "matched_keywords": sorted(set([*phrase_hits, *anchor_hits, *overlap_tokens])),
            "source_type": candidate.source_type,
            "source_language": candidate.source_language,
        },
    )


def _build_keywords(field_name: str) -> tuple[str, ...]:
    normalized_field_name = field_name.strip().lower()
    default_terms = tuple(token for token in normalized_field_name.split("_") if token)
    hinted_terms = _FIELD_HINTS.get(normalized_field_name, ())
    merged = []
    for item in (*hinted_terms, *default_terms, normalized_field_name.replace("_", " ")):
        if item and item not in merged:
            merged.append(item)
    return tuple(merged)


def _matches_metadata_filters(candidate: EvidenceChunkCandidate, request: EvidenceRetrievalRequest) -> bool:
    filters = request.metadata_filters
    if filters.bank_code and candidate.bank_code != filters.bank_code:
        return False
    if filters.country_code and candidate.country_code != filters.country_code:
        return False
    if filters.source_language and candidate.source_language != filters.source_language:
        return False
    if filters.source_types and candidate.source_type not in filters.source_types:
        return False
    if filters.source_document_ids and candidate.source_document_id not in filters.source_document_ids:
        return False
    if filters.anchor_types and candidate.anchor_type not in filters.anchor_types:
        return False
    return True


def _resolve_retrieval_mode(requested_mode: str) -> tuple[str, list[str]]:
    normalized = requested_mode.strip().lower() or "metadata-only"
    if normalized == "metadata-only":
        return "metadata-only", []

    if normalized == "vector-assisted":
        backend = os.getenv("FPDS_VECTOR_BACKEND", "pgvector")
        return (
            "metadata-only",
            [f"Vector-assisted retrieval requested but not implemented in the current worker; falling back to metadata-only while `FPDS_VECTOR_BACKEND={backend}` remains a future extension point."],
        )

    return "metadata-only", [f"Unsupported retrieval_mode `{requested_mode}` requested; falling back to metadata-only."]


def _field_signal_bonus(*, field_name: str, excerpt_text: str) -> float:
    if "rate" in field_name and ("%" in excerpt_text or "interest" in excerpt_text):
        return 0.18
    if "fee" in field_name and ("fee" in excerpt_text or "$" in excerpt_text):
        return 0.18
    if "balance" in field_name and "balance" in excerpt_text:
        return 0.18
    if "eligibility" in field_name and ("eligible" in excerpt_text or "qualify" in excerpt_text):
        return 0.18
    if "payment_frequency" in field_name and "monthly" in excerpt_text:
        return 0.18
    if "calculation_method" in field_name and "calculated" in excerpt_text:
        return 0.18
    if "term_length" in field_name and any(token in excerpt_text for token in ("term", "year", "month", "day")):
        return 0.18
    if "redeemable" in field_name and any(token in excerpt_text for token in ("redeemable", "cashable")):
        return 0.18
    if "compounding" in field_name and any(token in excerpt_text for token in ("compounded", "compound interest")):
        return 0.18
    if "payout_option" in field_name and any(token in excerpt_text for token in ("paid", "maturity", "interest paid")):
        return 0.18
    if "registered" in field_name and any(token in excerpt_text for token in ("tfsa", "rrsp", "rrif", "registered")):
        return 0.18
    if "transactions" in field_name and any(token in excerpt_text for token in ("transaction", "debit", "unlimited")):
        return 0.18
    if "transfer" in field_name and any(token in excerpt_text for token in ("e-transfer", "interac")):
        return 0.18
    if "overdraft" in field_name and "overdraft" in excerpt_text:
        return 0.18
    if "cheque" in field_name and any(token in excerpt_text for token in ("cheque", "check")):
        return 0.18
    if "student_plan_flag" in field_name and any(token in excerpt_text for token in ("student", "youth")):
        return 0.18
    if "newcomer_plan_flag" in field_name and any(token in excerpt_text for token in ("newcomer", "new to canada")):
        return 0.18
    return 0.05


def _tokenize(value: str) -> list[str]:
    return _TOKEN_RE.findall(value.lower())
