#!/usr/bin/env bash
# Commit with the prompt that produced the change recorded in the message.
#
# The hackathon asks judges to identify what was built during the event, and to show the
# muse-ember usage behind it. A commit message that carries the actual brief is the
# cheapest honest way to do both: `git log` becomes the audit trail.
#
#   tools/commit_with_prompt.sh -s "certify: ..." -p prompts/certify-task.md \
#       [-m "muse-ember-1.0 via Muse Code, 31 calls, \$0.03"] [-t trajectory.json]
#
#   tools/commit_with_prompt.sh -s "app: landing page" -p - <<'EOF'
#   the user's words
#   EOF
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

subject=""; prompt_path=""; meta=""; trajectory=""
while getopts "s:p:m:t:" opt; do
  case $opt in
    s) subject="$OPTARG" ;;
    p) prompt_path="$OPTARG" ;;
    m) meta="$OPTARG" ;;
    t) trajectory="$OPTARG" ;;
    *) echo "bad option" >&2; exit 2 ;;
  esac
done
[ -n "$subject" ] || { echo "usage: $0 -s subject -p promptfile|- [-m meta] [-t trajectory]" >&2; exit 2; }

if [ "$prompt_path" = "-" ]; then
  prompt_text="$(cat)"
  prompt_ref="(given in this commit message)"
elif [ -n "$prompt_path" ]; then
  [ -f "$prompt_path" ] || { echo "no such prompt file: $prompt_path" >&2; exit 2; }
  prompt_text="$(cat "$prompt_path")"
  prompt_ref="$prompt_path"
else
  prompt_text=""
  prompt_ref="(none recorded)"
fi

msg="$subject

Prompt: $prompt_ref"
[ -n "$meta" ] && msg="$msg
Produced by: $meta"
[ -n "$trajectory" ] && msg="$msg
Trajectory: $trajectory"

if [ -n "$prompt_text" ]; then
  msg="$msg

----- prompt -----
$prompt_text
----- end prompt -----"
fi

git -c user.name="${GIT_AUTHOR_NAME:-giveen}" \
    -c user.email="${GIT_AUTHOR_EMAIL:-giveen@users.noreply.github.com}" \
    commit -q -m "$msg"
echo "committed: $(git log --oneline -1)"
