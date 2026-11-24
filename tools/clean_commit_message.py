"""Rewrite a commit message to the narrow record: what changed, and who wrote it.

Removes any block that quotes a conversation or inlines a brief. A model-built commit keeps a
`Built-with:` trailer and a pointer to the brief file; nothing else is added to the log.
"""
import sys

msg = sys.stdin.read()
cut = msg.find("----- prompt -----")
if cut != -1:
    msg = msg[:cut]

lines = []
for line in msg.splitlines():
    if line.startswith(("Prompt:", "(Messages produced", "(conversation, not published)",
                        "Produced by: the assistant")):
        continue
    if line.startswith("Produced by: "):
        line = "Built-with: " + line.split("Produced by: ", 1)[1]
    lines.append(line)

while lines and not lines[-1].strip():
    lines.pop()
sys.stdout.write("\n".join(lines).rstrip() + "\n")
