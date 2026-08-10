from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation

from worker.pipeline.fpds_rate_safety import (
    bounded_rate_evidence_context,
    canonical_deposit_rate_suppression_reason,
    expired_promotional_offer_end_date,
)

_PERCENT_RE = re.compile(r"(?<!\d)(\d{1,2}(?:\.\d{1,4})?)\s*%")
_TERM_RATE_ROW_RE = re.compile(
    r"(?P<term>\d{1,3}(?:\.\d{1,2})?\s*(?:days?|months?|years?))\b"
    r"(?P<body>[^%\n\r]{0,120}?)"
    r"(?P<rate>(?<![\d.,])\d{1,2}(?:\.\d{1,4})?)\s*%",
    re.IGNORECASE,
)
_BALANCE_LINE_RE = re.compile(r"^\$[0-9,]")
_WHITESPACE_RE = re.compile(r"\s+")
_MONTH_RE = re.compile(r"\b(month|months|monthly|next month)\b", re.IGNORECASE)

_TARGET_SUPPORT_SOURCE_IDS = {
    "BMO-SAV-002": ("BMO-SAV-006",),
    "BMO-SAV-003": ("BMO-SAV-006",),
    "BMO-SAV-004": ("BMO-SAV-006",),
    "CIBC-SAV-002": ("CIBC-SAV-004",),
    "CIBC-SAV-003": ("CIBC-SAV-004",),
    "TD-SAV-002": ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"),
    "TD-SAV-003": ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"),
    "TD-SAV-004": ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"),
    "SCOTIA-SAV-004": ("SCOTIA-SAV-006",),
}
_TARGET_MATCH_TERMS = {
    "BMO-SAV-002": ("savings amplifier account", "savings amplifier"),
    "BMO-SAV-003": ("savings builder account", "savings builder"),
    "BMO-SAV-004": ("premium rate savings account", "premium rate savings"),
    "CIBC-SAV-002": ("cibc eadvantage savings account", "eadvantage savings"),
    "CIBC-SAV-003": ("cibc us$ personal account", "cibc us personal account", "us$ personal account", "us personal account"),
    "TD-SAV-002": ("td every day savings account", "every day savings"),
    "TD-SAV-003": ("td epremium savings account", "epremium savings"),
    "TD-SAV-004": ("td growth savings account", "growth savings"),
    "SCOTIA-SAV-004": ("money master savings account", "money master savings"),
}
_SUPPORTING_ROLE_FIELDS = {
    "account_comparison_rows",
    "account_fee_table",
    "account_interest_rates",
    "interest_rate_summary",
    "savings_rate_table",
    "savings_account_rates",
    "rate_tiers",
    "term_rate_table",
    "standard_rate",
    "public_display_rate",
    "promotional_rate",
    "monthly_fee",
    "public_display_fee",
    "fee_waiver_condition",
    "cashable_gic_rates",
    "non_cashable_gic_rates",
    "non_redeemable_gic_rates",
    "redeemable_gic_rates",
    "market_growth_gic_rates",
    "gic_rates",
    "term_deposit_rates",
    "product_variants",
    "product_comparison_rows",
    "minimum_guaranteed_return",
    "maximum_return",
    "minimum_deposit",
    "minimum_balance",
    "early_withdrawal_penalty",
}
_EXPIRY_SENSITIVE_FIELDS = {
    "standard_rate",
    "public_display_rate",
    "base_12_month_rate",
    "promotional_rate",
    "promotional_period_text",
    "introductory_rate_flag",
    "effective_date",
    "term_rate_table",
    "term_length_text",
    "term_length_days",
}


def supporting_source_ids_for_target(source_id: str) -> tuple[str, ...]:
    return _TARGET_SUPPORT_SOURCE_IDS.get(source_id, ())


def merge_supporting_artifacts(
    *,
    target_source_id: str,
    base_artifact: dict[str, object],
    supporting_artifacts: dict[str, dict[str, object]],
    missing_support_source_ids: list[str] | None = None,
) -> dict[str, object]:
    merged_artifact = {
        **base_artifact,
        "extracted_fields": [dict(item) for item in base_artifact.get("extracted_fields", [])],
        "evidence_links": [dict(item) for item in base_artifact.get("evidence_links", [])],
        "runtime_notes": list(base_artifact.get("runtime_notes", [])),
    }
    extracted_fields = merged_artifact["extracted_fields"]
    evidence_links = merged_artifact["evidence_links"]
    runtime_notes = merged_artifact["runtime_notes"]
    _remove_expired_offer_fields(
        extracted_fields=extracted_fields,
        evidence_links=evidence_links,
        runtime_notes=runtime_notes,
    )
    field_records = _field_record_map(extracted_fields)

    if missing_support_source_ids:
        runtime_notes.append(
            "Supporting-source merge skipped for missing extraction artifacts: "
            + ", ".join(sorted(dict.fromkeys(missing_support_source_ids)))
            + "."
        )

    for support_source_id, payload in supporting_artifacts.items():
        if support_source_id == "TD-SAV-005":
            supplement = _build_current_rate_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "TD-SAV-007":
            supplement = _build_fee_pdf_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "TD-SAV-008":
            supplement = _build_interest_pdf_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "SCOTIA-SAV-006":
            supplement = _build_scotia_rate_page_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "BMO-SAV-006":
            supplement = _build_bmo_rate_page_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "CIBC-SAV-004":
            supplement = _build_cibc_rate_page_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        else:
            supplement = _build_generic_support_supplement(
                target_source_id=target_source_id,
                base_artifact=merged_artifact,
                support_source_id=support_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )

        runtime_notes.extend(supplement["runtime_notes"])
        if not supplement["field_updates"]:
            continue

        for field_name, field_record in supplement["field_updates"].items():
            _upsert_field_record(extracted_fields, field_record)
            field_records[field_name] = field_record
        for field_name, link_record in supplement["evidence_updates"].items():
            _upsert_evidence_link(evidence_links, field_name=field_name, link_record=link_record)

    _cleanup_target_artifact(
        target_source_id=target_source_id,
        extracted_fields=extracted_fields,
        evidence_links=evidence_links,
        runtime_notes=runtime_notes,
    )
    return merged_artifact


def _remove_expired_offer_fields(
    *,
    extracted_fields: list[dict[str, object]],
    evidence_links: list[dict[str, object]],
    runtime_notes: list[str],
) -> None:
    expired_fields = {
        str(record.get("field_name") or "")
        for record in extracted_fields
        if str(record.get("field_name") or "") in _EXPIRY_SENSITIVE_FIELDS
        and expired_promotional_offer_end_date(str(record.get("evidence_text_excerpt") or "")) is not None
    }
    if not expired_fields:
        return
    for field_name in sorted(expired_fields):
        _remove_field(extracted_fields, evidence_links, field_name)
    runtime_notes.append(
        "Suppressed fields backed by an explicitly expired promotional offer before supporting-source merge: "
        + ", ".join(f"`{field_name}`" for field_name in sorted(expired_fields))
        + "."
    )


def _build_generic_support_supplement(
    *,
    target_source_id: str,
    base_artifact: dict[str, object],
    support_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    product_type_family = _canonical_product_type_family(
        str(base_artifact.get("schema_context", {}).get("product_type") or "")
    )
    if product_type_family not in {
        "chequing",
        "savings",
        "gic",
        "mortgage",
        "personal-loan",
        "line-of-credit",
    }:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    terms = _target_terms_from_artifact(base_artifact)
    if not terms and product_type_family != "gic":
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if product_type_family in {"mortgage", "personal-loan", "line-of-credit"}:
        rate_result = _build_generic_lending_rate_supplement(
            target_source_id=target_source_id,
            support_source_id=support_source_id,
            supporting_artifact=supporting_artifact,
            terms=terms,
            product_type=product_type_family,
            existing_fields=existing_fields,
        )
        companion_result = _build_generic_lending_companion_supplement(
            target_source_id=target_source_id,
            support_source_id=support_source_id,
            supporting_artifact=supporting_artifact,
            terms=terms,
            product_type=product_type_family,
            expected_fields={
                str(field_name)
                for field_name in base_artifact.get("schema_context", {}).get("expected_fields", [])
            },
            existing_fields={**existing_fields, **dict(rate_result["field_updates"])},
        )
        for key in ("field_updates", "evidence_updates"):
            rate_result[key] = {**dict(rate_result[key]), **dict(companion_result[key])}
        rate_result["runtime_notes"] = [
            *list(rate_result["runtime_notes"]),
            *list(companion_result["runtime_notes"]),
        ]
        return rate_result

    target_currency = _target_currency_from_artifact(base_artifact)
    matches = [
        match
        for match in supporting_artifact.get("retrieval_result", {}).get("matches", [])
        if _support_match_currency_is_compatible(
            target_currency=target_currency,
            match=match,
        )
    ]
    expected_fields = {
        str(field_name)
        for field_name in base_artifact.get("schema_context", {}).get("expected_fields", [])
    }
    penalty_result = {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    if (
        product_type_family == "gic"
        and "early_withdrawal_penalty" in expected_fields
        and "early_withdrawal_penalty" not in existing_fields
    ):
        penalty_result = _build_generic_cd_penalty_supplement(
            target_source_id=target_source_id,
            support_source_id=support_source_id,
            supporting_artifact=supporting_artifact,
            terms=terms,
        )
    if not matches:
        return penalty_result

    if product_type_family == "chequing":
        return _build_generic_chequing_fee_supplement(
            target_source_id=target_source_id,
            support_source_id=support_source_id,
            matches=matches,
            terms=terms,
            existing_fields=existing_fields,
        )
    if product_type_family == "savings":
        rate_result = _build_generic_savings_rate_supplement(
            target_source_id=target_source_id,
            support_source_id=support_source_id,
            matches=matches,
            terms=terms,
            existing_fields=existing_fields,
        )
        fee_result = _build_generic_savings_fee_supplement(
            target_source_id=target_source_id,
            support_source_id=support_source_id,
            matches=matches,
            terms=terms,
            existing_fields={
                **existing_fields,
                **dict(rate_result["field_updates"]),
            },
        )
        for key in ("field_updates", "evidence_updates"):
            rate_result[key] = {**dict(rate_result[key]), **dict(fee_result[key])}
        rate_result["runtime_notes"] = [
            *list(rate_result["runtime_notes"]),
            *list(fee_result["runtime_notes"]),
        ]
        return rate_result
    gic_result = _build_generic_gic_rate_supplement(
        target_source_id=target_source_id,
        support_source_id=support_source_id,
        matches=matches,
        terms=terms,
        existing_fields=existing_fields,
        allow_family_table_aggregation=_is_generic_gic_family_artifact(base_artifact),
    )
    if penalty_result["field_updates"]:
        for key in ("field_updates", "evidence_updates"):
            gic_result[key] = {**dict(gic_result[key]), **dict(penalty_result[key])}
        gic_result["runtime_notes"] = [
            *list(gic_result["runtime_notes"]),
            *list(penalty_result["runtime_notes"]),
        ]
    return gic_result


def _build_generic_cd_penalty_supplement(
    *,
    target_source_id: str,
    support_source_id: str,
    supporting_artifact: dict[str, object],
    terms: tuple[str, ...],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if not terms:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    for raw_field in supporting_artifact.get("extracted_fields", []):
        if not isinstance(raw_field, dict) or raw_field.get("field_name") != "early_withdrawal_penalty":
            continue
        metadata = raw_field.get("field_metadata")
        field_metadata = metadata if isinstance(metadata, dict) else {}
        evidence_quote = str(
            field_metadata.get("evidence_quote")
            or raw_field.get("evidence_text_excerpt")
            or ""
        ).strip()
        official_sources = field_metadata.get("official_web_sources")
        if not (
            field_metadata.get("official_grounding_contract_version") == "collection-official-grounding-v2"
            and str(field_metadata.get("official_verification_status") or "") in {"match", "mismatch"}
            and evidence_quote
            and isinstance(official_sources, list)
            and any(isinstance(source, dict) and str(source.get("url") or "").strip() for source in official_sources)
        ):
            continue
        normalized_quote = _normalize_text(evidence_quote)
        if not any(term and term in normalized_quote for term in terms):
            continue
        candidate_value = str(raw_field.get("candidate_value") or "").strip()
        normalized_value = _normalize_text(candidate_value)
        if not (
            any(marker in normalized_value for marker in ("early withdrawal", "withdraw before maturity", "withdrawal before maturity"))
            and re.search(r"(?:\$\s*\d|\d+(?:\.\d+)?\s*%|\b\d+\s+(?:days?|months?)\s+(?:of\s+)?interest\b)", candidate_value, flags=re.IGNORECASE)
        ):
            continue
        field_record = {
            **raw_field,
            "field_metadata": {
                **field_metadata,
                "supporting_source_id": support_source_id,
                "supporting_merge": True,
                "generic_supporting_merge": True,
            },
        }
        link_record = {
            "field_name": "early_withdrawal_penalty",
            "candidate_value": candidate_value,
            "evidence_chunk_id": raw_field.get("evidence_chunk_id"),
            "evidence_text_excerpt": evidence_quote,
            "source_document_id": raw_field.get("source_document_id"),
            "source_snapshot_id": raw_field.get("source_snapshot_id"),
            "citation_confidence": raw_field.get("confidence"),
            "model_execution_id": None,
            "anchor_type": raw_field.get("anchor_type"),
            "anchor_value": raw_field.get("anchor_value"),
            "page_no": raw_field.get("page_no"),
            "chunk_index": raw_field.get("chunk_index"),
        }
        return {
            "field_updates": {"early_withdrawal_penalty": field_record},
            "evidence_updates": {"early_withdrawal_penalty": link_record},
            "runtime_notes": [
                f"Supplemented the missing CD early-withdrawal penalty for `{target_source_id}` from exact-product official supporting source `{support_source_id}`."
            ],
        }
    return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}


def _build_generic_lending_rate_supplement(
    *,
    target_source_id: str,
    support_source_id: str,
    supporting_artifact: dict[str, object],
    terms: tuple[str, ...],
    product_type: str,
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    """Carry exact-product, officially grounded lending rates across sources.

    Lending rate pages often sit beside, rather than inside, the product detail
    page. Only AI-grounded support fields with an official consulted URL and an
    exact quote are eligible. Scalar rates are deliberately preserved as a
    qualified source-language summary so ranges, examples, dates, credit
    assumptions, and discounts are not flattened into a misleading number.
    """

    if "interest_rate_summary" in existing_fields:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    eligible_names = {
        "interest_rate_summary",
        "interest_rate",
        "mortgage_rate",
        "public_display_rate",
        "annual_percentage_rate",
        "apr",
    }
    ranked: list[tuple[float, dict[str, object], str]] = []
    for raw_field in supporting_artifact.get("extracted_fields", []):
        if not isinstance(raw_field, dict):
            continue
        field_name = str(raw_field.get("field_name") or "")
        if field_name not in eligible_names:
            continue
        metadata = raw_field.get("field_metadata")
        field_metadata = metadata if isinstance(metadata, dict) else {}
        official_sources = field_metadata.get("official_web_sources")
        evidence_quote = str(
            field_metadata.get("evidence_quote")
            or raw_field.get("evidence_text_excerpt")
            or ""
        ).strip()
        officially_grounded = (
            field_metadata.get("official_grounding_contract_version")
            == "collection-official-grounding-v2"
            and str(field_metadata.get("official_verification_status") or "")
            in {"match", "mismatch"}
            and bool(evidence_quote)
            and isinstance(official_sources, list)
            and any(
                isinstance(source, dict) and str(source.get("url") or "").strip()
                for source in official_sources
            )
        )
        if not officially_grounded:
            continue

        candidate_value = str(raw_field.get("candidate_value") or "").strip()
        rate_context = " ".join(value for value in (candidate_value, evidence_quote) if value)
        if "%" not in rate_context or not _lending_rate_has_local_target_identity(
            evidence_quote,
            terms=terms,
        ):
            continue
        try:
            confidence = float(raw_field.get("confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        ranked.append((confidence, raw_field, evidence_quote))

    if not ranked:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    ranked.sort(key=lambda item: item[0], reverse=True)
    _, source_field, evidence_quote = ranked[0]
    source_name = str(source_field.get("field_name") or "")
    source_value = str(source_field.get("candidate_value") or "").strip()
    # US mortgage examples are commonly scenario-priced. Preserve the exact
    # official sentence(s), including geography, LTV, credit, points, lock and
    # other assumptions, instead of publishing a deceptively bare rate/APR.
    summary = (
        evidence_quote
        if product_type == "mortgage"
        else source_value if source_name == "interest_rate_summary" and "%" in source_value else evidence_quote
    )
    summary = _compact_lending_rate_summary(summary)
    if not summary or "%" not in summary:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    source_metadata = source_field.get("field_metadata")
    field_record = {
        **source_field,
        "field_name": "interest_rate_summary",
        "candidate_value": summary,
        "value_type": "string",
        "extraction_method": "generic_supporting_lending_rate_merge",
        "field_metadata": {
            **(source_metadata if isinstance(source_metadata, dict) else {}),
            "supporting_source_id": support_source_id,
            "supporting_merge": True,
            "generic_supporting_merge": True,
            "supporting_original_field_name": source_name,
        },
    }
    link_record = {
        "field_name": "interest_rate_summary",
        "candidate_value": summary,
        "evidence_chunk_id": source_field.get("evidence_chunk_id"),
        "evidence_text_excerpt": evidence_quote,
        "source_document_id": source_field.get("source_document_id"),
        "source_snapshot_id": source_field.get("source_snapshot_id"),
        "citation_confidence": source_field.get("confidence"),
        "model_execution_id": None,
        "anchor_type": source_field.get("anchor_type"),
        "anchor_value": source_field.get("anchor_value"),
        "page_no": source_field.get("page_no"),
        "chunk_index": source_field.get("chunk_index"),
    }
    return {
        "field_updates": {"interest_rate_summary": field_record},
        "evidence_updates": {"interest_rate_summary": link_record},
        "runtime_notes": [
            f"Supplemented the missing lending rate summary for `{target_source_id}` from exact-product official supporting source `{support_source_id}`."
        ],
    }


def _build_generic_lending_companion_supplement(
    *,
    target_source_id: str,
    support_source_id: str,
    supporting_artifact: dict[str, object],
    terms: tuple[str, ...],
    product_type: str,
    expected_fields: set[str],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    allowed_by_type = {
        "mortgage": {"rate_type", "term_length_text"},
        "personal-loan": {"loan_amount_text", "term_length_text"},
        "line-of-credit": {"credit_limit_text", "security_requirement", "collateral_text", "secured_flag"},
    }
    allowed_fields = allowed_by_type.get(product_type, set()).intersection(expected_fields)
    allowed_fields.difference_update(existing_fields)
    if not allowed_fields or not terms:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for raw_field in supporting_artifact.get("extracted_fields", []):
        if not isinstance(raw_field, dict):
            continue
        field_name = str(raw_field.get("field_name") or "")
        if field_name not in allowed_fields or field_name in field_updates:
            continue
        metadata = raw_field.get("field_metadata")
        field_metadata = metadata if isinstance(metadata, dict) else {}
        evidence_quote = str(
            field_metadata.get("evidence_quote")
            or raw_field.get("evidence_text_excerpt")
            or ""
        ).strip()
        official_sources = field_metadata.get("official_web_sources")
        if not (
            field_metadata.get("official_grounding_contract_version") == "collection-official-grounding-v2"
            and str(field_metadata.get("official_verification_status") or "") in {"match", "mismatch"}
            and evidence_quote
            and isinstance(official_sources, list)
            and any(isinstance(source, dict) and str(source.get("url") or "").strip() for source in official_sources)
            and any(term and term in _normalize_text(evidence_quote) for term in terms)
        ):
            continue
        candidate_value = raw_field.get("candidate_value")
        if candidate_value in (None, "", [], {}):
            continue
        field_updates[field_name] = {
            **raw_field,
            "field_metadata": {
                **field_metadata,
                "supporting_source_id": support_source_id,
                "supporting_merge": True,
                "generic_supporting_merge": True,
            },
        }
        evidence_updates[field_name] = {
            "field_name": field_name,
            "candidate_value": str(candidate_value),
            "evidence_chunk_id": raw_field.get("evidence_chunk_id"),
            "evidence_text_excerpt": evidence_quote,
            "source_document_id": raw_field.get("source_document_id"),
            "source_snapshot_id": raw_field.get("source_snapshot_id"),
            "citation_confidence": raw_field.get("confidence"),
            "model_execution_id": None,
            "anchor_type": raw_field.get("anchor_type"),
            "anchor_value": raw_field.get("anchor_value"),
            "page_no": raw_field.get("page_no"),
            "chunk_index": raw_field.get("chunk_index"),
        }
    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            f"Supplemented exact-product lending comparison fields for `{target_source_id}` from official supporting source `{support_source_id}`: "
            + ", ".join(f"`{field_name}`" for field_name in sorted(field_updates))
            + "."
        ]
        if field_updates
        else [],
    }


def _lending_rate_has_local_target_identity(excerpt: str, *, terms: tuple[str, ...]) -> bool:
    normalized = _normalize_text(excerpt)
    percent_positions = [match.start() for match in _PERCENT_RE.finditer(normalized)]
    if not percent_positions:
        return False
    for term in terms:
        if not term:
            continue
        start = normalized.find(term)
        while start >= 0:
            if any(abs(percent_position - start) <= 360 for percent_position in percent_positions):
                return True
            start = normalized.find(term, start + len(term))
    return False


def _compact_lending_rate_summary(value: str) -> str:
    normalized = _WHITESPACE_RE.sub(" ", str(value or "")).strip()
    if len(normalized) <= 700:
        return normalized
    percent_match = _PERCENT_RE.search(normalized)
    if percent_match is None:
        return ""
    start = max(0, percent_match.start() - 280)
    end = min(len(normalized), start + 700)
    return normalized[start:end].strip()


def _build_generic_savings_rate_supplement(
    *,
    target_source_id: str,
    support_source_id: str,
    matches: list[dict[str, object]],
    terms: tuple[str, ...],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    existing_tier = existing_fields.get("tier_definition_text")
    has_useful_tier = existing_tier is not None and _is_useful_savings_tier_record(existing_tier)
    if all(field_name in existing_fields for field_name in ("standard_rate", "public_display_rate")) and has_useful_tier:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    current_table_match = _find_current_savings_rate_table_match(matches, terms=terms)
    match = current_table_match or _find_generic_support_match(
        matches=matches,
        terms=terms,
        preferred_fields=(
            "standard_rate",
            "public_display_rate",
            "promotional_rate",
            "savings_account_rates",
            "account_interest_rates",
            "savings_rate_table",
            "interest_rate_summary",
            "rate_tiers",
            "tier_definition_text",
        ),
        require_percentage=True,
    )
    if match is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if current_table_match is not None:
        current_rate = _extract_current_savings_account_rate(
            str(match.get("evidence_text_excerpt", "")), terms=terms
        )
        rate_values = {
            "standard_rate": _format_decimal(current_rate),
            "public_display_rate": _format_decimal(current_rate),
        } if current_rate is not None else {}
    else:
        rate_values = _extract_generic_rate_values(str(match.get("evidence_text_excerpt", "")))
    rate_excerpt = str(match.get("evidence_text_excerpt", ""))
    tier_summary = _extract_savings_balance_tier_summary(rate_excerpt)
    if tier_summary is not None:
        lowered_rate_excerpt = _normalize_text(rate_excerpt)
        if not any(
            marker in lowered_rate_excerpt
            for marker in ("boosted rate", "bonus rate", "promotional rate", "promo rate")
        ):
            tier_rates = _extract_all_percentages(rate_excerpt)
            if tier_rates:
                highest_tier_rate = _format_decimal(max(tier_rates))
                rate_values["standard_rate"] = highest_tier_rate
                rate_values["public_display_rate"] = highest_tier_rate
        rate_values["tier_definition_text"] = tier_summary
        rate_values["tiered_rate_flag"] = True
    if not rate_values:
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                f"Generic savings support source `{support_source_id}` matched `{target_source_id}`, but the rate evidence did not contain a numeric percentage."
            ],
        }

    return _build_generic_field_updates(
        support_source_id=support_source_id,
        match=match,
        field_values=rate_values,
        existing_fields=existing_fields,
        extraction_method="generic_supporting_savings_rate_merge",
        runtime_note=f"Supplemented missing savings rate fields for `{target_source_id}` from generic supporting source `{support_source_id}`.",
    )


def _build_generic_savings_fee_supplement(
    *,
    target_source_id: str,
    support_source_id: str,
    matches: list[dict[str, object]],
    terms: tuple[str, ...],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if all(field_name in existing_fields for field_name in ("monthly_fee", "public_display_fee")):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    match = _find_generic_support_match(
        matches=matches,
        terms=terms,
        preferred_fields=("monthly_fee", "public_display_fee", "account_fee_table", "fees_text"),
        require_money=True,
    )
    if match is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    fee_values = _extract_generic_monthly_fee_values(
        str(match.get("evidence_text_excerpt", "")),
        terms=terms,
    )
    if not fee_values:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    return _build_generic_field_updates(
        support_source_id=support_source_id,
        match=match,
        field_values=fee_values,
        existing_fields=existing_fields,
        extraction_method="generic_supporting_savings_fee_merge",
        runtime_note=(
            f"Supplemented missing savings fee fields for `{target_source_id}` "
            f"from generic supporting source `{support_source_id}`."
        ),
    )


def _build_generic_chequing_fee_supplement(
    *,
    target_source_id: str,
    support_source_id: str,
    matches: list[dict[str, object]],
    terms: tuple[str, ...],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    match = _find_generic_support_match(
        matches=matches,
        terms=terms,
        preferred_fields=(
            "monthly_fee",
            "public_display_fee",
            "fee_waiver_condition",
            "account_comparison_rows",
            "account_fee_table",
            "product_comparison_rows",
        ),
        require_money=True,
    )
    result: dict[str, dict[str, dict[str, object]] | list[str]] = {
        "field_updates": {},
        "evidence_updates": {},
        "runtime_notes": [],
    }
    if match is not None:
        fee_values = _extract_generic_monthly_fee_values(
            str(match.get("evidence_text_excerpt", "")),
            terms=terms,
        )
        if fee_values:
            fee_result = _build_generic_field_updates(
                support_source_id=support_source_id,
                match=match,
                field_values=fee_values,
                existing_fields=existing_fields,
                extraction_method="generic_supporting_chequing_fee_merge",
                runtime_note=f"Supplemented missing chequing fee fields for `{target_source_id}` from generic supporting source `{support_source_id}`.",
            )
            result["field_updates"].update(fee_result["field_updates"])
            result["evidence_updates"].update(fee_result["evidence_updates"])
            result["runtime_notes"].extend(fee_result["runtime_notes"])
        elif not all(field_name in existing_fields for field_name in ("monthly_fee", "public_display_fee")):
            result["runtime_notes"].append(
                f"Generic chequing support source `{support_source_id}` matched `{target_source_id}`, but no canonical-safe monthly fee was found."
            )

    if "unlimited_transactions_flag" not in existing_fields:
        unlimited_match = _find_target_unlimited_transaction_match(matches=matches, terms=terms)
        if unlimited_match is not None:
            result["field_updates"]["unlimited_transactions_flag"] = _build_support_field(
                field_name="unlimited_transactions_flag",
                candidate_value=True,
                value_type="boolean",
                match=unlimited_match,
                extraction_method="generic_supporting_unlimited_transaction_merge",
                field_metadata={
                    "supporting_source_id": support_source_id,
                    "supporting_merge": True,
                    "generic_supporting_merge": True,
                },
            )
            result["evidence_updates"]["unlimited_transactions_flag"] = _build_support_link(
                field_name="unlimited_transactions_flag",
                candidate_value=True,
                match=unlimited_match,
            )
            result["runtime_notes"].append(
                f"Supplemented an explicit account-wide unlimited-transaction flag for `{target_source_id}` from generic supporting source `{support_source_id}`."
            )
    return result


def _build_generic_gic_rate_supplement(
    *,
    target_source_id: str,
    support_source_id: str,
    matches: list[dict[str, object]],
    terms: tuple[str, ...],
    existing_fields: dict[str, dict[str, object]],
    allow_family_table_aggregation: bool = False,
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    desired_fields = ("standard_rate", "public_display_rate", "base_12_month_rate", "minimum_deposit", "term_rate_table")
    if all(
        field_name in existing_fields and not _is_invalid_gic_rate_record(field_name, existing_fields[field_name])
        for field_name in desired_fields
    ):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    minimum_result = _build_generic_gic_minimum_supplement(
        target_source_id=target_source_id,
        support_source_id=support_source_id,
        matches=matches,
        existing_fields=existing_fields,
    )

    current_table_match = (
        _find_current_gic_rate_table_match(matches)
        if allow_family_table_aggregation
        else None
    )
    structured_matches = [
        item
        for item in matches
        if str(item.get("field_name")) == "term_rate_table"
        and not _gic_structured_match_is_cross_product(str(item.get("evidence_text_excerpt", "")))
        and bool(_extract_generic_gic_rate_values(str(item.get("evidence_text_excerpt", ""))).get("term_rate_table"))
    ]
    match = current_table_match or _find_generic_support_match(
        matches=matches,
        terms=terms,
        preferred_fields=(
            "standard_rate",
            "public_display_rate",
            "promotional_rate",
            "cashable_gic_rates",
            "non_cashable_gic_rates",
            "non_redeemable_gic_rates",
            "redeemable_gic_rates",
            "market_growth_gic_rates",
            "gic_rates",
            "term_deposit_rates",
            "product_variants",
            "minimum_guaranteed_return",
            "maximum_return",
            "rate_tiers",
            "term_rate_table",
        ),
        require_percentage=True,
        allow_structured_gic_table=allow_family_table_aggregation,
    )
    if match is None:
        return minimum_result

    if current_table_match is not None:
        rate_values = _extract_current_gic_rate_values(str(match.get("evidence_text_excerpt", "")))
    elif allow_family_table_aggregation and structured_matches:
        match, rate_values = _aggregate_gic_family_rate_matches(structured_matches)
    else:
        rate_values = _extract_generic_gic_rate_values(str(match.get("evidence_text_excerpt", "")))
    if not rate_values:
        minimum_result["runtime_notes"] = [
            *list(minimum_result["runtime_notes"]),
            f"Generic GIC support source `{support_source_id}` matched `{target_source_id}`, but the rate evidence did not contain a numeric percentage."
        ]
        return minimum_result

    rate_result = _build_generic_field_updates(
        support_source_id=support_source_id,
        match=match,
        field_values=rate_values,
        existing_fields=existing_fields,
        extraction_method="generic_supporting_gic_rate_merge",
        runtime_note=f"Supplemented missing GIC rate fields for `{target_source_id}` from generic supporting source `{support_source_id}`.",
    )
    for key in ("field_updates", "evidence_updates"):
        rate_result[key] = {**dict(rate_result[key]), **dict(minimum_result[key])}
    rate_result["runtime_notes"] = [
        *list(rate_result["runtime_notes"]),
        *list(minimum_result["runtime_notes"]),
    ]
    return rate_result


def _build_generic_gic_minimum_supplement(
    *,
    target_source_id: str,
    support_source_id: str,
    matches: list[dict[str, object]],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    """Merge only an explicit product-wide GIC minimum; never infer one from fees or examples."""

    if "minimum_deposit" in existing_fields:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    match = next(
        (
            item
            for item in matches
            if _explicit_product_wide_gic_minimum(
                str(item.get("evidence_text_excerpt") or "")
            )
            is not None
        ),
        None,
    )
    if match is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    minimum = _explicit_product_wide_gic_minimum(
        str(match.get("evidence_text_excerpt") or "")
    )
    if minimum is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    return _build_generic_field_updates(
        support_source_id=support_source_id,
        match=match,
        field_values={"minimum_deposit": _format_decimal(minimum)},
        existing_fields=existing_fields,
        extraction_method="generic_supporting_gic_minimum_merge",
        runtime_note=(
            f"Supplemented an explicit product-wide GIC minimum for `{target_source_id}` "
            f"from generic supporting source `{support_source_id}`."
        ),
    )


def _explicit_product_wide_gic_minimum(excerpt: str) -> Decimal | None:
    normalized = _normalize_text(excerpt)
    if not re.search(r"\b(?:gic|guaranteed investment certificate)s?\b", normalized, flags=re.IGNORECASE):
        return None
    zero_patterns = (
        r"\bno\s+minimum\s+(?:balance|deposit|investment)\s+(?:is\s+)?required\s+to\s+(?:open|purchase|invest\s+in)\s+(?:(?:a|an|any|our|this|the)\s+)?(?:[a-z][a-z&.-]*\s+){0,4}(?:gic|guaranteed investment certificate)s?\b",
        r"\b(?:gic|guaranteed investment certificate)s?\b.{0,80}\b(?:minimum\s+(?:balance|deposit|investment)|(?:balance|deposit|investment)\s+minimum)\b.{0,30}\b(?:none|no\s+minimum|\$\s*0(?:\.00)?)\b",
        r"\b(?:none|no\s+minimum|\$\s*0(?:\.00)?)\b.{0,30}\b(?:minimum\s+(?:balance|deposit|investment)|(?:balance|deposit|investment)\s+minimum)\b.{0,80}\b(?:gic|guaranteed investment certificate)s?\b",
    )
    if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in zero_patterns):
        return Decimal("0")
    numeric_patterns = (
        r"\b(?:all|any|our)\s+(?:gic|guaranteed investment certificate)s?\b.{0,100}\b(?:minimum\s+(?:deposit|investment)|initial\s+investment)\s+(?:of|is|:)\s*\$\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)",
        r"\b(?:minimum\s+(?:deposit|investment)|initial\s+investment)\s+(?:of|is|:)\s*\$\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?).{0,100}\b(?:for\s+)?(?:all|any|our)\s+(?:gic|guaranteed investment certificate)s?\b",
    )
    for pattern in numeric_patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match is not None:
            return _to_decimal(match.group("amount").replace(",", ""))
    return None


def _aggregate_gic_family_rate_matches(
    matches: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    rows_by_key: dict[tuple[int | str, str], dict[str, object]] = {}
    representative_match = matches[0]
    representative_size = 0
    for match in matches:
        values = _extract_generic_gic_rate_values(str(match.get("evidence_text_excerpt", "")))
        rows = [dict(row) for row in values.get("term_rate_table", []) if isinstance(row, dict)]
        if len(rows) > representative_size:
            representative_match = match
            representative_size = len(rows)
        for row in rows:
            duration_key = row.get("term_length_days")
            if not isinstance(duration_key, int):
                duration_key = str(row.get("term_label") or "")
            key = (duration_key, str(row.get("rate") or ""))
            rows_by_key.setdefault(key, row)

    rows = sorted(
        rows_by_key.values(),
        key=lambda row: (
            int(row["term_length_days"]) if isinstance(row.get("term_length_days"), int) else 10**9,
            str(row.get("term_label") or ""),
        ),
    )
    if not rows:
        return representative_match, {}
    one_year_row = next(
        (
            row
            for row in rows
            if row.get("term_length_days") in {360, 365} or row.get("term_label") in {"12 month", "12 months", "1 year"}
        ),
        rows[0],
    )
    one_year_rate = str(one_year_row["rate"])
    return representative_match, {
        "standard_rate": one_year_rate,
        "public_display_rate": one_year_rate,
        "base_12_month_rate": one_year_rate,
        "term_rate_table": rows,
    }


def _gic_structured_match_is_cross_product(excerpt: str) -> bool:
    lowered = excerpt.lower()
    return any(
        marker in lowered
        for marker in (
            "notice savings account",
            "cash savings account",
            "high interest savings",
            "chequing account",
            "checking account",
            "personal account",
            "joint account",
            "us dollar account",
            "credit card",
            "mortgage",
        )
    ) and not any(marker in lowered for marker in ("gic", "term deposit"))


def _build_generic_field_updates(
    *,
    support_source_id: str,
    match: dict[str, object],
    field_values: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
    extraction_method: str,
    runtime_note: str,
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for field_name, candidate_value in field_values.items():
        if field_name in existing_fields:
            replace_invalid_savings_tier = (
                field_name == "tier_definition_text"
                and not _is_useful_savings_tier_record(existing_fields[field_name])
            )
            if not replace_invalid_savings_tier and not _is_invalid_gic_rate_record(field_name, existing_fields[field_name]):
                continue
        if field_name == "term_rate_table":
            value_type = "json"
        elif field_name == "tier_definition_text" or field_name == "fee_waiver_condition":
            value_type = "string"
        elif field_name == "tiered_rate_flag":
            value_type = "boolean"
        else:
            value_type = "decimal"
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type=value_type,
            match=match,
            extraction_method=extraction_method,
            field_metadata={
                "supporting_source_id": support_source_id,
                "supporting_merge": True,
                "generic_supporting_merge": True,
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [runtime_note],
    }


def _find_generic_support_match(
    *,
    matches: list[dict[str, object]],
    terms: tuple[str, ...],
    preferred_fields: tuple[str, ...],
    require_percentage: bool = False,
    require_money: bool = False,
    allow_structured_gic_table: bool = False,
) -> dict[str, object] | None:
    ranked: list[tuple[float, dict[str, object]]] = []
    preferred_field_set = set(preferred_fields)
    for match in matches:
        field_name = str(match.get("field_name", ""))
        if field_name not in preferred_field_set and field_name not in _SUPPORTING_ROLE_FIELDS:
            continue
        excerpt = str(match.get("evidence_text_excerpt", ""))
        if expired_promotional_offer_end_date(excerpt) is not None:
            continue
        haystack = _normalize_text(
            " ".join(
                str(item or "")
                for item in (
                    field_name,
                    match.get("anchor_value"),
                    excerpt,
                )
            )
        )
        structured_gic_table = (
            allow_structured_gic_table
            and field_name == "term_rate_table"
            and bool(_extract_generic_gic_rate_values(excerpt).get("term_rate_table"))
        )
        if not any(term in haystack for term in terms) and not structured_gic_table:
            continue
        if require_percentage and not _extract_all_percentages(excerpt):
            continue
        if require_money and not (_extract_money_amounts(excerpt) or _mentions_no_fee(excerpt)):
            continue

        try:
            score = float(match.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        if field_name in preferred_field_set:
            score += 0.15
        if structured_gic_table:
            score += 0.35
        score += min(0.25, sum(0.05 for term in terms if term in haystack))
        ranked.append((score, match))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _find_target_unlimited_transaction_match(
    *,
    matches: list[dict[str, object]],
    terms: tuple[str, ...],
) -> dict[str, object] | None:
    ranked: list[tuple[int, float, dict[str, object]]] = []
    for match in matches:
        excerpt = str(match.get("evidence_text_excerpt", ""))
        normalized = _normalize_text(excerpt)
        unlimited_matches = list(
            re.finditer(
                r"\bunlimited\s+(?:(?:no\s+fee|free)\s+)?(?:everyday\s+banking\s+|monthly\s+|banking\s+)?transactions?\b",
                normalized,
                flags=re.IGNORECASE,
            )
        )
        if not unlimited_matches:
            continue
        best_distance: int | None = None
        for unlimited_match in unlimited_matches:
            window_start = max(0, unlimited_match.start() - 180)
            window_end = min(len(normalized), unlimited_match.end() + 180)
            window = normalized[window_start:window_end]
            if any(term in window for term in terms):
                best_distance = min(
                    (
                        abs(window.find(term) + window_start - unlimited_match.start())
                        for term in terms
                        if term in window
                    ),
                    default=180,
                )
                break
        if best_distance is None:
            continue
        try:
            score = float(match.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        ranked.append((-best_distance, score, match))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return ranked[0][2]


def _find_current_savings_rate_table_match(
    matches: list[dict[str, object]], *, terms: tuple[str, ...]
) -> dict[str, object] | None:
    ranked: list[tuple[float, dict[str, object]]] = []
    for match in matches:
        excerpt = str(match.get("evidence_text_excerpt", ""))
        identity_context = _normalize_text(
            " ".join(
                str(value or "")
                for value in (match.get("field_name"), match.get("anchor_value"), excerpt[:180])
            )
        )
        if "savings" not in identity_context or "rate" not in identity_context or "competitor" in identity_context:
            continue
        if expired_promotional_offer_end_date(excerpt) is not None:
            continue
        if _extract_current_savings_account_rate(excerpt, terms=terms) is None:
            continue
        try:
            score = float(match.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        ranked.append((score, match))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _find_current_gic_rate_table_match(matches: list[dict[str, object]]) -> dict[str, object] | None:
    ranked: list[tuple[float, dict[str, object]]] = []
    for match in matches:
        excerpt = str(match.get("evidence_text_excerpt", ""))
        identity_context = _normalize_text(
            " ".join(
                str(value or "")
                for value in (match.get("field_name"), match.get("anchor_value"), excerpt[:220])
            )
        )
        if "gic" not in identity_context or "rate" not in identity_context:
            continue
        if expired_promotional_offer_end_date(excerpt) is not None:
            continue
        if not _extract_current_gic_rate_values(excerpt):
            continue
        try:
            score = float(match.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        if "current" in identity_context:
            score += 0.2
        ranked.append((score, match))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _extract_current_gic_rate_values(excerpt: str) -> dict[str, object]:
    normalized = _normalize_text(excerpt.replace("–", "-").replace("—", "-"))
    if "gic" not in normalized or "term" not in normalized:
        return {}
    if not re.search(r"(?:annual|rate)\s*\(%\)", normalized, flags=re.IGNORECASE):
        return {}

    rows: list[dict[str, object]] = []
    long_term_match = re.search(
        r"long[ -]?term\s+gics?\s+term\s+annual\s*\(%\)\s+semi\s+annual\s*\(%\)\s+monthly\s*\(%\)"
        r"(?P<table>.*?)long[ -]?term\s+gics?\s+are",
        normalized,
        flags=re.IGNORECASE,
    )
    if long_term_match is not None:
        long_term_minimum = _extract_gic_section_minimum(
            _gic_section(normalized, start_pattern=r"long[ -]?term\s+gics?", end_pattern=r"short[ -]?term\s+gics?")
        )
        for match in re.finditer(
            r"(?P<term>\d{1,2}\s+(?:month|months|year|years))\s+"
            r"(?P<annual>\d{1,2}(?:\.\d{1,4})?)\s+"
            r"(?P<semi>\d{1,2}(?:\.\d{1,4})?)\s+"
            r"(?P<monthly>\d{1,2}(?:\.\d{1,4})?)",
            long_term_match.group("table"),
            flags=re.IGNORECASE,
        ):
            term_label = _normalize_text(match.group("term"))
            rows.append(
                {
                    "term_label": term_label,
                    "term_length_days": _term_label_to_days(term_label),
                    "rate": _format_decimal(_to_decimal(match.group("annual"))),
                    "minimum_deposit": long_term_minimum,
                    "notes": "Long-term GIC annual interest rate",
                }
            )

    short_term_match = re.search(
        r"short[ -]?term\s+gics?\s+term\s+rate\s*\(%\)(?P<table>.*?)short[ -]?term\s+gics?\s+are",
        normalized,
        flags=re.IGNORECASE,
    )
    if short_term_match is not None:
        short_term_minimum = _extract_gic_section_minimum(
            _gic_section(normalized, start_pattern=r"short[ -]?term\s+gics?", end_pattern=r"cashable\s+gics?")
        )
        for match in re.finditer(
            r"(?P<start>\d{1,3})\s+(?:-|to\s+)?(?P<end>\d{1,3})\s+days\s+"
            r"(?P<rate>\d{1,2}(?:\.\d{1,4})?)",
            short_term_match.group("table"),
            flags=re.IGNORECASE,
        ):
            term_label = f"{match.group('start')}-{match.group('end')} days"
            rows.append(
                {
                    "term_label": term_label,
                    "term_length_days": None,
                    "rate": _format_decimal(_to_decimal(match.group("rate"))),
                    "minimum_deposit": short_term_minimum,
                    "notes": "Short-term non-redeemable GIC rate",
                }
            )

    cashable_match = re.search(
        r"cashable\s+gics?\s+term\s+after\s+30\s+days\s*\(%\)"
        r"(?:\s+after\s+90\s+days\s*\(%\))?(?P<table>.*?)cashable\s+gics?\s+require",
        normalized,
        flags=re.IGNORECASE,
    )
    if cashable_match is not None:
        cashable_minimum = _extract_gic_section_minimum(
            normalized[cashable_match.start(): cashable_match.end() + 360]
        )
        match = re.search(
            r"(?P<term>\d{1,2}\s+(?:month|months|year|years))\s+(?P<rate>\d{1,2}(?:\.\d{1,4})?)",
            cashable_match.group("table"),
            flags=re.IGNORECASE,
        )
        if match is not None:
            term_label = _normalize_text(match.group("term"))
            rows.append(
                {
                    "term_label": term_label,
                    "term_length_days": _term_label_to_days(term_label),
                    "rate": _format_decimal(_to_decimal(match.group("rate"))),
                    "minimum_deposit": cashable_minimum,
                    "notes": "Cashable GIC rate after the stated waiting period",
                }
            )

    if not rows:
        return {}
    one_year_row = next(
        (
            row
            for row in rows
            if row.get("term_length_days") in {360, 365}
            and str(row.get("notes")) == "Long-term GIC annual interest rate"
        ),
        rows[0],
    )
    one_year_rate = str(one_year_row["rate"])
    populated_minimums = {
        str(row["minimum_deposit"])
        for row in rows
        if row.get("minimum_deposit") not in {None, ""}
    }
    if len(populated_minimums) == 1:
        common_minimum = next(iter(populated_minimums))
        for row in rows:
            if row.get("minimum_deposit") in {None, ""}:
                row["minimum_deposit"] = common_minimum
    result: dict[str, object] = {
        "standard_rate": one_year_rate,
        "public_display_rate": one_year_rate,
        "base_12_month_rate": one_year_rate,
        "term_rate_table": rows,
    }
    if len(populated_minimums) == 1:
        result["minimum_deposit"] = next(iter(populated_minimums))
    return result


def _extract_gic_section_minimum(section_text: str) -> str | None:
    match = re.search(
        r"(?:minimum\s+(?:deposit|investment)(?:\s+of)?|(?:deposit|investment)\s+minimum|initial\s+investment(?:\s+of)?)\s*\$\s*"
        r"(?P<amount>\d[\d,]*(?:\.\d{1,2})?)",
        section_text,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    amount = _to_decimal(match.group("amount").replace(",", ""))
    return _format_decimal(amount) if amount is not None else None


def _gic_section(normalized: str, *, start_pattern: str, end_pattern: str) -> str:
    match = re.search(
        rf"{start_pattern}(?P<section>[\s\S]*?)(?={end_pattern}|$)",
        normalized,
        flags=re.IGNORECASE,
    )
    return match.group(0) if match is not None else ""


def _extract_current_savings_account_rate(
    excerpt: str, *, terms: tuple[str, ...] = ()
) -> Decimal | None:
    normalized = _normalize_text(excerpt)
    if re.search(r"(?:current\s+)?rate\s*\(%\)", normalized, flags=re.IGNORECASE) is None:
        return None
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in excerpt.splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        normalized_line = _normalize_text(line)
        target_match = (
            any(_savings_identity_term_matches_line(term=term, line=normalized_line) for term in terms)
            if terms
            else normalized_line == "savings account"
        )
        if not target_match:
            continue
        inline_value = next(iter(_extract_all_percentages(line)), None)
        value = inline_value if inline_value is not None else _to_decimal(lines[index + 1])
        if value is not None and Decimal("0") < value < Decimal("25"):
            return value
    if terms:
        for term in terms:
            if term in {"savings", "savings account", "saving account"}:
                continue
            targeted_match = re.search(
                rf"\b{re.escape(term)}\b.{{0,80}}?(?P<rate>\d{{1,2}}(?:\.\d{{1,4}})?)\s*%?",
                normalized,
                flags=re.IGNORECASE,
            )
            if targeted_match is None:
                continue
            value = _to_decimal(targeted_match.group("rate"))
            if value is not None and Decimal("0") < value < Decimal("25"):
                return value
        if any(term in {"savings account", "saving account"} for term in terms):
            inline_generic_match = re.search(
                r"(?:current\s+)?rate\s*\(%\)\s+savings\s+account\s+(?P<rate>\d{1,2}(?:\.\d{1,4})?)\b",
                normalized,
                flags=re.IGNORECASE,
            )
            if inline_generic_match is not None:
                value = _to_decimal(inline_generic_match.group("rate"))
                if value is not None and Decimal("0") < value < Decimal("25"):
                    return value
        return None
    inline_match = re.search(
        r"(?:current\s+)?rate\s*\(%\)\s+savings\s+account\s+(?P<rate>\d{1,2}(?:\.\d{1,4})?)\b",
        normalized,
        flags=re.IGNORECASE,
    )
    return _to_decimal(inline_match.group("rate")) if inline_match is not None else None


def _savings_identity_term_matches_line(*, term: str, line: str) -> bool:
    if term in {"savings", "savings account", "saving account"}:
        return line == term
    return term in line


def _target_terms_from_artifact(base_artifact: dict[str, object]) -> tuple[str, ...]:
    field_records = _field_record_map([dict(item) for item in base_artifact.get("extracted_fields", [])])
    product_name = str(field_records.get("product_name", {}).get("candidate_value") or "").strip()
    if not product_name:
        return ()

    normalized = _normalize_text(product_name)
    candidates = {
        normalized,
        _strip_bank_title_suffix(normalized),
        re.sub(r"^(?:td|rbc|bmo|cibc|scotiabank|scotia)\s+", "", normalized).strip(),
        re.sub(r"^invest(?:ing)?\s+in\s+", "", normalized).strip(),
    }
    if "|" in product_name:
        candidates.add(_normalize_text(product_name.split("|", 1)[0]))
    for segment in re.split(r"\s+(?:-|–|—|\|)\s+", product_name):
        normalized_segment = _normalize_text(segment)
        if normalized_segment:
            candidates.add(normalized_segment)
    expanded: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        expanded.add(candidate)
        simplified = re.sub(
            r"\b(?:account|accounts|package|packages|bank|banking|online|canada|trust|royal)\b",
            " ",
            candidate,
        )
        simplified = _WHITESPACE_RE.sub(" ", simplified).strip()
        if simplified:
            expanded.add(simplified)
        if "gic" in simplified and "gics" not in simplified:
            expanded.add(simplified.replace("gic", "gics"))
        if "gics" in simplified:
            expanded.add(simplified.replace("gics", "gic"))
        if "deposits" in simplified:
            expanded.add(re.sub(r"\bdeposits\b", "deposit", simplified))
        if any(marker in candidate for marker in ("u.s. dollar", "u s dollar", "us dollar", "usd")):
            suffix = "savings account" if "savings" in candidate else "account"
            expanded.update({f"us$ {suffix}", f"usd {suffix}", f"us dollar {suffix}"})

    return tuple(
        item
        for item in sorted(expanded, key=len, reverse=True)
        if (
            len(item) >= 4
            and item not in {"savings", "chequing", "checking", "gic", "gics"}
            and not _is_institution_only_target_term(item)
        )
    )


def _target_currency_from_artifact(base_artifact: dict[str, object]) -> str | None:
    field_records = _field_record_map([dict(item) for item in base_artifact.get("extracted_fields", [])])
    value = str(field_records.get("currency", {}).get("candidate_value") or "").strip().upper()
    return value if re.fullmatch(r"[A-Z]{3}", value) else None


def _support_match_currency_is_compatible(
    *,
    target_currency: str | None,
    match: dict[str, object],
) -> bool:
    """Keep product supplements from crossing an explicitly named currency.

    CAD is commonly implicit on Canadian product pages, while foreign-currency
    products state their currency in the title, anchor, or excerpt.  A match
    that explicitly names a different currency is therefore unsafe even when
    the rest of its product title is a substring of the target title.
    """

    if target_currency is None:
        return True
    haystack = _normalize_text(
        " ".join(
            str(item or "")
            for item in (
                match.get("anchor_value"),
                match.get("evidence_text_excerpt"),
            )
        )
    )
    detected: set[str] = set()
    currency_markers = {
        "USD": (
            r"\bu\.?\s*s\.?\s*d\b",
            r"\bu\.?\s*s\.?\s*\$",
            r"\bu\.?\s*s\.?\s+dollars?\b",
            r"\bunited states dollars?\b",
        ),
        "EUR": (r"\beuros?\b", r"\beur\b"),
        "GBP": (r"\bbritish pounds?\b", r"\bpounds? sterling\b", r"\bgbp\b"),
        "HKD": (r"\bhong kong dollars?\b", r"\bhkd\b"),
        "CNY": (r"\bchinese yuan\b", r"\brenminbi\b", r"\bcny\b", r"\brmb\b"),
        "JPY": (r"\bjapanese yen\b", r"\bjpy\b"),
    }
    for currency, patterns in currency_markers.items():
        if any(re.search(pattern, haystack, flags=re.IGNORECASE) for pattern in patterns):
            detected.add(currency)
    return not detected or target_currency in detected


def _is_generic_gic_family_artifact(base_artifact: dict[str, object]) -> bool:
    field_records = _field_record_map([dict(item) for item in base_artifact.get("extracted_fields", [])])
    product_name = str(field_records.get("product_name", {}).get("candidate_value") or "").strip()
    if not product_name:
        return False
    identity_segment = re.split(r"\s*(?:\||-|–|—)\s*", product_name, maxsplit=1)[0]
    normalized_identity = _normalize_text(identity_segment)
    normalized_identity = re.sub(r"\s*\(\s*gics?\s*\)\s*$", "", normalized_identity).strip()
    return normalized_identity in {
        "gic",
        "gics",
        "guaranteed investment certificate",
        "guaranteed investment certificates",
    }


def _is_institution_only_target_term(value: str) -> bool:
    tokens = value.split()
    return (len(tokens) <= 3 and tokens[-1:] == ["bank"]) or (
        len(tokens) <= 4 and tokens[-2:] == ["credit", "union"]
    )


def _strip_bank_title_suffix(value: str) -> str:
    stripped = re.sub(
        r"(?:\s*\|\s*)?(?:scotiabank|scotia|td(?: canada trust| bank)?|rbc(?: royal bank(?: of canada)?)?|royal bank of canada|bmo|cibc)(?: canada)?$",
        "",
        value,
    )
    return _WHITESPACE_RE.sub(" ", stripped).strip()


def _extract_generic_rate_values(excerpt: str) -> dict[str, str]:
    percentages = sorted(set(_extract_all_percentages(excerpt)))
    if not percentages:
        return {}
    if len(percentages) == 1:
        rate = _format_decimal(percentages[0])
        return {"standard_rate": rate, "public_display_rate": rate}
    standard_rate = percentages[0]
    public_display_rate = percentages[-1]
    return {
        "standard_rate": _format_decimal(standard_rate),
        "public_display_rate": _format_decimal(public_display_rate),
    }


def _extract_generic_gic_rate_values(excerpt: str) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    seen_terms: set[str] = set()
    for match in _TERM_RATE_ROW_RE.finditer(_WHITESPACE_RE.sub(" ", excerpt)):
        term_label = _normalize_text(match.group("term"))
        if term_label in seen_terms:
            continue
        rate = _to_decimal(match.group("rate"))
        if rate is None or rate <= 0:
            continue
        seen_terms.add(term_label)
        rows.append(
            {
                "term_label": term_label,
                "term_length_days": _term_label_to_days(term_label),
                "rate": _format_decimal(rate),
                "minimum_deposit": None,
                "notes": None,
            }
        )
    if not rows:
        return _extract_generic_rate_values(excerpt)

    one_year_row = next(
        (
            row
            for row in rows
            if row["term_length_days"] in {360, 365} or row["term_label"] in {"12 month", "12 months", "1 year"}
        ),
        rows[0],
    )
    display_rate = str(one_year_row["rate"])
    return {
        "standard_rate": display_rate,
        "public_display_rate": display_rate,
        "base_12_month_rate": display_rate,
        "term_rate_table": rows,
    }


def _term_label_to_days(term_label: str) -> int | None:
    match = re.fullmatch(r"(\d{1,3}(?:\.\d{1,2})?)\s*(day|days|month|months|year|years)", term_label)
    if match is None:
        return None
    value = Decimal(match.group(1))
    unit = match.group(2)
    if unit.startswith("day"):
        days = value
    elif unit.startswith("month"):
        days = value * Decimal("30")
    else:
        days = value * Decimal("365")
    if days != days.to_integral_value():
        days = (days + Decimal("0.5")).to_integral_value()
    return int(days)


def _is_invalid_gic_rate_record(field_name: str, record: dict[str, object]) -> bool:
    if field_name == "term_rate_table":
        value = record.get("candidate_value")
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return True
        if not isinstance(value, list) or not value:
            return True
        rates = [_to_decimal(str(row.get("rate"))) for row in value if isinstance(row, dict)]
        return not rates or all(rate is None or rate <= 0 for rate in rates)
    if field_name not in {"standard_rate", "public_display_rate", "base_12_month_rate"}:
        return False
    value = _to_decimal(str(record.get("candidate_value") or ""))
    if value is None or value <= 0:
        return True
    evidence_context = str(record.get("evidence_text_excerpt") or "")
    lowered_context = evidence_context.lower()
    other_product_context = (
        any(
            marker in lowered_context
            for marker in (
                "personal account",
                "joint account",
                "savings account",
                "chequing account",
                "checking account",
                "credit card",
                "mortgage",
            )
        )
        and "gic" not in lowered_context
        and "term deposit" not in lowered_context
    )
    return other_product_context or canonical_deposit_rate_suppression_reason(value=value, context=evidence_context) is not None


def _extract_generic_monthly_fee_values(
    excerpt: str,
    *,
    terms: tuple[str, ...] = (),
) -> dict[str, object]:
    comparison_values = _extract_target_comparison_monthly_fee(excerpt, terms=terms)
    if comparison_values:
        return comparison_values
    if _mentions_no_fee(excerpt):
        return {"monthly_fee": "0.00", "public_display_fee": "0.00"}
    lowered = _normalize_text(excerpt)
    patterns = (
        r"(?:monthly\s+(?:account\s+|plan\s+)?fee|account\s+fee)\s*(?:is|of|:)?\s*\$\s?(?P<fee>[0-9][0-9,]*(?:\.\d{1,2})?)",
        r"\$\s?(?P<fee>[0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:/\s*month|per\s+month|monthly)(?:\s+(?:account|plan))?\s+fee",
    )
    for pattern in patterns:
        for monthly_fee_match in re.finditer(pattern, lowered, flags=re.IGNORECASE):
            if terms:
                local_context = lowered[
                    max(0, monthly_fee_match.start() - 260) : min(len(lowered), monthly_fee_match.end() + 260)
                ]
                if not any(term and term in local_context for term in terms):
                    continue
            value = monthly_fee_match.group("fee").replace(",", "")
            try:
                if Decimal(value) > Decimal("500"):
                    continue
            except InvalidOperation:
                continue
            return {"monthly_fee": value, "public_display_fee": value}
    return {}


def _extract_target_comparison_monthly_fee(
    excerpt: str,
    *,
    terms: tuple[str, ...],
) -> dict[str, object]:
    """Map a horizontal comparison-table fee row to the target product column.

    Flattened HTML commonly lists all product headings first and all values
    second.  Reading the first `$0` anywhere in that chunk reverses a
    balance-qualified waiver or a neighbouring audience price into the base
    fee.  The product-heading order and fee-entry order provide a conservative,
    bank-independent column mapping.
    """

    # PDF text extraction sometimes substitutes the decimal point in a money
    # value with U+FFFD (for example, ``$30�95``). Restore only the narrow
    # digit + replacement + exactly-two-decimals shape; do not broadly rewrite
    # punctuation or adjacent footnote digits.
    normalized = _normalize_text(
        re.sub(r"(?<=\d)\ufffd(?=\d{2}(?:\D|$))", ".", excerpt)
    )
    fee_label = re.search(
        r"\bmonthly\s+(?:account\s+|plan\s+)?fees?(?:\d{1,2})?\b",
        normalized,
    )
    if fee_label is None or not terms:
        return {}
    header = normalized[: fee_label.start()]
    target_matches = [
        (header.find(term), term)
        for term in terms
        if term and header.find(term) >= 0
    ]
    if not target_matches:
        return {}
    target_position, target_term = max(target_matches, key=lambda item: len(item[1]))
    target_end = target_position + len(target_term)
    heading_markers = list(
        re.finditer(
            r"\b(?:chequing|checking|banking|bank)\s+account\b|\bbanking\s+plan\b|\b(?:banking\s+)?package\b",
            header,
            flags=re.IGNORECASE,
        )
    )
    if len(heading_markers) < 2:
        # A single named product followed by prose is a detail-style excerpt,
        # not a horizontal comparison table. Let the direct labelled-fee
        # parser handle it so a later waiver balance cannot become the fee.
        return {}
    target_index = next(
        (
            index
            for index, marker in enumerate(heading_markers)
            if marker.end() >= target_end and marker.end() - target_end <= 32
        ),
        None,
    )
    if target_index is None:
        return {}

    row = normalized[fee_label.end() :]
    next_row_markers = [
        marker
        for marker in (
            re.search(r"\bmonthly\s+fees?\s+for\s+seniors?\b", row),
            re.search(r"\bseniors?[’']?\s+discount\b", row),
            re.search(r"\bminimum\s+daily\s+(?:closing\s+)?balance\b", row),
            re.search(r"\bno\.\s+of\s+debit\s+transactions\b", row),
        )
        if marker is not None
    ]
    if next_row_markers:
        row = row[: min(marker.start() for marker in next_row_markers)]
    entry_pattern = re.compile(
        r"\$\s*(?P<fee>\d[\d,]*(?:\.\d{1,2})?)\s*"
        r"(?:or\s+\$\s*0(?:\.00)?\s*\((?P<waiver>[^)]{0,700})\)"
        r"|\((?P<condition>[^)]{0,700})\)"
        r"|(?=\s*\$|\s*$))",
        flags=re.IGNORECASE,
    )
    entries: list[tuple[str, str | None]] = []
    for entry in entry_pattern.finditer(row):
        fee = entry.group("fee").replace(",", "")
        context = entry.group("waiver") or entry.group("condition")
        entries.append((fee, context))
    if target_index >= len(entries):
        return {}

    fee, condition = entries[target_index]
    values: dict[str, object] = {
        "monthly_fee": fee,
        "public_display_fee": fee,
    }
    if condition:
        balance_match = re.search(
            r"minimum\s+(?:daily\s+)?(?:account\s+)?balance(?:\s+of)?\s+\$\s*(?P<balance>\d[\d,]*(?:\.\d{1,2})?)",
            condition,
            flags=re.IGNORECASE,
        )
        if balance_match is not None:
            balance = balance_match.group("balance").replace(",", "")
            values["minimum_balance"] = balance
            values["fee_waiver_condition"] = (
                f"Monthly fee {fee} is waived to 0.00 with a {balance} minimum balance."
            )
        elif any(
            marker in condition.lower()
            for marker in (
                "guaranteed income supplement",
                "beneficiary",
                "registered disability savings plan",
                "indigenous",
                "newcomer",
            )
        ):
            cleaned_condition = _normalize_text(condition).strip(" .")
            values["fee_waiver_condition"] = (
                f"Monthly fee {fee} is waived to 0.00 if {cleaned_condition}."
            )[:500]
    return values


def _extract_savings_balance_tier_summary(excerpt: str) -> str | None:
    normalized = _normalize_text(excerpt)
    if "daily closing balance" not in normalized or "%" not in normalized:
        return None
    balance_pattern = re.compile(
        r"(?P<label>\$\s*\d[\d,]*(?:\.\d+)?\s+(?:to\s+\$?\s*\d[\d,]*(?:\.\d+)?|and\s+over))",
        flags=re.IGNORECASE,
    )
    balance_matches = list(balance_pattern.finditer(normalized))
    if len(balance_matches) < 2:
        return None
    rows: list[tuple[str, tuple[str, ...]]] = []
    distinct_rates: set[str] = set()
    for index, balance_match in enumerate(balance_matches):
        end = balance_matches[index + 1].start() if index + 1 < len(balance_matches) else len(normalized)
        rates = tuple(
            match.group(1)
            for match in re.finditer(r"(?<![\d.])(\d{1,2}(?:\.\d{1,4})?)\s*%", normalized[balance_match.end() : end])
        )
        if not rates:
            continue
        label = re.sub(r"\s+", " ", balance_match.group("label")).strip()
        rows.append((label, rates[:2]))
        distinct_rates.update(rates[:2])
    if len(rows) < 2 or len(distinct_rates) < 2:
        return None
    has_dual_columns = "boosted rate" in normalized and "standard posted rate" in normalized
    rendered_rows = [
        f"{label}: {' / '.join(f'{rate}%' for rate in rates)}"
        for label, rates in rows
    ]
    suffix = " (Boosted Rate / Standard Posted Rate)" if has_dual_columns else ""
    return "Balance tiers: " + "; ".join(rendered_rows) + suffix + "."


def _is_useful_savings_tier_record(record: dict[str, object]) -> bool:
    value = str(record.get("candidate_value") or "")
    return "$" in value and "%" in value and "balance" in value.lower()


def _extract_money_amounts(excerpt: str) -> list[str]:
    values: list[str] = []
    for match in re.finditer(r"\$\s?([0-9][0-9,]*(?:\.\d{1,2})?)", excerpt):
        values.append(match.group(1).replace(",", ""))
    return values


def _mentions_no_fee(excerpt: str) -> bool:
    lowered = _normalize_text(excerpt)
    return any(
        token in lowered
        for token in (
            "no monthly fee",
            "no monthly account fee",
            "no monthly plan fee",
            "monthly fee $0",
            "$0 monthly fee",
        )
    )


def _canonical_product_type_family(product_type: str | None) -> str | None:
    normalized = str(product_type or "").strip().lower()
    if normalized in {
        "chequing",
        "savings",
        "gic",
        "mortgage",
        "personal-loan",
        "line-of-credit",
    }:
        return normalized
    if any(token in normalized for token in ("gic", "term-deposit", "term_deposit", "term deposit")):
        return "gic"
    if "savings" in normalized or "saving" in normalized:
        return "savings"
    if "chequing" in normalized or "checking" in normalized:
        return "chequing"
    if "mortgage" in normalized:
        return "mortgage"
    if "personal" in normalized and "loan" in normalized:
        return "personal-loan"
    if "line" in normalized and "credit" in normalized:
        return "line-of-credit"
    return None


def _build_current_rate_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if target_source_id not in _TARGET_MATCH_TERMS:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    terms = _TARGET_MATCH_TERMS[target_source_id]
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))

    rate_table_match = _find_product_matched_rate_table(target_source_id=target_source_id, matches=matches, terms=terms)
    if rate_table_match is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    rate_values = _extract_rate_values_from_match(target_source_id=target_source_id, match=rate_table_match)
    if not rate_values:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}
    tier_summary = _extract_savings_balance_tier_summary(
        str(rate_table_match.get("evidence_text_excerpt", ""))
    )
    if tier_summary is not None:
        rate_values["tier_definition_text"] = tier_summary
        rate_values["tiered_rate_flag"] = True

    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for field_name, candidate_value in rate_values.items():
        if field_name in existing_fields and not (
            field_name == "tier_definition_text"
            and not _is_useful_savings_tier_record(existing_fields[field_name])
        ):
            continue
        if field_name == "tier_definition_text":
            value_type = "string"
        elif field_name == "tiered_rate_flag":
            value_type = "boolean"
        else:
            value_type = "decimal"
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type=value_type,
            match=rate_table_match,
            extraction_method="supporting_rate_table_merge",
            field_metadata={
                "supporting_source_id": "TD-SAV-005",
                "supporting_merge": True,
                "match_terms": list(terms),
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=rate_table_match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            "Supplemented missing savings rate fields from `TD-SAV-005` current-rate evidence using a product-matched supporting chunk."
        ],
    }


def _build_fee_pdf_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    match = _select_support_match(
        matches=matches,
        field_name="fee_waiver_condition",
        required_keywords=("refund the fee", "maintain the required daily closing balance"),
    )
    if match is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    existing_field = existing_fields.get("fee_waiver_condition")
    if existing_field is not None and not _should_replace_fee_waiver(existing_field=existing_field, existing_fields=existing_fields):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if _is_zero_fee_target(existing_fields):
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                f"Reviewed `TD-SAV-007` fee-governing language for `{target_source_id}` and left `fee_waiver_condition` unset because the target monthly fee is already $0."
            ],
        }

    candidate_value = _clean_fee_waiver_text(str(match.get("evidence_text_excerpt", "")))
    if not candidate_value:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": {
            "fee_waiver_condition": _build_support_field(
                field_name="fee_waiver_condition",
                candidate_value=candidate_value,
                value_type="string",
                match=match,
                extraction_method="supporting_fee_pdf_merge",
                field_metadata={
                    "supporting_source_id": "TD-SAV-007",
                    "supporting_merge": True,
                },
            )
        },
        "evidence_updates": {
            "fee_waiver_condition": _build_support_link(
                field_name="fee_waiver_condition",
                candidate_value=candidate_value,
                match=match,
            )
        },
        "runtime_notes": [
            "Supplemented `fee_waiver_condition` from `TD-SAV-007` fee-governing PDF when the target detail text was missing or noisy."
        ],
    }


def _build_interest_pdf_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}

    field_specs: dict[str, tuple[tuple[str, ...], callable]] = {
        "interest_calculation_method": (
            ("interest will be calculated", "daily closing balance"),
            _clean_interest_calculation_text,
        ),
        "interest_payment_frequency": (
            ("paid monthly", "monthly"),
            _clean_interest_payment_frequency,
        ),
    }
    if target_source_id == "TD-SAV-004":
        field_specs["tier_definition_text"] = (
            ("tier", "daily closing balance"),
            _clean_tier_definition_text,
        )

    for field_name, (keywords, builder) in field_specs.items():
        existing_field = existing_fields.get(field_name)
        if existing_field is not None and not _should_replace_with_pdf(field_name=field_name, existing_field=existing_field):
            continue
        match = _select_support_match(matches=matches, field_name=field_name, required_keywords=keywords)
        if match is None:
            continue
        candidate_value = builder(str(match.get("evidence_text_excerpt", "")))
        if not candidate_value:
            continue
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type="string",
            match=match,
            extraction_method="supporting_interest_pdf_merge",
            field_metadata={
                "supporting_source_id": "TD-SAV-008",
                "supporting_merge": True,
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            "Replaced noisy interest-rule fields with targeted `TD-SAV-008` governing PDF evidence where stronger canonical wording was available."
        ],
    }


def _build_scotia_rate_page_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if target_source_id != "SCOTIA-SAV-004":
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if all(field_name in existing_fields for field_name in ("standard_rate", "public_display_rate")):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    match = _find_scotia_money_master_rate_match(target_source_id=target_source_id, matches=matches)
    if match is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    rate_values = _extract_scotia_money_master_rate_values(str(match.get("evidence_text_excerpt", "")))
    if not rate_values:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for field_name, candidate_value in rate_values.items():
        if field_name in existing_fields:
            continue
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type="decimal",
            match=match,
            extraction_method="supporting_scotia_rate_page_merge",
            field_metadata={
                "supporting_source_id": "SCOTIA-SAV-006",
                "supporting_merge": True,
                "match_terms": list(_TARGET_MATCH_TERMS[target_source_id]),
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            "Supplemented missing Scotia Money Master savings rate fields from `SCOTIA-SAV-006` supporting rate evidence."
        ],
    }


def _build_bmo_rate_page_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if target_source_id not in {"BMO-SAV-002", "BMO-SAV-003", "BMO-SAV-004"}:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if all(field_name in existing_fields for field_name in ("standard_rate", "public_display_rate")):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    terms = _TARGET_MATCH_TERMS[target_source_id]
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    match = _find_product_matched_rate_table(target_source_id=target_source_id, matches=matches, terms=terms)
    if match is None:
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                "BMO savings support source `BMO-SAV-006` was available, but no product-matched rate evidence was found."
            ],
        }

    rate_values = _extract_single_rate_values(str(match.get("evidence_text_excerpt", "")))
    if not rate_values:
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                "BMO savings support source `BMO-SAV-006` matched the product, but the rate evidence did not contain a numeric percentage."
            ],
        }

    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for field_name, candidate_value in rate_values.items():
        if field_name in existing_fields:
            continue
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type="decimal",
            match=match,
            extraction_method="supporting_bmo_rate_page_merge",
            field_metadata={
                "supporting_source_id": "BMO-SAV-006",
                "supporting_merge": True,
                "match_terms": list(terms),
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            "Supplemented missing BMO savings rate fields from `BMO-SAV-006` supporting rate evidence."
        ],
    }


def _build_cibc_rate_page_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if target_source_id not in {"CIBC-SAV-002", "CIBC-SAV-003"}:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if all(field_name in existing_fields for field_name in ("standard_rate", "public_display_rate")):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    terms = _TARGET_MATCH_TERMS[target_source_id]
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    match = _find_product_matched_rate_table(target_source_id=target_source_id, matches=matches, terms=terms)
    if match is None:
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                f"CIBC savings support source `CIBC-SAV-004` was available for `{target_source_id}`, but no product-matched rate evidence was found."
            ],
        }

    rate_values = _extract_single_rate_values(str(match.get("evidence_text_excerpt", "")))
    if not rate_values:
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                f"CIBC savings support source `CIBC-SAV-004` matched `{target_source_id}`, but the rate evidence did not contain a numeric percentage."
            ],
        }

    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for field_name, candidate_value in rate_values.items():
        if field_name in existing_fields:
            continue
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type="decimal",
            match=match,
            extraction_method="supporting_cibc_rate_page_merge",
            field_metadata={
                "supporting_source_id": "CIBC-SAV-004",
                "supporting_merge": True,
                "match_terms": list(terms),
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            f"Supplemented missing CIBC savings rate fields for `{target_source_id}` from `CIBC-SAV-004` supporting rate evidence."
        ],
    }


def _find_product_matched_rate_table(
    *,
    target_source_id: str,
    matches: list[dict[str, object]],
    terms: tuple[str, ...],
) -> dict[str, object] | None:
    preferred_fields = {
        "BMO-SAV-002": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates"),
        "BMO-SAV-003": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates"),
        "BMO-SAV-004": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates"),
        "CIBC-SAV-002": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates"),
        "CIBC-SAV-003": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates", "tier_definition_text"),
        "TD-SAV-002": ("standard_rate", "public_display_rate", "rate_tiers", "tier_definition_text"),
        "TD-SAV-003": ("standard_rate", "public_display_rate", "rate_tiers", "tier_definition_text"),
        "TD-SAV-004": ("rate_tiers", "boosted_rate", "promotional_rate", "tier_definition_text"),
    }.get(target_source_id, ("standard_rate", "public_display_rate"))
    for field_name in preferred_fields:
        for match in matches:
            if str(match.get("field_name", "")) != field_name:
                continue
            haystack = _normalize_text(
                " ".join(
                    str(item or "")
                    for item in (
                        match.get("anchor_value"),
                        match.get("evidence_text_excerpt"),
                    )
                )
            )
            if any(term in haystack for term in terms):
                return match
    return None


def _find_scotia_money_master_rate_match(
    *,
    target_source_id: str,
    matches: list[dict[str, object]],
) -> dict[str, object] | None:
    terms = _TARGET_MATCH_TERMS.get(target_source_id, ())
    ranked: list[tuple[float, dict[str, object]]] = []
    for match in matches:
        haystack = _normalize_text(
            " ".join(
                str(item or "")
                for item in (
                    match.get("field_name"),
                    match.get("anchor_value"),
                    match.get("evidence_text_excerpt"),
                )
            )
        )
        if not any(term in haystack for term in terms):
            continue
        percentages = _extract_all_percentages(str(match.get("evidence_text_excerpt", "")))
        if not percentages:
            continue
        score = 0.0
        try:
            score = float(match.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        score += min(0.25, len(percentages) * 0.05)
        ranked.append((score, match))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _extract_rate_values_from_match(*, target_source_id: str, match: dict[str, object]) -> dict[str, str]:
    excerpt = str(match.get("evidence_text_excerpt", ""))
    if not excerpt.strip():
        return {}
    if target_source_id == "TD-SAV-004":
        return _extract_growth_rate_values(excerpt)
    return _extract_single_rate_values(excerpt)


def _extract_single_rate_values(excerpt: str) -> dict[str, str]:
    percentages = _extract_all_percentages(excerpt)
    if not percentages:
        return {}
    max_rate = max(percentages)
    normalized = _format_decimal(max_rate)
    return {
        "standard_rate": normalized,
        "public_display_rate": normalized,
    }


def _extract_growth_rate_values(excerpt: str) -> dict[str, str]:
    boosted_rates: list[Decimal] = []
    standard_rates: list[Decimal] = []
    lines = [line.strip() for line in excerpt.splitlines() if line.strip()]
    index = 0
    while index < len(lines):
        line = lines[index]
        if not _looks_like_balance_line(line):
            index += 1
            continue
        rate_lines: list[Decimal] = []
        next_index = index + 1
        while next_index < len(lines) and not _looks_like_balance_line(lines[next_index]):
            rate = _extract_first_percentage(lines[next_index])
            if rate is not None:
                rate_lines.append(rate)
            next_index += 1
        if rate_lines:
            boosted_rates.append(rate_lines[0])
            standard_rates.append(rate_lines[1] if len(rate_lines) > 1 else rate_lines[0])
        index = next_index

    if not boosted_rates:
        percentages = _extract_all_percentages(excerpt)
        if not percentages:
            return {}
        boosted_rates = list(percentages)
        standard_rates = list(percentages)

    boosted_rate = max(boosted_rates)
    standard_rate = max(standard_rates) if standard_rates else boosted_rate
    return {
        "standard_rate": _format_decimal(standard_rate),
        "public_display_rate": _format_decimal(boosted_rate),
        "promotional_rate": _format_decimal(boosted_rate),
    }


def _extract_scotia_money_master_rate_values(excerpt: str) -> dict[str, str]:
    percentages = _extract_all_percentages(excerpt)
    if not percentages:
        return {}

    unique_percentages = sorted(set(percentages))
    standard_rate = min(unique_percentages)
    public_display_rate = max(unique_percentages)
    return {
        "standard_rate": _format_decimal(standard_rate),
        "public_display_rate": _format_decimal(public_display_rate),
    }


def _extract_all_percentages(excerpt: str) -> list[Decimal]:
    values: list[Decimal] = []
    for match in _PERCENT_RE.finditer(excerpt):
        window = bounded_rate_evidence_context(
            excerpt,
            value_start=match.start(),
            value_end=match.end(),
        )
        if canonical_deposit_rate_suppression_reason(value=match.group(1), context=window) is not None:
            continue
        decimal_value = _to_decimal(match.group(1))
        if decimal_value is not None:
            values.append(decimal_value)
    return values


def _extract_first_percentage(line: str) -> Decimal | None:
    match = _PERCENT_RE.search(line)
    if match is None:
        return None
    return _to_decimal(match.group(1))


def _to_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _format_decimal(value: Decimal) -> str:
    return f"{value:.2f}"


def _supplement_confidence(match: dict[str, object]) -> float:
    raw = match.get("score", 0.55)
    try:
        score = float(raw)
    except (TypeError, ValueError):
        score = 0.55
    return round(min(0.89, max(0.72, score)), 4)


def _looks_like_balance_line(line: str) -> bool:
    return bool(_BALANCE_LINE_RE.search(line.strip()))


def _normalize_text(value: str) -> str:
    lowered = value.lower().replace("??, ", " ")
    lowered = lowered.replace("™", " ").replace("®", " ")
    lowered = lowered.replace("-", " ").replace("_", " ")
    lowered = lowered.replace("?", " ")
    return _WHITESPACE_RE.sub(" ", lowered).strip()


def _field_record_map(extracted_fields: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for item in extracted_fields:
        field_name = str(item.get("field_name", ""))
        if field_name and field_name not in records:
            records[field_name] = item
    return records


def _build_support_field(
    *,
    field_name: str,
    candidate_value: object,
    value_type: str,
    match: dict[str, object],
    extraction_method: str,
    field_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "field_name": field_name,
        "candidate_value": candidate_value,
        "value_type": value_type,
        "confidence": _supplement_confidence(match),
        "extraction_method": extraction_method,
        "source_document_id": match["source_document_id"],
        "source_snapshot_id": match["source_snapshot_id"],
        "evidence_chunk_id": match["evidence_chunk_id"],
        "evidence_text_excerpt": match["evidence_text_excerpt"],
        "anchor_type": match["anchor_type"],
        "anchor_value": match["anchor_value"],
        "page_no": match["page_no"],
        "chunk_index": match["chunk_index"],
        "field_metadata": field_metadata,
    }


def _build_support_link(
    *,
    field_name: str,
    candidate_value: object,
    match: dict[str, object],
) -> dict[str, object]:
    return {
        "field_name": field_name,
        "candidate_value": str(candidate_value),
        "evidence_chunk_id": match["evidence_chunk_id"],
        "evidence_text_excerpt": match["evidence_text_excerpt"],
        "source_document_id": match["source_document_id"],
        "source_snapshot_id": match["source_snapshot_id"],
        "citation_confidence": _supplement_confidence(match),
        "model_execution_id": None,
        "anchor_type": match["anchor_type"],
        "anchor_value": match["anchor_value"],
        "page_no": match["page_no"],
        "chunk_index": match["chunk_index"],
    }


def _upsert_field_record(extracted_fields: list[dict[str, object]], field_record: dict[str, object]) -> None:
    field_name = str(field_record["field_name"])
    for index, existing in enumerate(extracted_fields):
        if str(existing.get("field_name", "")) != field_name:
            continue
        extracted_fields[index] = field_record
        return
    extracted_fields.append(field_record)


def _upsert_evidence_link(
    evidence_links: list[dict[str, object]],
    *,
    field_name: str,
    link_record: dict[str, object],
) -> None:
    for index in range(len(evidence_links) - 1, -1, -1):
        if str(evidence_links[index].get("field_name", "")) == field_name:
            evidence_links.pop(index)
    evidence_links.append(link_record)


def _remove_field(extracted_fields: list[dict[str, object]], evidence_links: list[dict[str, object]], field_name: str) -> None:
    for index in range(len(extracted_fields) - 1, -1, -1):
        if str(extracted_fields[index].get("field_name", "")) == field_name:
            extracted_fields.pop(index)
    for index in range(len(evidence_links) - 1, -1, -1):
        if str(evidence_links[index].get("field_name", "")) == field_name:
            evidence_links.pop(index)


def _cleanup_target_artifact(
    *,
    target_source_id: str,
    extracted_fields: list[dict[str, object]],
    evidence_links: list[dict[str, object]],
    runtime_notes: list[str],
) -> None:
    fields = _field_record_map(extracted_fields)
    fee_waiver_field = fields.get("fee_waiver_condition")
    if fee_waiver_field is not None and _is_zero_fee_target(fields) and _looks_like_fee_table_text(str(fee_waiver_field.get("candidate_value", ""))):
        _remove_field(extracted_fields, evidence_links, "fee_waiver_condition")
        runtime_notes.append(
            f"Suppressed noisy `fee_waiver_condition` for `{target_source_id}` because the product monthly fee is already $0 and no product-specific waiver rule should be persisted."
        )
        fields = _field_record_map(extracted_fields)

    for noisy_field_name in ("notes", "eligibility_text", "tier_definition_text"):
        field = fields.get(noisy_field_name)
        if field is None:
            continue
        candidate_value = str(field.get("candidate_value", ""))
        if not _looks_like_noisy_text(candidate_value):
            continue
        _remove_field(extracted_fields, evidence_links, noisy_field_name)
        runtime_notes.append(f"Suppressed noisy `{noisy_field_name}` text before normalization.")

    promotional_field = _field_record_map(extracted_fields).get("promotional_period_text")
    if promotional_field is not None:
        promotional_text = str(promotional_field.get("candidate_value", ""))
        if not _is_promotional_period_text(promotional_text):
            _remove_field(extracted_fields, evidence_links, "promotional_period_text")
            runtime_notes.append("Suppressed `promotional_period_text` because the extracted text described marketing copy rather than a bounded promotional period.")

    if target_source_id == "TD-SAV-004":
        _apply_growth_qualification_cleanup(
            extracted_fields=extracted_fields,
            evidence_links=evidence_links,
            runtime_notes=runtime_notes,
        )


def _apply_growth_qualification_cleanup(
    *,
    extracted_fields: list[dict[str, object]],
    evidence_links: list[dict[str, object]],
    runtime_notes: list[str],
) -> None:
    fields = _field_record_map(extracted_fields)
    boosted_field = fields.get("boosted_rate_eligibility")
    if boosted_field is None:
        return

    evidence_text = str(boosted_field.get("evidence_text_excerpt") or boosted_field.get("candidate_value") or "")
    if "qualify" not in evidence_text.lower():
        return

    eligibility_summary = _summarize_growth_eligibility(evidence_text)
    if eligibility_summary:
        eligibility_record = dict(boosted_field)
        eligibility_record["field_name"] = "eligibility_text"
        eligibility_record["candidate_value"] = eligibility_summary
        eligibility_record["extraction_method"] = "growth_qualification_cleanup"
        eligibility_record["field_metadata"] = {
            **dict(boosted_field.get("field_metadata", {})),
            "cleanup": "growth_eligibility_split",
        }
        _upsert_field_record(extracted_fields, eligibility_record)
        _upsert_evidence_link(
            evidence_links,
            field_name="eligibility_text",
            link_record={
                "field_name": "eligibility_text",
                "candidate_value": eligibility_summary,
                "evidence_chunk_id": boosted_field["evidence_chunk_id"],
                "evidence_text_excerpt": boosted_field["evidence_text_excerpt"],
                "source_document_id": boosted_field["source_document_id"],
                "source_snapshot_id": boosted_field["source_snapshot_id"],
                "citation_confidence": boosted_field["confidence"],
                "model_execution_id": None,
                "anchor_type": boosted_field["anchor_type"],
                "anchor_value": boosted_field["anchor_value"],
                "page_no": boosted_field["page_no"],
                "chunk_index": boosted_field["chunk_index"],
            },
        )

    boosted_summary = _summarize_growth_boosted_rate_eligibility(evidence_text)
    if boosted_summary:
        boosted_record = dict(boosted_field)
        boosted_record["candidate_value"] = boosted_summary
        boosted_record["extraction_method"] = "growth_qualification_cleanup"
        boosted_record["field_metadata"] = {
            **dict(boosted_field.get("field_metadata", {})),
            "cleanup": "growth_eligibility_split",
        }
        _upsert_field_record(extracted_fields, boosted_record)
        _upsert_evidence_link(
            evidence_links,
            field_name="boosted_rate_eligibility",
            link_record={
                "field_name": "boosted_rate_eligibility",
                "candidate_value": boosted_summary,
                "evidence_chunk_id": boosted_field["evidence_chunk_id"],
                "evidence_text_excerpt": boosted_field["evidence_text_excerpt"],
                "source_document_id": boosted_field["source_document_id"],
                "source_snapshot_id": boosted_field["source_snapshot_id"],
                "citation_confidence": boosted_field["confidence"],
                "model_execution_id": None,
                "anchor_type": boosted_field["anchor_type"],
                "anchor_value": boosted_field["anchor_value"],
                "page_no": boosted_field["page_no"],
                "chunk_index": boosted_field["chunk_index"],
            },
        )

    promotional_summary = _summarize_growth_promotional_period(evidence_text)
    if promotional_summary:
        promotional_record = dict(boosted_field)
        promotional_record["field_name"] = "promotional_period_text"
        promotional_record["candidate_value"] = promotional_summary
        promotional_record["extraction_method"] = "growth_qualification_cleanup"
        promotional_record["field_metadata"] = {
            **dict(boosted_field.get("field_metadata", {})),
            "cleanup": "growth_eligibility_split",
        }
        _upsert_field_record(extracted_fields, promotional_record)
        _upsert_evidence_link(
            evidence_links,
            field_name="promotional_period_text",
            link_record={
                "field_name": "promotional_period_text",
                "candidate_value": promotional_summary,
                "evidence_chunk_id": boosted_field["evidence_chunk_id"],
                "evidence_text_excerpt": boosted_field["evidence_text_excerpt"],
                "source_document_id": boosted_field["source_document_id"],
                "source_snapshot_id": boosted_field["source_snapshot_id"],
                "citation_confidence": boosted_field["confidence"],
                "model_execution_id": None,
                "anchor_type": boosted_field["anchor_type"],
                "anchor_value": boosted_field["anchor_value"],
                "page_no": boosted_field["page_no"],
                "chunk_index": boosted_field["chunk_index"],
            },
        )

    runtime_notes.append(
        "Split TD Growth boosted-rate qualification into cleaner `eligibility_text`, `boosted_rate_eligibility`, and `promotional_period_text` values."
    )


def _select_support_match(
    *,
    matches: list[dict[str, object]],
    field_name: str,
    required_keywords: tuple[str, ...],
) -> dict[str, object] | None:
    ranked: list[tuple[float, dict[str, object]]] = []
    for match in matches:
        if str(match.get("field_name", "")) != field_name:
            continue
        excerpt = str(match.get("evidence_text_excerpt", ""))
        lowered = excerpt.lower()
        if not any(keyword in lowered for keyword in required_keywords):
            continue
        score = 0.0
        try:
            score = float(match.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        score += sum(0.05 for keyword in required_keywords if keyword in lowered)
        ranked.append((score, match))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _should_replace_with_pdf(*, field_name: str, existing_field: dict[str, object]) -> bool:
    candidate_value = str(existing_field.get("candidate_value", ""))
    if field_name == "interest_payment_frequency":
        return candidate_value.strip().lower() not in {"monthly", "quarterly", "weekly", "annually", "semi-annually", "daily"}
    if field_name == "interest_calculation_method":
        return _looks_like_noisy_text(candidate_value) or "how our interest is calculated (pdf)" in candidate_value.lower()
    if field_name == "tier_definition_text":
        return _looks_like_noisy_text(candidate_value) or not any(token in candidate_value.lower() for token in ("tier", "balance", "%"))
    return False


def _should_replace_fee_waiver(*, existing_field: dict[str, object], existing_fields: dict[str, dict[str, object]]) -> bool:
    candidate_value = str(existing_field.get("candidate_value", ""))
    if _is_zero_fee_target(existing_fields):
        return True
    return _looks_like_noisy_text(candidate_value) or _looks_like_fee_table_text(candidate_value)


def _looks_like_noisy_text(value: str) -> bool:
    lowered = _normalize_text(value).lower()
    if not lowered:
        return True
    noisy_markers = (
        "additional account details & terms information",
        "how our interest is calculated (pdf)",
        "account and other related service fees (pdf)",
        "bank accounts and fees at a glance",
        "whether you're saving for the future",
        "general list of services",
    )
    return any(marker in lowered for marker in noisy_markers)


def _looks_like_fee_table_text(value: str) -> bool:
    lowered = _normalize_text(value).lower()
    table_markers = (
        "account fees monthly fee $0",
        "transaction fee",
        "transactions included per month",
        "additional transactions",
        "foreign atm fee",
        "free transfers to your other td accounts",
    )
    return any(marker in lowered for marker in table_markers)


def _is_zero_fee_target(existing_fields: dict[str, dict[str, object]]) -> bool:
    for field_name in ("monthly_fee", "public_display_fee"):
        field = existing_fields.get(field_name)
        if field is None:
            continue
        normalized = str(field.get("candidate_value", "")).strip()
        if normalized in {"0", "0.0", "0.00"}:
            return True
    return False


def _is_promotional_period_text(value: str) -> bool:
    lowered = _normalize_text(value).lower()
    if not lowered:
        return False
    if "next month" in lowered:
        return True
    if any(token in lowered for token in ("introductory", "promotion", "promotional", "bonus rate", "offer ends", "offer period")):
        return True
    return bool(_MONTH_RE.search(lowered) and any(token in lowered for token in ("for", "until", "next", "introductory", "promotion")))


def _clean_fee_waiver_text(excerpt: str) -> str | None:
    normalized = _normalize_text(excerpt)
    if "refund the fee" not in normalized.lower():
        return None
    if "maintain the required daily closing balance" in normalized.lower():
        return "The monthly fee is refunded when you maintain the required daily closing balance for the full month."
    return "The monthly fee may be refunded when the required balance conditions are met."


def _clean_interest_calculation_text(excerpt: str) -> str | None:
    normalized = _normalize_text(excerpt)
    lowered = normalized.lower()
    if "daily closing balance" in lowered and "interest" in lowered:
        return "Interest is calculated on the daily closing balance."
    if "interest will be calculated" in lowered:
        return _extract_sentence(normalized, ("interest will be calculated", "daily closing balance"))
    return None


def _clean_interest_payment_frequency(excerpt: str) -> str | None:
    lowered = _normalize_text(excerpt).lower()
    if "monthly" in lowered:
        return "monthly"
    if "quarterly" in lowered:
        return "quarterly"
    if "annually" in lowered or "yearly" in lowered:
        return "annually"
    return None


def _clean_tier_definition_text(excerpt: str) -> str | None:
    normalized = _normalize_text(excerpt)
    lowered = normalized.lower()
    if "daily closing balance" in lowered and "tier" in lowered:
        return _extract_sentence(normalized, ("daily closing balance", "tier")) or normalized[:220]
    if "tier" in lowered and "balance" in lowered:
        return _extract_sentence(normalized, ("tier", "balance")) or normalized[:220]
    return None


def _summarize_growth_eligibility(excerpt: str) -> str | None:
    lowered = excerpt.lower()
    has_chequing = "maintain an eligible td chequing account" in lowered
    has_transactions = "complete at least 2 out of the 3 qualifying monthly transactions" in lowered
    if has_chequing and has_transactions:
        return "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions."
    return None


def _summarize_growth_boosted_rate_eligibility(excerpt: str) -> str | None:
    summary = _summarize_growth_eligibility(excerpt)
    if summary is None:
        return None
    if "next month" in excerpt.lower():
        return summary[:-1] + " to earn the Boosted rate for the next month."
    return summary[:-1] + " to earn the Boosted rate."


def _summarize_growth_promotional_period(excerpt: str) -> str | None:
    if "next month" not in excerpt.lower():
        return None
    return "Meeting the qualification criteria earns the Boosted rate for the next month."


def _extract_sentence(value: str, keywords: tuple[str, ...]) -> str | None:
    for sentence in re.split(r"(?<=[.!?])\s+", value):
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            return sentence.strip()
    return None
