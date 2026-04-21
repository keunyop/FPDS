from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from api_service.aggregate_refresh import (
    DEFAULT_COUNTRY_CODE,
    DEFAULT_REFRESH_SCOPE,
    claim_aggregate_refresh_batch,
    complete_aggregate_refresh_batch,
    fail_aggregate_refresh_batch,
)
from api_service.config import Settings
from api_service.db import open_connection
from api_service.security import new_id

AGGREGATE_REFRESH_LOCK_KEY = 704251604221


def main() -> int:
    settings = Settings.from_env()
    with open_connection(settings) as connection:
        if not _try_acquire_lock(connection):
            return 0
        connection.commit()
        try:
            while True:
                batch = claim_aggregate_refresh_batch(
                    connection,
                    country_code=DEFAULT_COUNTRY_CODE,
                    refresh_scope=DEFAULT_REFRESH_SCOPE,
                )
                if not batch:
                    break
                connection.commit()

                snapshot_id = new_id("agg")
                try:
                    _run_refresh(
                        snapshot_id=snapshot_id,
                        country_code=str(batch["country_code"]),
                        refresh_scope=str(batch["refresh_scope"]),
                    )
                except Exception as exc:  # pragma: no cover - defensive background path
                    fail_aggregate_refresh_batch(
                        connection,
                        request_ids=list(batch["request_ids"]),
                        error_summary=str(exc),
                        completed_at=datetime.now(UTC),
                    )
                    connection.commit()
                    print(f"[aggregate-refresh-runner] failed batch {batch['request_ids']}: {exc}", flush=True)
                    continue

                complete_aggregate_refresh_batch(
                    connection,
                    request_ids=list(batch["request_ids"]),
                    snapshot_id=snapshot_id,
                    completed_at=datetime.now(UTC),
                )
                connection.commit()
                print(
                    f"[aggregate-refresh-runner] completed batch of {len(batch['request_ids'])} request(s) as {snapshot_id}",
                    flush=True,
                )
        finally:
            _release_lock(connection)
            connection.commit()
    return 0


def _run_refresh(*, snapshot_id: str, country_code: str, refresh_scope: str) -> None:
    from worker.pipeline.fpds_aggregate_refresh.persistence import (
        AggregateRefreshDatabaseConfig,
        PsqlAggregateRefreshRepository,
    )
    from worker.pipeline.fpds_aggregate_refresh.service import AggregateRefreshService

    attempted_at = datetime.now(UTC).isoformat()
    repository = PsqlAggregateRefreshRepository(AggregateRefreshDatabaseConfig.from_env())
    filter_scope = {
        "country_code": country_code,
        "bank_codes": [],
        "product_types": [],
    }
    refresh_started = False
    try:
        repository.ensure_refresh_run(
            snapshot_id=snapshot_id,
            triggered_by_run_id=None,
            refresh_scope=refresh_scope,
            country_code=country_code,
            filter_scope=filter_scope,
            attempted_at=attempted_at,
        )
        refresh_started = True
        canonical_rows = repository.load_current_canonical_rows(
            country_code=country_code,
            bank_codes=[],
            product_types=[],
        )
        service = AggregateRefreshService()
        result = service.build_snapshot(
            snapshot_id=snapshot_id,
            refresh_scope=refresh_scope,
            country_code=country_code,
            canonical_rows=canonical_rows,
            bank_codes=[],
            product_types=[],
            refreshed_at=datetime.now(UTC).isoformat(),
        )
        repository.persist_refresh_result(result=result, triggered_by_run_id=None)
    except Exception as exc:
        if refresh_started:
            repository.mark_refresh_failed(
                snapshot_id=snapshot_id,
                error_summary=str(exc),
                completed_at=datetime.now(UTC).isoformat(),
            )
        raise


def _try_acquire_lock(connection: Any) -> bool:
    row = connection.execute(
        "SELECT pg_try_advisory_lock(%(lock_key)s) AS acquired",
        {"lock_key": AGGREGATE_REFRESH_LOCK_KEY},
    ).fetchone()
    return bool(row and row.get("acquired"))


def _release_lock(connection: Any) -> None:
    connection.execute(
        "SELECT pg_advisory_unlock(%(lock_key)s)",
        {"lock_key": AGGREGATE_REFRESH_LOCK_KEY},
    )


if __name__ == "__main__":
    raise SystemExit(main())
