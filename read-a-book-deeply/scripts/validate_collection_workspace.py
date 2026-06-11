"""Validate a read-a-book-deeply thematic collection workspace.

The validator checks the collection layer built on top of already validated
single-book workspaces. It uses only the Python standard library, does not
access the network, and prints a JSON report.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_COLLECTION_PROMPTS = {
    "agent-a-summarizer-multibook.md",
    "agent-b-skeptic-multibook.md",
    "agent-c-cross-book-synthesizer.md",
    "agent-d-cross-book-skeptic.md",
    "orchestrator-final-multibook.md",
    "orchestrator-collection-final.md",
}
TOP_LEVEL_AGENT_OUTPUTS = {
    "agent_c_synthesis.md",
    "agent_d_skeptic.md",
    "orchestrator_collection_arbitration.md",
}
CLAIMS_LEDGER_MARKERS = (
    "Claim ID:",
    "Sources:",
    "Confidence:",
    "Risk:",
)
REQUIRED_SUBAGENT_ARTIFACT_ROLES = {
    "agent_a_structured_material",
    "agent_b_structured_risk",
}
_CHECKPOINT_MODULE: Any | None = None


class ManifestParseError(ValueError):
    """Raised when the limited YAML parser cannot parse the manifest."""


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def load_checkpoint_module(issues: list[str] | None = None) -> Any | None:
    global _CHECKPOINT_MODULE
    if _CHECKPOINT_MODULE is not None:
        return _CHECKPOINT_MODULE

    checkpoint_path = Path(__file__).resolve().parent / "checkpoint.py"
    if not checkpoint_path.is_file():
        if issues is not None:
            add_issue(issues, "Skill is missing scripts/checkpoint.py.")
        return None

    spec = importlib.util.spec_from_file_location("checkpoint", checkpoint_path)
    if spec is None or spec.loader is None:
        if issues is not None:
            add_issue(issues, "Could not load scripts/checkpoint.py.")
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _CHECKPOINT_MODULE = module
    return module


def parse_manifest(text: str) -> dict[str, Any]:
    checkpoint_module = load_checkpoint_module()
    if checkpoint_module is None or not hasattr(checkpoint_module, "parse_simple_yaml"):
        raise ManifestParseError("Could not load checkpoint YAML parser.")
    try:
        return checkpoint_module.parse_simple_yaml(text)
    except Exception as error:
        raise ManifestParseError(str(error)) from error


def resolve_manifest_path(collection_dir: Path, book_dir: Path | None, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw_path = Path(value)
    if raw_path.is_absolute():
        return raw_path
    if book_dir is not None:
        candidate = book_dir / raw_path
        if candidate.exists():
            return candidate
    return collection_dir / raw_path


def load_single_book_validator(skill_dir: Path, issues: list[str]) -> Any | None:
    validator_path = skill_dir / "scripts" / "validate_book_workspace.py"
    if not validator_path.is_file():
        add_issue(issues, "Skill is missing scripts/validate_book_workspace.py.")
        return None

    spec = importlib.util.spec_from_file_location("validate_book_workspace", validator_path)
    if spec is None or spec.loader is None:
        add_issue(issues, "Could not load validate_book_workspace.py.")
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "validate"):
        add_issue(issues, "validate_book_workspace.py does not expose validate().")
        return None
    return module


def load_subagent_artifact_validator(skill_dir: Path, issues: list[str]) -> Any | None:
    validator_path = skill_dir / "scripts" / "validate_subagent_artifact.py"
    if not validator_path.is_file():
        add_issue(issues, "Skill is missing scripts/validate_subagent_artifact.py.")
        return None

    spec = importlib.util.spec_from_file_location("validate_subagent_artifact", validator_path)
    if spec is None or spec.loader is None:
        add_issue(issues, "Could not load validate_subagent_artifact.py.")
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "validate_file"):
        add_issue(issues, "validate_subagent_artifact.py does not expose validate_file().")
        return None
    return module


def validate_skill_resources(skill_dir: Path, issues: list[str]) -> None:
    prompt_dir = skill_dir / "references" / "subagent-prompts"
    if not prompt_dir.is_dir():
        add_issue(issues, "Skill is missing references/subagent-prompts/.")
        return
    present = {p.name for p in prompt_dir.glob("*.md")}
    missing = sorted(REQUIRED_COLLECTION_PROMPTS - present)
    if missing:
        add_issue(issues, "Missing collection prompt templates: " + ", ".join(missing))

    collection_mode = skill_dir / "references" / "collection-mode.md"
    if not collection_mode.is_file():
        add_issue(issues, "Skill is missing references/collection-mode.md.")

    checkpointing = skill_dir / "references" / "checkpointing.md"
    if not checkpointing.is_file():
        add_issue(issues, "Skill is missing references/checkpointing.md.")

    artifact_validator = skill_dir / "scripts" / "validate_subagent_artifact.py"
    if not artifact_validator.is_file():
        add_issue(issues, "Skill is missing scripts/validate_subagent_artifact.py.")


def validate_top_level(collection_dir: Path, manifest: dict[str, Any], issues: list[str]) -> None:
    markdown_files = sorted(p.name for p in collection_dir.iterdir() if p.is_file() and p.suffix.lower() == ".md")
    if not markdown_files:
        add_issue(issues, "No top-level Markdown thematic report found.")
    elif len(markdown_files) > 1:
        add_issue(issues, "Multiple top-level Markdown reports found: " + ", ".join(markdown_files))

    synthesis = manifest.get("synthesis")
    final_report = synthesis.get("final_report") if isinstance(synthesis, dict) else None
    if isinstance(final_report, str) and final_report.strip():
        final_report_path = collection_dir / final_report
        if not final_report_path.is_file():
            add_issue(issues, f"Manifest final_report does not exist: {final_report}")
        elif final_report_path.parent.resolve() != collection_dir.resolve():
            add_issue(issues, "Manifest final_report must be a top-level Markdown file.")

    for banned_name in sorted(TOP_LEVEL_AGENT_OUTPUTS):
        if (collection_dir / banned_name).exists():
            add_issue(issues, f"Intermediate agent output left at collection top level: {banned_name}")

    theme_inference = manifest.get("theme_inference")
    selected_theme = theme_inference.get("selected_theme") if isinstance(theme_inference, dict) else None
    if markdown_files and isinstance(selected_theme, str) and selected_theme.strip():
        final_report_name = final_report if isinstance(final_report, str) and final_report.strip() else markdown_files[0]
        final_report_path = collection_dir / final_report_name
        if final_report_path.is_file():
            final_text = final_report_path.read_text(encoding="utf-8")
            if selected_theme not in final_text:
                add_issue(issues, "Final thematic report does not mention theme_inference.selected_theme.")


def validate_synthesis(collection_dir: Path, issues: list[str]) -> None:
    claims_ledger = collection_dir / "synthesis" / "claims_ledger.md"
    if not claims_ledger.is_file():
        add_issue(issues, "Missing synthesis/claims_ledger.md.")
    else:
        text = claims_ledger.read_text(encoding="utf-8")
        for marker in CLAIMS_LEDGER_MARKERS:
            if marker not in text:
                add_issue(issues, f"synthesis/claims_ledger.md is missing marker: {marker}")

    per_book_cards = collection_dir / "synthesis" / "inputs" / "per_book_cards.md"
    if not per_book_cards.is_file():
        add_issue(issues, "Missing synthesis/inputs/per_book_cards.md.")


def validate_books(
    collection_dir: Path,
    skill_dir: Path,
    manifest: dict[str, Any],
    issues: list[str],
    final_report_exists: bool,
) -> None:
    books = manifest.get("books")
    if not isinstance(books, list):
        add_issue(issues, "Manifest field 'books' must be a list.")
        return
    if len(books) < 2:
        add_issue(issues, "Manifest field 'books' must include at least 2 books.")

    single_book_validator = load_single_book_validator(skill_dir, issues)
    artifact_validator = load_subagent_artifact_validator(skill_dir, issues)
    artifact_protocol = manifest.get("artifact_protocol")
    run_id = artifact_protocol.get("run_id") if isinstance(artifact_protocol, dict) else None

    for index, book in enumerate(books, start=1):
        if not isinstance(book, dict):
            add_issue(issues, f"Book entry #{index} must be a mapping.")
            continue
        book_label = str(book.get("id") or f"#{index}")
        for field in ("id", "title", "book_dir", "final_summary", "book_md"):
            if not isinstance(book.get(field), str) or not book[field].strip():
                add_issue(issues, f"Book {book_label} is missing required field: {field}")

        for field in ("status", "workspace", "ab_review_status"):
            if not isinstance(book.get(field), str) or not book[field].strip():
                add_issue(issues, f"Book {book_label} is missing required field: {field}")
        for field in ("fallback_authorization_required", "fallback_authorized", "validator_ok"):
            if not isinstance(book.get(field), bool):
                add_issue(issues, f"Book {book_label} field '{field}' must be true or false.")
        for field in ("errors", "residual_risks"):
            if not isinstance(book.get(field), list):
                add_issue(issues, f"Book {book_label} field '{field}' must be a list.")

        if book.get("status") != "validated":
            add_issue(issues, f"Book {book_label} status must be 'validated' before final collection validation.")
            if final_report_exists:
                add_issue(issues, f"Book {book_label} is not validated, so final collection report must not exist.")
        if book.get("fallback_authorization_required") is True and final_report_exists:
            add_issue(issues, f"Book {book_label} has fallback_authorization_required=true, so final collection report must not exist.")
        if book.get("validator_ok") is not True and final_report_exists:
            add_issue(issues, f"Book {book_label} has validator_ok=false, so final collection report must not exist.")

        book_dir_for_artifacts = resolve_manifest_path(collection_dir, None, book.get("book_dir"))

        if final_report_exists and book.get("fallback_authorized") is not True:
            validate_subagent_artifacts(
                collection_dir,
                book_dir_for_artifacts,
                book,
                book_label,
                run_id,
                artifact_validator,
                issues,
            )

        book_dir = book_dir_for_artifacts
        if book_dir is None:
            continue
        if not book_dir.is_dir():
            add_issue(issues, f"Book {book_label} directory does not exist: {book.get('book_dir')}")
            continue

        workspace = resolve_manifest_path(collection_dir, None, book.get("workspace"))
        if workspace is None or not workspace.is_dir():
            add_issue(issues, f"Book {book_label} workspace does not exist: {book.get('workspace')}")

        final_summary = resolve_manifest_path(collection_dir, book_dir, book.get("final_summary"))
        if final_summary is None or not final_summary.is_file():
            add_issue(issues, f"Book {book_label} final_summary does not exist: {book.get('final_summary')}")

        book_md = resolve_manifest_path(collection_dir, book_dir, book.get("book_md"))
        if book_md is None or not book_md.is_file():
            add_issue(issues, f"Book {book_label} book_md does not exist: {book.get('book_md')}")

        for optional_field in ("coverage_ledger", "argument_map", "risk_register"):
            optional_value = book.get(optional_field)
            if isinstance(optional_value, str) and optional_value.strip():
                optional_path = resolve_manifest_path(collection_dir, book_dir, optional_value)
                if optional_path is None or not optional_path.exists():
                    add_issue(issues, f"Book {book_label} {optional_field} does not exist: {optional_value}")

        if single_book_validator is not None:
            book_report = single_book_validator.validate(book_dir, skill_dir)
            if not book_report.get("ok"):
                detail = "; ".join(str(item) for item in book_report.get("issues", []))
                add_issue(issues, f"Book {book_label} failed single-book validation: {detail}")


def validate_subagent_artifacts(
    collection_dir: Path,
    book_dir: Path | None,
    book: dict[str, Any],
    book_label: str,
    run_id: Any,
    artifact_validator: Any | None,
    issues: list[str],
) -> None:
    artifacts = book.get("subagent_artifacts")
    if not isinstance(artifacts, list):
        add_issue(issues, f"Book {book_label} is missing subagent_artifacts for multi-book A/B review.")
        return

    roles_seen: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            add_issue(issues, f"Book {book_label} subagent_artifacts entries must be mappings.")
            continue
        role = artifact.get("role")
        agent_id = artifact.get("agent_id")
        attempt_id = artifact.get("attempt_id")
        accepted_artifact = artifact.get("accepted_artifact")
        validation_report = artifact.get("validation_report")
        validation_ok = artifact.get("validation_ok")
        quarantined_attempts = artifact.get("quarantined_attempts")

        if isinstance(role, str):
            roles_seen.add(role)
        if role not in REQUIRED_SUBAGENT_ARTIFACT_ROLES:
            add_issue(issues, f"Book {book_label} has unsupported subagent artifact role: {role!r}")
        for field_name, field_value in (
            ("agent_id", agent_id),
            ("attempt_id", attempt_id),
            ("accepted_artifact", accepted_artifact),
            ("validation_report", validation_report),
        ):
            if not isinstance(field_value, str) or not field_value.strip():
                add_issue(
                    issues,
                    f"Book {book_label} subagent artifact {role!r} is missing required field: {field_name}",
                )
        if validation_ok is not True:
            add_issue(
                issues,
                f"Book {book_label} subagent artifact {role!r} must have validation_ok=true.",
            )
        if not isinstance(quarantined_attempts, list):
            add_issue(
                issues,
                f"Book {book_label} subagent artifact {role!r} quarantined_attempts must be a list.",
            )

        accepted_path = resolve_manifest_path(collection_dir, book_dir, accepted_artifact)
        if accepted_path is None or not accepted_path.is_file():
            add_issue(
                issues,
                f"Book {book_label} accepted subagent artifact does not exist: {accepted_artifact}",
            )
        elif artifact_validator is not None:
            report = artifact_validator.validate_file(
                accepted_path,
                expected_run_id=run_id if isinstance(run_id, str) and run_id.strip() else None,
                expected_book_id=str(book.get("id")) if isinstance(book.get("id"), str) else None,
                expected_agent_id=agent_id if isinstance(agent_id, str) and agent_id.strip() else None,
                expected_attempt_id=attempt_id if isinstance(attempt_id, str) and attempt_id.strip() else None,
                expected_role=role if isinstance(role, str) and role.strip() else None,
            )
            if not report.get("ok"):
                detail = "; ".join(str(item) for item in report.get("issues", []))
                add_issue(issues, f"Book {book_label} accepted subagent artifact failed validation: {detail}")

        validation_report_path = resolve_manifest_path(collection_dir, book_dir, validation_report)
        if validation_report_path is None or not validation_report_path.is_file():
            add_issue(
                issues,
                f"Book {book_label} subagent validation_report does not exist: {validation_report}",
            )

    missing_roles = sorted(REQUIRED_SUBAGENT_ARTIFACT_ROLES - roles_seen)
    if missing_roles:
        add_issue(
            issues,
            f"Book {book_label} is missing required subagent artifact roles: {', '.join(missing_roles)}",
        )


def validate_manifest_fields(collection_dir: Path, manifest: dict[str, Any], issues: list[str]) -> None:
    checkpoint_module = load_checkpoint_module(issues)
    if checkpoint_module is not None:
        checkpoint_issues = checkpoint_module.validate_checkpoint(
            manifest,
            checkpoint_module.COLLECTION_CHECKPOINT_KIND,
        )
        for issue in checkpoint_issues:
            add_issue(issues, f"Collection checkpoint is invalid: {issue}")

    resume = manifest.get("resume")
    if not isinstance(resume, dict):
        add_issue(issues, "Manifest field 'resume' must be a mapping.")
    else:
        if not isinstance(resume.get("can_resume"), bool):
            add_issue(issues, "resume.can_resume must be true or false.")
        if not isinstance(resume.get("resume_from"), str):
            add_issue(issues, "resume.resume_from must be a string.")
        if not isinstance(resume.get("next_action"), str):
            add_issue(issues, "resume.next_action must be a string.")
        if not isinstance(resume.get("blocked_reason"), str):
            add_issue(issues, "resume.blocked_reason must be a string.")

    theme = manifest.get("theme")
    if not isinstance(theme, str) or not theme.strip():
        add_issue(issues, "Manifest field 'theme' is required.")

    mode = manifest.get("mode")
    if mode not in {"linked", "bundled"}:
        add_issue(issues, "Manifest field 'mode' must be 'linked' or 'bundled'.")
    elif mode == "bundled" and not (collection_dir / "books").is_dir():
        add_issue(issues, "Bundled mode requires books/ directory.")

    artifact_protocol = manifest.get("artifact_protocol")
    if not isinstance(artifact_protocol, dict):
        add_issue(issues, "Manifest field 'artifact_protocol' must be a mapping.")
    else:
        run_id = artifact_protocol.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            add_issue(issues, "artifact_protocol.run_id is required.")
        for field in ("accepted_dir", "quarantine_dir", "validator"):
            if not isinstance(artifact_protocol.get(field), str) or not artifact_protocol[field].strip():
                add_issue(issues, f"artifact_protocol.{field} is required.")


def validate_theme_inference(manifest: dict[str, Any], issues: list[str]) -> None:
    theme_inference = manifest.get("theme_inference")
    if not isinstance(theme_inference, dict):
        add_issue(issues, "Manifest field 'theme_inference' must be a mapping.")
        return

    user_provided_theme = theme_inference.get("user_provided_theme")
    if not isinstance(user_provided_theme, bool):
        add_issue(issues, "theme_inference.user_provided_theme must be true or false.")

    selected_theme = theme_inference.get("selected_theme")
    if not isinstance(selected_theme, str) or not selected_theme.strip():
        add_issue(issues, "theme_inference.selected_theme is required before final collection validation.")

    theme_selection_basis = theme_inference.get("theme_selection_basis")
    if not isinstance(theme_selection_basis, str) or not theme_selection_basis.strip():
        add_issue(issues, "theme_inference.theme_selection_basis is required before final collection validation.")

    alternative_themes = theme_inference.get("alternative_themes")
    if not isinstance(alternative_themes, list):
        add_issue(issues, "theme_inference.alternative_themes must be a list.")
    else:
        non_empty_alternatives = [
            theme for theme in alternative_themes if isinstance(theme, str) and theme.strip()
        ]
        if len(non_empty_alternatives) < 2:
            add_issue(issues, "theme_inference.alternative_themes must include at least 2 non-empty themes.")

    if user_provided_theme is False:
        provisional = theme_inference.get("provisional_theme_direction")
        if not isinstance(provisional, str) or not provisional.strip():
            add_issue(
                issues,
                "theme_inference.provisional_theme_direction is required when user_provided_theme=false.",
            )


def validate_orchestration(manifest: dict[str, Any], issues: list[str]) -> None:
    orchestration = manifest.get("orchestration")
    if not isinstance(orchestration, dict):
        add_issue(issues, "Manifest field 'orchestration' must be a mapping.")
        return

    if orchestration.get("parallel_enabled") is not True:
        add_issue(issues, "orchestration.parallel_enabled must be true.")

    max_parallel_books = orchestration.get("max_parallel_books")
    if not isinstance(max_parallel_books, int) or max_parallel_books <= 0:
        add_issue(issues, "orchestration.max_parallel_books must be a positive integer.")

    if orchestration.get("authorization_scope") != "batch":
        add_issue(issues, "orchestration.authorization_scope must be 'batch'.")

    if orchestration.get("quality_gate") != "queue_not_downgrade":
        add_issue(issues, "orchestration.quality_gate must be 'queue_not_downgrade'.")

    if orchestration.get("owner") != "main_thread":
        add_issue(issues, "orchestration.owner must be 'main_thread'.")


def final_report_exists(collection_dir: Path, manifest: dict[str, Any]) -> bool:
    synthesis = manifest.get("synthesis")
    final_report = synthesis.get("final_report") if isinstance(synthesis, dict) else None
    if isinstance(final_report, str) and final_report.strip():
        return (collection_dir / final_report).is_file()
    return any(p.is_file() and p.suffix.lower() == ".md" for p in collection_dir.iterdir())


def validate(collection_dir: Path, skill_dir: Path) -> dict[str, object]:
    issues: list[str] = []
    manifest: dict[str, Any] = {}

    if not collection_dir.is_dir():
        add_issue(issues, f"Collection directory does not exist: {collection_dir}")
    else:
        manifest_path = collection_dir / "collection_manifest.yaml"
        if not manifest_path.is_file():
            add_issue(issues, "Missing collection_manifest.yaml.")
        else:
            try:
                manifest = parse_manifest(manifest_path.read_text(encoding="utf-8"))
            except ManifestParseError as error:
                add_issue(issues, f"Could not parse collection_manifest.yaml: {error}")

        if manifest:
            validate_manifest_fields(collection_dir, manifest, issues)
            validate_theme_inference(manifest, issues)
            validate_orchestration(manifest, issues)
            has_final_report = final_report_exists(collection_dir, manifest)
            validate_books(collection_dir, skill_dir, manifest, issues, has_final_report)
            validate_top_level(collection_dir, manifest, issues)
        validate_synthesis(collection_dir, issues)

    validate_skill_resources(skill_dir, issues)
    return {
        "collection_dir": str(collection_dir.resolve()),
        "skill_dir": str(skill_dir.resolve()),
        "ok": not issues,
        "issues": issues,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("collection_dir", help="Finished thematic collection workspace to validate")
    parser.add_argument(
        "--skill-dir",
        default=str(Path(__file__).resolve().parents[1]),
        help="Path to the read-a-book-deeply skill directory",
    )
    args = parser.parse_args(argv)

    report = validate(Path(args.collection_dir), Path(args.skill_dir))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
