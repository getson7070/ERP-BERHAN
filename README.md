# ERP-BERHAN
BERHAN PHARMA

## Configuration

Set the following environment variables before running the application:

- `SECRET_KEY` – Flask session secret.
- `FERNET_KEY` – key for data encryption.
- `DATABASE_URL` – path to the SQLite database file.

## Two-Factor Authentication

Both employees and clients must enroll a Time-based One-Time Password (TOTP).
After password authentication, scan the provided QR code and confirm the code to
enable 2FA for future logins.
