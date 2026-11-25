# Data cleaning report

Source: Fannie Mae public sample file, 108 columns, 757 monthly records, 8 loans. Prepared on our own computer (step 1).
Kept **61 columns** (the same 61 'active fields' the test cases describe). Dropped **47 columns that are empty on every row**: reference_pool_id, master_servicer, upb_at_issuance, interest_only_first_principal_and_interest_payment_date, months_to_amortization, mortgage_insurance_cancellation_indicator, repurchase_date, scheduled_principal_current, unscheduled_principal_current, credit_enhancement_proceeds, repurchase_make_whole_proceeds, other_foreclosure_proceeds, original_list_start_date, original_list_price, current_list_start_date, current_list_price, borrower_credit_score_at_issuance, co_borrower_credit_score_at_issuance, borrower_credit_score_current, co_borrower_credit_score_current, current_period_modification_loss_amount, cumulative_modification_loss_amount, current_period_credit_event_net_gain_or_loss, cumulative_credit_event_net_gain_or_loss, special_eligibility_program, zero_balance_code_change_date, loan_holdback_indicator, loan_holdback_effective_date, delinquent_accrued_interest, property_valuation_method, arm_initial_fixed_rate_period_5_yr_indicator, arm_product_type, initial_fixed_rate_period, interest_rate_adjustment_frequency, next_interest_rate_adjustment_date, next_payment_change_date, index, arm_cap_structure, initial_interest_rate_cap_up_percent, periodic_interest_rate_cap_up_percent, lifetime_interest_rate_cap_up_percent, mortgage_margin, arm_balloon_indicator, arm_plan_number, deal_name, alternative_delinquency_resolution_count, total_deferral_amount

## Kept, but worth knowing

- **All zero** (nothing happened in this sample): modification_related_non_interest_bearing_upb, principal_forgiveness_amount, foreclosure_principal_write_off_amount
- **One value on every row** (no variation in this sample): first_time_home_buyer_indicator = N, occupancy_status = P, amortization_type = FRM, prepayment_penalty_indicator = N, interest_only_loan_indicator = N, relocation_mortgage_indicator = N, high_balance_loan_indicator = N, high_loan_to_value_hltv_refinance_option_indicator = N
- **Location details** (3-digit zip, metro area): zip_code_short, metropolitan_statistical_area_msa_or_metropolitan_statistical_division_area_msda. The agents are told never to reveal or infer where a borrower lives.

## Tables built

- `loan_monthly`: the 61 kept columns, one row per loan per month (757 rows).
- `loan_static`: one row per loan with short names (loan_id, state, purpose, orig_upb, ltv, cltv, dti, min_score, ...).
- `default_risk_screen` (view): the configured screen with one flag per rule and `flag_count`.
- `loan_features`: derived facts per loan: loan_identifier, property_state, original_upb, original_interest_rate, ltv, cltv, dti, borrower_credit_score, co_borrower_credit_score, borrower_minimum_credit_score, has_subordinate_financing, monthly_records, first_period, last_period, peak_months_delinquent, peak_first_period, delinquent_months, first_90_plus_period, first_180_plus_period, first_modified_period, outcome, zero_balance_code, zero_balance_effective_date, upb_at_removal, disposition_costs, net_sales_proceeds, indicative_net_loss, indicative_severity_pct, max_upb_seen, last_upb, last_delinquency_status, last_interest_rate
