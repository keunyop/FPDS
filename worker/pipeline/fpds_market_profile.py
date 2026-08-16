from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


MARKET_PROFILE_VERSION = "2026-08-16-v3"


@dataclass(frozen=True)
class ComparisonRequirement:
    """One customer decision fact and the canonical fields that may satisfy it."""

    key: str
    alternatives: tuple[str, ...]
    required_when: str = "always"

    def applies(self, candidate_payload: Mapping[str, Any]) -> bool:
        if self.required_when == "always":
            return True
        if self.required_when == "positive_monthly_fee":
            for field_name in ("monthly_fee", "public_display_fee"):
                value = candidate_payload.get(field_name)
                if value in (None, "") or isinstance(value, bool):
                    continue
                try:
                    return Decimal(str(value).replace("$", "").replace(",", "").strip()) > 0
                except (InvalidOperation, ValueError):
                    continue
            return False
        raise ValueError(f"Unsupported market-profile condition: {self.required_when}")


@dataclass(frozen=True)
class CountryProductProfile:
    country_code: str
    product_type: str
    profile_version: str
    requirements: tuple[ComparisonRequirement, ...]
    supplemental_fields: tuple[str, ...] = ()

    @property
    def profile_key(self) -> str:
        return f"{self.country_code}:{self.product_type}"

    @property
    def collection_fields(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (
                    "product_name",
                    *(
                        field_name
                        for requirement in self.requirements
                        for field_name in requirement.alternatives
                    ),
                    *self.supplemental_fields,
                )
            )
        )


def _requirement(
    key: str,
    *alternatives: str,
    required_when: str = "always",
) -> ComparisonRequirement:
    return ComparisonRequirement(
        key=key,
        alternatives=tuple(alternatives),
        required_when=required_when,
    )


# This is the Canada/legacy baseline, not a claim that Canadian product
# semantics are universal. Explicitly named future countries fail closed until
# their product profile is registered; country-less legacy calls retain this
# baseline while callers finish carrying the country dimension.
_DEFAULT_REQUIREMENTS: dict[str, tuple[ComparisonRequirement, ...]] = {
    "chequing": (
        _requirement("monthly_fee", "monthly_fee", "public_display_fee"),
        # For Canadian chequing products this field represents the positive
        # balance threshold that waives a monthly fee. A genuinely no-fee
        # account has no fee-waiver threshold to publish, so requiring one
        # would turn an inapplicable fact into a false missing-value review.
        _requirement(
            "minimum_balance",
            "minimum_balance",
            required_when="positive_monthly_fee",
        ),
        _requirement("transactions", "included_transactions", "unlimited_transactions_flag"),
    ),
    "savings": (
        _requirement("ongoing_rate", "standard_rate", "base_12_month_rate", "public_display_rate"),
        _requirement("monthly_fee", "monthly_fee", "public_display_fee"),
        _requirement("minimum_balance", "minimum_balance"),
    ),
    "gic": (
        _requirement(
            "rate",
            "standard_rate",
            "base_12_month_rate",
            "public_display_rate",
            "highest_rate",
            "interest_rate_summary",
            "term_rate_table",
        ),
        _requirement("term", "term_length_text", "term_length_days", "term_rate_table"),
        _requirement("minimum_deposit", "minimum_deposit"),
        _requirement("redeemability", "redeemable_flag", "non_redeemable_flag"),
    ),
    "credit-card": (
        _requirement("annual_fee", "annual_fee"),
        _requirement("purchase_rate", "purchase_interest_rate"),
    ),
    "mortgage": (
        _requirement("rate", "mortgage_rate", "interest_rate_summary"),
        _requirement("rate_type", "rate_type"),
        _requirement("term", "term_length_text"),
    ),
    "personal-loan": (
        _requirement("rate", "interest_rate", "interest_rate_summary"),
        _requirement("amount", "loan_amount_text"),
        _requirement("term", "term_length_text"),
    ),
    "line-of-credit": (
        _requirement("rate", "interest_rate", "interest_rate_summary"),
        _requirement("limit", "credit_limit_text"),
        _requirement("security", "secured_flag", "security_requirement", "collateral_text"),
    ),
}


_COUNTRY_OVERRIDES: dict[tuple[str, str], tuple[ComparisonRequirement, ...]] = {
    # US checking pages normally describe monthly service fees, opening/minimum
    # balance, and relationship or activity waivers. A Canadian-style included
    # transaction count is neither consistently published nor decision-critical.
    ("US", "chequing"): (
        _requirement("monthly_fee", "monthly_fee", "public_display_fee"),
        _requirement("opening_or_minimum_balance", "minimum_balance", "minimum_deposit"),
        _requirement(
            "fee_waiver_or_qualifying_activity",
            "fee_waiver_condition",
            required_when="positive_monthly_fee",
        ),
    ),
    ("US", "savings"): (
        _requirement("ongoing_apy", "standard_rate", "base_12_month_rate", "public_display_rate"),
        _requirement("monthly_fee", "monthly_fee", "public_display_fee"),
        _requirement("opening_or_minimum_balance", "minimum_balance", "minimum_deposit"),
        _requirement(
            "fee_waiver_or_qualifying_activity",
            "fee_waiver_condition",
            required_when="positive_monthly_fee",
        ),
    ),
    # US certificates are compared by APY schedule, term, opening deposit, and
    # early-withdrawal penalty. Canadian redeemable/non-redeemable booleans are
    # not imposed on this market.
    ("US", "gic"): (
        _requirement(
            "apy_or_rate_schedule",
            "standard_rate",
            "base_12_month_rate",
            "public_display_rate",
            "highest_rate",
            "interest_rate_summary",
            "term_rate_table",
        ),
        _requirement("term", "term_length_text", "term_length_days", "term_rate_table"),
        _requirement("minimum_opening_deposit", "minimum_deposit"),
        _requirement("early_withdrawal_penalty", "early_withdrawal_penalty"),
    ),
    # Keep explicit US ownership even where today's minimum matches the global
    # baseline. That makes Public projection essential-only now and lets a
    # future market change remain isolated to this registry.
    ("US", "credit-card"): (
        _requirement("annual_fee", "annual_fee"),
        # US issuers normally publish a creditworthiness-based variable APR
        # range. The source-language summary is the preferred comparison fact;
        # an exact scalar remains a valid alternative for fixed-rate cards.
        _requirement(
            "purchase_rate",
            "purchase_interest_rate_summary",
            "purchase_interest_rate",
        ),
    ),
    # A standalone US mortgage scalar is misleading without its scenario. The
    # source-language summary retains APR/rate plus ZIP, LTV, points, credit,
    # date, and other assumptions when the official source states them.
    ("US", "mortgage"): (
        _requirement("qualified_rate_or_apr", "interest_rate_summary"),
        _requirement("rate_type", "rate_type"),
        _requirement("term", "term_length_text"),
    ),
    ("US", "personal-loan"): (
        _requirement("apr_or_rate_range", "interest_rate_summary", "interest_rate"),
        _requirement("amount_range", "loan_amount_text"),
        _requirement("term_range", "term_length_text"),
    ),
    ("US", "line-of-credit"): (
        _requirement("rate", "interest_rate", "interest_rate_summary"),
        _requirement("limit", "credit_limit_text"),
        _requirement("security", "secured_flag", "security_requirement", "collateral_text"),
    ),
}


_COUNTRY_SUPPLEMENTAL_FIELDS: dict[tuple[str, str], tuple[str, ...]] = {
    # A simple APY needs no prose, but a new-customer, balance-qualified, or
    # relationship APY must carry its material conditions into Public.
    ("US", "savings"): ("interest_rate_summary",),
    # Keep the scalar available for fixed-rate cards and numeric consumers; it
    # is not required when the exact source-language range is present.
    ("US", "credit-card"): ("purchase_interest_rate_summary",),
}


def country_product_profile(
    *,
    country_code: str | None,
    product_type: str | None,
) -> CountryProductProfile | None:
    normalized_type = str(product_type or "").strip().lower()
    if not normalized_type:
        return None
    normalized_country = str(country_code or "").strip().upper()
    requirements = _COUNTRY_OVERRIDES.get((normalized_country, normalized_type))
    resolved_country = normalized_country
    if requirements is None and normalized_country in {"", "CA"}:
        requirements = _DEFAULT_REQUIREMENTS.get(normalized_type)
        # `*` marks the backward-compatible Canada/legacy baseline to callers
        # that distinguish explicit market overrides for Public projection.
        resolved_country = "*"
    if requirements is None:
        return None
    return CountryProductProfile(
        country_code=resolved_country,
        product_type=normalized_type,
        profile_version=MARKET_PROFILE_VERSION,
        requirements=requirements,
        supplemental_fields=_COUNTRY_SUPPLEMENTAL_FIELDS.get(
            (normalized_country, normalized_type),
            (),
        ),
    )


def market_profile_product_type_is_known(product_type: str | None) -> bool:
    return str(product_type or "").strip().lower() in _DEFAULT_REQUIREMENTS


def market_profile_metadata(
    *,
    country_code: str | None,
    product_type: str | None,
) -> dict[str, str]:
    normalized_country = str(country_code or "").strip().upper()
    requested_country = normalized_country or "*"
    normalized_type = str(product_type or "").strip().lower()
    profile = country_product_profile(
        country_code=country_code,
        product_type=product_type,
    )
    if profile is None:
        return {
            "market_profile_key": f"{requested_country}:{normalized_type}",
            "market_profile_version": MARKET_PROFILE_VERSION,
            "market_profile_resolution": "dynamic_fail_closed",
        }
    return {
        # Keep the requested market in the operational key so a later profile
        # version does not rewrite source-registry identity or history.
        "market_profile_key": f"{requested_country}:{normalized_type}",
        "market_profile_version": profile.profile_version,
        "market_profile_resolution": (
            "country_override"
            if normalized_country and normalized_country != "CA"
            else "canada_baseline" if normalized_country == "CA" else "legacy_countryless_baseline"
        ),
    }
