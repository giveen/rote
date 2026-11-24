#!/usr/bin/env bash
# Commit, recording which model wrote the code — and nothing about the conversation.
#
#   tools/commit.sh -s "certify: HTML certificate for a run" \
#                   -b prompts/certify-task.md \
#                   -m "muse-ember-1.0 via Muse Code (31 calls, 96% cached, \$0.03)"
#
# -b references a brief file that is committed in prompts/. The file is NOT pasted into the
# message: the log stays readable and the evidence lives where it belongs. There is
# deliberately no way to pass free text, so a private conversation cannot end up in a public
# repository through this tool.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

subject=""; brief=""; meta=""
while getopts "s:b:m:" opt; do
  case $opt in
    s) subject="$OPTARG" ;;
    b) brief="$OPTARG" ;;
    m) meta="$OPTARG" ;;
    *) echo "bad option" >&2; exit 2 ;;
  esac
done
[ -n "$subject" ] || { echo "usage: $0 -s subject [-b brieffile] [-m model-and-cost]" >&2; exit 2; }

if [ -n "$brief" ]; then
  [ -f "$brief" ] || { echo "no such brief: $brief" >&2; exit 2; }
  case "$brief" in
    prompts/*) : ;;
    *) echo "a brief must live in prompts/ so the record stays in one place" >&2; exit 2 ;;
  esac
fi

msg="$subject"
if [ -n "$meta" ]; then
  msg="$msg

Built-with: $meta"
fi
[ -n "$brief" ] && msg="$msg
Brief: $brief"

git -c user.name="${GIT_AUTHOR_NAME:-giveen}" \
    -c user.email="${GIT_AUTHOR_EMAIL:-giveen@users.noreply.github.com}" \
    commit -q -m "$msg"
echo "committed: $(git log --oneline -1)"
