from __future__ import annotations

import ipaddress
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Union
from urllib.parse import urljoin
from urllib.parse import urlparse

from .url_utils import host_matches_allowed_domains


IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


@dataclass(frozen=True)
class FetchedResponse:
    body: bytes
    final_url: str
    content_type: str
    status_code: int
    headers: dict[str, str]
    fetched_at: str
    redirect_count: int


@dataclass(frozen=True)
class DiscoveryFetchPolicy:
    allowed_domains: tuple[str, ...]
    block_private_networks: bool = True
    timeout_seconds: int = 45
    user_agent: str = "FPDS/0.1 source-discovery"
    max_redirects: int = 5

    @classmethod
    def from_env(cls, *, extra_allowed_domains: tuple[str, ...] | list[str] = ()) -> "DiscoveryFetchPolicy":
        import os

        raw_allowlist = os.getenv("FPDS_SOURCE_FETCH_ALLOWLIST", "td.com,tdcanadatrust.com")
        allowlist = [
            domain.strip().lower()
            for domain in raw_allowlist.split(",")
            if domain.strip()
        ]
        allowlist.extend(
            domain.strip().lower()
            for domain in extra_allowed_domains
            if str(domain).strip()
        )
        allowed_domains = tuple(dict.fromkeys(allowlist))
        block_private = os.getenv("FPDS_SOURCE_FETCH_BLOCK_PRIVATE_NETWORKS", "true").strip().lower() != "false"
        timeout_raw = os.getenv("FPDS_SOURCE_FETCH_TIMEOUT_SECONDS", "45").strip()
        try:
            timeout_seconds = max(5, int(timeout_raw))
        except ValueError:
            timeout_seconds = 45
        return cls(
            allowed_domains=allowed_domains,
            block_private_networks=block_private,
            timeout_seconds=timeout_seconds,
        )


def fetch_text(url: str, policy: DiscoveryFetchPolicy) -> str:
    response = fetch_response(url, policy)
    charset = _get_charset(response.headers.get("content-type", ""))
    return response.body.decode(charset, errors="replace")


def fetch_bytes(url: str, policy: DiscoveryFetchPolicy) -> bytes:
    return fetch_response(url, policy).body


def fetch_response(url: str, policy: DiscoveryFetchPolicy) -> FetchedResponse:
    validate_fetch_url(url, policy)
    redirect_handler = _AllowlistRedirectHandler(policy)
    opener = urllib.request.build_opener(redirect_handler)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": policy.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.1",
        },
    )
    try:
        with opener.open(request, timeout=policy.timeout_seconds) as response:
            final_url = response.geturl()
            validate_fetch_url(final_url, policy)
            headers = {key.lower(): value for key, value in response.headers.items()}
            content_type = response.headers.get_content_type() or "application/octet-stream"
            status_code = getattr(response, "status", 200)
            return FetchedResponse(
                body=response.read(),
                final_url=final_url,
                content_type=content_type,
                status_code=status_code,
                headers=headers,
                fetched_at=datetime.now(UTC).isoformat(),
                redirect_count=redirect_handler.redirect_count,
            )
    except urllib.error.HTTPError as exc:
        raise ValueError(f"HTTP fetch failed with status {exc.code} for {url}") from exc


def validate_fetch_url(url: str, policy: DiscoveryFetchPolicy) -> None:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        raise ValueError(f"Discovery fetch requires https URLs: {url}")
    if not parsed.hostname:
        raise ValueError(f"Discovery fetch requires a hostname: {url}")
    if not host_matches_allowed_domains(parsed.hostname, policy.allowed_domains):
        raise ValueError(f"Host not in discovery fetch allowlist: {parsed.hostname}")
    if policy.block_private_networks:
        _assert_public_host(parsed.hostname)


def _assert_public_host(hostname: str) -> None:
    try:
        addr_info = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve hostname: {hostname}") from exc

    for item in addr_info:
        raw_ip = item[4][0]
        ip = ipaddress.ip_address(raw_ip)
        if _is_private_or_blocked(ip):
            raise ValueError(f"Resolved private or blocked address for hostname {hostname}: {raw_ip}")


def _is_private_or_blocked(ip: IPAddress) -> bool:
    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        )
    )


def _get_charset(content_type: str) -> str:
    lower = content_type.lower()
    marker = "charset="
    if marker not in lower:
        return "utf-8"
    _, charset = lower.split(marker, 1)
    return charset.strip().strip('"').strip("'") or "utf-8"


class _AllowlistRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, policy: DiscoveryFetchPolicy):
        super().__init__()
        self.policy = policy
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        if self.redirect_count > self.policy.max_redirects:
            raise ValueError(f"Redirect limit exceeded for {req.full_url}")
        resolved_url = urljoin(req.full_url, newurl)
        validate_fetch_url(resolved_url, self.policy)
        return super().redirect_request(req, fp, code, msg, headers, newurl)
