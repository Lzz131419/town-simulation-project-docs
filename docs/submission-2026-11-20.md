# 雾河镇完整交付目录

日期：2026-11-20。目标仓库：[Lzz131419/town-simulation-project-docs](https://github.com/Lzz131419/town-simulation-project-docs)，目标分支`main`。本次按用户授权提交当前v2工程、测试与验证材料，并保留最初第06–09周作业及v1代码历史。

## 建议阅读顺序

1. [项目README](../README.md)：项目用途、技术栈、账号和本地启动。
2. [原课程交付对照](delivery-checklist.md)：逐项对应四份PDF要求。
3. [v2产品设计](v2/product-design.md) → [Spec](v2/spec.md) → [架构](v2/architecture.md) → [任务与状态](v2/implementation-plan.md)。
4. [验证记录](v2/verification.md)、[后端工程审查](v2/backend-engineering.md)与[运行手册](v2/operations.md)：已验证内容、证据和剩余限制。

## 第06–09周作业材料

| 课程要求 | 本仓库入口 |
| --- | --- |
| 06：项目上下文、AI协作规则、项目管理 | [context](../context.md)、[agent-rules](../agent-rules.md)、[团队安排](team-guide.md)、[GitHub交付记录](github-delivery.md) |
| 07：范围、模块Spec、验收契约 | [MVP1范围](../spec/mvp1-scope.md)、[五模块Spec](../spec/README.md)，保留20条原版GWT验收标准 |
| 07：独立冷启动、偏差与复测 | [两轮冷启动校验](test/cold-start-01.md)，原始输入、回答及哈希清单保留在同目录 |
| 08：架构、接口、依赖与决策 | [原版架构](architecture.md)、[风险与依赖](dependency.md)、[ADR-001](../adr/ADR-001-runtime-and-state.md)、[ADR-002](../adr/ADR-002-atomicity-and-replay.md) |
| 08：风险验证探针与复核 | [Spike计划](spike/plan.md)、[实际结果](spike/atomic-replay-result.md)、[基线复核](review/baseline-review.md) |
| 09：任务、依赖、工单与评审 | [12项任务](../plans/mvp1-plan.md)、[工单材料](../plans/issues/README.md)、[分支计划](../plans/branch-plan.md)、[PR检查表](review/pr-checklist.md) |
| 原版实现与追踪 | [追踪矩阵](traceability.md)、[实现验收](test/implementation-results.md)、`src/`与`tests/` |

原PDF和软件工程模板作为参考来源，不重新上传课件。原课程要求中尚需真人完成的非作者评审、ADR接受等，继续如实标注；提交代码不代表这些要求自动完成。

## 当前v2工程

| 内容 | 路径及说明 |
| --- | --- |
| 前端 | `frontend/`：Vue 3、TypeScript、Phaser；中文多人地图、居民、AI计划、交易、订单、留言、归档与报表 |
| 后端 | `backend/app/`：FastAPI接口、领域规则、世界运行时、AI规划、同步协议与基础设施分层 |
| 数据库升级 | `backend/migrations/`：Alembic基线和查询索引；旧数据保留与重复升级验证 |
| 地图与配置 | `shared/world-map.json`、`backend/config/game.json` |
| 自动化测试 | `backend/tests/`、`frontend/tests/`；保留原版`tests/`及课程探针 |
| 工程启动与部署配方 | `scripts/`、`Dockerfile`、`compose.yaml`、`.env.example`、依赖锁文件 |
| 当前设计与证据 | `docs/v2/`、[ADR-003](../adr/ADR-003-shared-town-v2.md)；24项GWT验收标准 |
| 持续验证 | `.github/workflows/validation.yml`：文档、lint、覆盖率、数据库迁移、构建与原版回归 |

最新本地后端147项测试通过，语句覆盖率94.09%；独立测试库上19项浏览器回归通过。原始记录在[后端整改报告](v2/backend-engineering.md)。真实外部模型、PostgreSQL部署恢复及大规模多实例容量尚未验收；GitHub Actions执行结果应以本次提交对应的远端运行记录为准。

## 提交前复核

当前前端生产构建通过，原版44项规则回归和5项机制探针通过；文档检查覆盖75份Markdown及全部本地引用。记录：[构建](v2/evidence/publish-build.txt)、[v1回归](v2/evidence/publish-legacy.txt)、[机制探针](v2/evidence/publish-spike.txt)。后端及浏览器结果沿用本次代码对应的最新验证证据，本轮提交整理未改变业务实现。

## 启动与提交边界

从仓库根目录运行`npm run setup`，再运行`npm start`，访问`http://127.0.0.1:5173`。需要Node.js 22+和Python 3.12；默认固定成员账号见README。新环境启动时创建自己的数据库，不包含开发者的现有世界存档。

本次包含源码、锁文件、配置示例、课程材料、测试和有引用的验证证据。`.local/`数据库、密钥、真实模型配置、虚拟环境、依赖目录及构建缓存不纳入Git。保留历史，不删除旧课程资料或强制覆盖远端；仓库提交不等于上线一个公网可访问的多人服务器。
