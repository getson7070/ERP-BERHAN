#!/usr/bin/env python3
import os, secrets
new_secret = secrets.token_urlsafe(48)
print(new_secret)
# Persisting the secret is environment/platform specific; set this in Render env.
