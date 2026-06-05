"""Validate a read-a-book-deeply book workspace.

The validator checks the directory shape required by the skill after a written
deep summary has been produced. It intentionally does not inspect credentials,
upload anything, or call external services.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


IMAGE_LINK_RE = re.compile(
    r"!\[[^\]]*\]\(([^)]+\.(?:jpg|jpeg|png|gif|webp))\)", re.IGNORECASE
)
BARE_IMAGE_RE = re.compile(r"^Image\d+\.(?:jpg|jpeg|png|gif|webp)$", re.IGNORECASE)
REQUIRED_PROMPTS = {
    "agent-a-summarizer.md",
    "agent-b-skeptic.md",
    "b-critiques-a.md",
    "a-responds-b.md",
    "orchestrator-final.md",
}


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def validate_source(book_dir: Path, issues: list[str]) -> None:
    source_dir = book_dir / "source"
    if not source_dir.is_dir():
        add_issue(issues, "Missing source/ directory.")
        return
    source_files = [p for p in source_dir.iterdir() if p.is_file()]
    if not source_files:
        add_issue(issues, "source/ exists but contains no original book file.")


def validate_conversion(book_dir: Path, issues: list[str]) -> None:
    conversion_dir = book_dir / "conversion"
    if not conversion_dir.is_dir():
        add_issue(issues, "Missing conversion/ directory.")
        return

    book_md = conversion_dir / "book.md"
    if not book_md.is_file():
        add_issue(issues, "Missing conversion/book.md.")
    else:
        text = book_md.read_text(encoding="utf-8")
        for raw_link in IMAGE_LINK_RE.findall(text):
            link = raw_link.split("#", 1)[0].split("?", 1)[0]
            target = (conversion_dir / link).resolve()
            try:
                target.relative_to(conversion_dir.resolve())
            except ValueError:
                add_issue(issues, f"Image link escapes conversion/: {raw_link}")
                continue
            if not target.is_file():
                add_issue(issues, f"Markdown image link does not resolve: {raw_link}")

    manifest = conversion_dir / "image_manifest.md"
    if manifest.is_file():
        manifest_text = manifest.read_text(encoding="utf-8")
        if "MISSING" in manifest_text:
            add_issue(issues, "conversion/image_manifest.md contains MISSING entries.")


def validate_top_level(book_dir: Path, issues: list[str]) -> None:
    banned_names = {
        "source.md",
        "source_with_real_images.md",
        "image_manifest.md",
        "structure_ledger.md",
    }
    final_markdown = []

    for child in book_dir.iterdir():
        if child.name in {"source", "conversion"}:
            continue
        if child.is_dir():
            add_issue(issues, f"Unexpected top-level directory: {child.name}")
            continue
        if child.name in banned_names or BARE_IMAGE_RE.match(child.name):
            add_issue(issues, f"Intermediate file left at top level: {child.name}")
        if child.suffix.lower() == ".md" and child.name not in banned_names:
            final_markdown.append(child)

    if not final_markdown:
        add_issue(issues, "No final Markdown summary found at the book directory top level.")
    elif len(final_markdown) > 1:
        names = ", ".join(sorted(p.name for p in final_markdown))
        add_issue(issues, f"Multiple top-level Markdown deliverables found: {names}")


def validate_skill_prompts(skill_dir: Path, issues: list[str]) -> None:
    prompt_dir = skill_dir / "references" / "subagent-prompts"
    if not prompt_dir.is_dir():
        add_issue(issues, "Skill is missing references/subagent-prompts/.")
        return
    present = {p.name for p in prompt_dir.glob("*.md")}
    missing = sorted(REQUIRED_PROMPTS - present)
    if missing:
        add_issue(issues, "Missing subagent prompt templates: " + ", ".join(missing))


def validate(book_dir: Path, skill_dir: Path) -> dict[str, object]:
    issues: list[str] = []
    if not book_dir.is_dir():
        add_issue(issues, f"Book directory does not exist: {book_dir}")
    else:
        validate_source(book_dir, issues)
        validate_conversion(book_dir, issues)
        validate_top_level(book_dir, issues)
    validate_skill_prompts(skill_dir, issues)
    return {
        "book_dir": str(book_dir.resolve()),
        "skill_dir": str(skill_dir.resolve()),
        "ok": not issues,
        "issues": issues,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("book_dir", help="Finished book workspace to validate")
    parser.add_argument(
        "--skill-dir",
        default=str(Path(__file__).resolve().parents[1]),
        help="Path to the read-a-book-deeply skill directory",
    )
    args = parser.parse_args(argv)

    report = validate(Path(args.book_dir), Path(args.skill_dir))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
