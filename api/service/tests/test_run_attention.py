from __future__ import annotations

import re
import sqlite3
import unittest

from api_service.run_status import load_run_status_list, normalize_run_status_filters
from tests.test_auth import _QueuedConnection, _QueuedCursor


class _AggregateConnection(_QueuedConnection):
    def __init__(self, rows):
        super().__init__([{"total_items": len(rows)}, [], [], []])
        self.database = sqlite3.connect(":memory:")
        self.database.row_factory = sqlite3.Row
        self.database.execute("CREATE TABLE ingestion_run (country_code text, run_state text, partial_completion_flag boolean)")
        self.database.executemany("INSERT INTO ingestion_run VALUES (?, ?, ?)", rows)

    def execute(self, sql, params=None):
        if "AS attention_items" not in sql:
            return super().execute(sql, params)
        # Execute the production aggregate; adapt only the PostgreSQL parameter/ANY syntax.
        names = [":state" + str(i) for i in range(len(params["states"]))]
        query = sql.replace("= ANY(%(states)s)", "IN (" + ",".join(names) + ")")
        query = re.sub(r"%\((\w+)\)s", r":\1", query)
        bindings = {**params, **{"state"+str(i): state for i, state in enumerate(params["states"])}}
        return _QueuedCursor(dict(self.database.execute(query, bindings).fetchone()))


class RunAttentionTests(unittest.TestCase):
    def summary(self, rows):
        connection = _AggregateConnection(rows)
        try:
            filters = normalize_run_status_filters(country_code="CA", states=None, run_type=None,
                partial_only=False, started_from=None, started_to=None, search=None,
                sort_by="started_at", sort_order="desc", page=1, page_size=20)
            return load_run_status_list(connection, filters=filters)["summary"]
        finally:
            connection.database.close()

    def test_completed_partial_run_is_attention_without_any_failure(self):
        result = self.summary([("CA", "completed", True), ("CA", "completed", False)])
        self.assertEqual(result["attention_items"], 1)
        self.assertEqual(result["partial_items"], 1)

    def test_failed_partial_is_counted_once_and_other_country_is_excluded(self):
        result = self.summary([("CA", "failed", True), ("CA", "failed", False),
                               ("CA", "completed", True), ("US", "failed", True),
                               ("CA", "started", False)])
        self.assertEqual(result["attention_items"], 3)
        self.assertEqual(result["partial_items"], 2)

    def test_empty_and_healthy_runs_have_no_attention(self):
        for rows in ([], [("CA", "completed", False)]):
            self.assertEqual(self.summary(rows)["attention_items"], 0)
