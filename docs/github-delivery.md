# GitHub发布与看板交付

## 当前状态
原文档重建[Issue #5](https://github.com/Lzz131419/town-simulation-project-docs/issues/5)与[PR #6](https://github.com/Lzz131419/town-simulation-project-docs/pull/6)已完成合并，main为03c9856。用户随后授权正式开发，工程通过堆叠PR交付，未强推或覆盖历史。

12项任务Issues #7–#18及任务分支/PR已发布，准确对应见[工程进度](engineering-progress.md)与[tasks.json](../plans/tasks.json)。启动治理为[Issue #19](https://github.com/Lzz131419/town-simulation-project-docs/issues/19)，中文像素界面改造为[Issue #33](https://github.com/Lzz131419/town-simulation-project-docs/issues/33)。

## 看板
[雾河镇 MVP1 工程任务](https://github.com/users/techcswang-cpu/projects/1)具有Backlog、This Week、In Progress、Review、Done五个状态。12项任务均已录入Review；治理/评审工作进入This Week。保留私有可见性，不改变仓库或成员权限；未确认仓库Projects页的关联。

## 第6周文档PR演练
课程要求README-only文档PR及非作者评审；原PR #6是多文件重建，不能冒充该项练习。独立练习[Issue #34](https://github.com/Lzz131419/town-simulation-project-docs/issues/34)与[PR #35](https://github.com/Lzz131419/town-simulation-project-docs/pull/35)已创建，分支`docs/issue-34-readme-navigation`基于main，git diff确认仅修改README.md；人工评审与合并仍待完成。工程PR也不能代替人工签字。

## 发布与合并检查
本地执行文档校验、规则测试、机制探针与浏览器验证；保存测试日志、快照、性能样本和桌面截图。GitHub Actions当前未查询到运行记录，不能称远程CI通过。上游PR合并后重新选择base并核对增量，不跳过依赖或伪造批准。

## 回滚
保留Git历史，以revert对应提交回滚；不强推、不删除仓库和他人Issue/PR。原HTML探针保持历史用途。
