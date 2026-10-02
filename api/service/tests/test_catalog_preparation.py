from __future__ import annotations

from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from api_service import source_catalog as catalog, source_catalog_collection_runner as runner
from api_service.catalog_preparation import (
    preparation_signature, preparation_block_reason, reserve_preparation,
    claim_preparation, probe_sources,
)
from api_service.run_retry import retry_failed_run
from tests.test_source_catalog import _product_type_definition
from tests.test_source_catalog_collection_runner import _Connection, _ConnectionContext
from tests.test_run_retry import _QueuedConnection
from worker.discovery.fpds_discovery.fetch import DiscoveryFetchPolicy, FetchedResponse, _html_access_challenge_kind


def group():
    return {"run_id": "future-run", "catalog_item_id": "catalog", "country_code": "US",
            "bank_code": "BANK", "bank_name": "Example Bank", "product_type": "gic",
            "source_language": "en", "homepage_url": "https://bank.example",
            "normalized_homepage_url": "https://bank.example", "coverage_source_url": "https://bank.example/cds",
            "coverage_source_metadata": {}, "source_coverage_mode": "precision", "has_completed_collection": False}


def source(source_id="DETAIL", role="detail", source_type="html"):
    return {"source_id": source_id, "source_url": "https://bank.example/" + source_id.lower(),
            "normalized_url": "https://bank.example/" + source_id.lower(), "source_type": source_type,
            "discovery_role": role, "status": "active", "country_code": "US", "bank_code": "BANK",
            "source_language": "en", "product_type": "gic", "discovery_metadata": {}}


def response(body=b"<html>Product detail</html>", content_type="text/html"):
    return FetchedResponse(body=body, final_url="https://bank.example/page", content_type=content_type,
                           status_code=200, headers={"content-type": content_type}, fetched_at="now", redirect_count=0)


class CatalogPreparationTests(unittest.TestCase):
    def test_product_identity_handles_plural_cds_and_named_checking_across_hosts(self):
        for host in ("bank.example", "another.example"):
            for product_type, path, title in (
                ("gic", "/personal/savings/certificates-of-deposit", "Certificates of Deposit (CDs)"),
                ("gic", "/cds", "Personal CDs"),
                ("chequing", "/checking/personal-checking", "Personal Checking"),
                ("chequing", "/checking/interest-checking", "Personal Interest Checking"),
            ):
                html = f"<title>{title}</title><h1>{title}</h1><p>Interest rate and minimum balance. Monthly fee. Term and maturity.</p>"
                with patch.object(catalog, "fetch_text", return_value=html):
                    evidence = catalog._score_page_evidence(raw_url=f"https://{host}{path}", fetch_policy=None,
                        product_type=product_type, product_type_definition=_product_type_definition(product_type))
                self.assertGreaterEqual(evidence.page_evidence_score, 6, evidence)
                self.assertEqual(evidence.negative_signal_count, 0)
        self.assertEqual(catalog._identity_term_hits("ABCD account", ["cd"]), 0)

    def test_rates_information_and_faq_do_not_create_fake_savings_variants(self):
        common = dict(product_type="savings", title_text="Personal Savings Accounts | Bank",
                      primary_heading="Personal Savings Account")
        self.assertFalse(catalog._looks_like_multi_product_family_overview(**common,
            secondary_headings=["Savings Rates", "Personal Savings Account Information", "What is a savings account?"]))
        self.assertTrue(catalog._looks_like_multi_product_family_overview(**common,
            secondary_headings=["Youth Savings Account", "High Interest Savings Account"]))
        self.assertTrue(catalog._looks_like_multi_product_family_overview(product_type="line-of-credit",
            title_text="Home Equity", primary_heading="Home Equity Loans & Lines of Credit", secondary_headings=[]))

    def test_cloudflare_block_page_is_not_financial_evidence(self):
        blocked = response(b"<title>Attention Required!</title><h1>Sorry, you have been blocked</h1><div>Cloudflare Ray ID</div>")
        self.assertEqual(_html_access_challenge_kind(blocked), "managed_access_challenge")
        self.assertIsNone(_html_access_challenge_kind(response(b"<h1>Checking</h1><p>You are unable to access overdraft until eligible.</p>")))

    def test_access_probe_excludes_redirect_and_bad_format_without_changing_allowlist(self):
        policy = DiscoveryFetchPolicy(allowed_domains=("bank.example",))
        rows = [source(), source("FEES", "supporting_html"), source("PDF", "linked_pdf", "pdf")]
        with patch("worker.discovery.fpds_discovery.fetch.fetch_response", side_effect=[response(), ValueError("Host not in discovery fetch allowlist: media.example"), response()] ) as fetch:
            available, excluded = probe_sources(rows, policy=policy)
        self.assertEqual(available, ["DETAIL"])
        self.assertEqual({r["source_id"] for r in excluded}, {"FEES", "PDF"})
        self.assertTrue(all(r["reason_code"] == "terminal_source_failure" for r in excluded))
        self.assertTrue(all(c.args[1].allowed_domains == ("bank.example",) for c in fetch.call_args_list))

    def test_transient_probe_can_be_retried_and_valid_pdf_remains_eligible(self):
        policy = DiscoveryFetchPolicy(allowed_domains=("bank.example",))
        with patch("worker.discovery.fpds_discovery.fetch.fetch_response", side_effect=[TimeoutError("timed out"), response(b"%PDF-1.7 data", "application/pdf")]):
            held = {**source(), "latest_review_state": "deferred", "latest_review_action": "defer", "latest_review_actor": "reviewer"}
            available, excluded = probe_sources([held, source("PDF", "linked_pdf", "pdf")], policy=policy)
        self.assertEqual(available, ["PDF"])
        self.assertTrue(excluded[0]["retryable"])

    def test_known_terminal_companion_is_not_refetched_for_each_scope_in_batch(self):
        cache = {}
        with patch("worker.discovery.fpds_discovery.fetch.fetch_response", side_effect=ValueError("Host not in discovery fetch allowlist: media.example")) as fetch:
            for _ in range(2):
                probe_sources([source("FEES", "supporting_html")], policy=DiscoveryFetchPolicy(allowed_domains=("bank.example",)), cache=cache)
        self.assertEqual(fetch.call_count, 1)

    def test_revalidation_does_not_duplicate_active_preparation_and_expired_work_can_retry(self):
        row = group()
        state = {"status": "checking", "updated_at": datetime.now(UTC).isoformat(), "signature": preparation_signature(row)}
        row["coverage_source_metadata"] = {"collection_preparation": state}
        self.assertEqual(preparation_block_reason(row, explicit=True), "collection_preparation_in_progress")
        state["status"] = "collecting"
        self.assertEqual(preparation_block_reason(row, explicit=True), "collection_preparation_in_progress")
        state["status"] = "checking"
        state["updated_at"] = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
        self.assertIsNone(preparation_block_reason(row, explicit=False))
        state.update(status="skipped", retryable=False)
        self.assertEqual(preparation_block_reason(row, explicit=False), "preparation_requires_rediscovery")
        self.assertIsNone(preparation_block_reason(row, explicit=True))
        row["coverage_source_metadata"]["verification_status"] = "verified"
        self.assertIsNone(preparation_block_reason(row, explicit=False))
        row["coverage_source_url"] += "/changed"
        self.assertIsNone(preparation_block_reason(row, explicit=False))

    def test_reservation_and_claim_use_scoped_ownership(self):
        g = group(); plan = {"collection_id": "operation"}
        c = _Connection([{"catalog_item_id": "catalog"}])
        self.assertTrue(reserve_preparation(c, group=g, plan=plan))
        self.assertIn("country_code", c.calls[0][0])
        row = {**g, "status": "active", "coverage_source_metadata": {"collection_preparation": {"operation_id": "newer"}}}
        c = _Connection([row])
        self.assertFalse(claim_preparation(c, group=g, plan=plan))
        self.assertEqual(len(c.calls), 1)

    def run_preparation(self, *, detail=True, probe_result=None, claims=None, registered=False):
        g = group(); plan = {"collection_id": "operation", "correlation_id": "corr", "actor": {},
                            "preflight_before_run": True, "triggered_by": "tester", "runs_registered": registered}
        c = MagicMock(); c.__enter__.return_value = c
        rows = [source(), source("FEES", "supporting_html")] if detail else []
        generated = catalog.CatalogItemMaterializationResult(generated_rows=rows,
                    detail_source_ids=["DETAIL"] if detail else [], discovery_notes=["No detail sources"] if not detail else [])
        scope = {"collection_source_ids": [], "target_source_ids": []}
        with ExitStack() as stack:
            stack.enter_context(patch.object(runner, "open_connection", return_value=c))
            claim = stack.enter_context(patch.object(runner, "claim_preparation", side_effect=claims or [True, True]))
            update = stack.enter_context(patch.object(runner, "update_preparation", return_value=True))
            materialize = stack.enter_context(patch.object(runner, "_materialize_sources_for_catalog_item", return_value=generated))
            stack.enter_context(patch.object(runner, "_load_active_collection_scope", return_value=scope))
            stack.enter_context(patch.object(runner, "repair_catalog_coverage_route", return_value=catalog.CoverageRouteRepairResult(status="uncertain", coverage_source_url=None, coverage_source_metadata={}, notes=[])))
            stack.enter_context(patch.object(runner, "load_source_preflight_rows", return_value=rows))
            stack.enter_context(patch.object(runner, "probe_sources", return_value=probe_result or (["DETAIL", "FEES"], [])))
            prepare = stack.enter_context(patch.object(runner, "prepare_source_collection", return_value={"plan": {"triggered_by": "tester", "groups": [{**g, "included_source_ids": ["DETAIL"], "target_source_ids": ["DETAIL"]}]}}))
            insert = stack.enter_context(patch.object(runner, "_insert_collection_run_row"))
            finish = stack.enter_context(patch.object(runner, "_mark_run_finished"))
            collect = stack.enter_context(patch.object(runner.source_collection_runner, "_run_group"))
            runner._run_group(plan=plan, group=g)
        return SimpleNamespace(group=g, connection=c, materialize=materialize, prepare=prepare, insert=insert,
                               finish=finish, collect=collect, update=update, claim=claim)

    def test_registered_discovery_without_details_finishes_visible_skipped_run(self):
        result = self.run_preparation(detail=False, registered=True)
        result.insert.assert_not_called()
        result.collect.assert_not_called()
        result.finish.assert_called_once()
        self.assertEqual(result.finish.call_args.kwargs["run_state"], "completed")
        self.assertEqual(result.finish.call_args.kwargs["run_metadata"]["collection_phase"], "skipped")
        self.assertEqual(result.finish.call_args.kwargs["run_metadata"]["preparation_reason_codes"], ["no_eligible_detail"])
        self.assertEqual(result.materialize.call_args.kwargs["run_id"], "future-run")
        self.assertTrue(any('"collection_phase":"discovering"' in call.args[0] for call in result.connection.execute.call_args_list))

    def test_registered_inaccessible_detail_finishes_skipped_run(self):
        result = self.run_preparation(registered=True, probe_result=([], [{"source_id": "DETAIL", "reason_code": "terminal_source_failure"}]))
        result.collect.assert_not_called()
        self.assertEqual(result.finish.call_args.kwargs["run_metadata"]["collection_phase"], "skipped")

    def test_registered_transient_detail_failure_is_retryable_failed_run(self):
        result = self.run_preparation(registered=True, probe_result=([], [{"source_id": "DETAIL", "reason_code": "source_temporarily_unavailable", "retryable": True}]))
        self.assertEqual(result.finish.call_args.kwargs["run_state"], "failed")
        self.assertFalse(result.finish.call_args.kwargs["partial_completion_flag"])
        result.collect.assert_not_called()

    def test_registered_superseded_coverage_finishes_only_own_run(self):
        result = self.run_preparation(registered=True, claims=[False])
        result.materialize.assert_not_called()
        result.finish.assert_called_once()
        result.collect.assert_not_called()
        self.assertEqual(result.finish.call_args.kwargs["run_id"], "future-run")
        self.assertEqual(result.finish.call_args.kwargs["run_state"], "failed")

    def test_registered_coverage_changed_during_probe_does_not_leave_discovering(self):
        result = self.run_preparation(registered=True, claims=[True, False])
        result.connection.rollback.assert_called_once()
        self.assertEqual(result.finish.call_args.kwargs["run_state"], "failed")
        result.collect.assert_not_called()

    def test_registered_detail_reuses_run_id_for_collection_and_commits_first(self):
        result = self.run_preparation(registered=True)
        result.insert.assert_called_once()
        result.collect.assert_called_once()
        self.assertEqual(result.insert.call_args.kwargs["run_id"], "future-run")
        self.assertGreaterEqual(result.connection.commit.call_count, 2)

    def test_first_discovery_without_detail_never_creates_or_finishes_a_run(self):
        result = self.run_preparation(detail=False)
        result.insert.assert_not_called(); result.finish.assert_not_called(); result.collect.assert_not_called()
        self.assertIsNone(result.materialize.call_args.kwargs["run_id"])
        self.assertEqual(result.update.call_args.kwargs["status"], "skipped")

    def test_valid_detail_and_inaccessible_companion_create_only_one_real_run(self):
        result = self.run_preparation(probe_result=(["DETAIL"], [{"source_id": "FEES", "reason_code": "terminal_source_failure"}]))
        result.insert.assert_called_once(); result.collect.assert_called_once()
        self.assertTrue(result.group["ingestion_started"])
        self.assertEqual(result.prepare.call_args.kwargs["source_ids"], ["DETAIL"])
        self.assertEqual(result.prepare.call_args.kwargs["excluded_source_ids"], ["FEES"])
        self.assertEqual(result.update.call_args.kwargs["run_id"], "future-run")

    def test_no_accessible_detail_skips_before_run_even_for_first_collection(self):
        result = self.run_preparation(probe_result=([], [{"source_id": "DETAIL", "reason_code": "terminal_source_failure"}]))
        result.insert.assert_not_called(); result.collect.assert_not_called()
        self.assertEqual(result.update.call_args.kwargs["status"], "skipped")

    def test_preparation_persistence_failure_is_contained_for_next_bank(self):
        with patch.object(runner, "open_connection", side_effect=RuntimeError("temporary database failure")):
            runner._mark_preparation_best_effort(plan={"collection_id": "operation"}, group=group(), status="unavailable")

    def test_coverage_changed_during_probe_rolls_back_before_run(self):
        result = self.run_preparation(claims=[True, False])
        result.insert.assert_not_called(); result.collect.assert_not_called()
        result.connection.rollback.assert_called_once()

    def test_registered_retry_exposes_queue_id_without_superseding_original_outcome(self):
        c = _QueuedConnection([{"run_id": "old", "run_state": "completed", "partial_completion_flag": True,
                               "retried_by_run_id": None, "run_type": "source_catalog_collection",
                               "run_metadata": {"catalog_item_id": "catalog"}}])
        with patch("api_service.run_retry.start_source_catalog_collection", return_value={"workflow_state": "queued", "preflight_pending": True, "run_ids": ["new"], "collection_id": "operation"}):
            result = retry_failed_run(c, run_id="old", actor={}, request_context={})
        self.assertEqual(result["retry_run_id"], "new")
        self.assertEqual(result["workflow_state"], "queued")
        self.assertFalse(any("UPDATE ingestion_run" in sql for sql, _ in c.calls))

    def test_retry_preparation_preserves_the_original_partial_until_replacement_exists(self):
        c = _QueuedConnection([{"run_id": "old", "run_state": "completed", "partial_completion_flag": True,
                               "retried_by_run_id": None, "run_type": "source_catalog_collection",
                               "run_metadata": {"catalog_item_id": "catalog"}}])
        with patch("api_service.run_retry.start_source_catalog_collection", return_value={"workflow_state": "preparing", "run_ids": [], "collection_id": "operation"}):
            result = retry_failed_run(c, run_id="old", actor={}, request_context={})
        self.assertEqual(result["workflow_state"], "preparing")
        self.assertIsNone(result["retry_run_id"])
        self.assertFalse(any("UPDATE ingestion_run" in sql for sql, _ in c.calls))
