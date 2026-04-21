from __future__ import annotations

import os
import subprocess
from typing import Sequence

_HEX_SUFFIX = "__hex"


def run_psql_command(command: Sequence[str], sql: str, *, force_utf8: bool = False) -> str:
    short_command, variables = _strip_psql_variables(command)
    sql_input = _inject_psql_variables(sql, variables)
    run_kwargs: dict[str, object] = {
        "input": sql_input,
        "text": True,
        "capture_output": True,
        "check": False,
    }
    if force_utf8:
        env = dict(os.environ)
        env["PGCLIENTENCODING"] = "UTF8"
        run_kwargs.update(
            {
                "encoding": "utf-8",
                "errors": "replace",
                "env": env,
            }
        )
    completed = subprocess.run(
        [*short_command, "-v", "ON_ERROR_STOP=1", "-X", "-q", "-A", "-t"],
        **run_kwargs,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown psql error"
        raise RuntimeError(f"psql command failed: {stderr}")
    return completed.stdout.strip()


def _strip_psql_variables(command: Sequence[str]) -> tuple[list[str], dict[str, str]]:
    short_command: list[str] = []
    variables: dict[str, str] = {}
    index = 0
    while index < len(command):
        token = str(command[index])
        if token == "-v" and index + 1 < len(command):
            assignment = str(command[index + 1])
            key, separator, value = assignment.partition("=")
            if separator:
                variables[key] = value
                index += 2
                continue
        short_command.append(token)
        index += 1
    return short_command, variables


def _inject_psql_variables(sql: str, variables: dict[str, str]) -> str:
    if not variables:
        return sql
    preamble_lines: list[str] = []
    rewritten_sql = sql
    for key, value in variables.items():
        hex_name = f"{key}{_HEX_SUFFIX}"
        preamble_lines.append(rf"\set {hex_name} {value.encode('utf-8').hex()}")
        rewritten_sql = rewritten_sql.replace(
            f":'{key}'",
            f"convert_from(decode(:'{hex_name}', 'hex'), 'utf8')",
        )
    return "\n".join([*preamble_lines, rewritten_sql])
