from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
import json
import re
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

from .registry import RegistrySource, SourceRegistry
from .url_utils import host_matches_allowed_domains, infer_source_type, normalize_source_url

IGNORED_SCHEMES = ("javascript:", "mailto:", "tel:")
PROMOTION_KEYWORDS = ("offer", "offers", "bonus", "promo", "promotion")
COMPARE_KEYWORDS = ("compare",)
AUTHENTICATED_FLOW_KEYWORDS = ("easyweb", "login", "secureopen", "secure-open", "open-account", "apply")
PERSONALIZED_DISCOVERY_KEYWORDS = ("discovery.td.com", "find-the-account", "recommend")
_STRUCTURED_ATTRIBUTE_MAX_CHARS = 1_000_000
_STRUCTURED_LINK_MAX = 256
_STRUCTURED_DIRECT_LINK_MAX = 64
_STRUCTURED_NODE_MAX = 20_000
_STRUCTURED_SCRIPT_TYPES = {"application/json", "application/ld+json"}
_STRUCTURED_SCRIPT_MAX_COUNT = 8
_STRUCTURED_DIRECT_LINK_ATTRIBUTES = {
    "data-carddescriptionurl": "data-cardname",
}
_STRUCTURED_LINK_KEYS = {
    "agreementurl",
    "disclosureurl",
    "href",
    "pricingurl",
    "rateurl",
    "targeturl",
    "termsurl",
    "url",
}
_STRUCTURED_LABEL_KEYS = ("content", "label", "title", "name", "headline")
_STRUCTURED_TEXT_KEYS = {
    "body",
    "content",
    "description",
    "headline",
    "heading",
    "label",
    "name",
    "text",
    "title",
    "accountname",
    "cardname",
    "productname",
}
_STRUCTURED_PRICING_KEYS = {
    "annualfee",
    "annualpercentagerate",
    "annualpercentageyield",
    "apr",
    "apy",
    "earlywithdrawalpenalty",
    "feewaiver",
    "interestrate",
    "maintenancefee",
    "minimumbalance",
    "minimumdeposit",
    "minimumopeningdeposit",
    "monthlyfee",
    "minbalanceforfeewaiver",
    "includedtransactions",
    "pertransactionfee",
    "creditlimit",
    "loanamount",
    "openingdeposit",
    "penalty",
    "purchaseapr",
    "purchaseinterestrate",
    "rate",
    "ratetype",
    "term",
    "termlength",
}
_STRUCTURED_PRICING_LABEL_MARKERS = (
    "annual fee",
    "annual percentage",
    "apr",
    "apy",
    "early withdrawal",
    "interest rate",
    "maintenance fee",
    "minimum balance",
    "minimum deposit",
    "monthly fee",
    "opening deposit",
    "purchase rate",
    "rate",
)
_STRUCTURED_TEXT_MAX = 128
_STRUCTURED_TEXT_TOTAL_CHARS = 100_000


@dataclass(frozen=True)
class ExtractedLink:
    href: str
    resolved_url: str
    normalized_url: str
    source_type: str
    anchor_text: str


@dataclass(frozen=True)
class DiscoveryWarning:
    warning_code: str
    severity: str
    discovered_on_url: str
    target_url: str
    normalized_target_url: str | None
    source_type: str | None
    message: str

    def dedupe_key(self) -> tuple[str, str, str]:
        return (
            self.warning_code,
            self.discovered_on_url,
            self.normalized_target_url or self.target_url,
        )


@dataclass(frozen=True)
class SelectedSource:
    source_id: str
    source_document_id: str
    resolved_url: str
    normalized_source_url: str
    source_type: str
    source_language: str
    bank_code: str
    country_code: str
    priority: str
    discovery_role: str
    selection_mode: str
    discovery_status: str
    discovery_notes: list[str]
    registry_managed_flag: bool
    source_metadata: dict[str, object]

    @classmethod
    def from_registry_source(
        cls,
        source: RegistrySource,
        *,
        selection_mode: str,
        discovery_status: str,
        discovery_notes: list[str],
    ) -> "SelectedSource":
        record = source.to_source_document_record()
        return cls(
            source_id=source.source_id,
            source_document_id=str(record["source_document_id"]),
            resolved_url=source.url,
            normalized_source_url=str(record["normalized_source_url"]),
            source_type=str(record["source_type"]),
            source_language=str(record["source_language"]),
            bank_code=str(record["bank_code"]),
            country_code=str(record["country_code"]),
            priority=str(record["source_metadata"]["priority"]),
            discovery_role=str(record["source_metadata"]["discovery_role"]),
            selection_mode=selection_mode,
            discovery_status=discovery_status,
            discovery_notes=discovery_notes,
            registry_managed_flag=bool(record["registry_managed_flag"]),
            source_metadata=dict(record["source_metadata"]),
        )


@dataclass(frozen=True)
class DiscoveryResult:
    registry_version: str
    bank_code: str
    country_code: str
    product_type: str
    entry_source_id: str
    run_id: str | None
    correlation_id: str | None
    discovery_mode: str
    selected_sources: list[SelectedSource]
    warnings: list[DiscoveryWarning]

    def to_dict(self) -> dict[str, object]:
        discovered_sources = [item for item in self.selected_sources if item.discovery_status != "seed_only"]
        priority_counts = Counter(item.priority for item in self.selected_sources)
        type_counts = Counter(item.source_type for item in self.selected_sources)
        warning_counts = Counter(item.warning_code for item in self.warnings)
        return {
            "registry_version": self.registry_version,
            "bank_code": self.bank_code,
            "country_code": self.country_code,
            "product_type": self.product_type,
            "entry_source_id": self.entry_source_id,
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "discovery_mode": self.discovery_mode,
            "stats": {
                "selected_total": len(self.selected_sources),
                "discovered_total": len(discovered_sources),
                "warning_total": len(self.warnings),
                "selected_by_priority": dict(priority_counts),
                "selected_by_type": dict(type_counts),
                "warnings_by_code": dict(warning_counts),
            },
            "source_items": [item.__dict__ for item in self.selected_sources],
            "warnings": [warning.__dict__ for warning in self.warnings],
        }


class SourceDiscoveryService:
    def __init__(self, registry: SourceRegistry):
        self.registry = registry

    def discover(
        self,
        *,
        entry_html: str,
        html_loader: Callable[[str], str] | None = None,
        html_overrides: dict[str, str] | None = None,
        run_id: str | None = None,
        correlation_id: str | None = None,
        discovery_mode: str = "manual",
    ) -> DiscoveryResult:
        selected = self._seed_selected_sources()
        warnings: dict[tuple[str, str, str], DiscoveryWarning] = {}

        entry_source = self.registry.entry_source
        selected[entry_source.source_id] = SelectedSource.from_registry_source(
            entry_source,
            selection_mode="entry_seed",
            discovery_status="selected",
            discovery_notes=[f"Entry seed source for {self.registry.bank_code} {self.registry.product_type} discovery."],
        )

        self._scan_entry_links(
            entry_source=entry_source,
            entry_html=entry_html,
            selected=selected,
            warnings=warnings,
        )

        for html_source in self.registry.iter_html_sources():
            if html_source.discovery_role == "entry":
                continue
            html_text = self._load_html_for_source(
                html_source.normalized_url,
                html_loader=html_loader,
                html_overrides=html_overrides,
            )
            if html_text is None:
                continue
            self._scan_linked_pdfs(
                html_source=html_source,
                html_text=html_text,
                selected=selected,
                warnings=warnings,
            )

        ordered_sources = sorted(selected.values(), key=lambda item: item.source_id)
        ordered_warnings = sorted(
            warnings.values(),
            key=lambda item: (item.discovered_on_url, item.warning_code, item.target_url),
        )
        return DiscoveryResult(
            registry_version=self.registry.registry_version,
            bank_code=self.registry.bank_code,
            country_code=self.registry.country_code,
            product_type=self.registry.product_type,
            entry_source_id=self.registry.entry_source_id,
            run_id=run_id,
            correlation_id=correlation_id,
            discovery_mode=discovery_mode,
            selected_sources=ordered_sources,
            warnings=ordered_warnings,
        )

    def discover_live(
        self,
        *,
        html_loader: Callable[[str], str],
        run_id: str | None = None,
        correlation_id: str | None = None,
        discovery_mode: str = "manual",
    ) -> DiscoveryResult:
        entry_source = self.registry.entry_source
        entry_html = html_loader(entry_source.normalized_url)
        return self.discover(
            entry_html=entry_html,
            html_loader=html_loader,
            run_id=run_id,
            correlation_id=correlation_id,
            discovery_mode=discovery_mode,
        )

    def _seed_selected_sources(self) -> dict[str, SelectedSource]:
        selected: dict[str, SelectedSource] = {}
        for source in self.registry.sources:
            selected[source.source_id] = SelectedSource.from_registry_source(
                source,
                selection_mode="seed_only",
                discovery_status="seed_only",
                discovery_notes=["Approved registry seed included for reproducible run initialization."],
            )
        return selected

    def _scan_entry_links(
        self,
        *,
        entry_source: RegistrySource,
        entry_html: str,
        selected: dict[str, SelectedSource],
        warnings: dict[tuple[str, str, str], DiscoveryWarning],
    ) -> None:
        for link in extract_links(entry_html, base_url=entry_source.normalized_url):
            warning = self._classify_excluded_or_invalid_link(
                link=link,
                discovered_on_url=entry_source.normalized_url,
            )
            if warning is not None:
                warnings[warning.dedupe_key()] = warning
                continue

            registry_source = self.registry.match(link.normalized_url, link.source_type)
            if registry_source is None:
                warning = DiscoveryWarning(
                    warning_code="out_of_registry_link",
                    severity="warning",
                    discovered_on_url=entry_source.normalized_url,
                    target_url=link.resolved_url,
                    normalized_target_url=link.normalized_url,
                    source_type=link.source_type,
                    message="Entry page exposed a source that is not in the approved registry.",
                )
                warnings[warning.dedupe_key()] = warning
                continue

            if registry_source.discovery_role != "detail":
                continue

            selected[registry_source.source_id] = SelectedSource.from_registry_source(
                registry_source,
                selection_mode="discovered_from_entry",
                discovery_status="discovered",
                discovery_notes=[f"Discovered from entry page {entry_source.normalized_url}."],
            )

    def _scan_linked_pdfs(
        self,
        *,
        html_source: RegistrySource,
        html_text: str,
        selected: dict[str, SelectedSource],
        warnings: dict[tuple[str, str, str], DiscoveryWarning],
    ) -> None:
        for link in extract_links(html_text, base_url=html_source.normalized_url):
            warning = self._classify_excluded_or_invalid_link(
                link=link,
                discovered_on_url=html_source.normalized_url,
            )
            if warning is not None:
                warnings[warning.dedupe_key()] = warning
                continue

            if link.source_type != "pdf":
                continue

            registry_source = self.registry.match(link.normalized_url, "pdf")
            if registry_source is None:
                warning = DiscoveryWarning(
                    warning_code="out_of_registry_link",
                    severity="warning",
                    discovered_on_url=html_source.normalized_url,
                    target_url=link.resolved_url,
                    normalized_target_url=link.normalized_url,
                    source_type=link.source_type,
                    message="Linked PDF was not present in the approved registry.",
                )
                warnings[warning.dedupe_key()] = warning
                continue

            current = selected[registry_source.source_id]
            if current.discovery_status == "discovered":
                continue
            selected[registry_source.source_id] = SelectedSource.from_registry_source(
                registry_source,
                selection_mode="discovered_from_linked_pdf",
                discovery_status="discovered",
                discovery_notes=[f"Linked PDF discovered from {html_source.normalized_url}."],
            )

    def _load_html_for_source(
        self,
        normalized_url: str,
        *,
        html_loader: Callable[[str], str] | None,
        html_overrides: dict[str, str] | None,
    ) -> str | None:
        if html_overrides and normalized_url in html_overrides:
            return html_overrides[normalized_url]
        if html_loader is None:
            return None
        return html_loader(normalized_url)

    def _classify_excluded_or_invalid_link(
        self,
        *,
        link: ExtractedLink,
        discovered_on_url: str,
    ) -> DiscoveryWarning | None:
        parsed = urlparse(link.normalized_url)
        fingerprint = f"{parsed.netloc}{parsed.path}".lower()
        if any(keyword in fingerprint for keyword in PERSONALIZED_DISCOVERY_KEYWORDS):
            return DiscoveryWarning(
                warning_code="personalized_discovery_link",
                severity="warning",
                discovered_on_url=discovered_on_url,
                target_url=link.resolved_url,
                normalized_target_url=link.normalized_url,
                source_type=link.source_type,
                message="Personalized or recommendation-driven discovery flows are out of prototype scope.",
            )
        if any(keyword in fingerprint for keyword in COMPARE_KEYWORDS):
            return DiscoveryWarning(
                warning_code="compare_flow_link",
                severity="warning",
                discovered_on_url=discovered_on_url,
                target_url=link.resolved_url,
                normalized_target_url=link.normalized_url,
                source_type=link.source_type,
                message="Compare tool links are intentionally excluded from registry expansion.",
            )
        if any(keyword in fingerprint for keyword in PROMOTION_KEYWORDS):
            return DiscoveryWarning(
                warning_code="promotion_link",
                severity="warning",
                discovered_on_url=discovered_on_url,
                target_url=link.resolved_url,
                normalized_target_url=link.normalized_url,
                source_type=link.source_type,
                message="Promotion-oriented links are not accepted as canonical prototype sources.",
            )
        if any(keyword in fingerprint for keyword in AUTHENTICATED_FLOW_KEYWORDS):
            return DiscoveryWarning(
                warning_code="authenticated_flow_link",
                severity="warning",
                discovered_on_url=discovered_on_url,
                target_url=link.resolved_url,
                normalized_target_url=link.normalized_url,
                source_type=link.source_type,
                message="Authenticated or application flow links are intentionally excluded.",
            )
        hostname = parsed.hostname or ""
        if not host_matches_allowed_domains(hostname, self.registry.allowed_domains):
            return DiscoveryWarning(
                warning_code="cross_domain_link",
                severity="warning",
                discovered_on_url=discovered_on_url,
                target_url=link.resolved_url,
                normalized_target_url=link.normalized_url,
                source_type=link.source_type,
                message="Link resolved outside the approved public domain boundary.",
            )
        return None


class _LinkExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[ExtractedLink] = []
        self._current_href: str | None = None
        self._text_parts: list[str] = []
        self._structured_script_parts: list[str] | None = None
        self._structured_script_chars = 0
        self._structured_script_count = 0
        self._direct_link_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        self._extract_structured_attribute_links(attrs)
        if tag == "script":
            script_type = str(attr_map.get("type") or "").strip().lower()
            if (
                not attr_map.get("src")
                and script_type in _STRUCTURED_SCRIPT_TYPES
                and self._structured_script_count < _STRUCTURED_SCRIPT_MAX_COUNT
            ):
                self._structured_script_parts = []
                self._structured_script_chars = 0
                self._structured_script_count += 1
            return
        if tag != "a":
            return
        href = attr_map.get("href")
        if not href or href.startswith("#") or href.startswith(IGNORED_SCHEMES):
            return
        self._current_href = href
        self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._structured_script_parts is not None:
            if self._structured_script_chars + len(data) > _STRUCTURED_ATTRIBUTE_MAX_CHARS:
                self._structured_script_parts = None
            else:
                self._structured_script_parts.append(data)
                self._structured_script_chars += len(data)
        if self._current_href is None:
            return
        stripped = data.strip()
        if stripped:
            self._text_parts.append(stripped)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            if self._structured_script_parts is not None:
                raw_payload = "".join(self._structured_script_parts).strip()
                if raw_payload:
                    try:
                        payload = json.loads(raw_payload)
                    except (json.JSONDecodeError, TypeError):
                        pass
                    else:
                        self._extract_structured_payload_links(payload)
            self._structured_script_parts = None
            self._structured_script_chars = 0
            return
        if tag != "a" or self._current_href is None:
            return

        self._append_link(self._current_href, " ".join(self._text_parts).strip())
        self._current_href = None
        self._text_parts = []

    def _append_link(self, href: str, anchor_text: str, *, prefer_over_ordinary: bool = False) -> None:
        href_path = urlparse(href).path.lower()
        if (
            not href
            or href.startswith("#")
            or href.startswith(IGNORED_SCHEMES)
            or href_path.startswith(("/public-sites/", "/sitecore/"))
            or "{" in href
            or "}" in href
            or (len(self.links) >= _STRUCTURED_LINK_MAX and not prefer_over_ordinary)
            or (prefer_over_ordinary and self._direct_link_count >= _STRUCTURED_DIRECT_LINK_MAX)
        ):
            return
        resolved_url = urljoin(self.base_url, href)
        try:
            normalized_url = normalize_source_url(resolved_url)
        except ValueError:
            return

        link = ExtractedLink(
            href=href,
            resolved_url=resolved_url,
            normalized_url=normalized_url,
            source_type=infer_source_type(normalized_url),
            anchor_text=_strip_embedded_html(anchor_text),
        )
        if prefer_over_ordinary:
            if any(
                item.normalized_url == link.normalized_url
                and item.anchor_text == link.anchor_text
                for item in self.links[:self._direct_link_count]
            ):
                return
            self.links.insert(self._direct_link_count, link)
            self._direct_link_count += 1
            if len(self.links) > _STRUCTURED_LINK_MAX:
                self.links.pop()
            return
        self.links.append(link)

    def _extract_structured_attribute_links(self, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {
            str(name).lower(): (raw_value or "").strip()
            for name, raw_value in attrs
        }
        for link_key, label_key in _STRUCTURED_DIRECT_LINK_ATTRIBUTES.items():
            href = attr_map.get(link_key, "")
            if href and len(href) <= _STRUCTURED_ATTRIBUTE_MAX_CHARS:
                self._append_link(
                    _canonicalize_structured_attribute_link(href),
                    attr_map.get(label_key, ""),
                    prefer_over_ordinary=True,
                )

        for name, raw_value in attrs:
            value = (raw_value or "").strip()
            if (
                not name.lower().startswith("data-")
                or not value
                or len(value) > _STRUCTURED_ATTRIBUTE_MAX_CHARS
                or value[0] not in "[{"
            ):
                continue
            try:
                payload = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                continue
            self._extract_structured_payload_links(payload)

    def _extract_structured_payload_links(self, payload: Any) -> None:
        node_count = 0
        stack: list[tuple[Any, str | None, str]] = [(payload, None, "")]
        while stack and node_count < _STRUCTURED_NODE_MAX and len(self.links) < _STRUCTURED_LINK_MAX:
            node, parent_key, inherited_label = stack.pop()
            node_count += 1
            if isinstance(node, dict):
                label = _structured_node_label(node, inherited_label)
                normalized_node_keys = {
                    re.sub(r"[^a-z0-9]", "", str(key).lower())
                    for key in node
                }
                for key, item in node.items():
                    normalized_key = str(key).lower()
                    if isinstance(item, str) and (
                        normalized_key in _STRUCTURED_LINK_KEYS
                        or (normalized_key == "path" and str(parent_key or "").lower() == "learnmore")
                    ):
                        if normalized_key == "url" and "href" in normalized_node_keys:
                            # Headless CMS link envelopes often expose both a
                            # public href and an internal content-tree URL.
                            # Prefer the public route and never score the CMS
                            # alias as a second source.
                            continue
                        self._append_link(item.strip(), label)
                    elif isinstance(item, (dict, list)):
                        stack.append((item, str(key), label))
            elif isinstance(node, list):
                stack.extend(
                    (item, parent_key, inherited_label)
                    for item in reversed(node)
                    if isinstance(item, (dict, list))
                )


def _canonicalize_structured_attribute_link(value: str) -> str:
    """Convert a public CMS content-tree alias into its canonical web route."""

    parsed = urlparse(value)
    content_prefix = "/content/tdcom/"
    if not parsed.path.lower().startswith(content_prefix):
        return value
    public_path = "/" + parsed.path[len(content_prefix):]
    if public_path.lower().endswith(".html"):
        public_path = public_path[:-5]
    return parsed._replace(path=public_path).geturl()


def _strip_embedded_html(value: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", value or "").split())


def extract_links(html_text: str, *, base_url: str) -> list[ExtractedLink]:
    parser = _LinkExtractor(base_url=base_url)
    parser.feed(html_text)
    by_identity: dict[tuple[str, str], ExtractedLink] = {}
    for link in parser.links:
        by_identity.setdefault((link.normalized_url, link.anchor_text), link)
    return list(by_identity.values())


class _StructuredTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sections: list[str] = []
        self._seen: set[str] = set()
        self._total_chars = 0
        self._structured_script_parts: list[str] | None = None
        self._structured_script_chars = 0
        self._structured_script_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        for name, raw_value in attrs:
            value = (raw_value or "").strip()
            if (
                not name.lower().startswith("data-")
                or not value
                or len(value) > _STRUCTURED_ATTRIBUTE_MAX_CHARS
                or value[0] not in "[{"
            ):
                continue
            try:
                payload = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                continue
            self._extract_structured_payload_text(payload)
        if tag == "script":
            script_type = str(attr_map.get("type") or "").strip().lower()
            if (
                not attr_map.get("src")
                and script_type in _STRUCTURED_SCRIPT_TYPES
                and self._structured_script_count < _STRUCTURED_SCRIPT_MAX_COUNT
            ):
                self._structured_script_parts = []
                self._structured_script_chars = 0
                self._structured_script_count += 1

    def handle_data(self, data: str) -> None:
        if self._structured_script_parts is None:
            return
        if self._structured_script_chars + len(data) > _STRUCTURED_ATTRIBUTE_MAX_CHARS:
            self._structured_script_parts = None
            return
        self._structured_script_parts.append(data)
        self._structured_script_chars += len(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "script":
            return
        if self._structured_script_parts is not None:
            raw_payload = "".join(self._structured_script_parts).strip()
            if raw_payload:
                try:
                    payload = json.loads(raw_payload)
                except (json.JSONDecodeError, TypeError):
                    pass
                else:
                    self._extract_structured_payload_text(payload)
        self._structured_script_parts = None
        self._structured_script_chars = 0

    def _extract_structured_payload_text(self, payload: Any) -> None:
        node_count = 0
        stack: list[tuple[Any, str]] = [(payload, "")]
        while (
            stack
            and node_count < _STRUCTURED_NODE_MAX
            and len(self.sections) < _STRUCTURED_TEXT_MAX
            and self._total_chars < _STRUCTURED_TEXT_TOTAL_CHARS
        ):
            node, inherited_label = stack.pop()
            node_count += 1
            if isinstance(node, dict):
                product_label = _structured_node_label(node, inherited_label)
                pricing_label = next(
                    (
                        _strip_embedded_html(str(node[key]))
                        for key in _STRUCTURED_LABEL_KEYS
                        if isinstance(node.get(key), str)
                        and any(
                            marker in _strip_embedded_html(str(node[key])).lower()
                            for marker in _STRUCTURED_PRICING_LABEL_MARKERS
                        )
                    ),
                    "",
                )
                for key, item in node.items():
                    normalized_key = re.sub(r"[^a-z0-9]", "", str(key).lower())
                    if isinstance(item, str) and normalized_key in _STRUCTURED_TEXT_KEYS:
                        self._append(item)
                    elif (
                        isinstance(item, dict)
                        and normalized_key in _STRUCTURED_TEXT_KEYS
                        and (wrapped_value := _structured_wrapped_scalar(item)) is not None
                    ):
                        if normalized_key in {"title", "name", "headline", "productname", "accountname", "cardname"}:
                            self._append(str(wrapped_value))
                        elif product_label:
                            self._append(
                                f"{product_label} - {_humanize_structured_key(str(key))}: {wrapped_value}"
                            )
                        else:
                            self._append(str(wrapped_value))
                    elif isinstance(item, str) and normalized_key in _STRUCTURED_PRICING_KEYS:
                        self._append(f"{_humanize_structured_key(str(key))}: {item}")
                    elif (
                        isinstance(item, dict)
                        and normalized_key in _STRUCTURED_PRICING_KEYS
                        and (wrapped_value := _structured_wrapped_scalar(item)) is not None
                    ):
                        prefix = f"{product_label} - " if product_label else ""
                        self._append(
                            f"{prefix}{_humanize_structured_key(str(key))}: {wrapped_value}"
                        )
                    elif (
                        isinstance(item, (str, int, float))
                        and pricing_label
                        and normalized_key in {"amount", "displayvalue", "value"}
                    ):
                        self._append(f"{pricing_label}: {item}")
                    elif isinstance(item, (dict, list)):
                        stack.append((item, product_label))
            elif isinstance(node, list):
                stack.extend(
                    (item, inherited_label)
                    for item in reversed(node)
                    if isinstance(item, (dict, list))
                )

    def _append(self, value: str) -> None:
        text = _strip_embedded_html(value)
        if (
            len(text) < 2
            or text in self._seen
            or text.startswith(("http://", "https://", "/content/", "/etc/"))
        ):
            return
        remaining = _STRUCTURED_TEXT_TOTAL_CHARS - self._total_chars
        if remaining <= 0:
            return
        text = text[: min(4_000, remaining)]
        self._seen.add(text)
        self.sections.append(text)
        self._total_chars += len(text)


def extract_structured_text_sections(html_text: str) -> list[str]:
    parser = _StructuredTextExtractor()
    parser.feed(html_text)
    return parser.sections


def _humanize_structured_key(value: str) -> str:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    separated = re.sub(r"[_-]+", " ", separated)
    return " ".join(separated.split())


def _structured_node_label(node: dict[str, Any], inherited_label: str = "") -> str:
    """Read ordinary and CMS-wrapped labels without binding to one vendor.

    Sitecore and similar headless CMS payloads commonly represent a product
    title as `Title: {`jsonValue`: {`value`: `Essential`}}` while the sibling
    link is nested several objects deeper. Preserving that label is what turns
    a generic `Details` CTA into an exact-product source relationship.
    """

    normalized_items = {
        re.sub(r"[^a-z0-9]", "", str(key).lower()): value
        for key, value in node.items()
    }
    for key in _STRUCTURED_LABEL_KEYS:
        value = _structured_wrapped_scalar(normalized_items.get(key))
        if value is not None and str(value).strip():
            return _strip_embedded_html(str(value))
    for key in ("productname", "accountname", "cardname"):
        value = _structured_wrapped_scalar(normalized_items.get(key))
        if value is not None and str(value).strip():
            return _strip_embedded_html(str(value))
    return inherited_label


def _structured_wrapped_scalar(value: Any) -> str | int | float | None:
    """Unwrap bounded headless-CMS `value`/`jsonValue` scalar envelopes."""

    current = value
    for _ in range(5):
        if isinstance(current, (str, int, float)) and not isinstance(current, bool):
            return current
        if not isinstance(current, dict):
            return None
        normalized = {
            re.sub(r"[^a-z0-9]", "", str(key).lower()): item
            for key, item in current.items()
        }
        if "jsonvalue" in normalized:
            current = normalized["jsonvalue"]
            continue
        if "value" in normalized:
            current = normalized["value"]
            continue
        return None
    return None
