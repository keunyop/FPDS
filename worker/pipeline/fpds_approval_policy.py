from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


# Automatic approval needs a trustworthy product identity plus at least one
# product-defining fact. Empty optional fields are omissions, not failures.
# The ordering selects the first useful field when review AI must repair an
# otherwise identity-only candidate.
_DYNAMIC_DECISION_FIELDS: dict[str, tuple[str, ...]] = {
    "credit-card": (
        "annual_fee",
        "purchase_interest_rate",
        "rewards_summary",
        "cash_advance_rate",
        "balance_transfer_rate",
        "credit_limit_text",
    ),
    "mortgage": (
        "mortgage_rate",
        "rate_type",
        "term_length_text",
        "amortization_text",
        "payment_frequency",
        "prepayment_privileges",
    ),
    "personal-loan": (
        "loan_amount_text",
        "term_length_text",
        "interest_rate",
        "monthly_payment_text",
    ),
    "line-of-credit": (
        "credit_limit_text",
        "security_requirement",
        "secured_flag",
        "interest_rate",
        "minimum_payment_text",
    ),
}

_NON_DECISION_FIELDS = {
    "application_method",
    "bank_name",
    "description_short",
    "effective_date",
    "eligibility_text",
    "last_verified_at",
    "notes",
    "product_name",
    "source_subtype_label",
    "status",
    "subtype_code",
    "tags",
    "target_customer_tags",
}


def is_populated(value: object) -> bool:
    return value not in (None, "", [], {})


def dynamic_decision_fields(
    *,
    product_type: str | None,
    expected_fields: Iterable[str],
) -> list[str]:
    expected = list(
        dict.fromkeys(str(item).strip() for item in expected_fields if str(item).strip())
    )
    normalized_type = str(product_type or "").strip().lower()
    configured = _DYNAMIC_DECISION_FIELDS.get(normalized_type)
    if configured is not None:
        return [field_name for field_name in configured if field_name in expected]
    return [field_name for field_name in expected if field_name not in _NON_DECISION_FIELDS]


def populated_dynamic_decision_fields(
    *,
    product_type: str | None,
    expected_fields: Iterable[str],
    candidate_payload: Mapping[str, Any],
) -> list[str]:
    return [
        field_name
        for field_name in dynamic_decision_fields(
            product_type=product_type,
            expected_fields=expected_fields,
        )
        if is_populated(candidate_payload.get(field_name))
    ]


def dynamic_repair_fields(
    *,
    product_type: str | None,
    expected_fields: Iterable[str],
    candidate_payload: Mapping[str, Any],
) -> list[str]:
    """Return populated decision fields, or one preferred missing alternative."""

    decision_fields = dynamic_decision_fields(
        product_type=product_type,
        expected_fields=expected_fields,
    )
    populated = [
        field_name
        for field_name in decision_fields
        if is_populated(candidate_payload.get(field_name))
    ]
    if populated:
        return populated
    return decision_fields[:1]
