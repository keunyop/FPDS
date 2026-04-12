from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Callable

from .models import (
    EvidenceChunkRecord,
    ExistingParsedDocumentRecord,
    ParseChunkResult,
    ParseChunkSourceResult,
    ParseSourceSnapshot,
    ParsedArtifact,
)
from .parser import parse_snapshot_bytes
from .storage import ParseChunkObjectStore, ParseChunkStorageConfig


class ParseChunkService:
    def __init__(
        self,
        *,
        storage_config: ParseChunkStorageConfig,
        object_store: ParseChunkObjectStore,
        parser: Callable[..., ParsedArtifact] = parse_snapshot_bytes,
        chunk_max_chars: int = 900,
        chunk_overlap_chars: int = 120,
    ):
        self.storage_config = storage_config
        self.object_store = object_store
        self.parser = parser
        self.chunk_max_chars = chunk_max_chars
        self.chunk_overlap_chars = chunk_overlap_chars

    def parse_snapshots(
        self,
        *,
        run_id: str,
        snapshots: list[ParseSourceSnapshot],
        correlation_id: str | None = None,
        request_id: str | None = None,
        existing_parsed_documents: list[ExistingParsedDocumentRecord] | None = None,
    ) -> ParseChunkResult:
        known_parsed = {
            item.snapshot_id: item for item in (existing_parsed_documents or [])
        }
        source_results: list[ParseChunkSourceResult] = []
        partial_completion_flag = False

        for snapshot in snapshots:
            result = self._parse_single_snapshot(
                run_id=run_id,
                snapshot=snapshot,
                correlation_id=correlation_id,
                request_id=request_id,
                existing_parsed=known_parsed.get(snapshot.snapshot_id),
            )
            source_results.append(result)
            if result.parse_action == "failed":
                partial_completion_flag = True

        return ParseChunkResult(
            run_id=run_id,
            correlation_id=correlation_id,
            request_id=request_id,
            source_results=source_results,
            partial_completion_flag=partial_completion_flag,
        )

    def _parse_single_snapshot(
        self,
        *,
        run_id: str,
        snapshot: ParseSourceSnapshot,
        correlation_id: str | None,
        request_id: str | None,
        existing_parsed: ExistingParsedDocumentRecord | None,
    ) -> ParseChunkSourceResult:
        if existing_parsed is not None:
            return self._build_reused_result(
                run_id=run_id,
                snapshot=snapshot,
                correlation_id=correlation_id,
                request_id=request_id,
                existing_parsed=existing_parsed,
            )

        try:
            raw_body = self.object_store.get_object_bytes(object_key=snapshot.object_storage_key)
            artifact = self.parser(body=raw_body, content_type=snapshot.content_type)
            parsed_document_id = _build_parsed_document_id(snapshot.snapshot_id, artifact.parser_version)
            chunks = _build_evidence_chunks(
                parsed_document_id=parsed_document_id,
                source_language=snapshot.source_language,
                artifact=artifact,
                max_chars=self.chunk_max_chars,
                overlap_chars=self.chunk_overlap_chars,
            )
            if not chunks:
                raise ValueError("Chunk builder produced no evidence chunks.")

            parsed_storage_key = self.storage_config.build_parsed_text_object_key(
                country_code=snapshot.country_code,
                bank_code=snapshot.bank_code,
                source_document_id=snapshot.source_document_id,
                parsed_document_id=parsed_document_id,
            )
            metadata_storage_key = self.storage_config.build_parsed_metadata_object_key(
                country_code=snapshot.country_code,
                bank_code=snapshot.bank_code,
                source_document_id=snapshot.source_document_id,
                parsed_document_id=parsed_document_id,
            )
            self.object_store.put_object_bytes(
                object_key=parsed_storage_key,
                data=artifact.full_text.encode("utf-8"),
                content_type="text/plain; charset=utf-8",
            )
            self.object_store.put_object_bytes(
                object_key=metadata_storage_key,
                data=json.dumps(
                    _build_metadata_payload(
                        snapshot=snapshot,
                        artifact=artifact,
                        parsed_document_id=parsed_document_id,
                        parsed_storage_key=parsed_storage_key,
                        metadata_storage_key=metadata_storage_key,
                        chunk_count=len(chunks),
                    ),
                    indent=2,
                    ensure_ascii=True,
                ).encode("utf-8"),
                content_type="application/json",
            )

            parsed_document_record = {
                "parsed_document_id": parsed_document_id,
                "snapshot_id": snapshot.snapshot_id,
                "parsed_storage_key": parsed_storage_key,
                "parser_version": artifact.parser_version,
                "parse_quality_note": artifact.parse_quality_note,
                "parser_metadata": {
                    **artifact.parser_metadata,
                    "metadata_storage_key": metadata_storage_key,
                    "chunk_count": len(chunks),
                },
                "retention_class": self.storage_config.retention_class,
                "parsed_at": _utc_now_iso(),
            }
            warning_count = 1 if artifact.parse_quality_note else 0
            return ParseChunkSourceResult(
                source_id=snapshot.source_id,
                source_document_id=snapshot.source_document_id,
                snapshot_id=snapshot.snapshot_id,
                parse_action="stored",
                parsed_document_id=parsed_document_id,
                parsed_storage_key=parsed_storage_key,
                metadata_storage_key=metadata_storage_key,
                chunk_count=len(chunks),
                parse_quality_note=artifact.parse_quality_note,
                error_summary=None,
                parsed_document_record=parsed_document_record,
                evidence_chunk_records=[chunk.to_record() for chunk in chunks],
                run_source_item_record=_build_run_source_item_record(
                    run_id=run_id,
                    source_document_id=snapshot.source_document_id,
                    snapshot_id=snapshot.snapshot_id,
                    stage_status="completed",
                    warning_count=warning_count,
                    error_count=0,
                    error_summary=None,
                    stage_metadata={
                        "parse_action": "stored",
                        "parsed_document_id": parsed_document_id,
                        "parsed_storage_key": parsed_storage_key,
                        "metadata_storage_key": metadata_storage_key,
                        "chunk_count": len(chunks),
                        "parse_quality_note": artifact.parse_quality_note,
                        "parser_version": artifact.parser_version,
                        "correlation_id": correlation_id,
                        "request_id": request_id,
                    },
                ),
            )
        except Exception as exc:
            return ParseChunkSourceResult(
                source_id=snapshot.source_id,
                source_document_id=snapshot.source_document_id,
                snapshot_id=snapshot.snapshot_id,
                parse_action="failed",
                parsed_document_id=None,
                parsed_storage_key=None,
                metadata_storage_key=None,
                chunk_count=0,
                parse_quality_note=None,
                error_summary=str(exc),
                parsed_document_record=None,
                evidence_chunk_records=[],
                run_source_item_record=_build_run_source_item_record(
                    run_id=run_id,
                    source_document_id=snapshot.source_document_id,
                    snapshot_id=snapshot.snapshot_id,
                    stage_status="failed",
                    warning_count=0,
                    error_count=1,
                    error_summary=str(exc),
                    stage_metadata={
                        "parse_action": "failed",
                        "correlation_id": correlation_id,
                        "request_id": request_id,
                        "snapshot_id": snapshot.snapshot_id,
                        "snapshot_object_key": snapshot.object_storage_key,
                    },
                ),
            )

    def _build_reused_result(
        self,
        *,
        run_id: str,
        snapshot: ParseSourceSnapshot,
        correlation_id: str | None,
        request_id: str | None,
        existing_parsed: ExistingParsedDocumentRecord,
    ) -> ParseChunkSourceResult:
        parser_metadata = dict(existing_parsed.parser_metadata)
        return ParseChunkSourceResult(
            source_id=snapshot.source_id,
            source_document_id=snapshot.source_document_id,
            snapshot_id=snapshot.snapshot_id,
            parse_action="reused",
            parsed_document_id=existing_parsed.parsed_document_id,
            parsed_storage_key=existing_parsed.parsed_storage_key,
            metadata_storage_key=_optional_string(parser_metadata.get("metadata_storage_key")),
            chunk_count=existing_parsed.chunk_count,
            parse_quality_note=existing_parsed.parse_quality_note,
            error_summary=None,
            parsed_document_record=None,
            evidence_chunk_records=[],
            run_source_item_record=_build_run_source_item_record(
                run_id=run_id,
                source_document_id=snapshot.source_document_id,
                snapshot_id=snapshot.snapshot_id,
                stage_status="completed",
                warning_count=1 if existing_parsed.parse_quality_note else 0,
                error_count=0,
                error_summary=None,
                stage_metadata={
                    "parse_action": "reused",
                    "parsed_document_id": existing_parsed.parsed_document_id,
                    "parsed_storage_key": existing_parsed.parsed_storage_key,
                    "metadata_storage_key": parser_metadata.get("metadata_storage_key"),
                    "chunk_count": existing_parsed.chunk_count,
                    "parse_quality_note": existing_parsed.parse_quality_note,
                    "parser_version": existing_parsed.parser_version,
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                },
            ),
        )


def _build_evidence_chunks(
    *,
    parsed_document_id: str,
    source_language: str,
    artifact: ParsedArtifact,
    max_chars: int,
    overlap_chars: int,
) -> list[EvidenceChunkRecord]:
    chunk_records: list[EvidenceChunkRecord] = []

    for segment in artifact.segments:
        for rel_start, rel_end, excerpt in _split_text_with_overlap(
            segment.text,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        ):
            chunk_index = len(chunk_records)
            chunk_records.append(
                EvidenceChunkRecord(
                    evidence_chunk_id=_build_evidence_chunk_id(parsed_document_id, chunk_index),
                    parsed_document_id=parsed_document_id,
                    chunk_index=chunk_index,
                    anchor_type=segment.anchor_type,
                    anchor_value=segment.anchor_value,
                    page_no=segment.page_no,
                    source_language=source_language,
                    chunk_char_start=segment.char_start + rel_start,
                    chunk_char_end=segment.char_start + rel_end,
                    evidence_excerpt=excerpt,
                    retrieval_metadata={
                        "parser_version": artifact.parser_version,
                        "chunk_length": len(excerpt),
                        "segment_char_start": segment.char_start,
                        "segment_char_end": segment.char_end,
                    },
                )
            )

    return chunk_records


def _split_text_with_overlap(text: str, *, max_chars: int, overlap_chars: int) -> list[tuple[int, int, str]]:
    if not text.strip():
        return []

    chunks: list[tuple[int, int, str]] = []
    start = 0
    text_length = len(text)
    while start < text_length:
        raw_end = min(text_length, start + max_chars)
        if raw_end < text_length:
            window = text[start:raw_end]
            split_at = max(
                window.rfind("\n\n"),
                window.rfind("\n"),
                window.rfind(". "),
                window.rfind(" "),
            )
            if split_at >= max_chars // 2:
                raw_end = start + split_at + 1

        raw_chunk = text[start:raw_end]
        left_trim = len(raw_chunk) - len(raw_chunk.lstrip())
        right_trim = len(raw_chunk) - len(raw_chunk.rstrip())
        excerpt = raw_chunk.strip()
        if excerpt:
            chunks.append((start + left_trim, raw_end - right_trim, excerpt))

        if raw_end >= text_length:
            break
        next_start = max(raw_end - overlap_chars, start + 1)
        start = next_start if next_start > start else raw_end

    return chunks


def _build_metadata_payload(
    *,
    snapshot: ParseSourceSnapshot,
    artifact: ParsedArtifact,
    parsed_document_id: str,
    parsed_storage_key: str,
    metadata_storage_key: str,
    chunk_count: int,
) -> dict[str, object]:
    return {
        "snapshot_id": snapshot.snapshot_id,
        "source_document_id": snapshot.source_document_id,
        "parsed_document_id": parsed_document_id,
        "parser_name": artifact.parser_name,
        "parser_version": artifact.parser_version,
        "parse_quality_note": artifact.parse_quality_note,
        "parser_metadata": artifact.parser_metadata,
        "parsed_storage_key": parsed_storage_key,
        "metadata_storage_key": metadata_storage_key,
        "chunk_count": chunk_count,
    }


def _build_run_source_item_record(
    *,
    run_id: str,
    source_document_id: str,
    snapshot_id: str,
    stage_status: str,
    warning_count: int,
    error_count: int,
    error_summary: str | None,
    stage_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "run_source_item_id": _build_run_source_item_id(run_id, source_document_id),
        "run_id": run_id,
        "source_document_id": source_document_id,
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


def _build_parsed_document_id(snapshot_id: str, parser_version: str) -> str:
    digest = sha256(f"{snapshot_id}|{parser_version}".encode("utf-8")).hexdigest()[:16]
    return f"parsed-{digest}"


def _build_evidence_chunk_id(parsed_document_id: str, chunk_index: int) -> str:
    digest = sha256(f"{parsed_document_id}|{chunk_index}".encode("utf-8")).hexdigest()[:16]
    return f"chunk-{digest}"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
