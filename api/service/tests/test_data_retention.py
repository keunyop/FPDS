from __future__ import annotations

import unittest
from pathlib import Path

from api_service.data_retention import apply_data_retention


class DataRetentionTests(unittest.TestCase):
    def test_returns_not_installed_without_calling_retention_function(self) -> None:
        connection = _FakeConnection([{"available": False}])

        result = apply_data_retention(connection)

        self.assertEqual(result, {"status": "not_installed"})
        self.assertEqual(len(connection.calls), 1)

    def test_returns_database_cleanup_counts(self) -> None:
        connection = _FakeConnection(
            [
                {"available": True},
                {
                    "retention_summary": {
                        "evidence_chunks": 120,
                        "model_executions": 30,
                        "aggregate_snapshots": 8,
                    }
                },
            ]
        )

        result = apply_data_retention(connection)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["removed"]["evidence_chunks"], 120)
        self.assertEqual(len(connection.calls), 2)
        self.assertIn("fpds_apply_data_retention()", connection.calls[1])

    def test_retired_usage_writers_do_not_require_view_conflict_indexes(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        writer_paths = (
            repo_root / "api/service/api_service/source_catalog.py",
            repo_root / "worker/pipeline/fpds_extraction/persistence.py",
            repo_root / "worker/pipeline/fpds_normalization/persistence.py",
            repo_root / "worker/pipeline/fpds_validation_routing/persistence.py",
        )

        for writer_path in writer_paths:
            with self.subTest(writer=str(writer_path)):
                writer = writer_path.read_text(encoding="utf-8")
                self.assertNotIn("ON CONFLICT (llm_usage_id)", writer)


class _FakeConnection:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = iter(rows)
        self.calls: list[str] = []

    def execute(self, sql: str) -> "_FakeResult":
        self.calls.append(sql)
        return _FakeResult(next(self._rows))


class _FakeResult:
    def __init__(self, row: dict[str, object]) -> None:
        self._row = row

    def fetchone(self) -> dict[str, object]:
        return self._row


if __name__ == "__main__":
    unittest.main()
