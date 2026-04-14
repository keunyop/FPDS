from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalAggregateRow:
    product_id: str
    bank_code: str
    bank_name: str
    country_code: str
    product_family: str
    product_type: str
    subtype_code: str | None
    product_name: str
    source_language: str
    currency: str
    status: str
    last_verified_at: str | None
    last_changed_at: str | None
    product_version_id: str | None
    canonical_payload: dict[str, object]


@dataclass(frozen=True)
class AggregateRefreshResult:
    snapshot_id: str
    refresh_scope: str
    country_code: str
    filter_scope: dict[str, object]
    source_change_cutoff_at: str | None
    refreshed_at: str
    projection_rows: list[dict[str, object]]
    metric_snapshots: list[dict[str, object]]
    ranking_rows: list[dict[str, object]]
    scatter_rows: list[dict[str, object]]
    refresh_metadata: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "refresh_scope": self.refresh_scope,
            "country_code": self.country_code,
            "filter_scope": self.filter_scope,
            "source_change_cutoff_at": self.source_change_cutoff_at,
            "refreshed_at": self.refreshed_at,
            "stats": {
                "projection_row_count": len(self.projection_rows),
                "metric_scope_count": len(self.metric_snapshots),
                "ranking_row_count": len(self.ranking_rows),
                "scatter_row_count": len(self.scatter_rows),
            },
            "refresh_metadata": self.refresh_metadata,
            "metric_snapshots": self.metric_snapshots,
            "ranking_rows": self.ranking_rows,
            "scatter_rows": self.scatter_rows,
        }
