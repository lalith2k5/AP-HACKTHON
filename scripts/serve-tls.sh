#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

command -v caddy >/dev/null 2>&1 || { echo "Install: brew install caddy"; exit 1; }

echo "Starting Caddy on https://localhost:8443 (self-signed)."
echo "Browser will warn once — accept to proceed."
caddy run --config deploy/tls/Caddyfile
