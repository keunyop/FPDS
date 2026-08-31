from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AUTH_PASSWORD_MIN_LENGTH = 4


class LoginRequest(BaseModel):
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    login_id: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=AUTH_PASSWORD_MIN_LENGTH, max_length=256)


class CountrySwitchRequest(BaseModel):
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")


class PublicEngagementRequest(BaseModel):
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    product_id: str = Field(min_length=1, max_length=120)
    event_type: Literal[
        "finder_product_selected",
        "official_bank_click",
        "product_detail_click",
    ]


class PublicFeedbackRequest(BaseModel):
    country_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")
    submission_type: Literal["product_error", "site_feedback"]
    category: Literal[
        "accessibility_issue",
        "broken_link",
        "content_issue",
        "feature_suggestion",
        "incorrect_product_details",
        "incorrect_rate_or_fee",
        "missing_information",
        "other",
        "outdated_information",
        "usability_issue",
    ]
    details: str | None = Field(default=None, max_length=2000)
    locale: Literal["en", "ko", "ja"] = "en"
    product_id: str | None = Field(default=None, min_length=1, max_length=120)


class SignupRequestCreateRequest(BaseModel):
    login_id: str = Field(min_length=3, max_length=50)
    display_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=AUTH_PASSWORD_MIN_LENGTH, max_length=256)


class SignupRequestReviewRequest(BaseModel):
    role: str | None = Field(default=None, max_length=20)
    reason_text: str | None = Field(default=None, max_length=2000)


class ReviewDecisionRequest(BaseModel):
    reason_code: str | None = Field(default=None, max_length=100)
    reason_text: str | None = Field(default=None, max_length=2000)
    override_payload: dict[str, Any] = Field(default_factory=dict)


class SourceRegistryWriteRequest(BaseModel):
    source_id: str | None = Field(default=None, max_length=120)
    bank_code: str | None = Field(default=None, max_length=20)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    product_type: str | None = Field(default=None, max_length=50)
    product_key: str | None = Field(default=None, max_length=120)
    source_name: str | None = Field(default=None, max_length=300)
    source_url: str | None = Field(default=None, max_length=2000)
    source_type: str | None = Field(default=None, max_length=30)
    discovery_role: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=30)
    priority: str | None = Field(default=None, max_length=10)
    source_language: str | None = Field(default=None, max_length=10)
    purpose: str | None = Field(default=None, max_length=1000)
    expected_fields: list[str] = Field(default_factory=list)
    seed_source_flag: bool | None = None
    last_verified_at: str | None = None
    last_seen_at: str | None = None
    redirect_target_url: str | None = Field(default=None, max_length=2000)
    alias_urls: list[str] = Field(default_factory=list)
    change_reason: str | None = Field(default=None, max_length=2000)


class SourceCollectionRequest(BaseModel):
    source_ids: list[str] = Field(default_factory=list, min_length=1)


class BankWriteRequest(BaseModel):
    bank_name: str | None = Field(default=None, max_length=300)
    homepage_url: str | None = Field(default=None, max_length=2000)
    logo_url: str | None = Field(default=None, max_length=2000)
    logo_alt_text: str | None = Field(default=None, max_length=300)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    source_language: str | None = Field(default=None, max_length=10)
    status: str | None = Field(default=None, max_length=30)
    change_reason: str | None = Field(default=None, max_length=2000)
    initial_coverage_product_types: list[str] = Field(default_factory=list)


class BankAiOnboardingRequest(BaseModel):
    count: int = Field(ge=1, le=10)


class SourceCatalogWriteRequest(BaseModel):
    bank_code: str | None = Field(default=None, max_length=20)
    product_type: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=30)
    change_reason: str | None = Field(default=None, max_length=2000)


class SourceCatalogCollectionRequest(BaseModel):
    catalog_item_ids: list[str] = Field(default_factory=list, min_length=1)
    precision_rediscovery: bool = False


class ProductTypeWriteRequest(BaseModel):
    product_type_code: str | None = Field(default=None, max_length=50)
    product_family: str | None = Field(default=None, max_length=50)
    display_name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, max_length=30)
