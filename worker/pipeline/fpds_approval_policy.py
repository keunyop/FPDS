from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Any

from worker.pipeline.fpds_market_profile import (
    country_product_profile,
    market_profile_product_type_is_known,
)
from worker.pipeline.fpds_rate_safety import contains_explicit_rate_percentage


_SCALAR_NUMBER_RE = re.compile(r"^\s*\$?\s*\d{1,6}(?:\.\d{1,6})?\s*%?\s*$")

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


@dataclass(frozen=True)
class ComparisonQuality:
    applicable: bool
    contract_defined: bool
    complete: bool
    assessed_fields: tuple[str, ...]
    satisfied_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]


def comparison_quality(
    *,
    product_type: str | None,
    expected_fields: Iterable[str],
    candidate_payload: Mapping[str, Any],
    country_code: str | None = None,
) -> ComparisonQuality:
    """Evaluate the market-specific minimum comparison-grade contract.

    Known product types resolve one versioned ``country + product type``
    profile. An operator-managed unknown type fails closed until its registered
    fields contain at least one percentage field and one other decision field.
    """

    normalized_type = str(product_type or "").strip().lower()
    expected = list(
        dict.fromkeys(str(item).strip() for item in expected_fields if str(item).strip())
    )
    profile = country_product_profile(
        country_code=country_code,
        product_type=normalized_type,
    )
    contract_defined = profile is not None
    if profile is None:
        if not normalized_type:
            return ComparisonQuality(False, True, True, (), (), ())
        if str(country_code or "").strip() and market_profile_product_type_is_known(normalized_type):
            # A known product in a new market must not inherit another
            # country's semantics. Register its country profile first.
            return ComparisonQuality(True, False, False, (), (), ())
        rate_fields = tuple(field for field in expected if _looks_like_rate_field(field))
        decision_fields = tuple(
            field
            for field in dynamic_decision_fields(
                product_type=normalized_type,
                country_code=country_code,
                expected_fields=expected,
            )
            if field not in rate_fields
        )
        if not rate_fields or not decision_fields:
            return ComparisonQuality(True, False, False, (), (), ())
        requirements: list[tuple[str, ...]] = [rate_fields, decision_fields]
        active_requirements = requirements
        contract_defined = True
    else:
        active_requirements = [
            requirement.alternatives
            for requirement in profile.requirements
            if requirement.applies(candidate_payload)
        ]

    assessed_fields: list[str] = []
    satisfied_fields: list[str] = []
    missing_fields: list[str] = []
    for alternatives in active_requirements:
        assessed_fields.extend(alternatives)
        satisfied = next(
            (
                field_name
                for field_name in alternatives
                if _comparison_value_is_usable(
                    field_name=field_name,
                    value=candidate_payload.get(field_name),
                )
            ),
            None,
        )
        if (
            normalized_type == "savings"
            and alternatives[0] == "standard_rate"
            and satisfied == "public_display_rate"
            and is_populated(candidate_payload.get("promotional_rate"))
        ):
            # A promotional headline is not the ongoing savings rate customers
            # need for a durable comparison.
            satisfied = None
        if satisfied is None:
            missing_fields.append(alternatives[0])
        else:
            satisfied_fields.append(satisfied)
    return ComparisonQuality(
        applicable=True,
        contract_defined=contract_defined,
        complete=not missing_fields,
        assessed_fields=tuple(dict.fromkeys(assessed_fields)),
        satisfied_fields=tuple(dict.fromkeys(satisfied_fields)),
        missing_fields=tuple(dict.fromkeys(missing_fields)),
    )


def comparison_assessment_fields(
    *,
    product_type: str | None,
    expected_fields: Iterable[str],
    candidate_payload: Mapping[str, Any],
    country_code: str | None = None,
) -> list[str]:
    quality = comparison_quality(
        product_type=product_type,
        country_code=country_code,
        expected_fields=expected_fields,
        candidate_payload=candidate_payload,
    )
    selected = set((*quality.satisfied_fields, *quality.missing_fields))
    return [field_name for field_name in quality.assessed_fields if field_name in selected]


def _comparison_value_is_usable(*, field_name: str, value: object) -> bool:
    if not is_populated(value):
        return False
    if field_name == "term_rate_table":
        return isinstance(value, list) and any(
            isinstance(row, Mapping)
            and is_populated(row.get("rate"))
            and (is_populated(row.get("term_label")) or is_populated(row.get("term_length_days")))
            for row in value
        )
    if field_name == "unlimited_transactions_flag":
        return value is True
    if field_name in {"redeemable_flag", "non_redeemable_flag"}:
        return isinstance(value, bool)
    if field_name.endswith("rate_summary"):
        return contains_explicit_rate_percentage(value)
    if field_name == "annual_fee" or _looks_like_rate_field(field_name):
        if isinstance(value, bool):
            return False
        if isinstance(value, (int, float, Decimal)):
            return True
        return bool(_SCALAR_NUMBER_RE.fullmatch(str(value)))
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _looks_like_rate_field(field_name: str) -> bool:
    normalized = field_name.strip().lower()
    return (
        normalized == "apr"
        or "interest_rate" in normalized
        or normalized.endswith("_apr")
        or normalized.endswith("_rate")
    )


def dynamic_decision_fields(
    *,
    product_type: str | None,
    expected_fields: Iterable[str],
    country_code: str | None = None,
) -> list[str]:
    expected = list(
        dict.fromkeys(str(item).strip() for item in expected_fields if str(item).strip())
    )
    normalized_type = str(product_type or "").strip().lower()
    profile = country_product_profile(
        country_code=country_code,
        product_type=normalized_type,
    )
    if profile is not None:
        configured = profile.collection_fields[1:]
        return [field_name for field_name in configured if field_name in expected]
    return [field_name for field_name in expected if field_name not in _NON_DECISION_FIELDS]


def collection_fields_for_product_type(
    *,
    product_type: str | None,
    expected_fields: Iterable[str] = (),
    country_code: str | None = None,
) -> tuple[str, ...]:
    """Return the bounded fields requested from a new detail source."""

    normalized_type = str(product_type or "").strip().lower()
    profile = country_product_profile(
        country_code=country_code,
        product_type=normalized_type,
    )
    if profile is not None:
        return profile.collection_fields
    expected = tuple(
        dict.fromkeys(str(item).strip() for item in expected_fields if str(item).strip())
    )
    return expected or ("product_name",)


def populated_dynamic_decision_fields(
    *,
    product_type: str | None,
    expected_fields: Iterable[str],
    candidate_payload: Mapping[str, Any],
    country_code: str | None = None,
) -> list[str]:
    return [
        field_name
        for field_name in dynamic_decision_fields(
            product_type=product_type,
            country_code=country_code,
            expected_fields=expected_fields,
        )
        if is_populated(candidate_payload.get(field_name))
    ]


def dynamic_repair_fields(
    *,
    product_type: str | None,
    expected_fields: Iterable[str],
    candidate_payload: Mapping[str, Any],
    country_code: str | None = None,
) -> list[str]:
    """Return the selected satisfied field or missing field for each requirement.

    Alternative canonical fields express the same customer decision fact. Once
    one alternative satisfies that requirement, asking Review AI to verify all
    populated alternatives makes a redundant display field an approval blocker
    even though the essential comparison contract is complete.
    """

    decision_fields = dynamic_decision_fields(
        product_type=product_type,
        country_code=country_code,
        expected_fields=expected_fields,
    )
    quality_fields = comparison_assessment_fields(
        product_type=product_type,
        country_code=country_code,
        expected_fields=expected_fields,
        candidate_payload=candidate_payload,
    )
    if quality_fields:
        return quality_fields
    return decision_fields[:1]
