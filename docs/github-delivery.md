# GitHub发布与看板交付

## 2026-11-20 最新版本提交

用户已授权提交当前v2全部代码及原课程作业交付。本次内容、阅读路径和验证边界见[完整交付目录](submission-2026-11-20.md)。v1课程基线、冷启动原始证据与既有Git历史保留；v2包含Vue/Phaser前端、FastAPI后端、数据库迁移、AI规划、测试与运维资料。各阶段仅本地验证的记录保留原日期，不改写为当时已经远端发布。

下面的PR、Issue和看板信息是此前v1交付记录；不将本次代码提交视为补齐人工评审、ADR签字或云端部署。

## v1 交付历史
原文档重建[Issue #5](https://github.com/Lzz131419/town-simulation-project-docs/issues/5)与[PR #6](https://github.com/Lzz131419/town-simulation-project-docs/pull/6)已完成合并，原文档基线为历史提交03c9856。用户随后授权正式开发，工程通过堆叠PR交付。2026-11-19按用户明确授权，PR #20–#32、#35、#36共15项全部合入main（合并节点c781657），未强推或覆盖历史。

12项任务Issues #7–#18及任务分支/PR已发布，准确对应见[工程进度](engineering-progress.md)与[tasks.json](../plans/tasks.json)。启动治理为[Issue #19](https://github.com/Lzz131419/town-simulation-project-docs/issues/19)，中文像素界面改造为[Issue #33](https://github.com/Lzz131419/town-simulation-project-docs/issues/33)。

## 看板
[雾河镇 MVP1 工程任务](https://github.com/users/techcswang-cpu/projects/1)具有Backlog、This Week、In Progress、Review、Done五个状态。此前核验12项任务均已录入Review；治理/评审工作进入This Week。本次未修改看板状态，截图保留当时记录。保留私有可见性，不改变仓库或成员权限；未确认仓库Projects页的关联。

## 第6周文档PR演练
课程要求README-only文档PR及非作者评审；原PR #6是多文件重建，不能冒充该项练习。独立练习[Issue #34](https://github.com/Lzz131419/town-simulation-project-docs/issues/34)与[PR #35](https://github.com/Lzz131419/town-simulation-project-docs/pull/35)已创建，分支`docs/issue-34-readme-navigation`基于main，git diff确认仅修改README.md；PR #35已于2026-11-19合并，首次阅读路径保留在最新版README中；非作者人工评审仍待完成。工程PR也不能代替人工签字。

## 发布与合并检查
本地执行文档校验、规则测试、机制探针与浏览器验证；保存测试日志、快照、性能样本和桌面截图。合并节点c781657的GitHub Actions [Validation #44471378893](https://github.com/Lzz131419/town-simulation-project-docs/actions/runs/44471378893)已通过。各任务按依赖顺序将base重定向至main后合并；最后解决README导航冲突，保留新版README与阅读路径，核验合并树与最新工程版本一致。合并不代表已有非作者批准或ADR签字。

## 回滚
保留Git历史，以revert对应提交回滚；不强推、不删除仓库和他人Issue/PR。原HTML探针保持历史用途。
