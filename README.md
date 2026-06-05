# Read a Book Deeply

[![Install on skills.sh](https://skills.sh/b/askahistorian/read-a-book-deeply)](https://skills.sh/askahistorian/read-a-book-deeply)

Read the whole book, preserve its structure, and produce a faithful deep summary with an adversarial second pass.

`read-a-book-deeply` is a Codex skill for serious book work: uploaded books become clean source/conversion workspaces, EPUB images are unpacked and verified, the full manuscript is summarized by chapter, and an A/B adversarial review helps catch omissions before the final written summary is delivered.

## Install

```bash
npx skills add askahistorian/read-a-book-deeply --skill read-a-book-deeply
```

Then ask Codex:

```text
Use $read-a-book-deeply to read this EPUB and create a faithful deep summary in my language.
```

## What It Does

- Reads EPUB, PDF, DOCX, Markdown, text, and other book-length inputs.
- Creates a disciplined book workspace with `source/` for originals and `conversion/` for manuscripts, images, manifests, and chapter material.
- Uses MarkItDown plus a bundled EPUB image repair script to produce `conversion/book.md`.
- Verifies Markdown image links and flags missing image assets before summarization.
- Identifies genre and subgenre before summarizing.
- Summarizes according to the book's actual table of contents, chapters, sections, and headings.
- Runs an adversarial two-agent workflow when subagents are available: Agent A drafts coverage, Agent B hunts for omissions and risks, then the orchestrator writes the final summary.
- Separates source content, summary synthesis, interpretive judgment, and critical evaluation.
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

## Chinese 简介

`read-a-book-deeply` 用于把上传书籍完整读完并生成忠实的深度总结。它会先整理 `source/` 与 `conversion/` 目录，转换 EPUB/PDF/DOCX/Markdown 等书稿，修复 EPUB 图片链接，再按原书目录、章节和小标题逐级总结。若当前 Codex 环境支持 subagent，它会使用 A/B 双线程对抗流程：A 负责完整总结，B 专门寻找遗漏、误读和过度概括，最后由主线程仲裁生成唯一正式总结。

默认输出语言遵循：

1. 用户明确指定的语言
2. 用户提问语言
3. 英文 fallback

中文用户仍可得到熟悉的 `书名-深度总结.md` 文件名和中文总结结构。

## Output Shape

The skill creates one workspace per book:

```text
BookTitle-YYYYMMDD-HHMMSS/
├── Book Title - Deep Summary.md
├── source/
│   └── original uploaded book
└── conversion/
    ├── book.md
    ├── image_manifest.md
    ├── images/
    └── chapters/
```

For Chinese requests, the final summary filename may be `书名-深度总结.md`.

## Bundled Resources

- `scripts/convert_book_with_assets.py`: converts book files with MarkItDown and repairs EPUB image links.
- `scripts/validate_book_workspace.py`: checks final book workspace structure, required prompts, and image-link integrity.
- `references/subagent-prompts/`: fixed prompt templates for the summarizer, skeptic, cross-review, response, and orchestrator stages.

## Privacy

The skill itself does not publish, upload, or transmit user books. It only defines the local workflow and includes local scripts. Any future publishing or sharing action must be explicitly requested by the user.
