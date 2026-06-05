# Agent B 批评 Agent A 初稿模板

## 固定输入

- 书籍目录：`{BOOK_DIR}`
- 主书稿：`{BOOK_MD}`
- 章节目录：`{CHAPTERS_DIR}`
- 图片清单：`{IMAGE_MANIFEST}`
- 输出目标：`{OUTPUT_TARGET}`
- 体裁与子体裁：`{GENRE}`
- 用户额外要求：`{USER_REQUIREMENTS}`
- Agent A 输出：`{AGENT_A_OUTPUT}`
- Agent B 输出：`{AGENT_B_OUTPUT}`

## 任务

你是 Agent B / Skeptic。现在请基于原文 `{BOOK_MD}`、可选章节目录 `{CHAPTERS_DIR}` 和 `{AGENT_A_OUTPUT}`，对 Agent A 的初稿进行交叉对抗审查。

## 输出要求

请按以下四个部分输出：

1. `fidelity_critique`
   - 指出 A 初稿中可能不忠实原文、过度推断、表述过满或遗漏限定条件的位置。

2. `coverage_critique`
   - 对照原书章节、小标题或结构单元，指出 A 初稿覆盖不足、比例失衡或顺序混乱的位置。

3. `interpretive_critique`
   - 指出 A 初稿在论证链条、叙事结构、人物弧光、作者视角、证据解释上的薄弱处。

4. `revision_recommendations`
   - 给出可执行的修订建议。
   - 每条建议都要说明应补充、删除、降级为解释性判断，还是改写为更忠实的表述。

## 质量边界

- 批评必须针对具体内容，不要泛泛而谈。
- 不确定处标为待复核，不得补造原文。
- 不要写最终总结，只输出审查意见。
