from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .models import NormalizationEvidenceLink, NormalizationExtractedField, NormalizationInput

_PROFILE_PATH = Path(__file__).resolve().parents[2] / "discovery" / "data" / "canada_big5_deposit_product_profiles_2026-05-23.json"


@dataclass(frozen=True)
class ProductProfile:
    profile_id: str
    bank_codes: tuple[str, ...]
    product_types: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_url_tokens: tuple[str, ...]
    product_name: str
    fields: dict[str, object]


def expand_profile_product_inputs(item: NormalizationInput) -> list[NormalizationInput]:
    if not _profile_expansion_enabled(item):
        return []
    profiles = _profiles_for_item(item)
    if not profiles:
        return []
    return [_build_profile_input(item=item, profile=profile) for profile in profiles]


def should_suppress_unprofiled_profile_input(item: NormalizationInput) -> bool:
    if not _profile_expansion_enabled(item):
        return False
    return any(_profile_matches_bank_and_type(item=item, profile=profile) for profile in _load_product_profiles())


def _profiles_for_item(item: NormalizationInput) -> list[ProductProfile]:
    source_id = str(item.source_id or item.source_metadata.get("source_id") or "")
    source_url = str(item.normalized_source_url or "").lower().rstrip("/")
    matched: list[ProductProfile] = []
    for profile in _load_product_profiles():
        if not _profile_matches_bank_and_type(item=item, profile=profile):
            continue
        if source_id and source_id in profile.source_ids:
            matched.append(profile)
            continue
        if source_url and any(_source_url_matches_token(source_url, token) for token in profile.source_url_tokens):
            matched.append(profile)
    return matched


def _profile_matches_bank_and_type(*, item: NormalizationInput, profile: ProductProfile) -> bool:
    bank_code = str(item.bank_code or item.source_metadata.get("bank_code") or "").upper()
    product_type = _product_type_for_item(item)
    if not bank_code or not product_type:
        return False
    return bool(set(profile.bank_codes) & _bank_code_aliases(bank_code)) and product_type in profile.product_types


def _product_type_for_item(item: NormalizationInput) -> str:
    return str(item.source_metadata.get("product_type") or item.schema_context.get("product_type") or "").strip().lower()


def _profile_expansion_enabled(item: NormalizationInput) -> bool:
    """Keep dated product profiles as explicit QA fixtures, never live collection truth."""

    return str(item.source_metadata.get("product_profile_expansion_mode") or "").strip().lower() == "fixture"


def _build_profile_input(*, item: NormalizationInput, profile: ProductProfile) -> NormalizationInput:
    evidence_link = _first_evidence_link(item)
    profile_fields = [
        _profile_field(item=item, profile=profile, field_name="product_name", value=profile.product_name, value_type="string", evidence_link=evidence_link),
        *[
            _profile_field(
                item=item,
                profile=profile,
                field_name=field_name,
                value=value,
                value_type=_value_type(value),
                evidence_link=evidence_link,
            )
            for field_name, value in profile.fields.items()
        ],
    ]
    profile_links = [
        _profile_evidence_link(item=item, field=field, evidence_link=evidence_link)
        for field in profile_fields
        if evidence_link is not None
    ]
    return NormalizationInput(
        **{
            **item.__dict__,
            "candidate_key": profile.profile_id,
            "source_metadata": {
                **item.source_metadata,
                "product_profile_id": profile.profile_id,
                "product_page_url": profile.fields.get("product_page_url"),
                "product_name": profile.product_name,
            },
            "extracted_fields": [
                *item.extracted_fields,
                *profile_fields,
            ],
            "evidence_links": [
                *item.evidence_links,
                *profile_links,
            ],
            "runtime_notes": [
                *item.runtime_notes,
                f"Expanded deposit product profile `{profile.profile_id}` from source `{item.source_id}`.",
            ],
        }
    )


def _profile_field(
    *,
    item: NormalizationInput,
    profile: ProductProfile,
    field_name: str,
    value: object,
    value_type: str,
    evidence_link: NormalizationEvidenceLink | None,
) -> NormalizationExtractedField:
    return NormalizationExtractedField(
        field_name=field_name,
        candidate_value=value,
        value_type=value_type,
        confidence=0.9,
        extraction_method="source_profile_product_expansion",
        source_document_id=item.source_document_id,
        source_snapshot_id=item.snapshot_id,
        evidence_chunk_id=evidence_link.evidence_chunk_id if evidence_link is not None else None,
        evidence_text_excerpt=evidence_link.evidence_text_excerpt if evidence_link is not None else None,
        anchor_type=evidence_link.anchor_type if evidence_link is not None else None,
        anchor_value=evidence_link.anchor_value if evidence_link is not None else None,
        page_no=evidence_link.page_no if evidence_link is not None else None,
        chunk_index=evidence_link.chunk_index if evidence_link is not None else None,
        field_metadata={
            "product_profile_id": profile.profile_id,
            "profile_source_ids": list(profile.source_ids),
        },
    )


def _profile_evidence_link(
    *,
    item: NormalizationInput,
    field: NormalizationExtractedField,
    evidence_link: NormalizationEvidenceLink | None,
) -> NormalizationEvidenceLink:
    assert evidence_link is not None
    return NormalizationEvidenceLink(
        field_name=field.field_name,
        candidate_value=_stringify(field.candidate_value),
        evidence_chunk_id=evidence_link.evidence_chunk_id,
        evidence_text_excerpt=evidence_link.evidence_text_excerpt,
        source_document_id=item.source_document_id,
        source_snapshot_id=item.snapshot_id,
        citation_confidence=min(0.9, evidence_link.citation_confidence),
        model_execution_id=evidence_link.model_execution_id,
        anchor_type=evidence_link.anchor_type,
        anchor_value=evidence_link.anchor_value,
        page_no=evidence_link.page_no,
        chunk_index=evidence_link.chunk_index,
    )


def _first_evidence_link(item: NormalizationInput) -> NormalizationEvidenceLink | None:
    for link in item.evidence_links:
        if link.evidence_chunk_id:
            return link
    return None


def _value_type(value: object) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "decimal"
    if isinstance(value, list | dict):
        return "json"
    return "string"


def _stringify(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _source_url_matches_token(source_url: str, token: str) -> bool:
    return source_url.rstrip("/") == token.rstrip("/")


def _load_product_profiles() -> tuple[ProductProfile, ...]:
    if not _PROFILE_PATH.exists():
        return ()
    payload = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
    profiles = []
    for item in payload.get("profiles", []):
        profile_id = str(item["profile_id"])
        product_name = str(item["product_name"])
        bank_code = str(item.get("bank_code") or "").strip().upper()
        product_type = str(item.get("product_type") or "").strip().lower()
        source_ids = tuple(str(value) for value in item.get("source_ids", []) if str(value).strip())
        source_url_tokens = tuple(str(value).lower().rstrip("/") for value in item.get("source_url_tokens", []) if str(value).strip())
        fields = {
            key: value
            for key, value in item.items()
            if key not in {"profile_id", "source_ids", "source_url_tokens", "product_name", "bank_code"}
        }
        profiles.append(
            ProductProfile(
                profile_id=profile_id,
                bank_codes=tuple(sorted(_bank_code_aliases(bank_code))) if bank_code else (),
                product_types=(product_type,) if product_type else (),
                source_ids=source_ids,
                source_url_tokens=source_url_tokens,
                product_name=product_name,
                fields=fields,
            )
        )
    return tuple(profiles)


def _bank_code_aliases(bank_code: str) -> set[str]:
    aliases = {bank_code}
    if bank_code == "SCOTIA":
        aliases.add("SCOTIABANK")
    if bank_code == "SCOTIABANK":
        aliases.add("SCOTIA")
    return aliases
