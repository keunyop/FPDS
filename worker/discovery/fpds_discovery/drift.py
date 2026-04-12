from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, Sequence

from .fetch import DiscoveryFetchPolicy, FetchedResponse, fetch_response
from .url_utils import normalize_source_url

_HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")


class SourceLike(Protocol):
    source_id: str
    source_document_id: str
    resolved_url: str
    normalized_source_url: str
    source_type: str


@dataclass(frozen=True)
class DriftIssue:
    source_id: str
    source_document_id: str
    issue_code: str
    severity: str
    expected_url: str
    detected_url: str | None
    expected_source_type: str
    detected_content_type: str | None
    message: str


@dataclass(frozen=True)
class SourcePreflightCheck:
    source_id: str
    source_document_id: str
    expected_url: str
    expected_source_type: str
    status: str
    fetched_at: str | None
    final_url: str | None
    normalized_final_url: str | None
    status_code: int | None
    content_type: str | None
    redirect_count: int | None
    error_summary: str | None
    issues: list[DriftIssue]


@dataclass(frozen=True)
class PreflightDriftResult:
    run_id: str
    correlation_id: str | None
    request_id: str | None
    checks: list[SourcePreflightCheck]

    def to_dict(self) -> dict[str, object]:
        issue_total = sum(len(item.issues) for item in self.checks)
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "stats": {
                "source_total": len(self.checks),
                "ok_count": sum(1 for item in self.checks if item.status == "ok"),
                "warning_count": sum(1 for item in self.checks if item.status == "warning"),
                "error_count": sum(1 for item in self.checks if item.status == "error"),
                "issue_total": issue_total,
            },
            "source_checks": [
                {
                    **item.__dict__,
                    "issues": [issue.__dict__ for issue in item.issues],
                }
                for item in self.checks
            ],
        }

    def issues_for_source_document(self, source_document_id: str) -> list[DriftIssue]:
        for item in self.checks:
            if item.source_document_id == source_document_id:
                return list(item.issues)
        return []

    def status_for_source_document(self, source_document_id: str) -> str | None:
        for item in self.checks:
            if item.source_document_id == source_document_id:
                return item.status
        return None


class RegistryPreflightDriftService:
    def __init__(
        self,
        *,
        fetch_policy: DiscoveryFetchPolicy,
        fetcher: Callable[[str, DiscoveryFetchPolicy], FetchedResponse] = fetch_response,
    ):
        self.fetch_policy = fetch_policy
        self.fetcher = fetcher

    def check_sources(
        self,
        *,
        run_id: str,
        sources: Sequence[SourceLike],
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> PreflightDriftResult:
        checks = [self._check_source(source) for source in sources]
        return PreflightDriftResult(
            run_id=run_id,
            correlation_id=correlation_id,
            request_id=request_id,
            checks=checks,
        )

    def _check_source(self, source: SourceLike) -> SourcePreflightCheck:
        try:
            fetched = self.fetcher(source.resolved_url, self.fetch_policy)
        except Exception as exc:
            issue = DriftIssue(
                source_id=source.source_id,
                source_document_id=source.source_document_id,
                issue_code="fetch_failed",
                severity="error",
                expected_url=source.normalized_source_url,
                detected_url=None,
                expected_source_type=source.source_type,
                detected_content_type=None,
                message=str(exc),
            )
            return SourcePreflightCheck(
                source_id=source.source_id,
                source_document_id=source.source_document_id,
                expected_url=source.normalized_source_url,
                expected_source_type=source.source_type,
                status="error",
                fetched_at=None,
                final_url=None,
                normalized_final_url=None,
                status_code=None,
                content_type=None,
                redirect_count=None,
                error_summary=str(exc),
                issues=[issue],
            )

        issues: list[DriftIssue] = []
        normalized_final_url = normalize_source_url(fetched.final_url)
        if normalized_final_url != source.normalized_source_url:
            issues.append(
                DriftIssue(
                    source_id=source.source_id,
                    source_document_id=source.source_document_id,
                    issue_code="final_url_changed",
                    severity="warning",
                    expected_url=source.normalized_source_url,
                    detected_url=normalized_final_url,
                    expected_source_type=source.source_type,
                    detected_content_type=fetched.content_type,
                    message="Final fetched URL differs from the approved active registry URL.",
                )
            )
        if not _content_type_matches(source.source_type, fetched.content_type):
            issues.append(
                DriftIssue(
                    source_id=source.source_id,
                    source_document_id=source.source_document_id,
                    issue_code="content_type_changed",
                    severity="warning",
                    expected_url=source.normalized_source_url,
                    detected_url=normalized_final_url,
                    expected_source_type=source.source_type,
                    detected_content_type=fetched.content_type,
                    message="Fetched content type does not match the registry source type.",
                )
            )

        return SourcePreflightCheck(
            source_id=source.source_id,
            source_document_id=source.source_document_id,
            expected_url=source.normalized_source_url,
            expected_source_type=source.source_type,
            status="warning" if issues else "ok",
            fetched_at=fetched.fetched_at,
            final_url=fetched.final_url,
            normalized_final_url=normalized_final_url,
            status_code=fetched.status_code,
            content_type=fetched.content_type,
            redirect_count=fetched.redirect_count,
            error_summary=None,
            issues=issues,
        )


def _content_type_matches(source_type: str, content_type: str) -> bool:
    normalized = content_type.lower().strip()
    if source_type == "pdf":
        return normalized.startswith("application/pdf")
    if source_type == "html":
        return normalized.startswith(_HTML_CONTENT_TYPES)
    return True
