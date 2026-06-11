# Read a Book Deeply

[![Install on skills.sh](https://skills.sh/b/askahistorian/read-a-book-deeply)](https://skills.sh/askahistorian/read-a-book-deeply/read-a-book-deeply)

**中文** | [English](README.en.md)

一个用于严肃读书任务的 Codex skill：完整读完书籍，保留原书结构，修复图片资产，通过 A/B 对抗审稿和 Orchestrator 仲裁，生成忠实、可追溯的深度总结。

它适合你不想要“快速概览”，而是想让 Codex 按章节、论证、人物、事件、概念和证据认真读完整本书的场景。单书精读和多书主题共读都支持。

## 快速开始

本 skill 依赖外部 [`markitdown`](https://github.com/microsoft/markitdown) 命令完成 EPUB、PDF、DOCX 等格式到 Markdown 的基础转换。先确认本机可运行：

```bash
markitdown --help
```

如果命令不存在，可先安装 MarkItDown：

```bash
pip install markitdown
```

安装 skill：

```bash
npx skills add askahistorian/read-a-book-deeply --skill read-a-book-deeply
```

单书示例：

```text
使用 $read-a-book-deeply 读完这本 EPUB，并用中文生成忠实的深度总结；我明确授权你启动 subagents / 多代理对抗总结。
```

多书主题共读示例：

```text
使用 $read-a-book-deeply 围绕“现代国家形成”主题读这 3 本书，并生成中文主题共读报告；我授权你启动 subagents / 多代理。
```

如果没有明确授权 subagents，skill 会先询问。若 subagents 无法启动、环境禁止或用户拒绝授权，它不会自动降级到单线程自审；只有在用户明确授权本次 fallback 后才会继续。

## 适合什么任务

- 学术书、专著、论文式非虚构
- 历史、传记、回忆录、文明研究
- 哲学、宗教、社会科学、政治思想
- 商业、自助、方法论和实践类非虚构
- 需要情节、人物、主题、叙事技巧分析的小说和文学作品
- 多本书之间的主题共读、比较阅读、概念矩阵和阅读路径
- 需要按用户指定语言输出的多语言精读流程

## 它会做什么

1. 为每本书创建规范本地工作区，原始文件放入 `source/`，转换稿、图片、manifest、checkpoint 和工作材料放入 `conversion/`。
2. 调用 MarkItDown 完成基础转换，并用内置脚本修复 EPUB 图片链接，生成 `conversion/book.md` 和 `conversion/image_manifest.md`。
3. 写入 `conversion/checkpoint.yaml`，记录当前阶段、已完成文件、subagent 授权、fallback 授权、验证结果和残余风险，方便中断后恢复。
4. 按原书目录、章节、小标题和可识别结构阅读，不用自由主题聚类替代原书结构。
5. 优先启动 A/B 对抗审稿：Agent A 产出总结和结构材料，Agent B 查找遗漏、误读和风险，Orchestrator 仲裁并写唯一正式稿。
6. 在多书模式下，先逐本完成单书深读和验证，再创建 collection 层，生成主题共读报告、claims ledger、概念矩阵、分歧/互补分析和阅读路径。
7. 交付前运行 validator，检查工作区结构、图片链接、checkpoint/manifest、subagent artifact 和 collection 规则。

## 输出语言

最终总结语言按以下优先级决定：

1. 用户明确指定的语言
2. 用户提问语言
3. 请求语言不明确时使用英文

中文单书请求默认使用 `书名-深度总结.md`。非中文单书请求默认使用 `{Book Title} - Deep Summary.md`，除非用户指定文件名。

中文多书主题共读默认使用 `主题共读报告.md`。非中文多书主题共读默认使用 `{Theme} - Thematic Reading Report.md`，除非用户指定文件名。

正文会区分并本地化这些概念：

- 原书内容：书中实际写了什么
- 总结综合：对原书内容的压缩整理
- 解释性判断：基于原书的明确推断
- 批判性评价：仅在用户明确要求批评/评价时单独加入

## 输出结构

单书工作区：

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

中文请求中，顶层最终总结也可以是 `书名-深度总结.md`。

多书主题共读会额外生成 collection 工作区，默认使用 linked 模式指向已验证的单书工作区：

```text
Theme-collection-YYYYMMDD-HHMMSS/
├── collection_manifest.yaml
├── 主题共读报告.md
└── synthesis/
    ├── inputs/
    ├── claims_ledger.md
    ├── concept_matrix.md
    ├── agreement_disagreement_map.md
    ├── reading_path.md
    └── review/
```

collection 顶层只保留一个主题共读报告。横向综合材料、审稿记录、checkpoint/resume 状态和 claims ledger 留在 `synthesis/` 或 `collection_manifest.yaml` 中。

## 恢复与验证

单书恢复状态保存在：

```text
conversion/checkpoint.yaml
```

多书恢复状态保存在：

```text
collection_manifest.yaml
```

如果 checkpoint 或 manifest 缺失、损坏、和实际文件冲突，或者记录显示 fallback 需要授权但尚未授权，skill 会停止并询问用户，不会偷偷选择另一条降级路线。

单书验证命令：

```bash
python path/to/read-a-book-deeply/scripts/validate_book_workspace.py "path/to/{BookTitle}-{timestamp}" --skill-dir "path/to/read-a-book-deeply"
```

多书 collection 验证命令：

```bash
python path/to/read-a-book-deeply/scripts/validate_collection_workspace.py "path/to/{Theme}-collection-{timestamp}" --skill-dir "path/to/read-a-book-deeply"
```

## 质量原则

- 完整阅读优先于压缩。
- 事实忠实优先于漂亮文风。
- 明确证据优先于解释发挥。
- 章节结构优先于自由归纳。
- 不确定内容会标注为待复核或残余风险。
- 批判性评价只在用户明确要求时出现。
- fallback 需要用户明确授权，不能隐式发生。

## 内置资源

- `scripts/convert_book_with_assets.py`：调用 MarkItDown 转换书籍，并修复 EPUB 图片链接。
- `scripts/checkpoint.py`：创建、原子写入并校验单书 checkpoint 与 collection resume 字段。
- `scripts/validate_book_workspace.py`：检查单书工作区结构、图片链接、checkpoint 和必要 prompt。
- `scripts/validate_collection_workspace.py`：检查 collection 工作区、manifest、resume、claims ledger、单书链接和 collection 规则。
- `scripts/validate_subagent_artifact.py`：检查多书模式 accepted subagent artifact 的 sentinel、必需结构和重复/追加污染。
- `references/checkpointing.md`：单书与多书恢复、授权状态、checkpoint 字段和 validator 契约。
- `references/collection-mode.md`：多书主题共读、证据等级、manifest、per-book card 和 claims ledger 规范。
- `references/subagent-prompts/`：Agent A/B/C/D 与 Orchestrator 的 prompt 模板。

## 隐私与边界

这个 skill 本身不会发布、上传或传输用户书籍。它只定义本地工作流并提供本地脚本。任何发布、上传、音频生成、NotebookLM、API key、云同步等动作都不属于本 skill 的默认目标，必须由用户另行明确要求。

本仓库只包含 skill 与可复用资源，不包含任何用户书籍、转换稿、总结、音频、凭据、NotebookLM 数据或环境文件。
