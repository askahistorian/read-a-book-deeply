# Read a Book Deeply

[![Install on skills.sh](https://skills.sh/b/askahistorian/read-a-book-deeply)](https://skills.sh/askahistorian/read-a-book-deeply/read-a-book-deeply)

**中文** | [English](README.en.md)

完整读完一本书，保留原书结构，并通过 A/B 对抗审稿生成忠实、可追溯的深度总结。

`read-a-book-deeply` 是一个面向严肃阅读任务的 Codex skill。它把上传的 EPUB、PDF、DOCX、Markdown、纯文本等书籍整理成干净的本地工作区，修复 EPUB 图片链接，校验图像与图表资产，然后按原书目录、章节和小标题生成完整深度总结。生成总结时，它必须优先尝试启动 A/B 双线程 subagent 对抗流程：Agent A 负责完整总结，Agent B 专门寻找遗漏、误读和过度概括，最后由 Orchestrator 仲裁并写出唯一正式总结；如果双 agent 无法启动，必须先获得用户明确授权，才可改用单线程自审 fallback。

## 前置条件

本 skill 依赖外部 `markitdown` (https://github.com/microsoft/markitdown) 命令完成 EPUB、PDF、DOCX 等文件到 Markdown 的基础转换。请先确保本机可以运行：

```bash
markitdown --help
```

如果命令不存在，请先安装 MarkItDown，例如：

```bash
pip install markitdown
```

本 skill 不内置 MarkItDown 的核心转换能力；它会调用已安装的 `markitdown` CLI，并在此基础上修复 EPUB 图片链接、生成 `conversion/book.md` 与 `image_manifest.md`。

## 安装

```bash
npx skills add askahistorian/read-a-book-deeply --skill read-a-book-deeply
```

然后对 Codex 说：

```text
使用 $read-a-book-deeply 读完这本 EPUB，并用中文生成忠实的深度总结；我明确授权你启动 subagents / 多代理对抗总结。
```

也可以用于多书主题共读。一次上传多本书时，skill 会自动视为同主题共读；如果你没有指定主题，它会先判断一个临时主题方向，等每本书独立深读和验证完成后，再自动选出正式主题与两个备选主题。

```text
使用 $read-a-book-deeply 围绕“现代国家形成”主题读这 3 本书，并生成中文主题共读报告；我授权你启动 subagents / 多代理。
```

## 它会做什么

- 读取 EPUB、PDF、DOCX、Markdown、文本和其他书籍长度的输入。
- 为每本书创建规范工作区：`source/` 保存原始文件，`conversion/` 保存转换稿、图片、manifest 和章节材料。
- 使用 MarkItDown 与内置 EPUB 图片修复脚本生成 `conversion/book.md`。
- 在总结前校验 Markdown 图片链接，并标记缺失图片资产。
- 先识别体裁与子体裁，再决定总结重点。
- 严格跟随原书目录、章节、分节和小标题，不用自由主题聚类替代原书结构。
- 生成总结时优先启动双 agent 对抗流程：Agent A 起草覆盖稿，Agent B 审查遗漏与风险，Orchestrator 写出最终稿；双 agent 无法启动时，不会自动降级，必须先由用户明确授权单线程自审 fallback。
- 支持多书主题共读：主线程直接管理每本书的转换、图片校验、并发 A/B 启动、artifact 校验、仲裁和验证；先逐本完成并验证单书深读，再在集合层生成可追溯的比较、分歧分析、概念矩阵、claims ledger 和主题共读报告。
- 多书模式使用并发 artifact 隔离协议：每个 subagent attempt 都带有唯一 `run_id`、`book_id`、`agent_id` 和 `attempt_id`，长输出先拆成体裁兼容的结构化材料，通过校验后才进入 Orchestrator；单书模式逻辑不变。
- 未指定主题时，先生成临时主题方向；所有单书总结完成后，自动生成正式共读主题和两个备选主题。
- 区分“原书内容”“总结综合”“解释性判断”“批判性评价”等质量标签，并按输出语言本地化。
- 只有当用户明确要求时，才生成批判性评价。

## 适合这些书

- 学术书与专著
- 历史、传记、回忆录、文明研究
- 哲学、宗教、社会科学、政治思想
- 商业、自助、实践类非虚构
- 需要情节、人物、主题与叙事分析的小说和文学作品
- 需要按用户语言输出的多语言书籍精读流程

## 质量承诺

这个 skill 追求的是忠实的深度，而不是快捷的概览。

- 完整阅读优先于压缩。
- 事实忠实优先于漂亮文风。
- 明确证据优先于解释发挥。
- 章节结构优先于自由归纳。
- 不确定内容会被标注，不会被包装成确定结论。
- 用户数据默认留在本地，除非用户另行明确要求发布或上传。

本仓库只包含 skill 与可复用资源，不包含任何用户书籍、转换稿、总结、音频、凭据、NotebookLM 数据或环境文件。

## 输出语言

最终总结语言遵循固定优先级：

1. 用户明确指定的语言
2. 用户提问语言
3. 英文 fallback

中文用户默认可得到熟悉的 `书名-深度总结.md` 文件名。非中文用户默认使用 `Book Title - Deep Summary.md`。

## 输出结构

每本书会生成一个独立工作区：

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

中文请求中，最终总结文件名可为 `书名-深度总结.md`。

多书主题共读会额外生成一个 collection 工作区，默认使用 linked 模式指向已验证的单书工作区。collection 顶层只保留一个主题共读报告，横向综合材料、审稿记录、批量 checkpoint/resume 状态和 claims ledger 留在 `synthesis/` 或 `collection_manifest.yaml` 中；它不会替代任何单书深度总结。

## 内置资源

- `scripts/convert_book_with_assets.py`：使用 MarkItDown 转换书籍，并修复 EPUB 图片链接。
- `scripts/checkpoint.py`：创建、原子写入并校验单书 checkpoint 与 collection resume 字段。
- `scripts/validate_book_workspace.py`：检查最终书籍工作区结构、必要 prompt 和图片链接完整性。
- `scripts/validate_collection_workspace.py`：检查多书主题共读 collection 工作区、manifest、claims ledger、逐书链接和单书验证结果。
- `scripts/validate_subagent_artifact.py`：检查多书模式 accepted subagent artifact 的 sentinel、必需结构和 cumulative-append corruption。
- `references/collection-mode.md`：多书主题共读的详细工作流、证据等级、manifest、per-book card 和 claims ledger 规范。
- `references/checkpointing.md`：单书与多书中断恢复、授权状态、checkpoint 字段和 validator 契约。
- `references/subagent-prompts/`：用于总结者、审稿者、交叉审查、回应与 Orchestrator 阶段的固定 prompt 模板。
- `references/subagent-prompts/agent-a-summarizer-multibook.md`、`agent-b-skeptic-multibook.md`、`orchestrator-final-multibook.md`：多书模式逐书 A/B 结构化材料和单书最终仲裁模板。
- `references/subagent-prompts/agent-c-cross-book-synthesizer.md`、`agent-d-cross-book-skeptic.md`、`orchestrator-collection-final.md`：多书横向综合、横向审查和集合最终仲裁模板。

## 隐私

这个 skill 本身不会发布、上传或传输用户书籍。它只定义本地工作流并提供本地脚本。任何后续发布或分享动作都必须由用户明确要求。
