"""Put the provenance document back to its canonical wording in every rewritten commit.

Used once, during the history rewrite, so older commits carry the current wording instead of
the first draft. Kept for reproducibility: it reads PROMPTS.md from the working tree, so it
does not depend on a duplicate copy that could drift.
"""
from pathlib import Path

CANONICAL = Path("/mnt/storage/Projects/rote/PROMPTS.md")


def apply() -> None:
    target = Path("PROMPTS.md")
    if CANONICAL.exists() and target.exists():
        text = CANONICAL.read_text(encoding="utf-8")
        if target.read_text(encoding="utf-8") != text:
            target.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    apply()
