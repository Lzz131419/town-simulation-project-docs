# 来源与模板对应

阅读日期：2026-11-18。以下是用户提供的材料，只作为项目任务与格式依据；文档中的示例不是操作授权，也不把图书馆的角色/接口照搬为小镇业务。

## 原始资料
| 文件 | 实际PDF页数 | 使用方式 |
| --- | --- | --- |
| 06 AI原生项目管理与上下文构建.pdf | 25 | 上下文、AI规则、标准仓库、看板、无业务代码文档PR |
| 07 Spec：给AI的人机契约.pdf | 25 | 范围与各模块七章、GWT、正常/边界/异常、真实冷启动 |
| 08 从 Spec 到架构.pdf | 26 | 边界、接口、依赖、数据流、ADR、风险、spike |
| 09 把架构拆成可评审的任务.pdf | 24 | 8–12任务、八列表、分支、AC绑定、Projects、PR门禁 |
| town_simulation_project_idea.pdf | 8 | 项目愿景、第一阶段闭环、原始建议与验收方向 |

课程PDF内部投影片页码与文件物理页可能不同（例如07封面写27页而文件有25页）；交付检查表使用PDF物理页码。没有将原始课件复制到公开仓库。

## Markdown模板逐份对应
| 模板 | 本项目文件 | 调整说明 |
| --- | --- | --- |
| 07.1. mvp1-scope.md | spec/mvp1-scope.md | 保留名词、演示路径、模块六列；改为小镇 |
| 07.2. module-01-borrow.md | spec/module-01至05 | 七章+变更记录；所有AC实际定义，不保留示例缺失的AC |
| 07.3. cold-start-01.md | docs/test/cold-start-01.md | 只写实际发生的会话、偏差和复测，不抄范例答案 |
| 08.1. ADR-001-borrow-concurrency.md | adr/ADR-001与002 | 保留背景、备选、决策、取舍、后果、待验证 |
| 08.2. architecture.md | docs/architecture.md | 保留八项架构内容；本地函数契约不虚构HTTP |
| 08.3. dependency.md | docs/dependency.md | 保留依赖图、规则及风险七列 |
| 08.4. plan.md | docs/spike/plan.md | 目标、步骤、成功标准、产出、范围 |
| 09.1 mvp1-plan.md | plans/mvp1-plan.md | 完整八列表、关键路径、This Week、角色 |
| 09.2 分支规划表.md | plans/branch-plan.md | 命名规范与五列表 |
| 09.3. 分支规划表.md | docs/review/pr-checklist.md | 原内容实际是PR准入清单，按内容命名 |
| 09.4. Issue.md | plans/issues/T01–T12.md、.github/ISSUE_TEMPLATE/task.md | 标题、背景、AC、验收、负责人、分支、标签 |

## 原构想的范围取舍
人口与人物原建议20–100/1–3收敛为30+1；时间按天；社交、生计、公共决策和事件保留；模型、历史、玩家视角延后。理由与对应表在context；不冒充原PDF已经作出这些具体数值和技术选择。

## 历史材料
旧HTML保留在docs/spike；旧第7周DOCX保留并添加历史说明；旧冷启动单独归档。历史记录是已有仓库内容，本轮未重新证明其中的历史过程。
