from __future__ import annotations

from hashlib import sha1
from urllib.parse import ParseResult, urlparse, urlunparse


def normalize_source_url(url: str) -> str:
    """Normalize TD source URLs for source identity and dedupe."""
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
