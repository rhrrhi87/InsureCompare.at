#!/usr/bin/env bash
# File: nginx/generate-dev-certs.sh
# Generates a self-signed TLS certificate for local docker-compose runs.
#
# Usage:
#     ./nginx/generate-dev-certs.sh
#
# In production, replace the contents of nginx/certs/ with certificates from
# Let's Encrypt or your CA of choice.

set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")" && pwd)/certs"
mkdir -p "${CERT_DIR}"

if [[ -f "${CERT_DIR}/fullchain.pem" && -f "${CERT_DIR}/privkey.pem" ]]; then
  echo "Certificates already exist in ${CERT_DIR}; skipping."
  exit 0
fi

openssl req -x509 -nodes \
  -newkey rsa:4096 \
  -keyout "${CERT_DIR}/privkey.pem" \
  -out "${CERT_DIR}/fullchain.pem" \
  -days 365 \
  -subj "/C=AT/ST=Vienna/L=Vienna/O=InsureCompare.at/OU=Dev/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:app.insurecompare.local,IP:127.0.0.1"

chmod 644 "${CERT_DIR}/fullchain.pem"
chmod 600 "${CERT_DIR}/privkey.pem"
echo "Self-signed dev certificates written to ${CERT_DIR}"
