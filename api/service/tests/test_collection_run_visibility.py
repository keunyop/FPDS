from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch
from api_service import source_catalog as catalog
from api_service.run_status import _build_where_clause, _display_run_state, normalize_run_status_filters


def row(code, product_type="savings"):
    return {"catalog_item_id": code, "bank_code": code, "bank_name": code,
            "country_code": "CA", "product_type": product_type, "status": "active",
            "homepage_url": "https://bank.example", "source_language": "en"}


class CollectionRunVisibilityTests(unittest.TestCase):
    def launch(self, rows, eligible=None, skipped=None, reservations=None, launch_error=None):
        connection = MagicMock()
        connection.execute.return_value.fetchall.return_value = rows
        events = []
        connection.commit.side_effect = lambda: events.append("commit")
        def launch(plan):
            events.append("launch")
            self.assertEqual(events[-2], "commit")
            if launch_error:
                raise launch_error
        def insert(*args, **kwargs):
            events.append(kwargs["group"]["collection_phase"])
        with (patch.object(catalog, "_preflight_catalog_items", return_value=(rows if eligible is None else eligible, list(skipped or []))),
              patch.object(catalog, "reserve_preparation", side_effect=reservations or [True] * len(rows)),
              patch.object(catalog, "_insert_collection_run_row", side_effect=insert) as inserted,
              patch.object(catalog, "_launch_source_catalog_collection_runner", side_effect=launch) as launched,
              patch.object(catalog, "_record_catalog_audit_event")):
            if launch_error:
                with self.assertRaises(RuntimeError):
                    catalog.start_source_catalog_collection(connection, catalog_item_ids=[r["catalog_item_id"] for r in rows], actor={}, request_context={})
                result = None
            else:
                result = catalog.start_source_catalog_collection(connection, catalog_item_ids=[r["catalog_item_id"] for r in rows], actor={}, request_context={})
        return result, connection, inserted, launched, events

    def test_every_selected_bank_type_run_exists_before_background_launch(self):
        result, connection, inserted, launched, events = self.launch([row("A"), row("B", "gic")])
        self.assertEqual(events, ["queued", "queued", "commit", "launch"])
        self.assertEqual(len(result["run_ids"]), 2)
        self.assertEqual(result["run_ids"], [group["run_id"] for group in launched.call_args.args[0]["groups"]])
        self.assertTrue(all(call.kwargs["group"]["country_code"] == "CA" for call in inserted.call_args_list))

    def test_known_exclusion_is_a_visible_terminal_run(self):
        skipped = [{"catalog_item_id": "A", "bank_code": "A", "product_type": "savings", "reason_codes": ["no_eligible_detail"]}]
        result, connection, inserted, launched, _ = self.launch([row("A")], eligible=[], skipped=skipped)
        self.assertEqual(len(result["run_ids"]), 1)
        self.assertEqual(inserted.call_args.kwargs["group"]["collection_phase"], "skipped")
        launched.assert_not_called()
        terminal = next(call.args[1] for call in connection.execute.call_args_list if "UPDATE ingestion_run" in call.args[0])
        self.assertEqual(json.loads(terminal["metadata"])["preparation_reason_codes"], ["no_eligible_detail"])

    def test_duplicate_reservation_never_creates_an_extra_run(self):
        result, _, inserted, launched, _ = self.launch([row("A")], reservations=[False])
        self.assertEqual(result["run_ids"], [])
        inserted.assert_not_called()
        launched.assert_not_called()

    def test_launch_failure_finishes_all_registered_runs(self):
        _, connection, _, _, events = self.launch([row("A"), row("B")], launch_error=RuntimeError("launch failed"))
        terminal = [call for call in connection.execute.call_args_list if "UPDATE ingestion_run" in call.args[0]]
        self.assertEqual(len(terminal), 2)
        self.assertTrue(all("run_state='failed'" in call.args[0] for call in terminal))
        self.assertEqual(events[-1], "commit")

    def test_display_state_respects_terminal_lifecycle(self):
        for state, phase, expected in [("started", "queued", "queued"), ("started", "discovering", "discovering"),
                ("started", "collecting", "started"), ("completed", "skipped", "skipped"),
                ("failed", "queued", "failed"), ("retried", "skipped", "retried")]:
            self.assertEqual(_display_run_state({"run_state": state, "run_metadata": {"collection_phase": phase}}), expected)

    def test_phase_filters_keep_country_scope_and_default_lifecycle_compatibility(self):
        filters = normalize_run_status_filters(country_code="US", states=["queued", "discovering", "skipped"], run_type=None,
            partial_only=False, started_from=None, started_to=None, search="BANK", sort_by="started_at", sort_order="desc", page=1, page_size=20)
        sql, params = _build_where_clause(filters)
        self.assertEqual(params["country_code"], "US")
        self.assertEqual(params["states"], ["queued", "discovering", "skipped"])
        self.assertIn("collection_phase", sql)
        self.assertIn("bank_code", sql)
        self.assertIn("ir.run_state::text", sql)
