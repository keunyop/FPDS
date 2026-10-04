from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from worker.pipeline.fpds_field_contract import field_contract, registered_field_names, value_matches_contract
from worker.pipeline.fpds_market_profile import country_product_profile

MAX_COLLECTION_TARGETS = 60


def resolve_collection_fields(*, product_type: str, country_code: str | None,
                              expected_fields=(), collection_field_policy=None) -> dict[str, Any]:
    """Resolve a country-owned target list without weakening financial essentials.

    Locked alternatives remain grouped/conditional requirements, not independent
    mandatory values. An explicit optional list controls targeting; proved facts
    encountered in the same evidence still survive ordinary normalization.
    """
    country = str(country_code or 'CA').upper()
    profile = country_product_profile(country_code=country, product_type=product_type)
    requirements = [{'key': r.key, 'alternatives': list(r.alternatives),
                     'required_when': r.required_when} for r in (profile.requirements if profile else ())]
    locked = list(dict.fromkeys(['product_name', 'currency',
                                *(f for r in requirements for f in r['alternatives'])]))
    registered = [f for f in expected_fields if isinstance(f, str) and field_contract(f)]
    catalog = sorted(set(registered_field_names()) | set(registered))
    policies = collection_field_policy if isinstance(collection_field_policy, Mapping) else {}
    policy = policies.get(country)
    configured = isinstance(policy, Mapping)
    if configured:
        required = list(dict.fromkeys([*locked, *policy.get('required_fields', [])]))
        optional = list(dict.fromkeys(policy.get('optional_fields', [])))
    else:
        required = locked
        optional = list(dict.fromkeys([*(profile.supplemental_fields if profile else ()), *registered]))
    optional = [f for f in optional if f not in required]
    return {'country_code': country, 'configured': configured,
            'required_fields': required, 'optional_fields': optional,
            'locked_required_fields': locked, 'requirements': requirements,
            'field_catalog': [{'field_key': f, 'value_type': field_contract(f).value_type,
                              'unit': field_contract(f).unit} for f in catalog]}


def validate_collection_fields(value: object, *, resolved: Mapping) -> dict[str, list[str]]:
    if not isinstance(value, Mapping) or set(value) != {'required_fields', 'optional_fields'}:
        raise ValueError('Provide required_fields and optional_fields lists.')
    lists = {}
    catalog = {f['field_key'] for f in resolved['field_catalog']}
    for key in ('required_fields', 'optional_fields'):
        items = value[key]
        if not isinstance(items, list) or len(items) > 100:
            raise ValueError('Collection fields must be bounded lists.')
        if any(not isinstance(f, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,79}', f)
               or f not in catalog or not field_contract(f) for f in items):
            raise ValueError('Only registered typed collection fields are allowed.')
        if len(set(items)) != len(items):
            raise ValueError('Collection fields must not contain duplicates.')
        lists[key] = list(items)
    if len(lists['required_fields']) + len(lists['optional_fields']) > MAX_COLLECTION_TARGETS:
        raise ValueError('Select at most 60 collection targets for one bounded evidence pass.')
    if set(lists['required_fields']) & set(lists['optional_fields']):
        raise ValueError('A field cannot be both required and optional.')
    if not set(resolved['locked_required_fields']).issubset(lists['required_fields']):
        raise ValueError('Identity, currency and mandatory financial requirements cannot be removed.')
    return lists


def metadata_collection_fields(metadata: Mapping, *, product_type: str, country_code: str | None):
    return resolve_collection_fields(product_type=product_type, country_code=country_code,
        expected_fields=metadata.get('expected_fields', ()),
        collection_field_policy=metadata.get('collection_field_policy'))


def additional_required_fields(resolved: Mapping) -> list[str]:
    locked = set(resolved['locked_required_fields'])
    return [f for f in resolved['required_fields'] if f not in locked]


def missing_additional_required_fields(resolved: Mapping, payload: Mapping) -> list[str]:
    return [f for f in additional_required_fields(resolved)
            if payload.get(f) in (None, '', [], {}) or not value_matches_contract(f, payload.get(f))]
