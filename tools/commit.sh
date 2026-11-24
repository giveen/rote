#!/usr/bin/env bash
# Commit with the prompt it came from, in the form asked for:
#
#   tools/commit.sh -s "certify: HTML certificate for a run" \
#                   -p "add rote certify — a self-contained HTML certificate for a run" \
#                   -m "muse-ember-1.0 via Muse Code, 31 calls, \$0.03"
#
# The prompt is ONE line. Long briefs stay in prompts/ and are referred to in the body, never
# pasted: the log is a log. There is no way to pass a conversation transcript through this
# tool, which is deliberate.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

subject=""; prompt=""; meta=""
while getopts "s:p:m:" opt; do
  case $opt in
    s) subject="$OPTARG" ;;
    p) prompt="$OPTARG" ;;
    m) meta="$OPTARG" ;;
    *) echo "bad option" >&2; exit 2 ;;
  esac
done
[ -n "$subject" ] || { echo "usage: $0 -s subject -p \"one line prompt\" [-m meta]" >&2; exit 2; }
[ -n "$prompt" ] || { echo "a commit needs the prompt it came from (-p)" >&2; exit 2; }
case "$prompt" in
  *$'\n'*) echo "the prompt must be one line" >&2; exit 2 ;;
esac

msg="$subject

Prompt to Muse: \"$prompt\""
[ -n "$meta" ] && msg="$msg

Built by: $meta"

git -c user.name="${GIT_AUTHOR_NAME:-giveen}" \
    -c user.email="${GIT_AUTHOR_EMAIL:-giveen@users.noreply.github.com}" \
    commit -q -m "$msg"
echo "committed: $(git log --oneline -1)"
