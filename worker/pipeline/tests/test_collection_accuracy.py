from __future__ import annotations
import unittest
from copy import deepcopy
from worker.pipeline.fpds_collection_accuracy import (
    sanitize_candidate, acceptance_receipt_valid, quote_supports_value, RECEIPT_KEY,
)
from worker.pipeline.fpds_field_contract import value_matches_contract


def candidate_fixture():
    payload = {"product_name":"Example Savings", "standard_rate":2.5, "monthly_fee":0, "minimum_balance":0}
    quotes = {"product_name":"Example Savings in Canadian dollars", "standard_rate":"Annual interest rate 2.5% in CAD", "monthly_fee":"Monthly fee $0 CAD", "minimum_balance":"Minimum balance $0 CAD"}
    mappings = {name:{"normalized_value":value, "evidence_chunk_id":name,
                "official_grounding_contract_version":"collection-official-grounding-v2",
                "official_verification_status":"match", "official_evidence_quote":quotes[name],
                "official_web_sources":[{"url":"https://bank.example/savings"}]}
                for name,value in payload.items()}
    row = {"country_code":"CA","bank_code":"EXAMPLE","product_type":"savings",
           "product_name":"Example Savings","currency":"CAD", "candidate_payload":payload,
           "field_mapping_metadata":mappings}
    evidence=[{"evidence_chunk_id":name,"source_url":"https://bank.example/savings","evidence_excerpt":quote} for name,quote in quotes.items()]
    metadata={"discovery_role":"detail","official_domain_allowlist":["bank.example"],"expected_fields":list(payload)}
    return row,metadata,evidence


class CollectionAccuracyTests(unittest.TestCase):
    def test_zero_money_requires_the_same_financial_attribute(self):
        invalid = [
            ("minimum_balance", "Minimum daily balance $4,000 for bonus points. Family members get no fee daily banking."),
            ("minimum_deposit", "Minimum opening deposit $100. No monthly fee."),
            ("annual_fee", "Annual fee $99. No transaction fee."),
            ("transaction_fee", "Transaction fee $2. No annual fee."),
        ]
        for field, quote in invalid:
            with self.subTest(field=field, quote=quote):
                self.assertFalse(quote_supports_value(field, 0, quote))
        valid = [
            ("minimum_balance", "No minimum balance required"),
            ("minimum_deposit", "No minimum deposit"),
            ("monthly_fee", "No monthly account fee"),
            ("annual_fee", "No annual fee"),
            ("transaction_fee", "No transaction fee"),
            ("minimum_balance", "Minimum balance $0 CAD"),
        ]
        for field, quote in valid:
            with self.subTest(field=field, quote=quote):
                self.assertTrue(quote_supports_value(field, 0, quote))

    def test_family_fee_benefit_cannot_prove_zero_balance(self):
        row, meta, evidence = candidate_fixture()
        quote = ("Earn 500 Bonus Points every month with a minimum daily balance of $4,000 "
                 "or more in your chequing account. Family members in your household get "
                 "no fee daily banking with Family Bundle.")
        row["field_mapping_metadata"]["minimum_balance"]["official_evidence_quote"] = quote
        evidence[-1]["evidence_excerpt"] = quote
        result, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertFalse(receipt["accepted"])
        self.assertNotIn("minimum_balance", result["candidate_payload"])
        self.assertEqual(receipt["omitted_fields"]["minimum_balance"], "field_meaning_unproven")

    def test_transaction_fee_waiver_balance_is_not_a_general_minimum(self):
        row, meta, evidence = candidate_fixture()
        row["candidate_payload"]["minimum_balance"] = 1500
        quote = "Minimum monthly balance for no transaction fees 2\n$1,500 CAD"
        row["field_mapping_metadata"]["minimum_balance"].update(normalized_value=1500, official_evidence_quote=quote)
        evidence[-1]["evidence_excerpt"] = quote
        result, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertNotIn("minimum_balance", result["candidate_payload"])
        self.assertEqual(receipt["omitted_fields"]["minimum_balance"], "transaction_waiver_balance_not_minimum")
        self.assertFalse(receipt["accepted"])
        row["field_mapping_metadata"]["minimum_balance"]["official_evidence_quote"] = "Minimum balance $1,500 CAD"
        evidence[-1]["evidence_excerpt"] = "Minimum balance $1,500 CAD for no transaction fees"
        self.assertEqual(sanitize_candidate(row, source_metadata=meta, evidence=evidence)[1]["omitted_fields"]["minimum_balance"],
                         "transaction_waiver_balance_not_minimum")
        quote = "Minimum balance $1,500 CAD"
        row["field_mapping_metadata"]["minimum_balance"]["official_evidence_quote"] = quote
        evidence[-1]["evidence_excerpt"] = quote
        self.assertTrue(sanitize_candidate(row, source_metadata=meta, evidence=evidence)[1]["accepted"])

    def test_extraction_records_why_a_required_count_was_omitted(self):
        from unittest.mock import patch
        from worker.pipeline.fpds_extraction.models import ExtractionDocumentContext
        from worker.pipeline.fpds_evidence_retrieval.models import EvidenceChunkCandidate
        from worker.pipeline.fpds_extraction.service import _extract_official_fields_with_ai
        url = "https://bank.example/usd-chequing"
        context = ExtractionDocumentContext("parsed", "source", "snapshot", "EXAMPLE", "CA", "html", "en",
            {"product_type": "chequing", "discovery_role": "detail", "official_domain_allowlist": ["bank.example"],
             "normalized_source_url": url, "expected_fields": ["included_transactions"]})
        quote = "One free Everyday Transaction per month"
        chunk = EvidenceChunkCandidate("chunk", "parsed", 0, "section", "account", None, "en", quote,
            {}, "source", "snapshot", "EXAMPLE", "CA", "html")
        field = {"field_name": "included_transactions", "status": "match", "has_verified_value": True,
                 "verified_value_json": "1", "evidence_chunk_id": "chunk", "evidence_quote": quote,
                 "confidence": 0.99, "sources": [{"url": url}]}
        usage = {"model_id": "gpt-6-luna", "web_search_sources": [{"url": url}]}
        cases = [(field, None), ({**field, "verified_value_json": '\"1\"'}, "invalid_field_type"),
                 ({**field, "evidence_quote": "One free transaction"}, "exact_quote_missing"),
                 ({**field, "evidence_chunk_id": "invented"}, "evidence_chunk_missing"),
                 ({**field, "status": "unverified", "evidence_chunk_id": ""}, "model_unverified")]
        for response_field, reason in cases:
            with self.subTest(reason=reason), patch("worker.pipeline.fpds_extraction.service.invoke_openai_json_schema",
                    return_value=({"fields": [response_field]}, usage)) as invoke:
                fields, notes, _ = _extract_official_fields_with_ai(context=context, candidates=[chunk],
                    requested_fields=["included_transactions"], collected_fields=[])
                self.assertEqual(len(fields), 0 if reason else 1)
                self.assertIn("A fact mentioned only in summary is not collected", invoke.call_args.kwargs["instructions"])
                if reason:
                    self.assertIn(reason, " ".join(notes))
                else:
                    self.assertIs(type(fields[0].candidate_value), int)
                    self.assertEqual(fields[0].candidate_value, 1)

    def test_written_transaction_counts_keep_native_integer_meaning(self):
        quote = "One free Everyday Transaction per month, including Everyday In-Person, Cheque or Pre-Authorized Payments"
        self.assertTrue(quote_supports_value("included_transactions", 1, quote))
        self.assertFalse(quote_supports_value("included_transactions", 2, quote))
        for invalid in ("One free transaction if you maintain $1000", "Up to one free transaction",
                        "1.5 free transactions", "-1 free transaction", "One or two free transactions", "Between one and two free transactions",
                        "Twenty one free transactions", "One hundred and one free transactions"):
            self.assertFalse(quote_supports_value("included_transactions", 1, invalid), invalid)
        self.assertFalse(quote_supports_value("included_transactions", "1", quote))
        self.assertFalse(quote_supports_value("included_transactions", 2, "One or two free transactions"))
        self.assertFalse(quote_supports_value("included_transactions", 0, "1,000 free transactions"))
        self.assertTrue(quote_supports_value("included_transactions", 1000, "1,000 free transactions"))

    def test_suitability_heading_is_separate_from_zero_fee_conditions(self):
        quote = "USD Chequing\nA smarter way to keep your US dollars.\nOpen an account\nMonthly fee\n$0\nGreat if\nYou want protection from rate fluctuations"
        self.assertTrue(quote_supports_value("monthly_fee", 0, quote))
        for condition in ("\nif you maintain a balance of $1000", "\nMinimum balance $1000", "\nFee waived for qualifying members"):
            self.assertFalse(quote_supports_value("monthly_fee", 0, quote + condition))
        self.assertFalse(quote_supports_value("monthly_fee", 0, "Monthly fee $0\nIf you maintain a balance of $1000"))

    def test_captured_chequing_layout_accepts_only_grounded_facts(self):
        # Shape reproduced from the live pilot, including the original line breaks.
        payload = {"product_name": "USD Chequing", "monthly_fee": 0, "included_transactions": 1}
        quotes = {"product_name": "USD Chequing", "monthly_fee": "Monthly fee\n$0",
                  "included_transactions": "One free Everyday Transaction per month"}
        chunks = {"product_name": "USD Chequing\nA smarter way to keep your US dollars.",
                  "monthly_fee": "USD Chequing\nOpen an account\nMonthly fee\n$0\nGreat if\nYou want protection from rate fluctuations",
                  "included_transactions": "With this account you get:\nOne free Everyday Transaction per month, including Everyday In-Person, Cheque or Pre-Authorized Payments\nEasy transfers between your Canadian and US dollar accounts through the mobile app or online banking\nIncludes ATM transfers between accounts"}
        mappings = {name: {"normalized_value": value, "evidence_chunk_id": name,
                    "official_grounding_contract_version": "collection-official-grounding-v2",
                    "official_verification_status": "match", "official_evidence_quote": quotes[name],
                    "official_web_sources": [{"url": "https://bank.example/usd-chequing"}]}
                    for name, value in payload.items()}
        row = {"country_code": "CA", "bank_code": "EXAMPLE", "product_type": "chequing",
               "product_name": "USD Chequing", "currency": "USD", "candidate_payload": payload,
               "field_mapping_metadata": mappings}
        evidence = [{"evidence_chunk_id": name, "source_url": "https://bank.example/usd-chequing", "evidence_excerpt": excerpt}
                    for name, excerpt in chunks.items()]
        meta = {"discovery_role": "detail", "official_domain_allowlist": ["bank.example"], "expected_fields": list(payload)}
        result, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertTrue(receipt["accepted"], receipt)
        self.assertTrue(acceptance_receipt_valid(result, result["candidate_payload"]))
        self.assertIs(type(result["candidate_payload"]["included_transactions"]), int)
        evidence[2]["evidence_excerpt"] += " if you maintain a $1000 balance"
        _, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertFalse(receipt["accepted"])
        self.assertEqual(receipt["omitted_fields"]["included_transactions"], "evidence_context_ambiguous")

    def test_annual_fee_cannot_prove_annual_interest_basis(self):
        row, meta, evidence = candidate_fixture()
        quote = "Interest rate 2.5% CAD. Annual fee $39 CAD."
        evidence[1]["evidence_excerpt"] = quote
        row["field_mapping_metadata"]["standard_rate"]["official_evidence_quote"] = "Interest rate 2.5% CAD."
        _, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertEqual(receipt["omitted_fields"]["standard_rate"], "annual_rate_basis_unproven")
        evidence[1]["evidence_excerpt"] = "Interest rate 2.5% CAD. Annual interest payment date: December 31."
        _, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertEqual(receipt["omitted_fields"]["standard_rate"], "annual_rate_basis_unproven")

    def test_native_finite_types_and_structured_rows(self):
        for v in ("2.5", True, float("nan"), float("inf"), -1):
            self.assertFalse(value_matches_contract("standard_rate",v))
        for v in (1.5, "12", True, -1):
            self.assertFalse(value_matches_contract("term_length_days",v))
        for v in ({"rate":2}, [{"term_label":"1 year","rate":"2"}], [{"term_label":"1 year","rate":True}], [{"term_label":"1 year","rate":2,"extra":"guess"}]):
            self.assertFalse(value_matches_contract("term_rate_table",v))
        self.assertTrue(value_matches_contract("term_rate_table",[{"term_label":"1 year","rate":2.5,"minimum_deposit":1000}]))

    def test_exact_numeric_token_and_percentage_unit(self):
        self.assertFalse(quote_supports_value("standard_rate",2,"Interest rate 2.5%"))
        self.assertFalse(quote_supports_value("standard_rate",2.5,"Deposit $2.50; 100 transactions"))
        self.assertFalse(quote_supports_value("standard_rate",0.5,"An interest rate discount of 0.5%"))
        self.assertTrue(quote_supports_value("standard_rate",2.5,"Annual interest rate 2.50%"))

    def test_prose_and_boolean_cannot_pass_vacuous_number_check(self):
        self.assertFalse(quote_supports_value("security_requirement","No collateral required","Apply today"))
        self.assertFalse(quote_supports_value("secured_flag",True,"Apply today"))
        self.assertTrue(quote_supports_value("secured_flag",False,"This is an unsecured loan"))
        self.assertFalse(quote_supports_value("secured_flag",True,"This is an unsecured loan"))
        self.assertTrue(quote_supports_value("redeemable_flag",False,"This is non-redeemable"))
        self.assertFalse(quote_supports_value("term_length_days",365,"A 12 month term"))

    def test_rates_and_counts_do_not_cross_meanings_or_conditions(self):
        for quote in ("Interest rate 2.5% to 4%", "Earn an interest rate up to 2.5%", "Interest rate 2.5% if you qualify"):
            self.assertFalse(quote_supports_value("standard_rate", 2.5, quote))
        self.assertFalse(quote_supports_value("purchase_interest_rate", 22.9, "Cash advance interest rate 22.9%"))
        self.assertFalse(quote_supports_value("included_transactions", 12, "Monthly fee $12; 20 transactions"))
        self.assertTrue(quote_supports_value("included_transactions", 20, "20 included transactions"))
        self.assertTrue(quote_supports_value("monthly_fee", 0, "No monthly fee"))
        self.assertFalse(quote_supports_value("monthly_fee", 0, "No monthly fee if balance is $5,000"))
        self.assertFalse(quote_supports_value("monthly_fee", 5000, "Monthly fee $12 waived with a balance of $5,000"))

    def test_short_quote_cannot_hide_qualifying_source_context(self):
        row, meta, evidence = candidate_fixture()
        evidence[1]["evidence_excerpt"] += " if you maintain a balance of $10,000"
        result, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertFalse(receipt["accepted"])
        self.assertNotIn("standard_rate", result["candidate_payload"])
        self.assertEqual(receipt["omitted_fields"]["standard_rate"], "evidence_context_ambiguous")
        self.assertFalse(quote_supports_value("standard_rate", 2.5, "Annual interest rate -2.5%"))
        self.assertFalse(quote_supports_value("interest_rate_summary", "Interest rate 5%", "Interest rate 5% if you qualify"))

    def test_rate_requires_explicit_annual_basis(self):
        row, meta, evidence = candidate_fixture()
        quote = "Monthly interest rate 2.5% CAD"
        row["field_mapping_metadata"]["standard_rate"]["official_evidence_quote"] = quote
        evidence[1]["evidence_excerpt"] = quote
        _, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
        self.assertEqual(receipt["omitted_fields"]["standard_rate"], "annual_rate_basis_unproven")

    def test_term_table_cannot_borrow_another_terms_rate(self):
        row = [{"term_label":"1 year", "rate":2.5}]
        self.assertTrue(quote_supports_value("term_rate_table", row, "1 year 2.5% annual interest"))
        self.assertFalse(quote_supports_value("term_rate_table", row, "11 year 2.5% annual interest"))
        self.assertFalse(quote_supports_value("term_rate_table", row, "1 year unavailable; 2 year 2.5% annual interest"))
        self.assertFalse(quote_supports_value("term_rate_table", row, "1 year -2.5% annual interest"))

    def test_foreign_currency_fee_cannot_enter_domestic_product(self):
        for quote in ("Monthly fee $0 USD", "Monthly fee €0"):
            row, meta, evidence = candidate_fixture()
            row["field_mapping_metadata"]["monthly_fee"]["official_evidence_quote"] = quote
            evidence[2]["evidence_excerpt"] = quote
            result, receipt = sanitize_candidate(row, source_metadata=meta, evidence=evidence)
            self.assertNotIn("monthly_fee", result["candidate_payload"])
            self.assertEqual(receipt["omitted_fields"]["monthly_fee"], "field_currency_mismatch")

    def test_correct_candidate_gets_content_bound_receipt(self):
        row,meta,evidence=candidate_fixture()
        result,receipt=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
        self.assertTrue(receipt["accepted"],receipt)
        self.assertTrue(acceptance_receipt_valid(result))
        result["candidate_payload"]["standard_rate"]=25
        self.assertFalse(acceptance_receipt_valid(result))

    def test_omit_optional_unsupported_fact_without_human_queue(self):
        row,meta,evidence=candidate_fixture()
        row["candidate_payload"]["minimum_deposit"]=100
        result,receipt=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
        self.assertNotIn("minimum_deposit",result["candidate_payload"])
        self.assertTrue(receipt["accepted"])
        self.assertEqual(receipt["omitted_fields"]["minimum_deposit"],"value_changed_after_grounding")

    def test_missing_essential_quote_or_provider_proof_excludes(self):
        for change in ("quote", "url", "proof", "type", "changed"):
            row,meta,evidence=candidate_fixture()
            m=row["field_mapping_metadata"]["standard_rate"]
            if change=="quote":m["official_evidence_quote"]="Annual interest rate 9%"
            if change=="url":m["official_web_sources"]=[{"url":"https://other.example/savings"}]
            if change=="proof":m.pop("official_grounding_contract_version")
            if change=="type":row["candidate_payload"]["standard_rate"]="2.5"
            if change=="changed":row["candidate_payload"]["standard_rate"]=3
            result,receipt=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
            self.assertFalse(receipt["accepted"],change)
            self.assertNotIn("standard_rate",result["candidate_payload"])

    def test_unknown_currency_and_supporting_page_exclude(self):
        row,meta,evidence=candidate_fixture()
        row["currency"]="USD"
        _,receipt=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
        self.assertIn("product_currency_unverified",receipt["reasons"])
        row["currency"]="CAD"; meta["discovery_role"]="supporting"
        _,receipt=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
        self.assertIn("source_is_not_product_detail",receipt["reasons"])

    def test_new_projection_guard_preserves_legacy_and_hides_tampered_receipt(self):
        from dataclasses import replace
        from worker.pipeline.fpds_aggregate_refresh.models import CanonicalAggregateRow
        from worker.pipeline.fpds_aggregate_refresh.service import AggregateRefreshService
        row,meta,evidence=candidate_fixture()
        accepted,_=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
        item=CanonicalAggregateRow(product_id="valid",bank_code="EXAMPLE",bank_name="Example Bank",country_code="CA",
            product_family="deposit",product_type="savings",subtype_code="standard",product_name=row["product_name"],
            source_language="en",currency="CAD",status="active",last_verified_at="2026-09-30T00:00:00Z",
            last_changed_at=None,product_version_id="version-1",canonical_payload=accepted["candidate_payload"])
        tampered=replace(item,product_id="tampered",canonical_payload={**item.canonical_payload,"monthly_fee":50})
        legacy=replace(item,product_id="legacy",canonical_payload=row["candidate_payload"])
        result=AggregateRefreshService().build_snapshot(snapshot_id="test",refresh_scope="all_active_products",country_code="CA",canonical_rows=[item,tampered,legacy])
        self.assertEqual({r["product_id"] for r in result.projection_rows},{"valid","legacy"})
        self.assertEqual(result.refresh_metadata["source_counts"]["excluded_accuracy_rows"],1)
        import json
        self.assertNotIn(RECEIPT_KEY,json.dumps(result.projection_rows))

    def test_no_allowlist_and_fake_receipt_fail_closed(self):
        row,meta,evidence=candidate_fixture()
        meta["official_domain_allowlist"]=[]
        _,receipt=sanitize_candidate(row,source_metadata=meta,evidence=evidence)
        self.assertFalse(receipt["accepted"])
        self.assertFalse(acceptance_receipt_valid(row))


class CollectionAccuracyIntegrationTests(unittest.TestCase):
    def test_real_normalization_validation_accept_or_exclude_without_review(self):
        from tempfile import TemporaryDirectory
        from dataclasses import replace
        from worker.pipeline.fpds_normalization.models import NormalizationInput, NormalizationExtractedField, NormalizationEvidenceLink
        from worker.pipeline.fpds_normalization.service import NormalizationService
        from worker.pipeline.fpds_normalization.storage import NormalizationStorageConfig, build_object_store
        from worker.pipeline.fpds_validation_routing.models import ValidationInput, ValidationEvidenceLink, ValidationRoutingConfig
        from worker.pipeline.fpds_validation_routing.service import ValidationRoutingService
        from worker.pipeline.fpds_validation_routing.storage import ValidationRoutingStorageConfig
        from worker.pipeline.fpds_field_contract import canonical_value_type
        row, meta, evidence = candidate_fixture()
        meta = {**meta, "normalized_source_url":"https://bank.example/savings", "product_type":"savings"}
        fields=[]; links=[]
        for name,value in row["candidate_payload"].items():
            m = row["field_mapping_metadata"][name]
            quote=m["official_evidence_quote"]
            fields.append(NormalizationExtractedField(field_name=name,candidate_value=value,
                value_type=canonical_value_type(name), confidence=.99, extraction_method="openai_official_grounding",
                source_document_id="src-1", source_snapshot_id="snap-1", evidence_chunk_id=name,
                evidence_text_excerpt=quote,anchor_type="heading",anchor_value="Example Savings",page_no=None,chunk_index=0,
                field_metadata={"official_grounding_contract_version":"collection-official-grounding-v2",
                    "official_verification_status":"match","official_web_sources":m["official_web_sources"],"evidence_quote":quote}))
            links.append(NormalizationEvidenceLink(field_name=name,candidate_value=str(value),evidence_chunk_id=name,
                evidence_text_excerpt=quote,source_document_id="src-1",source_snapshot_id="snap-1",citation_confidence=.99,
                model_execution_id="extract-1",anchor_type="heading",anchor_value="Example Savings",page_no=None,chunk_index=0))
        item=NormalizationInput(source_id="source-1",source_document_id="src-1",snapshot_id="snap-1",parsed_document_id="parsed-1",
            extraction_model_execution_id="extract-1",extracted_storage_key="input",metadata_storage_key=None,bank_code="EXAMPLE",
            country_code="CA",source_type="html",source_language="en",source_metadata=meta,
            schema_context={"product_type":"savings","product_family":"deposit","country_code":"CA"},
            extracted_fields=fields,evidence_links=links,runtime_notes=[],normalized_source_url=meta["normalized_source_url"])
        with TemporaryDirectory(dir="tmp") as temp:
            config=NormalizationStorageConfig(driver="filesystem",env_prefix="test",normalization_object_prefix="normalized",retention_class="hot",filesystem_root=temp)
            store=build_object_store(config)
            normalizer=NormalizationService(storage_config=config,object_store=store)
            validator=ValidationRoutingService(storage_config=ValidationRoutingStorageConfig(driver="filesystem",env_prefix="test",validation_object_prefix="validated",retention_class="hot",filesystem_root=temp),object_store=store)
            for supported in (True,False):
                changed_fields=fields if supported else [replace(f,field_metadata={}) if f.field_name=="standard_rate" else f for f in fields]
                normalized=normalizer.normalize_inputs(run_id="run-1",inputs=[replace(item,extracted_fields=changed_fields)]).source_results[0]
                self.assertIsNone(normalized.error_summary)
                candidate=normalized.normalized_candidate_record
                receipt=candidate["candidate_payload"][RECEIPT_KEY]
                self.assertEqual(receipt["accepted"],supported,receipt)
                v=ValidationInput(source_id="source-1",source_document_id="src-1",snapshot_id="snap-1",parsed_document_id="parsed-1",
                    candidate_id=candidate["candidate_id"],candidate_run_id="run-1",normalization_model_execution_id="normalize-1",
                    normalized_storage_key="normalized",metadata_storage_key=None,bank_code="EXAMPLE",country_code="CA",
                    source_type="html",source_language="en",source_metadata=meta,normalized_candidate_record=candidate,
                    field_evidence_links=[ValidationEvidenceLink(**link) for link in normalized.field_evidence_link_records],runtime_notes=normalized.runtime_notes)
                outcome=validator.validate_and_route_inputs(run_id="run-1",inputs=[v],taxonomy_registry={"savings":{"standard","other"}},
                    routing_config=ValidationRoutingConfig(routing_mode="phase1",auto_approve_min_confidence=0,
                        review_warning_confidence_floor=0,force_review_issue_codes=set())).source_results[0]
                self.assertEqual(outcome.validation_action,"auto_validated" if supported else "excluded",outcome.validation_issue_codes)
                self.assertIsNone(outcome.review_task_record)
                self.assertIsNone(outcome.review_task_id)

if __name__=="__main__":unittest.main()
