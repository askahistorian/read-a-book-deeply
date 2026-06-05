# Read a Book Deeply

[![Install on skills.sh](https://skills.sh/b/askahistorian/read-a-book-deeply)](https://skills.sh/askahistorian/read-a-book-deeply/read-a-book-deeply)

**中文** | [English](README.en.md)

完整读完一本书，保留原书结构，并通过 A/B 对抗审稿生成忠实、可追溯的深度总结。

`read-a-book-deeply` 是一个面向严肃阅读任务的 Codex skill。它把上传的 EPUB、PDF、DOCX、Markdown、纯文本等书籍整理成干净的本地工作区，修复 EPUB 图片链接，校验图像与图表资产，然后按原书目录、章节和小标题生成完整深度总结。生成总结时，它必须优先尝试启动 A/B 双线程 subagent 对抗流程：Agent A 负责完整总结，Agent B 专门寻找遗漏、误读和过度概括，最后由 Orchestrator 仲裁并写出唯一正式总结；只有无法启动 subagent 时才使用 fallback 单线程自审路线。

## 安装

```bash
npx skills add askahistorian/read-a-book-deeply --skill read-a-book-deeply
```

然后对 Codex 说：

```text
使用 $read-a-book-deeply 读完这本 EPUB，并用中文生成忠实的深度总结；我明确授权你启动 subagents / 多代理对抗总结。
```

## 它会做什么

- 读取 EPUB、PDF、DOCX、Markdown、文本和其他书籍长度的输入。
- 为每本书创建规范工作区：`source/` 保存原始文件，`conversion/` 保存转换稿、图片、manifest 和章节材料。
- 使用 MarkItDown 与内置 EPUB 图片修复脚本生成 `conversion/book.md`。
- 在总结前校验 Markdown 图片链接，并标记缺失图片资产。
- 先识别体裁与子体裁，再决定总结重点。
- 严格跟随原书目录、章节、分节和小标题，不用自由主题聚类替代原书结构。
- 生成总结时优先启动双 agent 对抗流程：Agent A 起草覆盖稿，Agent B 审查遗漏与风险，Orchestrator 写出最终稿；仅无法启动 subagent 时才 fallback 到单线程自审。
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
    ├── image_manifest.md
    ├── images/
    └── chapters/
```

中文请求中，最终总结文件名可为 `书名-深度总结.md`。

## 内置资源

- `scripts/convert_book_with_assets.py`：使用 MarkItDown 转换书籍，并修复 EPUB 图片链接。
- `scripts/validate_book_workspace.py`：检查最终书籍工作区结构、必要 prompt 和图片链接完整性。
- `references/subagent-prompts/`：用于总结者、审稿者、交叉审查、回应与 Orchestrator 阶段的固定 prompt 模板。

## 隐私

这个 skill 本身不会发布、上传或传输用户书籍。它只定义本地工作流并提供本地脚本。任何后续发布或分享动作都必须由用户明确要求。
