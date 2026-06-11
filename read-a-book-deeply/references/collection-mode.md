# Multi-book / Thematic Reading Mode

Multi-book thematic reading is a main-thread collection orchestrator layered on top of the single-book workflow. It never replaces single-book deep reading. Each book must first receive its own faithful deep summary, adversarial review attempt, Orchestrator arbitration, clean workspace, and successful single-book validation.

## 1. Trigger Conditions

Enter this mode whenever the user uploads or asks to read multiple books in one request. Treat those books as one thematic reading collection. Also enter this mode when the user asks to:

- Read multiple books around one theme.
- Compare several books.
- Produce a thematic reading report.
- Build a cross-book synthesis, reading path, or concept map.
- Use phrases such as "多本书共读", "主题阅读", "比较这几本书", or "thematic reading report".

Do not enter this mode for a single-book summary, a brief recommendation list, audio generation, upload/publishing tasks, or a request that only asks for one book's deep summary.

If the user does not name a theme, do not ask for one. Infer a provisional theme direction from titles, metadata, tables of contents, and visible source content. This early direction is only a working hypothesis for orchestration; the final selected theme is chosen after all books have been independently summarized and validated.

## 2. Workflow Overview

1. Identify the book list, output language, and whether the user explicitly requests critical evaluation.
2. If the user supplied a theme, set it as the working collection theme. If not, infer `provisional_theme_direction` and record that the user did not provide a theme.
3. Create `collection_manifest.yaml` immediately as the batch checkpoint.
4. The main thread creates or resumes each book workspace, converts the book, validates images, and updates the batch checkpoint.
5. The main thread starts per-book Agent A/B review directly when subagents are authorized and available. Preserve parallel A/B execution when capacity allows, but isolate every subagent attempt with the concurrent artifact protocol.
6. The main thread validates completed A/B artifacts with `scripts/validate_subagent_artifact.py`, quarantines corrupted attempts, and commits only accepted artifacts.
7. The main-thread Orchestrator writes each book's final summary from `conversion/book.md` plus accepted structured A/B artifacts.
8. Validate each book workspace with `scripts/validate_book_workspace.py`.
9. If per-book A/B review cannot launch, the main thread must queue, retry, or ask the user for explicit single-thread fallback authorization. The book is not ready for collection until A/B is handled or the user explicitly authorizes fallback for that run.
10. After every book is validated, choose `selected_theme` and two `alternative_themes` from the final summaries and structure materials. If the user supplied a theme, `selected_theme` should match it.
11. Create `synthesis/inputs/per_book_cards.md`, `synthesis/inputs/source_index.md`, and `synthesis/inputs/unresolved_questions.md`.
12. Build `synthesis/claims_ledger.md` before treating cross-book claims as final.
13. Launch Agent C and Agent D if subagents are authorized and available.
14. The main-thread Collection Orchestrator arbitrates Agent C and Agent D, revises the claims ledger, and writes the only top-level thematic report.
15. Run `scripts/validate_collection_workspace.py` and fix every issue before delivery.

## 3. Main-thread Book Execution

The main thread owns all book conversion, checkpointing, A/B launch, arbitration, validation, and final collection synthesis. Do not create a Book Worker subagent and do not ask any subagent to create other subagents.

Default `max_parallel_books` is 3. This is a batch-level planning limit for active book pipelines, not a permission to weaken per-book A/B review. If there are more than 3 books, queue the rest.

Book status values:

- `queued`: Book is known but not assigned.
- `preparing`: Source has been placed in `source/` and workspace setup has started.
- `converted`: `conversion/book.md` exists and conversion/image checks are complete.
- `ab_reviewing`: The main thread has launched or is monitoring the book's A/B adversarial review.
- `fallback_authorization_required`: A/B could not launch and the main thread is waiting for explicit user authorization before any single-thread fallback.
- `finalizing`: Orchestrator is writing the single-book final summary.
- `validated`: Single-book final summary exists and `validate_book_workspace.py` passed.

Main-thread rules:

- Process each book as an independent single-book workflow.
- Use the provisional theme direction only as context; preserve the book's own chapter structure.
- Do not make cross-book claims until all single-book summaries pass validation.
- Keep intermediate materials under `conversion/`, `conversion/review/`, or `conversion/_work/`.
- Record A/B status, validator result, fallback authorization state, and residual risks in `collection_manifest.yaml`.
- If A/B agents cannot launch, set the book status to `fallback_authorization_required` and ask the user whether they explicitly authorize single-thread fallback.

The main thread owns scheduling, checkpoint updates, handoff, final theme selection, collection synthesis, and final delivery.

## 4. Concurrent Subagent Artifact Protocol

This protocol applies only in multi-book mode. Single-book mode continues to use the original single-book A/B prompts and Orchestrator prompt.

Use the multi-book prompt templates for per-book A/B and per-book final arbitration:

- `agent-a-summarizer-multibook.md`
- `agent-b-skeptic-multibook.md`
- `orchestrator-final-multibook.md`

The protocol preserves subagent concurrency while removing shared mutable artifact writes:

- Create one batch `run_id` and record it in `collection_manifest.yaml`.
- Each subagent attempt receives `run_id`, `book_id`, `agent_id`, and `attempt_id`.
- Attempt-local debug material belongs under `conversion/review/runs/{run_id}/{book_id}/{agent_id}/{attempt_id}/`.
- Subagents must not append to official artifacts and must not write shared filenames such as `summary_draft.md`.
- Streaming transcript is debug material only. It must not become an accepted Orchestrator input.
- The main thread validates completed subagent content with `scripts/validate_subagent_artifact.py`.
- Accepted artifacts are committed under `conversion/review/accepted/`.
- Corrupted attempts are recorded under `quarantined_attempts` and retried with a new `attempt_id`.
- A retry caused by artifact corruption is not fallback and does not authorize self-review.

Multi-book A/B outputs are structured to reduce long streaming pressure without reducing final quality. Agent A produces:

- `structure_coverage_ledger`
- `content_synthesis_notes`
- `interpretation_boundary_notes`
- `final_summary_building_blocks`

Agent B produces:

- `coverage_risk_register`
- `fidelity_risk_register`
- `genre_specific_risk_notes`
- `must_not_miss_register`

These sections are genre-compatible. Nonfiction, fiction, literature, history, biography, memoir, and mixed genres must all follow the book's own structure. The final single-book summary quality remains the Orchestrator's responsibility: it must still use `conversion/book.md` directly, cover every important chapter or structural unit, and separate source content, summary synthesis, and interpretive judgment.

## 5. Theme Inference

Use two-stage theme handling.

Stage 1: provisional direction. When the user gives no theme, infer `provisional_theme_direction` from titles, metadata, tables of contents, prefaces, headings, or visible source content. This direction should be broad and low-risk, such as "modern state formation and institutional capacity" rather than a precise thesis.

Stage 2: final theme selection. After all books pass single-book validation, synthesize the final summaries, coverage ledgers, argument maps, and risk registers to choose:

- `selected_theme`: the theme used for Agent C/D synthesis and the final report.
- `alternative_themes`: exactly two plausible but not selected themes.
- `theme_selection_basis`: a short explanation of why `selected_theme` best fits the full set.

Stage 3: collection synthesis. Use `selected_theme` for per-book cards, claims ledger, Agent C/D, and the final thematic report. The final report should briefly note the two alternatives and why they were not adopted.

## 6. Collection Modes

Default to `linked` mode. It keeps the collection workspace small and points back to already validated book workspaces.

```text
{Theme}-collection-{timestamp}/
├── collection_manifest.yaml
├── 主题共读报告.md or {Theme} - Thematic Reading Report.md
└── synthesis/
    ├── inputs/
    │   ├── per_book_cards.md
    │   ├── source_index.md
    │   └── unresolved_questions.md
    ├── agent_c_synthesis.md
    ├── agent_d_skeptic.md
    ├── concept_matrix.md
    ├── agreement_disagreement_map.md
    ├── chronology_or_argument_map.md
    ├── claims_ledger.md
    ├── reading_path.md
    └── review/
        ├── orchestrator_collection_arbitration.md
        └── collection_validation.json
```

Use `bundled` mode only when the user needs a portable archive. In bundled mode, copy or place the validated book workspaces under `books/`.

```text
{Theme}-collection-{timestamp}/
├── collection_manifest.yaml
├── 主题共读报告.md or {Theme} - Thematic Reading Report.md
├── books/
│   ├── BookA-YYYYMMDD-HHMMSS/
│   ├── BookB-YYYYMMDD-HHMMSS/
│   └── BookC-YYYYMMDD-HHMMSS/
└── synthesis/
```

Top-level rules:

- The collection top level must contain exactly one final thematic Markdown report.
- The collection top level must contain `collection_manifest.yaml`.
- Intermediate material must stay under `synthesis/`.
- Agent C, Agent D, and collection arbitration outputs must not be written at the top level.
- `books/` is required in `bundled` mode and optional only there.

## 7. Collection Manifest Schema

Use `collection_manifest.yaml`:

```yaml
checkpoint_version: 1
checkpoint_kind: collection
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
  validator: "scripts/validate_collection_workspace.py"
  status: not_run
  report_path: ""
  issues: []
residual_risks: []
resume:
  can_resume: true
  resume_from: initialized
  next_action: ""
  blocked_reason: ""
theme: ""
mode: linked
language: zh
critical_evaluation_requested: false
subagents_authorized: false
artifact_protocol:
  run_id: ""
  accepted_dir: "conversion/review/accepted"
  quarantine_dir: "conversion/review/quarantine"
  validator: "scripts/validate_subagent_artifact.py"
theme_inference:
  user_provided_theme: false
  provisional_theme_direction: ""
  selected_theme: ""
  alternative_themes:
    - ""
    - ""
  theme_selection_basis: ""
orchestration:
  parallel_enabled: true
  max_parallel_books: 3
  authorization_scope: batch
  quality_gate: queue_not_downgrade
  owner: main_thread
books:
  - id: book_a
    title: ""
    status: queued
    workspace: ""
    book_dir: ""
    final_summary: ""
    book_md: ""
    coverage_ledger: ""
    argument_map: ""
    risk_register: ""
    subagent_artifacts:
      - agent_id: agent_a
        role: agent_a_structured_material
        attempt_id: ""
        accepted_artifact: ""
        validation_report: ""
        validation_ok: true
        quarantined_attempts: []
      - agent_id: agent_b
        role: agent_b_structured_risk
        attempt_id: ""
        accepted_artifact: ""
        validation_report: ""
        validation_ok: true
        quarantined_attempts: []
    ab_review_status: ""
    fallback_authorization_required: false
    fallback_authorized: false
    validator_ok: true
    errors: []
    residual_risks: []
synthesis:
  requires_original_lookup_for_cross_book_claims: true
  claims_ledger: "synthesis/claims_ledger.md"
  final_report: "主题共读报告.md"
```

Required fields:

- Top-level checkpoint fields must follow `references/checkpointing.md` with `checkpoint_kind: collection`.
- `resume` must include `can_resume`, `resume_from`, `next_action`, and `blocked_reason`.
- `theme` must be non-empty.
- `artifact_protocol.run_id` is required for multi-book subagent runs, and accepted artifacts must use the same `run_id` sentinel.
- `theme_inference` is required.
- If `theme_inference.user_provided_theme` is `false`, `provisional_theme_direction`, `selected_theme`, at least two `alternative_themes`, and `theme_selection_basis` are required before final delivery.
- `selected_theme` must be written only after all books are validated.
- The final thematic report must use `selected_theme`.
- `synthesis.final_report` must follow `SKILL.md` output filename rules: Chinese collection requests use `主题共读报告.md`; non-Chinese collection requests use `{Theme} - Thematic Reading Report.md` unless the user requested a filename.
- `orchestration` is required, with `parallel_enabled: true`, `max_parallel_books: 3` by default, `authorization_scope: batch`, `quality_gate: queue_not_downgrade`, and `owner: main_thread`.
- `mode` must be `linked` or `bundled`.
- `books` must contain at least two books.
- Each book requires `id`, `title`, `status`, `workspace`, `book_dir`, `final_summary`, `book_md`, `ab_review_status`, `fallback_authorization_required`, `fallback_authorized`, and `validator_ok`.
- Each non-fallback validated book requires accepted `agent_a_structured_material` and `agent_b_structured_risk` artifacts with `validation_ok: true`.
- Each book must reach `validated` before final collection synthesis.
- A book with `fallback_authorization_required: true` is not ready for final collection synthesis.
- `final_summary` and `book_md` must resolve to existing files.
- Missing `coverage_ledger`, `argument_map`, or `risk_register` must be listed as residual risk in the collection report.
- `validator_ok` is a note, not proof. The collection validator should still call or reuse the single-book validator.

## 8. Per-book Cards

Before cross-book synthesis, create `synthesis/inputs/per_book_cards.md`. Each card must include:

- Book title and id.
- Genre and subgenre.
- The book's core question.
- Core thesis, narrative spine, or argument.
- Method, evidence, or narrative technique.
- Contribution to the theme.
- Limits or residual risks.
- Theme-relevant chapters.
- Key concepts available for comparison.
- Read material paths.
- Misattribution warnings.

Base each card on the final summary, accepted structured A/B artifacts, coverage ledger, argument map, and risk register. If a material is missing, say it is missing. Do not invent a substitute.

## 9. Evidence Levels

- Level 1: The claim comes from a final deep summary. Use this for overview and book positioning.
- Level 2: The claim is supported by coverage ledger, argument map, or risk register. Use this for structure, argument, and risk analysis.
- Level 3: The claim has been checked against `conversion/book.md`. Use this for cross-book claims, dispute judgments, concept differences, and high-risk attribution.

Rules:

- Key thematic report judgments should reach at least Level 2.
- Core cross-book claims, disagreement judgments, and mutual-support judgments need Level 3 spot checks or an explicit "not checked against original manuscript" label.
- A claim without an evidence level must not become a core conclusion.

## 10. Claims Ledger

`synthesis/claims_ledger.md` is the quality core of the collection workflow. Use a stable block format:

```text
Claim ID: C-001
Claim:
三本书都把现代国家能力的形成与财政汲取能力联系起来，但对战争压力的解释权重不同。

Type:
跨书综合判断

Sources:
- Book A: final summary 第 2 部分；book.md 第 2-3 章已回查
- Book B: argument map 中央论点；book.md 第 5 章已回查
- Book C: final summary 结论部分；未回查原文

Evidence Level:
Level 2 with partial Level 3 lookup

Confidence:
中

Risk:
Book C 更强调制度路径依赖，不应完全等同于 A/B 的战争财政解释。

Decision:
保留，但在最终报告中写成“存在部分重叠”，不得写成“三本书一致认为”。
```

Recommended claim types:

- 单书观察
- 跨书共识
- 跨书分歧
- 互补关系
- 概念差异
- 方法差异
- 解释性判断
- 待核验判断

Hard rules:

- Cross-book claims must list at least two sources unless they are explicitly marked as single-book observations.
- Core claims must include confidence and risk.
- Unverified claims cannot be written as certain conclusions.
- Claims that Agent D identifies as misattribution must be deleted or revised.

## 11. Agent Roles

The main thread handles every single-book pipeline. It converts, verifies assets, launches per-book A/B agents directly, validates and accepts structured artifacts, prepares the single-book final summary, runs validation, updates checkpoints, and records residual risks. It does not delegate book pipeline ownership to a Book Worker.

Agent C / Cross-book Synthesizer produces horizontal synthesis material only. It reads the collection manifest, per-book cards, final summaries, ledgers, argument maps, risk registers, and specific `conversion/book.md` passages when needed. It outputs book positions, concept matrix, agreements, disagreements, complementarities, irreducible tensions, candidate claims, required source lookups, and a reading path draft. It does not write the final report.

Agent D / Cross-book Skeptic reviews Agent C's synthesis. It checks misattribution, over-synthesis, missing minor views, concept conflation, evidence gaps, and claims that should be revised or deleted. It does not write a replacement final report.

The main-thread Collection Orchestrator arbitrates Agent C and Agent D, resolves or records unresolved risks, updates the claims ledger, and writes the only top-level final thematic report.

All A/B and C/D delegation must follow the batch authorization rule. A single explicit authorization for `subagents`, `多代理`, `parallel agent work`, or equivalent delegated work covers the whole multi-book batch. It does not authorize single-thread fallback; fallback needs separate explicit user authorization after the specific delegation failure is known.

## 12. Final Thematic Report Structure

Default structure:

1. 主题问题界定
   - State `selected_theme`.
   - If the user did not supply a theme, briefly mention the two alternatives and why they were not adopted.
2. 这组书分别站在哪里
3. 共识区
4. 分歧区
5. 互补区
6. 不能被强行综合的张力
7. 关键概念矩阵
8. 论证图、时间线或叙事图
9. 推荐阅读路径
10. 可追溯 claims ledger 摘要
11. 残余风险与未解决问题

Add a separate critical evaluation section only when the user explicitly asks for critique. That section may cover evidence quality, method limits, bias, omissions, and contemporary relevance.

## 13. Fallback Rules

Parallel capacity limits cause queueing, not fallback. A/B failure, missing subagent tools, unsupported nested delegation, or capacity exhaustion never permits automatic single-thread self-review.

Use Agent C and Agent D when subagents are available and explicitly authorized. If delegation is unavailable, forbidden by environment policy, declined by the user, or fails after a concrete attempt, ask the user whether they explicitly authorize main-thread synthesis plus self-review. Do not continue with fallback synthesis until that authorization is received. The final quality note must name the exact reason and state that the user explicitly authorized fallback.

Fallback does not relax evidence rules, claims ledger requirements, single-book validation, or collection validation.

## 14. Validation Requirements

Before delivery, run:

```bash
python path/to/read-a-book-deeply/scripts/validate_collection_workspace.py "path/to/{Theme}-collection-{timestamp}" --skill-dir "path/to/read-a-book-deeply"
```

The validator checks collection structure, manifest fields, theme inference, orchestration settings, linked book paths, per-book status, accepted subagent artifacts, artifact validation reports, single-book validation results, top-level cleanliness, claims ledger presence, per-book cards, and collection prompt resources. Fix every issue before final delivery.
