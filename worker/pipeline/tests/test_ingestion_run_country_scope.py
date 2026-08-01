from __future__ import annotations

import unittest

from worker.discovery.fpds_snapshot.persistence import (
    PsqlSnapshotRepository,
    SnapshotDatabaseConfig,
)
from worker.pipeline.fpds_extraction.persistence import (
    ExtractionDatabaseConfig,
    PsqlExtractionRepository,
)
from worker.pipeline.fpds_normalization.persistence import (
    NormalizationDatabaseConfig,
    PsqlNormalizationRepository,
)
from worker.pipeline.fpds_parse_chunk.persistence import (
    ParseChunkDatabaseConfig,
    PsqlParseChunkRepository,
)
from worker.pipeline.fpds_validation_routing.persistence import (
    PsqlValidationRoutingRepository,
    ValidationRoutingDatabaseConfig,
)
from worker.run_scope import require_single_country_code


class _RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []

    def __call__(self, command, sql: str) -> str:
        self.calls.append((list(command), sql))
        if "FROM pg_tables" in sql:
            return "public\n"
        return ""


class IngestionRunCountryScopeTests(unittest.TestCase):
    def test_country_scope_normalizes_one_country_and_rejects_mixed_runs(self) -> None:
        self.assertEqual(require_single_country_code(["us", "US"]), "US")
        with self.assertRaisesRegex(ValueError, "exactly one country_code"):
            require_single_country_code(["CA", "US"])
        with self.assertRaisesRegex(ValueError, "invalid country_code"):
            require_single_country_code(["USA"])

    def test_every_worker_stage_persists_country_code(self) -> None:
        repository_factories = [
            lambda runner: PsqlSnapshotRepository(
                SnapshotDatabaseConfig(database_url="postgresql://test", schema="public"),
                command_runner=runner,
            ),
            lambda runner: PsqlParseChunkRepository(
                ParseChunkDatabaseConfig(database_url="postgresql://test", schema="public"),
                command_runner=runner,
            ),
            lambda runner: PsqlExtractionRepository(
                ExtractionDatabaseConfig(database_url="postgresql://test", schema="public"),
                command_runner=runner,
            ),
            lambda runner: PsqlNormalizationRepository(
                NormalizationDatabaseConfig(database_url="postgresql://test", schema="public"),
                command_runner=runner,
            ),
            lambda runner: PsqlValidationRoutingRepository(
                ValidationRoutingDatabaseConfig(database_url="postgresql://test", schema="public"),
                command_runner=runner,
            ),
        ]

        for factory in repository_factories:
            with self.subTest(factory=factory):
                runner = _RecordingRunner()
                repository = factory(runner)
                method = getattr(
                    repository,
                    "start_ingestion_run"
                    if isinstance(repository, PsqlSnapshotRepository)
                    else "ensure_ingestion_run",
                )
                method(
                    run_id="run_US_contract",
                    country_code="US",
                    trigger_type="manual",
                    triggered_by="test",
                    source_scope_count=1,
                    correlation_id="correlation",
                    request_id="request",
                    source_ids=["source-US"],
                    started_at="2026-07-30T00:00:00+00:00",
                )

                command, sql = runner.calls[-1]
                self.assertIn("country_code", sql)
                self.assertIn("country_code = EXCLUDED.country_code", sql)
                self.assertIn("country_code=US", command)


if __name__ == "__main__":
    unittest.main()
