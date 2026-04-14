from __future__ import annotations

import json
import unittest

from worker.pipeline.fpds_aggregate_refresh.models import AggregateRefreshResult, CanonicalAggregateRow
from worker.pipeline.fpds_aggregate_refresh.persistence import (
    AggregateRefreshDatabaseConfig,
    PsqlAggregateRefreshRepository,
)
from worker.pipeline.fpds_aggregate_refresh.service import AggregateRefreshService


class AggregateRefreshServiceTests(unittest.TestCase):
    def test_build_snapshot_generates_projection_metrics_rankings_and_scatter(self) -> None:
        service = AggregateRefreshService()
        result = service.build_snapshot(
            snapshot_id="agg-001",
            refresh_scope="phase1_public",
            country_code="CA",
            canonical_rows=_build_rows(),
            refreshed_at="2026-04-13T12:00:00+00:00",
        )

        self.assertEqual(len(result.projection_rows), 11)
        metric_snapshot = result.metric_snapshots[0]
        self.assertEqual(metric_snapshot["total_active_products"], 10)
        self.assertEqual(metric_snapshot["banks_in_scope"], 5)
        self.assertEqual(metric_snapshot["highest_display_rate"], 4.5)
        self.assertEqual(metric_snapshot["recently_changed_products_30d"], 9)

        projection_by_product_id = {item["product_id"]: item for item in result.projection_rows}
        self.assertEqual(projection_by_product_id["chq-rbc-student"]["fee_bucket"], "free")
        self.assertEqual(projection_by_product_id["sav-td-epremium"]["minimum_balance_bucket"], "5000_plus")
        self.assertEqual(projection_by_product_id["gic-td-short"]["minimum_deposit_bucket"], "under_500")
        self.assertEqual(projection_by_product_id["gic-bmo-1y"]["term_bucket"], "from_1y_to_3y")
        self.assertEqual(projection_by_product_id["gic-scotia-4y"]["term_bucket"], "over_3y")

        ranking_keys = {item["ranking_key"] for item in result.ranking_rows}
        self.assertEqual(
            ranking_keys,
            {"highest_display_rate", "lowest_monthly_fee", "lowest_minimum_deposit", "recently_changed_30d"},
        )
        highest_rate_rows = [item for item in result.ranking_rows if item["ranking_key"] == "highest_display_rate"]
        self.assertEqual(highest_rate_rows[0]["product_id"], "gic-bmo-1y")
        lowest_fee_rows = [item for item in result.ranking_rows if item["ranking_key"] == "lowest_monthly_fee"]
        self.assertEqual(lowest_fee_rows[0]["product_id"], "chq-rbc-student")
        lowest_deposit_rows = [item for item in result.ranking_rows if item["ranking_key"] == "lowest_minimum_deposit"]
        self.assertEqual(lowest_deposit_rows[0]["product_id"], "gic-td-short")
        recent_rows = [item for item in result.ranking_rows if item["ranking_key"] == "recently_changed_30d"]
        self.assertEqual(recent_rows[0]["product_id"], "chq-scotia-premium")

        scatter_preset_counts: dict[str, int] = {}
        for row in result.scatter_rows:
            scatter_preset_counts[row["axis_preset"]] = scatter_preset_counts.get(row["axis_preset"], 0) + 1
        self.assertEqual(
            scatter_preset_counts,
            {
                "chequing_fee_vs_minimum_balance": 4,
                "savings_rate_vs_minimum_balance": 3,
                "gic_rate_vs_minimum_deposit": 3,
                "gic_term_vs_rate": 3,
            },
        )
        self.assertIn("bucket_policy", result.refresh_metadata)


class AggregateRefreshPersistenceTests(unittest.TestCase):
    def test_repository_loads_canonical_rows_and_persists_snapshot(self) -> None:
        runner = _FakeRunner(
            outputs=[
                "public",
                "",
                json.dumps(
                    [
                        {
                            "product_id": "sav-001",
                            "bank_code": "TD",
                            "bank_name": "TD Bank",
                            "country_code": "CA",
                            "product_family": "deposit",
                            "product_type": "savings",
                            "subtype_code": "high_interest",
                            "product_name": "TD ePremium Savings Account",
                            "source_language": "en",
                            "currency": "CAD",
                            "status": "active",
                            "last_verified_at": "2026-04-12T00:00:00+00:00",
                            "last_changed_at": "2026-04-10T00:00:00+00:00",
                            "product_version_id": "pv-001",
                            "canonical_payload": {
                                "public_display_rate": 3.2,
                                "minimum_balance": 5000,
                                "target_customer_tags": ["newcomer"],
                            },
                        }
                    ]
                ),
                "",
            ]
        )
        repository = PsqlAggregateRefreshRepository(
            AggregateRefreshDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        repository.ensure_refresh_run(
            snapshot_id="agg-001",
            triggered_by_run_id="run-001",
            refresh_scope="phase1_public",
            country_code="CA",
            filter_scope={"country_code": "CA", "bank_codes": ["TD"], "product_types": ["savings"]},
            attempted_at="2026-04-13T12:00:00+00:00",
        )
        rows = repository.load_current_canonical_rows(
            country_code="CA",
            bank_codes=["TD"],
            product_types=["savings"],
        )
        repository.persist_refresh_result(
            result=_build_persistence_result(),
            triggered_by_run_id="run-001",
        )

        self.assertEqual(rows[0].product_id, "sav-001")
        ensure_variables = runner.variables_for_call(1)
        load_variables = runner.variables_for_call(2)
        self.assertEqual(ensure_variables["attempted_at"], "2026-04-13T12:00:00+00:00")
        self.assertEqual(load_variables["bank_codes_json"], '["TD"]')
        self.assertIn("public_product_projection", runner.calls[3][1])
        self.assertIn("dashboard_metric_snapshot", runner.calls[3][1])


class _FakeRunner:
    def __init__(self, *, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls: list[tuple[list[str], str]] = []

    def __call__(self, command: list[str], sql: str) -> str:
        self.calls.append((list(command), sql))
        return self.outputs.pop(0)

    def variables_for_call(self, index: int) -> dict[str, str]:
        command = self.calls[index][0]
        variables: dict[str, str] = {}
        for position, token in enumerate(command):
            if token != "-v":
                continue
            key, value = command[position + 1].split("=", 1)
            variables[key] = value
        return variables


def _build_rows() -> list[CanonicalAggregateRow]:
    return [
        _row(
            product_id="chq-rbc-student",
            bank_code="RBC",
            product_type="chequing",
            subtype_code="package",
            product_name="RBC Student Banking",
            last_changed_at="2026-04-10T00:00:00+00:00",
            payload={"public_display_rate": 1.0, "monthly_fee": 0, "minimum_balance": 0, "target_customer_tags": ["student"]},
        ),
        _row(
            product_id="chq-cibc-smart",
            bank_code="CIBC",
            product_type="chequing",
            subtype_code="standard",
            product_name="CIBC Smart Account",
            last_changed_at="2026-03-20T00:00:00+00:00",
            payload={"public_display_rate": 0.5, "monthly_fee": 4.95, "minimum_balance": 1500},
        ),
        _row(
            product_id="chq-scotia-premium",
            bank_code="SCOTIA",
            product_type="chequing",
            subtype_code="premium",
            product_name="Scotiabank Ultimate Package",
            last_changed_at="2026-04-11T00:00:00+00:00",
            payload={"public_display_rate": 0.75, "monthly_fee": 14.99, "minimum_balance": 4000},
        ),
        _row(
            product_id="chq-td-everyday",
            bank_code="TD",
            product_type="chequing",
            subtype_code="standard",
            product_name="TD Everyday Chequing Account",
            last_changed_at="2026-04-01T00:00:00+00:00",
            payload={"monthly_fee": 16.95, "minimum_balance": 5000},
        ),
        _row(
            product_id="sav-td-epremium",
            bank_code="TD",
            product_type="savings",
            subtype_code="high_interest",
            product_name="TD ePremium Savings Account",
            last_changed_at="2026-03-25T00:00:00+00:00",
            payload={"public_display_rate": 3.2, "minimum_balance": 5000},
        ),
        _row(
            product_id="sav-rbc-high",
            bank_code="RBC",
            product_type="savings",
            subtype_code="high_interest",
            product_name="RBC High Interest eSavings",
            last_changed_at="2026-04-05T00:00:00+00:00",
            payload={"public_display_rate": 2.7, "minimum_balance": 0},
        ),
        _row(
            product_id="sav-bmo-standard",
            bank_code="BMO",
            product_type="savings",
            subtype_code="standard",
            product_name="BMO Savings Builder",
            last_changed_at="2026-04-08T00:00:00+00:00",
            payload={"public_display_rate": 1.5, "minimum_balance": 100},
        ),
        _row(
            product_id="gic-bmo-1y",
            bank_code="BMO",
            product_type="gic",
            subtype_code="non_redeemable",
            product_name="BMO 1 Year GIC",
            last_changed_at="2026-04-07T00:00:00+00:00",
            payload={"public_display_rate": 4.5, "minimum_deposit": 500, "term_length_days": 365},
        ),
        _row(
            product_id="gic-scotia-4y",
            bank_code="SCOTIA",
            product_type="gic",
            subtype_code="non_redeemable",
            product_name="Scotiabank 4 Year GIC",
            last_changed_at="2026-03-01T00:00:00+00:00",
            payload={"public_display_rate": 4.2, "minimum_deposit": 5000, "term_length_days": 1460},
        ),
        _row(
            product_id="gic-td-short",
            bank_code="TD",
            product_type="gic",
            subtype_code="redeemable",
            product_name="TD 6 Month Cashable GIC",
            last_changed_at="2026-04-03T00:00:00+00:00",
            payload={"public_display_rate": 4.3, "minimum_deposit": 250, "term_length_days": 180},
        ),
        _row(
            product_id="sav-cibc-inactive",
            bank_code="CIBC",
            product_type="savings",
            subtype_code="standard",
            product_name="CIBC Dormant Savings",
            status="inactive",
            last_changed_at="2026-02-01T00:00:00+00:00",
            payload={"public_display_rate": 0.1, "minimum_balance": 0},
        ),
    ]


def _row(
    *,
    product_id: str,
    bank_code: str,
    product_type: str,
    subtype_code: str,
    product_name: str,
    last_changed_at: str,
    payload: dict[str, object],
    status: str = "active",
) -> CanonicalAggregateRow:
    bank_name = {
        "RBC": "Royal Bank of Canada",
        "TD": "TD Bank",
        "BMO": "BMO",
        "SCOTIA": "Scotiabank",
        "CIBC": "CIBC",
    }[bank_code]
    return CanonicalAggregateRow(
        product_id=product_id,
        bank_code=bank_code,
        bank_name=bank_name,
        country_code="CA",
        product_family="deposit",
        product_type=product_type,
        subtype_code=subtype_code,
        product_name=product_name,
        source_language="en",
        currency="CAD",
        status=status,
        last_verified_at="2026-04-12T00:00:00+00:00",
        last_changed_at=last_changed_at,
        product_version_id=f"pv-{product_id}",
        canonical_payload=payload,
    )


def _build_persistence_result() -> AggregateRefreshResult:
    return AggregateRefreshResult(
        snapshot_id="agg-001",
        refresh_scope="phase1_public",
        country_code="CA",
        filter_scope={"country_code": "CA", "bank_codes": ["TD"], "product_types": ["savings"]},
        source_change_cutoff_at="2026-04-10T00:00:00+00:00",
        refreshed_at="2026-04-13T12:01:00+00:00",
        projection_rows=[
            {
                "snapshot_id": "agg-001",
                "product_id": "sav-001",
                "bank_code": "TD",
                "bank_name": "TD Bank",
                "country_code": "CA",
                "product_family": "deposit",
                "product_type": "savings",
                "subtype_code": "high_interest",
                "product_name": "TD ePremium Savings Account",
                "source_language": "en",
                "currency": "CAD",
                "status": "active",
                "public_display_rate": 3.2,
                "public_display_fee": None,
                "monthly_fee": None,
                "effective_fee": None,
                "minimum_balance": 5000.0,
                "minimum_deposit": None,
                "term_length_days": None,
                "product_highlight_badge_code": None,
                "target_customer_tags": ["newcomer"],
                "fee_bucket": None,
                "minimum_balance_bucket": "5000_plus",
                "minimum_deposit_bucket": None,
                "term_bucket": None,
                "last_verified_at": "2026-04-12T00:00:00+00:00",
                "last_changed_at": "2026-04-10T00:00:00+00:00",
                "refresh_metadata": {"product_version_id": "pv-001"},
            }
        ],
        metric_snapshots=[
            {
                "snapshot_id": "agg-001",
                "scope_key": "all_active_products",
                "total_active_products": 1,
                "banks_in_scope": 1,
                "highest_display_rate": 3.2,
                "recently_changed_products_30d": 1,
                "breakdown_payload": {
                    "products_by_bank": [{"bank_code": "TD", "bank_name": "TD Bank", "count": 1, "share_percent": 100.0}],
                    "products_by_product_type": [{"product_type": "savings", "product_type_label": "Savings", "count": 1, "share_percent": 100.0}],
                },
                "freshness_payload": {"snapshot_id": "agg-001", "refreshed_at": "2026-04-13T12:01:00+00:00", "status": "fresh"},
                "completeness_note": None,
            }
        ],
        ranking_rows=[],
        scatter_rows=[],
        refresh_metadata={"source_counts": {"projection_rows": 1}},
    )


if __name__ == "__main__":
    unittest.main()
