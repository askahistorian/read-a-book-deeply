"""Convert a book with MarkItDown and make EPUB images agent-readable.

Usage:
    python scripts/convert_book_with_assets.py "source/book.epub" "conversion"

The script intentionally uses only the Python standard library. It delegates
text conversion to the installed `markitdown` CLI, then repairs the common EPUB
case where Markdown contains image placeholders such as `Image00004.jpg` but
the image files were not written next to the Markdown.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
IMAGE_LINK_RE = re.compile(
    r"!\[([^\]]*)\]\(([^)]+\.(?:jpg|jpeg|png|gif|webp))\)", re.IGNORECASE
)


@dataclass
class ConversionReport:
    input_file: str
    output_dir: str
    markdown_file: str
    fixed_markdown_file: str
    book_file: str
    image_dir: str
    extracted_images: int
    linked_images: int
    missing_links: list[str]


def run_markitdown(input_file: Path, output_md: Path) -> None:
    cmd = ["markitdown", str(input_file), "-o", str(output_md)]
    completed = subprocess.run(cmd, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "markitdown failed\n"
            f"command: {' '.join(cmd)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )


def extract_epub_images(epub_file: Path, image_dir: Path) -> set[str]:
    extracted: set[str] = set()
    if epub_file.suffix.lower() != ".epub":
        return extracted

    image_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(epub_file) as zf:
        for info in zf.infolist():
            source_name = Path(info.filename).name
            if not source_name:
                continue
            if Path(source_name).suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            target = image_dir / source_name
            with zf.open(info) as src, target.open("wb") as dst:
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
            extracted.add(source_name)

    return extracted


def repair_markdown_image_links(source_md: Path, fixed_md: Path) -> tuple[set[str], list[str]]:
    text = source_md.read_text(encoding="utf-8")
    linked: set[str] = set()
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        alt = match.group(1)
        raw_path = match.group(2)
        image_name = Path(raw_path).name
        linked.add(image_name)
        return f"![{alt}](images/{image_name})"

    fixed_text = IMAGE_LINK_RE.sub(replace, text)
    fixed_md.write_text(fixed_text, encoding="utf-8")

    image_dir = fixed_md.parent / "images"
    existing_lower = {p.name.lower() for p in image_dir.glob("*")}
    for image_name in sorted(linked):
        if image_name.lower() not in existing_lower:
            missing.append(image_name)

    return linked, missing


def write_manifest(
    manifest_file: Path,
    extracted_names: set[str],
    linked_names: set[str],
    missing_links: list[str],
) -> None:
    lines = [
        "# Image Asset Manifest",
        "",
        f"- Extracted images: {len(extracted_names)}",
        f"- Linked images in Markdown: {len(linked_names)}",
        f"- Missing linked images: {len(missing_links)}",
        "",
        "## Linked Images",
        "",
    ]
    extracted_lower = {name.lower() for name in extracted_names}
    for name in sorted(linked_names):
        status = "OK" if name.lower() in extracted_lower else "MISSING"
        lines.append(f"- `{name}` -> `images/{name}` [{status}]")

    linked_lower = {name.lower() for name in linked_names}
    unlinked = sorted(name for name in extracted_names if name.lower() not in linked_lower)
    if unlinked:
        lines += ["", "## Extracted But Not Linked", ""]
        for name in unlinked:
            lines.append(f"- `images/{name}`")

    if missing_links:
        lines += ["", "## Missing Links", ""]
        for name in missing_links:
            lines.append(f"- `{name}`")

    manifest_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def convert_book(input_path: Path, output_dir: Path, skip_convert: bool = False) -> ConversionReport:
    input_path = input_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_md = output_dir / "source.md"
    fixed_md = output_dir / "book.md"
    image_dir = output_dir / "images"

    if not skip_convert or not source_md.exists():
        run_markitdown(input_path, source_md)

    extracted_names = extract_epub_images(input_path, image_dir)
    linked_names, missing_links = repair_markdown_image_links(source_md, fixed_md)
    write_manifest(output_dir / "image_manifest.md", extracted_names, linked_names, missing_links)

    if linked_names and missing_links:
        raise RuntimeError(
            "Some Markdown image links still do not resolve: " + ", ".join(missing_links)
        )

    return ConversionReport(
        input_file=str(input_path),
        output_dir=str(output_dir.resolve()),
        markdown_file=str(source_md.resolve()),
        fixed_markdown_file=str(fixed_md.resolve()),
        book_file=str(fixed_md.resolve()),
        image_dir=str(image_dir.resolve()),
        extracted_images=len(extracted_names),
        linked_images=len(linked_names),
        missing_links=missing_links,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Book file, usually EPUB/PDF/DOCX")
    parser.add_argument("output_dir", help="Book output directory")
    parser.add_argument(
        "--skip-convert",
        action="store_true",
        help="Reuse output_dir/source.md and only repair/extract assets.",
    )
    args = parser.parse_args(argv)

    report = convert_book(Path(args.input_file), Path(args.output_dir), args.skip_convert)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
