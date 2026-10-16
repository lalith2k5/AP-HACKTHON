#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT="backups/storesignal-$TS.tar.gz"
mkdir -p backups
tar czf "$OUT" \
  config/ \
  data/reference/ \
  data/processed/*.jsonl \
  models/ \
  data/evaluation/ 2>/dev/null || true
echo "Backup: $OUT"
ls -lh "$OUT"
