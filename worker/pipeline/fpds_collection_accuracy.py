"""Fail-closed, shared collection acceptance. No human decisions or model scores."""
from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from hashlib import sha256
import json
import re
from urllib.parse import urlsplit, urlunsplit

from worker.pipeline.fpds_field_contract import field_contract, value_matches_contract
from worker.pipeline.fpds_approval_policy import comparison_quality
from worker.pipeline.fpds_rate_safety import rate_component_only

ACCURACY_VERSION = "collection-accuracy-2026-09-30"
RECEIPT_KEY = "_collection_accuracy"
# Registry/workflow metadata is not a collected financial attribute.
CONTEXT_FIELDS = {"status", "last_verified_at", "bank_name", "subtype_code"}
CURRENCY_PATTERNS = {"CAD": r"\bCAD\b|Canadian dollars?", "USD": r"\bUSD\b|U\.?S\.? dollars?", "EUR": r"\bEUR\b|euros?", "GBP": r"\bGBP\b|pounds? sterling"}
IDENTITY_FIELDS = ("country_code", "bank_code", "product_type", "product_name", "currency")
_NUMBER = r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\w.])"


def text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def exact_quote(quote: object, excerpt: object) -> bool:
    q = text(quote)
    return bool(q and "..." not in q and "…" not in q and q.casefold() in text(excerpt).casefold())


def _numbers(value: str) -> list[Decimal]:
    return [Decimal(m.group().replace(",", "")) for m in re.finditer(_NUMBER, value)]


def quote_supports_value(field_name: str, value: object, quote: str) -> bool:
    """Require field meaning as well as exact values; never strip units into numbers."""
    if value is None or not value_matches_contract(field_name, value):
        return False
    contract = field_contract(field_name)
    q = text(quote)
    if not contract or not q:
        return False
    if field_name == "currency":
        return value in CURRENCY_PATTERNS and bool(re.search(CURRENCY_PATTERNS[value], q, re.I)) and not any(
            code != value and re.search(pattern, q, re.I) for code, pattern in CURRENCY_PATTERNS.items())
    if contract.value_type == "string":
        if field_name in {"interest_rate_summary", "purchase_interest_rate_summary", "fee_waiver_condition", "early_withdrawal_penalty"}:
            return text(value).casefold() == q.casefold()
        return bool(text(value)) and text(value).casefold() in q.casefold()
    if contract.value_type == "boolean":
        # Absence of a positive statement never proves false.
        patterns = {
            "secured_flag": (r"(?<!un)\bsecured\b|\bcollateral (?:is )?required\b", r"\bunsecured\b|no collateral required|\bnot secured\b"),
            "unlimited_transactions_flag": (r"\bunlimited\b.{0,35}\btransactions?\b", r"\b(?:limited to|maximum of) \d+.{0,20}transactions?"),
            "redeemable_flag": (r"(?<!non-)\bredeemable\b|can be (?:redeemed|cashed) before maturity", r"non[- ]redeemable|cannot be (?:redeemed|cashed) before maturity"),
            "non_redeemable_flag": (r"non[- ]redeemable|cannot be (?:redeemed|cashed) before maturity", r"(?<!non-)\bredeemable\b"),
        }
        pair = patterns.get(field_name)
        if re.search(r"\b(?:may|might|could|optional|depending)\b|not unsecured|not non[- ]redeemable", q, re.I):
            return False
        if not pair:
            return False
        yes, no = (bool(re.search(p, q, re.I)) for p in pair)
        # non-redeemable contains redeemable; resolve explicit negation first.
        if field_name == "redeemable_flag" and no:
            yes = False
        if field_name == "non_redeemable_flag" and yes:
            no = False
        return (yes and not no) if value is True else (no and not yes)
    if contract.value_type == "json":
        if field_name != "term_rate_table" or not isinstance(value, list) or not value:
            return False
        for row in value:
            label = text(row.get("term_label"))
            # Require a rate in the same row following this exact term. Never
            # accept merely finding every number somewhere in a large table.
            matches = list(re.finditer(r"(?<!\w)" + re.escape(label) + r"(?!\w)", q, re.I)) if label else []
            if len(matches) != 1:
                return False
            local = q[matches[0].end():matches[0].end() + 160]
            first_rate = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%", local)
            if not first_rate or re.search(r"\b\d+\s*[- ]?\s*(?:days?|months?|years?)\b|[-−]\s*\d", local[:first_rate.end()], re.I):
                return False
            rates = [first_rate.group(1)]
            if not rates or Decimal(rates[0]) != Decimal(str(row["rate"])):
                return False
            days = row.get("term_length_days")
            if days is not None and not re.search(rf"(?<![\d.]){days}\s*days?\b", label, re.I):
                return False
            amount = row.get("minimum_deposit")
            if amount is not None and not quote_supports_value("minimum_deposit", amount, local):
                return False
            if row.get("notes") and not exact_quote(row["notes"], q):
                return False
        return True
    if re.search(r"[-−]\s*\d+(?:\.\d+)?\s*%", q):
        return False
    number = Decimal(str(value))
    if not number.is_finite() or number < 0:
        return False
    if contract.unit == "percentage_points":
        if rate_component_only(value=value, context=q):
            return False
        rates = re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%", q)
        # A scalar cannot represent a tier, range, conditional offer or example.
        if re.search(r"\b(?:up to|from|between|as low as|bonus|introductory|promotional|example|illustration|if|when|qualify|qualifying|depending)\b", q, re.I):
            return False
        if len({Decimal(v) for v in rates}) != 1:
            return False
        rate_labels = {
            "purchase_interest_rate": r"purchase",
            "cash_advance_rate": r"cash advance",
            "balance_transfer_rate": r"balance transfer",
            "mortgage_rate": r"mortgage",
            "base_12_month_rate": r"12[- ]month|1[- ]year|one[- ]year",
        }
        meaning = rate_labels.get(field_name)
        if meaning and not re.search(meaning, q, re.I):
            return False
        return number < 100 and number in {Decimal(v) for v in rates} and bool(re.search(r"\b(?:rate|interest|apr|apy|yield)\b", q, re.I))
    labels = {
        "monthly_fee": r"monthly.{0,25}(?:fee|charge)|(?:fee|charge).{0,20}(?:monthly|per month)",
        "public_display_fee": r"monthly.{0,25}(?:fee|charge)|(?:fee|charge).{0,20}(?:monthly|per month)",
        "annual_fee": r"annual.{0,20}fee|fee.{0,20}(?:annual|per year)",
        "minimum_deposit": r"(?:minimum|initial|opening).{0,30}deposit|deposit.{0,30}(?:minimum|to open)|open.{0,25}(?:at least|minimum)",
        "minimum_balance": r"minimum.{0,25}balance|balance.{0,25}(?:at least|minimum)",
        "transaction_fee": r"transaction.{0,20}(?:fee|charge)|per transaction",
        "included_transactions": r"transactions?",
        "term_length_days": r"days?",
    }
    label = labels.get(field_name)
    if not label or not re.search(label, q, re.I):
        return False
    if field_name == "included_transactions":
        return bool(re.search(rf"(?<![\d.]){int(number)}\s+(?:(?:free|included|debit)\s+)?transactions?\b", q, re.I))
    if field_name == "term_length_days":
        return bool(re.search(rf"(?<![\d.]){int(number)}\s*days?\b", q, re.I))
    if contract.unit == "currency_amount":
        # A waiver balance or example must not stand in for a fee.
        amounts = re.findall(r"(?:[$€£]|\b(?:CAD|USD|EUR|GBP)\s*)(\d[\d,]*(?:\.\d+)?)", q, re.I)
        amounts += re.findall(r"(\d[\d,]*(?:\.\d+)?)\s*(?:dollars?|CAD|USD|EUR|GBP)\b", q, re.I)
        matching = {Decimal(v.replace(",", "")) for v in amounts}
        if number == 0 and re.search(r"\b(?:if|when|waived|waiver|provided|qualify|qualifying)\b", q, re.I):
            return False
        if number == 0 and re.search(r"\b(?:no|zero)\b.{0,25}\b(?:fee|minimum)\b", q, re.I):
            return True
        if number not in _numbers(q) or number not in matching:
            return False
        if field_name in {"monthly_fee", "public_display_fee", "annual_fee", "minimum_deposit", "minimum_balance", "transaction_fee"}:
            label_match = re.search(label, q, re.I)
            local = q[label_match.end():label_match.end() + 90]
            local_amount = re.search(r"(?:[$€£]|\b(?:CAD|USD|EUR|GBP)\s*)(\d[\d,]*(?:\.\d+)?)", local, re.I)
            if local_amount:
                return Decimal(local_amount.group(1).replace(",", "")) == number
            # Amount-first labels are accepted only in a short single-amount quote.
            return len(matching) == 1 and len(q) <= 90
        return False
    return True


def canonical_url(value: object) -> str:
    try:
        u = urlsplit(str(value or ""))
        if u.scheme != "https" or not u.hostname or u.username or u.password or u.port not in (None, 443):
            return ""
        return urlunsplit(("https", u.hostname.lower().removeprefix("www."), u.path.rstrip("/") or "/", u.query, ""))
    except ValueError:
        return ""


def _official_url(url: str, domains: object) -> bool:
    host = urlsplit(url).hostname if url else None
    if not host or not isinstance(domains, (list, tuple)):
        return False
    for domain in domains:
        raw = str(domain or "").lower().strip().removeprefix("https://").removeprefix("http://").split("/")[0].removeprefix("www.")
        if "." in raw and (host == raw or host.endswith("." + raw)):
            return True
    return False


def payload_digest(record: Mapping, payload: Mapping) -> str:
    facts = {k: v for k, v in payload.items() if k != RECEIPT_KEY}
    data = {"identity": {k: record.get(k) for k in IDENTITY_FIELDS}, "payload": facts}
    try:
        return sha256(json.dumps(data, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()).hexdigest()
    except (TypeError, ValueError):
        return ""


def acceptance_receipt_valid(record: Mapping, payload: Mapping | None = None) -> bool:
    p = payload if payload is not None else record.get("candidate_payload", {})
    receipt = p.get(RECEIPT_KEY, {}) if isinstance(p, Mapping) else {}
    if not isinstance(receipt, Mapping) or receipt.get("version") != ACCURACY_VERSION:
        return False
    digest = payload_digest(record, p)
    return bool(digest and receipt.get("accepted") is True and receipt.get("digest") == digest
                and all(value_matches_contract(k, v) for k, v in p.items() if k != RECEIPT_KEY))


def sanitize_candidate(record: dict, *, source_metadata: Mapping, evidence: list[dict]) -> tuple[dict, dict]:
    """Omit unproven fields and attach a content-bound acceptance result.

    Evidence must come from current-run extraction or DB joins, never model text.
    The returned exclusions contain field names/reasons only, not rejected values.
    """
    result = dict(record)
    payload = dict(record.get("candidate_payload") or {})
    mappings = record.get("field_mapping_metadata") or {}
    chunks = {str(e.get("evidence_chunk_id")): e for e in evidence}
    omitted = {}
    verified = []
    for name, value in list(payload.items()):
        if name == RECEIPT_KEY:
            payload.pop(name)
            continue
        if name in CONTEXT_FIELDS:
            continue
        if value is None or value == "" or value == [] or value == {}:
            payload.pop(name)
            continue
        m = mappings.get(name, {})
        e = chunks.get(str(m.get("evidence_chunk_id")), {})
        quote = m.get("official_evidence_quote")
        origin = canonical_url(e.get("source_url"))
        sources = m.get("official_web_sources") or []
        reason = None
        if not field_contract(name) or not value_matches_contract(name, value):
            reason = "invalid_or_undefined_field_type"
        elif m.get("normalized_value") != value:
            reason = "value_changed_after_grounding"
        elif m.get("official_grounding_contract_version") != "collection-official-grounding-v2" or m.get("official_verification_status") not in ("match", "mismatch"):
            reason = "official_grounding_missing"
        elif not _official_url(origin, source_metadata.get("official_domain_allowlist")) or not any(isinstance(s, dict) and canonical_url(s.get("url")) == origin for s in sources):
            reason = "evidence_source_mismatch"
        elif not exact_quote(quote, e.get("evidence_excerpt")):
            reason = "exact_evidence_missing"
        elif field_contract(name).unit in {"currency_amount", "percentage_points", "structured_rows"} and (
            any(code != record.get("currency") and re.search(pattern, str(e.get("evidence_excerpt") or ""), re.I)
                for code, pattern in CURRENCY_PATTERNS.items())
            or ("€" in str(quote) and record.get("currency") != "EUR")
            or ("£" in str(quote) and record.get("currency") != "GBP")
        ):
            reason = "field_currency_mismatch"
        elif (field_contract(name).unit == "percentage_points" or name == "term_rate_table") and not re.search(r"\b(?:annual|annually|apr|apy|per annum|per year)\b|\bp\.?a\.?(?!\w)", str(e.get("evidence_excerpt") or ""), re.I):
            reason = "annual_rate_basis_unproven"
        elif not quote_supports_value(name, value, str(quote)):
            reason = "field_meaning_unproven"
        elif field_contract(name).value_type in {"decimal", "integer", "boolean"} and not quote_supports_value(name, value, str(e.get("evidence_excerpt") or "")):
            # Check the retained context too: a model may quote only the number
            # and omit an adjacent tier, condition, negation or conflicting rate.
            reason = "evidence_context_ambiguous"
        if reason:
            payload.pop(name)
            omitted[name] = reason
        else:
            verified.append(name)
    # Derived display aliases may only copy an accepted field of the same meaning.
    if "monthly_fee" in verified:
        payload["public_display_fee"] = payload["monthly_fee"]
        verified.append("public_display_fee")
    identity_verified = "product_name" in verified and payload.get("product_name") == record.get("product_name")
    reasons = []
    if not identity_verified:
        reasons.append("product_identity_unverified")
    if source_metadata.get("discovery_role") != "detail":
        reasons.append("source_is_not_product_detail")
    # Currency needs explicit ISO/name evidence, not merely a country default.
    currency = str(record.get("currency") or "")
    currency_verified = any(
        quote_supports_value("currency", currency, str(mappings.get(name, {}).get("official_evidence_quote") or ""))
        for name in verified
    )
    currency_mapping = mappings.get("currency", {})
    currency_evidence = chunks.get(str(currency_mapping.get("evidence_chunk_id")), {})
    currency_origin = canonical_url(currency_evidence.get("source_url"))
    if (currency_mapping.get("official_grounding_contract_version") == "collection-official-grounding-v2"
        and currency_mapping.get("official_verification_status") in ("match", "mismatch")
        and currency_mapping.get("normalized_value") == currency
        and _official_url(currency_origin, source_metadata.get("official_domain_allowlist"))
        and any(isinstance(source, dict) and canonical_url(source.get("url")) == currency_origin for source in currency_mapping.get("official_web_sources", []))
        and exact_quote(currency_mapping.get("official_evidence_quote"), currency_evidence.get("evidence_excerpt"))
        and quote_supports_value("currency", currency, str(currency_mapping.get("official_evidence_quote") or ""))):
        currency_verified = True
    if not currency_verified:
        reasons.append("product_currency_unverified")
    else:
        verified.append("currency")
    quality = comparison_quality(product_type=record.get("product_type"), country_code=record.get("country_code"), expected_fields=source_metadata.get("expected_fields", []), candidate_payload=payload)
    if not quality.applicable or not quality.contract_defined or not quality.complete:
        reasons.append("essential_fields_missing")
    receipt = {"version": ACCURACY_VERSION, "accepted": not reasons, "verified_fields": sorted(set(verified)), "omitted_fields": omitted, "reasons": reasons, "missing_fields": list(quality.missing_fields)}
    receipt["digest"] = payload_digest(record, payload)
    payload[RECEIPT_KEY] = receipt
    result["candidate_payload"] = payload
    return result, receipt
