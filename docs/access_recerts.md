# Access Recertification

Periodic access reviews ensure least-privilege access across tenants. Administrators should:

1. Quarterly, export active users per organization.
2. Confirm each role and permission is still required.
3. Remove or downgrade accounts that are unused for 90 days.
4. Log recertification results in the audit log for traceability.

Automating these steps via scheduled tasks is recommended; see `docs/automation_analytics.md` for guidance on Celery jobs.
