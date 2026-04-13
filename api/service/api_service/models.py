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
