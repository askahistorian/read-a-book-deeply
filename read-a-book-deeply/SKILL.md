---
name: read-a-book-deeply
description: Create faithful whole-book deep summaries from uploaded books and converted book manuscripts. Use when the user asks Codex to read, summarize, analyze, study, digest, or produce a deep summary of an EPUB, PDF, DOCX, Markdown, text, or other book-length file, especially when full chapter coverage, genre-aware analysis, image/figure preservation, adversarial subagent review, or a final written book summary is required. Also use for Chinese requests such as 深度总结, 读完这本书, 按章节总结, 书籍精读, and for multilingual book-summary workflows.
---

# Read A Book Deeply

## Purpose

Use this skill to turn an uploaded book into one faithful written deep summary. The workflow preserves the book's structure, repairs EPUB image links, uses an adversarial two-agent review when available, and stops after the written summary.

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
    ├── image_manifest.md
    ├── images/
    └── chapters/              optional
```

Rules:

- Put original uploaded files only in `source/`.
- Put conversion files only in `conversion/`.
- Normalize the main converted manuscript to `conversion/book.md`.
- Do not leave `source.md`, `source_with_real_images.md`, `image_manifest.md`, or `Image000xx.jpg` files at the book directory top level.
- Read Markdown as UTF-8.

## Convert The Book

Use `scripts/convert_book_with_assets.py` for EPUB and image-heavy files:

```bash
python path/to/read-a-book-deeply/scripts/convert_book_with_assets.py "source/original.epub" "conversion"
```

The script runs MarkItDown, extracts EPUB images into `conversion/images/`, rewrites Markdown image links, and writes `conversion/image_manifest.md`.

After conversion:

1. Move or copy the repaired manuscript to `conversion/book.md`.
2. Remove or archive intermediate files whose names contain `source` if they are no longer needed.
3. Check `conversion/image_manifest.md`; any `MISSING` entry must be fixed before summarizing.
4. If conversion already produced `source.md`, rerun with `--skip-convert` to repair assets without reconverting.

## Summarize With Adversarial Review

First identify the book's genre and subgenre. Use the book's own table of contents, chapters, and headings as the coverage skeleton.

Genre-specific emphasis:

- Nonfiction, academic, business/self-help, philosophy: central thesis, reasoning chain, evidence, concept framework, and the book's own limits.
- Fiction/literature: plot structure, character arcs, themes, narrative technique, imagery, and emotional tone.
- History, biography, memoir: historical context, key people, causal relationships, author viewpoint, and possible bias presented by the text.

When subagent tools are available and the current environment permits delegation, orchestrate the two-agent workflow with `fork_context=false` for the first round. Give both agents only `conversion/book.md`, optional `conversion/chapters/`, optional `conversion/image_manifest.md`, the output target, genre, quality standards, and user requirements. Never use files in `source/` as subagent input.

Use the bundled templates in `references/subagent-prompts/`:

- `agent-a-summarizer.md`: Agent A independently produces `summary_draft`, `coverage_ledger`, and `argument_map`.
- `agent-b-skeptic.md`: Agent B independently produces `adversarial_report`, `must_not_miss_list`, and `risk_register`.
- `b-critiques-a.md`: Agent B critiques Agent A after the independent first round.
- `a-responds-b.md`: Agent A responds with accepted, rejected, or revised items.
- `orchestrator-final.md`: Main thread arbitrates and writes the only final summary.

If isolated subagents are unavailable, fall back to a single-thread deep summary plus self-review, and state in the final quality note that isolated subagents were not used.

## Final Summary Requirements

The final written summary must:

- Cover every important chapter, section, and heading implied by the book structure.
- Stay faithful to the source; do not invent plot, arguments, quotations, page numbers, or author intent.
- Separate source content, summary synthesis, and interpretive judgment.
- Include critical evaluation only when the user explicitly asks for it, and label it separately.
- Prefer factual fidelity over style, chapter coverage over compression, and explicit evidence over speculation.

Only keep one final written summary at the book directory top level. Do not keep long final QA reports, agent drafts, critique logs, or intermediate review files unless the user explicitly asks for them.

## Validate Before Delivery

Run the bundled validator on the finished book directory:

```bash
python path/to/read-a-book-deeply/scripts/validate_book_workspace.py "path/to/{BookTitle}-{timestamp}" --skill-dir "path/to/read-a-book-deeply"
```

Fix every reported issue before delivering. In the conversation, provide only a concise quality note covering:

- Agent A and Agent B roles, or the fallback used.
- Key revisions made after review.
- Orchestrator arbitration result.
- Residual risks, if any.
