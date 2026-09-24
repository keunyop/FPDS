"""Public-only deposit comparison scenarios; never infer a return from a headline.

Missing basis/conditions in old snapshots fail closed. No live bank or canonical
reads occur here. Terms retain calendar months separately from literal days.
"""
from __future__ import annotations

import re
import json
from typing import Any
from api_service.public_rates import public_rate, interpret_rate_text
from api_service.public_common import serialize_decimal

_TERM = re.compile(r"^(\d+(?:\.\d+)?)\s*[- ]?\s*(years?|months?|days?)$", re.I)
_MARKET = re.compile(r"\b(?:indexed|index.linked|market.linked|equity.linked|ActionGIC|step.up|step.rate|escalating)\b", re.I)
_PROMO = re.compile(r"\b(?:promo(?:tion(?:al)?)?|introductory|welcome rate|bonus rate|limited.time|first \d+ (?:days?|months?))\b", re.I)
_TIER = re.compile(r"\b(?:tiered|boosted|tier[s ]|conditional rate)\b|interest.{0,60}(?:when|if).{0,60}balance", re.I)
_ANNUAL = re.compile(r"\b(?:per annum|annual(?:ized)? (?:interest )?rate|nominal annual|p\.a\.)", re.I)
_APY = re.compile(r"\b(?:APY|annual percentage yield|effective annual (?:rate|yield))\b", re.I)


def _number(value: Any, maximum: float = float('inf')) -> float | None:
    if isinstance(value, bool):
        return None
    value = serialize_decimal(value)
    return value if value is not None and 0 <= value <= maximum else None


def _term(label: Any, days: Any) -> dict[str, Any] | None:
    """Do not equate 360 days with a year, or parse a range as one maturity."""
    text = str(label or '').strip()
    numeric_days = _number(days, 36500)
    if days is not None and numeric_days is None:
        return None
    if numeric_days is not None and (numeric_days == 0 or not numeric_days.is_integer()):
        return None
    if text:
        match = _TERM.fullmatch(text)
        if not match:
            return None
        value, unit = float(match[1]), match[2].lower()
        if value <= 0:
            return None
        months = value * 12 if unit.startswith('year') else value if unit.startswith('month') else None
        if months is not None:
            if not months.is_integer() or months > 1200:
                return None
            # Existing canonical normalization uses 30 days/month and 365/year.
            if numeric_days is not None and numeric_days not in (months * 30, round(months * 365 / 12), int(months * 365 / 12)):
                return None
            return {'key': f'm{int(months)}', 'months': int(months), 'days': None}
        if not value.is_integer() or value > 36500 or (numeric_days is not None and value != numeric_days):
            return None
        numeric_days = value
    if numeric_days:
        return {'key': f'd{int(numeric_days)}', 'months': None, 'days': int(numeric_days)}
    return None


def deposit_terms(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get('product_type') not in ('savings', 'gic'):
        return None
    metadata = row.get('refresh_metadata')
    metadata = metadata if isinstance(metadata, dict) else {}
    conditions = metadata.get('deposit_conditions')
    conditions = conditions if isinstance(conditions, dict) else {}
    approved = row.get('approved_deposit_conditions')
    approved = approved if isinstance(approved, dict) else {}
    facts = {**metadata, **approved, **conditions}
    rate = public_rate(row)
    text = ' '.join(str(facts.get(key) or '') for key in (
        'interest_rate_summary', 'interest_rate', 'rate_type', 'description_short',
        'interest_calculation_method', 'tier_definition_text', 'promotional_period_text'))
    identity = str(row.get('product_name') or '')
    result = {'version': 1, 'basis': 'unknown', 'reason': None,
              'calculation_reason': None, 'withdrawal': 'unknown', 'options': []}

    def blocked(reason: str):
        return {**result, 'reason': reason, 'calculation_reason': reason, 'options': []}

    if _MARKET.search(identity + ' ' + text):
        return blocked('market_linked')
    if _PROMO.search(text) or facts.get('introductory_rate_flag') is True or facts.get('promotional_rate') is not None or facts.get('promotional_period_text'):
        return blocked('promotional')
    uniform_tiers = bool(re.search(r'per annum for all listed balance tiers', str(facts.get('interest_rate_summary') or ''), re.I))
    if not uniform_tiers and (_TIER.search(text) or facts.get('tiered_rate_flag') is True or facts.get('tier_definition_text')):
        return blocked('tiered')
    if not re.fullmatch(r'[A-Z]{3}', str(row.get('currency') or '')):
        return blocked('currency_unknown')
    result['basis'] = 'apy' if _APY.search(text) else 'annual' if _ANNUAL.search(text) else 'unknown'
    # Bounded, source-reviewed legacy clarification; never replaces a rate.
    # See public-deposit-comparison-review-2026-09-24.md. A different approved
    # version, currency, product or numeric value must obtain its own basis.
    if (result['basis'] == 'unknown' and row.get('product_id') == 'prod_mL9V64-_mjTai9Pb'
            and metadata.get('product_version_id') == 'pver_zq7rmli_JKGxZwKC'
            and row.get('country_code') == 'CA' and row.get('bank_code') == 'OAKEN'
            and row.get('currency') == 'CAD' and rate['comparable_rate'] == 2.8
            and _number(metadata.get('standard_rate'), 100) == 2.8):
        result['basis'] = 'annual'
    if result['basis'] == 'unknown':
        return blocked('basis_unknown')
    if result['basis'] == 'apy':
        result['calculation_reason'] = 'apy'
    # These are scenarios without reinvestment, not a compound-interest model.
    if facts.get('compounding_frequency') or re.search(r'compound(?:ed|ing)?', str(facts.get('interest_calculation_method') or '') + ' ' + str(facts.get('payout_option') or ''), re.I):
        result['calculation_reason'] = 'compound'
    if rate['kind'] in ('reference', 'conditional', 'promotional'):
        return blocked('rate_unclear')
    if row.get('product_type') == 'savings':
        if rate['kind'] != 'absolute' or rate['comparable_rate'] is None:
            return blocked('rate_unclear')
        if facts.get('term_rate_table'):
            return blocked('tiered')
        result['options'] = [{'key': 'ongoing', 'months': None, 'days': None,
                              'rate': rate['comparable_rate'],
                              'minimum_deposit': _number(row.get('minimum_balance'))}]
        return result

    if re.search(r'\b(?:variable|floating|prime)\b', identity + ' ' + text, re.I):
        return blocked('variable')
    redeemable, non_redeemable = facts.get('redeemable_flag'), facts.get('non_redeemable_flag')
    if redeemable is True and non_redeemable is True:
        return blocked('conditions_unclear')
    result['withdrawal'] = 'redeemable' if redeemable is True else 'non_redeemable' if non_redeemable is True or redeemable is False else 'unknown'
    table = facts.get('term_rate_table')
    table = table if isinstance(table, list) else []
    root_term = _term(facts.get('term_length_text'), row.get('term_length_days'))
    if not table:
        if not root_term:
            return blocked('term_unknown')
        if rate['kind'] != 'absolute' or rate['comparable_rate'] is None:
            return blocked('rate_unclear')
        result['options'] = [{**root_term, 'rate': rate['comparable_rate'], 'minimum_deposit': _number(row.get('minimum_deposit'))}]
    else:
        options = {}
        for item in table:
            if not isinstance(item, dict):
                return blocked('term_conflict')
            term = _term(item.get('term_label'), item.get('term_length_days'))
            value = _number(item.get('rate'), 100)
            if not term or value is None:
                return blocked('term_conflict')
            # Unstructured row qualifications need review before arithmetic.
            if item.get('notes'):
                return blocked('conditions_unclear')
            option = {**term, 'rate': value, 'minimum_deposit': _number(item.get('minimum_deposit')) if item.get('minimum_deposit') is not None else _number(row.get('minimum_deposit'))}
            if term['key'] in options and options[term['key']] != option:
                return blocked('term_conflict')
            options[term['key']] = option
        root_text = str(facts.get('term_length_text') or '').strip()
        if root_text and not root_term:
            try:
                labels = json.loads(root_text)
            except (ValueError, TypeError):
                labels = None
            if isinstance(labels, list):
                declared = [_term(label, None) for label in labels]
                if any(term is None for term in declared) or any(key not in {term['key'] for term in declared} for key in options):
                    return blocked('term_conflict')
            else:
                interval = re.fullmatch(r'(\d+)\s*(?:years?\s*)?(?:to|[-–])\s*(\d+)\s*(years?|months?|days?)', root_text, re.I)
                if not interval:
                    return blocked('term_conflict')
                lower, upper = _term(interval[1] + ' ' + interval[3], None), _term(interval[2] + ' ' + interval[3], None)
                if lower is None or upper is None:
                    return blocked('term_conflict')
                unit = 'months' if lower['months'] is not None else 'days'
                if any(option[unit] is None or not lower[unit] <= option[unit] <= upper[unit] for option in options.values()):
                    return blocked('term_conflict')
        if root_term and root_term['key'] not in options:
            return blocked('term_conflict')
        if row.get('term_length_days') is not None and not root_term:
            return blocked('term_conflict')
        for key in ('interest_rate_summary', 'interest_rate'):
            if facts.get(key) and interpret_rate_text(facts[key])['kind'] not in ('absolute', 'range'):
                return blocked('rate_unclear')
        # Scalar/standard values must belong to this schedule, never another product.
        values = {option['rate'] for option in options.values()}
        if any(_number(facts.get(key), 100) is not None and _number(facts[key], 100) not in values for key in ('standard_rate', 'base_12_month_rate')):
            return blocked('rate_unclear')
        if _number(row.get('public_display_rate'), 100) not in values:
            return blocked('rate_unclear')
        result['options'] = sorted(options.values(), key=lambda option: option['months'] * 365 / 12 if option['months'] else option['days'])
    return result
