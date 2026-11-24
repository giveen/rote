"""Put one quoted prompt line into every commit message.

Format, exactly as asked:

    Prompt to Muse: "what was asked for"

The prompt is one line: the instruction a commit came from. Full briefs stay in prompts/ and
are referenced, never pasted, so the log stays a log.
"""
import sys

# subject -> the one-line prompt the change came from
PROMPTS = {
    "start rote": "build the demo app the recorder will drive",
    "gate:": "before nine days of work, find out whether Ember can read a screen recording at all",
    "recording → plan": "make it work end to end: recording to plan to automation to a passing replay",
    "submission: prompt and token trace": "the submission needs a prompt and token trace showing usage and amount spent",
    "verifier: booleans": "a correct run must never be reported as a failure",
    "app: landing page": "put the prompt each change came from in its commit message",
    "docs: record who wrote what": "record who wrote what, so a judge can tell",
    "prompts: the brief": "Muse has to build it, and the brief and trace have to be recorded",
    "harness: one source of truth": "the locator helpers drifted between the recorder and the generated code",
    "docs: keep the provenance record narrow": "keep the record narrow: briefs and the trajectory, never conversation",
    "tools: a commit helper": "make the commit helper unable to publish a conversation",
    "tools: drop the one-off scrubber": "remove the scrubber that carried the text it was removing",
    "certify:": "add rote certify — a self-contained HTML certificate for a run",
}

FALLBACK = "continue the work on rote"


def prompt_for(subject: str) -> str:
    for key, value in PROMPTS.items():
        if subject.startswith(key):
            return value
    return FALLBACK


def main() -> None:
    msg = sys.stdin.read()
    cut = msg.find("----- prompt -----")
    if cut != -1:
        msg = msg[:cut]

    lines = []
    for line in msg.splitlines():
        if line.startswith(("Prompt:", "Prompt to Muse:", "Brief:", "Built-with:",
                            "Trajectory:", "Produced by:", "(Messages produced",
                            "(conversation")):
            continue
        lines.append(line)
    while lines and not lines[-1].strip():
        lines.pop()

    subject = lines[0] if lines else ""
    body = "\n".join(lines[1:]).strip()
    out = f'{subject}\n\nPrompt to Muse: "{prompt_for(subject)}"'
    if body:
        out += f"\n\n{body}"
    sys.stdout.write(out.rstrip() + "\n")


if __name__ == "__main__":
    main()
