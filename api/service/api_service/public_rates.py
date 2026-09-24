"""Interpret approved Public rate fields without turning components into totals.

This module never looks up a benchmark or computes a rate from a formula.
Qualified source text takes precedence over a legacy scalar projection.
"""
from __future__ import annotations

import re
from typing import Any

from api_service.public_common import serialize_decimal

_NUMBER = r"(?:\d{1,3}(?:\.\d+)?|\.\d+)"
_PERCENT = re.compile(rf"(?<![\d.])({_NUMBER})\s*%")
_PLAIN = re.compile(rf"^\s*({_NUMBER})\s*%?\s*$")
_RATE = re.compile(r"\b(?:APR|APY|rate|rates|per annum|interest)\b", re.I)
_REFERENCE = re.compile(r"\b(?:prime|SOFR|SONIA|EURIBOR|LIBOR|(?:reference|index|base|benchmark)(?:\s+\w+){0,2}\s+rate)\b", re.I)
_SPREAD = re.compile(rf"(?:plus|minus|[+−–-])\s*(?:a\s+)?(?:margin\s+of\s+)?{_NUMBER}\s*%", re.I)
_RANGE = re.compile(rf"{_NUMBER}\s*%?\s*(?:APR|APY)?\s*(?:to|through|and|[-–—])\s*{_NUMBER}\s*%", re.I)
_PROMOTION = re.compile(r"\b(?:intro(?:ductory)?|promo(?:tion(?:al)?)?|special offer|welcome rate|bonus rate|limited.time)\b|\bfirst\s+\d+\s+(?:months?|days?|billing cycles?)\b", re.I)
_CONDITIONAL = re.compile(
    r"\b(?:discount(?:ed|s)?|as low as|up to|starting (?:at|from)|representative|example|sample|assum(?:es|ing|ption)|"
    r"creditworthiness|credit score|credit profile|excellent credit|qualif(?:y|ying|ied)|"
    r"stress test|LTV|CLTV|loan.to.value|down payment|points?|rate cap|maximum APR|"
    r"automatic payments?|autopay|tiered|boosted|preferential|conditional|depending|depends|"
    r"subject to|based on|if|when|provided that|minimum balance|balance.*or more)\b", re.I)
_NON_RATE = re.compile(r"\b(?:stress test|qualifying rate|discount|down payment|LTV|CLTV|points?|finance charges?|origination fees?|cash\s*back|cash advances?|balance transfers?|rate cap|maximum APR)\b", re.I)


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    number = serialize_decimal(value)
    return number if number is not None and 0 <= number <= 100 else None


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _result(kind: str, text: str | None, rate: float | None = None) -> dict[str, Any]:
    return {"kind": kind, "comparable_rate": rate, "source_text": text}


def interpret_rate_text(value: Any) -> dict[str, Any]:
    """A range, component, promotion or assumption is never a scalar candidate."""
    text = _text(value)
    if text is None:
        rate = _number(value)
        return _result("absolute" if rate is not None else "unknown", None, rate)
    normalized = " ".join(text.replace("**", "").replace("__", "").split())
    plain = _PLAIN.fullmatch(normalized)
    if plain:
        rate = _number(plain.group(1))
        return _result("absolute" if rate is not None else "unknown", text, rate)
    if _PROMOTION.search(normalized) or re.search(r"%.*\bfor\s+(?:the\s+)?(?:first\s+)?\d+\s+(?:months?|days?|billing cycles?)\b.*\b(?:then|after)\b", normalized, re.I):
        return _result("promotional", text)
    # Reference formulas can contain ranges of margins and a dated prime value.
    # None of those percentages establishes a comparable all-in rate.
    if re.search(r"stress test|qualifying rate", normalized, re.I):
        return _result("conditional", text)
    reference = _REFERENCE.search(normalized)
    rate_range = _RANGE.search(normalized)
    if reference and (rate_range is None or (_SPREAD.search(normalized) and reference.start() < rate_range.start())):
        return _result("reference", text)
    if rate_range and _RATE.search(normalized) and not re.search(r"stress test|qualifying rate", normalized, re.I):
        return _result("range", text)
    if _SPREAD.search(normalized) or re.search(r"\b(?:spread|margin|add-on)\b", normalized, re.I):
        return _result("reference", text)
    if _CONDITIONAL.search(normalized):
        return _result("conditional", text)
    if _NON_RATE.search(normalized):
        return _result("unknown", text)
    values = {_number(match.group(1)) for match in _PERCENT.finditer(normalized)}
    values.discard(None)
    if _RATE.search(normalized) and len(values) == 1:
        return _result("absolute", text, next(iter(values)))
    # Several explicit rates may describe distinct terms/scenarios or rate/APR.
    # Do not choose the lowest, or turn discrete scenarios into a numeric range.
    return _result("conditional" if len(values) > 1 else "unknown", text)


def public_rate(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("refresh_metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    if row.get("product_type") == "gic" and re.search(
        r"\b(?:indexed|index.linked|market.linked|equity.linked|ActionGIC|step.up|step.rate|escalating)\b",
        str(row.get("product_name") or "") + " " + str(metadata.get("interest_rate_summary") or ""), re.I
    ):
        return _result("conditional", _text(metadata.get("interest_rate_summary")) or _text(row.get("product_name")))
    card = row.get("product_type") == "credit-card"
    keys = ("purchase_interest_rate_summary", "purchase_interest_rate") if card else (
        "interest_rate_summary", "mortgage_rate", "interest_rate")
    texts = list(dict.fromkeys(text for key in keys if (text := _text(metadata.get(key)))))
    parsed = [interpret_rate_text(text) for text in texts]

    # Marketing descriptions are not a rate source. Only rate-specific
    # qualifiers can veto a scalar; deposit insurance percentages, for example,
    # cannot. An explicit conflicting interest rate is also unsafe to compare.
    description = _text(metadata.get("description_short"))
    if description and _RATE.search(description):
        qualification_text = re.sub(
            r"eligible for (?:CDIC|FDIC|deposit insurance)(?: coverage)?", "insured", description, flags=re.I)
        qualifies_rate = re.search(
            r"(?:tiered|boosted|preferential|conditional)\W{0,5}(?:interest\s+)?rates?"
            r"|(?:interest|rate|APY|APR).{0,80}(?:autopay|discount|eligible|new clients|new customers)"
            r"|interest.{0,60}when.{0,50}balance", qualification_text, re.I)
        if _REFERENCE.search(description) or _PROMOTION.search(description) or qualifies_rate:
            description_rate = interpret_rate_text(description)
            parsed.append(description_rate)
            if description not in texts:
                texts.append(description)
        elif _PERCENT.search(description):
            described = interpret_rate_text(description)
            stored = _number(row.get("public_display_rate"))
            if described["kind"] == "absolute" and stored is not None and described["comparable_rate"] != stored:
                parsed.append(_result("conditional", description))
                texts.append(description)
    qualified_texts = [text for text in texts if not _PLAIN.fullmatch(text)]
    source_text = "\n".join(qualified_texts or texts) or None
    for kind in ("promotional", "reference", "range", "conditional", "unknown"):
        if any(item["kind"] == kind for item in parsed):
            return _result(kind, source_text)

    table = metadata.get("term_rate_table")
    if isinstance(table, list):
        table_rates = {_number(item.get("rate")) for item in table if isinstance(item, dict)} - {None}
        if len(table_rates) > 1:
            return _result("range", source_text or "; ".join(
                f"{item.get('term_label') or str(item.get('term_length_days') or '')}: {item['rate']}%"
                + (f" ({item['notes']})" if item.get('notes') else "")
                for item in table if isinstance(item, dict) and _number(item.get("rate")) is not None
            ))
        for item in table:
            if isinstance(item, dict) and (notes := _text(item.get("notes"))):
                if _PROMOTION.search(notes) or _CONDITIONAL.search(notes) or _REFERENCE.search(notes):
                    return _result(interpret_rate_text(notes)["kind"], source_text or notes)

    values = {item["comparable_rate"] for item in parsed if item["comparable_rate"] is not None}
    stored = _number(metadata.get("purchase_interest_rate")) if card else None
    if stored is None:
        stored = _number(row.get("public_display_rate"))
    if stored is not None:
        values.add(stored)
    if row.get("product_family") == "deposit":
        standard = _number(metadata.get("standard_rate"))
        if standard is not None:
            values.add(standard)
            if stored is not None and standard != stored and not source_text:
                source_text = f"Standard rate: {standard:g}%; other published rate: {stored:g}%."
    # Contradictory approved scalar/summary values require review, not min().
    if len(values) > 1:
        return _result("conditional", source_text)
    if values:
        return _result("absolute", source_text, next(iter(values)))
    return _result("unknown", source_text)


def comparable_rate(row: dict[str, Any]) -> float | None:
    return public_rate(row)["comparable_rate"]
