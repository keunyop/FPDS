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
) -> dict[str, Any]:
    missing_fields = [field_name for field_name in expected_fields if is_empty_review_value(candidate_payload.get(field_name))]
    suspect_fields = [
        field_name
        for field_name, value in candidate_payload.items()
        if _suspect_reason(field_name=field_name, value=value) is not None
    ]
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
            "issue_type": _suspect_reason(field_name=field_name, value=candidate_payload.get(field_name)),
            "current_value": candidate_payload.get(field_name),
        }
        for field_name in suspect_fields
        if field_name not in missing_fields
    )

    if source_role not in {"detail", "unknown"}:
        return _diagnosis(
            category="non_product_source",
            headline="This source does not appear to be a product detail page.",
            recommended_action="reject",
            affected_fields=affected_fields,
        )
    if suspect_fields:
        return _diagnosis(
            category="suspect_fields",
            headline=f"{_field_count_label(len(suspect_fields))} contain navigation or non-value marketing copy.",
            recommended_action="edit_approve",
            affected_fields=affected_fields,
        )
    if missing_fields:
        return _diagnosis(
            category="missing_fields",
            headline=f"{_field_count_label(len(missing_fields), expected=True)} are missing.",
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
    for field_name in field_names:
        agent_value = candidate_payload.get(field_name)
        effective_value = effective_payload.get(field_name)
        suspect_reason = _suspect_reason(field_name=field_name, value=agent_value)
        items.append(
            {
                "field_name": field_name,
                "label": field_label(field_name),
                "agent_value": agent_value,
                "effective_value": effective_value,
                "missing": field_name in expected_fields and is_empty_review_value(agent_value),
                "suspect": suspect_reason is not None,
                "issue_type": "missing" if field_name in expected_fields and is_empty_review_value(agent_value) else suspect_reason,
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


def _field_count_label(count: int, *, expected: bool = False) -> str:
    qualifier = "expected " if expected else ""
    noun = "field" if count == 1 else "fields"
    return f"{count} {qualifier}{noun}"


def _suspect_reason(*, field_name: str, value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.lower().split())
    if normalized in {"home", "go to main content", "document go to main content", "learn more", "read more"}:
        return "navigation_copy"
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
    )
    if len(normalized) >= 140 and sum(marker in normalized for marker in navigation_markers) >= 3:
        return "navigation_copy"
    if (field_name.endswith("_rate") or field_name in {"rate", "interest_rate"}) and len(normalized) >= 45:
        if field_name == "post_maturity_interest_rate" and len(normalized) >= 160:
            return None if re.search(r"(?:%|\bprime\b)", normalized, flags=re.IGNORECASE) else "non_value_copy"
        if not re.search(r"(?:\d|%|\bprime\b)", normalized, flags=re.IGNORECASE):
            return "non_value_copy"
    return None


def _review_field_sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
    return (
        0 if item["missing"] or item["suspect"] else 1,
        0 if item["field_name"] == "product_name" else 1,
        str(item["field_name"]),
    )
