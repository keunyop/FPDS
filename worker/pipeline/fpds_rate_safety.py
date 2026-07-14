from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re

MAX_CANONICAL_ANNUAL_DEPOSIT_RATE = Decimal("25")

_NON_ANNUAL_RETURN_MARKERS = (
    "not an annual rate",
    "not an annualized rate",
    "not annual rate",
    "full term return",
    "full-term return",
    "maximum full term return",
    "maximum full-term return",
    "minimum guaranteed return",
    "index return",
    "underlying index",
    "based on the performance",
    "performance of the underlying",
    "participation rate",
    "participation factor",
    "principal guaranteed",
    "principal is guaranteed",
    "principal protection",
    "return cap",
    "return limit",
    "limitation on interest",
    "limit on interest",
    "cannot exceed",
    "not exceed",
    "regardless of the performance",
    "of the original investment",
    "of original investment",
    "of the original principal",
    "of original principal",
    "of the principal balance",
    "partial redemption",
    "partial withdrawal",
    "redemption limit",
    "withdrawal limit",
    "amount may be redeemed",
    "amount may be withdrawn",
    "redeem up to",
    "withdraw up to",
    "encash up to",
)


def canonical_deposit_rate_suppression_reason(
    *,
    value: object,
    context: str | None = None,
) -> str | None:
    decimal_value = _to_decimal(value)
    if decimal_value is not None and decimal_value > MAX_CANONICAL_ANNUAL_DEPOSIT_RATE:
        return "implausible_annual_deposit_rate"

    normalized_context = _normalize_context(context)
    if not normalized_context:
        return None
    if any(marker in normalized_context for marker in _NON_ANNUAL_RETURN_MARKERS):
        return "non_annual_return_context"
    return None


def _to_decimal(value: object) -> Decimal | None:
    if value in {None, ""} or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    normalized = str(value).replace(",", "").replace("$", "").replace("%", "").strip()
    normalized = re.sub(r"\b(?:cad|cdn|dollars?)\b", "", normalized, flags=re.IGNORECASE).strip()
    normalized = re.sub(r"\s+", "", normalized)
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError):
        return None


def _normalize_context(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()
