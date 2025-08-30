#!/bin/bash
# Install local tooling required for security and accessibility checks.
set -euo pipefail

apt-get update
apt-get install -y curl nodejs npm chromium \
  libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libnss3 \
  libasound2t64 libx11-xcb1 libxss1 libgdk-pixbuf2.0-0 libxshmfence1 libdrm2

npm install -g pa11y

# Install gitleaks
curl -sSfL https://github.com/gitleaks/gitleaks/releases/download/v8.28.0/gitleaks_8.28.0_linux_x64.tar.gz \
  | tar xz -C /usr/local/bin gitleaks

# Install Trivy (vulnerability scanner)
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
  | sh -s -- -b /usr/local/bin

# Install kube-linter
curl -sSfL https://github.com/stackrox/kube-linter/releases/download/v0.7.5/kube-linter-linux.tar.gz \
  | tar xz -C /usr/local/bin kube-linter

# Install kube-score
curl -sSfL https://github.com/zegl/kube-score/releases/download/v1.20.0/kube-score_1.20.0_linux_amd64.tar.gz \
  | tar xz -C /usr/local/bin kube-score

pip install --break-system-packages "typer[all]==0.16.1" python-owasp-zap-v2.4 playwright pyyaml

playwright install --with-deps chromium

curl -sSfL https://raw.githubusercontent.com/zaproxy/zaproxy/main/docker/zap-baseline.py \
  -o /usr/local/bin/zap-baseline.py
curl -sSfL https://raw.githubusercontent.com/zaproxy/zaproxy/main/docker/zap_common.py \
  -o /usr/local/bin/zap_common.py
chmod +x /usr/local/bin/zap-baseline.py /usr/local/bin/zap_common.py
