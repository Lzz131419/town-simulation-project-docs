# 分支规划表

## 命名规范
功能feature/issue-{编号}-{描述}；修复fix/...；探针spike/...；测试test/...；文档docs/...。编号必须是GitHub实际Issue号，不用T编号冒充。本轮按依赖逐项开发并创建有真实增量的堆叠分支；开发时的依赖见工程进度表；2026-11-19各PR均重定向至main并按依赖顺序合并。

## 规划表
| 任务ID | 分支名 | 负责人 | 依赖 | 计划完成 |
| --- | --- | --- | --- | --- |
| T01 | `feature/issue-7-schema` | 张果 | 无 | 依赖完成后2人日 |
| T02 | `feature/issue-8-world-control` | 王崛 | T01、T04、T05、T10 | 依赖完成后3人日 |
| T03 | `feature/issue-9-observer-ui` | 张果 | T02、T06、T07、T08、T09、T10、T11 | 依赖完成后3人日 |
| T04 | `feature/issue-10-livelihood` | 李展博 | T01 | 依赖完成后3人日 |
| T05 | `feature/issue-11-social-invariants` | 李展博 | T04 | 依赖完成后2人日 |
| T06 | `feature/issue-12-profile-import` | 孙祥 | T01 | 依赖完成后2人日 |
| T07 | `feature/issue-13-profile-validation` | 孙祥 | T06 | 依赖完成后2人日 |
| T08 | `feature/issue-14-proposal-vote` | 钱俊昊 | T01 | 依赖完成后2人日 |
| T09 | `feature/issue-15-proposal-execution` | 钱俊昊 | T08 | 依赖完成后2人日 |
| T10 | `feature/issue-16-snapshot-core` | 姚富恩 | T01 | 依赖完成后2人日 |
| T11 | `test/issue-17-snapshot-validation` | 姚富恩 | T10、T04、T05 | 依赖完成后2人日 |
| T12 | `test/issue-18-integration-demo` | 王崛 | T03 | 依赖完成后2人日 |

## PR策略
一个任务一个PR；未完成依赖不得通过复制临时代码绕过。通过AI辅助核对和至少1名非作者人工评审后合并，保留验收证据。变更治理文档也写清来源、范围和检查方式。

## 当前事实
12个真实Issue、12条任务分支和12个任务PR均已发布；另有启动PR与中文界面改造Issue #33。开发时base、PR链接与合并状态见[工程进度](../docs/engineering-progress.md)。15个工程与文档PR现已全部合并，main包含完整MVP1与最新中文桌面界面；非作者评审与ADR接受另行记录。
