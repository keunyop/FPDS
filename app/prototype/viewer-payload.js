window.FPDS_VIEWER_PAYLOAD = {
  "viewer_version": "fpds-prototype-viewer-v1",
  "generated_at": "2026-04-12T04:56:42.603748+00:00",
  "run": {
    "run_id": "run_20260411_3528_validate_harden3",
    "run_state": "completed",
    "trigger_type": "manual",
    "triggered_by": "codex",
    "source_scope_count": 3,
    "source_success_count": 3,
    "source_failure_count": 0,
    "candidate_count": 3,
    "review_queued_count": 3,
    "partial_completion_flag": false,
    "error_summary": null,
    "started_at": "2026-04-12T04:56:00.216076+00:00",
    "completed_at": "2026-04-12T04:56:31.419311+00:00",
    "run_metadata": {
      "request_id": null,
      "source_ids": [
        "TD-SAV-002",
        "TD-SAV-003",
        "TD-SAV-004"
      ],
      "routing_mode": "prototype",
      "trigger_type": "manual",
      "triggered_by": "codex",
      "correlation_id": null,
      "pipeline_stage": "validation_routing",
      "validation_stats": {
        "failed_count": 0,
        "queued_count": 3,
        "source_total": 3,
        "review_task_count": 3,
        "auto_validated_count": 0
      }
    },
    "stage_status_counts": {
      "completed": 3
    },
    "source_ids": [
      "TD-SAV-002",
      "TD-SAV-003",
      "TD-SAV-004"
    ],
    "routing_mode": "prototype"
  },
  "metrics": {
    "candidate_count": 3,
    "pass_count": 3,
    "warning_count": 0,
    "error_count": 0,
    "review_queued_count": 3,
    "evidence_link_count": 40,
    "average_confidence": 0.8864
  },
  "candidates": [
    {
      "source_id": "TD-SAV-004",
      "review_task_id": "review-47d2cf74bbcf0432",
      "review_state": "queued",
      "queue_reason_code": "manual_sampling_review",
      "issue_summary": [
        {
          "code": "manual_sampling_review",
          "summary": "Prototype routing keeps all candidates in review.",
          "severity": "warning"
        }
      ],
      "candidate_id": "cand-502fba004c5cf723",
      "run_id": "run_20260411_3527_normalize_harden3",
      "source_document_id": "src-td-html-ccce6ce37887f36e",
      "bank_code": "TD",
      "bank_name": "TD Bank",
      "country_code": "CA",
      "product_family": "deposit",
      "product_type": "savings",
      "subtype_code": "standard",
      "product_name": "TD Growth\u2122 Savings Account",
      "source_language": "en",
      "currency": "CAD",
      "candidate_state": "in_review",
      "validation_status": "pass",
      "source_confidence": 0.8908,
      "review_reason_code": "manual_sampling_review",
      "validation_issue_codes": [],
      "candidate_payload": {
        "status": "active",
        "bank_name": "TD Bank",
        "monthly_fee": 0.0,
        "product_name": "TD Growth\u2122 Savings Account",
        "subtype_code": "standard",
        "standard_rate": 0.65,
        "effective_date": null,
        "minimum_balance": 5000.0,
        "minimum_deposit": 5000.0,
        "transaction_fee": "Account Fees Monthly Fee $0 Transactions fee $5.00 each 3 Free transfers to your other TD accounts Unlimited 4 Non-TD ATM Fee (in Canada) $2.00 each 5 Foreign ATM Fee (in U.S., Mexico) $3.00 each 5 Foreign ATM Fees (in any other foreign country) $5.00 each 5",
        "eligibility_text": "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions.",
        "last_verified_at": "2026-04-12T04:55:43.964110+00:00",
        "promotional_rate": 1.5,
        "tiered_rate_flag": true,
        "description_short": "Earns interest on Balances over $5000 with the Boosted rate 1",
        "public_display_fee": 0.0,
        "public_display_rate": 1.5,
        "source_subtype_label": null,
        "target_customer_tags": [],
        "tier_definition_text": "TD Growth\u2122 Savings Account Earns interest on Balances over $5000 with the Boosted rate 1 Free transfers to your other TD deposit accounts Unlimited 4 Monthly Fee $ 0",
        "withdrawal_limit_text": "TD Growth\u2122 Savings Account Earns interest on Balances over $5000 with the Boosted rate 1 Free transfers to your other TD deposit accounts Unlimited 4 Monthly Fee $ 0",
        "promotional_period_text": "Meeting the qualification criteria earns the Boosted rate for the next month.",
        "boosted_rate_eligibility": "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions to earn the Boosted rate for the next month.",
        "interest_payment_frequency": "monthly",
        "interest_calculation_method": "Interest is calculated on the daily closing balance."
      },
      "field_mapping_metadata": {
        "currency": {
          "value_type": "string",
          "normalized_value": "CAD",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "currency",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "bank_code": {
          "value_type": "string",
          "normalized_value": "TD",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "bank_code",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "monthly_fee": {
          "value_type": "decimal",
          "normalized_value": 0.0,
          "evidence_chunk_id": "chunk-c05da8277120890e",
          "extraction_method": "heuristic_money",
          "source_field_name": "monthly_fee",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.83
        },
        "country_code": {
          "value_type": "string",
          "normalized_value": "CA",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "country_code",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "product_name": {
          "value_type": "string",
          "normalized_value": "TD Growth\u2122 Savings Account",
          "evidence_chunk_id": null,
          "extraction_method": "derived_title",
          "source_field_name": "product_name",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.88
        },
        "product_type": {
          "value_type": "string",
          "normalized_value": "savings",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "product_type",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "subtype_code": {
          "normalized_value": "standard",
          "source_field_name": "product_name",
          "normalization_method": "heuristic_subtype_inference",
          "source_subtype_label": null
        },
        "standard_rate": {
          "value_type": "decimal",
          "normalized_value": 0.65,
          "evidence_chunk_id": "chunk-5d7593ba539487df",
          "extraction_method": "supporting_rate_table_merge",
          "source_field_name": "standard_rate",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.72
        },
        "product_family": {
          "value_type": "string",
          "normalized_value": "deposit",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "product_family",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "minimum_balance": {
          "value_type": "decimal",
          "normalized_value": 5000.0,
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "extraction_method": "heuristic_money",
          "source_field_name": "minimum_balance",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "minimum_deposit": {
          "value_type": "decimal",
          "normalized_value": 5000.0,
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "extraction_method": "heuristic_money",
          "source_field_name": "minimum_deposit",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "source_language": {
          "value_type": "string",
          "normalized_value": "en",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "source_language",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "transaction_fee": {
          "value_type": "string",
          "normalized_value": "Account Fees Monthly Fee $0 Transactions fee $5.00 each 3 Free transfers to your other TD accounts Unlimited 4 Non-TD ATM Fee (in Canada) $2.00 each 5 Foreign ATM Fee (in U.S., Mexico) $3.00 each 5 Foreign ATM Fees (in any other foreign country) $5.00 each 5",
          "evidence_chunk_id": "chunk-c05da8277120890e",
          "extraction_method": "heuristic_text",
          "source_field_name": "transaction_fee",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "eligibility_text": {
          "value_type": "string",
          "normalized_value": "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions.",
          "evidence_chunk_id": "chunk-9f644fbb1a515d2a",
          "extraction_method": "growth_qualification_cleanup",
          "source_field_name": "eligibility_text",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.76
        },
        "promotional_rate": {
          "value_type": "decimal",
          "normalized_value": 1.5,
          "evidence_chunk_id": "chunk-5d7593ba539487df",
          "extraction_method": "supporting_rate_table_merge",
          "source_field_name": "promotional_rate",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.72
        },
        "tiered_rate_flag": {
          "value_type": "boolean",
          "normalized_value": true,
          "evidence_chunk_id": "chunk-c8956e47b18ae2e9",
          "extraction_method": "heuristic_flag",
          "source_field_name": "tiered_rate_flag",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "description_short": {
          "value_type": "string",
          "normalized_value": "Earns interest on Balances over $5000 with the Boosted rate 1",
          "evidence_chunk_id": null,
          "extraction_method": "derived_description",
          "source_field_name": "description_short",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.7
        },
        "public_display_fee": {
          "value_type": "decimal",
          "normalized_value": 0.0,
          "evidence_chunk_id": "chunk-c05da8277120890e",
          "extraction_method": "heuristic_money",
          "source_field_name": "public_display_fee",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.83
        },
        "public_display_rate": {
          "value_type": "decimal",
          "normalized_value": 1.5,
          "evidence_chunk_id": "chunk-5d7593ba539487df",
          "extraction_method": "supporting_rate_table_merge",
          "source_field_name": "public_display_rate",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.72
        },
        "tier_definition_text": {
          "value_type": "string",
          "normalized_value": "TD Growth\u2122 Savings Account Earns interest on Balances over $5000 with the Boosted rate 1 Free transfers to your other TD deposit accounts Unlimited 4 Monthly Fee $ 0",
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "extraction_method": "heuristic_text",
          "source_field_name": "tier_definition_text",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "withdrawal_limit_text": {
          "value_type": "string",
          "normalized_value": "TD Growth\u2122 Savings Account Earns interest on Balances over $5000 with the Boosted rate 1 Free transfers to your other TD deposit accounts Unlimited 4 Monthly Fee $ 0",
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "extraction_method": "heuristic_text",
          "source_field_name": "withdrawal_limit_text",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "promotional_period_text": {
          "value_type": "string",
          "normalized_value": "Meeting the qualification criteria earns the Boosted rate for the next month.",
          "evidence_chunk_id": "chunk-9f644fbb1a515d2a",
          "extraction_method": "growth_qualification_cleanup",
          "source_field_name": "promotional_period_text",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.76
        },
        "boosted_rate_eligibility": {
          "value_type": "string",
          "normalized_value": "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions to earn the Boosted rate for the next month.",
          "evidence_chunk_id": "chunk-9f644fbb1a515d2a",
          "extraction_method": "growth_qualification_cleanup",
          "source_field_name": "boosted_rate_eligibility",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.76
        },
        "interest_payment_frequency": {
          "value_type": "string",
          "normalized_value": "monthly",
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "extraction_method": "heuristic_frequency",
          "source_field_name": "interest_payment_frequency",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "interest_calculation_method": {
          "value_type": "string",
          "normalized_value": "Interest is calculated on the daily closing balance.",
          "evidence_chunk_id": "chunk-200e9e741b35b01c",
          "extraction_method": "supporting_interest_pdf_merge",
          "source_field_name": "interest_calculation_method",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.85
        }
      },
      "highlight_fields": [
        {
          "field_name": "status",
          "label": "Status",
          "value": "active"
        },
        {
          "field_name": "monthly_fee",
          "label": "Monthly Fee",
          "value": 0.0
        },
        {
          "field_name": "standard_rate",
          "label": "Standard Rate",
          "value": 0.65
        },
        {
          "field_name": "promotional_rate",
          "label": "Promo Rate",
          "value": 1.5
        },
        {
          "field_name": "public_display_rate",
          "label": "Public Rate",
          "value": 1.5
        },
        {
          "field_name": "public_display_fee",
          "label": "Public Fee",
          "value": 0.0
        },
        {
          "field_name": "minimum_balance",
          "label": "Minimum Balance",
          "value": 5000.0
        },
        {
          "field_name": "minimum_deposit",
          "label": "Minimum Deposit",
          "value": 5000.0
        },
        {
          "field_name": "interest_payment_frequency",
          "label": "Interest Payout",
          "value": "monthly"
        },
        {
          "field_name": "eligibility_text",
          "label": "Eligibility",
          "value": "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions."
        },
        {
          "field_name": "last_verified_at",
          "label": "Last Verified",
          "value": "2026-04-12T04:55:43.964110+00:00"
        }
      ],
      "source_context": {
        "source_url": "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/growth-savings-account",
        "source_type": "html",
        "source_metadata": {
          "purpose": "TD Growth Savings primary detail source",
          "priority": "P0",
          "source_id": "TD-SAV-004",
          "product_type": "savings",
          "discovery_role": "detail",
          "expected_fields": [
            "product_name",
            "description_short",
            "monthly_fee",
            "transaction_fee",
            "boosted_rate_eligibility"
          ],
          "seed_source_flag": true
        },
        "snapshot_id": "snap-2a38b480916a6d67",
        "fetched_at": "2026-04-10T05:39:21.159057+00:00",
        "parsed_document_id": "parsed-9f012538945d6293",
        "parse_quality_note": null,
        "stage_status": "completed",
        "warning_count": 1,
        "error_count": 0,
        "error_summary": null,
        "runtime_notes": [
          "Supplemented missing savings rate fields from `TD-SAV-005` current-rate evidence using a product-matched supporting chunk.",
          "Reviewed `TD-SAV-007` fee-governing language for `TD-SAV-004` and left `fee_waiver_condition` unset because the target monthly fee is already $0.",
          "Replaced noisy interest-rule fields with targeted `TD-SAV-008` governing PDF evidence where stronger canonical wording was available.",
          "Suppressed noisy `fee_waiver_condition` for `TD-SAV-004` because the product monthly fee is already $0 and no product-specific waiver rule should be persisted.",
          "Suppressed noisy `notes` text before normalization.",
          "Suppressed `promotional_period_text` because the extracted text described marketing copy rather than a bounded promotional period.",
          "Split TD Growth boosted-rate qualification into cleaner `eligibility_text`, `boosted_rate_eligibility`, and `promotional_period_text` values."
        ]
      },
      "evidence_links": [
        {
          "field_name": "boosted_rate_eligibility",
          "label": "Boosted Rate Eligibility",
          "candidate_value": "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions to earn the Boosted rate for the next month.",
          "citation_confidence": 0.76,
          "evidence_chunk_id": "chunk-9f644fbb1a515d2a",
          "evidence_excerpt": "Boosted Rate Eligibility\nEarn the Boosted rate 1 on your savings for the next month! Here\u2019s how to qualify:\n1 Maintain an eligible TD Chequing Account: TD Unlimited Chequing Account TD All-Inclusive Banking Plan TD Wealth Private Banking Chequing Account\nMaintain an eligible TD Chequing Account:\nTD Unlimited Chequing Account\nTD All-Inclusive Banking Plan\nTD Wealth Private Banking Chequing Account\n2 Complete at least 2 out of the 3 Qualifying Monthly Transactions 1 on your eligible TD Chequing Account each month: Direct Deposit Pre-Authorized Debit Online Bill Payment\nComplete at least 2 out of the 3 Qualifying Monthly Transactions 1 on your eligible TD Chequing Account each month:\nDirect Deposit\nPre-Authorized Debit\nOnline Bill Payment",
          "anchor_type": "section",
          "anchor_value": "boosted-rate-eligibility",
          "page_no": null,
          "chunk_index": 3,
          "anchor_label": "Section boosted-rate-eligibility"
        },
        {
          "field_name": "eligibility_text",
          "label": "Eligibility",
          "candidate_value": "Maintain an eligible TD Chequing Account and complete at least 2 of 3 qualifying monthly transactions.",
          "citation_confidence": 0.76,
          "evidence_chunk_id": "chunk-9f644fbb1a515d2a",
          "evidence_excerpt": "Boosted Rate Eligibility\nEarn the Boosted rate 1 on your savings for the next month! Here\u2019s how to qualify:\n1 Maintain an eligible TD Chequing Account: TD Unlimited Chequing Account TD All-Inclusive Banking Plan TD Wealth Private Banking Chequing Account\nMaintain an eligible TD Chequing Account:\nTD Unlimited Chequing Account\nTD All-Inclusive Banking Plan\nTD Wealth Private Banking Chequing Account\n2 Complete at least 2 out of the 3 Qualifying Monthly Transactions 1 on your eligible TD Chequing Account each month: Direct Deposit Pre-Authorized Debit Online Bill Payment\nComplete at least 2 out of the 3 Qualifying Monthly Transactions 1 on your eligible TD Chequing Account each month:\nDirect Deposit\nPre-Authorized Debit\nOnline Bill Payment",
          "anchor_type": "section",
          "anchor_value": "boosted-rate-eligibility",
          "page_no": null,
          "chunk_index": 3,
          "anchor_label": "Section boosted-rate-eligibility"
        },
        {
          "field_name": "interest_calculation_method",
          "label": "Interest Calculation Method",
          "candidate_value": "Interest is calculated on the daily closing balance.",
          "citation_confidence": 0.85,
          "evidence_chunk_id": "chunk-200e9e741b35b01c",
          "evidence_excerpt": "About Our Interest Calculations\nAs of December 18, 2025\nCHART 2: SAVINGS ACCOUNTS\nSavings Account Daily Closing Balance Rate Details\nTD Every Day Savings Total Daily Closing Balance\nUp to $999.99\nTotal Daily Closing Balance\n$1,000.00 to $4,999.99\nTotal Daily Closing Balance\n$5,000.00 to $9,999.99\nTotal Daily Closing Balance\n$10,000.00 to $24,999.99\nTotal Daily Closing Balance\n$25,000.00 to $59,999.99\nTotal Daily Closing Balance\n$60,000.00 and over\n0.010%\n0.010%\n0.010%\n0.010%\n0.010%\n0.010%\nOnly one interest rate applies to your\ntotal Daily Closing Balance based on the\nTiers listed. Interest will be calculated\neach day by multiplying your total Daily\nClosing Balance by the interest rate for\nthe Tier to which your total Daily Closing\nBalance corresponds.\nTD ePremium Savings Total Daily Closing Balance\nUp to $9,999.99\nTotal Daily Closing Balance\n$10,000.00 to $49,999.99\nTotal Daily Closing",
          "anchor_type": "page",
          "anchor_value": "page-3",
          "page_no": 3,
          "chunk_index": 8,
          "anchor_label": "Page 3"
        },
        {
          "field_name": "interest_payment_frequency",
          "label": "Interest Payout",
          "candidate_value": "monthly",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "evidence_excerpt": "TD Growth\u2122 Savings Account\nEarns interest on Balances over $5000 with the Boosted rate 1\nFree transfers to your other TD deposit accounts Unlimited 4\nMonthly Fee $ 0",
          "anchor_type": "section",
          "anchor_value": "td-growth-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-growth-savings-account"
        },
        {
          "field_name": "minimum_balance",
          "label": "Minimum Balance",
          "candidate_value": "5000.0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "evidence_excerpt": "TD Growth\u2122 Savings Account\nEarns interest on Balances over $5000 with the Boosted rate 1\nFree transfers to your other TD deposit accounts Unlimited 4\nMonthly Fee $ 0",
          "anchor_type": "section",
          "anchor_value": "td-growth-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-growth-savings-account"
        },
        {
          "field_name": "minimum_deposit",
          "label": "Minimum Deposit",
          "candidate_value": "5000.0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "evidence_excerpt": "TD Growth\u2122 Savings Account\nEarns interest on Balances over $5000 with the Boosted rate 1\nFree transfers to your other TD deposit accounts Unlimited 4\nMonthly Fee $ 0",
          "anchor_type": "section",
          "anchor_value": "td-growth-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-growth-savings-account"
        },
        {
          "field_name": "monthly_fee",
          "label": "Monthly Fee",
          "candidate_value": "0.0",
          "citation_confidence": 0.83,
          "evidence_chunk_id": "chunk-c05da8277120890e",
          "evidence_excerpt": "Account Fees\nMonthly Fee\n$0\nTransactions fee\n$5.00 each 3\nFree transfers to your other TD accounts\nUnlimited 4\nNon-TD ATM Fee (in Canada)\n$2.00 each 5\nForeign ATM Fee (in U.S., Mexico)\n$3.00 each 5\nForeign ATM Fees (in any other foreign country)\n$5.00 each 5",
          "anchor_type": "section",
          "anchor_value": "account-fees",
          "page_no": null,
          "chunk_index": 4,
          "anchor_label": "Section account-fees"
        },
        {
          "field_name": "promotional_period_text",
          "label": "Promotional Period Text",
          "candidate_value": "Meeting the qualification criteria earns the Boosted rate for the next month.",
          "citation_confidence": 0.76,
          "evidence_chunk_id": "chunk-9f644fbb1a515d2a",
          "evidence_excerpt": "Boosted Rate Eligibility\nEarn the Boosted rate 1 on your savings for the next month! Here\u2019s how to qualify:\n1 Maintain an eligible TD Chequing Account: TD Unlimited Chequing Account TD All-Inclusive Banking Plan TD Wealth Private Banking Chequing Account\nMaintain an eligible TD Chequing Account:\nTD Unlimited Chequing Account\nTD All-Inclusive Banking Plan\nTD Wealth Private Banking Chequing Account\n2 Complete at least 2 out of the 3 Qualifying Monthly Transactions 1 on your eligible TD Chequing Account each month: Direct Deposit Pre-Authorized Debit Online Bill Payment\nComplete at least 2 out of the 3 Qualifying Monthly Transactions 1 on your eligible TD Chequing Account each month:\nDirect Deposit\nPre-Authorized Debit\nOnline Bill Payment",
          "anchor_type": "section",
          "anchor_value": "boosted-rate-eligibility",
          "page_no": null,
          "chunk_index": 3,
          "anchor_label": "Section boosted-rate-eligibility"
        },
        {
          "field_name": "promotional_rate",
          "label": "Promo Rate",
          "candidate_value": "1.5",
          "citation_confidence": 0.72,
          "evidence_chunk_id": "chunk-5d7593ba539487df",
          "evidence_excerpt": "TD\u00a0Growth\u2122 Savings Account 6\nDaily Closing Balance Tiers\nBoosted Rate 6\nStandard Posted Rate\n$0 to $4,999.99\n0.00%\n$5,000.00 to $9,999.99\n0.50%\n0.00%\n$10,000 to $99,999.99\n1.00%\n0.40%\n$100,000.00 to $499,999.99\n1.30%\n0.55%\n$500,000.00 and over\n1.50%\n0.65%\nBoosted Rate 6\nStandard Posted Rate\nDaily Closing Balance Tiers\nBoosted Rate 6\nStandard Posted Rate\n$0 to $4,999.99\n0.00%\n$5,000.00 to $9,999.99\n0.50%\n0.00%\n$10,000 to $99,999.99\n1.00%\n0.50%\n$100,000.00 to $499,999.99\n1.30%\n0.65%\nPortion of Daily Closing Balance $500,000.00 and over\n1.50%\n0.75%",
          "anchor_type": "section",
          "anchor_value": "td-growth-savings-account-6",
          "page_no": null,
          "chunk_index": 2,
          "anchor_label": "Section td-growth-savings-account-6"
        },
        {
          "field_name": "public_display_fee",
          "label": "Public Fee",
          "candidate_value": "0.0",
          "citation_confidence": 0.83,
          "evidence_chunk_id": "chunk-c05da8277120890e",
          "evidence_excerpt": "Account Fees\nMonthly Fee\n$0\nTransactions fee\n$5.00 each 3\nFree transfers to your other TD accounts\nUnlimited 4\nNon-TD ATM Fee (in Canada)\n$2.00 each 5\nForeign ATM Fee (in U.S., Mexico)\n$3.00 each 5\nForeign ATM Fees (in any other foreign country)\n$5.00 each 5",
          "anchor_type": "section",
          "anchor_value": "account-fees",
          "page_no": null,
          "chunk_index": 4,
          "anchor_label": "Section account-fees"
        },
        {
          "field_name": "public_display_rate",
          "label": "Public Rate",
          "candidate_value": "1.5",
          "citation_confidence": 0.72,
          "evidence_chunk_id": "chunk-5d7593ba539487df",
          "evidence_excerpt": "TD\u00a0Growth\u2122 Savings Account 6\nDaily Closing Balance Tiers\nBoosted Rate 6\nStandard Posted Rate\n$0 to $4,999.99\n0.00%\n$5,000.00 to $9,999.99\n0.50%\n0.00%\n$10,000 to $99,999.99\n1.00%\n0.40%\n$100,000.00 to $499,999.99\n1.30%\n0.55%\n$500,000.00 and over\n1.50%\n0.65%\nBoosted Rate 6\nStandard Posted Rate\nDaily Closing Balance Tiers\nBoosted Rate 6\nStandard Posted Rate\n$0 to $4,999.99\n0.00%\n$5,000.00 to $9,999.99\n0.50%\n0.00%\n$10,000 to $99,999.99\n1.00%\n0.50%\n$100,000.00 to $499,999.99\n1.30%\n0.65%\nPortion of Daily Closing Balance $500,000.00 and over\n1.50%\n0.75%",
          "anchor_type": "section",
          "anchor_value": "td-growth-savings-account-6",
          "page_no": null,
          "chunk_index": 2,
          "anchor_label": "Section td-growth-savings-account-6"
        },
        {
          "field_name": "standard_rate",
          "label": "Standard Rate",
          "candidate_value": "0.65",
          "citation_confidence": 0.72,
          "evidence_chunk_id": "chunk-5d7593ba539487df",
          "evidence_excerpt": "TD\u00a0Growth\u2122 Savings Account 6\nDaily Closing Balance Tiers\nBoosted Rate 6\nStandard Posted Rate\n$0 to $4,999.99\n0.00%\n$5,000.00 to $9,999.99\n0.50%\n0.00%\n$10,000 to $99,999.99\n1.00%\n0.40%\n$100,000.00 to $499,999.99\n1.30%\n0.55%\n$500,000.00 and over\n1.50%\n0.65%\nBoosted Rate 6\nStandard Posted Rate\nDaily Closing Balance Tiers\nBoosted Rate 6\nStandard Posted Rate\n$0 to $4,999.99\n0.00%\n$5,000.00 to $9,999.99\n0.50%\n0.00%\n$10,000 to $99,999.99\n1.00%\n0.50%\n$100,000.00 to $499,999.99\n1.30%\n0.65%\nPortion of Daily Closing Balance $500,000.00 and over\n1.50%\n0.75%",
          "anchor_type": "section",
          "anchor_value": "td-growth-savings-account-6",
          "page_no": null,
          "chunk_index": 2,
          "anchor_label": "Section td-growth-savings-account-6"
        },
        {
          "field_name": "tier_definition_text",
          "label": "Tier Definition Text",
          "candidate_value": "TD Growth\u2122 Savings Account Earns interest on Balances over $5000 with the Boosted rate 1 Free transfers to your other TD deposit accounts Unlimited 4 Monthly Fee $ 0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "evidence_excerpt": "TD Growth\u2122 Savings Account\nEarns interest on Balances over $5000 with the Boosted rate 1\nFree transfers to your other TD deposit accounts Unlimited 4\nMonthly Fee $ 0",
          "anchor_type": "section",
          "anchor_value": "td-growth-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-growth-savings-account"
        },
        {
          "field_name": "tiered_rate_flag",
          "label": "Tiered Rate Flag",
          "candidate_value": "true",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-c8956e47b18ae2e9",
          "evidence_excerpt": "Plan Highlights\n$0 Monthly Fee Enjoy your savings account without the burden of monthly fees.\n$0 Monthly Fee\nEnjoy your savings account without the burden of monthly fees.\nEarn the Boosted Rate 1 Customers with an eligible TD Chequing 1 Account can earn\u202fhigher returns on balances of $5,000 or more with the Boosted Rate\u00a0instead of the Standard Posted Rate.\nEarn the Boosted Rate 1\nCustomers with an eligible TD Chequing 1 Account can earn\u202fhigher returns on balances of $5,000 or more with the Boosted Rate\u00a0instead of the Standard Posted Rate.\nTiered Interest Rates The more you save, the higher your interest rate \u2013 helping you earn more as you save.\nTiered Interest Rates\nThe more you save, the higher your interest rate \u2013 helping you earn more as you save.\nFree Transfers Enjoy unlimited, free transfers to all of your TD deposit accounts. 4\nFree Transfers\nEnjoy unlimited, free transfers to all",
          "anchor_type": "section",
          "anchor_value": "plan-highlights",
          "page_no": null,
          "chunk_index": 1,
          "anchor_label": "Section plan-highlights"
        },
        {
          "field_name": "transaction_fee",
          "label": "Transaction Fee",
          "candidate_value": "Account Fees Monthly Fee $0 Transactions fee $5.00 each 3 Free transfers to your other TD accounts Unlimited 4 Non-TD ATM Fee (in Canada) $2.00 each 5 Foreign ATM Fee (in U.S., Mexico) $3.00 each 5 Foreign ATM Fees (in any other foreign country) $5.00 each 5",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-c05da8277120890e",
          "evidence_excerpt": "Account Fees\nMonthly Fee\n$0\nTransactions fee\n$5.00 each 3\nFree transfers to your other TD accounts\nUnlimited 4\nNon-TD ATM Fee (in Canada)\n$2.00 each 5\nForeign ATM Fee (in U.S., Mexico)\n$3.00 each 5\nForeign ATM Fees (in any other foreign country)\n$5.00 each 5",
          "anchor_type": "section",
          "anchor_value": "account-fees",
          "page_no": null,
          "chunk_index": 4,
          "anchor_label": "Section account-fees"
        },
        {
          "field_name": "withdrawal_limit_text",
          "label": "Withdrawal Limit Text",
          "candidate_value": "TD Growth\u2122 Savings Account Earns interest on Balances over $5000 with the Boosted rate 1 Free transfers to your other TD deposit accounts Unlimited 4 Monthly Fee $ 0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-7cfce3637154be8b",
          "evidence_excerpt": "TD Growth\u2122 Savings Account\nEarns interest on Balances over $5000 with the Boosted rate 1\nFree transfers to your other TD deposit accounts Unlimited 4\nMonthly Fee $ 0",
          "anchor_type": "section",
          "anchor_value": "td-growth-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-growth-savings-account"
        }
      ],
      "evidence_field_count": 16
    },
    {
      "source_id": "TD-SAV-003",
      "review_task_id": "review-4f94decd0aeaa6ba",
      "review_state": "queued",
      "queue_reason_code": "manual_sampling_review",
      "issue_summary": [
        {
          "code": "manual_sampling_review",
          "summary": "Prototype routing keeps all candidates in review.",
          "severity": "warning"
        }
      ],
      "candidate_id": "cand-9307a7579cccb64b",
      "run_id": "run_20260411_3527_normalize_harden3",
      "source_document_id": "src-td-html-ea1ab93268f19492",
      "bank_code": "TD",
      "bank_name": "TD Bank",
      "country_code": "CA",
      "product_family": "deposit",
      "product_type": "savings",
      "subtype_code": "high_interest",
      "product_name": "TD ePremium Savings Account",
      "source_language": "en",
      "currency": "CAD",
      "candidate_state": "in_review",
      "validation_status": "pass",
      "source_confidence": 0.8847,
      "review_reason_code": "manual_sampling_review",
      "validation_issue_codes": [],
      "candidate_payload": {
        "status": "active",
        "bank_name": "TD Bank",
        "monthly_fee": 0.0,
        "product_name": "TD ePremium Savings Account",
        "subtype_code": "high_interest",
        "standard_rate": 0.45,
        "effective_date": null,
        "minimum_balance": 10000.0,
        "minimum_deposit": 10000.0,
        "transaction_fee": "Account Fees Monthly Fee $0 Transaction Fee 3 $5.00 each Free Online Transfers 2 Unlimited Non-TD ATM Fee (in Canada) 4 $2.00 each Foreign ATM Fee (in U.S., Mexico) 4 $3.00 each Foreign ATM Fees (in any other foreign country) 4 $5.00 each",
        "last_verified_at": "2026-04-12T04:55:37.563155+00:00",
        "description_short": "On balances of $10,000 or more High interest rate",
        "public_display_fee": 0.0,
        "public_display_rate": 0.45,
        "source_subtype_label": null,
        "target_customer_tags": [],
        "tier_definition_text": "Free online transfers Enjoy unlimited free online transfers to your other TD deposit accounts 2 Automated Savings You can make savings part of your everyday life with our Automated Savings services Additional account benefits Free paperless record keeping or online statements",
        "free_online_transfers": "TD ePremium Savings Account On balances of $10,000 or more High interest rate Free online transfers to your other TD Canada Trust deposit accounts 2 Unlimited Monthly Fee $0",
        "withdrawal_limit_text": "TD ePremium Savings Account On balances of $10,000 or more High interest rate Free online transfers to your other TD Canada Trust deposit accounts 2 Unlimited Monthly Fee $0",
        "interest_payment_frequency": "monthly",
        "interest_calculation_method": "Plan Highlights High interest rate Earn interest calculated daily, when your account balance is $10,000 or more."
      },
      "field_mapping_metadata": {
        "currency": {
          "value_type": "string",
          "normalized_value": "CAD",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "currency",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "bank_code": {
          "value_type": "string",
          "normalized_value": "TD",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "bank_code",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "monthly_fee": {
          "value_type": "decimal",
          "normalized_value": 0.0,
          "evidence_chunk_id": "chunk-0b7119ff34364921",
          "extraction_method": "heuristic_money",
          "source_field_name": "monthly_fee",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.83
        },
        "country_code": {
          "value_type": "string",
          "normalized_value": "CA",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "country_code",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "product_name": {
          "value_type": "string",
          "normalized_value": "TD ePremium Savings Account",
          "evidence_chunk_id": null,
          "extraction_method": "derived_title",
          "source_field_name": "product_name",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.88
        },
        "product_type": {
          "value_type": "string",
          "normalized_value": "savings",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "product_type",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "subtype_code": {
          "normalized_value": "high_interest",
          "source_field_name": "product_name",
          "normalization_method": "heuristic_subtype_inference",
          "source_subtype_label": null
        },
        "standard_rate": {
          "value_type": "decimal",
          "normalized_value": 0.45,
          "evidence_chunk_id": "chunk-3fb2a59cf25131e3",
          "extraction_method": "supporting_rate_table_merge",
          "source_field_name": "standard_rate",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.72
        },
        "product_family": {
          "value_type": "string",
          "normalized_value": "deposit",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "product_family",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "minimum_balance": {
          "value_type": "decimal",
          "normalized_value": 10000.0,
          "evidence_chunk_id": "chunk-3124258c76c37de7",
          "extraction_method": "heuristic_money",
          "source_field_name": "minimum_balance",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "minimum_deposit": {
          "value_type": "decimal",
          "normalized_value": 10000.0,
          "evidence_chunk_id": "chunk-a7049fc3d80e0546",
          "extraction_method": "heuristic_money",
          "source_field_name": "minimum_deposit",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "source_language": {
          "value_type": "string",
          "normalized_value": "en",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "source_language",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "transaction_fee": {
          "value_type": "string",
          "normalized_value": "Account Fees Monthly Fee $0 Transaction Fee 3 $5.00 each Free Online Transfers 2 Unlimited Non-TD ATM Fee (in Canada) 4 $2.00 each Foreign ATM Fee (in U.S., Mexico) 4 $3.00 each Foreign ATM Fees (in any other foreign country) 4 $5.00 each",
          "evidence_chunk_id": "chunk-0b7119ff34364921",
          "extraction_method": "heuristic_text",
          "source_field_name": "transaction_fee",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.59
        },
        "description_short": {
          "value_type": "string",
          "normalized_value": "On balances of $10,000 or more High interest rate",
          "evidence_chunk_id": null,
          "extraction_method": "derived_description",
          "source_field_name": "description_short",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.7
        },
        "public_display_fee": {
          "value_type": "decimal",
          "normalized_value": 0.0,
          "evidence_chunk_id": "chunk-0b7119ff34364921",
          "extraction_method": "heuristic_money",
          "source_field_name": "public_display_fee",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.83
        },
        "public_display_rate": {
          "value_type": "decimal",
          "normalized_value": 0.45,
          "evidence_chunk_id": "chunk-3fb2a59cf25131e3",
          "extraction_method": "supporting_rate_table_merge",
          "source_field_name": "public_display_rate",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.72
        },
        "tier_definition_text": {
          "value_type": "string",
          "normalized_value": "Free online transfers Enjoy unlimited free online transfers to your other TD deposit accounts 2 Automated Savings You can make savings part of your everyday life with our Automated Savings services Additional account benefits Free paperless record keeping or online statements",
          "evidence_chunk_id": "chunk-3124258c76c37de7",
          "extraction_method": "heuristic_text",
          "source_field_name": "tier_definition_text",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "free_online_transfers": {
          "value_type": "string",
          "normalized_value": "TD ePremium Savings Account On balances of $10,000 or more High interest rate Free online transfers to your other TD Canada Trust deposit accounts 2 Unlimited Monthly Fee $0",
          "evidence_chunk_id": "chunk-a7049fc3d80e0546",
          "extraction_method": "heuristic_text",
          "source_field_name": "free_online_transfers",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "withdrawal_limit_text": {
          "value_type": "string",
          "normalized_value": "TD ePremium Savings Account On balances of $10,000 or more High interest rate Free online transfers to your other TD Canada Trust deposit accounts 2 Unlimited Monthly Fee $0",
          "evidence_chunk_id": "chunk-a7049fc3d80e0546",
          "extraction_method": "heuristic_text",
          "source_field_name": "withdrawal_limit_text",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "interest_payment_frequency": {
          "value_type": "string",
          "normalized_value": "monthly",
          "evidence_chunk_id": "chunk-a7049fc3d80e0546",
          "extraction_method": "heuristic_frequency",
          "source_field_name": "interest_payment_frequency",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "interest_calculation_method": {
          "value_type": "string",
          "normalized_value": "Plan Highlights High interest rate Earn interest calculated daily, when your account balance is $10,000 or more.",
          "evidence_chunk_id": "chunk-3124258c76c37de7",
          "extraction_method": "heuristic_sentence",
          "source_field_name": "interest_calculation_method",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.85
        }
      },
      "highlight_fields": [
        {
          "field_name": "status",
          "label": "Status",
          "value": "active"
        },
        {
          "field_name": "monthly_fee",
          "label": "Monthly Fee",
          "value": 0.0
        },
        {
          "field_name": "standard_rate",
          "label": "Standard Rate",
          "value": 0.45
        },
        {
          "field_name": "public_display_rate",
          "label": "Public Rate",
          "value": 0.45
        },
        {
          "field_name": "public_display_fee",
          "label": "Public Fee",
          "value": 0.0
        },
        {
          "field_name": "minimum_balance",
          "label": "Minimum Balance",
          "value": 10000.0
        },
        {
          "field_name": "minimum_deposit",
          "label": "Minimum Deposit",
          "value": 10000.0
        },
        {
          "field_name": "interest_payment_frequency",
          "label": "Interest Payout",
          "value": "monthly"
        },
        {
          "field_name": "last_verified_at",
          "label": "Last Verified",
          "value": "2026-04-12T04:55:37.563155+00:00"
        }
      ],
      "source_context": {
        "source_url": "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/epremium-savings-account",
        "source_type": "html",
        "source_metadata": {
          "purpose": "TD ePremium Savings primary detail source",
          "priority": "P0",
          "source_id": "TD-SAV-003",
          "product_type": "savings",
          "discovery_role": "detail",
          "expected_fields": [
            "product_name",
            "description_short",
            "monthly_fee",
            "transaction_fee",
            "free_online_transfers"
          ],
          "seed_source_flag": true
        },
        "snapshot_id": "snap-e6b73a16fb92200a",
        "fetched_at": "2026-04-11T07:37:21.056469+00:00",
        "parsed_document_id": "parsed-5d032ecec3f01711",
        "parse_quality_note": null,
        "stage_status": "completed",
        "warning_count": 1,
        "error_count": 0,
        "error_summary": null,
        "runtime_notes": [
          "Supplemented missing savings rate fields from `TD-SAV-005` current-rate evidence using a product-matched supporting chunk.",
          "Reviewed `TD-SAV-007` fee-governing language for `TD-SAV-003` and left `fee_waiver_condition` unset because the target monthly fee is already $0.",
          "Suppressed noisy `fee_waiver_condition` for `TD-SAV-003` because the product monthly fee is already $0 and no product-specific waiver rule should be persisted.",
          "Suppressed noisy `notes` text before normalization.",
          "Suppressed noisy `eligibility_text` text before normalization.",
          "Suppressed `promotional_period_text` because the extracted text described marketing copy rather than a bounded promotional period."
        ]
      },
      "evidence_links": [
        {
          "field_name": "free_online_transfers",
          "label": "Free Online Transfers",
          "candidate_value": "TD ePremium Savings Account On balances of $10,000 or more High interest rate Free online transfers to your other TD Canada Trust deposit accounts 2 Unlimited Monthly Fee $0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-a7049fc3d80e0546",
          "evidence_excerpt": "TD ePremium Savings Account\nOn balances of $10,000 or more High interest rate\nFree online transfers to your other TD Canada Trust deposit accounts 2 Unlimited\nMonthly Fee $0",
          "anchor_type": "section",
          "anchor_value": "td-epremium-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-epremium-savings-account"
        },
        {
          "field_name": "interest_calculation_method",
          "label": "Interest Calculation Method",
          "candidate_value": "Plan Highlights High interest rate Earn interest calculated daily, when your account balance is $10,000 or more.",
          "citation_confidence": 0.85,
          "evidence_chunk_id": "chunk-3124258c76c37de7",
          "evidence_excerpt": "Plan Highlights\nHigh interest rate Earn interest calculated daily, when your account balance is $10,000 or more.\nFree online transfers Enjoy unlimited free online transfers to your other TD deposit accounts 2\nAutomated Savings You can make savings part of your everyday life with our Automated Savings services\nAdditional account benefits Free paperless record keeping or online statements",
          "anchor_type": "section",
          "anchor_value": "plan-highlights",
          "page_no": null,
          "chunk_index": 1,
          "anchor_label": "Section plan-highlights"
        },
        {
          "field_name": "interest_payment_frequency",
          "label": "Interest Payout",
          "candidate_value": "monthly",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-a7049fc3d80e0546",
          "evidence_excerpt": "TD ePremium Savings Account\nOn balances of $10,000 or more High interest rate\nFree online transfers to your other TD Canada Trust deposit accounts 2 Unlimited\nMonthly Fee $0",
          "anchor_type": "section",
          "anchor_value": "td-epremium-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-epremium-savings-account"
        },
        {
          "field_name": "minimum_balance",
          "label": "Minimum Balance",
          "candidate_value": "10000.0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-3124258c76c37de7",
          "evidence_excerpt": "Plan Highlights\nHigh interest rate Earn interest calculated daily, when your account balance is $10,000 or more.\nFree online transfers Enjoy unlimited free online transfers to your other TD deposit accounts 2\nAutomated Savings You can make savings part of your everyday life with our Automated Savings services\nAdditional account benefits Free paperless record keeping or online statements",
          "anchor_type": "section",
          "anchor_value": "plan-highlights",
          "page_no": null,
          "chunk_index": 1,
          "anchor_label": "Section plan-highlights"
        },
        {
          "field_name": "minimum_deposit",
          "label": "Minimum Deposit",
          "candidate_value": "10000.0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-a7049fc3d80e0546",
          "evidence_excerpt": "TD ePremium Savings Account\nOn balances of $10,000 or more High interest rate\nFree online transfers to your other TD Canada Trust deposit accounts 2 Unlimited\nMonthly Fee $0",
          "anchor_type": "section",
          "anchor_value": "td-epremium-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-epremium-savings-account"
        },
        {
          "field_name": "monthly_fee",
          "label": "Monthly Fee",
          "candidate_value": "0.0",
          "citation_confidence": 0.83,
          "evidence_chunk_id": "chunk-0b7119ff34364921",
          "evidence_excerpt": "Account Fees\nMonthly Fee\n$0\nTransaction Fee 3\n$5.00 each\nFree Online Transfers 2\nUnlimited\nNon-TD ATM Fee (in Canada) 4\n$2.00 each\nForeign ATM Fee (in U.S., Mexico) 4\n$3.00 each\nForeign ATM Fees (in any other foreign country) 4\n$5.00 each",
          "anchor_type": "section",
          "anchor_value": "account-fees",
          "page_no": null,
          "chunk_index": 2,
          "anchor_label": "Section account-fees"
        },
        {
          "field_name": "public_display_fee",
          "label": "Public Fee",
          "candidate_value": "0.0",
          "citation_confidence": 0.83,
          "evidence_chunk_id": "chunk-0b7119ff34364921",
          "evidence_excerpt": "Account Fees\nMonthly Fee\n$0\nTransaction Fee 3\n$5.00 each\nFree Online Transfers 2\nUnlimited\nNon-TD ATM Fee (in Canada) 4\n$2.00 each\nForeign ATM Fee (in U.S., Mexico) 4\n$3.00 each\nForeign ATM Fees (in any other foreign country) 4\n$5.00 each",
          "anchor_type": "section",
          "anchor_value": "account-fees",
          "page_no": null,
          "chunk_index": 2,
          "anchor_label": "Section account-fees"
        },
        {
          "field_name": "public_display_rate",
          "label": "Public Rate",
          "candidate_value": "0.45",
          "citation_confidence": 0.72,
          "evidence_chunk_id": "chunk-3fb2a59cf25131e3",
          "evidence_excerpt": "TD ePremium Savings Account 2\nTotal Daily Closing Balance\nInterest Rate\n$0 to $9,999.99\n0.000%\n$10,000.00 to $49,999.99\n0.450%\n$50,000.00 to $99,999.99\n0.450%\n$100,000.00 to $249,999.99\n0.450%\n$250,000.00 to $1,000,000.00\n0.450%\nPortion of Daily Closing Balance $1,000,000.01 and over\n0.450%",
          "anchor_type": "section",
          "anchor_value": "td-epremium-savings-account-2",
          "page_no": null,
          "chunk_index": 3,
          "anchor_label": "Section td-epremium-savings-account-2"
        },
        {
          "field_name": "standard_rate",
          "label": "Standard Rate",
          "candidate_value": "0.45",
          "citation_confidence": 0.72,
          "evidence_chunk_id": "chunk-3fb2a59cf25131e3",
          "evidence_excerpt": "TD ePremium Savings Account 2\nTotal Daily Closing Balance\nInterest Rate\n$0 to $9,999.99\n0.000%\n$10,000.00 to $49,999.99\n0.450%\n$50,000.00 to $99,999.99\n0.450%\n$100,000.00 to $249,999.99\n0.450%\n$250,000.00 to $1,000,000.00\n0.450%\nPortion of Daily Closing Balance $1,000,000.01 and over\n0.450%",
          "anchor_type": "section",
          "anchor_value": "td-epremium-savings-account-2",
          "page_no": null,
          "chunk_index": 3,
          "anchor_label": "Section td-epremium-savings-account-2"
        },
        {
          "field_name": "tier_definition_text",
          "label": "Tier Definition Text",
          "candidate_value": "Free online transfers Enjoy unlimited free online transfers to your other TD deposit accounts 2 Automated Savings You can make savings part of your everyday life with our Automated Savings services Additional account benefits Free paperless record keeping or online statements",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-3124258c76c37de7",
          "evidence_excerpt": "Plan Highlights\nHigh interest rate Earn interest calculated daily, when your account balance is $10,000 or more.\nFree online transfers Enjoy unlimited free online transfers to your other TD deposit accounts 2\nAutomated Savings You can make savings part of your everyday life with our Automated Savings services\nAdditional account benefits Free paperless record keeping or online statements",
          "anchor_type": "section",
          "anchor_value": "plan-highlights",
          "page_no": null,
          "chunk_index": 1,
          "anchor_label": "Section plan-highlights"
        },
        {
          "field_name": "transaction_fee",
          "label": "Transaction Fee",
          "candidate_value": "Account Fees Monthly Fee $0 Transaction Fee 3 $5.00 each Free Online Transfers 2 Unlimited Non-TD ATM Fee (in Canada) 4 $2.00 each Foreign ATM Fee (in U.S., Mexico) 4 $3.00 each Foreign ATM Fees (in any other foreign country) 4 $5.00 each",
          "citation_confidence": 0.59,
          "evidence_chunk_id": "chunk-0b7119ff34364921",
          "evidence_excerpt": "Account Fees\nMonthly Fee\n$0\nTransaction Fee 3\n$5.00 each\nFree Online Transfers 2\nUnlimited\nNon-TD ATM Fee (in Canada) 4\n$2.00 each\nForeign ATM Fee (in U.S., Mexico) 4\n$3.00 each\nForeign ATM Fees (in any other foreign country) 4\n$5.00 each",
          "anchor_type": "section",
          "anchor_value": "account-fees",
          "page_no": null,
          "chunk_index": 2,
          "anchor_label": "Section account-fees"
        },
        {
          "field_name": "withdrawal_limit_text",
          "label": "Withdrawal Limit Text",
          "candidate_value": "TD ePremium Savings Account On balances of $10,000 or more High interest rate Free online transfers to your other TD Canada Trust deposit accounts 2 Unlimited Monthly Fee $0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-a7049fc3d80e0546",
          "evidence_excerpt": "TD ePremium Savings Account\nOn balances of $10,000 or more High interest rate\nFree online transfers to your other TD Canada Trust deposit accounts 2 Unlimited\nMonthly Fee $0",
          "anchor_type": "section",
          "anchor_value": "td-epremium-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-epremium-savings-account"
        }
      ],
      "evidence_field_count": 12
    },
    {
      "source_id": "TD-SAV-002",
      "review_task_id": "review-f1776d5bb1266aa3",
      "review_state": "queued",
      "queue_reason_code": "manual_sampling_review",
      "issue_summary": [
        {
          "code": "manual_sampling_review",
          "summary": "Prototype routing keeps all candidates in review.",
          "severity": "warning"
        }
      ],
      "candidate_id": "cand-f49c8b4ae74cf226",
      "run_id": "run_20260411_3527_normalize_harden3",
      "source_document_id": "src-td-html-7922da6819d41139",
      "bank_code": "TD",
      "bank_name": "TD Bank",
      "country_code": "CA",
      "product_family": "deposit",
      "product_type": "savings",
      "subtype_code": "standard",
      "product_name": "TD Every Day Savings Account",
      "source_language": "en",
      "currency": "CAD",
      "candidate_state": "in_review",
      "validation_status": "pass",
      "source_confidence": 0.8838,
      "review_reason_code": "manual_sampling_review",
      "validation_issue_codes": [],
      "candidate_payload": {
        "status": "active",
        "bank_name": "TD Bank",
        "monthly_fee": 0.0,
        "product_name": "TD Every Day Savings Account",
        "subtype_code": "standard",
        "standard_rate": 0.01,
        "effective_date": null,
        "minimum_balance": 0.0,
        "minimum_deposit": 0.0,
        "last_verified_at": "2026-04-12T04:55:30.826489+00:00",
        "description_short": "Earns interest on Every dollar",
        "public_display_fee": 0.0,
        "public_display_rate": 0.01,
        "source_subtype_label": null,
        "target_customer_tags": [],
        "tier_definition_text": "TD Every Day Savings Account Earns interest on Every dollar Free transfers to your other TD Canada Trust deposit accounts 1 Unlimited Monthly Fee $0",
        "included_transactions": "Plan Highlights Included transactions 1 transaction 2 per month Free transfers to your other TD accounts Enjoy unlimited free transfers to your other TD deposit accounts 1 Daily interest Interest calculated on every dollar Automated Savings You can make savings part of your every",
        "withdrawal_limit_text": "TD Every Day Savings Account Earns interest on Every dollar Free transfers to your other TD Canada Trust deposit accounts 1 Unlimited Monthly Fee $0",
        "additional_transaction_fee": "Account Fees Monthly Fee $0 Transactions included per month 2 1 Additional Transactions 2 $3.00 each Free Transfers to your other TD accounts 1 Unlimited Non-TD ATM Fee (in Canada) 3 $2.00 each Foreign ATM Fee (in U.S., Mexico) 3 $3.00 each Foreign ATM Fees (in any other foreign",
        "interest_payment_frequency": "monthly",
        "interest_calculation_method": "Interest is calculated on the daily closing balance."
      },
      "field_mapping_metadata": {
        "currency": {
          "value_type": "string",
          "normalized_value": "CAD",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "currency",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "bank_code": {
          "value_type": "string",
          "normalized_value": "TD",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "bank_code",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "monthly_fee": {
          "value_type": "decimal",
          "normalized_value": 0.0,
          "evidence_chunk_id": "chunk-d853d95a7c12ec77",
          "extraction_method": "heuristic_money",
          "source_field_name": "monthly_fee",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.83
        },
        "country_code": {
          "value_type": "string",
          "normalized_value": "CA",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "country_code",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "product_name": {
          "value_type": "string",
          "normalized_value": "TD Every Day Savings Account",
          "evidence_chunk_id": null,
          "extraction_method": "derived_title",
          "source_field_name": "product_name",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.88
        },
        "product_type": {
          "value_type": "string",
          "normalized_value": "savings",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "product_type",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "subtype_code": {
          "normalized_value": "standard",
          "source_field_name": "product_name",
          "normalization_method": "heuristic_subtype_inference",
          "source_subtype_label": null
        },
        "standard_rate": {
          "value_type": "decimal",
          "normalized_value": 0.01,
          "evidence_chunk_id": "chunk-95e926e14085a7f2",
          "extraction_method": "supporting_rate_table_merge",
          "source_field_name": "standard_rate",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.72
        },
        "product_family": {
          "value_type": "string",
          "normalized_value": "deposit",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "product_family",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "minimum_balance": {
          "value_type": "decimal",
          "normalized_value": 0.0,
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "extraction_method": "heuristic_money",
          "source_field_name": "minimum_balance",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "minimum_deposit": {
          "value_type": "decimal",
          "normalized_value": 0.0,
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "extraction_method": "heuristic_money",
          "source_field_name": "minimum_deposit",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "source_language": {
          "value_type": "string",
          "normalized_value": "en",
          "evidence_chunk_id": null,
          "extraction_method": "derived_context",
          "source_field_name": "source_language",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.99
        },
        "description_short": {
          "value_type": "string",
          "normalized_value": "Earns interest on Every dollar",
          "evidence_chunk_id": null,
          "extraction_method": "derived_description",
          "source_field_name": "description_short",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.7
        },
        "public_display_fee": {
          "value_type": "decimal",
          "normalized_value": 0.0,
          "evidence_chunk_id": "chunk-d853d95a7c12ec77",
          "extraction_method": "heuristic_money",
          "source_field_name": "public_display_fee",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.83
        },
        "public_display_rate": {
          "value_type": "decimal",
          "normalized_value": 0.01,
          "evidence_chunk_id": "chunk-95e926e14085a7f2",
          "extraction_method": "supporting_rate_table_merge",
          "source_field_name": "public_display_rate",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.72
        },
        "tier_definition_text": {
          "value_type": "string",
          "normalized_value": "TD Every Day Savings Account Earns interest on Every dollar Free transfers to your other TD Canada Trust deposit accounts 1 Unlimited Monthly Fee $0",
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "extraction_method": "heuristic_text",
          "source_field_name": "tier_definition_text",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "included_transactions": {
          "value_type": "string",
          "normalized_value": "Plan Highlights Included transactions 1 transaction 2 per month Free transfers to your other TD accounts Enjoy unlimited free transfers to your other TD deposit accounts 1 Daily interest Interest calculated on every dollar Automated Savings You can make savings part of your every",
          "evidence_chunk_id": "chunk-7ea50b3f9827439e",
          "extraction_method": "heuristic_text",
          "source_field_name": "included_transactions",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "withdrawal_limit_text": {
          "value_type": "string",
          "normalized_value": "TD Every Day Savings Account Earns interest on Every dollar Free transfers to your other TD Canada Trust deposit accounts 1 Unlimited Monthly Fee $0",
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "extraction_method": "heuristic_text",
          "source_field_name": "withdrawal_limit_text",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "additional_transaction_fee": {
          "value_type": "string",
          "normalized_value": "Account Fees Monthly Fee $0 Transactions included per month 2 1 Additional Transactions 2 $3.00 each Free Transfers to your other TD accounts 1 Unlimited Non-TD ATM Fee (in Canada) 3 $2.00 each Foreign ATM Fee (in U.S., Mexico) 3 $3.00 each Foreign ATM Fees (in any other foreign",
          "evidence_chunk_id": "chunk-d853d95a7c12ec77",
          "extraction_method": "heuristic_text",
          "source_field_name": "additional_transaction_fee",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "interest_payment_frequency": {
          "value_type": "string",
          "normalized_value": "monthly",
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "extraction_method": "heuristic_frequency",
          "source_field_name": "interest_payment_frequency",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.55
        },
        "interest_calculation_method": {
          "value_type": "string",
          "normalized_value": "Interest is calculated on the daily closing balance.",
          "evidence_chunk_id": "chunk-200e9e741b35b01c",
          "extraction_method": "supporting_interest_pdf_merge",
          "source_field_name": "interest_calculation_method",
          "normalization_method": "heuristic_canonical_mapping",
          "extraction_confidence": 0.85
        }
      },
      "highlight_fields": [
        {
          "field_name": "status",
          "label": "Status",
          "value": "active"
        },
        {
          "field_name": "monthly_fee",
          "label": "Monthly Fee",
          "value": 0.0
        },
        {
          "field_name": "standard_rate",
          "label": "Standard Rate",
          "value": 0.01
        },
        {
          "field_name": "public_display_rate",
          "label": "Public Rate",
          "value": 0.01
        },
        {
          "field_name": "public_display_fee",
          "label": "Public Fee",
          "value": 0.0
        },
        {
          "field_name": "minimum_balance",
          "label": "Minimum Balance",
          "value": 0.0
        },
        {
          "field_name": "minimum_deposit",
          "label": "Minimum Deposit",
          "value": 0.0
        },
        {
          "field_name": "interest_payment_frequency",
          "label": "Interest Payout",
          "value": "monthly"
        },
        {
          "field_name": "last_verified_at",
          "label": "Last Verified",
          "value": "2026-04-12T04:55:30.826489+00:00"
        }
      ],
      "source_context": {
        "source_url": "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/every-day-savings-account",
        "source_type": "html",
        "source_metadata": {
          "purpose": "TD Every Day Savings primary detail source",
          "priority": "P0",
          "source_id": "TD-SAV-002",
          "product_type": "savings",
          "discovery_role": "detail",
          "expected_fields": [
            "product_name",
            "description_short",
            "monthly_fee",
            "included_transactions",
            "additional_transaction_fee"
          ],
          "seed_source_flag": true
        },
        "snapshot_id": "snap-5cb335a1f79c7572",
        "fetched_at": "2026-04-10T05:39:16.848141+00:00",
        "parsed_document_id": "parsed-279eed7a9e8087fa",
        "parse_quality_note": null,
        "stage_status": "completed",
        "warning_count": 1,
        "error_count": 0,
        "error_summary": null,
        "runtime_notes": [
          "Supplemented missing savings rate fields from `TD-SAV-005` current-rate evidence using a product-matched supporting chunk.",
          "Reviewed `TD-SAV-007` fee-governing language for `TD-SAV-002` and left `fee_waiver_condition` unset because the target monthly fee is already $0.",
          "Replaced noisy interest-rule fields with targeted `TD-SAV-008` governing PDF evidence where stronger canonical wording was available.",
          "Suppressed noisy `fee_waiver_condition` for `TD-SAV-002` because the product monthly fee is already $0 and no product-specific waiver rule should be persisted.",
          "Suppressed noisy `notes` text before normalization.",
          "Suppressed noisy `eligibility_text` text before normalization.",
          "Suppressed `promotional_period_text` because the extracted text described marketing copy rather than a bounded promotional period."
        ]
      },
      "evidence_links": [
        {
          "field_name": "additional_transaction_fee",
          "label": "Additional Transaction Fee",
          "candidate_value": "Account Fees Monthly Fee $0 Transactions included per month 2 1 Additional Transactions 2 $3.00 each Free Transfers to your other TD accounts 1 Unlimited Non-TD ATM Fee (in Canada) 3 $2.00 each Foreign ATM Fee (in U.S., Mexico) 3 $3.00 each Foreign ATM Fees (in any other foreign",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-d853d95a7c12ec77",
          "evidence_excerpt": "Account Fees\nMonthly Fee\n$0\nTransactions included per month 2\n1\nAdditional Transactions 2\n$3.00 each\nFree Transfers to your other TD accounts 1\nUnlimited\nNon-TD ATM Fee (in Canada) 3\n$2.00 each\nForeign ATM Fee (in U.S., Mexico) 3\n$3.00 each\nForeign ATM Fees (in any other foreign country) 3\n$5.00 each\nPaper Statement Fee\n$2.00 per month",
          "anchor_type": "section",
          "anchor_value": "account-fees",
          "page_no": null,
          "chunk_index": 2,
          "anchor_label": "Section account-fees"
        },
        {
          "field_name": "included_transactions",
          "label": "Included Transactions",
          "candidate_value": "Plan Highlights Included transactions 1 transaction 2 per month Free transfers to your other TD accounts Enjoy unlimited free transfers to your other TD deposit accounts 1 Daily interest Interest calculated on every dollar Automated Savings You can make savings part of your every",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-7ea50b3f9827439e",
          "evidence_excerpt": "Plan Highlights\nIncluded transactions 1 transaction 2 per month\nFree transfers to your other TD accounts Enjoy unlimited free transfers to your other TD deposit accounts 1\nDaily interest Interest calculated on every dollar\nAutomated Savings You can make savings part of your everyday life with our Automated Savings service\nAdditional account benefits Free paperless record keeping or online statements",
          "anchor_type": "section",
          "anchor_value": "plan-highlights",
          "page_no": null,
          "chunk_index": 1,
          "anchor_label": "Section plan-highlights"
        },
        {
          "field_name": "interest_calculation_method",
          "label": "Interest Calculation Method",
          "candidate_value": "Interest is calculated on the daily closing balance.",
          "citation_confidence": 0.85,
          "evidence_chunk_id": "chunk-200e9e741b35b01c",
          "evidence_excerpt": "About Our Interest Calculations\nAs of December 18, 2025\nCHART 2: SAVINGS ACCOUNTS\nSavings Account Daily Closing Balance Rate Details\nTD Every Day Savings Total Daily Closing Balance\nUp to $999.99\nTotal Daily Closing Balance\n$1,000.00 to $4,999.99\nTotal Daily Closing Balance\n$5,000.00 to $9,999.99\nTotal Daily Closing Balance\n$10,000.00 to $24,999.99\nTotal Daily Closing Balance\n$25,000.00 to $59,999.99\nTotal Daily Closing Balance\n$60,000.00 and over\n0.010%\n0.010%\n0.010%\n0.010%\n0.010%\n0.010%\nOnly one interest rate applies to your\ntotal Daily Closing Balance based on the\nTiers listed. Interest will be calculated\neach day by multiplying your total Daily\nClosing Balance by the interest rate for\nthe Tier to which your total Daily Closing\nBalance corresponds.\nTD ePremium Savings Total Daily Closing Balance\nUp to $9,999.99\nTotal Daily Closing Balance\n$10,000.00 to $49,999.99\nTotal Daily Closing",
          "anchor_type": "page",
          "anchor_value": "page-3",
          "page_no": 3,
          "chunk_index": 8,
          "anchor_label": "Page 3"
        },
        {
          "field_name": "interest_payment_frequency",
          "label": "Interest Payout",
          "candidate_value": "monthly",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "evidence_excerpt": "TD Every Day\u00a0Savings Account\nEarns interest on Every dollar\nFree transfers to your other TD Canada Trust deposit accounts 1 Unlimited\nMonthly Fee $0",
          "anchor_type": "section",
          "anchor_value": "td-every-day-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-every-day-savings-account"
        },
        {
          "field_name": "minimum_balance",
          "label": "Minimum Balance",
          "candidate_value": "0.0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "evidence_excerpt": "TD Every Day\u00a0Savings Account\nEarns interest on Every dollar\nFree transfers to your other TD Canada Trust deposit accounts 1 Unlimited\nMonthly Fee $0",
          "anchor_type": "section",
          "anchor_value": "td-every-day-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-every-day-savings-account"
        },
        {
          "field_name": "minimum_deposit",
          "label": "Minimum Deposit",
          "candidate_value": "0.0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "evidence_excerpt": "TD Every Day\u00a0Savings Account\nEarns interest on Every dollar\nFree transfers to your other TD Canada Trust deposit accounts 1 Unlimited\nMonthly Fee $0",
          "anchor_type": "section",
          "anchor_value": "td-every-day-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-every-day-savings-account"
        },
        {
          "field_name": "monthly_fee",
          "label": "Monthly Fee",
          "candidate_value": "0.0",
          "citation_confidence": 0.83,
          "evidence_chunk_id": "chunk-d853d95a7c12ec77",
          "evidence_excerpt": "Account Fees\nMonthly Fee\n$0\nTransactions included per month 2\n1\nAdditional Transactions 2\n$3.00 each\nFree Transfers to your other TD accounts 1\nUnlimited\nNon-TD ATM Fee (in Canada) 3\n$2.00 each\nForeign ATM Fee (in U.S., Mexico) 3\n$3.00 each\nForeign ATM Fees (in any other foreign country) 3\n$5.00 each\nPaper Statement Fee\n$2.00 per month",
          "anchor_type": "section",
          "anchor_value": "account-fees",
          "page_no": null,
          "chunk_index": 2,
          "anchor_label": "Section account-fees"
        },
        {
          "field_name": "public_display_fee",
          "label": "Public Fee",
          "candidate_value": "0.0",
          "citation_confidence": 0.83,
          "evidence_chunk_id": "chunk-d853d95a7c12ec77",
          "evidence_excerpt": "Account Fees\nMonthly Fee\n$0\nTransactions included per month 2\n1\nAdditional Transactions 2\n$3.00 each\nFree Transfers to your other TD accounts 1\nUnlimited\nNon-TD ATM Fee (in Canada) 3\n$2.00 each\nForeign ATM Fee (in U.S., Mexico) 3\n$3.00 each\nForeign ATM Fees (in any other foreign country) 3\n$5.00 each\nPaper Statement Fee\n$2.00 per month",
          "anchor_type": "section",
          "anchor_value": "account-fees",
          "page_no": null,
          "chunk_index": 2,
          "anchor_label": "Section account-fees"
        },
        {
          "field_name": "public_display_rate",
          "label": "Public Rate",
          "candidate_value": "0.01",
          "citation_confidence": 0.72,
          "evidence_chunk_id": "chunk-95e926e14085a7f2",
          "evidence_excerpt": "TD Every Day Savings Account 1\nTotal Daily Closing Balance\nInterest Rate\n$0 to $999.99\n0.010%\n$1,000.00 to $4,999.99\n0.010%\n$5,000.00 to $9999.99\n0.010%\n$10,000.00 to $24,999.99\n0.010%\n$25,000.00 to $59,999.99\n0.010%\n$60,000.00 and over\n0.010%",
          "anchor_type": "section",
          "anchor_value": "td-every-day-savings-account-1",
          "page_no": null,
          "chunk_index": 1,
          "anchor_label": "Section td-every-day-savings-account-1"
        },
        {
          "field_name": "standard_rate",
          "label": "Standard Rate",
          "candidate_value": "0.01",
          "citation_confidence": 0.72,
          "evidence_chunk_id": "chunk-95e926e14085a7f2",
          "evidence_excerpt": "TD Every Day Savings Account 1\nTotal Daily Closing Balance\nInterest Rate\n$0 to $999.99\n0.010%\n$1,000.00 to $4,999.99\n0.010%\n$5,000.00 to $9999.99\n0.010%\n$10,000.00 to $24,999.99\n0.010%\n$25,000.00 to $59,999.99\n0.010%\n$60,000.00 and over\n0.010%",
          "anchor_type": "section",
          "anchor_value": "td-every-day-savings-account-1",
          "page_no": null,
          "chunk_index": 1,
          "anchor_label": "Section td-every-day-savings-account-1"
        },
        {
          "field_name": "tier_definition_text",
          "label": "Tier Definition Text",
          "candidate_value": "TD Every Day Savings Account Earns interest on Every dollar Free transfers to your other TD Canada Trust deposit accounts 1 Unlimited Monthly Fee $0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "evidence_excerpt": "TD Every Day\u00a0Savings Account\nEarns interest on Every dollar\nFree transfers to your other TD Canada Trust deposit accounts 1 Unlimited\nMonthly Fee $0",
          "anchor_type": "section",
          "anchor_value": "td-every-day-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-every-day-savings-account"
        },
        {
          "field_name": "withdrawal_limit_text",
          "label": "Withdrawal Limit Text",
          "candidate_value": "TD Every Day Savings Account Earns interest on Every dollar Free transfers to your other TD Canada Trust deposit accounts 1 Unlimited Monthly Fee $0",
          "citation_confidence": 0.55,
          "evidence_chunk_id": "chunk-6e67c66ca2ce575a",
          "evidence_excerpt": "TD Every Day\u00a0Savings Account\nEarns interest on Every dollar\nFree transfers to your other TD Canada Trust deposit accounts 1 Unlimited\nMonthly Fee $0",
          "anchor_type": "section",
          "anchor_value": "td-every-day-savings-account",
          "page_no": null,
          "chunk_index": 0,
          "anchor_label": "Section td-every-day-savings-account"
        }
      ],
      "evidence_field_count": 12
    }
  ]
};
