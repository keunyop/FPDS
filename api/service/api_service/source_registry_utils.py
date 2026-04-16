from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path
from urllib.parse import ParseResult, urlparse, urlunparse

_SEED_BANK_NAMES = {
    "RBC": "Royal Bank of Canada",
    "TD": "TD Bank",
    "BMO": "Bank of Montreal",
    "SCOTIA": "Scotiabank",
    "CIBC": "CIBC",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def discovery_data_root() -> Path:
    return repo_root() / "worker" / "discovery" / "data"


def default_registry_catalog_path() -> Path:
    return discovery_data_root() / "source_registry_catalog.json"


def normalize_source_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme or '<missing>'}")
    if not parsed.netloc:
        raise ValueError(f"Missing hostname in URL: {url}")

    netloc = _normalize_netloc(parsed)
    path = _normalize_path(parsed.path)
    normalized = ParseResult(
        scheme=parsed.scheme.lower(),
        netloc=netloc,
        path=path,
        params="",
        query="",
        fragment="",
    )
    return urlunparse(normalized)


def infer_source_type(url: str) -> str:
    parsed = urlparse(url)
    if parsed.path.lower().endswith(".pdf"):
        return "pdf"
    return "html"


def build_source_document_id(bank_code: str, normalized_source_url: str, source_type: str) -> str:
    identity = f"{bank_code}|{normalized_source_url}|{source_type}"
    digest = sha1(identity.encode("utf-8")).hexdigest()[:16]
    return f"src-{bank_code.lower()}-{source_type}-{digest}"


def load_seed_source_registry_rows() -> list[dict[str, object]]:
    catalog_path = default_registry_catalog_path()
    raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    default_country_code = str(raw_catalog["country_code"]).strip().upper()
    rows: list[dict[str, object]] = []
    for registry_entry in raw_catalog.get("registries", []):
        registry_path = Path(str(registry_entry["registry_path"]))
        if not registry_path.is_absolute():
            registry_path = (catalog_path.parent / registry_path).resolve()
        raw_registry = json.loads(registry_path.read_text(encoding="utf-8"))
        bank_code = str(raw_registry["bank_code"]).strip().upper()
        country_code = str(raw_registry.get("country_code", default_country_code)).strip().upper()
        product_type = str(raw_registry["product_type"]).strip().lower()
        source_language = str(raw_registry.get("source_language", "en")).strip().lower()
        for source in raw_registry.get("sources", []):
            source_url = str(source["url"]).strip()
            rows.append(
                {
                    "source_id": str(source["source_id"]).strip(),
                    "bank_code": bank_code,
                    "country_code": country_code,
                    "product_type": product_type,
                    "product_key": None,
                    "source_name": str(source.get("purpose") or source["source_id"]).strip(),
                    "source_url": source_url,
                    "normalized_url": normalize_source_url(source_url),
                    "source_type": str(source.get("source_type") or infer_source_type(source_url)).strip().lower(),
                    "discovery_role": str(source.get("discovery_role", "detail")).strip().lower(),
                    "status": "active",
                    "priority": str(source.get("priority", "P1")).strip().upper(),
                    "source_language": str(source.get("source_language", source_language)).strip().lower(),
                    "purpose": str(source.get("purpose", "")).strip(),
                    "expected_fields": [str(item).strip() for item in source.get("expected_fields", []) if str(item).strip()],
                    "seed_source_flag": bool(source.get("seed_source_flag", False)),
                    "redirect_target_url": None,
                    "alias_urls": [],
                    "change_reason": "seeded_from_json_catalog",
                }
            )
    return rows


def load_seed_bank_profiles() -> list[dict[str, object]]:
    catalog_path = default_registry_catalog_path()
    raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    default_country_code = str(raw_catalog["country_code"]).strip().upper()
    profiles: dict[str, dict[str, object]] = {}
    for registry_entry in raw_catalog.get("registries", []):
        registry_path = Path(str(registry_entry["registry_path"]))
        if not registry_path.is_absolute():
            registry_path = (catalog_path.parent / registry_path).resolve()
        raw_registry = json.loads(registry_path.read_text(encoding="utf-8"))
        bank_code = str(raw_registry["bank_code"]).strip().upper()
        if bank_code in profiles:
            continue
        country_code = str(raw_registry.get("country_code", default_country_code)).strip().upper()
        source_language = str(raw_registry.get("source_language", "en")).strip().lower()
        entry_source_id = str(raw_registry["entry_source_id"]).strip()
        entry_source = next((item for item in raw_registry.get("sources", []) if str(item.get("source_id", "")).strip() == entry_source_id), None)
        homepage_url = str((entry_source or raw_registry["sources"][0])["url"]).strip()
        profiles[bank_code] = {
            "bank_code": bank_code,
            "country_code": country_code,
            "bank_name": _SEED_BANK_NAMES.get(bank_code, bank_code),
            "homepage_url": homepage_url,
            "normalized_homepage_url": normalize_source_url(homepage_url),
            "source_language": source_language,
            "managed_flag": True,
            "change_reason": "seeded_from_json_catalog",
        }
    return list(profiles.values())


def load_seed_source_catalog_items() -> list[dict[str, object]]:
    catalog_path = default_registry_catalog_path()
    raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    default_country_code = str(raw_catalog["country_code"]).strip().upper()
    rows: list[dict[str, object]] = []
    for registry_entry in raw_catalog.get("registries", []):
        bank_code = str(registry_entry["bank_code"]).strip().upper()
        product_type = str(registry_entry["product_type"]).strip().lower()
        country_code = str(registry_entry.get("country_code", default_country_code)).strip().upper()
        rows.append(
            {
                "catalog_item_id": f"catalog-{country_code.lower()}-{bank_code.lower()}-{product_type}",
                "bank_code": bank_code,
                "country_code": country_code,
                "product_type": product_type,
                "status": "active",
                "change_reason": "seeded_from_json_catalog",
            }
        )
    return rows


def _normalize_netloc(parsed: ParseResult) -> str:
    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    if (parsed.scheme.lower() == "https" and port == 443) or (parsed.scheme.lower() == "http" and port == 80):
        port = None
    if port is None:
        return hostname
    return f"{hostname}:{port}"


def _normalize_path(path: str) -> str:
    if not path:
        return "/"

    normalized = path
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized
