from __future__ import annotations

from hashlib import sha1
import re
from urllib.parse import ParseResult, parse_qsl, urlencode, urlparse, urlunparse


_SOURCE_IDENTITY_QUERY_KEYS = {
    "accountid",
    "accounttype",
    "agreementid",
    "cardid",
    "disclosureid",
    "documentid",
    "market",
    "product",
    "productcode",
    "product_code",
    "subproduct_code",
    "fpid",
    "productid",
    "region",
    "state",
    "zip",
    "zipcode",
}
_DISCLOSURE_IDENTITY_QUERY_KEYS = {"cid", "offerid", "pocd", "doc", "form", "file", "id"}
_DISCLOSURE_PATH_MARKERS = (
    "agreement",
    "disclosure",
    "fee",
    "pdf",
    "pricing",
    "rate",
    "terms",
)


def normalize_source_url(url: str) -> str:
    """Normalize public source URLs without collapsing priced documents.

    Tracking, presentation, and locale parameters do not define a source and
    remain excluded. A bounded set of product/document and market parameters
    is retained because many banks expose every card disclosure or local rate
    sheet through one path whose query is the only official document identity.
    """
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
        query=_normalize_identity_query(parsed.query, path=path),
        fragment="",
    )
    return urlunparse(normalized)


def infer_source_type(url: str) -> str:
    parsed = urlparse(url)
    if parsed.path.lower().endswith(".pdf") or parsed.path.lower().rstrip("/").split("/")[-1] == "pdf":
        return "pdf"
    return "html"


def build_source_identity(bank_code: str, normalized_source_url: str, source_type: str) -> str:
    return f"{bank_code}|{normalized_source_url}|{source_type}"


def build_source_document_id(bank_code: str, normalized_source_url: str, source_type: str) -> str:
    identity = build_source_identity(bank_code, normalized_source_url, source_type)
    digest = sha1(identity.encode("utf-8")).hexdigest()[:16]
    return f"src-{bank_code.lower()}-{source_type}-{digest}"


def host_matches_allowed_domains(hostname: str, allowed_domains: tuple[str, ...]) -> bool:
    host = hostname.lower()
    for allowed in allowed_domains:
        domain = allowed.lower()
        if host == domain:
            return True
        if host.endswith(f".{domain}"):
            return True
    return False


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

    while "//" in path:
        path = path.replace("//", "/")

    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return path


def _normalize_identity_query(query: str, *, path: str) -> str:
    if not query:
        return ""
    lowered_path = path.lower()
    disclosure_path = any(marker in lowered_path for marker in _DISCLOSURE_PATH_MARKERS)
    kept: list[tuple[str, str]] = []
    for key, value in parse_qsl(query, keep_blank_values=False):
        normalized_key = key.strip().lower()
        normalized_value = value.strip()
        if not normalized_value:
            continue
        if normalized_key in _SOURCE_IDENTITY_QUERY_KEYS or (
            disclosure_path and normalized_key in _DISCLOSURE_IDENTITY_QUERY_KEYS
        ):
            kept.append((normalized_key, normalized_value))
    kept.sort(key=lambda item: (item[0], item[1]))
    return urlencode(kept, doseq=True)


def url_locale_conflicts_source_language(*, normalized_url: str, source_language: str) -> bool:
    """Reject a clearly different locale host or path from an allowed domain."""

    requested = str(source_language or "").strip().lower().replace("_", "-").split("-", 1)[0]
    if not requested:
        return False
    known_languages = {"en", "fr", "es", "de", "it", "pt", "zh", "ja", "ko"}
    parsed = urlparse(normalized_url)
    hostname_labels = [item for item in str(parsed.hostname or "").lower().split(".") if item]
    if hostname_labels:
        host_locale = {"zt": "zh"}.get(hostname_labels[0], hostname_labels[0])
        if host_locale in known_languages and host_locale != requested:
            return True
    for segment in [item for item in parsed.path.lower().split("/") if item]:
        locale = segment.replace("_", "-").split("-", 1)[0]
        if locale in known_languages and locale != requested:
            return True
    return False


def url_country_scope_conflicts(*, country_code: str, normalized_url: str) -> bool:
    """Reject an explicit market route that conflicts with the collection country.

    Some banks serve Canada and the United States from one registered domain.
    Domain allowlisting therefore is not enough: `/ca/...` must never enter a
    US run and `/us/...` must never enter a Canada run. Unmarked shared legal or
    disclosure paths remain eligible as supporting evidence.
    """

    requested = str(country_code or "").strip().lower()
    if not requested:
        return False
    known_markets = {"ca", "us", "ph"}
    parsed = urlparse(str(normalized_url or ""))
    hostname = str(parsed.hostname or "").lower().strip(".")
    segments = [segment.lower().replace("_", "-") for segment in parsed.path.split("/") if segment]
    explicit_markets: set[str] = set()
    host_labels = [label for label in hostname.split(".") if label]
    if host_labels and host_labels[0] in known_markets:
        explicit_markets.add(host_labels[0])
    if host_labels and host_labels[-1] in known_markets:
        explicit_markets.add(host_labels[-1])
    for key, value in parse_qsl(parsed.query):
        if key.casefold() == "market" and value.casefold() in known_markets:
            explicit_markets.add(value.casefold())
    for segment in segments[:3]:
        if segment in known_markets:
            explicit_markets.add(segment)
        locale_match = re.fullmatch(r"[a-z]{2}-(ca|us|ph)", segment)
        if locale_match:
            explicit_markets.add(locale_match.group(1))
    return bool(explicit_markets - {requested})
