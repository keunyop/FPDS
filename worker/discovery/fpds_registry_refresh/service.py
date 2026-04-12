from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from worker.discovery.fpds_discovery.discovery import DiscoveryResult, SourceDiscoveryService
from worker.discovery.fpds_discovery.drift import PreflightDriftResult, RegistryPreflightDriftService
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, fetch_text
from worker.discovery.fpds_discovery.registry import SourceRegistry
from worker.discovery.fpds_snapshot.capture import CaptureSource


@dataclass(frozen=True)
class RegistryRefreshCandidateDiff:
    change_type: str
    severity: str
    source_id: str | None
    source_document_id: str | None
    discovery_role: str | None
    source_type: str | None
    expected_url: str | None
    detected_url: str | None
    discovered_on_url: str | None
    message: str
    recommended_action: str


@dataclass(frozen=True)
class RegistryRefreshResult:
    run_id: str
    correlation_id: str | None
    registry_version: str
    candidate_diffs: list[RegistryRefreshCandidateDiff]
    discovery_result: DiscoveryResult
    preflight_result: PreflightDriftResult

    def to_dict(self) -> dict[str, object]:
        change_counts: dict[str, int] = {}
        for item in self.candidate_diffs:
            change_counts[item.change_type] = change_counts.get(item.change_type, 0) + 1
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "registry_version": self.registry_version,
            "stats": {
                "candidate_diff_total": len(self.candidate_diffs),
                "candidate_diffs_by_type": change_counts,
            },
            "candidate_diffs": [item.__dict__ for item in self.candidate_diffs],
            "discovery": self.discovery_result.to_dict(),
            "preflight": self.preflight_result.to_dict(),
        }


class RegistryRefreshService:
    def __init__(
        self,
        *,
        registry: SourceRegistry,
        fetch_policy: DiscoveryFetchPolicy,
        html_loader: Callable[[str], str] | None = None,
        discovery_service: SourceDiscoveryService | None = None,
        preflight_service: RegistryPreflightDriftService | None = None,
    ):
        self.registry = registry
        self.fetch_policy = fetch_policy
        self.html_loader = html_loader or (lambda url: fetch_text(url, self.fetch_policy))
        self.discovery_service = discovery_service or SourceDiscoveryService(registry)
        self.preflight_service = preflight_service or RegistryPreflightDriftService(fetch_policy=fetch_policy)

    def refresh_live(
        self,
        *,
        run_id: str,
        correlation_id: str | None = None,
    ) -> RegistryRefreshResult:
        discovery_result = self.discovery_service.discover_live(
            html_loader=self.html_loader,
            run_id=run_id,
            correlation_id=correlation_id,
            discovery_mode="scheduled",
        )
        preflight_result = self.preflight_service.check_sources(
            run_id=run_id,
            correlation_id=correlation_id,
            sources=[CaptureSource.from_registry_source(source) for source in self.registry.sources],
        )
        return self.build_result(
            run_id=run_id,
            correlation_id=correlation_id,
            discovery_result=discovery_result,
            preflight_result=preflight_result,
        )

    def build_result(
        self,
        *,
        run_id: str,
        correlation_id: str | None,
        discovery_result: DiscoveryResult,
        preflight_result: PreflightDriftResult,
    ) -> RegistryRefreshResult:
        diffs_by_key: dict[tuple[str, str | None, str | None, str | None], RegistryRefreshCandidateDiff] = {}

        for check in preflight_result.checks:
            for issue in check.issues:
                diff = _diff_from_preflight_issue(
                    registry=self.registry,
                    issue_code=issue.issue_code,
                    source_id=check.source_id,
                    source_document_id=check.source_document_id,
                    expected_url=check.expected_url,
                    detected_url=check.normalized_final_url,
                    detected_content_type=check.content_type,
                )
                if diff is None:
                    continue
                diffs_by_key[_diff_key(diff)] = diff

        for warning in discovery_result.warnings:
            diff = _diff_from_discovery_warning(warning_code=warning.warning_code, warning_payload=warning.__dict__)
            if diff is None:
                continue
            diffs_by_key[_diff_key(diff)] = diff

        selected_by_id = {item.source_id: item for item in discovery_result.selected_sources}
        for source in self.registry.sources:
            if source.discovery_role not in {"detail", "linked_pdf"}:
                continue
            selected = selected_by_id[source.source_id]
            if selected.discovery_status != "seed_only":
                continue
            diff = RegistryRefreshCandidateDiff(
                change_type="source_missing_from_discovery",
                severity="warning",
                source_id=source.source_id,
                source_document_id=source.source_document_id,
                discovery_role=source.discovery_role,
                source_type=source.source_type,
                expected_url=source.normalized_url,
                detected_url=None,
                discovered_on_url=None,
                message="Approved registry source was not rediscovered during the scheduled refresh crawl.",
                recommended_action="Review whether the source moved, was delisted, or should be deprecated.",
            )
            diffs_by_key[_diff_key(diff)] = diff

        return RegistryRefreshResult(
            run_id=run_id,
            correlation_id=correlation_id,
            registry_version=self.registry.registry_version,
            candidate_diffs=sorted(
                diffs_by_key.values(),
                key=lambda item: (
                    item.severity,
                    item.change_type,
                    item.source_id or "",
                    item.expected_url or "",
                    item.detected_url or "",
                ),
            ),
            discovery_result=discovery_result,
            preflight_result=preflight_result,
        )


def _diff_key(item: RegistryRefreshCandidateDiff) -> tuple[str, str | None, str | None, str | None]:
    return (
        item.change_type,
        item.source_id,
        item.expected_url,
        item.detected_url,
    )


def _diff_from_preflight_issue(
    *,
    registry: SourceRegistry,
    issue_code: str,
    source_id: str,
    source_document_id: str,
    expected_url: str,
    detected_url: str | None,
    detected_content_type: str | None,
) -> RegistryRefreshCandidateDiff | None:
    registry_source = registry.by_source_id(source_id)
    if issue_code == "final_url_changed":
        return RegistryRefreshCandidateDiff(
            change_type="redirect_detected",
            severity="warning",
            source_id=source_id,
            source_document_id=source_document_id,
            discovery_role=registry_source.discovery_role,
            source_type=registry_source.source_type,
            expected_url=expected_url,
            detected_url=detected_url,
            discovered_on_url=None,
            message="Approved source resolved to a different final URL during preflight.",
            recommended_action="Review the redirect target and approve a registry URL update only if it is the same logical source.",
        )
    if issue_code == "content_type_changed":
        return RegistryRefreshCandidateDiff(
            change_type="content_type_changed",
            severity="warning",
            source_id=source_id,
            source_document_id=source_document_id,
            discovery_role=registry_source.discovery_role,
            source_type=registry_source.source_type,
            expected_url=expected_url,
            detected_url=detected_url,
            discovered_on_url=None,
            message=f"Approved source returned unexpected content type: {detected_content_type or 'unknown'}.",
            recommended_action="Review whether the source changed format or if the registry source type is now stale.",
        )
    if issue_code == "fetch_failed":
        return RegistryRefreshCandidateDiff(
            change_type="source_unreachable",
            severity="error",
            source_id=source_id,
            source_document_id=source_document_id,
            discovery_role=registry_source.discovery_role,
            source_type=registry_source.source_type,
            expected_url=expected_url,
            detected_url=None,
            discovered_on_url=None,
            message="Approved source could not be fetched during preflight.",
            recommended_action="Review source availability before the next promotion or deprecation decision.",
        )
    return None


def _diff_from_discovery_warning(
    *,
    warning_code: str,
    warning_payload: dict[str, object],
) -> RegistryRefreshCandidateDiff | None:
    if warning_code != "out_of_registry_link":
        return None
    return RegistryRefreshCandidateDiff(
        change_type="new_source_candidate",
        severity="warning",
        source_id=None,
        source_document_id=None,
        discovery_role=None,
        source_type=str(warning_payload.get("source_type") or ""),
        expected_url=None,
        detected_url=str(warning_payload.get("normalized_target_url") or warning_payload.get("target_url") or ""),
        discovered_on_url=str(warning_payload.get("discovered_on_url") or ""),
        message=str(warning_payload.get("message") or "Scheduled refresh discovered an out-of-registry link."),
        recommended_action="Review whether this link should stay excluded, become an alias, or be promoted as a new candidate source.",
    )
