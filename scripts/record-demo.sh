#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
WEB="$ROOT/web"
OUT="$ROOT/demo_recordings"
mkdir -p "$OUT"

say() { printf "\033[1;36m> \033[0m%s\n" "$*"; }
ok()  { printf "\033[1;32mOK \033[0m%s\n" "$*"; }
err() { printf "\033[1;31m!! \033[0m%s\n" "$*" >&2; }

if ! curl -sf http://localhost:8790/health >/dev/null 2>&1; then
  say "Backend down - starting"
  lsof -ti:8790 | xargs kill -9 2>/dev/null || true
  nohup ./scripts/run-api.sh > /tmp/storesignal-api.log 2>&1 &
  for i in {1..20}; do
    if curl -sf http://localhost:8790/health >/dev/null 2>&1; then break; fi
    sleep 0.5
  done
  curl -sf http://localhost:8790/health >/dev/null 2>&1 || { err "backend failed"; exit 1; }
  ok "backend up"
else
  ok "backend already up"
fi

if ! curl -sf -o /dev/null http://localhost:3300/ 2>/dev/null; then
  say "Frontend down - starting"
  lsof -ti:3300 | xargs kill -9 2>/dev/null || true
  ( cd "$WEB" && nohup npm run dev -- --port 3300 > /tmp/storesignal-web.log 2>&1 & )
  for i in {1..40}; do
    if curl -sf -o /dev/null http://localhost:3300/ 2>/dev/null; then break; fi
    sleep 0.5
  done
  curl -sf -o /dev/null http://localhost:3300/ 2>/dev/null || { err "frontend failed"; exit 1; }
  ok "frontend up"
else
  ok "frontend already up"
fi

HAVE_FFMPEG=0
command -v ffmpeg >/dev/null 2>&1 && HAVE_FFMPEG=1
if [ "$HAVE_FFMPEG" = "0" ]; then
  say "ffmpeg not installed - webm only (brew install ffmpeg for mp4)"
fi

cd "$WEB"
rm -rf test-results
say "Recording headless walkthrough (~70s) - do not touch anything"
RECORD_DEMO=1 npx playwright test e2e/demo-walkthrough.spec.ts --reporter=line || {
  err "Playwright failed - see web/test-results/"
  exit 1
}

VIDEO=$(find test-results -name "video.webm" -type f 2>/dev/null | head -1 || true)
[ -z "$VIDEO" ] && { err "no video produced"; exit 1; }

STAMP=$(date +%Y%m%d_%H%M%S)
DEST="$OUT/storesignal_demo_${STAMP}.webm"
cp "$VIDEO" "$DEST"
ok "webm: $DEST"

FINAL="$DEST"
if [ "$HAVE_FFMPEG" = "1" ]; then
  say "Converting to mp4"
  MP4="${DEST%.webm}.mp4"
  if ffmpeg -i "$DEST" -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -movflags +faststart "$MP4" -y >/dev/null 2>&1; then
    ok "mp4:  $MP4"
    FINAL="$MP4"
  else
    err "ffmpeg failed - keeping webm"
  fi
fi

say "Opening the video"
open "$FINAL" 2>/dev/null || true

echo
ok "Done"
echo "  File:   $FINAL"
echo "  Size:   $(du -h "$FINAL" | cut -f1)"
echo "  Folder: $(dirname "$FINAL")"
