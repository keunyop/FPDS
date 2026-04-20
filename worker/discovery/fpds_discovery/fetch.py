from __future__ import annotations

import ipaddress
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
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
    timeout_seconds: int = 90
    user_agent: str = "FPDS/0.1 source-discovery"
    max_redirects: int = 5
    browser_fallback_domains: tuple[str, ...] = ()
    browser_fallback_timeout_seconds: int = 120
    browser_executable: str | None = None

    @classmethod
    def from_env(cls, *, extra_allowed_domains: tuple[str, ...] | list[str] = ()) -> "DiscoveryFetchPolicy":
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
        timeout_raw = os.getenv("FPDS_SOURCE_FETCH_TIMEOUT_SECONDS", "90").strip()
        try:
            timeout_seconds = max(5, int(timeout_raw))
        except ValueError:
            timeout_seconds = 90
        raw_browser_domains = os.getenv(
            "FPDS_SOURCE_BROWSER_FALLBACK_DOMAINS",
            "bmo.com,www.bmo.com",
        )
        browser_fallback_domains = tuple(
            dict.fromkeys(
                domain.strip().lower()
                for domain in raw_browser_domains.split(",")
                if domain.strip()
            )
        )
        browser_timeout_raw = os.getenv("FPDS_SOURCE_BROWSER_FALLBACK_TIMEOUT_SECONDS", "120").strip()
        try:
            browser_fallback_timeout_seconds = max(15, int(browser_timeout_raw))
        except ValueError:
            browser_fallback_timeout_seconds = 120
        browser_executable = os.getenv("FPDS_SOURCE_BROWSER_EXECUTABLE", "").strip() or None
        return cls(
            allowed_domains=allowed_domains,
            block_private_networks=block_private,
            timeout_seconds=timeout_seconds,
            browser_fallback_domains=browser_fallback_domains,
            browser_fallback_timeout_seconds=browser_fallback_timeout_seconds,
            browser_executable=browser_executable,
        )


def fetch_text(url: str, policy: DiscoveryFetchPolicy) -> str:
    response = fetch_response(url, policy)
    normalized_content_type = response.content_type.lower().strip()
    if not normalized_content_type.startswith(("text/html", "application/xhtml+xml")):
        raise ValueError(f"Text fetch expected HTML content but received {response.content_type} for {url}")
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
        if _should_try_browser_fallback(url, policy, exc):
            return _fetch_response_via_browser(url, policy)
        raise ValueError(f"HTTP fetch failed with status {exc.code} for {url}") from exc
    except Exception as exc:
        if _should_try_browser_fallback(url, policy, exc):
            return _fetch_response_via_browser(url, policy)
        raise


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


def _should_try_browser_fallback(url: str, policy: DiscoveryFetchPolicy, exc: Exception) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False
    if parsed.path.lower().endswith(".pdf"):
        return False
    if not policy.browser_fallback_domains:
        return False
    if not host_matches_allowed_domains(hostname, policy.browser_fallback_domains):
        return False
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in {403, 408, 425, 429, 500, 502, 503, 504}
    if isinstance(exc, (TimeoutError, socket.timeout, ConnectionResetError, ConnectionAbortedError)):
        return True
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        return isinstance(reason, (TimeoutError, socket.timeout, ConnectionResetError, ConnectionAbortedError))
    return False


def _fetch_response_via_browser(url: str, policy: DiscoveryFetchPolicy) -> FetchedResponse:
    browser_executable = _resolve_browser_executable(policy.browser_executable)
    if browser_executable is None:
        raise RuntimeError(
            "Browser fallback fetch was requested but no supported browser executable was found. "
            "Set FPDS_SOURCE_BROWSER_EXECUTABLE to msedge.exe or chrome.exe."
        )

    with tempfile.TemporaryDirectory(prefix="fpds-browser-fetch-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        output_path = temp_dir / "snapshot.pdf"
        profile_path = temp_dir / "profile"
        command = [
            browser_executable,
            "--headless=new",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-blink-features=AutomationControlled",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=15000",
            "--no-pdf-header-footer",
            "--window-size=1440,2200",
            (
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0"
            ),
            f"--user-data-dir={profile_path}",
            f"--print-to-pdf={output_path}",
            url,
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=policy.browser_fallback_timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown browser error"
            raise RuntimeError(f"Browser fallback fetch failed for {url}: {stderr}")
        if not output_path.exists():
            raise RuntimeError(f"Browser fallback fetch did not produce a PDF snapshot for {url}.")
        body = output_path.read_bytes()
        if not body:
            raise RuntimeError(f"Browser fallback fetch produced an empty PDF snapshot for {url}.")
        return FetchedResponse(
            body=body,
            final_url=url,
            content_type="application/pdf",
            status_code=200,
            headers={
                "content-type": "application/pdf",
                "x-fpds-fetch-method": "browser_pdf_fallback",
                "x-fpds-browser-executable": Path(browser_executable).name,
            },
            fetched_at=datetime.now(UTC).isoformat(),
            redirect_count=0,
        )


def _resolve_browser_executable(explicit_executable: str | None) -> str | None:
    candidates = [
        explicit_executable,
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "msedge.exe",
        "chrome.exe",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        if Path(candidate).is_file():
            return candidate
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None
