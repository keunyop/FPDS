from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from worker.psql_cli import run_psql_command


class PsqlCliTests(unittest.TestCase):
    def test_run_psql_command_moves_variables_off_command_line(self) -> None:
        captured: dict[str, object] = {}
        large_json = '{"items":[' + ",".join(['{"value":"abc"}'] * 400) + "]}"

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            captured["command"] = list(command)
            captured["kwargs"] = dict(kwargs)
            return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

        with patch("worker.psql_cli.subprocess.run", side_effect=fake_run):
            result = run_psql_command(
                [
                    "psql",
                    "postgres://example",
                    "-v",
                    f"source_documents_json={large_json}",
                    "-v",
                    "run_id=run-123",
                ],
                "SELECT :'source_documents_json'::jsonb, :'run_id';",
            )

        self.assertEqual(result, "ok")
        command = captured["command"]
        self.assertEqual(
            command,
            ["psql", "postgres://example", "-v", "ON_ERROR_STOP=1", "-X", "-q", "-A", "-t"],
        )
        sql_input = str(dict(captured["kwargs"])["input"])
        self.assertIn(r"\set source_documents_json__hex ", sql_input)
        self.assertIn(r"\set run_id__hex ", sql_input)
        self.assertIn("decode(:'source_documents_json__hex', 'hex')", sql_input)
        self.assertIn("decode(:'run_id__hex', 'hex')", sql_input)
        self.assertNotIn(large_json, " ".join(command))

    def test_run_psql_command_sets_utf8_environment_when_requested(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            captured["command"] = list(command)
            captured["kwargs"] = dict(kwargs)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with patch("worker.psql_cli.subprocess.run", side_effect=fake_run):
            run_psql_command(["psql", "postgres://example"], "SELECT 1;", force_utf8=True)

        kwargs = dict(captured["kwargs"])
        self.assertEqual(kwargs["encoding"], "utf-8")
        self.assertEqual(kwargs["errors"], "replace")
        self.assertEqual(dict(kwargs["env"])["PGCLIENTENCODING"], "UTF8")


if __name__ == "__main__":
    unittest.main()
