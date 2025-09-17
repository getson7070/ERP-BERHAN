# Secret Rotation Runbook

This document outlines rotation procedures for encryption-related secrets.

## JWT Secret Rotation

JWT secrets are versioned using a `JWT_SECRETS` map and the active key is
selected via `JWT_SECRET_ID`.  Secrets are loaded from a vault file or
environment variables through `erp.secrets.get_secret`.

1. **Prepare new secret**
   ```bash
   ./scripts/rotate_jwt_secret.py
   ```
   The script appends a new random key to `jwt_secrets.json`, flips
   `JWT_SECRET_ID` and records the rotation in `logs/jwt_rotation.log`.
   The unit test `tests/test_jwt_rotation.py` verifies these artefacts.

2. **Validate in CI**
   ```bash
   pytest tests/test_jwt_rotation.py
   ```
   The test ensures tokens signed with the previous key remain valid until
   expiry, the rotation log contains the new secret id, and the rotation
   script updates the secrets file safely.

3. **Deploy application**
   Redeploy services so all instances pick up the updated secret map and
   `JWT_SECRET_ID` value.
4. **Cleanup**
   After all tokens issued with the old key expire, remove the obsolete
   entry from `jwt_secrets.json` and the `JWT_SECRETS` variable.

## Fernet Encryption Key Rotation

`FERNET_KEY` secures tokens and other sensitive fields.  The key is stored in
the secret vault and referenced by the application via `erp.security`.

1. **Generate new key**
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Store the printed value as the new `FERNET_KEY` in the secret manager.

2. **Deploy application**
   Restart or redeploy all services so the new key is loaded.  All encrypted
   data should be re-encrypted using the new key as part of the deployment
   process.

3. **Cleanup**
   Remove the old key from the secret store once all data has been re-encrypted
   and verified.

## Continuous Verification

CI runs `tests/test_jwt_rotation.py` on every push and publishes the
`jwt-rotation.log` artifact so auditors can review recent rotations. To
manually exercise the check:

```bash
pytest tests/test_jwt_rotation.py -k rotate
```


## Centralized Secret Rotation via AWS Secrets Manager

To improve security, secrets should be stored and rotated using a managed Key Management Service (KMS) or Secrets Manager rather than local files.

1. **Create a secret** in AWS Secrets Manager for JWT signing keys with automatic rotation enabled. Choose a rotation interval (e.g., 30 days) and configure a rotation Lambda that generates a new signing key and updates the `JWT_SECRET_ID` version.
2. **Update application configuration** to fetch secrets at startup using the AWS SDK (e.g., `boto3`). The helper in `erp/secrets.py` should call `secretsmanager.get_secret_value()` and cache the active secret.
3. **Enable expiration alerts** with CloudWatch Events or EventBridge to notify operations before a secret version expires. Alerts should route to the on‑call channel (e.g., PagerDuty/Slack).
4. **Enforce pre‑commit hooks** to block commits containing hard‑coded secrets or AWS ARNs. The `.pre-commit-config.yaml` includes secret scanning hooks such as `detect-secrets`.

The rotation Lambda and associated EventBridge rules should be managed via infrastructure‑as‑code and validated in CI. Removing plaintext secrets from the repository and delegating rotation to AWS ensures auditability and reduces the risk of credential leaks.
