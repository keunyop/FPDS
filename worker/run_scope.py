from __future__ import annotations

import re
from collections.abc import Iterable

_COUNTRY_CODE_RE = re.compile(r"^[A-Z]{2}$")


def require_single_country_code(values: Iterable[object]) -> str:
    """Return one normalized ISO alpha-2 country code for an ingestion run."""

    country_codes: set[str] = set()
    invalid_values: list[str] = []
    for value in values:
        country_code = str(value or "").strip().upper()
        if not _COUNTRY_CODE_RE.fullmatch(country_code):
            invalid_values.append(str(value))
            continue
        country_codes.add(country_code)

    if invalid_values:
        raise ValueError(
            "Ingestion run country scope contains invalid country_code values: "
            + ", ".join(sorted(invalid_values))
        )
    if len(country_codes) != 1:
        displayed = ", ".join(sorted(country_codes)) or "none"
        raise ValueError(
            "Ingestion run must contain exactly one country_code; "
            f"received {displayed}."
        )
    return next(iter(country_codes))
