from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


FIELD_CONTRACT_VERSION = "2026-07-16"


@dataclass(frozen=True)
class FieldContract:
    value_type: str
    unit: str | None = None


_STRING_FIELDS = {
    "product_name",
    "description_short",
    "fee_waiver_condition",
    "promotional_period_text",
    "eligibility_text",
    "application_method",
    "post_maturity_interest_rate",
    "tax_benefits",
    "deposit_insurance",
    "term_length_text",
    "interest_calculation_method",
    "interest_payment_frequency",
    "tier_definition_text",
    "withdrawal_limit_text",
    "compounding_frequency",
    "payout_option",
    "cheque_book_info",
    "notes",
    "rate_type",
    "amortization_text",
    "payment_frequency",
    "prepayment_privileges",
    "rewards_summary",
    "credit_limit_text",
    "loan_amount_text",
    "monthly_payment_text",
    "security_requirement",
    "collateral_text",
    "minimum_payment_text",
    "fees_text",
}
_DECIMAL_FIELDS = {
    "monthly_fee",
    "public_display_fee",
    "minimum_balance",
    "minimum_deposit",
    "standard_rate",
    "base_12_month_rate",
    "promotional_rate",
    "public_display_rate",
    "highest_rate",
    "annual_fee",
    "purchase_interest_rate",
    "cash_advance_rate",
    "balance_transfer_rate",
    "mortgage_rate",
    "interest_rate",
}
_MONEY_FIELDS = {
    "monthly_fee",
    "public_display_fee",
    "minimum_balance",
    "minimum_deposit",
    "annual_fee",
}
_INTEGER_FIELDS = {"term_length_days", "included_transactions"}
_BOOLEAN_FIELDS = {
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
    "secured_flag",
}
_JSON_FIELDS = {"term_rate_table"}


def field_contract(field_name: str) -> FieldContract | None:
    normalized = field_name.strip().lower()
    if normalized in _STRING_FIELDS:
        return FieldContract("string")
    if normalized in _DECIMAL_FIELDS:
        return FieldContract(
            "decimal",
            "currency_amount" if normalized in _MONEY_FIELDS else "percentage_points",
        )
    if normalized in _INTEGER_FIELDS:
        return FieldContract("integer", "days" if normalized == "term_length_days" else "count")
    if normalized in _BOOLEAN_FIELDS or normalized.endswith("_flag"):
        return FieldContract("boolean")
    if normalized in _JSON_FIELDS:
        return FieldContract("json", "structured_rows")
    return None


def canonical_value_type(field_name: str, declared_type: str = "string") -> str:
    contract = field_contract(field_name)
    if contract is not None:
        return contract.value_type
    return declared_type if declared_type in {"string", "decimal", "integer", "boolean", "json"} else "string"


def field_contract_payload(field_names: list[str] | tuple[str, ...]) -> dict[str, dict[str, str | None]]:
    payload: dict[str, dict[str, str | None]] = {}
    for field_name in field_names:
        contract = field_contract(field_name)
        if contract is None:
            continue
        payload[field_name] = {
            "value_type": contract.value_type,
            "unit": contract.unit,
        }
    return payload


def value_matches_contract(field_name: str, value: object) -> bool:
    if value is None:
        return True
    contract = field_contract(field_name)
    if contract is None:
        return True
    if contract.value_type == "string":
        return isinstance(value, str)
    if contract.value_type == "boolean":
        return isinstance(value, bool)
    if contract.value_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if contract.value_type == "decimal":
        return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
    if contract.value_type == "json":
        return isinstance(value, (list, dict))
    return True


def mapping_contract_metadata(field_name: str) -> dict[str, Any]:
    contract = field_contract(field_name)
    if contract is None:
        return {"field_contract_version": FIELD_CONTRACT_VERSION}
    return {
        "field_contract_version": FIELD_CONTRACT_VERSION,
        "canonical_value_type": contract.value_type,
        "canonical_unit": contract.unit,
    }
