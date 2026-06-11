"""Validate multi-book subagent artifacts for corruption and contract shape.

The validator is intentionally conservative. It does not judge summary quality;
it only blocks artifacts that are unsafe to pass into the multi-book
orchestrator because they look like streamed cumulative snapshots, partial
outputs, wrong-run outputs, or malformed role outputs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SENTINEL_FIELDS = ("run_id", "book_id", "agent_id", "attempt_id")
COMMON_REQUIRED_SECTIONS = {
    "agent_a_structured_material": (
        "structure_coverage_ledger",
        "content_synthesis_notes",
        "interpretation_boundary_notes",
        "final_summary_building_blocks",
    ),
    "agent_b_structured_risk": (
        "coverage_risk_register",
        "fidelity_risk_register",
        "genre_specific_risk_notes",
        "must_not_miss_register",
    ),
    "orchestrator_single_book_multibook": (
        "原书内容",
        "总结",
    ),
}


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def parse_sentinels(text: str) -> dict[str, str]:
    sentinels: dict[str, str] = {}
    for raw_line in text.splitlines()[:40]:
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in {*SENTINEL_FIELDS, "artifact_role"}:
            sentinels[key] = value
    return sentinels


def repeated_heading_issues(text: str) -> list[str]:
    issues: list[str] = []
    positions_by_heading: dict[str, list[int]] = {}
    for match in HEADING_RE.finditer(text):
        normalized = match.group(2).strip().lower()
        positions_by_heading.setdefault(normalized, []).append(match.start())

    for heading, positions in sorted(positions_by_heading.items()):
        if len(positions) > 2:
            issues.append(
                f"Heading appears more than twice: {heading!r} ({len(positions)} times)."
            )
        if len(positions) >= 4:
            gaps = [right - left for left, right in zip(positions, positions[1:])]
            if all(right > left for left, right in zip(gaps, gaps[1:])):
                issues.append(
                    f"Heading positions show increasing prefix-copy spacing: {heading!r}."
                )
    return issues


def unique_line_ratio(text: str) -> float:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 0.0
    return len(set(lines)) / len(lines)


def validate_text(
    text: str,
    *,
    expected_run_id: str | None = None,
    expected_book_id: str | None = None,
    expected_agent_id: str | None = None,
    expected_attempt_id: str | None = None,
    expected_role: str | None = None,
    min_chars: int = 200,
) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []

    if len(text.strip()) < min_chars:
        add_issue(issues, f"Artifact is too short: {len(text.strip())} chars.")

    sentinels = parse_sentinels(text)
    expected_values = {
        "run_id": expected_run_id,
        "book_id": expected_book_id,
        "agent_id": expected_agent_id,
        "attempt_id": expected_attempt_id,
        "artifact_role": expected_role,
    }
    for field, expected_value in expected_values.items():
        if expected_value is None:
            continue
        actual_value = sentinels.get(field)
        if actual_value != expected_value:
            add_issue(
                issues,
                f"Sentinel mismatch for {field}: expected {expected_value!r}, got {actual_value!r}.",
            )

    if expected_role is not None:
        for section in COMMON_REQUIRED_SECTIONS.get(expected_role, ()):
            if section not in text:
                add_issue(issues, f"Missing required section marker: {section}")

    ratio = unique_line_ratio(text)
    if len(text) > 2000 and ratio < 0.18:
        add_issue(issues, f"Unique-line ratio is too low: {ratio:.3f}.")
    elif len(text) > 2000 and ratio < 0.28:
        warnings.append(f"Unique-line ratio is low: {ratio:.3f}.")

    issues.extend(repeated_heading_issues(text))

    return {
        "ok": not issues,
        "issues": issues,
        "warnings": warnings,
        "sentinels": sentinels,
        "stats": {
            "chars": len(text),
            "lines": len(text.splitlines()),
            "unique_line_ratio": ratio,
        },
    }


def validate_file(path: Path, **kwargs: Any) -> dict[str, Any]:
    issues: list[str] = []
    if not path.is_file():
        add_issue(issues, f"Artifact does not exist: {path}")
        return {
            "artifact": str(path),
            "ok": False,
            "issues": issues,
            "warnings": [],
            "sentinels": {},
            "stats": {"chars": 0, "lines": 0, "unique_line_ratio": 0.0},
        }
    result = validate_text(path.read_text(encoding="utf-8"), **kwargs)
    result["artifact"] = str(path.resolve())
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", help="Artifact file to validate")
    parser.add_argument("--run-id")
    parser.add_argument("--book-id")
    parser.add_argument("--agent-id")
    parser.add_argument("--attempt-id")
    parser.add_argument("--role")
    parser.add_argument("--min-chars", type=int, default=200)
    args = parser.parse_args(argv)

    report = validate_file(
        Path(args.artifact),
        expected_run_id=args.run_id,
        expected_book_id=args.book_id,
        expected_agent_id=args.agent_id,
        expected_attempt_id=args.attempt_id,
        expected_role=args.role,
        min_chars=args.min_chars,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
