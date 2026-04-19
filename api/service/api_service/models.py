from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=256)


class ReviewDecisionRequest(BaseModel):
    reason_code: str | None = Field(default=None, max_length=100)
    reason_text: str | None = Field(default=None, max_length=2000)
    override_payload: dict[str, Any] = Field(default_factory=dict)


class SourceRegistryWriteRequest(BaseModel):
    source_id: str | None = Field(default=None, max_length=120)
    bank_code: str | None = Field(default=None, max_length=20)
    country_code: str | None = Field(default=None, max_length=10)
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
    country_code: str | None = Field(default=None, max_length=10)
    source_language: str | None = Field(default=None, max_length=10)
    status: str | None = Field(default=None, max_length=30)
    change_reason: str | None = Field(default=None, max_length=2000)
    initial_coverage_product_types: list[str] = Field(default_factory=list)


class SourceCatalogWriteRequest(BaseModel):
    bank_code: str | None = Field(default=None, max_length=20)
    product_type: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=30)
    change_reason: str | None = Field(default=None, max_length=2000)


class SourceCatalogCollectionRequest(BaseModel):
    catalog_item_ids: list[str] = Field(default_factory=list, min_length=1)


class ProductTypeWriteRequest(BaseModel):
    product_type_code: str | None = Field(default=None, max_length=50)
    display_name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, max_length=30)
