from __future__ import annotations

import unittest

from worker.pipeline.fpds_evidence_retrieval.models import (
    EvidenceChunkCandidate,
    EvidenceRetrievalRequest,
    MetadataFilters,
)
from worker.pipeline.fpds_evidence_retrieval.service import EvidenceRetrievalService
from worker.pipeline.fpds_vector_embedding import build_retrieval_embedding


class VectorAssistedRetrievalRegressionTests(unittest.TestCase):
    def test_vector_assisted_falls_back_when_pgvector_candidates_are_missing(self) -> None:
        service = EvidenceRetrievalService()
        request = EvidenceRetrievalRequest(
            correlation_id="corr-regression",
            run_id="run-regression",
            parsed_document_id="parsed-regression",
            field_names=["monthly_fee"],
            metadata_filters=MetadataFilters(),
            retrieval_mode="vector-assisted",
            max_matches_per_field=1,
        )
        candidates = [
            EvidenceChunkCandidate(
                evidence_chunk_id="chunk-regression-fee",
                parsed_document_id="parsed-regression",
                chunk_index=0,
                anchor_type="section",
                anchor_value="fees",
                page_no=None,
                source_language="en",
                evidence_excerpt="Monthly fee: $0.",
                retrieval_metadata={},
                source_document_id="src-regression",
                source_snapshot_id="snap-regression",
                bank_code="TD",
                country_code="CA",
                source_type="html",
            )
        ]

        result = service.retrieve(request=request, candidates=candidates, vector_candidates_by_field={})

        self.assertEqual(result.applied_retrieval_mode, "metadata-only")
        self.assertEqual(result.matches[0].evidence_chunk_id, "chunk-regression-fee")

    def test_bootstrap_embedding_is_stable_for_same_input(self) -> None:
        first = build_retrieval_embedding("monthly fee account charge")
        second = build_retrieval_embedding("monthly fee account charge")

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)


if __name__ == "__main__":
    unittest.main()
