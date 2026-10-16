#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ARCHIVE="${1:?usage: $0 <archive.tar.gz>}"
[ -f "$ARCHIVE" ] || { echo "not found: $ARCHIVE"; exit 1; }
tar xzf "$ARCHIVE"
echo "Restored from $ARCHIVE"
