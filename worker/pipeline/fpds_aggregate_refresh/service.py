from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Iterable

from .models import AggregateRefreshResult, CanonicalAggregateRow

_PRODUCT_TYPE_LABELS = {
    "chequing": "Chequing",
    "savings": "Savings",
    "gic": "GIC",
}
_RANKING_KEYS = (
    "highest_display_rate",
    "lowest_monthly_fee",
    "lowest_minimum_deposit",
    "recently_changed_30d",
)
_SCATTER_PRESETS = (
    "chequing_fee_vs_minimum_balance",
    "savings_rate_vs_minimum_balance",
    "gic_rate_vs_minimum_deposit",
    "gic_term_vs_rate",
)
_ALL_ACTIVE_SCOPE_KEY = "all_active_products"


class AggregateRefreshService:
    def build_snapshot(
        self,
        *,
        snapshot_id: str,
        refresh_scope: str,
        country_code: str,
        canonical_rows: list[CanonicalAggregateRow],
        bank_codes: list[str] | None = None,
        product_types: list[str] | None = None,
        refreshed_at: str | None = None,
    ) -> AggregateRefreshResult:
        refreshed_at = refreshed_at or datetime.now(UTC).isoformat()
        refreshed_dt = _parse_datetime(refreshed_at)
        filter_scope = {
            "country_code": country_code,
            "bank_codes": sorted({item for item in (bank_codes or []) if item}),
            "product_types": sorted({item for item in (product_types or []) if item}),
        }
        projection_rows = [
            self._build_projection_row(
                snapshot_id=snapshot_id,
                canonical_row=item,
            )
            for item in canonical_rows
        ]
        active_rows = [item for item in projection_rows if item["status"] == "active"]
        source_change_cutoff_at = _latest_timestamp(
            item for item in (_coerce_timestamp(row.get("last_changed_at")) for row in projection_rows) if item is not None
        )
        metric_snapshots = [
            self._build_metric_snapshot(
                snapshot_id=snapshot_id,
                refreshed_at=refreshed_at,
                refreshed_dt=refreshed_dt,
                active_rows=active_rows,
            )
        ]
        ranking_rows = self._build_ranking_rows(
            snapshot_id=snapshot_id,
            refreshed_dt=refreshed_dt,
            active_rows=active_rows,
        )
        scatter_rows = self._build_scatter_rows(
            snapshot_id=snapshot_id,
            active_rows=active_rows,
        )
        refresh_metadata = {
            "ranking_keys": sorted({row["ranking_key"] for row in ranking_rows}),
            "scatter_presets": sorted({row["axis_preset"] for row in scatter_rows}),
            "bucket_policy": {
                "fee_bucket": ["free", "low_fee", "high_fee"],
                "minimum_balance_bucket": ["none", "under_1000", "from_1000_to_4999", "5000_plus"],
                "minimum_deposit_bucket": ["none", "under_500", "from_500_to_4999", "5000_plus"],
                "term_bucket": ["under_1y", "from_1y_to_3y", "over_3y"],
            },
            "source_counts": {
                "projection_rows": len(projection_rows),
                "active_rows": len(active_rows),
                "metric_scopes": len(metric_snapshots),
                "ranking_rows": len(ranking_rows),
                "scatter_rows": len(scatter_rows),
            },
        }
        return AggregateRefreshResult(
            snapshot_id=snapshot_id,
            refresh_scope=refresh_scope,
            country_code=country_code,
            filter_scope=filter_scope,
            source_change_cutoff_at=source_change_cutoff_at,
            refreshed_at=refreshed_at,
            projection_rows=projection_rows,
            metric_snapshots=metric_snapshots,
            ranking_rows=ranking_rows,
            scatter_rows=scatter_rows,
            refresh_metadata=refresh_metadata,
        )

    def _build_projection_row(
        self,
        *,
        snapshot_id: str,
        canonical_row: CanonicalAggregateRow,
    ) -> dict[str, object]:
        payload = dict(canonical_row.canonical_payload)
        bank_name = canonical_row.bank_name or str(payload.get("bank_name") or canonical_row.bank_code)
        subtype_code = canonical_row.subtype_code or _coerce_string(payload.get("subtype_code"))
        public_display_rate = _coerce_float(payload.get("public_display_rate"))
        public_display_fee = _coerce_float(payload.get("public_display_fee"))
        monthly_fee = _coerce_float(payload.get("monthly_fee"))
        minimum_balance = _coerce_float(payload.get("minimum_balance"))
        minimum_deposit = _coerce_float(payload.get("minimum_deposit"))
        term_length_days = _coerce_int(payload.get("term_length_days"))
        effective_fee = public_display_fee if public_display_fee is not None else monthly_fee
        return {
            "snapshot_id": snapshot_id,
            "product_id": canonical_row.product_id,
            "bank_code": canonical_row.bank_code,
            "bank_name": bank_name,
            "country_code": canonical_row.country_code,
            "product_family": canonical_row.product_family,
            "product_type": canonical_row.product_type,
            "subtype_code": subtype_code,
            "product_name": canonical_row.product_name,
            "source_language": canonical_row.source_language,
            "currency": canonical_row.currency,
            "status": canonical_row.status,
            "public_display_rate": public_display_rate,
            "public_display_fee": public_display_fee,
            "monthly_fee": monthly_fee,
            "effective_fee": effective_fee,
            "minimum_balance": minimum_balance,
            "minimum_deposit": minimum_deposit,
            "term_length_days": term_length_days,
            "product_highlight_badge_code": _coerce_string(payload.get("product_highlight_badge_code")),
            "target_customer_tags": _coerce_tags(payload.get("target_customer_tags")),
            "fee_bucket": _fee_bucket(effective_fee),
            "minimum_balance_bucket": _minimum_balance_bucket(minimum_balance),
            "minimum_deposit_bucket": _minimum_deposit_bucket(minimum_deposit),
            "term_bucket": _term_bucket(term_length_days),
            "last_verified_at": canonical_row.last_verified_at,
            "last_changed_at": canonical_row.last_changed_at,
            "refresh_metadata": {
                "product_version_id": canonical_row.product_version_id,
            },
        }

    def _build_metric_snapshot(
        self,
        *,
        snapshot_id: str,
        refreshed_at: str,
        refreshed_dt: datetime,
        active_rows: list[dict[str, object]],
    ) -> dict[str, object]:
        total_active_products = len(active_rows)
        distinct_banks = {str(item["bank_code"]) for item in active_rows}
        rate_values = [float(value) for value in (item.get("public_display_rate") for item in active_rows) if value is not None]
        recent_threshold = refreshed_dt - timedelta(days=30)
        recently_changed_products = sum(
            1
            for item in active_rows
            if (changed_at := _coerce_timestamp(item.get("last_changed_at"))) is not None and changed_at >= recent_threshold
        )
        products_by_bank = []
        bank_counter = Counter((str(item["bank_code"]), str(item["bank_name"])) for item in active_rows)
        for (bank_code, bank_name), count in sorted(bank_counter.items(), key=lambda item: (-item[1], item[0][1], item[0][0])):
            products_by_bank.append(
                {
                    "bank_code": bank_code,
                    "bank_name": bank_name,
                    "count": count,
                    "share_percent": _share_percent(count, total_active_products),
                }
            )
        products_by_product_type = []
        type_counter = Counter(str(item["product_type"]) for item in active_rows)
        for product_type, count in sorted(type_counter.items(), key=lambda item: (-item[1], _PRODUCT_TYPE_LABELS.get(item[0], item[0]), item[0])):
            products_by_product_type.append(
                {
                    "product_type": product_type,
                    "product_type_label": _PRODUCT_TYPE_LABELS.get(product_type, product_type.title()),
                    "count": count,
                    "share_percent": _share_percent(count, total_active_products),
                }
            )
        missing_rate_count = sum(1 for item in active_rows if item.get("public_display_rate") is None)
        completeness_note = None
        if missing_rate_count:
            completeness_note = f"{missing_rate_count} active products are excluded from rate-based comparisons."
        return {
            "snapshot_id": snapshot_id,
            "scope_key": _ALL_ACTIVE_SCOPE_KEY,
            "total_active_products": total_active_products,
            "banks_in_scope": len(distinct_banks),
            "highest_display_rate": max(rate_values) if rate_values else None,
            "recently_changed_products_30d": recently_changed_products,
            "breakdown_payload": {
                "products_by_bank": products_by_bank,
                "products_by_product_type": products_by_product_type,
            },
            "freshness_payload": {
                "snapshot_id": snapshot_id,
                "refreshed_at": refreshed_at,
                "status": "fresh",
            },
            "completeness_note": completeness_note,
        }

    def _build_ranking_rows(
        self,
        *,
        snapshot_id: str,
        refreshed_dt: datetime,
        active_rows: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        ranking_rows: list[dict[str, object]] = []
        recent_threshold = refreshed_dt - timedelta(days=30)
        definitions = {
            "highest_display_rate": (
                [item for item in active_rows if item.get("public_display_rate") is not None],
                lambda item: (-float(item["public_display_rate"]), str(item["bank_name"]), str(item["product_name"]), str(item["product_id"])),
                lambda item: float(item["public_display_rate"]),
                "percent",
                {},
            ),
            "lowest_monthly_fee": (
                [item for item in active_rows if item["product_type"] == "chequing" and item.get("effective_fee") is not None],
                lambda item: (float(item["effective_fee"]), str(item["bank_name"]), str(item["product_name"]), str(item["product_id"])),
                lambda item: float(item["effective_fee"]),
                "currency",
                {},
            ),
            "lowest_minimum_deposit": (
                [item for item in active_rows if item["product_type"] == "gic" and item.get("minimum_deposit") is not None],
                lambda item: (
                    float(item["minimum_deposit"]),
                    -float(item["public_display_rate"]) if item.get("public_display_rate") is not None else 0.0,
                    str(item["bank_name"]),
                    str(item["product_name"]),
                    str(item["product_id"]),
                ),
                lambda item: float(item["minimum_deposit"]),
                "currency",
                {},
            ),
            "recently_changed_30d": (
                [
                    item
                    for item in active_rows
                    if (changed_at := _coerce_timestamp(item.get("last_changed_at"))) is not None and changed_at >= recent_threshold
                ],
                lambda item: (
                    -_coerce_timestamp(item["last_changed_at"]).timestamp(),
                    str(item["bank_name"]),
                    str(item["product_name"]),
                    str(item["product_id"]),
                ),
                lambda item: round((refreshed_dt - _coerce_timestamp(item["last_changed_at"])).total_seconds() / 86400, 4),
                "days",
                {"window_days": 30},
            ),
        }
        for ranking_key in _RANKING_KEYS:
            eligible_rows, sort_key, metric_value_builder, metric_unit, metadata = definitions[ranking_key]
            if len(eligible_rows) < 3:
                continue
            ranked_rows = sorted(eligible_rows, key=sort_key)[:5]
            for rank, row in enumerate(ranked_rows, start=1):
                ranking_rows.append(
                    {
                        "snapshot_id": snapshot_id,
                        "scope_key": _ALL_ACTIVE_SCOPE_KEY,
                        "ranking_key": ranking_key,
                        "rank": rank,
                        "product_id": row["product_id"],
                        "bank_code": row["bank_code"],
                        "bank_name": row["bank_name"],
                        "product_name": row["product_name"],
                        "product_type": row["product_type"],
                        "metric_value": metric_value_builder(row),
                        "metric_unit": metric_unit,
                        "last_changed_at": row.get("last_changed_at"),
                        "ranking_metadata": metadata,
                    }
                )
        return ranking_rows

    def _build_scatter_rows(
        self,
        *,
        snapshot_id: str,
        active_rows: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        scatter_rows: list[dict[str, object]] = []
        definitions = {
            "chequing_fee_vs_minimum_balance": (
                [
                    item
                    for item in active_rows
                    if item["product_type"] == "chequing" and item.get("effective_fee") is not None and item.get("minimum_balance") is not None
                ],
                "effective_fee",
                "minimum_balance",
                {"x_field": "effective_fee", "y_field": "minimum_balance"},
            ),
            "savings_rate_vs_minimum_balance": (
                [
                    item
                    for item in active_rows
                    if item["product_type"] == "savings" and item.get("minimum_balance") is not None and item.get("public_display_rate") is not None
                ],
                "minimum_balance",
                "public_display_rate",
                {"x_field": "minimum_balance", "y_field": "public_display_rate"},
            ),
            "gic_rate_vs_minimum_deposit": (
                [
                    item
                    for item in active_rows
                    if item["product_type"] == "gic" and item.get("minimum_deposit") is not None and item.get("public_display_rate") is not None
                ],
                "minimum_deposit",
                "public_display_rate",
                {"x_field": "minimum_deposit", "y_field": "public_display_rate"},
            ),
            "gic_term_vs_rate": (
                [
                    item
                    for item in active_rows
                    if item["product_type"] == "gic" and item.get("term_length_days") is not None and item.get("public_display_rate") is not None
                ],
                "term_length_days",
                "public_display_rate",
                {"x_field": "term_length_days", "y_field": "public_display_rate"},
            ),
        }
        for axis_preset in _SCATTER_PRESETS:
            eligible_rows, x_field, y_field, metadata = definitions[axis_preset]
            if len(eligible_rows) < 3:
                continue
            for row in sorted(eligible_rows, key=lambda item: (str(item["bank_name"]), str(item["product_name"]), str(item["product_id"]))):
                scatter_rows.append(
                    {
                        "snapshot_id": snapshot_id,
                        "scope_key": _ALL_ACTIVE_SCOPE_KEY,
                        "axis_preset": axis_preset,
                        "product_id": row["product_id"],
                        "bank_code": row["bank_code"],
                        "bank_name": row["bank_name"],
                        "product_name": row["product_name"],
                        "product_type": row["product_type"],
                        "x_value": float(row[x_field]),
                        "y_value": float(row[y_field]),
                        "highlight_badge_code": row.get("product_highlight_badge_code"),
                        "last_changed_at": row.get("last_changed_at"),
                        "point_metadata": metadata,
                    }
                )
        return scatter_rows


def _coerce_tags(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _coerce_string(value: object) -> str | None:
    if value in {None, ""}:
        return None
    return str(value)


def _coerce_float(value: object) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: object) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _coerce_timestamp(value: object) -> datetime | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            return _parse_datetime(value)
        except ValueError:
            return None
    return None


def _latest_timestamp(values: Iterable[datetime]) -> str | None:
    latest = None
    for item in values:
        if latest is None or item > latest:
            latest = item
    return latest.isoformat() if latest is not None else None


def _share_percent(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((count / total) * 100, 2)


def _fee_bucket(value: float | None) -> str | None:
    if value is None:
        return None
    if value <= 0:
        return "free"
    if value < 15:
        return "low_fee"
    return "high_fee"


def _minimum_balance_bucket(value: float | None) -> str | None:
    if value is None:
        return None
    if value <= 0:
        return "none"
    if value < 1000:
        return "under_1000"
    if value < 5000:
        return "from_1000_to_4999"
    return "5000_plus"


def _minimum_deposit_bucket(value: float | None) -> str | None:
    if value is None:
        return None
    if value <= 0:
        return "none"
    if value < 500:
        return "under_500"
    if value < 5000:
        return "from_500_to_4999"
    return "5000_plus"


def _term_bucket(value: int | None) -> str | None:
    if value is None:
        return None
    if value < 365:
        return "under_1y"
    if value <= 1095:
        return "from_1y_to_3y"
    return "over_3y"
