# GPG Commit Signing

This guide documents how to create and use a GPG key for signing commits in the ERP-BERHAN repository.

## Generate a Key

```bash
gpg --batch --gen-key <<'EOK'
%no-protection
Key-Type: RSA
Key-Length: 3072
Subkey-Type: RSA
Subkey-Length: 3072
Name-Real: getson7070
Name-Email: getson7070@example.com
Expire-Date: 0
%commit
EOK
```

## Configure Git

```bash
git config user.name "getson7070"
git config user.email "getson7070@example.com"
git config user.signingkey <KEY_ID>
git config commit.gpgsign true
```

## Verify Signatures

Use `git log --show-signature -1` to verify the latest commit. CI workflows also enforce signature validity.

Keep private keys secure and rotate them if compromised.
