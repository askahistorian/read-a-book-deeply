# Read a Book Deeply

[![Install on skills.sh](https://skills.sh/b/askahistorian/read-a-book-deeply)](https://skills.sh/askahistorian/read-a-book-deeply/read-a-book-deeply)

[中文](README.md) | **English**

A Codex skill for serious reading work: read the whole book, preserve the book's own structure, repair image assets, use A/B adversarial review plus Orchestrator arbitration, and produce a faithful, traceable deep summary.

Use it when you do not want a quick overview, but want Codex to read the full book by chapter, argument, character, event, concept, and evidence. It supports both single-book deep reading and multi-book thematic reading.

## Quick Start

This skill depends on the external [`markitdown`](https://github.com/microsoft/markitdown) command for base conversion from EPUB, PDF, DOCX, and similar formats to Markdown. First make sure it works locally:

```bash
markitdown --help
```

If the command is unavailable, install MarkItDown first:

```bash
pip install markitdown
```

Install the skill:

```bash
npx skills add askahistorian/read-a-book-deeply --skill read-a-book-deeply
```

Single-book example:

```text
Use $read-a-book-deeply to read this EPUB and create a faithful deep summary in Chinese; I explicitly authorize you to start subagents / parallel agent work for the adversarial review.
```

Multi-book thematic reading example:

```text
Use $read-a-book-deeply to read these 3 books around "modern state formation" and create a Chinese thematic reading report; I authorize subagents / parallel agent work.
```

If subagents are not explicitly authorized, the skill will ask first. If subagents cannot start, the environment forbids them, or the user declines authorization, the workflow will not silently downgrade to single-thread self-review; it continues only after the user explicitly authorizes fallback for that run.

## Best For

- Academic books, monographs, and argument-heavy nonfiction
- History, biography, memoir, and civilization studies
- Philosophy, religion, social science, and political thought
- Business, self-help, methodology, and practical nonfiction
- Fiction and literary works that need plot, character, theme, and narrative-technique analysis
- Thematic reading, comparison, concept matrices, and reading paths across multiple books
- Multilingual deep-reading workflows where output should follow the user's requested language

## What It Does

1. Creates a disciplined local workspace for each book: originals in `source/`; converted manuscript, images, manifest, checkpoint, and working materials in `conversion/`.
2. Calls MarkItDown for base conversion, then uses the bundled repair script to fix EPUB image links and produce `conversion/book.md` plus `conversion/image_manifest.md`.
3. Writes `conversion/checkpoint.yaml` with the current phase, completed files, subagent authorization, fallback authorization, validation result, and residual risks so interrupted work can resume.
4. Reads according to the book's table of contents, chapters, headings, and recognizable structure instead of replacing the book with free-form topic clusters.
5. Attempts A/B adversarial review first: Agent A produces summary and structure material, Agent B searches for omissions, misreadings, and risks, and the Orchestrator arbitrates and writes the only final summary.
6. In multi-book mode, completes and validates every single-book workflow first, then builds a collection layer with a thematic report, claims ledger, concept matrix, agreement/disagreement analysis, complementarities, and reading path.
7. Runs validators before delivery to check workspace shape, image links, checkpoint/manifest state, subagent artifacts, and collection rules.

## Output Language

The final summary language follows this priority order:

1. The language explicitly requested by the user.
2. The language of the user's request.
3. English when the request language is unclear.

For Chinese single-book requests, the default final filename is `书名-深度总结.md`. For non-Chinese single-book requests, the default is `{Book Title} - Deep Summary.md`, unless the user asks for a specific filename.

For Chinese multi-book thematic reading, the default final report filename is `主题共读报告.md`. For non-Chinese multi-book thematic reading, the default is `{Theme} - Thematic Reading Report.md`, unless the user asks for a specific filename.

The summary labels and localizes these concepts:

- Source content: what the book itself says.
- Summary synthesis: compressed organization of the source content.
- Interpretive judgment: a clearly marked inference from the book.
- Critical evaluation: included only when the user explicitly asks for critique or evaluation.

## Output Shape

Single-book workspace:

```text
BookTitle-YYYYMMDD-HHMMSS/
├── Book Title - Deep Summary.md
├── source/
│   └── original uploaded book
└── conversion/
    ├── book.md
    ├── checkpoint.yaml
    ├── image_manifest.md
    ├── images/
    └── chapters/              optional
```

For Chinese requests, the top-level final summary may be `书名-深度总结.md`.

Multi-book thematic reading also creates a collection workspace, usually in linked mode pointing back to validated single-book workspaces:

```text
Theme-collection-YYYYMMDD-HHMMSS/
├── collection_manifest.yaml
├── Theme - Thematic Reading Report.md
└── synthesis/
    ├── inputs/
    ├── claims_ledger.md
    ├── concept_matrix.md
    ├── agreement_disagreement_map.md
    ├── reading_path.md
    └── review/
```

The collection top level keeps only one final thematic report. Cross-book synthesis materials, review notes, checkpoint/resume state, and the claims ledger stay under `synthesis/` or `collection_manifest.yaml`.

## Resume And Validate

Single-book recovery state lives in:

```text
conversion/checkpoint.yaml
```

Multi-book recovery state lives in:

```text
collection_manifest.yaml
```

If the checkpoint or manifest is missing, malformed, inconsistent with actual files, or says fallback authorization is required but not yet authorized, the skill stops and asks the user what to do. It does not silently choose another downgrade path.

Validate a single-book workspace:

```bash
python path/to/read-a-book-deeply/scripts/validate_book_workspace.py "path/to/{BookTitle}-{timestamp}" --skill-dir "path/to/read-a-book-deeply"
```

Validate a multi-book collection:

```bash
python path/to/read-a-book-deeply/scripts/validate_collection_workspace.py "path/to/{Theme}-collection-{timestamp}" --skill-dir "path/to/read-a-book-deeply"
```

## Quality Principles

- Whole-book reading comes before compression.
- Factual fidelity comes before polished prose.
- Explicit evidence comes before interpretation.
- Chapter structure comes before free-form synthesis.
- Uncertain content is labeled as pending review or residual risk.
- Critical evaluation appears only when the user explicitly asks for it.
- Fallback requires explicit user authorization and cannot happen implicitly.

## Bundled Resources

- `scripts/convert_book_with_assets.py`: calls MarkItDown and repairs EPUB image links.
- `scripts/checkpoint.py`: creates, atomically writes, and validates single-book checkpoints and collection resume fields.
- `scripts/validate_book_workspace.py`: checks single-book workspace shape, image links, checkpoint state, and required prompts.
- `scripts/validate_collection_workspace.py`: checks collection workspace shape, manifest, resume state, claims ledger, linked books, and collection rules.
- `scripts/validate_subagent_artifact.py`: checks multi-book accepted subagent artifacts for sentinels, required structure, and repeated/append-style corruption.
- `references/checkpointing.md`: recovery rules, authorization state, checkpoint fields, and validator contract for single-book and multi-book work.
- `references/collection-mode.md`: multi-book thematic reading, evidence levels, manifest, per-book cards, and claims ledger rules.
- `references/subagent-prompts/`: prompt templates for Agent A/B/C/D and Orchestrator stages.

## Privacy And Boundaries

The skill itself does not publish, upload, or transmit user books. It only defines the local workflow and includes local scripts. Publishing, uploading, audio generation, NotebookLM, API keys, cloud sync, and similar actions are outside the default scope of this skill and require a separate explicit user request.

This repository contains only the skill and reusable resources. It does not include user books, converted manuscripts, summaries, audio files, credentials, NotebookLM data, or environment files.
