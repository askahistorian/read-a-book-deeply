# Orchestrator 多书模式单书最终仲裁模板

## 固定输入

- 书籍目录：`{BOOK_DIR}`
- 主书稿：`{BOOK_MD}`
- 章节目录：`{CHAPTERS_DIR}`
- 图片清单：`{IMAGE_MANIFEST}`
- 输出目标：`{OUTPUT_TARGET}`
- 体裁与子体裁：`{GENRE}`
- 用户额外要求：`{USER_REQUIREMENTS}`
- 集合 manifest：`{COLLECTION_MANIFEST}`
- Agent A accepted artifact：`{AGENT_A_ACCEPTED_ARTIFACT}`
- Agent B accepted artifact：`{AGENT_B_ACCEPTED_ARTIFACT}`
- artifact 校验记录：`{ARTIFACT_VALIDATION_REPORTS}`

本模板只用于多书主题共读模式中“逐书最终总结”阶段。单书模式继续使用 `orchestrator-final.md`。

## 任务

你是主线程 Orchestrator。请基于 `{BOOK_MD}`、可选的 `{CHAPTERS_DIR}`、Agent A 的 accepted 结构化总结材料、Agent B 的 accepted 结构化风险材料和 artifact 校验记录，仲裁并生成唯一正式单书总结产物：`{OUTPUT_TARGET}`。

多书模式下，A/B 的长输出已拆成结构化材料；这不降低最终总结质量。你必须直接回查原文并完整覆盖原书结构，不得把 A/B 材料当作原文替代品。

## 仲裁原则

- 事实忠实度优先于文采。
- 章节覆盖优先于压缩表达。
- 明确证据优先于推测。
- 原书内容、总结归纳和解释性判断必须区分。
- 除非用户额外要求中明确要求批判性评价，不得生成对原书的批判性评价；若用户明确要求，必须将批判性评价单独标注。
- 若 A 与 B 冲突，以原文为准；无法确认的内容标为残余风险，不写成确定事实。
- 若 artifact 校验记录显示某个 attempt 被 quarantine，禁止使用该 attempt 作为仲裁输入。

## 正式总结要求

- 使用 `SKILL.md` 的输出语言优先级：用户明确指定语言优先，其次使用用户请求语言，请求语言不明时使用英文。
- 先识别体裁与子体裁，再按原书目录、章节、小标题或可识别结构逐级总结。
- 非虚构、学术、商业/自助、哲学类侧重中心论点、论证链条、证据、概念框架与局限。
- 小说/文学类侧重情节结构、人物弧光、主题、叙事技巧、意象与情感基调。
- 历史/传记/回忆录类侧重历史脉络、关键人物、因果关系、作者视角与偏向。
- 混合或其他体裁必须跟随原书自有结构，不得强行套用单一类别模板。
- 不得虚构情节、观点、引文、页码或作者意图。

## 交付与顶层目录约束

- 最终只保留一个正式总结产物：`{OUTPUT_TARGET}`。
- 不要在书籍目录顶层生成或保留长篇最终质检报告。
- A/B accepted artifacts、quarantine attempts、校验记录和仲裁记录应保留在 `conversion/review/` 下。
- 会话中只输出浓缩版质检说明，简要列出：
  - 多书模式 A/B 结构化材料是否通过校验。
  - 关键修订点。
  - 主线程仲裁结果。
  - 残余风险。
