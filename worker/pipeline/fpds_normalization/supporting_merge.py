from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_PERCENT_RE = re.compile(r"(?<!\d)(\d{1,2}(?:\.\d{1,4})?)\s*%")
_BALANCE_LINE_RE = re.compile(r"^\$[0-9,]")
_WHITESPACE_RE = re.compile(r"\s+")
_MONTH_RE = re.compile(r"\b(month|months|monthly|next month)\b", re.IGNORECASE)

_TARGET_SUPPORT_SOURCE_IDS = {
    "BMO-SAV-002": ("BMO-SAV-006",),
    "BMO-SAV-003": ("BMO-SAV-006",),
    "BMO-SAV-004": ("BMO-SAV-006",),
    "CIBC-SAV-002": ("CIBC-SAV-004",),
    "CIBC-SAV-003": ("CIBC-SAV-004",),
    "TD-SAV-002": ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"),
    "TD-SAV-003": ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"),
    "TD-SAV-004": ("TD-SAV-005", "TD-SAV-007", "TD-SAV-008"),
    "SCOTIA-SAV-004": ("SCOTIA-SAV-006",),
}
_TARGET_MATCH_TERMS = {
    "BMO-SAV-002": ("savings amplifier account", "savings amplifier"),
    "BMO-SAV-003": ("savings builder account", "savings builder"),
    "BMO-SAV-004": ("premium rate savings account", "premium rate savings"),
    "CIBC-SAV-002": ("cibc eadvantage savings account", "eadvantage savings"),
    "CIBC-SAV-003": ("cibc us$ personal account", "cibc us personal account", "us$ personal account", "us personal account"),
    "TD-SAV-002": ("td every day savings account", "every day savings"),
    "TD-SAV-003": ("td epremium savings account", "epremium savings"),
    "TD-SAV-004": ("td growth savings account", "growth savings"),
    "SCOTIA-SAV-004": ("money master savings account", "money master savings"),
}


def supporting_source_ids_for_target(source_id: str) -> tuple[str, ...]:
    return _TARGET_SUPPORT_SOURCE_IDS.get(source_id, ())


def merge_supporting_artifacts(
    *,
    target_source_id: str,
    base_artifact: dict[str, object],
    supporting_artifacts: dict[str, dict[str, object]],
    missing_support_source_ids: list[str] | None = None,
) -> dict[str, object]:
    merged_artifact = {
        **base_artifact,
        "extracted_fields": [dict(item) for item in base_artifact.get("extracted_fields", [])],
        "evidence_links": [dict(item) for item in base_artifact.get("evidence_links", [])],
        "runtime_notes": list(base_artifact.get("runtime_notes", [])),
    }
    extracted_fields = merged_artifact["extracted_fields"]
    evidence_links = merged_artifact["evidence_links"]
    runtime_notes = merged_artifact["runtime_notes"]
    field_records = _field_record_map(extracted_fields)

    if missing_support_source_ids:
        runtime_notes.append(
            "Supporting-source merge skipped for missing extraction artifacts: "
            + ", ".join(sorted(dict.fromkeys(missing_support_source_ids)))
            + "."
        )

    for support_source_id, payload in supporting_artifacts.items():
        if support_source_id == "TD-SAV-005":
            supplement = _build_current_rate_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "TD-SAV-007":
            supplement = _build_fee_pdf_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "TD-SAV-008":
            supplement = _build_interest_pdf_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "SCOTIA-SAV-006":
            supplement = _build_scotia_rate_page_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "BMO-SAV-006":
            supplement = _build_bmo_rate_page_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        elif support_source_id == "CIBC-SAV-004":
            supplement = _build_cibc_rate_page_supplement(
                target_source_id=target_source_id,
                supporting_artifact=payload,
                existing_fields=field_records,
            )
        else:
            continue

        runtime_notes.extend(supplement["runtime_notes"])
        if not supplement["field_updates"]:
            continue

        for field_name, field_record in supplement["field_updates"].items():
            _upsert_field_record(extracted_fields, field_record)
            field_records[field_name] = field_record
        for field_name, link_record in supplement["evidence_updates"].items():
            _upsert_evidence_link(evidence_links, field_name=field_name, link_record=link_record)

    _cleanup_target_artifact(
        target_source_id=target_source_id,
        extracted_fields=extracted_fields,
        evidence_links=evidence_links,
        runtime_notes=runtime_notes,
    )
    return merged_artifact


def _build_current_rate_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if target_source_id not in _TARGET_MATCH_TERMS:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    terms = _TARGET_MATCH_TERMS[target_source_id]
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))

    rate_table_match = _find_product_matched_rate_table(target_source_id=target_source_id, matches=matches, terms=terms)
    if rate_table_match is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    rate_values = _extract_rate_values_from_match(target_source_id=target_source_id, match=rate_table_match)
    if not rate_values:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for field_name, candidate_value in rate_values.items():
        if field_name in existing_fields:
            continue
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type="decimal",
            match=rate_table_match,
            extraction_method="supporting_rate_table_merge",
            field_metadata={
                "supporting_source_id": "TD-SAV-005",
                "supporting_merge": True,
                "match_terms": list(terms),
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=rate_table_match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            "Supplemented missing savings rate fields from `TD-SAV-005` current-rate evidence using a product-matched supporting chunk."
        ],
    }


def _build_fee_pdf_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    match = _select_support_match(
        matches=matches,
        field_name="fee_waiver_condition",
        required_keywords=("refund the fee", "maintain the required daily closing balance"),
    )
    if match is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    existing_field = existing_fields.get("fee_waiver_condition")
    if existing_field is not None and not _should_replace_fee_waiver(existing_field=existing_field, existing_fields=existing_fields):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if _is_zero_fee_target(existing_fields):
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                f"Reviewed `TD-SAV-007` fee-governing language for `{target_source_id}` and left `fee_waiver_condition` unset because the target monthly fee is already $0."
            ],
        }

    candidate_value = _clean_fee_waiver_text(str(match.get("evidence_text_excerpt", "")))
    if not candidate_value:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": {
            "fee_waiver_condition": _build_support_field(
                field_name="fee_waiver_condition",
                candidate_value=candidate_value,
                value_type="string",
                match=match,
                extraction_method="supporting_fee_pdf_merge",
                field_metadata={
                    "supporting_source_id": "TD-SAV-007",
                    "supporting_merge": True,
                },
            )
        },
        "evidence_updates": {
            "fee_waiver_condition": _build_support_link(
                field_name="fee_waiver_condition",
                candidate_value=candidate_value,
                match=match,
            )
        },
        "runtime_notes": [
            "Supplemented `fee_waiver_condition` from `TD-SAV-007` fee-governing PDF when the target detail text was missing or noisy."
        ],
    }


def _build_interest_pdf_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}

    field_specs: dict[str, tuple[tuple[str, ...], callable]] = {
        "interest_calculation_method": (
            ("interest will be calculated", "daily closing balance"),
            _clean_interest_calculation_text,
        ),
        "interest_payment_frequency": (
            ("paid monthly", "monthly"),
            _clean_interest_payment_frequency,
        ),
    }
    if target_source_id == "TD-SAV-004":
        field_specs["tier_definition_text"] = (
            ("tier", "daily closing balance"),
            _clean_tier_definition_text,
        )

    for field_name, (keywords, builder) in field_specs.items():
        existing_field = existing_fields.get(field_name)
        if existing_field is not None and not _should_replace_with_pdf(field_name=field_name, existing_field=existing_field):
            continue
        match = _select_support_match(matches=matches, field_name=field_name, required_keywords=keywords)
        if match is None:
            continue
        candidate_value = builder(str(match.get("evidence_text_excerpt", "")))
        if not candidate_value:
            continue
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type="string",
            match=match,
            extraction_method="supporting_interest_pdf_merge",
            field_metadata={
                "supporting_source_id": "TD-SAV-008",
                "supporting_merge": True,
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            "Replaced noisy interest-rule fields with targeted `TD-SAV-008` governing PDF evidence where stronger canonical wording was available."
        ],
    }


def _build_scotia_rate_page_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if target_source_id != "SCOTIA-SAV-004":
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if all(field_name in existing_fields for field_name in ("standard_rate", "public_display_rate")):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    match = _find_scotia_money_master_rate_match(target_source_id=target_source_id, matches=matches)
    if match is None:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    rate_values = _extract_scotia_money_master_rate_values(str(match.get("evidence_text_excerpt", "")))
    if not rate_values:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for field_name, candidate_value in rate_values.items():
        if field_name in existing_fields:
            continue
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type="decimal",
            match=match,
            extraction_method="supporting_scotia_rate_page_merge",
            field_metadata={
                "supporting_source_id": "SCOTIA-SAV-006",
                "supporting_merge": True,
                "match_terms": list(_TARGET_MATCH_TERMS[target_source_id]),
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            "Supplemented missing Scotia Money Master savings rate fields from `SCOTIA-SAV-006` supporting rate evidence."
        ],
    }


def _build_bmo_rate_page_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if target_source_id not in {"BMO-SAV-002", "BMO-SAV-003", "BMO-SAV-004"}:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if all(field_name in existing_fields for field_name in ("standard_rate", "public_display_rate")):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    terms = _TARGET_MATCH_TERMS[target_source_id]
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    match = _find_product_matched_rate_table(target_source_id=target_source_id, matches=matches, terms=terms)
    if match is None:
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                "BMO savings support source `BMO-SAV-006` was available, but no product-matched rate evidence was found."
            ],
        }

    rate_values = _extract_single_rate_values(str(match.get("evidence_text_excerpt", "")))
    if not rate_values:
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                "BMO savings support source `BMO-SAV-006` matched the product, but the rate evidence did not contain a numeric percentage."
            ],
        }

    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for field_name, candidate_value in rate_values.items():
        if field_name in existing_fields:
            continue
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type="decimal",
            match=match,
            extraction_method="supporting_bmo_rate_page_merge",
            field_metadata={
                "supporting_source_id": "BMO-SAV-006",
                "supporting_merge": True,
                "match_terms": list(terms),
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            "Supplemented missing BMO savings rate fields from `BMO-SAV-006` supporting rate evidence."
        ],
    }


def _build_cibc_rate_page_supplement(
    *,
    target_source_id: str,
    supporting_artifact: dict[str, object],
    existing_fields: dict[str, dict[str, object]],
) -> dict[str, dict[str, dict[str, object]] | list[str]]:
    if target_source_id not in {"CIBC-SAV-002", "CIBC-SAV-003"}:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    if all(field_name in existing_fields for field_name in ("standard_rate", "public_display_rate")):
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    terms = _TARGET_MATCH_TERMS[target_source_id]
    matches = list(supporting_artifact.get("retrieval_result", {}).get("matches", []))
    match = _find_product_matched_rate_table(target_source_id=target_source_id, matches=matches, terms=terms)
    if match is None:
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                f"CIBC savings support source `CIBC-SAV-004` was available for `{target_source_id}`, but no product-matched rate evidence was found."
            ],
        }

    rate_values = _extract_single_rate_values(str(match.get("evidence_text_excerpt", "")))
    if not rate_values:
        return {
            "field_updates": {},
            "evidence_updates": {},
            "runtime_notes": [
                f"CIBC savings support source `CIBC-SAV-004` matched `{target_source_id}`, but the rate evidence did not contain a numeric percentage."
            ],
        }

    field_updates: dict[str, dict[str, object]] = {}
    evidence_updates: dict[str, dict[str, object]] = {}
    for field_name, candidate_value in rate_values.items():
        if field_name in existing_fields:
            continue
        field_updates[field_name] = _build_support_field(
            field_name=field_name,
            candidate_value=candidate_value,
            value_type="decimal",
            match=match,
            extraction_method="supporting_cibc_rate_page_merge",
            field_metadata={
                "supporting_source_id": "CIBC-SAV-004",
                "supporting_merge": True,
                "match_terms": list(terms),
            },
        )
        evidence_updates[field_name] = _build_support_link(
            field_name=field_name,
            candidate_value=candidate_value,
            match=match,
        )

    if not field_updates:
        return {"field_updates": {}, "evidence_updates": {}, "runtime_notes": []}

    return {
        "field_updates": field_updates,
        "evidence_updates": evidence_updates,
        "runtime_notes": [
            f"Supplemented missing CIBC savings rate fields for `{target_source_id}` from `CIBC-SAV-004` supporting rate evidence."
        ],
    }


def _find_product_matched_rate_table(
    *,
    target_source_id: str,
    matches: list[dict[str, object]],
    terms: tuple[str, ...],
) -> dict[str, object] | None:
    preferred_fields = {
        "BMO-SAV-002": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates"),
        "BMO-SAV-003": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates"),
        "BMO-SAV-004": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates"),
        "CIBC-SAV-002": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates"),
        "CIBC-SAV-003": ("standard_rate", "public_display_rate", "interest_rate_summary", "savings_account_rates", "tier_definition_text"),
        "TD-SAV-002": ("standard_rate", "public_display_rate", "rate_tiers", "tier_definition_text"),
        "TD-SAV-003": ("standard_rate", "public_display_rate", "rate_tiers", "tier_definition_text"),
        "TD-SAV-004": ("rate_tiers", "boosted_rate", "promotional_rate", "tier_definition_text"),
    }.get(target_source_id, ("standard_rate", "public_display_rate"))
    for field_name in preferred_fields:
        for match in matches:
            if str(match.get("field_name", "")) != field_name:
                continue
            haystack = _normalize_text(
                " ".join(
                    str(item or "")
                    for item in (
                        match.get("anchor_value"),
                        match.get("evidence_text_excerpt"),
                    )
                )
            )
            if any(term in haystack for term in terms):
                return match
    return None


def _find_scotia_money_master_rate_match(
    *,
    target_source_id: str,
    matches: list[dict[str, object]],
) -> dict[str, object] | None:
    terms = _TARGET_MATCH_TERMS.get(target_source_id, ())
    ranked: list[tuple[float, dict[str, object]]] = []
    for match in matches:
        haystack = _normalize_text(
            " ".join(
                str(item or "")
                for item in (
                    match.get("field_name"),
                    match.get("anchor_value"),
                    match.get("evidence_text_excerpt"),
                )
            )
        )
        if not any(term in haystack for term in terms):
            continue
        percentages = _extract_all_percentages(str(match.get("evidence_text_excerpt", "")))
        if not percentages:
            continue
        score = 0.0
        try:
            score = float(match.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        score += min(0.25, len(percentages) * 0.05)
        ranked.append((score, match))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _extract_rate_values_from_match(*, target_source_id: str, match: dict[str, object]) -> dict[str, str]:
    excerpt = str(match.get("evidence_text_excerpt", ""))
    if not excerpt.strip():
        return {}
    if target_source_id == "TD-SAV-004":
        return _extract_growth_rate_values(excerpt)
    return _extract_single_rate_values(excerpt)


def _extract_single_rate_values(excerpt: str) -> dict[str, str]:
    percentages = _extract_all_percentages(excerpt)
    if not percentages:
        return {}
    max_rate = max(percentages)
    normalized = _format_decimal(max_rate)
    return {
        "standard_rate": normalized,
        "public_display_rate": normalized,
    }


def _extract_growth_rate_values(excerpt: str) -> dict[str, str]:
    boosted_rates: list[Decimal] = []
    standard_rates: list[Decimal] = []
    lines = [line.strip() for line in excerpt.splitlines() if line.strip()]
    index = 0
    while index < len(lines):
        line = lines[index]
        if not _looks_like_balance_line(line):
            index += 1
            continue
        rate_lines: list[Decimal] = []
        next_index = index + 1
        while next_index < len(lines) and not _looks_like_balance_line(lines[next_index]):
            rate = _extract_first_percentage(lines[next_index])
            if rate is not None:
                rate_lines.append(rate)
            next_index += 1
        if rate_lines:
            boosted_rates.append(rate_lines[0])
            standard_rates.append(rate_lines[1] if len(rate_lines) > 1 else rate_lines[0])
        index = next_index

    if not boosted_rates:
        percentages = _extract_all_percentages(excerpt)
        if not percentages:
            return {}
        boosted_rates = list(percentages)
        standard_rates = list(percentages)

    boosted_rate = max(boosted_rates)
    standard_rate = max(standard_rates) if standard_rates else boosted_rate
    return {
        "standard_rate": _format_decimal(standard_rate),
        "public_display_rate": _format_decimal(boosted_rate),
        "promotional_rate": _format_decimal(boosted_rate),
    }


def _extract_scotia_money_master_rate_values(excerpt: str) -> dict[str, str]:
    percentages = _extract_all_percentages(excerpt)
    if not percentages:
        return {}

    unique_percentages = sorted(set(percentages))
    standard_rate = min(unique_percentages)
    public_display_rate = max(unique_percentages)
    return {
        "standard_rate": _format_decimal(standard_rate),
        "public_display_rate": _format_decimal(public_display_rate),
    }


def _extract_all_percentages(excerpt: str) -> list[Decimal]:
    values: list[Decimal] = []
    for match in _PERCENT_RE.finditer(excerpt):
        decimal_value = _to_decimal(match.group(1))
        if decimal_value is not None:
            values.append(decimal_value)
    return values


def _extract_first_percentage(line: str) -> Decimal | None:
    match = _PERCENT_RE.search(line)
    if match is None:
        return None
    return _to_decimal(match.group(1))


def _to_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _format_decimal(value: Decimal) -> str:
    return f"{value:.2f}"


def _supplement_confidence(match: dict[str, object]) -> float:
    raw = match.get("score", 0.55)
    try:
        score = float(raw)
    except (TypeError, ValueError):
        score = 0.55
    return round(min(0.89, max(0.72, score)), 4)


def _looks_like_balance_line(line: str) -> bool:
    return bool(_BALANCE_LINE_RE.search(line.strip()))


def _normalize_text(value: str) -> str:
    lowered = value.lower().replace("??, ", " ")
    lowered = lowered.replace("-", " ").replace("_", " ")
    lowered = lowered.replace("?", " ")
    return _WHITESPACE_RE.sub(" ", lowered).strip()


def _field_record_map(extracted_fields: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for item in extracted_fields:
        field_name = str(item.get("field_name", ""))
        if field_name and field_name not in records:
            records[field_name] = item
    return records


def _build_support_field(
    *,
    field_name: str,
    candidate_value: object,
    value_type: str,
    match: dict[str, object],
    extraction_method: str,
    field_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "field_name": field_name,
        "candidate_value": candidate_value,
        "value_type": value_type,
        "confidence": _supplement_confidence(match),
        "extraction_method": extraction_method,
        "source_document_id": match["source_document_id"],
        "source_snapshot_id": match["source_snapshot_id"],
        "evidence_chunk_id": match["evidence_chunk_id"],
        "evidence_text_excerpt": match["evidence_text_excerpt"],
        "anchor_type": match["anchor_type"],
        "anchor_value": match["anchor_value"],
        "page_no": match["page_no"],
        "chunk_index": match["chunk_index"],
        "field_metadata": field_metadata,
    }


def _build_support_link(
    *,
    field_name: str,
    candidate_value: object,
    match: dict[str, object],
) -> dict[str, object]:
    return {
        "field_name": field_name,
        "candidate_value": str(candidate_value),
        "evidence_chunk_id": match["evidence_chunk_id"],
        "evidence_text_excerpt": match["evidence_text_excerpt"],
        "source_document_id": match["source_document_id"],
        "source_snapshot_id": match["source_snapshot_id"],
        "citation_confidence": _supplement_confidence(match),
        "model_execution_id": None,
        "anchor_type": match["anchor_type"],
        "anchor_value": match["anchor_value"],
        "page_no": match["page_no"],
        "chunk_index": match["chunk_index"],
    }


def _upsert_field_record(extracted_fields: list[dict[str, object]], field_record: dict[str, object]) -> None:
    field_name = str(field_record["field_name"])
    for index, existing in enumerate(extracted_fields):
        if str(existing.get("field_name", "")) != field_name:
            continue
        extracted_fields[index] = field_record
        return
    extracted_fields.append(field_record)


def _upsert_evidence_link(
    evidence_links: list[dict[str, object]],
    *,
    field_name: str,
    link_record: dict[str, object],
) -> None:
    for index in range(len(evidence_links) - 1, -1, -1):
        if str(evidence_links[index].get("field_name", "")) == field_name:
            evidence_links.pop(index)
    evidence_links.append(link_record)


def _remove_field(extracted_fields: list[dict[str, object]], evidence_links: list[dict[str, object]], field_name: str) -> None:
    for index in range(len(extracted_fields) - 1, -1, -1):
        if str(extracted_fields[index].get("field_name", "")) == field_name:
            extracted_fields.pop(index)
    for index in range(len(evidence_links) - 1, -1, -1):
        if str(evidence_links[index].get("field_name", "")) == field_name:
            evidence_links.pop(index)


def _cleanup_target_artifact(
    *,
    target_source_id: str,
    extracted_fields: list[dict[str, object]],
    evidence_links: list[dict[str, object]],
    runtime_notes: list[str],
) -> None:
    fields = _field_record_map(extracted_fields)
    fee_waiver_field = fields.get("fee_waiver_condition")
    if fee_waiver_field is not None and _is_zero_fee_target(fields) and _looks_like_fee_table_text(str(fee_waiver_field.get("candidate_value", ""))):
        _remove_field(extracted_fields, evidence_links, "fee_waiver_condition")
        runtime_notes.append(
            f"Suppressed noisy `fee_waiver_condition` for `{target_source_id}` because the product monthly fee is already $0 and no product-specific waiver rule should be persisted."
        )
        fields = _field_record_map(extracted_fields)

    for noisy_field_name in ("notes", "eligibility_text", "tier_definition_text"):
        field = fields.get(noisy_field_name)
        if field is None:
            continue
        candidate_value = str(field.get("candidate_value", ""))
        if not _looks_like_noisy_text(candidate_value):
            continue
        _remove_field(extracted_fields, evidence_links, noisy_field_name)
        runtime_notes.append(f"Suppressed noisy `{noisy_field_name}` text before normalization.")

    promotional_field = _field_record_map(extracted_fields).get("promotional_period_text")
    if promotional_field is not None:
        promotional_text = str(promotional_field.get("candidate_value", ""))
        if not _is_promotional_period_text(promotional_text):
            _remove_field(extracted_fields, evidence_links, "promotional_period_text")
            runtime_notes.append("Suppressed `promotional_period_text` because the extracted text described marketing copy rather than a bounded promotional period.")

    if target_source_id == "TD-SAV-004":
        _apply_growth_qualification_cleanup(
            extracted_fields=extracted_fields,
            evidence_links=evidence_links,
            runtime_notes=runtime_notes,
        )


def _apply_growth_qualification_cleanup(
    *,
    extracted_fields: list[dict[str, object]],
    evidence_links: list[dict[str, object]],
    runtime_notes: list[str],
) -> None:
    fields = _field_record_map(extracted_fields)
    boosted_field = fields.get("boosted_rate_eligibility")
    if boosted_field is None:
        return

    evidence_text = str(boosted_field.get("evidence_text_excerpt") or boosted_field.get("candidate_value") or "")
    if "qualify" not in evidence_text.lower():
        return

    eligibility_summary = _summarize_growth_eligibility(evidence_text)
    if eligibility_summary:
        eligibility_record = dict(boosted_field)
        eligibility_record["field_name"] = "eligibility_text"
        eligibility_record["candidate_value"] = eligibility_summary
        eligibility_record["extraction_method"] = "growth_qualification_cleanup"
        eligibility_record["field_metadata"] = {
            **dict(boosted_field.get("field_metadata", {})),
            "cleanup": "growth_eligibility_split",
        }
        _upsert_field_record(extracted_fields, eligibility_record)
        _upsert_evidence_link(
            evidence_links,
            field_name="eligibility_text",
            link_record={
                "field_name": "eligibility_text",
                "candidate_value": eligibility_summary,
                "evidence_chunk_id": boosted_field["evidence_chunk_id"],
                "evidence_text_excerpt": boosted_field["evidence_text_excerpt"],
                "source_document_id": boosted_field["source_document_id"],
                "source_snapshot_id": boosted_field["source_snapshot_id"],
                "citation_confidence": boosted_field["confidence"],
                "model_execution_id": None,
                "anchor_type": boosted_field["anchor_type"],
                "anchor_value": boosted_field["anchor_value"],
                "page_no": boosted_field["page_no"],
                "chunk_index": boosted_field["chunk_index"],
            },
        )

    boosted_summary = _summarize_growth_boosted_rate_eligibility(evidence_text)
    if boosted_summary:
        boosted_record = dict(boosted_field)
        boosted_record["candidate_value"] = boosted_summary
        boosted_record["extraction_method"] = "growth_qualification_cleanup"
        boosted_record["field_metadata"] = {
            **dict(boosted_field.get("field_metadata", {})),
            "cleanup": "growth_eligibility_split",
        }
        _upsert_field_record(extracted_fields, boosted_record)
        _upsert_evidence_link(
            evidence_links,
            field_name="boosted_rate_eligibility",
            link_record={
                "field_name": "boosted_rate_eligibility",
                "candidate_value": boosted_summary,
                "evidence_chunk_id": boosted_field["evidence_chunk_id"],
                "evidence_text_excerpt": boosted_field["evidence_text_excerpt"],
                "source_document_id": boosted_field["source_document_id"],
                "source_snapshot_id": boosted_field["source_snapshot_id"],
                "citation_confidence": boosted_field["confidence"],
                "model_execution_id": None,
                "anchor_type": boosted_field["anchor_type"],
                "anchor_value": boosted_field["anchor_value"],
                "page_no": boosted_field["page_no"],
                "chunk_index": boosted_field["chunk_index"],
            },
        )

    promotional_summary = _summarize_growth_promotional_period(evidence_text)
    if promotional_summary:
        promotional_record = dict(boosted_field)
        promotional_record["field_name"] = "promotional_period_text"
        promotional_record["candidate_value"] = promotional_summary
        promotional_record["extraction_method"] = "growth_qualification_cleanup"
        promotional_record["field_metadata"] = {
            **dict(boosted_field.get("field_metadata", {})),
            "cleanup": "growth_eligibility_split",
        }
        _upsert_field_record(extracted_fields, promotional_record)
        _upsert_evidence_link(
            evidence_links,
            field_name="promotional_period_text",
            link_record={
                "field_name": "promotional_period_text",
                "candidate_value": promotional_summary,
                "evidence_chunk_id": boosted_field["evidence_chunk_id"],
                "evidence_text_excerpt": boosted_field["evidence_text_excerpt"],
                "source_document_id": boosted_field["source_document_id"],
                "source_snapshot_id": boosted_field["source_snapshot_id"],
                "citation_confidence": boosted_field["confidence"],
                "model_execution_id": None,
                "anchor_type": boosted_field["anchor_type"],
                "anchor_value": boosted_field["anchor_value"],
                "page_no": boosted_field["page_no"],
                "chunk_index": boosted_field["chunk_index"],
            },
        )

    runtime_notes.append(
        "Split TD Growth boosted-rate qualification into cleaner `eligibility_text`, `boosted_rate_eligibility`, and `promotional_period_text` values."
    )


def _select_support_match(
    *,
    matches: list[dict[str, object]],
    field_name: str,
    required_keywords: tuple[str, ...],
) -> dict[str, object] | None:
    ranked: list[tuple[float, dict[str, object]]] = []
    for match in matches:
        if str(match.get("field_name", "")) != field_name:
            continue
        excerpt = str(match.get("evidence_text_excerpt", ""))
        lowered = excerpt.lower()
        if not any(keyword in lowered for keyword in required_keywords):
            continue
        score = 0.0
        try:
            score = float(match.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        score += sum(0.05 for keyword in required_keywords if keyword in lowered)
        ranked.append((score, match))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _should_replace_with_pdf(*, field_name: str, existing_field: dict[str, object]) -> bool:
    candidate_value = str(existing_field.get("candidate_value", ""))
    if field_name == "interest_payment_frequency":
        return candidate_value.strip().lower() not in {"monthly", "quarterly", "weekly", "annually", "semi-annually", "daily"}
    if field_name == "interest_calculation_method":
        return _looks_like_noisy_text(candidate_value) or "how our interest is calculated (pdf)" in candidate_value.lower()
    if field_name == "tier_definition_text":
        return _looks_like_noisy_text(candidate_value) or not any(token in candidate_value.lower() for token in ("tier", "balance", "%"))
    return False


def _should_replace_fee_waiver(*, existing_field: dict[str, object], existing_fields: dict[str, dict[str, object]]) -> bool:
    candidate_value = str(existing_field.get("candidate_value", ""))
    if _is_zero_fee_target(existing_fields):
        return True
    return _looks_like_noisy_text(candidate_value) or _looks_like_fee_table_text(candidate_value)


def _looks_like_noisy_text(value: str) -> bool:
    lowered = _normalize_text(value).lower()
    if not lowered:
        return True
    noisy_markers = (
        "additional account details & terms information",
        "how our interest is calculated (pdf)",
        "account and other related service fees (pdf)",
        "bank accounts and fees at a glance",
        "whether you're saving for the future",
        "general list of services",
    )
    return any(marker in lowered for marker in noisy_markers)


def _looks_like_fee_table_text(value: str) -> bool:
    lowered = _normalize_text(value).lower()
    table_markers = (
        "account fees monthly fee $0",
        "transaction fee",
        "transactions included per month",
        "additional transactions",
        "foreign atm fee",
        "free transfers to your other td accounts",
    )
    return any(marker in lowered for marker in table_markers)


def _is_zero_fee_target(existing_fields: dict[str, dict[str, object]]) -> bool:
    for field_name in ("monthly_fee", "public_display_fee"):
        field = existing_fields.get(field_name)
        if field is None:
            continue
        normalized = str(field.get("candidate_value", "")).strip()
        if normalized in {"0", "0.0", "0.00"}:
            return True
    return False


def _is_promotional_period_text(value: str) -> bool:
    lowered = _normalize_text(value).lower()
    if not lowered:
        return False
    if "next month" in lowered:
        return True
    if any(token in lowered for token in ("introductory", "promotion", "promotional", "bonus rate", "offer ends", "offer period")):
        return True
    return bool(_MONTH_RE.search(lowered) and any(token in lowered for token in ("for", "until", "next", "introductory", "promotion")))


def _clean_fee_waiver_text(excerpt: str) -> str | None:
    normalized = _normalize_text(excerpt)
    if "refund the fee" not in normalized.lower():
        return None
    if "maintain the required daily closing balance" in normalized.lower():
        return "The monthly fee is refunded when you maintain the required daily closing balance for the full month."
    return "The monthly fee may be refunded when the required balance conditions are met."


def _clean_interest_calculation_text(excerpt: str) -> str | None:
    normalized = _normalize_text(excerpt)
    lowered = normalized.lower()
    if "daily closing balance" in lowered and "interest" in lowered:
        return "Interest is calculated on the daily closing balance."
    if "interest will be calculated" in lowered:
        return _extract_sentence(normalized, ("interest will be calculated", "daily closing balance"))
    return None


def _clean_interest_payment_frequency(excerpt: str) -> str | None:
    lowered = _normalize_text(excerpt).lower()
    if "monthly" in lowered:
        return "monthly"
    if "quarterly" in lowered:
        return "quarterly"
    if "annually" in lowered or "yearly" in lowered:
        return "annually"
    return None


def _clean_tier_definition_text(excerpt: str) -> str | None:
    normalized = _normalize_text(excerpt)
    lowered = normalized.lower()
    if "daily closing balance" in lowered and "tier" in lowered:
        return _extract_sentence(normalized, ("daily closing balance", "tier")) or normalized[:220]
    if "tier" in lowered and "balance" in lowered:
        return _extract_sentence(normalized, ("tier", "balance")) or normalized[:220]
    return None


def _summarize_growth_eligibility(excerpt: str) -> str | None:
    lowered = excerpt.lower()
    has_chequing = "maintain an eligible td chequing account" in lowered
    has_transactions = "complete at least 2 out of the 3 qualifying monthly transactions" in lowered
    if has_chequing and has_transactions:
        return "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions."
    return None


def _summarize_growth_boosted_rate_eligibility(excerpt: str) -> str | None:
    summary = _summarize_growth_eligibility(excerpt)
    if summary is None:
        return None
    if "next month" in excerpt.lower():
        return summary[:-1] + " to earn the Boosted rate for the next month."
    return summary[:-1] + " to earn the Boosted rate."


def _summarize_growth_promotional_period(excerpt: str) -> str | None:
    if "next month" not in excerpt.lower():
        return None
    return "Meeting the qualification criteria earns the Boosted rate for the next month."


def _extract_sentence(value: str, keywords: tuple[str, ...]) -> str | None:
    for sentence in re.split(r"(?<=[.!?])\s+", value):
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            return sentence.strip()
    return None
