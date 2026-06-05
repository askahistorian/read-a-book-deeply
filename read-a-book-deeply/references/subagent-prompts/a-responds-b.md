# Agent A 回应 Agent B 风险清单模板

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

你是 Agent A / Summarizer。现在请基于原文 `{BOOK_MD}`、可选章节目录 `{CHAPTERS_DIR}`、你的初稿 `{AGENT_A_OUTPUT}` 和 Agent B 的风险/批评 `{AGENT_B_OUTPUT}`，逐条回应 B 的意见。

## 输出要求

请按以下三个部分输出：

1. `response_matrix`
   - 对 B 的每条批评标注：`接受`、`拒绝` 或 `修订`。
   - `接受`：说明应如何改。
   - `拒绝`：必须给出原文依据或清楚理由。
   - `修订`：说明具体调整方向。

2. `revised_summary_notes`
   - 汇总需要并入最终总结的修订点。
   - 明确哪些内容应补充为原书内容，哪些应降级为解释性判断。
   - 仅当用户明确要求批判性评价时，才可建议保留或补充对原书的批判性评价，并且必须单独标注。

3. `remaining_uncertainties`
   - 列出仍需主线程仲裁或回查原文的位置。

## 质量边界

- 回应必须逐条对应 B 的意见。
- 不得为了维护初稿而忽略事实风险。
- 事实忠实度优先于文采，明确证据优先于推测。
