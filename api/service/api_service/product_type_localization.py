from __future__ import annotations

from typing import Any


_US_DISCOVERY_OVERRIDES: dict[str, dict[str, object]] = {
    "chequing": {
        "display_name": "Checking account",
        "description": "Consumer transaction and checking accounts used for everyday deposits, payments, and debit-card access.",
        "discovery_keywords": (
            "checking",
            "checking account",
            "consumer checking",
            "everyday banking",
            "transaction account",
        ),
    },
    "gic": {
        "display_name": "Certificate of Deposit (CD)",
        "description": "Bank certificates of deposit and other fixed-term deposit accounts with a stated maturity.",
        "discovery_keywords": (
            "certificate of deposit",
            "CD account",
            "bank CD",
            "fixed term CD",
            "featured CD",
            "flexible CD",
        ),
    },
    "mortgage": {
        "description": "Residential home loans, including fixed-rate, adjustable-rate, FHA, VA, jumbo, and refinance mortgages.",
        "discovery_keywords": ("home loan", "fixed-rate mortgage", "adjustable-rate mortgage", "refinance", "jumbo mortgage"),
    },
    "personal-loan": {
        "description": "Consumer personal, auto, student, and other installment loans.",
        "discovery_keywords": ("personal loan", "auto loan", "student loan", "installment loan"),
    },
    "line-of-credit": {
        "description": "Personal and home-equity revolving lines of credit.",
        "discovery_keywords": ("line of credit", "personal line", "home equity line of credit", "HELOC"),
    },
}


_JP_DISCOVERY_KEYWORDS = {
    "chequing": ("普通預金", "決済用普通預金", "当座預金"),
    "savings": ("貯蓄預金",),
    "gic": ("定期預金", "スーパー定期", "大口定期", "変動金利定期"),
    "mortgage": ("住宅ローン", "ホームローン"),
    "personal-loan": ("フリーローン", "マイカーローン", "マイローン", "証書貸付型"),
    "line-of-credit": ("カードローン", "当座貸越型"),
    "business-loan": ("事業性融資", "事業者ローン", "事業資金融資", "サポートローン"),
    "business-line-of-credit": ("事業者カードローン", "当貸ローン", "ビジネスライン"),
}


def localize_product_type_definition(
    *,
    country_code: str,
    definition: dict[str, Any],
) -> dict[str, Any]:
    """Return discovery-only vocabulary without changing the canonical type code."""

    localized = dict(definition)
    country = str(country_code or "").strip().upper()
    if country == "JP":
        kind = str(definition.get("product_type_code") or "").strip().lower()
        keywords = _JP_DISCOVERY_KEYWORDS.get(kind)
        if keywords:
            localized.update(display_name=keywords[0], discovery_keywords=list(keywords),
                             description=" / ".join(keywords))
        return localized
    if country != "US":
        return localized

    product_type_code = str(definition.get("product_type_code") or "").strip().lower()
    override = _US_DISCOVERY_OVERRIDES.get(product_type_code)
    if override is None:
        description = str(localized.get("description") or "")
        localized["description"] = description.replace("Canadian ", "").replace("Canada ", "")
        return localized

    existing_keywords = [
        str(item).strip()
        for item in localized.get("discovery_keywords", [])
        if str(item).strip()
    ]
    localized.update({key: value for key, value in override.items() if key != "discovery_keywords"})
    localized["discovery_keywords"] = list(
        dict.fromkeys([*existing_keywords, *(str(item) for item in override["discovery_keywords"])])
    )
    return localized
