"""Checkpoint helpers for read-a-book-deeply workspaces.

The module owns the checkpoint field names, phase enums, minimal YAML parser,
and atomic write helper used by the validators. It intentionally supports only
the simple YAML subset used by this skill's checkpoint files.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CHECKPOINT_VERSION = 1
SINGLE_CHECKPOINT_RELATIVE_PATH = Path("conversion") / "checkpoint.yaml"
COLLECTION_MANIFEST_NAME = "collection_manifest.yaml"
COLLECTION_RESUME_FIELD = "resume"
SINGLE_CHECKPOINT_KIND = "single_book"
COLLECTION_CHECKPOINT_KIND = "collection"
VALID_CHECKPOINT_KINDS = {SINGLE_CHECKPOINT_KIND, COLLECTION_CHECKPOINT_KIND}
VALID_PHASES = {
    "initialized",
    "source_prepared",
    "converted",
    "image_validated",
    "ab_reviewing",
    "fallback_authorization_required",
    "finalizing",
    "validated",
    "collection_synthesizing",
    "delivered",
    "blocked",
}
VALID_AUTH_STATUSES = {
    "unknown",
    "not_required",
    "requested",
    "authorized",
    "declined",
    "unavailable",
    "failed",
}
VALID_VALIDATION_STATUSES = {"not_run", "passed", "failed"}
REQUIRED_CHECKPOINT_FIELDS = (
    "checkpoint_version",
    "checkpoint_kind",
    "current_phase",
    "completed_files",
    "subagent_authorization",
    "fallback_authorization",
    "validation",
    "residual_risks",
)


class CheckpointParseError(ValueError):
    """Raised when a checkpoint cannot be parsed."""


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_checkpoint(checkpoint_kind: str, current_phase: str = "initialized") -> dict[str, Any]:
    return {
        "checkpoint_version": CHECKPOINT_VERSION,
        "checkpoint_kind": checkpoint_kind,
        "current_phase": current_phase,
        "updated_at": utc_timestamp(),
        "completed_files": [],
        "subagent_authorization": {
            "required": True,
            "status": "unknown",
            "reason": "",
        },
        "fallback_authorization": {
            "required": False,
            "status": "unknown",
            "reason": "",
        },
        "validation": {
            "validator": "",
            "status": "not_run",
            "report_path": "",
            "issues": [],
        },
        "residual_risks": [],
    }


def strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        without_comment = strip_comment(raw_line).rstrip()
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        if "\t" in without_comment[:indent]:
            raise CheckpointParseError("Tabs are not supported for indentation.")
        lines.append((indent, without_comment.strip()))

    if not lines:
        raise CheckpointParseError("Checkpoint is empty.")

    parsed, next_index = parse_block(lines, 0, lines[0][0])
    if next_index != len(lines):
        raise CheckpointParseError(f"Unexpected trailing content near line {next_index + 1}.")
    if not isinstance(parsed, dict):
        raise CheckpointParseError("Checkpoint root must be a mapping.")
    return parsed


def parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    current_indent, current_text = lines[index]
    if current_indent < indent:
        return {}, index
    if current_indent != indent:
        raise CheckpointParseError(
            f"Unexpected indentation near line {index + 1}: expected {indent}, got {current_indent}."
        )
    if current_text == "-" or current_text.startswith("- "):
        return parse_list(lines, index, indent)
    return parse_map(lines, index, indent)


def parse_map(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise CheckpointParseError(f"Unexpected nested mapping near line {index + 1}.")
        if text.startswith("- "):
            break
        if ":" not in text:
            raise CheckpointParseError(f"Expected key/value pair near line {index + 1}.")
        key, raw_value = text.split(":", 1)
        key = key.strip()
        if not key:
            raise CheckpointParseError(f"Empty key near line {index + 1}.")
        raw_value = raw_value.strip()
        index += 1
        if raw_value:
            result[key] = parse_scalar(raw_value)
        elif index < len(lines) and lines[index][0] > current_indent:
            result[key], index = parse_block(lines, index, lines[index][0])
        else:
            result[key] = {}
    return result, index


def parse_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise CheckpointParseError(f"Unexpected nested list item near line {index + 1}.")
        if text != "-" and not text.startswith("- "):
            break

        item_text = text[1:].strip()
        index += 1
        if not item_text:
            if index < len(lines) and lines[index][0] > current_indent:
                item, index = parse_block(lines, index, lines[index][0])
            else:
                item = None
            result.append(item)
            continue

        if ":" in item_text:
            key, raw_value = item_text.split(":", 1)
            item = {key.strip(): parse_scalar(raw_value.strip())}
            if index < len(lines) and lines[index][0] > current_indent:
                nested, index = parse_block(lines, index, lines[index][0])
                if not isinstance(nested, dict):
                    raise CheckpointParseError(
                        f"List item mapping has non-mapping continuation near line {index + 1}."
                    )
                item.update(nested)
            result.append(item)
        else:
            result.append(parse_scalar(item_text))
            if index < len(lines) and lines[index][0] > current_indent:
                raise CheckpointParseError(
                    f"Scalar list item cannot have nested content near line {index + 1}."
                )
    return result, index


def format_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return '""'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        if value == "" or any(char in value for char in ":#[]{}"):
            return json.dumps(value, ensure_ascii=False)
        return value
    return json.dumps(value, ensure_ascii=False)


def dump_simple_yaml(data: dict[str, Any]) -> str:
    return "\n".join(format_yaml_value(data, 0)) + "\n"


def format_yaml_value(value: Any, indent: int) -> list[str]:
    spaces = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{spaces}{key}:")
                lines.extend(format_yaml_value(item, indent + 2))
            elif isinstance(item, list) and not item:
                lines.append(f"{spaces}{key}: []")
            elif isinstance(item, dict) and not item:
                lines.append(f"{spaces}{key}: {{}}")
            else:
                lines.append(f"{spaces}{key}: {format_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{spaces}[]"]
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{spaces}-")
                lines.extend(format_yaml_value(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{spaces}-")
                lines.extend(format_yaml_value(item, indent + 2))
            else:
                lines.append(f"{spaces}- {format_scalar(item)}")
        return lines
    return [f"{spaces}{format_scalar(value)}"]


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def write_checkpoint(path: Path, checkpoint: dict[str, Any]) -> None:
    checkpoint = dict(checkpoint)
    checkpoint["updated_at"] = utc_timestamp()
    atomic_write_text(path, dump_simple_yaml(checkpoint))


def validate_checkpoint(data: dict[str, Any], expected_kind: str) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_CHECKPOINT_FIELDS:
        if field not in data:
            issues.append(f"Checkpoint is missing required field: {field}")

    if data.get("checkpoint_version") != CHECKPOINT_VERSION:
        issues.append(
            f"checkpoint_version must be {CHECKPOINT_VERSION}, got {data.get('checkpoint_version')!r}."
        )
    if data.get("checkpoint_kind") != expected_kind:
        issues.append(
            f"checkpoint_kind must be {expected_kind!r}, got {data.get('checkpoint_kind')!r}."
        )
    if data.get("current_phase") not in VALID_PHASES:
        issues.append(f"current_phase is not recognized: {data.get('current_phase')!r}.")
    if not isinstance(data.get("completed_files"), list):
        issues.append("completed_files must be a list.")
    if not isinstance(data.get("residual_risks"), list):
        issues.append("residual_risks must be a list.")

    validate_authorization(data.get("subagent_authorization"), "subagent_authorization", issues)
    validate_authorization(data.get("fallback_authorization"), "fallback_authorization", issues)
    validate_validation(data.get("validation"), issues)
    return issues


def validate_authorization(value: Any, field: str, issues: list[str]) -> None:
    if not isinstance(value, dict):
        issues.append(f"{field} must be a mapping.")
        return
    if not isinstance(value.get("required"), bool):
        issues.append(f"{field}.required must be true or false.")
    if value.get("status") not in VALID_AUTH_STATUSES:
        issues.append(f"{field}.status is not recognized: {value.get('status')!r}.")
    if not isinstance(value.get("reason"), str):
        issues.append(f"{field}.reason must be a string.")


def validate_validation(value: Any, issues: list[str]) -> None:
    if not isinstance(value, dict):
        issues.append("validation must be a mapping.")
        return
    if not isinstance(value.get("validator"), str):
        issues.append("validation.validator must be a string.")
    if value.get("status") not in VALID_VALIDATION_STATUSES:
        issues.append(f"validation.status is not recognized: {value.get('status')!r}.")
    if not isinstance(value.get("report_path"), str):
        issues.append("validation.report_path must be a string.")
    if not isinstance(value.get("issues"), list):
        issues.append("validation.issues must be a list.")


def load_checkpoint(path: Path) -> dict[str, Any]:
    try:
        return parse_simple_yaml(path.read_text(encoding="utf-8"))
    except CheckpointParseError:
        raise
    except OSError as error:
        raise CheckpointParseError(str(error)) from error


def validate_checkpoint_file(path: Path, expected_kind: str) -> dict[str, Any]:
    if not path.is_file():
        return {"ok": False, "issues": [f"Checkpoint file does not exist: {path}"]}
    try:
        data = load_checkpoint(path)
    except CheckpointParseError as error:
        return {"ok": False, "issues": [f"Could not parse checkpoint: {error}"]}
    issues = validate_checkpoint(data, expected_kind)
    return {"ok": not issues, "issues": issues, "checkpoint": data}


def single_checkpoint_path(book_dir: Path) -> Path:
    return book_dir / SINGLE_CHECKPOINT_RELATIVE_PATH


def collection_manifest_path(collection_dir: Path) -> Path:
    return collection_dir / COLLECTION_MANIFEST_NAME


def init_single(book_dir: Path, phase: str) -> dict[str, Any]:
    checkpoint = default_checkpoint(SINGLE_CHECKPOINT_KIND, phase)
    write_checkpoint(single_checkpoint_path(book_dir), checkpoint)
    return checkpoint


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-single")
    init_parser.add_argument("book_dir")
    init_parser.add_argument("--phase", default="initialized", choices=sorted(VALID_PHASES))

    validate_single_parser = subparsers.add_parser("validate-single")
    validate_single_parser.add_argument("book_dir")

    validate_collection_parser = subparsers.add_parser("validate-collection-resume")
    validate_collection_parser.add_argument("collection_dir")

    args = parser.parse_args(argv)
    if args.command == "init-single":
        checkpoint = init_single(Path(args.book_dir), args.phase)
        print(json.dumps(checkpoint, ensure_ascii=False, indent=2))
        return 0

    if args.command == "validate-single":
        report = validate_checkpoint_file(
            single_checkpoint_path(Path(args.book_dir)),
            SINGLE_CHECKPOINT_KIND,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1

    manifest_report = validate_checkpoint_file(
        collection_manifest_path(Path(args.collection_dir)),
        COLLECTION_CHECKPOINT_KIND,
    )
    print(json.dumps(manifest_report, ensure_ascii=False, indent=2))
    return 0 if manifest_report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
