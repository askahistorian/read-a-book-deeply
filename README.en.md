# Read a Book Deeply

[![Install on skills.sh](https://skills.sh/b/askahistorian/read-a-book-deeply)](https://skills.sh/askahistorian/read-a-book-deeply/read-a-book-deeply)

[中文](README.md) | **English**

Read the whole book, preserve its structure, and produce a faithful deep summary with an adversarial second pass.

`read-a-book-deeply` is a Codex skill for serious book work. Uploaded books become clean local workspaces, EPUB images are unpacked and verified, the full manuscript is summarized by chapter, and subagent tools are attempted first for an A/B adversarial review before the final written summary is delivered. If the A/B agents cannot start, single-thread fallback requires explicit user authorization first.

## Prerequisites

This skill depends on the external `markitdown` (https://github.com/microsoft/markitdown) command for the base conversion from EPUB, PDF, DOCX, and similar files to Markdown. First make sure this command works on your machine:

```bash
markitdown --help
```

If the command is unavailable, install MarkItDown first, for example:

```bash
pip install markitdown
```

This skill does not bundle MarkItDown's core conversion logic. It calls the installed `markitdown` CLI, then repairs EPUB image links and creates `conversion/book.md` plus `image_manifest.md`.

## Install

```bash
npx skills add askahistorian/read-a-book-deeply --skill read-a-book-deeply
```

Then ask Codex:

```text
Use $read-a-book-deeply to read this EPUB and create a faithful deep summary in my language; I explicitly authorize you to start subagents / parallel agent work for the adversarial review.
```

You can also use it for thematic reading across several books. When multiple books are uploaded in one request, the skill treats them as one thematic reading collection. If you do not specify a theme, it first infers a provisional theme direction, then selects one final theme and two alternatives after every book has been independently summarized and validated.

```text
Use $read-a-book-deeply to read these 3 books around "modern state formation" and create a Chinese thematic reading report; I authorize subagents / parallel agent work.
```

## What It Does

- Reads EPUB, PDF, DOCX, Markdown, text, and other book-length inputs.
- Creates a disciplined book workspace with `source/` for originals and `conversion/` for manuscripts, images, manifests, and chapter material.
- Uses MarkItDown plus a bundled EPUB image repair script to produce `conversion/book.md`.
- Verifies Markdown image links and flags missing image assets before summarization.
- Identifies genre and subgenre before summarizing.
- Summarizes according to the book's actual table of contents, chapters, sections, and headings.
- Attempts the adversarial two-agent workflow first: Agent A drafts coverage, Agent B hunts for omissions and risks, then the Orchestrator writes the final summary. If the two-agent workflow cannot start, fallback is not automatic and requires explicit user authorization.
- Supports multi-book thematic reading: the main thread directly manages each book's conversion, image checks, concurrent A/B launch, artifact validation, arbitration, and validation; each book is completed and validated first, then a collection layer produces traceable comparison, disagreement analysis, concept matrix, claims ledger, and thematic report.
- Multi-book mode uses a concurrent artifact isolation protocol: every subagent attempt carries a unique `run_id`, `book_id`, `agent_id`, and `attempt_id`; long outputs are split into genre-compatible structured materials and validated before they enter the Orchestrator. Single-book mode is unchanged.
- If no theme is specified, the workflow starts with a provisional theme direction, then automatically selects a final reading theme and two alternatives after all single-book summaries are complete.
- Separates source content, summary synthesis, interpretive judgment, and critical evaluation, with labels localized to the output language.
- Includes critical evaluation only when the user explicitly requests it.

## Best For

- Academic books and monographs
- History, biography, memoir, and civilization studies
- Philosophy, religion, social science, and political thought
- Business, self-help, and practical nonfiction
- Fiction and literary works that need plot, character, theme, and narrative analysis
- Multilingual book workflows where the summary should follow the user's requested language

## Quality Promise

This skill is designed for faithful depth, not shortcut summaries.

- Whole-book coverage comes before compression.
- Factual fidelity comes before stylish prose.
- Explicit evidence comes before interpretation.
- Chapter structure comes before free-form topic clustering.
- Uncertain claims are labeled instead of inflated.
- User data stays local unless the user separately chooses to publish or upload it.

This repository contains only the skill and its reusable resources. It does not include user books, converted manuscripts, summaries, audio files, credentials, NotebookLM data, or environment files.

## Output Language

The final summary language follows this priority order:

1. The language explicitly requested by the user.
2. The language of the user's request.
3. English fallback.

For Chinese requests, the final summary filename may be `书名-深度总结.md`. For non-Chinese requests, the default filename is `Book Title - Deep Summary.md`.

## Output Shape

The skill creates one workspace per book:

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

Multi-book thematic reading adds a collection workspace, usually in linked mode, pointing back to the validated book workspaces. The collection top level keeps only one final thematic report; cross-book synthesis material, review notes, batch checkpoint/resume state, and the claims ledger stay under `synthesis/` or `collection_manifest.yaml`. It does not replace any single-book deep summary.

## Bundled Resources

- `scripts/convert_book_with_assets.py`: converts book files with MarkItDown and repairs EPUB image links.
- `scripts/checkpoint.py`: creates, atomically writes, and validates single-book checkpoints and collection resume fields.
- `scripts/validate_book_workspace.py`: checks final book workspace structure, required prompts, and image-link integrity.
- `scripts/validate_collection_workspace.py`: validates the thematic collection workspace, manifest, claims ledger, book links, and single-book validation results.
- `scripts/validate_subagent_artifact.py`: checks multi-book accepted subagent artifacts for sentinels, required structure, and cumulative-append corruption.
- `references/collection-mode.md`: detailed multi-book workflow, evidence levels, manifest, per-book card, and claims ledger rules.
- `references/checkpointing.md`: single-book and multi-book resume rules, authorization state, checkpoint fields, and validator contract.
- `references/subagent-prompts/`: fixed prompt templates for the summarizer, skeptic, cross-review, response, and Orchestrator stages.
- `references/subagent-prompts/agent-a-summarizer-multibook.md`, `agent-b-skeptic-multibook.md`, and `orchestrator-final-multibook.md`: per-book structured A/B materials and final single-book arbitration templates for multi-book mode.
- `references/subagent-prompts/agent-c-cross-book-synthesizer.md`, `agent-d-cross-book-skeptic.md`, and `orchestrator-collection-final.md`: templates for cross-book synthesis, cross-book skepticism, and final collection arbitration.

## Privacy

The skill itself does not publish, upload, or transmit user books. It only defines the local workflow and includes local scripts. Any future publishing or sharing action must be explicitly requested by the user.
