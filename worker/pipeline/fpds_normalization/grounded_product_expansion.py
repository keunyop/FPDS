from __future__ import annotations

from hashlib import sha256
from typing import Any

from .models import NormalizationEvidenceLink, NormalizationExtractedField, NormalizationInput

_VARIANT_FIELD_TYPES = {
    "credit-card": {
        "product_name": "string",
        "annual_fee": "decimal",
        "purchase_interest_rate": "decimal",
    },
    "line-of-credit": {
        "product_name": "string",
        "interest_rate_summary": "string",
        "credit_limit_text": "string",
        "minimum_payment_text": "string",
        "security_requirement": "string",
        "secured_flag": "boolean",
    },
}
_GROUNDING_METHODS = {
    "credit-card": "deterministic_sibling_product_block",
    "line-of-credit": "deterministic_sibling_lending_table",
}


def expand_grounded_product_inputs(item: NormalizationInput) -> list[NormalizationInput]:
    """Expand complete sibling products captured from one official detail page."""

    product_type = _product_type_for_item(item)
    if product_type not in _VARIANT_FIELD_TYPES:
        return []
    product_name_field = next(
        (field for field in item.extracted_fields if field.field_name == "product_name"),
        None,
    )
    if product_name_field is None or not isinstance(product_name_field.field_metadata, dict):
        return []
    raw_variants = product_name_field.field_metadata.get("grounded_product_variants")
    if not isinstance(raw_variants, list) or len(raw_variants) < 2:
        return []
    variants = [
        variant
        for value in raw_variants
        if (variant := _valid_variant(value, product_type=product_type)) is not None
    ]
    if len(variants) < 2:
        return []
    return [
        _build_variant_input(
            item=item,
            variant=variant,
            product_type=product_type,
            variant_count=len(variants),
        )
        for variant in variants
    ]


def _valid_variant(value: object, *, product_type: str) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    required_fields = (
        ("product_name", "annual_fee", "purchase_interest_rate")
        if product_type == "credit-card"
        else ("product_name", "interest_rate_summary", "credit_limit_text", "minimum_payment_text")
    )
    if any(value.get(key) in {None, ""} for key in (*required_fields, "evidence_chunk_id", "evidence_text_excerpt")):
        return None
    if product_type == "line-of-credit" and all(
        value.get(key) in {None, ""} for key in ("security_requirement", "secured_flag")
    ):
        return None
    metadata = value.get("field_metadata")
    if not isinstance(metadata, dict):
        return None
    if not (
        metadata.get("official_grounding_contract_version") == "collection-official-grounding-v2"
        and metadata.get("official_verification_status") == "match"
        and metadata.get("official_grounding_method") == _GROUNDING_METHODS[product_type]
        and metadata.get("evidence_quote")
        and metadata.get("official_web_sources")
    ):
        return None
    return dict(value)


def _build_variant_input(
    *,
    item: NormalizationInput,
    variant: dict[str, Any],
    product_type: str,
    variant_count: int,
) -> NormalizationInput:
    product_name = str(variant["product_name"]).strip()
    candidate_key = "grounded-" + product_type + "-" + sha256(product_name.casefold().encode("utf-8")).hexdigest()[:16]
    variant_field_types = _VARIANT_FIELD_TYPES[product_type]
    variant_field_names = set(variant_field_types)
    variant_fields = [
        _variant_field(item=item, variant=variant, field_name=field_name, value_type=value_type)
        for field_name, value_type in variant_field_types.items()
        if field_name in variant and variant[field_name] not in {None, ""}
    ]
    variant_links = [
        _variant_evidence_link(item=item, variant=variant, field=field)
        for field in variant_fields
    ]
    return NormalizationInput(
        **{
            **item.__dict__,
            "candidate_key": candidate_key,
            "source_metadata": _resolved_variant_source_metadata(
                item=item,
                product_name=product_name,
                variant_count=variant_count,
            ),
            "extracted_fields": [
                *[field for field in item.extracted_fields if field.field_name not in variant_field_names],
                *variant_fields,
            ],
            "evidence_links": [
                *[link for link in item.evidence_links if link.field_name not in variant_field_names],
                *variant_links,
            ],
            "runtime_notes": [
                *item.runtime_notes,
                f"Expanded grounded sibling {product_type} product from official evidence: {product_name}.",
            ],
        }
    )


def _resolved_variant_source_metadata(
    *,
    item: NormalizationInput,
    product_name: str,
    variant_count: int,
) -> dict[str, object]:
    metadata = dict(item.source_metadata)
    discovery = metadata.get("discovery_metadata")
    if isinstance(discovery, dict):
        resolved_discovery = dict(discovery)
        for reason_key in ("selection_reason_codes", "page_evidence_reason_codes"):
            resolved_reasons = [
                str(code)
                for code in discovery.get(reason_key, [])
                if str(code).strip().lower() != "multi_product_family_overview"
            ]
            if reason_key == "selection_reason_codes":
                resolved_reasons.append("grounded_product_variants_resolved")
            resolved_discovery[reason_key] = list(dict.fromkeys(resolved_reasons))
        metadata["discovery_metadata"] = resolved_discovery
    metadata.update(
        {
            "product_name": product_name,
            "grounded_sibling_product_count": variant_count,
        }
    )
    return metadata


def _variant_field(
    *,
    item: NormalizationInput,
    variant: dict[str, Any],
    field_name: str,
    value_type: str,
) -> NormalizationExtractedField:
    return NormalizationExtractedField(
        field_name=field_name,
        candidate_value=variant[field_name],
        value_type=value_type,
        confidence=0.94,
        extraction_method="deterministic_sibling_product_block",
        source_document_id=item.source_document_id,
        source_snapshot_id=item.snapshot_id,
        evidence_chunk_id=str(variant["evidence_chunk_id"]),
        evidence_text_excerpt=str(variant["evidence_text_excerpt"]),
        anchor_type=str(variant.get("anchor_type") or "") or None,
        anchor_value=str(variant.get("anchor_value") or "") or None,
        page_no=_optional_int(variant.get("page_no")),
        chunk_index=_optional_int(variant.get("chunk_index")),
        field_metadata=dict(variant["field_metadata"]),
    )


def _variant_evidence_link(
    *,
    item: NormalizationInput,
    variant: dict[str, Any],
    field: NormalizationExtractedField,
) -> NormalizationEvidenceLink:
    return NormalizationEvidenceLink(
        field_name=field.field_name,
        candidate_value=str(field.candidate_value),
        evidence_chunk_id=str(variant["evidence_chunk_id"]),
        evidence_text_excerpt=str(variant["evidence_text_excerpt"]),
        source_document_id=item.source_document_id,
        source_snapshot_id=item.snapshot_id,
        citation_confidence=field.confidence,
        model_execution_id=item.extraction_model_execution_id,
        anchor_type=field.anchor_type,
        anchor_value=field.anchor_value,
        page_no=field.page_no,
        chunk_index=field.chunk_index,
    )


def _product_type_for_item(item: NormalizationInput) -> str:
    return str(
        item.source_metadata.get("product_type")
        or item.schema_context.get("product_type")
        or ""
    ).strip().lower()


def _optional_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
