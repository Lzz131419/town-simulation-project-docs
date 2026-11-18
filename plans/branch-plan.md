# 分支规划表

## 命名规范
功能feature/issue-{编号}-{描述}；修复fix/...；探针spike/...；测试test/...；文档docs/...。编号必须是GitHub实际Issue号，不用T编号冒充。分支在依赖合并后从更新的main创建，不一次性创建12条空分支。

## 规划表
| 任务ID | 分支名 | 负责人 | 依赖 | 计划完成 |
| --- | --- | --- | --- | --- |
| T01 | `feature/issue-{number}-schema` | 张果 | 无 | 依赖完成后2人日 |
| T02 | `feature/issue-{number}-world-control` | 王崛 | T01、T04、T05、T10 | 依赖完成后3人日 |
| T03 | `feature/issue-{number}-observer-ui` | 张果 | T02、T06、T07、T08、T09、T10、T11 | 依赖完成后3人日 |
| T04 | `feature/issue-{number}-livelihood` | 李展博 | T01 | 依赖完成后3人日 |
| T05 | `feature/issue-{number}-social-invariants` | 李展博 | T04 | 依赖完成后2人日 |
| T06 | `feature/issue-{number}-profile-import` | 孙祥 | T01 | 依赖完成后2人日 |
| T07 | `feature/issue-{number}-profile-validation` | 孙祥 | T06 | 依赖完成后2人日 |
| T08 | `feature/issue-{number}-proposal-vote` | 钱俊昊 | T01 | 依赖完成后2人日 |
| T09 | `feature/issue-{number}-proposal-execution` | 钱俊昊 | T08 | 依赖完成后2人日 |
| T10 | `feature/issue-{number}-snapshot-core` | 姚富恩 | T01 | 依赖完成后2人日 |
| T11 | `test/issue-{number}-snapshot-validation` | 姚富恩 | T10、T04、T05 | 依赖完成后2人日 |
| T12 | `test/issue-{number}-integration-demo` | 王崛 | T03 | 依赖完成后2人日 |

## PR策略
一个任务一个PR；未完成依赖不得通过复制临时代码绕过。通过AI辅助核对和至少1名非作者人工评审后合并，保留验收证据。变更治理文档也写清来源、范围和检查方式。

## 当前事实
本轮文档重建使用`docs/issue-5-rebuild-weeks-06-09`，关联文档Issue #5。12项后续开发任务的线上Issue号、远程任务分支和PR尚未创建，故这些任务保留明确的编号模板。发布后更新本表、tasks.json与每份Issue正文；不得声称已经建立线上看板。
