"""FPDS source discovery package."""

from .discovery import SourceDiscoveryService
from .fetch import DiscoveryFetchPolicy, fetch_text
from .registry import DEFAULT_REGISTRY_PATH, RegistrySource, SourceRegistry, load_registry
from .url_utils import build_source_document_id, build_source_identity, normalize_source_url

__all__ = [
    "DEFAULT_REGISTRY_PATH",
    "DiscoveryFetchPolicy",
    "RegistrySource",
    "SourceDiscoveryService",
    "SourceRegistry",
    "build_source_document_id",
    "build_source_identity",
    "fetch_text",
    "load_registry",
    "normalize_source_url",
]
