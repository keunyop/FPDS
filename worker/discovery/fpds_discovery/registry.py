from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .url_utils import build_source_document_id, build_source_identity, normalize_source_url

DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "td_savings_source_registry.json"


@dataclass(frozen=True)
class RegistrySource:
    source_id: str
    priority: str
    seed_source_flag: bool
    source_type: str
    discovery_role: str
    purpose: str
    url: str
    normalized_url: str
    expected_fields: tuple[str, ...]
    source_language: str
    bank_code: str
    country_code: str
    product_type: str

    @property
    def identity(self) -> str:
        return build_source_identity(self.bank_code, self.normalized_url, self.source_type)

    @property
    def source_document_id(self) -> str:
        return build_source_document_id(self.bank_code, self.normalized_url, self.source_type)

    def to_source_document_record(self) -> dict[str, object]:
        return {
            "source_document_id": self.source_document_id,
            "bank_code": self.bank_code,
            "country_code": self.country_code,
            "normalized_source_url": self.normalized_url,
            "source_type": self.source_type,
            "source_language": self.source_language,
            "registry_managed_flag": True,
            "source_metadata": {
                "source_id": self.source_id,
                "priority": self.priority,
                "purpose": self.purpose,
                "product_type": self.product_type,
                "discovery_role": self.discovery_role,
                "seed_source_flag": self.seed_source_flag,
                "expected_fields": list(self.expected_fields),
            },
        }


@dataclass(frozen=True)
class SourceRegistry:
    registry_version: str
    bank_code: str
    country_code: str
    product_type: str
    source_language: str
    allowed_domains: tuple[str, ...]
    entry_source_id: str
    sources: tuple[RegistrySource, ...]

    def __post_init__(self) -> None:
        by_identity: dict[str, RegistrySource] = {}
        by_source_id: dict[str, RegistrySource] = {}
        for source in self.sources:
            by_identity[source.identity] = source
            by_source_id[source.source_id] = source
        object.__setattr__(self, "_by_identity", by_identity)
        object.__setattr__(self, "_by_source_id", by_source_id)

    @property
    def entry_source(self) -> RegistrySource:
        return self.by_source_id(self.entry_source_id)

    def by_source_id(self, source_id: str) -> RegistrySource:
        return self._by_source_id[source_id]

    def match(self, normalized_url: str, source_type: str) -> RegistrySource | None:
        identity = build_source_identity(self.bank_code, normalized_url, source_type)
        return self._by_identity.get(identity)

    def iter_html_sources(self) -> tuple[RegistrySource, ...]:
        return tuple(source for source in self.sources if source.source_type == "html")


def load_registry(path: Path | None = None) -> SourceRegistry:
    registry_path = path or DEFAULT_REGISTRY_PATH
    raw = json.loads(registry_path.read_text(encoding="utf-8"))

    bank_code = raw["bank_code"]
    country_code = raw["country_code"]
    product_type = raw["product_type"]
    source_language = raw["source_language"]

    sources: list[RegistrySource] = []
    for item in raw["sources"]:
        normalized_url = normalize_source_url(item["url"])
        sources.append(
            RegistrySource(
                source_id=item["source_id"],
                priority=item["priority"],
                seed_source_flag=bool(item["seed_source_flag"]),
                source_type=item["source_type"],
                discovery_role=item["discovery_role"],
                purpose=item["purpose"],
                url=item["url"],
                normalized_url=normalized_url,
                expected_fields=tuple(item["expected_fields"]),
                source_language=item.get("source_language", source_language),
                bank_code=bank_code,
                country_code=country_code,
                product_type=product_type,
            )
        )

    return SourceRegistry(
        registry_version=raw["registry_version"],
        bank_code=bank_code,
        country_code=country_code,
        product_type=product_type,
        source_language=source_language,
        allowed_domains=tuple(raw["allowed_domains"]),
        entry_source_id=raw["entry_source_id"],
        sources=tuple(sources),
    )
