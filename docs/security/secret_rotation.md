# JWT Secret Rotation Runbook

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
   expiry and that the rotation log contains the new secret id.

3. **Deploy application**
   Redeploy services so all instances pick up the updated secret map and
   `JWT_SECRET_ID` value.

4. **Cleanup**
   After all tokens issued with the old key expire, remove the obsolete
   entry from `jwt_secrets.json` and the `JWT_SECRETS` variable.

## Continuous Verification

CI runs `tests/test_jwt_rotation.py` on every push and publishes the
`jwt-rotation.log` artifact so auditors can review recent rotations. To
manually exercise the check:

```bash
pytest tests/test_jwt_rotation.py -k rotate
```
