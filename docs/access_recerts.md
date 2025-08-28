# Access Recertification

Periodic access reviews ensure least-privilege access across tenants. Administrators should:

1. Quarterly, export active users per organization.
2. Confirm each role and permission is still required.
3. Remove or downgrade accounts that are unused for 90 days.
4. Log recertification results in the audit log for traceability.

Use `scripts/access_recert_export.py` to generate an immutable (read-only) CSV
export of current assignments. Store exports in WORM-capable storage such as S3
Object Lock for tamper evidence. The latest automated export is available as a
[CI artifact](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain).

Automating these steps via scheduled tasks is recommended; see `docs/automation_analytics.md` for guidance on Celery jobs.

The `data_retention.export_access_recert` Celery task runs automatically on the first day of each quarter at 05:00 UTC via Celery beat and writes the CSV export to write-once storage.

The latest quarterly export is published as a CI artifact named `access-recert-export` on the [main workflow](https://github.com/getson7070/ERP-BERHAN/actions/workflows/ci.yml?query=branch%3Amain).
