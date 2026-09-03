# QC_REPORT — veterinary_clinic_system (100-task suite)

Per-task QC battery (tools/qc_task.py), each task against **fresh containers**:

| run | expectation |
|---|---|
| `noop` — verifier on pristine state | FAIL (exit 1) |
| `random` — verifier after 10 valid-API junk actions | FAIL |
| `hardcode` — verifier after a lazy plausible-but-underived write | FAIL |
| `gold` — reference solution exits 0 | PASS |
| `verify_after_gold` | PASS (exit 0) |
| `verify_idempotent` — verifier rerun on identical state | PASS |

Machine-readable transcripts: `qc_results/<task_id>.json`. Par step counts are
in each task's `task.json` (`par_steps`), recorded from gold API-call counts.

## Summary

**Total tasks QC'd:** 100
**Passing:** 100 / 100 (100.0%)
**Failing:** 0
**Failing tasks:** none

### Per-category breakdown

| category | pass | fail | total |
|---|---|---|---|
| easy / aggregation / backend | 9 | 0 | 9 |
| easy / create / backend | 1 | 0 | 1 |
| easy / create / websearch | 2 | 0 | 2 |
| easy / delete / backend | 1 | 0 | 1 |
| easy / update / backend | 4 | 0 | 4 |
| easy / workflow / backend | 1 | 0 | 1 |
| easy / workflow / frontend | 2 | 0 | 2 |
| hard / aggregation / backend | 6 | 0 | 6 |
| hard / aggregation / frontend | 1 | 0 | 1 |
| hard / aggregation / websearch | 4 | 0 | 4 |
| hard / delete / backend | 1 | 0 | 1 |
| hard / idempotency / backend | 1 | 0 | 1 |
| hard / idempotency / frontend | 1 | 0 | 1 |
| hard / repair / backend | 6 | 0 | 6 |
| hard / repair / frontend | 2 | 0 | 2 |
| hard / repair / websearch | 1 | 0 | 1 |
| hard / update / websearch | 1 | 0 | 1 |
| hard / workflow / backend | 3 | 0 | 3 |
| hard / workflow / frontend | 1 | 0 | 1 |
| hard / workflow / websearch | 4 | 0 | 4 |
| medium / aggregation / backend | 12 | 0 | 12 |
| medium / aggregation / frontend | 3 | 0 | 3 |
| medium / aggregation / websearch | 2 | 0 | 2 |
| medium / create / backend | 2 | 0 | 2 |
| medium / create / frontend | 1 | 0 | 1 |
| medium / delete / backend | 1 | 0 | 1 |
| medium / idempotency / backend | 1 | 0 | 1 |
| medium / idempotency / frontend | 1 | 0 | 1 |
| medium / repair / backend | 5 | 0 | 5 |
| medium / repair / websearch | 3 | 0 | 3 |
| medium / update / backend | 4 | 0 | 4 |
| medium / update / frontend | 1 | 0 | 1 |
| medium / update / websearch | 4 | 0 | 4 |
| medium / workflow / backend | 1 | 0 | 1 |
| medium / workflow / frontend | 7 | 0 | 7 |

## Transcript — exemplar tasks (executed interactively during authoring)

### 021_overdue_invoice_flagging (easy, update, backend)

```
$ python tools/qc_task.py 021_overdue_invoice_flagging
021_overdue_invoice_flagging: PASS {'noop_fail': True, 'random_fail': True,
'hardcode_fail': True, 'gold_pass': True, 'idempotent_pass': True}
```

### 008_vaccination_compliance_report (hard, aggregation, backend)

```
$ python tools/qc_all.py --workers 2 --only 008_,011_
008_vaccination_compliance_report: PASS {'noop_fail': True, 'random_fail': True,
'hardcode_fail': True, 'gold_pass': True, 'idempotent_pass': True}
```

### 011_boarding_checkin_flow (easy, workflow, frontend)

```
011_boarding_checkin_flow: PASS {'noop_fail': True, 'random_fail': True,
'hardcode_fail': True, 'gold_pass': True, 'idempotent_pass': True}
```

## Equivalence tests

### Per-task result (latest QC run)

| task_id | pass | reset_s |
|---|---|---|
| 001_overdue_vaccine_compliance_flag | PASS | 47.3 |
| 002_rabies_booster_due_recompute | PASS | 49.3 |
| 003_vaccination_reminder_batch | PASS | 46.2 |
| 004_fvrcp_kitten_series_check | PASS | 45.8 |
| 005_vaccine_lot_recall_trace | PASS | 88.1 |
| 006_bordetella_boarding_gate | PASS | 81.5 |
| 007_overdue_vax_owner_letters | PASS | 36.0 |
| 008_vaccination_compliance_report | PASS | 28.3 |
| 009_rabies_certificate_doc_check | PASS | 31.0 |
| 010_vaccine_inventory_coverage | PASS | 30.1 |
| 011_boarding_checkin_flow | PASS | 31.2 |
| 012_boarding_checkout_cleaning_cycle | PASS | 31.0 |
| 013_daily_log_completion | PASS | 27.5 |
| 014_boarding_occupancy_snapshot | PASS | 27.7 |
| 015_run_maintenance_rebalance | PASS | 34.4 |
| 016_boarding_stay_invoice_draft | PASS | 19.3 |
| 017_feeding_instruction_digest | PASS | 19.0 |
| 018_boarding_overstay_flag | PASS | 15.4 |
| 019_run_status_audit | PASS | 58.7 |
| 020_boarding_deposit_writeoff | PASS | 18.6 |
| 021_overdue_invoice_flagging | PASS | 18.6 |
| 022_ar_aging_report | PASS | 37.1 |
| 023_late_fee_assessment | PASS | 16.2 |
| 024_estimate_to_invoice_conversion | PASS | 57.9 |
| 025_statement_balance_resync | PASS | 49.0 |
| 026_invoice_number_gap_audit | PASS | 34.0 |
| 027_paid_invoice_receipt_log | PASS | 40.4 |
| 028_draft_invoice_purge | PASS | 19.4 |
| 029_owner_payment_plan_split | PASS | 21.5 |
| 030_revenue_by_location_rollup | PASS | 20.4 |
| 031_cs_administer_witnessed_entry | PASS | 31.5 |
| 032_cs_running_balance_reconciliation | PASS | 52.1 |
| 033_cs_log_gap_detection | PASS | 35.2 |
| 034_pharmacy_reorder_report | PASS | 31.7 |
| 035_cs_waste_protocol_entry | PASS | 42.7 |
| 036_inventory_valuation_report | PASS | 28.5 |
| 037_vaccine_stock_shrink | PASS | 27.5 |
| 038_controlled_dea_schedule_backfill | PASS | 24.2 |
| 039_low_stock_supplier_summary | PASS | 23.0 |
| 040_controlled_refill_freeze | PASS | 29.3 |
| 041_noshow_fee_flag | PASS | 15.2 |
| 042_waitlist_promotion | PASS | 19.2 |
| 043_double_booking_repair | PASS | 23.1 |
| 044_provider_utilization_report | PASS | 17.2 |
| 045_same_day_reschedule_block | PASS | 16.2 |
| 046_appointment_reminder_queue_fill | PASS | 17.6 |
| 047_exam_room_turnover_report | PASS | 18.5 |
| 048_appointment_reason_triage | PASS | 17.9 |
| 049_no_show_rate_report | PASS | 18.7 |
| 050_schedule_density_rebalance | PASS | 17.9 |
| 051_critical_lab_callback | PASS | 16.4 |
| 052_soap_note_lock_enforcement | PASS | 17.6 |
| 053_problem_list_rollup | PASS | 18.4 |
| 054_weight_trend_alert | PASS | 15.5 |
| 055_amendment_chain_repair | PASS | 18.3 |
| 056_lab_flag_summary | PASS | 20.1 |
| 057_unlinked_lab_orphans | PASS | 17.6 |
| 058_visit_note_completeness_score | PASS | 16.1 |
| 059_species_visit_mix_report | PASS | 19.4 |
| 060_geriatric_panel_recall | PASS | 15.7 |
| 061_new_patient_enrollment | PASS | 17.0 |
| 062_transfer_approval_flow | PASS | 24.9 |
| 063_duplicate_owner_merge | PASS | 45.4 |
| 064_microchip_format_audit | PASS | 18.4 |
| 065_deceased_patient_archive | PASS | 19.8 |
| 066_owner_contact_normalization | PASS | 16.2 |
| 067_multi_pet_household_report | PASS | 17.4 |
| 068_patient_species_weight_sanity | PASS | 16.8 |
| 069_transfer_chain_consistency | PASS | 17.5 |
| 070_owner_lifetime_value_report | PASS | 18.9 |
| 071_location_performance_dashboard | PASS | 28.8 |
| 072_fee_schedule_parity_check | PASS | 22.0 |
| 073_provider_location_coverage | PASS | 35.5 |
| 074_cross_location_patient_moves | PASS | 47.2 |
| 075_sql_vs_api_crosscheck | PASS | 44.6 |
| 076_weekly_schedule_load_balance | PASS | 39.3 |
| 077_data_freshness_report | PASS | 45.0 |
| 078_timezone_safe_daily_census | PASS | 15.9 |
| 079_appointment_to_visit_linkage | PASS | 15.6 |
| 080_enterprise_kpi_pack | PASS | 19.5 |
| 081_reminder_template_render | PASS | 18.0 |
| 082_inbound_comms_triage | PASS | 15.3 |
| 083_file_storage_audit | PASS | 22.0 |
| 084_imaging_metadata_gap_fill | PASS | 18.4 |
| 085_reminder_staleness_sweep | PASS | 23.5 |
| 086_owner_statement_messages | PASS | 18.9 |
| 087_template_deprecation_migration | PASS | 20.0 |
| 088_comms_volume_by_channel | PASS | 21.9 |
| 089_document_expiry_tracker | PASS | 32.4 |
| 090_after_hours_message_log | PASS | 21.8 |
| 091_idempotent_reminder_send | PASS | 19.2 |
| 092_idempotent_occupancy_sync | PASS | 160.6 |
| 093_idempotent_invoice_numbering | PASS | 25.6 |
| 094_idempotent_daily_log_close | PASS | 16.8 |
| 095_seed_integrity_forensics | PASS | 17.6 |
| 096_temporal_anomaly_detection | PASS | 17.9 |
| 097_referential_cascade_delete | PASS | 18.2 |
| 098_negative_balance_underflow | PASS | 19.4 |
| 099_full_state_reconciliation | PASS | 20.7 |
| 100_grand_daily_closeout | PASS | 19.3 |

## Notes on baseline design

- **Random baseline** traffic: logins, `GET /v1/tables`, sampled collection
  reads, and pushes to a scratch `veterinary_clinic_system_junk_probe`
  collection — valid API usage that never touches task-relevant state.
- **Hardcode baseline**: for report tasks, a plausible ops_reports row with a
  stale `batch_code` (`EP-DEADBEEF`) and invented numbers; for mutation tasks, a
  plausible un-derived status flip on the first row of the blast collection.
  Both fail because verifiers recompute expectations from live data + the live
  per-episode nonce.
- Baselines run on a separate container from the gold run so baseline mutations
  cannot contaminate gold-final-state grading.
