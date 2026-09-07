# QC_REPORT — veterinary_clinic_system (v2, 98-task suite)

Per-task QC battery (`tools/qc_task.py`), each task against **fresh containers**:

| run | expectation |
|---|---|
| `noop` — verifier on pristine state | FAIL (exit 1) |
| `random` — verifier after 10 valid-API junk actions | FAIL |
| `hardcode` — verifier after a lazy plausible-but-underived write | FAIL |
| `gold` — reference solution exits 0 | PASS |
| `verify_after_gold` | PASS (exit 0) |
| `verify_idempotent` — verifier rerun on identical state | PASS |

Machine-readable transcripts: `qc_results/<task_id>.json`. Par step counts are in each task's `task.json` (`par_steps`), recorded from gold API-call counts.

## Summary

**Total tasks QC'd:** 98
**Passing:** 98 / 98 (100.0%)
**Failing:** 0
**Failing tasks:** none

Every one of the 98 tasks is now **hard** difficulty (v1 had a 20 easy / 48 medium / 32 hard mix) — the hardmode rewrite raised the floor instead of just adding a harder tail. Surface split: 86 backend, 8 websearch, 4 frontend. Every gold solution also passes an idempotent-rerun check (`idempotent_pass: true` in every `qc_results/<id>.json`), not just the 4 tasks in v1 whose category was literally "idempotency."

### Category-tag frequency (v2 tasks carry 2-4 category tags each, e.g. `workflow,aggregation,reconciliation`)

| category | tasks tagged |
|---|---|
| aggregation | 77 |
| workflow | 60 |
| reconciliation | 59 |
| idempotency | 19 |
| update | 17 |
| repair | 16 |
| report | 14 |
| create | 13 |
| delete | 3 |
| dashboard | 2 |
| analytics | 1 |
| compliance | 1 |
| billing | 1 |
| reporting | 1 |
| websearch | 1 |
| finance | 1 |
| pricing | 1 |
| staffing | 1 |
| audit | 1 |

## Per-task result (latest QC run)

| task_id | difficulty | surface | categories | pass |
|---|---|---|---|---|
| 001_overdue_vaccine_compliance_flag | hard | backend | update,aggregation,reconciliation | PASS |
| 002_rabies_booster_due_recompute | hard | backend | update,aggregation,workflow | PASS |
| 003_vaccination_reminder_batch | hard | backend | workflow,aggregation,reconciliation | PASS |
| 004_fvrcp_kitten_series_check | hard | backend | workflow,analytics,reconciliation | PASS |
| 005_vaccine_lot_recall_trace | hard | backend | aggregation,workflow,reconciliation | PASS |
| 006_bordetella_boarding_gate | hard | backend | workflow,update,reconciliation | PASS |
| 007_overdue_vax_owner_letters | hard | backend | workflow,aggregation,reconciliation | PASS |
| 009_rabies_certificate_doc_check | hard | backend | repair,create,aggregation | PASS |
| 011_boarding_checkin_flow | hard | backend | workflow,create,aggregation | PASS |
| 012_boarding_checkout_cleaning_cycle | hard | backend | workflow,create,aggregation | PASS |
| 013_daily_log_completion | hard | backend | workflow,create,aggregation | PASS |
| 014_boarding_occupancy_snapshot | hard | backend | aggregation,workflow,reconciliation | PASS |
| 015_run_maintenance_rebalance | hard | backend | update,workflow,aggregation | PASS |
| 016_boarding_stay_invoice_draft | hard | backend | workflow,aggregation,reconciliation | PASS |
| 017_feeding_instruction_digest | hard | backend | aggregation,workflow | PASS |
| 018_boarding_overstay_flag | hard | backend | update,workflow,aggregation | PASS |
| 019_run_status_audit | hard | backend | repair,aggregation,reconciliation | PASS |
| 020_boarding_deposit_writeoff | hard | websearch | update,workflow,aggregation | PASS |
| 021_overdue_invoice_flagging | hard | backend | update,workflow,aggregation | PASS |
| 022_ar_aging_report | hard | websearch | aggregation,reconciliation | PASS |
| 023_late_fee_assessment | hard | backend | update,workflow,aggregation | PASS |
| 024_estimate_to_invoice_conversion | hard | backend | create,workflow,aggregation | PASS |
| 025_statement_balance_resync | hard | backend | repair,create,aggregation | PASS |
| 026_invoice_number_gap_audit | hard | backend | aggregation,reconciliation | PASS |
| 027_paid_invoice_receipt_log | hard | backend | create,aggregation,workflow | PASS |
| 028_draft_invoice_purge | hard | backend | delete,create,aggregation | PASS |
| 029_owner_payment_plan_split | hard | backend | workflow,create,aggregation | PASS |
| 030_revenue_by_location_rollup | hard | backend | aggregation,reconciliation,report | PASS |
| 031_cs_administer_witnessed_entry | hard | backend | create,workflow,reconciliation | PASS |
| 032_cs_running_balance_reconciliation | hard | backend | reconciliation,aggregation,report | PASS |
| 033_cs_log_gap_detection | hard | backend | repair,reconciliation,report | PASS |
| 034_pharmacy_reorder_report | hard | backend | aggregation,reconciliation,report | PASS |
| 035_cs_waste_protocol_entry | hard | backend | workflow,update,idempotency | PASS |
| 036_inventory_valuation_report | hard | backend | aggregation,reconciliation,idempotency | PASS |
| 037_vaccine_stock_shrink | hard | backend | update,aggregation,idempotency | PASS |
| 038_controlled_dea_schedule_backfill | hard | backend | repair,aggregation,idempotency | PASS |
| 039_low_stock_supplier_summary | hard | backend | aggregation,reconciliation,idempotency | PASS |
| 040_controlled_refill_freeze | hard | backend | workflow,compliance,aggregation | PASS |
| 041_noshow_fee_flag | hard | backend | workflow,billing,aggregation | PASS |
| 042_waitlist_promotion | hard | backend | workflow,repair,idempotency | PASS |
| 043_double_booking_repair | hard | backend | repair,workflow,aggregation | PASS |
| 044_provider_utilization_report | hard | backend | aggregation,reporting,reconciliation | PASS |
| 045_same_day_reschedule_block | hard | backend | workflow,update,reconciliation | PASS |
| 046_appointment_reminder_queue_fill | hard | backend | workflow,aggregation,reconciliation | PASS |
| 047_exam_room_turnover_report | hard | backend | aggregation,reconciliation | PASS |
| 048_appointment_reason_triage | hard | backend | update,aggregation,reconciliation | PASS |
| 049_no_show_rate_report | hard | backend | aggregation,reconciliation | PASS |
| 050_schedule_density_rebalance | hard | backend | workflow,reconciliation,idempotency | PASS |
| 051_critical_lab_callback | hard | backend | workflow,aggregation,reconciliation,idempotency | PASS |
| 052_soap_note_lock_enforcement | hard | websearch | update,workflow,reconciliation,idempotency | PASS |
| 053_problem_list_rollup | hard | backend | aggregation,idempotency | PASS |
| 054_weight_trend_alert | hard | websearch | aggregation,workflow,reconciliation,idempotency | PASS |
| 055_amendment_chain_repair | hard | backend | repair,workflow,aggregation | PASS |
| 056_lab_flag_summary | hard | backend | aggregation,workflow,idempotency | PASS |
| 057_unlinked_lab_orphans | hard | backend | repair,reconciliation,aggregation,idempotency | PASS |
| 058_visit_note_completeness_score | hard | backend | aggregation,workflow,idempotency | PASS |
| 059_species_visit_mix_report | hard | frontend | aggregation,workflow,reconciliation | PASS |
| 060_geriatric_panel_recall | hard | websearch | workflow,aggregation,reconciliation | PASS |
| 061_new_patient_enrollment | hard | websearch | create,workflow,reconciliation | PASS |
| 062_transfer_approval_flow | hard | frontend | workflow,reconciliation,aggregation | PASS |
| 063_duplicate_owner_merge | hard | frontend | repair,workflow,reconciliation | PASS |
| 064_microchip_format_audit | hard | websearch | repair,aggregation,reconciliation | PASS |
| 065_deceased_patient_archive | hard | backend | workflow,reconciliation,idempotency | PASS |
| 066_owner_contact_normalization | hard | backend | update,workflow,aggregation | PASS |
| 067_multi_pet_household_report | hard | backend | aggregation,workflow,report | PASS |
| 068_patient_species_weight_sanity | hard | websearch | repair,websearch,aggregation | PASS |
| 069_transfer_chain_consistency | hard | backend | repair,reconciliation,report | PASS |
| 070_owner_lifetime_value_report | hard | backend | aggregation,reconciliation,finance | PASS |
| 071_location_performance_dashboard | hard | frontend | aggregation,reconciliation,dashboard | PASS |
| 072_fee_schedule_parity_check | hard | backend | aggregation,reconciliation,pricing | PASS |
| 073_provider_location_coverage | hard | backend | aggregation,staffing,dashboard | PASS |
| 074_cross_location_patient_moves | hard | backend | aggregation,reconciliation,audit | PASS |
| 075_sql_vs_api_crosscheck | hard | backend | aggregation,reconciliation,report | PASS |
| 076_weekly_schedule_load_balance | hard | backend | aggregation,reconciliation,report | PASS |
| 077_data_freshness_report | hard | backend | aggregation,reconciliation,report | PASS |
| 078_timezone_safe_daily_census | hard | backend | aggregation,reconciliation,report | PASS |
| 079_appointment_to_visit_linkage | hard | backend | reconciliation,aggregation,repair | PASS |
| 080_enterprise_kpi_pack | hard | backend | aggregation,reconciliation,workflow | PASS |
| 081_reminder_template_render | hard | backend | workflow,reconciliation,update | PASS |
| 082_inbound_comms_triage | hard | backend | workflow,update,aggregation | PASS |
| 083_file_storage_audit | hard | backend | aggregation,reconciliation,workflow | PASS |
| 084_imaging_metadata_gap_fill | hard | backend | repair,reconciliation,workflow | PASS |
| 085_reminder_staleness_sweep | hard | backend | delete,workflow,report | PASS |
| 086_owner_statement_messages | hard | backend | create,aggregation,report | PASS |
| 087_template_deprecation_migration | hard | backend | update,report,workflow | PASS |
| 088_comms_volume_by_channel | hard | backend | aggregation,report | PASS |
| 089_document_expiry_tracker | hard | backend | aggregation,reconciliation,workflow | PASS |
| 090_after_hours_message_log | hard | backend | create,workflow,reconciliation | PASS |
| 091_idempotent_reminder_send | hard | backend | idempotency,workflow,aggregation | PASS |
| 092_idempotent_occupancy_sync | hard | backend | idempotency,reconciliation,workflow | PASS |
| 093_idempotent_invoice_numbering | hard | backend | idempotency,workflow,aggregation | PASS |
| 094_idempotent_daily_log_close | hard | backend | idempotency,workflow,aggregation | PASS |
| 095_seed_integrity_forensics | hard | backend | aggregation,reconciliation | PASS |
| 096_temporal_anomaly_detection | hard | backend | aggregation,reconciliation | PASS |
| 097_referential_cascade_delete | hard | backend | delete,workflow,reconciliation | PASS |
| 098_negative_balance_underflow | hard | backend | repair,reconciliation,workflow | PASS |
| 099_full_state_reconciliation | hard | backend | reconciliation,aggregation,workflow | PASS |
| 100_grand_daily_closeout | hard | backend | workflow,reconciliation,aggregation | PASS |

## Notes on baseline design

- **Random baseline** traffic: logins, `GET /v1/tables`, sampled collection reads, and pushes to a scratch `veterinary_clinic_system_junk_probe` collection — valid API usage that never touches task-relevant state.
- **Hardcode baseline**: for report tasks, a plausible ops_reports row with a stale `batch_code` and invented numbers; for mutation tasks, a plausible un-derived status flip on the first row of the blast collection. Both fail because verifiers recompute expectations from live data + the live per-episode nonce, and — new in v2 — cross-check every aggregate two independent ways (a raw-row Python filter and a separate SQL `GROUP BY`/`SUM`) before ever comparing to the agent's written report.
- Baselines run on a separate container from the gold run so baseline mutations cannot contaminate gold-final-state grading.
- Every task now ships **two independently written gold solutions** (`gold.py` + `gold_alt.py`); both must pass the same verifier, catching verifiers that were accidentally overfit to one solution's incidental behavior (row iteration order, tie-breaking, etc.).
