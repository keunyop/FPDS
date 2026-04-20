from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from hashlib import sha256
from typing import Callable

from worker.discovery.fpds_discovery.drift import PreflightDriftResult
from worker.discovery.fpds_discovery.fetch import (
    DiscoveryFetchPolicy,
    FetchedResponse,
    fetch_response,
)
from worker.discovery.fpds_discovery.registry import RegistrySource

from .storage import SnapshotObjectStore, SnapshotStorageConfig


@dataclass(frozen=True)
class CaptureSource:
    source_id: str
    source_document_id: str
    resolved_url: str
    normalized_source_url: str
    source_type: str
    source_language: str
    bank_code: str
    country_code: str
    priority: str
    registry_managed_flag: bool
    source_metadata: dict[str, object]

    @classmethod
    def from_registry_source(cls, source: RegistrySource) -> "CaptureSource":
        record = source.to_source_document_record()
        return cls(
            source_id=source.source_id,
            source_document_id=source.source_document_id,
            resolved_url=source.url,
            normalized_source_url=source.normalized_url,
            source_type=source.source_type,
            source_language=source.source_language,
            bank_code=source.bank_code,
            country_code=source.country_code,
            priority=source.priority,
            registry_managed_flag=bool(record["registry_managed_flag"]),
            source_metadata=dict(record["source_metadata"]),
        )

    @classmethod
    def from_discovery_item(cls, item: object) -> "CaptureSource":
        return cls(
            source_id=str(getattr(item, "source_id")),
            source_document_id=str(getattr(item, "source_document_id")),
            resolved_url=str(getattr(item, "resolved_url")),
            normalized_source_url=str(getattr(item, "normalized_source_url")),
            source_type=str(getattr(item, "source_type")),
            source_language=str(getattr(item, "source_language")),
            bank_code=str(getattr(item, "bank_code")),
            country_code=str(getattr(item, "country_code")),
            priority=str(getattr(item, "priority")),
            registry_managed_flag=bool(getattr(item, "registry_managed_flag", False)),
            source_metadata=dict(getattr(item, "source_metadata", {})),
        )

    def to_source_document_record(self, *, discovered_at: str) -> dict[str, object]:
        return {
            "source_document_id": self.source_document_id,
            "bank_code": self.bank_code,
            "country_code": self.country_code,
            "normalized_source_url": self.normalized_source_url,
            "source_type": self.source_type,
            "source_language": self.source_language,
            "registry_managed_flag": self.registry_managed_flag,
            "source_metadata": self.source_metadata,
            "discovered_at": discovered_at,
        }


@dataclass(frozen=True)
class ExistingSnapshotRecord:
    snapshot_id: str
    source_document_id: str
    object_storage_key: str
    content_type: str
    checksum: str
    fingerprint: str
    fetch_status: str
    response_metadata: dict[str, object]
    retention_class: str
    fetched_at: str

    @property
    def dedupe_key(self) -> tuple[str, str]:
        return (self.source_document_id, self.fingerprint)


@dataclass(frozen=True)
class SnapshotSourceResult:
    source_id: str
    source_document_id: str
    snapshot_action: str
    attempt_count: int
    snapshot_id: str | None
    object_storage_key: str | None
    checksum: str | None
    fingerprint: str | None
    content_type: str | None
    fetch_status: str | None
    fetched_at: str | None
    error_summary: str | None
    source_snapshot_record: dict[str, object] | None
    run_source_item_record: dict[str, object]


@dataclass(frozen=True)
class SnapshotCaptureResult:
    run_id: str
    correlation_id: str | None
    request_id: str | None
    source_results: list[SnapshotSourceResult]
    partial_completion_flag: bool
    preflight_result: PreflightDriftResult | None = None

    def to_dict(self) -> dict[str, object]:
        stored_count = sum(1 for item in self.source_results if item.snapshot_action == "stored")
        reused_count = sum(1 for item in self.source_results if item.snapshot_action == "reused")
        failed_count = sum(1 for item in self.source_results if item.snapshot_action == "failed")
        payload = {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "partial_completion_flag": self.partial_completion_flag,
            "stats": {
                "source_total": len(self.source_results),
                "stored_count": stored_count,
                "reused_count": reused_count,
                "failed_count": failed_count,
            },
            "source_results": [item.__dict__ for item in self.source_results],
        }
        if self.preflight_result is not None:
            payload["preflight"] = self.preflight_result.to_dict()
        return payload


class SnapshotCaptureService:
    def __init__(
        self,
        *,
        fetch_policy: DiscoveryFetchPolicy,
        storage_config: SnapshotStorageConfig,
        object_store: SnapshotObjectStore,
        fetcher: Callable[[str, DiscoveryFetchPolicy], FetchedResponse] = fetch_response,
        max_attempts: int = 3,
        max_concurrency: int = 4,
    ):
        self.fetch_policy = fetch_policy
        self.storage_config = storage_config
        self.object_store = object_store
        self.fetcher = fetcher
        self.max_attempts = max_attempts
        self.max_concurrency = max(1, max_concurrency)

    def capture_sources(
        self,
        *,
        run_id: str,
        sources: list[CaptureSource],
        correlation_id: str | None = None,
        request_id: str | None = None,
        existing_snapshots: list[ExistingSnapshotRecord] | None = None,
        preflight_result: PreflightDriftResult | None = None,
    ) -> SnapshotCaptureResult:
        known_snapshots = {
            record.dedupe_key: record for record in (existing_snapshots or [])
        }
        if self.max_concurrency <= 1 or len(sources) <= 1:
            source_results = [
                self._capture_single_source(
                    run_id=run_id,
                    source=source,
                    correlation_id=correlation_id,
                    request_id=request_id,
                    known_snapshots=known_snapshots,
                    preflight_result=preflight_result,
                )
                for source in sources
            ]
        else:
            with ThreadPoolExecutor(max_workers=min(self.max_concurrency, len(sources))) as executor:
                futures = [
                    executor.submit(
                        self._capture_single_source,
                        run_id=run_id,
                        source=source,
                        correlation_id=correlation_id,
                        request_id=request_id,
                        known_snapshots=dict(known_snapshots),
                        preflight_result=preflight_result,
                    )
                    for source in sources
                ]
                source_results = [future.result() for future in futures]

        partial_completion_flag = False
        for result in source_results:
            if result.snapshot_action == "stored" and result.source_snapshot_record is not None:
                record = ExistingSnapshotRecord(**result.source_snapshot_record)
                known_snapshots[record.dedupe_key] = record
            if result.snapshot_action == "failed":
                partial_completion_flag = True

        return SnapshotCaptureResult(
            run_id=run_id,
            correlation_id=correlation_id,
            request_id=request_id,
            source_results=source_results,
            partial_completion_flag=partial_completion_flag,
            preflight_result=preflight_result,
        )

    def _capture_single_source(
        self,
        *,
        run_id: str,
        source: CaptureSource,
        correlation_id: str | None,
        request_id: str | None,
        known_snapshots: dict[tuple[str, str], ExistingSnapshotRecord],
        preflight_result: PreflightDriftResult | None,
    ) -> SnapshotSourceResult:
        attempt_count = 0
        last_error: str | None = None
        preflight_issues = preflight_result.issues_for_source_document(source.source_document_id) if preflight_result is not None else []
        preflight_status = preflight_result.status_for_source_document(source.source_document_id) if preflight_result is not None else None
        preflight_issue_codes = [issue.issue_code for issue in preflight_issues]

        while attempt_count < self.max_attempts:
            attempt_count += 1
            try:
                fetched = self.fetcher(source.resolved_url, self.fetch_policy)
                checksum = _build_checksum(fetched.body)
                fingerprint = _build_fingerprint(fetched.body, fetched.content_type)
                known = known_snapshots.get((source.source_document_id, fingerprint))
                if known is not None:
                    return self._build_reused_result(
                        run_id=run_id,
                        source=source,
                        attempt_count=attempt_count,
                        correlation_id=correlation_id,
                        request_id=request_id,
                        fetched=fetched,
                        known=known,
                        preflight_warning_count=len(preflight_issues),
                        preflight_status=preflight_status,
                        preflight_issue_codes=preflight_issue_codes,
                    )

                snapshot_id = _build_snapshot_id(source.source_document_id, fingerprint)
                object_key = self.storage_config.build_snapshot_object_key(
                    country_code=source.country_code,
                    bank_code=source.bank_code,
                    source_document_id=source.source_document_id,
                    snapshot_id=snapshot_id,
                )
                self.object_store.put_object(
                    object_key=object_key,
                    data=fetched.body,
                    content_type=fetched.content_type,
                )
                response_metadata = _build_response_metadata(
                    source=source,
                    fetched=fetched,
                    attempt_count=attempt_count,
                )
                snapshot_record = {
                    "snapshot_id": snapshot_id,
                    "source_document_id": source.source_document_id,
                    "object_storage_key": object_key,
                    "content_type": fetched.content_type,
                    "checksum": checksum,
                    "fingerprint": fingerprint,
                    "fetch_status": "fetched",
                    "response_metadata": response_metadata,
                    "retention_class": self.storage_config.retention_class,
                    "fetched_at": fetched.fetched_at,
                }
                return SnapshotSourceResult(
                    source_id=source.source_id,
                    source_document_id=source.source_document_id,
                    snapshot_action="stored",
                    attempt_count=attempt_count,
                    snapshot_id=snapshot_id,
                    object_storage_key=object_key,
                    checksum=checksum,
                    fingerprint=fingerprint,
                    content_type=fetched.content_type,
                    fetch_status="fetched",
                    fetched_at=fetched.fetched_at,
                    error_summary=None,
                    source_snapshot_record=snapshot_record,
                    run_source_item_record=_build_run_source_item_record(
                        run_id=run_id,
                        source=source,
                        snapshot_id=snapshot_id,
                        stage_status="completed",
                        warning_count=len(preflight_issues),
                        error_count=0,
                        error_summary=None,
                        stage_metadata={
                            "snapshot_action": "stored",
                            "request_id": request_id,
                            "content_type": fetched.content_type,
                            "checksum": checksum,
                            "fingerprint": fingerprint,
                            "object_storage_key": object_key,
                            "correlation_id": correlation_id,
                            "attempt_count": attempt_count,
                            "preflight_status": preflight_status,
                            "preflight_issue_codes": preflight_issue_codes,
                        },
                    ),
                )
            except Exception as exc:
                last_error = str(exc)

        return SnapshotSourceResult(
            source_id=source.source_id,
            source_document_id=source.source_document_id,
            snapshot_action="failed",
            attempt_count=attempt_count,
            snapshot_id=None,
            object_storage_key=None,
            checksum=None,
            fingerprint=None,
            content_type=None,
            fetch_status=None,
            fetched_at=None,
            error_summary=last_error,
            source_snapshot_record=None,
            run_source_item_record=_build_run_source_item_record(
                run_id=run_id,
                source=source,
                snapshot_id=None,
                stage_status="failed",
                warning_count=len(preflight_issues),
                error_count=attempt_count,
                error_summary=last_error,
                stage_metadata={
                    "snapshot_action": "failed",
                    "request_id": request_id,
                    "attempt_count": attempt_count,
                    "correlation_id": correlation_id,
                    "requested_url": source.resolved_url,
                    "preflight_status": preflight_status,
                    "preflight_issue_codes": preflight_issue_codes,
                },
            ),
        )

    def _build_reused_result(
        self,
        *,
        run_id: str,
        source: CaptureSource,
        attempt_count: int,
        correlation_id: str | None,
        request_id: str | None,
        fetched: FetchedResponse,
        known: ExistingSnapshotRecord,
        preflight_warning_count: int = 0,
        preflight_status: str | None = None,
        preflight_issue_codes: list[str] | None = None,
    ) -> SnapshotSourceResult:
        return SnapshotSourceResult(
            source_id=source.source_id,
            source_document_id=source.source_document_id,
            snapshot_action="reused",
            attempt_count=attempt_count,
            snapshot_id=known.snapshot_id,
            object_storage_key=known.object_storage_key,
            checksum=known.checksum,
            fingerprint=known.fingerprint,
            content_type=known.content_type,
            fetch_status="reused",
            fetched_at=fetched.fetched_at,
            error_summary=None,
            source_snapshot_record=None,
            run_source_item_record=_build_run_source_item_record(
                run_id=run_id,
                source=source,
                snapshot_id=known.snapshot_id,
                stage_status="completed",
                warning_count=preflight_warning_count,
                error_count=0,
                error_summary=None,
                stage_metadata={
                    "snapshot_action": "reused",
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "attempt_count": attempt_count,
                    "existing_snapshot_id": known.snapshot_id,
                    "existing_fetched_at": known.fetched_at,
                    "preflight_status": preflight_status,
                    "preflight_issue_codes": preflight_issue_codes or [],
                    "current_response_metadata": _build_response_metadata(
                        source=source,
                        fetched=fetched,
                        attempt_count=attempt_count,
                    ),
                },
            ),
        )


def _build_checksum(body: bytes) -> str:
    return sha256(body).hexdigest()


def _build_fingerprint(body: bytes, content_type: str) -> str:
    digest = sha256()
    digest.update(content_type.encode("utf-8"))
    digest.update(b"\n")
    digest.update(body)
    return digest.hexdigest()


def _build_snapshot_id(source_document_id: str, fingerprint: str) -> str:
    digest = sha256(f"{source_document_id}|{fingerprint}".encode("utf-8")).hexdigest()[:16]
    return f"snap-{digest}"


def _build_response_metadata(
    *,
    source: CaptureSource,
    fetched: FetchedResponse,
    attempt_count: int,
) -> dict[str, object]:
    return {
        "source_id": source.source_id,
        "request_url": source.resolved_url,
        "final_url": fetched.final_url,
        "status_code": fetched.status_code,
        "content_length": len(fetched.body),
        "content_type": fetched.content_type,
        "redirect_count": fetched.redirect_count,
        "etag": fetched.headers.get("etag"),
        "last_modified": fetched.headers.get("last-modified"),
        "cache_control": fetched.headers.get("cache-control"),
        "attempt_count": attempt_count,
    }


def _build_run_source_item_record(
    *,
    run_id: str,
    source: CaptureSource,
    snapshot_id: str | None,
    stage_status: str,
    warning_count: int,
    error_count: int,
    error_summary: str | None,
    stage_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "run_source_item_id": _build_run_source_item_id(run_id, source.source_document_id),
        "run_id": run_id,
        "source_document_id": source.source_document_id,
        "selected_snapshot_id": snapshot_id,
        "stage_status": stage_status,
        "warning_count": warning_count,
        "error_count": error_count,
        "error_summary": error_summary,
        "stage_metadata": stage_metadata,
    }


def _build_run_source_item_id(run_id: str, source_document_id: str) -> str:
    digest = sha256(f"{run_id}|{source_document_id}".encode("utf-8")).hexdigest()[:16]
    return f"rsi-{digest}"
