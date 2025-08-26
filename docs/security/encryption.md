# Encryption at Rest

PostgreSQL Transparent Data Encryption (TDE) or disk-level encryption should be enabled. Store keys in a secrets manager and
rotate them annually using documented procedures. When rotating, generate a new key, re-encrypt data files, and securely
destroy the old key.
