from __future__ import annotations

import json
import unittest

from worker.pipeline.fpds_evidence_retrieval.models import (
    EvidenceChunkCandidate,
    EvidenceRetrievalRequest,
    MetadataFilters,
)
from worker.pipeline.fpds_evidence_retrieval.persistence import (
    PsqlEvidenceRetrievalRepository,
    RetrievalDatabaseConfig,
)
from worker.pipeline.fpds_evidence_retrieval.service import EvidenceRetrievalService


class EvidenceRetrievalServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = EvidenceRetrievalService()
        self.candidates = [
            EvidenceChunkCandidate(
                evidence_chunk_id="chunk-fee-001",
                parsed_document_id="parsed-001",
                chunk_index=0,
                anchor_type="section",
                anchor_value="fees",
                page_no=None,
                source_language="en",
                evidence_excerpt="Monthly fee: $0. No fee for this savings account.",
                retrieval_metadata={},
                source_document_id="src-001",
                source_snapshot_id="snap-001",
                bank_code="TD",
                country_code="CA",
                source_type="html",
            ),
            EvidenceChunkCandidate(
                evidence_chunk_id="chunk-rate-001",
                parsed_document_id="parsed-001",
                chunk_index=1,
                anchor_type="page",
                anchor_value="page-1",
                page_no=1,
                source_language="en",
                evidence_excerpt="Interest is calculated daily and paid monthly based on the daily closing balance.",
                retrieval_metadata={},
                source_document_id="src-001",
                source_snapshot_id="snap-001",
                bank_code="TD",
                country_code="CA",
                source_type="pdf",
            ),
        ]

    def test_retrieve_ranks_fee_chunk_for_monthly_fee(self) -> None:
        request = EvidenceRetrievalRequest(
            correlation_id="corr-001",
            run_id="run-001",
            parsed_document_id="parsed-001",
            field_names=["monthly_fee"],
            metadata_filters=MetadataFilters(),
            retrieval_mode="metadata-only",
            max_matches_per_field=2,
        )

        result = self.service.retrieve(request=request, candidates=self.candidates)

        self.assertEqual(result.applied_retrieval_mode, "metadata-only")
        self.assertEqual(result.matches[0].field_name, "monthly_fee")
        self.assertEqual(result.matches[0].evidence_chunk_id, "chunk-fee-001")
        self.assertGreater(result.matches[0].score, result.matches[1].score)

    def test_retrieve_filters_candidates_by_metadata(self) -> None:
        request = EvidenceRetrievalRequest(
            correlation_id=None,
            run_id="run-002",
            parsed_document_id="parsed-001",
            field_names=["interest_payment_frequency"],
            metadata_filters=MetadataFilters(source_types=("pdf",), anchor_types=("page",)),
            retrieval_mode="metadata-only",
            max_matches_per_field=2,
        )

        result = self.service.retrieve(request=request, candidates=self.candidates)

        self.assertEqual(len(result.matches), 1)
        self.assertEqual(result.matches[0].evidence_chunk_id, "chunk-rate-001")

    def test_vector_assisted_request_falls_back_to_metadata_only(self) -> None:
        request = EvidenceRetrievalRequest(
            correlation_id=None,
            run_id="run-003",
            parsed_document_id="parsed-001",
            field_names=["standard_rate"],
            metadata_filters=MetadataFilters(),
            retrieval_mode="vector-assisted",
            max_matches_per_field=1,
        )

        result = self.service.retrieve(request=request, candidates=self.candidates)

        self.assertEqual(result.applied_retrieval_mode, "metadata-only")
        self.assertEqual(len(result.runtime_notes), 1)
        self.assertIn("falling back to metadata-only", result.runtime_notes[0])

    def test_vector_assisted_request_uses_vector_ranked_candidates_when_available(self) -> None:
        request = EvidenceRetrievalRequest(
            correlation_id=None,
            run_id="run-004",
            parsed_document_id="parsed-001",
            field_names=["monthly_fee"],
            metadata_filters=MetadataFilters(),
            retrieval_mode="vector-assisted",
            max_matches_per_field=1,
        )
        vector_candidates = [
            EvidenceChunkCandidate(
                evidence_chunk_id="chunk-plan-charge-001",
                parsed_document_id="parsed-001",
                chunk_index=3,
                anchor_type="section",
                anchor_value="account charges",
                page_no=None,
                source_language="en",
                evidence_excerpt="There is no account plan charge for this savings product.",
                retrieval_metadata={},
                source_document_id="src-001",
                source_snapshot_id="snap-001",
                bank_code="TD",
                country_code="CA",
                source_type="html",
                vector_score=0.96,
            )
        ]

        result = self.service.retrieve(
            request=request,
            candidates=self.candidates,
            vector_candidates_by_field={"monthly_fee": vector_candidates},
        )

        self.assertEqual(result.applied_retrieval_mode, "vector-assisted")
        self.assertEqual(result.matches[0].evidence_chunk_id, "chunk-plan-charge-001")
        self.assertEqual(result.matches[0].match_metadata["vector_score"], 0.96)


class EvidenceRetrievalPersistenceTests(unittest.TestCase):
    def test_load_latest_parsed_documents_reads_json_rows(self) -> None:
        runner = _FakeRunner(
            outputs=[
                "public",
                json.dumps(
                    [
                        {
                            "parsed_document_id": "parsed-001",
                            "source_document_id": "src-001",
                            "snapshot_id": "snap-001",
                        }
                    ]
                ),
            ]
        )
        repository = PsqlEvidenceRetrievalRepository(
            RetrievalDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        result = repository.load_latest_parsed_documents(source_document_ids=["src-001"])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].parsed_document_id, "parsed-001")
        self.assertEqual(json.loads(runner.last_variables()["source_document_ids_json"]), ["src-001"])

    def test_load_chunk_candidates_reads_joined_chunk_rows(self) -> None:
        runner = _FakeRunner(
            outputs=[
                "public",
                json.dumps(
                    [
                        {
                            "evidence_chunk_id": "chunk-001",
                            "parsed_document_id": "parsed-001",
                            "chunk_index": 0,
                            "anchor_type": "section",
                            "anchor_value": "fees",
                            "page_no": None,
                            "source_language": "en",
                            "evidence_excerpt": "Monthly fee: $0",
                            "retrieval_metadata": {},
                            "source_document_id": "src-001",
                            "source_snapshot_id": "snap-001",
                            "bank_code": "TD",
                            "country_code": "CA",
                            "source_type": "html",
                        }
                    ]
                ),
            ]
        )
        repository = PsqlEvidenceRetrievalRepository(
            RetrievalDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        result = repository.load_chunk_candidates(parsed_document_id="parsed-001")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].evidence_chunk_id, "chunk-001")
        self.assertEqual(runner.last_variables()["parsed_document_id"], "parsed-001")

    def test_load_vector_chunk_candidates_reads_pgvector_ranked_rows(self) -> None:
        runner = _FakeRunner(
            outputs=[
                "public",
                "true",
                json.dumps(
                    [
                        {
                            "evidence_chunk_id": "chunk-001",
                            "parsed_document_id": "parsed-001",
                            "chunk_index": 0,
                            "anchor_type": "section",
                            "anchor_value": "fees",
                            "page_no": None,
                            "source_language": "en",
                            "evidence_excerpt": "No account plan charge",
                            "retrieval_metadata": {},
                            "source_document_id": "src-001",
                            "source_snapshot_id": "snap-001",
                            "bank_code": "TD",
                            "country_code": "CA",
                            "source_type": "html",
                            "vector_score": 0.91,
                        }
                    ]
                ),
            ]
        )
        repository = PsqlEvidenceRetrievalRepository(
            RetrievalDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        result = repository.load_vector_chunk_candidates(
            parsed_document_id="parsed-001",
            field_query_text="monthly fee account charge",
            metadata_filters=MetadataFilters(bank_code="TD", source_types=("html",)),
            max_matches=2,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].evidence_chunk_id, "chunk-001")
        self.assertEqual(result[0].vector_score, 0.91)
        self.assertIn("evidence_chunk_embedding", runner.calls[-1][1])
        self.assertIn("<=>", runner.calls[-1][1])
        self.assertEqual(runner.last_variables()["bank_code"], "TD")


class _FakeRunner:
    def __init__(self, *, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls: list[tuple[list[str], str]] = []

    def __call__(self, command: list[str], sql: str) -> str:
        self.calls.append((list(command), sql))
        return self.outputs.pop(0)

    def last_variables(self) -> dict[str, str]:
        command = self.calls[-1][0]
        variables: dict[str, str] = {}
        for index, token in enumerate(command):
            if token != "-v":
                continue
            key, value = command[index + 1].split("=", 1)
            variables[key] = value
        return variables


if __name__ == "__main__":
    unittest.main()
