#!/usr/bin/env bash
# Make a self-signed certificate for local HTTPS (issue #10).
# Run from the project folder:  bash scripts/make_cert.sh
set -euo pipefail
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 365 -subj "/CN=localhost"
echo "Wrote cert.pem and key.pem (git-ignored). Start HTTPS with: HTTPS=1 python src/run.py"
