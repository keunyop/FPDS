from __future__ import annotations

from datetime import UTC, date, datetime
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
    "owns or controls",
    "voting shares",
    "beneficial ownership",
    "ownership stake",
    "ownership, control and structure",
    "cash back",
    "cashback",
    "rewards rate",
    "reward rate",
    "prepay up to",
    "prepayment privilege",
    "prepayment amount",
    "prepayment option",
    "prepayment allowance",
    "original mortgage amount",
    "original principal each year",
    "home equity",
    "minimum equity",
    "down payment",
    "loan-to-value",
    "loan to value",
)

_MONTH_NAME_PATTERN = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
_MONTH_DAY_PATTERN = rf"{_MONTH_NAME_PATTERN}\s+\d{{1,2}}(?:st|nd|rd|th)?"
_EXPLICIT_OFFER_END_PATTERNS = (
    re.compile(
        rf"\b(?:offer\s+)?valid\s+from\s+{_MONTH_DAY_PATTERN}(?:,?\s+\d{{4}})?\s+"
        rf"(?:through|to|until)\s+(?P<end>{_MONTH_DAY_PATTERN},?\s+\d{{4}})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:offer\s+)?valid\s+from\s+{_MONTH_DAY_PATTERN}\s+"
        rf"(?:through|to|until)\s+(?P<end>{_MONTH_DAY_PATTERN}),?\s+(?P<year>\d{{4}})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:offer\s+)?(?:valid\s+until|expires?|ends?|through)\s+"
        rf"(?P<end>{_MONTH_DAY_PATTERN},?\s+\d{{4}})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:offer\s+)?(?:valid\s+until|expires?|ends?|through)\s+"
        r"(?P<end>\d{4}-\d{2}-\d{2})\b",
        re.IGNORECASE,
    ),
)


def canonical_deposit_rate_suppression_reason(
    *,
    value: object,
    context: str | None = None,
    reference_date: date | None = None,
) -> str | None:
    decimal_value = _to_decimal(value)
    if decimal_value is not None and decimal_value >= MAX_CANONICAL_ANNUAL_DEPOSIT_RATE:
        return "implausible_annual_deposit_rate"

    normalized_context = _normalize_context(context)
    if not normalized_context:
        return None
    if expired_promotional_offer_end_date(normalized_context, reference_date=reference_date) is not None:
        return "expired_promotional_offer"
    if any(marker in normalized_context for marker in _NON_ANNUAL_RETURN_MARKERS):
        return "non_annual_return_context"
    if re.search(
        r"\b(?:withdraw|redeem|encash|prepay|pre-pay)(?:\s+\w+){0,8}\s+\d{1,3}(?:\.\d+)?\s*%",
        normalized_context,
    ):
        return "non_annual_return_context"
    return None


def expired_promotional_offer_end_date(
    context: str | None,
    *,
    reference_date: date | None = None,
) -> date | None:
    normalized_context = _normalize_context(context)
    if not normalized_context or not any(
        marker in normalized_context
        for marker in ("offer valid", "valid until", "offer expires", "offer ends", "expires", "through")
    ):
        return None

    active_reference_date = reference_date or datetime.now(UTC).date()
    for pattern in _EXPLICIT_OFFER_END_PATTERNS:
        match = pattern.search(normalized_context)
        if match is None:
            continue
        end_text = match.group("end")
        if match.groupdict().get("year"):
            end_text = f"{end_text}, {match.group('year')}"
        parsed_end_date = _parse_offer_date(end_text)
        if parsed_end_date is not None and parsed_end_date < active_reference_date:
            return parsed_end_date
    return None


def _parse_offer_date(value: str) -> date | None:
    normalized = re.sub(r"(?<=\d)(?:st|nd|rd|th)\b", "", value.strip(), flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", normalized):
        try:
            return date.fromisoformat(normalized)
        except ValueError:
            return None
    normalized = re.sub(r"\s*,\s*", " ", normalized)
    for date_format in ("%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(normalized, date_format).date()
        except ValueError:
            continue
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
