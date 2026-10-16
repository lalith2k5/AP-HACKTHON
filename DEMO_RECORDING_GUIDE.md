# Fallback Demo Recording Guide

Per spec section 22.1: "Have a fallback recording labeled as a recording."

This file is the complete plan for producing and using that recording. It is
deliberately simple. You are not producing a trailer; you are producing
insurance against a broken projector, dead Wi-Fi, or a backend that will not
start.

## Non-negotiable rule

If the recording is shown, it MUST be visibly labeled as a recording. The
spec prohibits passing a recording off as a live run. The demo script has a
disclosure line for this; keep it.

## What you need

- macOS with Screen Recording permission granted to QuickTime (System
  Settings > Privacy & Security > Screen Recording)
- One clean browser profile with no other tabs open
- The app running in Mode A (static key), not OIDC
- Optional: OBS Studio (free) if you want to composite mic audio + a lower
  third label. QuickTime alone is enough for the minimum viable fallback.

## Which tool to use

| Scenario | Tool |
|---|---|
| Simplest, works out of the box | QuickTime Player (built-in) |
| Need to label the recording on-screen | OBS Studio |
| Need to record with mic narration | Either; OBS gives more control |

If you only have 10 minutes, use QuickTime. If you have 45 minutes and want a
polished fallback, use OBS.

---

## Option A — QuickTime (15 minutes total)

### Setup

1. Open Terminal. Start the backend:
       set +H
       cd "$HOME/storesignal-ai"
       ./scripts/run-api.sh

2. Open another Terminal tab. Start the frontend:
       set +H
       cd "$HOME/storesignal-ai/web"
       npm run dev -- --port 3300

3. Open Chrome (not Safari — better for demoing). Sign into a clean profile.
   Navigate to http://localhost:3300

4. Bump browser zoom to 110% (Cmd+Plus twice). Font will read well on any
   projector.

5. Verify the sidebar shows all 11 items. If not, the frontend build is stale
   — run `npm run build` first.

### Record

1. Open QuickTime Player > File > New Screen Recording.
2. Click the dropdown arrow next to the record button. Select your
   microphone if you want narration. Otherwise set to "None".
3. Click Record. Select "Record Selected Portion" and frame the browser
   window (not the whole screen).
4. Walk through the DEMO_SCRIPT.md beats in order. Do not improvise.
5. Stop recording. File > Save. Name it `storesignal_fallback_YYYYMMDD.mov`.
6. Move it to `~/storesignal-ai/demo_recordings/` and add `.gitignore`
   entry so the large file does not get committed.

### Trim

1. File > Trim. Cut the first 2 seconds (you clicking Record) and the last
   2 seconds (you stopping).
2. File > Export As > 1080p. Save alongside the original.

---

## Option B — OBS Studio (45 minutes total)

### Why OBS

You want an on-screen "RECORDING — NOT LIVE" label burned into the video so
no one can mistake it. OBS does this with a single Text source.

### Setup

1. Install: `brew install --cask obs`
2. Open OBS. Skip the auto-configuration wizard (choose "Cancel").
3. Sources panel: add "Display Capture" > your main display.
4. Add "Audio Input Capture" > your microphone.
5. Add "Text (GDI+)" > type "RECORDING — NOT LIVE DEMO". Font size 48.
   Bold. Red text. Bottom-right corner with 40px margin.
6. Settings > Output > Recording:
   - Format: mp4
   - Encoder: Apple VT H264 Hardware
   - Rate control: CBR, bitrate 8000 Kbps
7. Settings > Video: 1920x1080, 30fps.

### Record

Same as QuickTime — walk the beats in order.

### Stop

Stop Recording. File lives in `~/Movies/`. Rename and move as above.

---

## Per-beat recording plan

Match the seven beats in DEMO_SCRIPT.md exactly. Timings are targets, not
requirements.

| Beat | Target time | What is on screen | What you say (short) |
|---|---|---|---|
| 1. Frame | 0:00-0:30 | Sidebar, SIMULATED DATA badge | "This is not a sentiment dashboard. Early warning and incident resolution." |
| 2. Overview | 0:30-1:30 | /overview KPIs + urgent queue, then filter DEL | "40,053 records. Accuracy 0.891. Sorted by policy severity, not volume." |
| 3. Safety boundary | 1:30-3:00 | /alerts filtered to mandatory_policy, then open one, Evidence tab | "One record. One signal. Escalates anyway. This is the safety boundary." |
| 4. Emerging trend | 3:00-4:00 | /trends, categories + anomalies table | "Baseline vs current. Robust z-score. Three seeded incidents, all detected." |
| 5. Assignment and audit | 4:00-5:00 | Incident Actions tab, then /audit | "Change owner, add note, save. Timeline shows it. Audit log is append-only." |
| 6. Regional brief | 5:00-6:00 | /reports | "Executive summary, top five, mandatory-risk section, evidence links." |
| 7. Evaluation honesty | 6:00-6:45 | /data-health | "Hidden-label evaluator. Pipeline re-run takes 27 seconds. We do not run it live." |
| 8. Close | 6:45-7:15 | Sidebar visible | "Safety overrides volume. Every claim has evidence. Runs locally." |

Total: ~7:15. If you go over 7:45, cut Beat 2 shorter.

---

## Pre-record checklist

- [ ] Backend running via `./scripts/run-api.sh` (NOT bare uvicorn)
- [ ] Frontend running on :3300
- [ ] Demo state fresh: POST /api/v1/demo/reset, then re-run pipeline (27s)
- [ ] Browser zoom 110%, one tab, clean profile
- [ ] No Slack/email notifications enabled
- [ ] System Do Not Disturb ON
- [ ] Microphone muted if you are not narrating
- [ ] Recording label visible (OBS only)
- [ ] One full silent rehearsal before recording

---

## Playback plan on demo day

If live demo is impossible:

1. Open the recording in QuickTime or VLC. Set the window to 100% screen
   size. Test the projector/audio output before the session begins.
2. Before pressing play, say clearly:
   "Live demo is not possible due to [reason]. I am showing a recorded
   walkthrough from [date]. It is a recording, not a live run."
3. Press play. Let it run. Do not pause to talk over it unless necessary.
4. After it ends, invite questions. Have DEMO_SCRIPT.md open for reference.
5. If a judge asks to see something live, offer the API docs or a specific
   file in the repo instead.

## Storage and retention

- Recordings live in `~/storesignal-ai/demo_recordings/` (gitignored)
- Keep at least two copies: laptop + one external drive
- Do not commit recordings to the public repo — they may contain
  identifiable demo voices
- Delete old recordings after each hackathon or pilot

## Minimum viable fallback

If you have only 20 minutes of prep: use QuickTime, skip narration, target
6 minutes, and put a text label "RECORDED [date]" on a sticky note stuck to
the projector laptop's screen frame. Ugly but compliant with the spec.

## What not to do

- Do not pass the recording off as live. Spec 22.1 explicitly prohibits this.
- Do not use the recording as evidence of measured results. Spec 22.1 also
  prohibits presenting screenshot values as measured results — show the
  evaluation report if asked.
- Do not record the terminal. Only the browser.
- Do not show real customer or staff data. The system runs on simulated data
  by default; keep it that way for the recording.
