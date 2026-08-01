from __future__ import annotations


_COUNTRY_DEFAULT_CURRENCIES = {
    "CA": "CAD",
    "US": "USD",
}


def default_currency_for_country(country_code: object) -> str | None:
    """Return a configured market default without inferring from page locale."""

    return _COUNTRY_DEFAULT_CURRENCIES.get(str(country_code or "").strip().upper())
