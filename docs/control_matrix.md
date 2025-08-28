# Control Matrix

| Control                            | ISO-27001 Clause | Ethiopian Law | Implementation |
|------------------------------------|-----------------|---------------|----------------|
| Access Control                     | A.9             | Art. 26       | RBAC with quarterly recertification exports |
| Data Retention                     | A.18            | Art. 23       | `scripts/purge_expired_records.py` removes aged data |
| Anonymization                      | A.18            | Art. 27       | Background jobs hash or drop PII after retention period |
| Audit Trail Integrity              | A.12            | Art. 25       | `scripts/check_audit_chain.py` verifies tamper-proof logs |
| Encryption and Key Management      | A.10            | Art. 32       | Secrets stored in HashiCorp Vault, keys rotated annually |
