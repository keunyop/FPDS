BEGIN;

UPDATE product_type_registry
SET expected_fields = CASE product_type_code
    WHEN 'chequing' THEN '["product_name","description_short","monthly_fee","public_display_fee","fee_waiver_condition","minimum_balance","included_transactions","unlimited_transactions_flag","interac_e_transfer_included","overdraft_available","cheque_book_info","student_plan_flag","newcomer_plan_flag","eligibility_text","application_method","deposit_insurance","notes"]'::jsonb
    WHEN 'savings' THEN '["product_name","description_short","standard_rate","base_12_month_rate","public_display_rate","promotional_rate","promotional_period_text","introductory_rate_flag","monthly_fee","minimum_balance","interest_calculation_method","interest_payment_frequency","tiered_rate_flag","tier_definition_text","withdrawal_limit_text","registered_flag","term_rate_table","eligibility_text","application_method","deposit_insurance","notes"]'::jsonb
    WHEN 'gic' THEN '["product_name","description_short","standard_rate","base_12_month_rate","public_display_rate","promotional_rate","minimum_deposit","term_length_text","term_length_days","term_rate_table","redeemable_flag","non_redeemable_flag","compounding_frequency","payout_option","registered_plan_supported","eligibility_text","application_method","post_maturity_interest_rate","tax_benefits","deposit_insurance","notes"]'::jsonb
    ELSE expected_fields
END,
updated_at = now()
WHERE product_family = 'deposit'
  AND product_type_code IN ('chequing', 'savings', 'gic');

UPDATE source_registry_item
SET expected_fields = CASE product_type
    WHEN 'chequing' THEN '["product_name","description_short","monthly_fee","public_display_fee","fee_waiver_condition","minimum_balance","included_transactions","unlimited_transactions_flag","interac_e_transfer_included","overdraft_available","cheque_book_info","student_plan_flag","newcomer_plan_flag","eligibility_text","application_method","deposit_insurance","notes"]'::jsonb
    WHEN 'savings' THEN '["product_name","description_short","standard_rate","base_12_month_rate","public_display_rate","promotional_rate","promotional_period_text","introductory_rate_flag","monthly_fee","minimum_balance","interest_calculation_method","interest_payment_frequency","tiered_rate_flag","tier_definition_text","withdrawal_limit_text","registered_flag","term_rate_table","eligibility_text","application_method","deposit_insurance","notes"]'::jsonb
    WHEN 'gic' THEN '["product_name","description_short","standard_rate","base_12_month_rate","public_display_rate","promotional_rate","minimum_deposit","term_length_text","term_length_days","term_rate_table","redeemable_flag","non_redeemable_flag","compounding_frequency","payout_option","registered_plan_supported","eligibility_text","application_method","post_maturity_interest_rate","tax_benefits","deposit_insurance","notes"]'::jsonb
    ELSE expected_fields
END,
updated_at = now()
WHERE product_type IN ('chequing', 'savings', 'gic')
  AND status = 'active';

INSERT INTO migration_history (migration_name)
VALUES ('0024_deposit_field_contract_defaults.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
