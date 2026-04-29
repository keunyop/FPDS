from __future__ import annotations

import json
from pathlib import Path
from shutil import rmtree
import unittest

from worker.pipeline.fpds_parse_chunk.models import ExistingParsedDocumentRecord, ParseSourceSnapshot
from worker.pipeline.fpds_parse_chunk.persistence import (
    ParseChunkDatabaseConfig,
    PsqlParseChunkRepository,
)
from worker.pipeline.fpds_parse_chunk.service import ParseChunkService
from worker.pipeline.fpds_parse_chunk.storage import ParseChunkStorageConfig, build_object_store


class ParseChunkServiceTests(unittest.TestCase):
    def test_html_snapshot_parses_and_chunks_with_section_anchor(self) -> None:
        temp_path = _prepare_workspace_temp_dir("parse-chunk-html")
        try:
            snapshot = ParseSourceSnapshot(
                source_id="TD-SAV-002",
                snapshot_id="snap-html-001",
                source_document_id="src-html-001",
                object_storage_key="dev/snapshots/CA/TD/src-html-001/snap-html-001/raw",
                content_type="text/html",
                source_language="en",
                bank_code="TD",
                country_code="CA",
            )
            _write_object(
                temp_path,
                snapshot.object_storage_key,
                b"""
                <html>
                  <body>
                    <main>
                      <h1>Every Day Savings Account</h1>
                      <p>No monthly fee.</p>
                      <h2>Interest</h2>
                      <p>Earn interest daily and pay monthly.</p>
                    </main>
                  </body>
                </html>
                """,
            )
            storage_config = ParseChunkStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                snapshot_object_prefix="snapshots",
                parsed_object_prefix="parsed",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ParseChunkService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
                chunk_max_chars=120,
                chunk_overlap_chars=20,
            )

            result = service.parse_snapshots(run_id="run_20260410_html", snapshots=[snapshot])

            self.assertFalse(result.partial_completion_flag)
            item = result.source_results[0]
            self.assertEqual(item.parse_action, "stored")
            self.assertGreaterEqual(item.chunk_count, 1)
            self.assertEqual(item.evidence_chunk_records[0]["anchor_type"], "section")
            self.assertIn("Every Day Savings Account", item.evidence_chunk_records[0]["evidence_excerpt"])

            parsed_path = temp_path / Path(str(item.parsed_storage_key).replace("/", "\\"))
            metadata_path = temp_path / Path(str(item.metadata_storage_key).replace("/", "\\"))
            self.assertTrue(parsed_path.exists())
            self.assertTrue(metadata_path.exists())
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["chunk_count"], item.chunk_count)
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_html_snapshot_falls_back_to_body_when_main_is_empty(self) -> None:
        temp_path = _prepare_workspace_temp_dir("parse-chunk-empty-main")
        try:
            snapshot = ParseSourceSnapshot(
                source_id="BMO-GIC-003",
                snapshot_id="snap-html-empty-main",
                source_document_id="src-html-empty-main",
                object_storage_key="dev/snapshots/CA/BMO/src-html-empty-main/snap-html-empty-main/raw",
                content_type="text/html",
                source_language="en",
                bank_code="BMO",
                country_code="CA",
            )
            _write_object(
                temp_path,
                snapshot.object_storage_key,
                b"""
                <html>
                  <head><title>BMO Progressive GIC</title></head>
                  <body>
                    <main id="content"></main>
                    <div id="app">
                      <h1>BMO Progressive GIC</h1>
                      <p>Principal protected guaranteed investment certificate.</p>
                      <p>Choose a term and review current rates.</p>
                    </div>
                  </body>
                </html>
                """,
            )
            storage_config = ParseChunkStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                snapshot_object_prefix="snapshots",
                parsed_object_prefix="parsed",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ParseChunkService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
                chunk_max_chars=120,
                chunk_overlap_chars=20,
            )

            result = service.parse_snapshots(run_id="run_20260410_empty_main", snapshots=[snapshot])

            self.assertFalse(result.partial_completion_flag)
            item = result.source_results[0]
            self.assertEqual(item.parse_action, "stored")
            self.assertGreaterEqual(item.chunk_count, 1)
            self.assertIn("BMO Progressive GIC", item.evidence_chunk_records[0]["evidence_excerpt"])
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_pdf_snapshot_parses_and_chunks_with_page_anchor(self) -> None:
        temp_path = _prepare_workspace_temp_dir("parse-chunk-pdf")
        try:
            snapshot = ParseSourceSnapshot(
                source_id="TD-SAV-007",
                snapshot_id="snap-pdf-001",
                source_document_id="src-pdf-001",
                object_storage_key="dev/snapshots/CA/TD/src-pdf-001/snap-pdf-001/raw",
                content_type="application/pdf",
                source_language="en",
                bank_code="TD",
                country_code="CA",
            )
            _write_object(
                temp_path,
                snapshot.object_storage_key,
                _build_minimal_pdf(["TD Fee Schedule and Terms", ""]),
            )
            storage_config = ParseChunkStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                snapshot_object_prefix="snapshots",
                parsed_object_prefix="parsed",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ParseChunkService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
                chunk_max_chars=120,
                chunk_overlap_chars=20,
            )

            result = service.parse_snapshots(run_id="run_20260410_pdf", snapshots=[snapshot])

            self.assertFalse(result.partial_completion_flag)
            item = result.source_results[0]
            self.assertEqual(item.parse_action, "stored")
            self.assertEqual(item.evidence_chunk_records[0]["anchor_type"], "page")
            self.assertEqual(item.evidence_chunk_records[0]["page_no"], 1)
            self.assertIn("Partial PDF parse", item.parse_quality_note or "")
        finally:
            rmtree(temp_path, ignore_errors=True)

    def test_existing_parsed_document_is_reused_without_object_read(self) -> None:
        snapshot = ParseSourceSnapshot(
            source_id="TD-SAV-008",
            snapshot_id="snap-reuse-001",
            source_document_id="src-reuse-001",
            object_storage_key="dev/snapshots/CA/TD/src-reuse-001/snap-reuse-001/raw",
            content_type="application/pdf",
            source_language="en",
            bank_code="TD",
            country_code="CA",
        )
        existing = ExistingParsedDocumentRecord(
            parsed_document_id="parsed-existing-001",
            snapshot_id=snapshot.snapshot_id,
            parsed_storage_key="dev/parsed/CA/TD/src-reuse-001/parsed-existing-001/parsed.txt",
            parser_version="fpds-parse-chunk-v1",
            parse_quality_note=None,
            parser_metadata={"metadata_storage_key": "dev/parsed/CA/TD/src-reuse-001/parsed-existing-001/metadata.json"},
            retention_class="hot",
            parsed_at="2026-04-10T00:00:00+00:00",
            chunk_count=3,
        )
        service = ParseChunkService(
            storage_config=ParseChunkStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                snapshot_object_prefix="snapshots",
                parsed_object_prefix="parsed",
                retention_class="hot",
                filesystem_root="ignored-for-reuse",
            ),
            object_store=_FailingReadObjectStore(),
        )

        result = service.parse_snapshots(
            run_id="run_20260410_reuse",
            snapshots=[snapshot],
            existing_parsed_documents=[existing],
        )

        item = result.source_results[0]
        self.assertEqual(item.parse_action, "reused")
        self.assertEqual(item.chunk_count, 3)
        self.assertEqual(item.parsed_document_id, existing.parsed_document_id)


class ParseChunkPersistenceTests(unittest.TestCase):
    def test_load_latest_snapshots_reads_json_rows_from_psql_output(self) -> None:
        runner = _FakeRunner(
            outputs=[
                "public",
                json.dumps(
                    [
                        {
                            "snapshot_id": "snap-001",
                            "source_document_id": "src-001",
                            "object_storage_key": "dev/snapshots/CA/TD/src-001/snap-001/raw",
                            "content_type": "text/html",
                            "source_language": "en",
                            "bank_code": "TD",
                            "country_code": "CA",
                        }
                    ]
                ),
            ]
        )
        repository = PsqlParseChunkRepository(
            ParseChunkDatabaseConfig(database_url="postgres://example", schema="public"),
            command_runner=runner,
        )

        snapshots = repository.load_latest_snapshots(source_document_ids=["src-001"])

        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].snapshot_id, "snap-001")
        self.assertEqual(json.loads(runner.last_variables()["source_document_ids_json"]), ["src-001"])

    def test_persist_parse_chunk_result_batches_documents_chunks_and_run_items(self) -> None:
        temp_path = _prepare_workspace_temp_dir("parse-chunk-persist")
        try:
            snapshot = ParseSourceSnapshot(
                source_id="TD-SAV-004",
                snapshot_id="snap-persist-001",
                source_document_id="src-persist-001",
                object_storage_key="dev/snapshots/CA/TD/src-persist-001/snap-persist-001/raw",
                content_type="text/html",
                source_language="en",
                bank_code="TD",
                country_code="CA",
            )
            _write_object(
                temp_path,
                snapshot.object_storage_key,
                b"<html><body><main><h1>ePremium Savings</h1><p>Bonus interest details.</p></main></body></html>",
            )
            storage_config = ParseChunkStorageConfig(
                driver="filesystem",
                env_prefix="dev",
                snapshot_object_prefix="snapshots",
                parsed_object_prefix="parsed",
                retention_class="hot",
                filesystem_root=str(temp_path),
            )
            service = ParseChunkService(
                storage_config=storage_config,
                object_store=build_object_store(storage_config),
                chunk_max_chars=120,
                chunk_overlap_chars=20,
            )
            parse_result = service.parse_snapshots(run_id="run_20260410_persist", snapshots=[snapshot])

            runner = _FakeRunner(outputs=["public", ""])
            repository = PsqlParseChunkRepository(
                ParseChunkDatabaseConfig(database_url="postgres://example", schema="public"),
                command_runner=runner,
            )

            persisted = repository.persist_parse_chunk_result(
                run_id="run_20260410_persist",
                parse_result=parse_result,
                trigger_type="manual",
                triggered_by="codex",
                completed_at="2026-04-10T00:10:00+00:00",
            )

            self.assertEqual(persisted.run_state, "completed")
            self.assertEqual(persisted.parsed_document_count, 1)
            self.assertGreaterEqual(persisted.evidence_chunk_count, 1)
            variables = runner.last_variables()
            self.assertEqual(variables["run_state"], "completed")
            self.assertIn("parsed_document_payload", runner.last_sql())
            self.assertIn("\"parsed_document_id\"", runner.last_sql())
            self.assertIn("\"evidence_chunk_id\"", runner.last_sql())
        finally:
            rmtree(temp_path, ignore_errors=True)


class _FailingReadObjectStore:
    def get_object_bytes(self, *, object_key: str) -> bytes:
        raise AssertionError("Object read should not happen for reused parsed documents")

    def put_object_bytes(self, *, object_key: str, data: bytes, content_type: str) -> None:
        raise AssertionError("Object write should not happen for reused parsed documents")


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

    def last_sql(self) -> str:
        return self.calls[-1][1]


def _prepare_workspace_temp_dir(name: str) -> Path:
    path = Path("worker/pipeline/tests/.tmp") / name
    rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_object(root: Path, object_key: str, data: bytes) -> None:
    target = root / Path(object_key.replace("/", "\\"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def _build_minimal_pdf(page_texts: list[str]) -> bytes:
    objects: list[bytes] = []

    page_ids = [3 + (index * 2) for index in range(len(page_texts))]
    font_object_id = 3 + (len(page_texts) * 2)

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_texts)} >>".encode("ascii"))

    for index, text in enumerate(page_texts):
        page_id = page_ids[index]
        content_id = page_id + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {content_id} 0 R /Resources << /Font << /F1 {font_object_id} 0 R >> >> >>".encode(
                "ascii"
            )
        )
        stream_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT\n/F1 12 Tf\n72 720 Td\n({stream_text}) Tj\nET\n".encode("latin-1") if text else b""
        content = b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream"
        objects.append(content)

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


if __name__ == "__main__":
    unittest.main()
