#!/usr/bin/env bash
# Build exactly the files the submission form asks for, in one folder.
#
#   tools/submission_files.sh   →  submission-upload/
#
# The form takes an image (≤10 MB, up to 10), and for Muse Code a JSON export (≤10 MB). The
# repository keeps that trajectory gzipped to stay light, so it is expanded here — the upload
# field wants .json, not .json.gz.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

OUT=submission-upload
rm -rf "$OUT"; mkdir -p "$OUT"

# 1. The usage dashboard screenshot the form asks for.
# Kept outside results/submission/ because that folder is rebuilt from a fresh run.
shot=$(ls -1 results/usage/*.png results/submission/usage-*.png 2>/dev/null | tail -1 || true)
if [ -n "$shot" ]; then
  cp "$shot" "$OUT/usage-dashboard.png"
  echo "usage screenshot   → $OUT/usage-dashboard.png ($(du -h "$shot" | cut -f1))"
else
  echo "usage screenshot   → MISSING: capture dev.meta.ai/usage for Nov 23 – Dec 2 first"
fi

# 2. The Muse Code trajectory, uncompressed.
if [ -f prompts/muse-code-trajectory.json.gz ]; then
  gunzip -c prompts/muse-code-trajectory.json.gz > "$OUT/muse-code-trajectory.json"
  size=$(stat -c%s "$OUT/muse-code-trajectory.json")
  echo "trajectory         → $OUT/muse-code-trajectory.json ($((size/1024/1024)) MB, limit 10 MB)"
else
  echo "trajectory         → MISSING: prompts/muse-code-trajectory.json.gz not found"
fi

# 3. The written answers, ready to paste.
cat > "$OUT/answers.md" <<'TXT'
# Submission answers, ready to paste

Each written field on the form caps at 3,000 characters. Drafts below are well inside that.

## Project Description (3,000 max)

rote turns one screen recording of a repetitive web task into automation that proves itself.

Every team has a chore nobody automates, because writing the automation costs more than doing
the task: copying rows from a spreadsheet into a web form, checking out a purchase, onboarding
a supplier. rote watches someone do it once — an ordinary screen recording — and works out the
procedure: the fields, their order, and the one block that repeats per row of data.

Then it does something the usual "AI writes a script" demo does not: it runs the automation in
a real browser against data that was never in the recording, and lets the app's own state decide
whether it worked. Failing plans go back to Muse Ember with the app's real controls as evidence,
and it repairs the plan — not the code.

The model's job is deliberately small. Muse Ember reads the recording and returns a plan of
fields, actions and one repeating range. A compiler turns that plan into ~70 lines of readable
Playwright. Nothing about the running automation is AI: once proven, no model is called again.

Four tasks across four apps cost 9 model calls and about two and a half cents.

## Describe your use of Meta products (3,000 max)

Everything is built on Muse Ember through the Meta Model API.

- Reading the recording: one call per task, effort "max", strict JSON schema output. An hour of
  screen recording bills at roughly 170 input tokens, so the reading is effectively free.
- Repairing a wrong plan: when the replay disagrees, the failure evidence plus the app's live
  control inventory (labels, buttons, aria-labels, dropdown options, input types) goes back to
  Muse Ember, which returns a corrected plan. The loop keeps a memory of earlier attempts so it
  cannot undo a fix.
- Cost engineering: a stable instruction block sits in the cached prefix (25x cheaper than
  uncached input), and reasoning effort cascades from minimal upward, so a task that is right
  first time never pays for the expensive tiers.
- Muse Code built part of the product: `rote/certify.py` and its tests were written by
  muse-ember-1.0 through Muse Code. The session export is included, and every commit carries the
  prompt it came from.

Every call is metered in a ledger, and the submission's trace.md lists each call's tokens and
cost from the API's own usage object.

## Why are Meta's models important to your solution? (3,000 max)

The economics are the product. rote has to read a video, and video understanding at frontier
prices makes the idea pointless: a three-minute recording would cost more than the task it
describes. Muse Ember reads a recording for about a tenth of a cent, so "just record yourself
doing it" becomes a reasonable thing to ask someone.

Cheap tokens also make the repair loop affordable. The honest version of this system fails
often — first plans are wrong — and recovering means paying for another call. At Ember prices a
retry costs a fraction of a cent, so the architecture can afford to be honest instead of
pretending the first answer was right.

Cheapness makes the small-model route viable for another reason: the model never writes code.
It returns a short plan, which a compiler turns into a script and a browser tests. That division
is what lets a model at this price do a job people usually reach for a flagship model to do.
TXT

echo "answers            → $OUT/answers.md"
echo
echo "Upload: usage-dashboard.png, muse-code-trajectory.json"
echo "Paste:  team id 1857589511891749, repo https://github.com/giveen/rote, video link, answers.md"
