# GitHub发布与看板交付

## 当前状态
本轮文档已完成重建、独立冷启动和静态检查，用户于2026-11-18授权提交GitHub。保留旧Git历史，以本次文档变更更新主分支。12份MVP1开发工单仍是待发布正文，线上Projects、开发任务Issue与非作者人工评审不因文档提交而自动完成。

## 本轮提交追踪
- 文档重建Issue：[#5](https://github.com/Lzz131419/town-simulation-project-docs/issues/5)。
- 文档分支：`docs/issue-5-rebuild-weeks-06-09`。
- 关联PR和最终main提交以该Issue的GitHub链接与合并记录为准。
- 本次文档提交不等同于12项开发工单已录入Projects或非作者评审完成。

## 1. 提交前检查
- 重新fetch并核对远程main是否仍是本次基线f62d04b，若有其他人更新，先合并核对，不强推覆盖。
- 运行文档校验与探针，保留结果；按本轮交付索引逐项复核。
- Git差异不应包含原始课程PDF、凭据、个人资料或新增src业务实现。
- 使用有写权限的GitHub登录；浏览器登录不等于本机Git已认证。

## 2. 第6周文档PR演练
先检查旧仓库是否已有可复用的真实PR证据；若不能满足课件要求，则创建一个README-only任务Issue，从更新的main切文档分支，仅调整README导航，按模板开PR，关联Issue，非作者人工评审后合并。这里“空PR”指无业务代码的文档PR，不是Git不允许的零diff PR。不能预写人工评审通过。

## 3. 第9周任务发布
逐一查重后把plans/issues/T01–T12创建为真实Issue；记录编号、URL和实际账号指派。随后用真实编号替换分支规划和Issue正文的{number}。不一次性开12个空分支。

## 4. GitHub Projects
在仓库关联的Project中建立Status选项Backlog、This Week、In Progress、Review、Done；录入全部12个MVP1 Issue。T01排入This Week，其余Backlog。Review列已建但可为空；只有实际PR出现后进入Review。验收与合并都有证据才进入Done。

## 5. 发布回读
保存Project URL、12个Issue URL、关联PR、各Status截图或API回读结果；确认卡片数量、负责人、AC、分支名和任务依赖一致。没有Project权限时报告缺项，不能用Markdown表声称线上看板完成。

## 6. 回滚
保留原Git历史，以revert本轮提交回滚文档；不删除仓库、不强推历史、不移除他人Issue或PR。原HTML探针继续只读演示。
