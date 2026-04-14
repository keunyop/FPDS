from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .registry import RegistrySource, SourceRegistry, load_registry

DEFAULT_REGISTRY_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "source_registry_catalog.json"


@dataclass(frozen=True)
class RegistryCatalogEntry:
    bank_code: str
    country_code: str
    product_type: str
    registry_path: Path

    @property
    def registry_key(self) -> str:
        return f"{self.country_code}:{self.bank_code}:{self.product_type}"


def load_registry_catalog(path: Path | None = None) -> tuple[RegistryCatalogEntry, ...]:
    catalog_path = path or DEFAULT_REGISTRY_CATALOG_PATH
    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    country_code = raw["country_code"]
    entries: list[RegistryCatalogEntry] = []
    for item in raw["registries"]:
        registry_path = Path(item["registry_path"])
        if not registry_path.is_absolute():
            registry_path = (catalog_path.parent / registry_path).resolve()
        entries.append(
            RegistryCatalogEntry(
                bank_code=item["bank_code"],
                country_code=item.get("country_code", country_code),
                product_type=item["product_type"],
                registry_path=registry_path,
            )
        )
    return tuple(entries)


def load_all_registries(path: Path | None = None) -> tuple[SourceRegistry, ...]:
    return tuple(load_registry(entry.registry_path) for entry in load_registry_catalog(path))


def load_catalog_source_index(path: Path | None = None) -> dict[str, RegistrySource]:
    source_index: dict[str, RegistrySource] = {}
    for registry in load_all_registries(path):
        for source in registry.sources:
            if source.source_id in source_index:
                raise ValueError(f"Duplicate catalog source id: {source.source_id}")
            source_index[source.source_id] = source
    return source_index


def resolve_sources_by_id(
    source_ids: list[str],
    *,
    registry_path: Path | None = None,
    catalog_path: Path | None = None,
) -> dict[str, RegistrySource]:
    if registry_path is not None:
        registry = load_registry(registry_path)
        missing_source_ids = [source_id for source_id in source_ids if source_id not in {source.source_id for source in registry.sources}]
        if missing_source_ids:
            raise ValueError("Source ids not found in the selected registry: " + ", ".join(missing_source_ids))
        return {source_id: registry.by_source_id(source_id) for source_id in source_ids}

    source_index = load_catalog_source_index(catalog_path)
    missing_source_ids = [source_id for source_id in source_ids if source_id not in source_index]
    if missing_source_ids:
        raise ValueError("Source ids not found in the registry catalog: " + ", ".join(missing_source_ids))
    return {source_id: source_index[source_id] for source_id in source_ids}
