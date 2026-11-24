"""Rewrite a commit message so it carries the brief, never the person's own words.

A commit produced by the assistant used to quote the user's chat verbatim. On a public
repository that publishes a private conversation, so the quoted block is removed and the
message points at where a brief would live instead.
"""
import sys

msg = sys.stdin.read()
marker = "----- prompt -----"
if "Produced by: the assistant" not in msg:
    sys.stdout.write(msg)          # a model's brief stays: that is the point of the record
    raise SystemExit(0)

head = msg.split(marker, 1)[0].rstrip()
lines = [ln for ln in head.splitlines()
         if not ln.startswith("Prompt: (given in this commit message)")]
lines.append("Prompt: none published — this change came from conversation, not from a "
             "model brief.")
lines.append("(Messages produced by a model quote their brief verbatim; conversation is "
             "not published.)")
sys.stdout.write("\n".join(lines).rstrip() + "\n")
