# Checkpointing and Resume Protocol

This file is the workflow SSOT for recovery state. `scripts/checkpoint.py` is the code SSOT for checkpoint field names, phase enums, simple YAML parsing, atomic writes, and deterministic validation.

## 1. Scope

Use checkpoints for both single-book and multi-book work.

- Single-book checkpoint file: `conversion/checkpoint.yaml`.
- Multi-book checkpoint file: `collection_manifest.yaml`.
- Collection resume details live in `collection_manifest.yaml` under `resume`.

Do not create parallel ad hoc progress files. Working notes may live under `conversion/_work/`, `conversion/review/`, or `synthesis/review/`, but recovery decisions must use the checkpoint or manifest.

## 2. Resume Discovery

When starting or resuming work:

1. Look for an existing book workspace with `source/` and `conversion/`.
2. For a single book, load `conversion/checkpoint.yaml`.
3. For a collection, load `collection_manifest.yaml`.
4. Run the relevant validator before trusting a completed phase.
5. Resume only from the checkpointed `current_phase` and verified files.

If the checkpoint or manifest is missing, malformed, points to missing files, or conflicts with the actual workspace, stop and ask the user whether to rebuild, repair, or continue from a specific phase. Do not infer a hidden fallback path.

## 3. Atomic Writes

Update checkpoints through `scripts/checkpoint.py` helpers or the same atomic pattern:

1. Write the new YAML to a temporary file in the same directory.
2. Flush and fsync the temporary file.
3. Replace the target checkpoint with `os.replace`.

Never stream partial checkpoint content directly into the final checkpoint file.

## 4. Single-book Checkpoint Schema

`conversion/checkpoint.yaml`:

```yaml
checkpoint_version: 1
checkpoint_kind: single_book
current_phase: initialized
updated_at: "2026-06-12T00:00:00+00:00"
completed_files: []
subagent_authorization:
  required: true
  status: unknown
  reason: ""
fallback_authorization:
  required: false
  status: unknown
  reason: ""
validation:
  validator: "scripts/validate_book_workspace.py"
  status: not_run
  report_path: ""
  issues: []
residual_risks: []
```

Recommended phases:

- `initialized`: workspace exists, but source placement may not be complete.
- `source_prepared`: original file is under `source/`.
- `converted`: `conversion/book.md` exists.
- `image_validated`: image manifest and Markdown image links have been checked.
- `ab_reviewing`: Agent A/B work is launched or being monitored.
- `fallback_authorization_required`: delegation failed, was unavailable, or was declined; user authorization is required before self-review fallback.
- `finalizing`: Orchestrator is writing the only final summary.
- `validated`: `scripts/validate_book_workspace.py` passed.
- `delivered`: user-facing delivery note has been sent.
- `blocked`: work cannot continue without user input.

## 5. Collection Resume Fields

`collection_manifest.yaml` is also the batch checkpoint. It must include the same top-level checkpoint fields as the single-book checkpoint with `checkpoint_kind: collection`, plus:

```yaml
resume:
  can_resume: true
  resume_from: initialized
  next_action: ""
  blocked_reason: ""
```

Book-level status, A/B status, fallback authorization, validation status, accepted artifacts, quarantined attempts, and residual risks remain in `books`. Do not duplicate per-book state in another collection progress file.

## 6. Authorization State

Use the checkpoint authorization blocks for both subagents and fallback:

- `unknown`: no explicit user decision is recorded.
- `requested`: the user has been asked and work is waiting.
- `authorized`: the user explicitly authorized this path.
- `declined`: the user explicitly declined this path.
- `unavailable`: the environment or tool surface cannot provide the path.
- `failed`: a concrete launch or execution attempt failed.
- `not_required`: this authorization is not needed for the current path.

Fallback must not start unless `fallback_authorization.status` is `authorized` for the current run.

## 7. Validation Contract

Before delivery:

- Single book: `scripts/validate_book_workspace.py` must pass and will validate `conversion/checkpoint.yaml`.
- Collection: `scripts/validate_collection_workspace.py` must pass and will validate checkpoint fields plus `resume` in `collection_manifest.yaml`.
- Multi-book accepted subagent artifacts: `scripts/validate_subagent_artifact.py` must pass before artifacts are accepted by the main thread.

Validators check structure and recovery metadata; they do not prove literary quality. Residual quality risks belong in `residual_risks` and the concise delivery note.
