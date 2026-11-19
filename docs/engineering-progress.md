# MVP1 工程进度

2026-11-18用户授权正式实现，随后要求中文原创像素小镇桌面界面。原文档基线保留在历史提交03c9856。2026-11-19按用户明确授权，PR #20–#32、#35、#36共15项已全部合入main，合并节点为c781657；代码、测试、最新桌面截图与文档均已进入主分支。

## 已实现与验证
五模块与DEMO-01已实现，44项本地Node测试通过；浏览器性能与完整文件恢复通过。最新界面、桌面尺寸和原始证据见[验收记录](test/implementation-results.md)。合并节点c781657的远端[Validation #44471378893](https://github.com/Lzz131419/town-simulation-project-docs/actions/runs/44471378893)已通过，执行文档检查、机制探针与Node测试。

## 任务与PR
[工程看板](https://github.com/users/techcswang-cpu/projects/1)由当前协作者techcswang-cpu持有，保持私有；默认仓库为本项目，未变更成员权限，未声称已挂入仓库Projects页。此前记录的12项任务均为Review，治理/人工评审跟踪列入This Week，Done为空；本次未修改看板状态。[看板截图](test/evidence/project-board.png)记录五列与计数。

下表保留开发时的堆叠依赖；所有PR合并时的目标均为main，已按依赖顺序完成。合并状态不代表非作者人工评审结论。

| 任务 | 分支 | 开发时基于 | PR（均已合并） |
| --- | --- | --- | --- |
| SETUP | `docs/engineering-kickoff` | `main` | [#20](https://github.com/Lzz131419/town-simulation-project-docs/pull/20) |
| T01 | `feature/issue-7-schema` | `docs/engineering-kickoff` | [#21](https://github.com/Lzz131419/town-simulation-project-docs/pull/21) |
| T04 | `feature/issue-10-livelihood` | `feature/issue-7-schema` | [#22](https://github.com/Lzz131419/town-simulation-project-docs/pull/22) |
| T05 | `feature/issue-11-social-invariants` | `feature/issue-10-livelihood` | [#23](https://github.com/Lzz131419/town-simulation-project-docs/pull/23) |
| T06 | `feature/issue-12-profile-import` | `feature/issue-11-social-invariants` | [#24](https://github.com/Lzz131419/town-simulation-project-docs/pull/24) |
| T07 | `feature/issue-13-profile-validation` | `feature/issue-12-profile-import` | [#25](https://github.com/Lzz131419/town-simulation-project-docs/pull/25) |
| T08 | `feature/issue-14-proposal-vote` | `feature/issue-13-profile-validation` | [#26](https://github.com/Lzz131419/town-simulation-project-docs/pull/26) |
| T09 | `feature/issue-15-proposal-execution` | `feature/issue-14-proposal-vote` | [#27](https://github.com/Lzz131419/town-simulation-project-docs/pull/27) |
| T10 | `feature/issue-16-snapshot-core` | `feature/issue-15-proposal-execution` | [#28](https://github.com/Lzz131419/town-simulation-project-docs/pull/28) |
| T11 | `test/issue-17-snapshot-validation` | `feature/issue-16-snapshot-core` | [#29](https://github.com/Lzz131419/town-simulation-project-docs/pull/29) |
| T02 | `feature/issue-8-world-control` | `test/issue-17-snapshot-validation` | [#30](https://github.com/Lzz131419/town-simulation-project-docs/pull/30) |
| T03 | `feature/issue-9-observer-ui` | `feature/issue-8-world-control` | [#31](https://github.com/Lzz131419/town-simulation-project-docs/pull/31) |
| T12 | `test/issue-18-integration-demo` | `feature/issue-9-observer-ui` | [#32](https://github.com/Lzz131419/town-simulation-project-docs/pull/32) |

中文前端重构跟踪[Issue #33](https://github.com/Lzz131419/town-simulation-project-docs/issues/33)，已合并[PR #36](https://github.com/Lzz131419/town-simulation-project-docs/pull/36)，分支`feature/issue-33-chinese-town-view`基于T12，包含最新桌面UI、相关源码格式整理与文档/证据同步。

## 尚未完成的人工流程
PR合并已按用户授权完成；至少一名非作者Review、ADR-001/002接受和课程任务Done仍待真实确认，不以合并替代这些流程。负责人是计划分工，成果按小组共同交付，不编造个人贡献。第6周README-only演练PR #35已合并，人工评审待办独立跟踪于[GitHub交付](github-delivery.md)。
