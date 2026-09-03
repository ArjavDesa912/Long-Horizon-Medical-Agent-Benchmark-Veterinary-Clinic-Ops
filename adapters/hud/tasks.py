"""Tasks for veterinary-clinic-system — run with: hud eval tasks.py <agent>

Only the 10 open tasks (full gold.py + verifier.py shipped in this sample)
are listed. The env.py adapter binds one HUD task template per task_id, named
by the task's slug (task_id with the leading zero-padded number stripped).
"""

from env import (
    overdue_vaccine_compliance_flag,
    rabies_booster_due_recompute,
    vaccination_reminder_batch,
    boarding_checkin_flow,
    ar_aging_report,
    draft_invoice_purge,
    double_booking_repair,
    new_patient_enrollment,
    enterprise_kpi_pack,
    idempotent_reminder_send,
)

tasks = [
    overdue_vaccine_compliance_flag(),
    rabies_booster_due_recompute(),
    vaccination_reminder_batch(),
    boarding_checkin_flow(),
    ar_aging_report(),
    draft_invoice_purge(),
    double_booking_repair(),
    new_patient_enrollment(),
    enterprise_kpi_pack(),
    idempotent_reminder_send(),
]
