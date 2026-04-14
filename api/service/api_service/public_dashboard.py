from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Iterable

from api_service.public_common import (
    PublicQueryFilters,
    applied_filters_payload,
    apply_public_filters,
    build_freshness_payload,
    load_latest_public_snapshot,
    load_public_projection_rows,
    localize_product_type,
    normalize_public_query_filters,
    serialize_datetime,
    serialize_decimal,
)

SUPPORTED_AXIS_PRESETS = (
    "chequing_fee_vs_minimum_balance",
    "savings_rate_vs_minimum_balance",
    "gic_rate_vs_minimum_deposit",
    "gic_term_vs_rate",
)

RANKING_PRIORITY_BY_SCOPE = {
    "mixed": ("highest_display_rate", "recently_changed_30d"),
    "chequing": ("lowest_monthly_fee", "recently_changed_30d", "highest_display_rate"),
    "savings": ("highest_display_rate", "recently_changed_30d"),
    "gic": ("highest_display_rate", "lowest_minimum_deposit", "recently_changed_30d"),
}

SUMMARY_LABELS = {
    "en": {
        "total_active_products": "Total Active Products",
        "banks_in_scope": "Banks In Scope",
        "highest_display_rate": "Highest Display Rate",
        "recently_changed_products_30d": "Recently Changed (30d)",
        "products_by_bank": "Products by Bank",
        "products_by_product_type": "Products by Product Type",
        "rate_scope_note": "Products without display-rate data are excluded.",
        "recent_scope_note": "The window is fixed to the trailing 30 days from the latest snapshot refresh.",
    },
    "ko": {
        "total_active_products": "활성 상품 수",
        "banks_in_scope": "포함 은행 수",
        "highest_display_rate": "최고 표시 금리",
        "recently_changed_products_30d": "최근 변경 상품 수 (30일)",
        "products_by_bank": "은행별 상품 수",
        "products_by_product_type": "상품 유형별 상품 수",
        "rate_scope_note": "표시 금리 데이터가 없는 상품은 제외됩니다.",
        "recent_scope_note": "최신 스냅샷 갱신 시각 기준 최근 30일 창입니다.",
    },
    "ja": {
        "total_active_products": "有効商品数",
        "banks_in_scope": "対象銀行数",
        "highest_display_rate": "最高表示金利",
        "recently_changed_products_30d": "直近30日の変更商品数",
        "products_by_bank": "銀行別商品数",
        "products_by_product_type": "商品タイプ別商品数",
        "rate_scope_note": "表示金利データがない商品は除外されます。",
        "recent_scope_note": "最新スナップショット更新時刻基準の直近30日です。",
    },
}

RANKING_LABELS = {
    "en": {
        "highest_display_rate": ("Highest Display Rate", "Display Rate"),
        "lowest_monthly_fee": ("Lowest Monthly Fee", "Monthly Fee"),
        "lowest_minimum_deposit": ("Lowest Minimum Deposit", "Minimum Deposit"),
        "recently_changed_30d": ("Recently Changed", "Days Since Change"),
        "insufficient": "Not enough eligible products for this comparison.",
    },
    "ko": {
        "highest_display_rate": ("최고 표시 금리", "표시 금리"),
        "lowest_monthly_fee": ("최저 월 수수료", "월 수수료"),
        "lowest_minimum_deposit": ("최저 최소 예치금", "최소 예치금"),
        "recently_changed_30d": ("최근 변경", "변경 후 경과일"),
        "insufficient": "비교 가능한 상품 수가 충분하지 않습니다.",
    },
    "ja": {
        "highest_display_rate": ("最高表示金利", "表示金利"),
        "lowest_monthly_fee": ("最低月額手数料", "月額手数料"),
        "lowest_minimum_deposit": ("最低預入額", "最低預入額"),
        "recently_changed_30d": ("最近更新", "変更からの日数"),
        "insufficient": "比較に十分な商品数がありません。",
    },
}

SCATTER_LABELS = {
    "en": {
        "chequing_fee_vs_minimum_balance": ("Chequing Fee vs Minimum Balance", "Monthly Fee", "Minimum Balance"),
        "savings_rate_vs_minimum_balance": ("Savings Rate vs Minimum Balance", "Minimum Balance", "Display Rate"),
        "gic_rate_vs_minimum_deposit": ("GIC Rate vs Minimum Deposit", "Minimum Deposit", "Display Rate"),
        "gic_term_vs_rate": ("GIC Term vs Rate", "Term Length", "Display Rate"),
        "mixed_scope_note": "Select exactly one product type to load a comparative scatter chart.",
        "insufficient": "At least three eligible products are required for a comparative chart.",
        "methodology": "Metrics are derived from the latest successful aggregate snapshot and exclude products missing the required numeric fields.",
    },
    "ko": {
        "chequing_fee_vs_minimum_balance": ("입출금 수수료와 최소 잔액", "월 수수료", "최소 잔액"),
        "savings_rate_vs_minimum_balance": ("저축 금리와 최소 잔액", "최소 잔액", "표시 금리"),
        "gic_rate_vs_minimum_deposit": ("GIC 금리와 최소 예치금", "최소 예치금", "표시 금리"),
        "gic_term_vs_rate": ("GIC 기간과 금리", "가입 기간", "표시 금리"),
        "mixed_scope_note": "비교 차트를 보려면 상품 유형을 하나만 선택하세요.",
        "insufficient": "비교 차트에는 최소 3개의 유효 상품이 필요합니다.",
        "methodology": "지표는 최신 성공 aggregate snapshot을 기준으로 계산되며 필요한 숫자 필드가 없는 상품은 제외됩니다.",
    },
    "ja": {
        "chequing_fee_vs_minimum_balance": ("当座預金の手数料と最低残高", "月額手数料", "最低残高"),
        "savings_rate_vs_minimum_balance": ("貯蓄金利と最低残高", "最低残高", "表示金利"),
        "gic_rate_vs_minimum_deposit": ("GIC金利と最低預入額", "最低預入額", "表示金利"),
        "gic_term_vs_rate": ("GIC期間と金利", "期間", "表示金利"),
        "mixed_scope_note": "比較散布図を表示するには商品タイプを1つだけ選択してください。",
        "insufficient": "比較散布図には最低3件の有効商品が必要です。",
        "methodology": "指標は最新の成功した aggregate snapshot から算出され、必要な数値フィールドが欠けた商品は除外されます。",
    },
}


@dataclass(frozen=True)
class PublicDashboardQuery:
    filters: PublicQueryFilters
    axis_preset: str | None


def normalize_public_dashboard_query(
    *,
    locale: str | None,
    country_code: str | None,
    bank_codes: Iterable[str] | None,
    product_types: Iterable[str] | None,
    subtype_codes: Iterable[str] | None,
    target_customer_tags: Iterable[str] | None,
    fee_bucket: str | None,
    minimum_balance_bucket: str | None,
    minimum_deposit_bucket: str | None,
    term_bucket: str | None,
    axis_preset: str | None,
) -> PublicDashboardQuery:
    normalized_axis_preset = (axis_preset or "").strip().lower() or None
    if normalized_axis_preset not in SUPPORTED_AXIS_PRESETS:
        normalized_axis_preset = None

    return PublicDashboardQuery(
        filters=normalize_public_query_filters(
            locale=locale,
            country_code=country_code,
            bank_codes=bank_codes,
            product_types=product_types,
            subtype_codes=subtype_codes,
            target_customer_tags=target_customer_tags,
            fee_bucket=fee_bucket,
            minimum_balance_bucket=minimum_balance_bucket,
            minimum_deposit_bucket=minimum_deposit_bucket,
            term_bucket=term_bucket,
        ),
        axis_preset=normalized_axis_preset,
    )


def load_public_dashboard_summary(connection, *, query: PublicDashboardQuery) -> dict[str, Any]:
    snapshot, filtered_rows = _load_scoped_rows(connection, filters=query.filters)
    freshness = build_freshness_payload(snapshot, cache_ttl_sec=900)
    locale = query.filters.locale
    labels = SUMMARY_LABELS[locale]
    refreshed_at = _resolve_refreshed_at(snapshot)
    recent_threshold = refreshed_at - timedelta(days=30) if refreshed_at else None

    highest_display_rate = max(
        (serialize_decimal(row.get("public_display_rate")) for row in filtered_rows if row.get("public_display_rate") is not None),
        default=None,
    )
    recently_changed_count = sum(
        1
        for row in filtered_rows
        if recent_threshold and (changed_at := _as_datetime(row.get("last_changed_at"))) is not None and changed_at >= recent_threshold
    )
    total_active_products = len(filtered_rows)
    bank_counts = _count_breakdown(
        filtered_rows,
        key_builder=lambda row: (str(row["bank_code"]), str(row["bank_name"])),
    )
    type_counts = _count_breakdown(
        filtered_rows,
        key_builder=lambda row: (str(row["product_type"]), localize_product_type(str(row["product_type"]), locale=locale) or str(row["product_type"])),
    )

    return {
        "metrics": [
            {
                "metric_key": "total_active_products",
                "label": labels["total_active_products"],
                "value": total_active_products,
                "unit": "count",
                "scope_note": None,
            },
            {
                "metric_key": "banks_in_scope",
                "label": labels["banks_in_scope"],
                "value": len({str(row["bank_code"]) for row in filtered_rows}),
                "unit": "count",
                "scope_note": None,
            },
            {
                "metric_key": "highest_display_rate",
                "label": labels["highest_display_rate"],
                "value": highest_display_rate,
                "unit": "percent",
                "scope_note": labels["rate_scope_note"],
            },
            {
                "metric_key": "recently_changed_products_30d",
                "label": labels["recently_changed_products_30d"],
                "value": recently_changed_count,
                "unit": "count",
                "scope_note": labels["recent_scope_note"],
            },
        ],
        "breakdowns": {
            "products_by_bank": [
                {
                    "bank_code": bank_code,
                    "bank_name": bank_name,
                    "count": count,
                    "share_percent": _share_percent(count, total_active_products),
                }
                for bank_code, bank_name, count in bank_counts
            ],
            "products_by_product_type": [
                {
                    "product_type": product_type,
                    "product_type_label": product_type_label,
                    "count": count,
                    "share_percent": _share_percent(count, total_active_products),
                }
                for product_type, product_type_label, count in type_counts
            ],
        },
        "applied_filters": applied_filters_payload(query.filters),
        "freshness": freshness,
    }


def load_public_dashboard_rankings(connection, *, query: PublicDashboardQuery) -> dict[str, Any]:
    snapshot, filtered_rows = _load_scoped_rows(connection, filters=query.filters)
    freshness = build_freshness_payload(snapshot, cache_ttl_sec=900)
    locale = query.filters.locale
    labels = RANKING_LABELS[locale]
    refreshed_at = _resolve_refreshed_at(snapshot)
    scope_key = _resolve_scope_key(filtered_rows, filters=query.filters)
    ranking_keys = RANKING_PRIORITY_BY_SCOPE[scope_key]

    widgets: list[dict[str, Any]] = []
    for ranking_key in ranking_keys:
        widget = _build_ranking_widget(
            filtered_rows=filtered_rows,
            ranking_key=ranking_key,
            locale=locale,
            refreshed_at=refreshed_at,
        )
        if widget:
            widgets.append(widget)

    if scope_key == "mixed":
        widgets = widgets[:2]

    return {
        "widgets": widgets,
        "availability_status": "ready" if widgets else "insufficient_data",
        "insufficiency_note": None if widgets else labels["insufficient"],
        "applied_filters": applied_filters_payload(query.filters),
        "freshness": freshness,
    }


def load_public_dashboard_scatter(connection, *, query: PublicDashboardQuery) -> dict[str, Any]:
    snapshot, filtered_rows = _load_scoped_rows(connection, filters=query.filters)
    freshness = build_freshness_payload(snapshot, cache_ttl_sec=900)
    locale = query.filters.locale
    labels = SCATTER_LABELS[locale]
    scope_key = _resolve_scope_key(filtered_rows, filters=query.filters)
    axis_preset = query.axis_preset or _default_axis_preset(scope_key)

    if not axis_preset:
        return {
            "chart_key": None,
            "title": None,
            "x_axis": None,
            "y_axis": None,
            "points": [],
            "availability_status": "scope_selection_required",
            "insufficiency_note": labels["mixed_scope_note"],
            "methodology_note": labels["methodology"],
            "applied_filters": applied_filters_payload(query.filters),
            "freshness": freshness,
        }

    chart = _build_scatter_chart(filtered_rows=filtered_rows, axis_preset=axis_preset, locale=locale)
    if chart is None:
        title, x_label, y_label = SCATTER_LABELS[locale][axis_preset]
        return {
            "chart_key": axis_preset,
            "title": title,
            "x_axis": {"key": _axis_metadata(axis_preset)["x_field"], "label": x_label, "unit": _axis_metadata(axis_preset)["x_unit"]},
            "y_axis": {"key": _axis_metadata(axis_preset)["y_field"], "label": y_label, "unit": _axis_metadata(axis_preset)["y_unit"]},
            "points": [],
            "availability_status": "insufficient_data",
            "insufficiency_note": labels["insufficient"],
            "methodology_note": labels["methodology"],
            "applied_filters": applied_filters_payload(query.filters),
            "freshness": freshness,
        }

    return {
        **chart,
        "availability_status": "ready",
        "insufficiency_note": None,
        "methodology_note": labels["methodology"],
        "applied_filters": applied_filters_payload(query.filters),
        "freshness": freshness,
    }


def _load_scoped_rows(connection, *, filters: PublicQueryFilters) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    snapshot = load_latest_public_snapshot(connection, country_code=filters.country_code)
    if not snapshot:
        return None, []
    rows = load_public_projection_rows(
        connection,
        snapshot_id=str(snapshot["snapshot_id"]),
        country_code=filters.country_code,
    )
    return snapshot, apply_public_filters(rows, filters=filters)


def _resolve_scope_key(rows: list[dict[str, Any]], *, filters: PublicQueryFilters) -> str:
    if len(filters.product_types) == 1:
        return filters.product_types[0]
    distinct_product_types = {str(row["product_type"]) for row in rows}
    if len(distinct_product_types) == 1:
        return next(iter(distinct_product_types))
    return "mixed"


def _build_ranking_widget(
    *,
    filtered_rows: list[dict[str, Any]],
    ranking_key: str,
    locale: str,
    refreshed_at: datetime | None,
) -> dict[str, Any] | None:
    title, metric_label = RANKING_LABELS[locale][ranking_key]
    if ranking_key == "highest_display_rate":
        eligible_rows = [row for row in filtered_rows if row.get("public_display_rate") is not None]
        eligible_rows = sorted(
            eligible_rows,
            key=lambda row: (
                -(serialize_decimal(row.get("public_display_rate")) or 0.0),
                str(row["bank_name"]),
                str(row["product_name"]),
                str(row["product_id"]),
            ),
        )
        metric_unit = "percent"
        metric_value_builder = lambda row: serialize_decimal(row.get("public_display_rate"))
        metadata: dict[str, Any] = {}
    elif ranking_key == "lowest_monthly_fee":
        eligible_rows = [
            row
            for row in filtered_rows
            if row["product_type"] == "chequing" and row.get("effective_fee") is not None
        ]
        eligible_rows = sorted(
            eligible_rows,
            key=lambda row: (
                serialize_decimal(row.get("effective_fee")) or 0.0,
                str(row["bank_name"]),
                str(row["product_name"]),
                str(row["product_id"]),
            ),
        )
        metric_unit = "currency"
        metric_value_builder = lambda row: serialize_decimal(row.get("effective_fee"))
        metadata = {}
    elif ranking_key == "lowest_minimum_deposit":
        eligible_rows = [
            row
            for row in filtered_rows
            if row["product_type"] == "gic" and row.get("minimum_deposit") is not None
        ]
        eligible_rows = sorted(
            eligible_rows,
            key=lambda row: (
                serialize_decimal(row.get("minimum_deposit")) or 0.0,
                -(serialize_decimal(row.get("public_display_rate")) or 0.0),
                str(row["bank_name"]),
                str(row["product_name"]),
                str(row["product_id"]),
            ),
        )
        metric_unit = "currency"
        metric_value_builder = lambda row: serialize_decimal(row.get("minimum_deposit"))
        metadata = {}
    else:
        if not refreshed_at:
            return None
        recent_threshold = refreshed_at - timedelta(days=30)
        eligible_rows = [
            row
            for row in filtered_rows
            if (changed_at := _as_datetime(row.get("last_changed_at"))) is not None and changed_at >= recent_threshold
        ]
        eligible_rows = sorted(
            eligible_rows,
            key=lambda row: (
                -(_as_datetime(row.get("last_changed_at")) or datetime.fromtimestamp(0, tz=UTC)).timestamp(),
                str(row["bank_name"]),
                str(row["product_name"]),
                str(row["product_id"]),
            ),
        )
        metric_unit = "days"
        metric_value_builder = lambda row: round(
            (refreshed_at - (_as_datetime(row.get("last_changed_at")) or refreshed_at)).total_seconds() / 86400,
            4,
        )
        metadata = {"window_days": 30}

    if len(eligible_rows) < 3:
        return None

    items = []
    for index, row in enumerate(eligible_rows[:5], start=1):
        items.append(
            {
                "rank": index,
                "product_id": str(row["product_id"]),
                "bank_code": str(row["bank_code"]),
                "bank_name": str(row["bank_name"]),
                "product_name": str(row["product_name"]),
                "product_type": str(row["product_type"]),
                "metric_value": metric_value_builder(row),
                "metric_unit": metric_unit,
                "last_changed_at": serialize_datetime(row.get("last_changed_at")),
            }
        )

    return {
        "ranking_key": ranking_key,
        "title": title,
        "metric_label": metric_label,
        "items": items,
        **metadata,
    }


def _build_scatter_chart(
    *,
    filtered_rows: list[dict[str, Any]],
    axis_preset: str,
    locale: str,
) -> dict[str, Any] | None:
    axis = _axis_metadata(axis_preset)
    eligible_rows = [
        row
        for row in filtered_rows
        if axis["product_type"] == row["product_type"]
        and row.get(axis["x_field"]) is not None
        and row.get(axis["y_field"]) is not None
    ]
    if len(eligible_rows) < 3:
        return None

    title, x_label, y_label = SCATTER_LABELS[locale][axis_preset]
    points = [
        {
            "product_id": str(row["product_id"]),
            "bank_code": str(row["bank_code"]),
            "bank_name": str(row["bank_name"]),
            "product_name": str(row["product_name"]),
            "product_type": str(row["product_type"]),
            "x_value": serialize_decimal(row.get(axis["x_field"])),
            "y_value": serialize_decimal(row.get(axis["y_field"])),
            "highlight_badge_code": row.get("product_highlight_badge_code"),
        }
        for row in sorted(
            eligible_rows,
            key=lambda row: (
                str(row["bank_name"]),
                str(row["product_name"]),
                str(row["product_id"]),
            ),
        )
    ]
    return {
        "chart_key": axis_preset,
        "title": title,
        "x_axis": {"key": axis["x_field"], "label": x_label, "unit": axis["x_unit"]},
        "y_axis": {"key": axis["y_field"], "label": y_label, "unit": axis["y_unit"]},
        "points": points,
    }


def _default_axis_preset(scope_key: str) -> str | None:
    if scope_key == "chequing":
        return "chequing_fee_vs_minimum_balance"
    if scope_key == "savings":
        return "savings_rate_vs_minimum_balance"
    if scope_key == "gic":
        return "gic_rate_vs_minimum_deposit"
    return None


def _axis_metadata(axis_preset: str) -> dict[str, str]:
    return {
        "chequing_fee_vs_minimum_balance": {
            "product_type": "chequing",
            "x_field": "effective_fee",
            "x_unit": "currency",
            "y_field": "minimum_balance",
            "y_unit": "currency",
        },
        "savings_rate_vs_minimum_balance": {
            "product_type": "savings",
            "x_field": "minimum_balance",
            "x_unit": "currency",
            "y_field": "public_display_rate",
            "y_unit": "percent",
        },
        "gic_rate_vs_minimum_deposit": {
            "product_type": "gic",
            "x_field": "minimum_deposit",
            "x_unit": "currency",
            "y_field": "public_display_rate",
            "y_unit": "percent",
        },
        "gic_term_vs_rate": {
            "product_type": "gic",
            "x_field": "term_length_days",
            "x_unit": "days",
            "y_field": "public_display_rate",
            "y_unit": "percent",
        },
    }[axis_preset]


def _count_breakdown(
    rows: list[dict[str, Any]],
    *,
    key_builder,
) -> list[tuple[str, str, int]]:
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        key = key_builder(row)
        counts[key] = counts.get(key, 0) + 1
    items = [(code, label, count) for (code, label), count in counts.items()]
    items.sort(key=lambda item: (-item[2], item[1], item[0]))
    return items


def _resolve_refreshed_at(snapshot: dict[str, Any] | None) -> datetime | None:
    if not snapshot:
        return None
    return _as_datetime(snapshot.get("refreshed_at") or snapshot.get("attempted_at"))


def _share_percent(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((count / total) * 100, 2)


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None
