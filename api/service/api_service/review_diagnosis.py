from __future__ import annotations

import re
from typing import Any


def build_review_diagnosis(
    *,
    source_role: str,
    expected_fields: list[str],
    candidate_payload: dict[str, Any],
    validation_status: str,
    validation_issue_codes: list[str],
    product_type: str | None = None,
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    priority_fields = _priority_expected_fields(product_type=product_type, expected_fields=expected_fields)
    missing_fields = [field_name for field_name in priority_fields if is_empty_review_value(candidate_payload.get(field_name))]
    field_issues = _candidate_field_issues(
        candidate_payload=candidate_payload,
        source_metadata=source_metadata or {},
        product_type=product_type,
    )
    suspect_fields = list(field_issues)
    affected_fields = [
        {
            "field_name": field_name,
            "label": field_label(field_name),
            "issue_type": "missing",
            "current_value": candidate_payload.get(field_name),
        }
        for field_name in missing_fields
    ]
    affected_fields.extend(
        {
            "field_name": field_name,
            "label": field_label(field_name),
            "issue_type": field_issues[field_name],
            "current_value": candidate_payload.get(field_name),
        }
        for field_name in suspect_fields
        if field_name not in missing_fields
    )

    if source_role not in {"detail", "unknown"} or _source_is_non_product_page(source_metadata or {}):
        return _diagnosis(
            category="non_product_source",
            headline="This source does not appear to be a product detail page.",
            recommended_action="reject",
            affected_fields=[],
        )
    if "ambiguous_product_boundary" in validation_issue_codes or _source_has_multi_product_boundary(source_metadata or {}):
        return _diagnosis(
            category="ambiguous_product_boundary",
            headline="This page contains multiple products that cannot be safely reviewed as one proposal.",
            recommended_action="defer",
            affected_fields=[],
        )
    if suspect_fields:
        return _diagnosis(
            category="suspect_fields",
            headline=f"{_field_count_label(len(affected_fields))} {_attention_verb(len(affected_fields))} attention.",
            recommended_action="edit_approve",
            affected_fields=affected_fields,
        )
    if missing_fields:
        return _diagnosis(
            category="missing_fields",
            headline=f"{_field_count_label(len(missing_fields), expected=True)} {_count_verb(len(missing_fields))} missing.",
            recommended_action="edit_approve",
            affected_fields=affected_fields,
        )
    if validation_status == "error":
        return _diagnosis(
            category="validation_error",
            headline="Validation found an error that needs a source check.",
            recommended_action="defer" if "conflicting_evidence" in validation_issue_codes else "edit_approve",
            affected_fields=affected_fields,
        )
    return _diagnosis(
        category="evidence_review",
        headline="Verify the proposed values against the source.",
        recommended_action="approve",
        affected_fields=affected_fields,
    )


def build_review_field_items(
    *,
    expected_fields: list[str],
    candidate_payload: dict[str, Any],
    evidence_field_names: list[str],
    current_payload: dict[str, Any] | None,
    product_type: str | None = None,
    source_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    effective_payload = {**candidate_payload, **(current_payload or {})}
    field_names = list(
        dict.fromkeys(
            [
                *expected_fields,
                *candidate_payload.keys(),
                *evidence_field_names,
                *((current_payload or {}).keys()),
            ]
        )
    )
    items: list[dict[str, Any]] = []
    priority_fields = set(_priority_expected_fields(product_type=product_type, expected_fields=expected_fields))
    field_issues = _candidate_field_issues(
        candidate_payload=candidate_payload,
        source_metadata=source_metadata or {},
        product_type=product_type,
    )
    for field_name in field_names:
        agent_value = candidate_payload.get(field_name)
        effective_value = effective_payload.get(field_name)
        suspect_reason = field_issues.get(field_name)
        items.append(
            {
                "field_name": field_name,
                "label": field_label(field_name),
                "agent_value": agent_value,
                "effective_value": effective_value,
                "missing": field_name in priority_fields and is_empty_review_value(agent_value),
                "suspect": suspect_reason is not None,
                "issue_type": "missing" if field_name in priority_fields and is_empty_review_value(agent_value) else suspect_reason,
                "evidence_count": evidence_field_names.count(field_name),
                "editable": field_name not in {"country_code", "bank_code", "product_family"},
            }
        )
    return sorted(items, key=_review_field_sort_key)


def is_empty_review_value(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def field_label(field_name: str) -> str:
    return field_name.replace("_", " ").strip().title()


def _diagnosis(*, category: str, headline: str, recommended_action: str, affected_fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "category": category,
        "headline": headline,
        "recommended_action": recommended_action,
        "affected_fields": affected_fields,
    }


def _source_has_multi_product_boundary(source_metadata: dict[str, Any]) -> bool:
    discovery_metadata = source_metadata.get("discovery_metadata")
    if not isinstance(discovery_metadata, dict):
        return False
    reason_codes = {
        str(code).strip().lower()
        for code in [
            *list(discovery_metadata.get("selection_reason_codes") or []),
            *list(discovery_metadata.get("page_evidence_reason_codes") or []),
        ]
        if str(code).strip()
    }
    return "multi_product_family_overview" in reason_codes


def _field_count_label(count: int, *, expected: bool = False) -> str:
    qualifier = "required " if expected else ""
    noun = "field" if count == 1 else "fields"
    return f"{count} {qualifier}{noun}"


def _count_verb(count: int) -> str:
    return "is" if count == 1 else "are"


def _attention_verb(count: int) -> str:
    return "needs" if count == 1 else "need"


def _priority_expected_fields(*, product_type: str | None, expected_fields: list[str]) -> list[str]:
    optional_fields = {
        "notes",
        "description_short",
        "rewards_summary",
        "eligibility_text",
        "application_method",
        "fees_text",
        "collateral_text",
        "deposit_insurance",
    }
    normalized_type = str(product_type or "").strip().lower()
    if normalized_type == "gic":
        priority = [field_name for field_name in ("product_name", "minimum_deposit") if field_name in expected_fields]
        term_field = next((field_name for field_name in ("term_length_text", "term_length_days") if field_name in expected_fields), None)
        rate_field = next(
            (
                field_name
                for field_name in ("standard_rate", "base_12_month_rate", "public_display_rate", "highest_rate", "promotional_rate")
                if field_name in expected_fields
            ),
            None,
        )
        return [*priority, *([term_field] if term_field else []), *([rate_field] if rate_field else [])]
    type_priority = {
        "credit-card": {"product_name", "annual_fee", "purchase_interest_rate"},
        "mortgage": {"product_name", "mortgage_rate", "rate_type", "term_length_text"},
        "personal-loan": {"product_name", "interest_rate", "loan_amount_text", "term_length_text"},
        "line-of-credit": {"product_name", "interest_rate", "credit_limit_text", "secured_flag"},
    }.get(normalized_type)
    if type_priority is not None:
        return [field_name for field_name in expected_fields if field_name in type_priority]
    return [field_name for field_name in expected_fields if field_name not in optional_fields]


def _candidate_field_issues(
    *,
    candidate_payload: dict[str, Any],
    source_metadata: dict[str, Any],
    product_type: str | None = None,
) -> dict[str, str]:
    issues = {
        field_name: reason
        for field_name, value in candidate_payload.items()
        if (reason := _suspect_reason(field_name=field_name, value=value, product_type=product_type)) is not None
    }
    if _term_days_conflict(candidate_payload):
        issues["term_length_days"] = "cross_field_conflict"
    for field_name in _duplicated_page_copy_fields(candidate_payload):
        issues[field_name] = "duplicated_page_copy"
    if _product_name_conflicts_with_source(candidate_payload=candidate_payload, source_metadata=source_metadata):
        issues["product_name"] = "source_identity_mismatch"
    return issues


def _suspect_reason(*, field_name: str, value: Any, product_type: str | None = None) -> str | None:
    if field_name.endswith("_flag") or field_name in {"secured_flag", "redeemable_flag"}:
        if value is not None and not isinstance(value, bool):
            return "invalid_type"
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.lower().split())
    if field_name == "product_name" and re.match(r"^(?:see|view|check)\b.{0,50}\brates?\b", normalized):
        return "cta_copy"
    if re.search(r"(?:\{\{|\}\}|\$\{|rds%|%rate\b|\[object object\])", normalized):
        return "unresolved_placeholder"
    if normalized in {"home", "go to main content", "skip to main content", "document go to main content", "document skip to main content", "learn more", "read more"}:
        return "navigation_copy"
    if normalized.startswith("document ") and len(normalized.split()) <= 4:
        return "navigation_copy"
    if product_type in {"credit-card", "mortgage", "personal-loan", "line-of-credit"}:
        if field_name == "monthly_payment_text" and re.fullmatch(
            r"monthly fees?\s*(?:free|\$?0(?:\.00)?)", normalized
        ):
            return "cross_product_copy"
        if field_name == "fees_text" and normalized in {"monthly fees free", "monthly fee free"}:
            return "cross_product_copy"
        if field_name == "loan_amount_text" and len(normalized) > 100 and re.search(
            r"(?:\$|\b\d[\d,.]*\b|\bminimum\b|\bmaximum\b|\bup to\b)", normalized
        ) is None:
            return "non_value_copy"
        if field_name == "security_requirement":
            short_navigation_markers = (
                "document", "rates", "contact us", "search", "login", "log in", "go to homepage", "online banking"
            )
            if sum(marker in normalized for marker in short_navigation_markers) >= 3:
                return "navigation_copy"
        if field_name == "prepayment_privileges" and not any(
            marker in normalized
            for marker in ("prepay", "pre-pay", "prepayment", "pre-payment", "repay", "penalty", "privilege")
        ):
            return "non_value_copy"
    navigation_markers = (
        "main navigation",
        "online banking",
        "find an atm",
        "find a branch",
        "about us",
        "contact us",
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
    if len(normalized) >= 140 and sum(marker in normalized for marker in navigation_markers) >= 3:
        return "navigation_copy"
    if (field_name.endswith("_rate") or field_name in {"rate", "interest_rate"}) and len(normalized) >= 45:
        if len(normalized) >= 150:
            return "page_copy"
        if field_name == "post_maturity_interest_rate" and len(normalized) >= 160:
            return None if re.search(r"(?:%|\bprime\b)", normalized, flags=re.IGNORECASE) else "non_value_copy"
        if not re.search(r"(?:\d|%|\bprime\b)", normalized, flags=re.IGNORECASE):
            return "non_value_copy"
    if field_name == "application_method" and normalized.startswith("how do i apply"):
        return "non_value_copy"
    if field_name == "payment_frequency":
        frequency_markers = ("weekly", "biweekly", "bi-weekly", "semi-monthly", "monthly", "accelerated")
        if (
            len(normalized) > 100
            or any(marker in normalized for marker in ("calculator", "prepayment", "pre-payment", "special offers"))
            or not any(marker in normalized for marker in frequency_markers)
        ):
            return "non_value_copy"
    if field_name == "amortization_text" and (
        len(normalized) > 160
        or re.search(r"\b\d{1,3}\s*(?:year|years|month|months)\b", normalized) is None
    ):
        return "non_value_copy"
    if field_name in {"eligibility", "eligibility_text"}:
        calculator_cta = "calculator" in normalized and any(
            marker in normalized
            for marker in ("calculate", "find out how much", "may qualify to borrow", "estimate how much")
        ) and not any(
            marker in normalized
            for marker in ("must ", "requires ", "eligible if", "at least", "minimum ", "resident", "income", "credit score")
        )
        if calculator_cta:
            return "non_value_copy"
        estimate_output = any(
            marker in normalized
            for marker in ("receive an estimate", "get an estimate", "estimate for the total")
        ) and "eligible" in normalized and not any(
            marker in normalized
            for marker in ("must ", "requires ", "eligible if", "at least", "minimum ", "resident", "income", "credit score")
        )
        if estimate_output:
            return "non_value_copy"
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
    if len(normalized) >= 240 and field_name in concise_fields:
        return "page_copy"
    return None


def _duplicated_page_copy_fields(candidate_payload: dict[str, Any]) -> set[str]:
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


def _term_days_conflict(candidate_payload: dict[str, Any]) -> bool:
    raw_days = candidate_payload.get("term_length_days")
    term_text = str(candidate_payload.get("term_length_text") or "")
    if raw_days in {None, ""} or not term_text:
        return False
    try:
        term_days = int(str(raw_days))
    except (TypeError, ValueError):
        return False
    durations: list[int] = []
    for amount, unit in re.findall(r"(?<!\d)(\d{1,3})\s*(day|days|month|months|year|years)\b", term_text, flags=re.IGNORECASE):
        value = int(amount)
        durations.append(value if unit.lower().startswith("day") else value * 30 if unit.lower().startswith("month") else value * 365)
    if not durations:
        return False
    minimum_days = min(durations)
    maximum_days = max(durations)
    return not (
        minimum_days - max(7, round(minimum_days * 0.08))
        <= term_days
        <= maximum_days + max(7, round(maximum_days * 0.08))
    )


def _product_name_conflicts_with_source(*, candidate_payload: dict[str, Any], source_metadata: dict[str, Any]) -> bool:
    product_name = str(candidate_payload.get("product_name") or "").strip().lower()
    discovery = source_metadata.get("discovery_metadata")
    if not product_name or not isinstance(discovery, dict):
        return False
    page_title = str(discovery.get("page_title") or "")
    source_identity = " ".join(
        str(discovery.get(key) or "")
        for key in ("page_title", "primary_heading")
    ).lower()
    if not source_identity:
        return False
    stop_words = {
        "bank", "canada", "personal", "product", "products", "account", "accounts",
        "credit", "card", "cards", "loan", "loans", "mortgage", "mortgages", "line", "of", "the", "a", "and",
    }
    if "|" in page_title:
        stop_words.update(
            term
            for term in re.findall(r"[a-z0-9]+", page_title.rsplit("|", 1)[-1].lower())
            if len(term) >= 4
        )
    name_terms = {term for term in re.findall(r"[a-z0-9]+", product_name) if len(term) >= 4 and term not in stop_words}
    source_terms = {term for term in re.findall(r"[a-z0-9]+", source_identity) if len(term) >= 4 and term not in stop_words}
    return bool(name_terms and source_terms and name_terms.isdisjoint(source_terms))


def _source_is_non_product_page(source_metadata: dict[str, Any]) -> bool:
    source_url = str(source_metadata.get("normalized_source_url") or "").lower()
    if any(
        marker in source_url
        for marker in (
            "/resource-centre/",
            "/resource-center/",
            "/articles/",
            "/blog/",
            "/switch-mortgage",
            "/switch-your-mortgage",
            "/manage-mortgage",
            "/manage-my-mortgage",
        )
    ):
        return True
    discovery_metadata = source_metadata.get("discovery_metadata")
    if not isinstance(discovery_metadata, dict):
        return False
    reason_codes = {
        str(code).strip().lower()
        for code in [
            *list(discovery_metadata.get("selection_reason_codes") or []),
            *list(discovery_metadata.get("page_evidence_reason_codes") or []),
        ]
        if str(code).strip()
    }
    return bool(reason_codes.intersection({"non_product_editorial_page", "non_product_service_flow"}))


def _review_field_sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
    return (
        0 if item["missing"] or item["suspect"] else 1,
        0 if item["field_name"] == "product_name" else 1,
        str(item["field_name"]),
    )
