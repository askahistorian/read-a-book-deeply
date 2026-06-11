---
name: read-a-book-deeply
description: Create faithful whole-book deep summaries from uploaded books and converted book manuscripts. Use when the user asks Codex to read, summarize, analyze, study, digest, or produce a deep summary of an EPUB, PDF, DOCX, Markdown, text, or other book-length file, especially when full chapter coverage, genre-aware analysis, image/figure preservation, adversarial subagent review, or a final written book summary is required. Also use for Chinese requests such as 深度总结, 读完这本书, 按章节总结, 书籍精读, and for multilingual book-summary workflows.
---

# Read A Book Deeply

## Purpose

Use this skill to turn an uploaded book into one faithful written deep summary. The workflow preserves the book's structure, repairs EPUB image links, requires an adversarial two-agent subagent review attempt before summarizing, and stops after the written summary.

Do not add audio generation, narration scripts, API-key handling, or any continuation beyond the written deep summary.

## Output Language

Choose the final summary language in this order:

1. The language explicitly requested by the user.
2. The language of the user's request.
3. English if the request language is unclear.

For Chinese requests, keep the final filename as `书名-深度总结.md`. For non-Chinese requests, use `{Book Title} - Deep Summary.md` unless the user requests a filename.

Use localized section labels for these concepts while preserving their meaning:

- Source content: what the book itself says.
- Summary synthesis: the agent's compressed synthesis of the book.
- Interpretive judgment: a clearly labeled inference from the book.
- Critical evaluation: only include this when the user explicitly requests critique.

## Required Workspace Shape

Create one directory per book using `{BookTitle}-{timestamp}`. Keep the top level clean:

```text
{BookTitle}-{timestamp}/
├── {BookTitle}-深度总结.md or {Book Title} - Deep Summary.md
├── source/
│   └── original uploaded book
└── conversion/
    ├── book.md
    ├── checkpoint.yaml
    ├── image_manifest.md
    ├── images/
    └── chapters/              optional
```

Rules:

- Put original uploaded files only in `source/`.
- Put conversion files only in `conversion/`.
- Normalize the main converted manuscript to `conversion/book.md`.
- Create and update `conversion/checkpoint.yaml`; it is the single-book recovery record.
- Do not leave `source.md`, `source_with_real_images.md`, `image_manifest.md`, or `Image000xx.jpg` files at the book directory top level.
- Read Markdown as UTF-8.

## Resume From Checkpoint

Before starting new work, inspect the target directory for an existing book workspace or collection workspace. Recovery state is authoritative in `conversion/checkpoint.yaml` for a single book and `collection_manifest.yaml` for a multi-book collection.

Follow `references/checkpointing.md` for checkpoint fields, phase names, authorization state, atomic writes, and resume rules. If checkpoint state is missing, malformed, conflicts with the actual files, or says fallback authorization is required but not authorized, stop and ask the user how to proceed. Do not infer a hidden fallback path.

## Convert The Book

Use `scripts/convert_book_with_assets.py` for EPUB and image-heavy files:

```bash
python path/to/read-a-book-deeply/scripts/convert_book_with_assets.py "source/original.epub" "conversion"
```

The script runs MarkItDown, extracts EPUB images into `conversion/images/`, rewrites Markdown image links, writes `conversion/image_manifest.md`, and initializes `conversion/checkpoint.yaml`.

After conversion:

1. Move or copy the repaired manuscript to `conversion/book.md`.
2. Do not create top-level intermediate artifacts. Keep converted source drafts, repair outputs, manifests, agent drafts, review notes, QA notes, and other working files inside `conversion/`.
3. Check `conversion/image_manifest.md`; any `MISSING` entry must be fixed before summarizing.
4. If conversion already produced `source.md`, rerun with `--skip-convert` to repair assets without reconverting.

Use `conversion/_work/` or `conversion/review/` for intermediate material that needs to exist after the run. Delivery does not require deleting internal `conversion/` working files; the requirement is that the book directory top level stays clean.

## Summarize With Adversarial Review

First identify the book's genre and subgenre. Use the book's own table of contents, chapters, and headings as the coverage skeleton.

Genre-specific emphasis:

- Nonfiction, academic, business/self-help, philosophy: central thesis, reasoning chain, evidence, concept framework, and the book's own limits.
- Fiction/literature: plot structure, character arcs, themes, narrative technique, imagery, and emotional tone.
- History, biography, memoir: historical context, key people, causal relationships, author viewpoint, and possible bias presented by the text.

After conversion and image-link validation, attempt to start subagent tools before writing the final summary. The first summarization pass must use the two-agent workflow with `fork_context=false` whenever delegation can start. Give both agents only `conversion/book.md`, optional `conversion/chapters/`, optional `conversion/image_manifest.md`, the output target, genre, quality standards, and user requirements. Never use files in `source/` as subagent input.

If subagent tools are available but their tool policy requires explicit user authorization, use this authorization handshake before summarizing:

1. If the current user request already explicitly authorizes `subagents`, `多代理`, `parallel agent work`, or equivalent delegated agent work, start the two-agent workflow immediately without asking again.
2. If the current user request does not explicitly authorize subagents, ask the user for explicit authorization before summarizing. The authorization request must mention `subagents` or `多代理` plainly.
3. If the user declines authorization, or if authorization cannot be obtained, do not fall back automatically. Ask whether the user explicitly authorizes a single-thread fallback.

Use fallback only when subagent tools are absent, the current environment forbids delegation, the user does not authorize subagents, or a concrete attempt to start subagents fails, and only after the user explicitly authorizes single-thread fallback for that run. Do not begin a single-thread deep summary until that fallback authorization is received.

Use the bundled templates in `references/subagent-prompts/`:

- `agent-a-summarizer.md`: Agent A independently produces `summary_draft`, `coverage_ledger`, and `argument_map`.
- `agent-b-skeptic.md`: Agent B independently produces `adversarial_report`, `must_not_miss_list`, and `risk_register`.
- `b-critiques-a.md`: Agent B critiques Agent A after the independent first round.
- `a-responds-b.md`: Agent A responds with accepted, rejected, or revised items.
- `orchestrator-final.md`: Main thread arbitrates and writes the only final summary.

If fallback is explicitly authorized by the user, use a single-thread deep summary plus self-review. In the final quality note, state whether Agent A and Agent B were launched, or give the specific fallback reason: user did not authorize subagents, subagent tools were unavailable, the environment forbade delegation, or subagent launch failed after a concrete attempt. Also state that the user explicitly authorized single-thread fallback for that run.

## Multi-book / Thematic Reading Mode

Use multi-book thematic reading mode whenever the user uploads or asks to read multiple books in one request. Treat the batch as one thematic reading collection. If the user gives a theme, use it as the collection theme. If not, infer a provisional theme direction and record it in `collection_manifest.yaml`; do not replace single-book chapter coverage with theme clustering.

Run the single-book standard independently for every book. The main thread owns source placement, conversion, image validation, per-book A/B launch or queueing, artifact validation, Orchestrator arbitration, checkpoint updates, validation, final theme selection, collection synthesis, and delivery. Do not create a Book Worker subagent or ask any subagent to launch other subagents.

Detailed collection workspace rules, manifest/checkpoint schema, subagent artifact protocol, Agent C/D roles, fallback rules, evidence levels, claims ledger, and validation requirements are in `references/collection-mode.md`. Checkpoint/resume rules are in `references/checkpointing.md`. Before delivery, run:

```bash
python path/to/read-a-book-deeply/scripts/validate_collection_workspace.py "path/to/{Theme}-collection-{timestamp}" --skill-dir "path/to/read-a-book-deeply"
```

## Final Summary Requirements

The final written summary must:

- Cover every important chapter, section, and heading implied by the book structure.
- Stay faithful to the source; do not invent plot, arguments, quotations, page numbers, or author intent.
- Separate source content, summary synthesis, and interpretive judgment.
- Include critical evaluation only when the user explicitly asks for it, and label it separately.
- Prefer factual fidelity over style, chapter coverage over compression, and explicit evidence over speculation.

Only keep one final written summary at the book directory top level. Do not write long final QA reports, agent drafts, critique logs, or intermediate review files at the book directory top level unless the user explicitly asks for them. If those materials need to be retained, keep them inside `conversion/_work/` or `conversion/review/`.

## Validate Before Delivery

Run the bundled validator on the finished book directory:

```bash
python path/to/read-a-book-deeply/scripts/validate_book_workspace.py "path/to/{BookTitle}-{timestamp}" --skill-dir "path/to/read-a-book-deeply"
```

Fix every reported issue before delivering. In the conversation, provide only a concise quality note covering:

- Agent A and Agent B roles, or the fallback reason and self-review route used.
- Key revisions made after review.
- Orchestrator arbitration result.
- Residual risks, if any.
