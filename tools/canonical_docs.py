"""Replace the provenance document with its canonical wording in every commit in a rewrite."""
from pathlib import Path

canonical = Path("/mnt/storage/Projects/rote/tools/PROMPTS.canonical.md").read_text()


def apply() -> None:
    target = Path("PROMPTS.md")
    if target.exists() and target.read_text(encoding="utf-8") != canonical:
        target.write_text(canonical, encoding="utf-8")


if __name__ == "__main__":
    apply()
