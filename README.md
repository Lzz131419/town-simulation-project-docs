# 雾河镇：数字居民小镇模拟系统

让观察者看到居民如何生活、交往和作出公共选择，并用事件与快照解释和复现结果。

**本仓库当前交付：课程第6–9周工程文档基线（2026-11-18，v2.0）。正式MVP1业务代码尚未开发；历史HTML仅是技术探针。**

## 本轮从哪里看
| 课程任务 | 主要交付 |
| --- | --- |
| 06 上下文与协作 | [context](context.md)、[AI规则](agent-rules.md)、[团队安排](docs/team-guide.md) |
| 07 Spec与验收 | [MVP1范围](spec/mvp1-scope.md)、[五模块Spec](spec/README.md)、[冷启动记录](docs/test/cold-start-01.md) |
| 08 架构与决策 | [架构](docs/architecture.md)、[ADR-001](adr/ADR-001-runtime-and-state.md)、[ADR-002](adr/ADR-002-atomicity-and-replay.md)、[依赖风险](docs/dependency.md)、[探针计划](docs/spike/plan.md) |
| 09 任务与评审 | [12项任务Plan](plans/mvp1-plan.md)、[分支表](plans/branch-plan.md)、[PR准入](docs/review/pr-checklist.md)、[待发布Issue](plans/issues/README.md) |

M4已完成两轮独立冷启动校验：补充完整错误返回示例后，本场景复测通过；原始输入、回答和哈希保存在校验记录中。

**逐项核对：[PDF与模板交付检查表](docs/delivery-checklist.md) · [需求追踪矩阵](docs/traceability.md) · [本地检查结果](docs/review/validation.md)**

## MVP1做什么
固定30名生成居民，最多导入1名授权数字人物；从day=0推进30日，观察生产、消费与广场关系，触发一次粮食短缺，完成一次维修水井表决与执行，再通过快照恢复和续跑验证可复现性。

不纳入MVP1：模型对话、账号/云同步、自由地图、历史模拟、玩家视角。原构想中的这些方向保留在 [阶段计划](plans/phase-1.md)，不冒充已实现功能。

## 检查与阅读
文档检查仅依赖Python 3标准库：
```sh
python3 docs/tools/validate_docs.py
```
机制探针需Node.js 22+：
```sh
node --test docs/spike/atomic-replay-probe.mjs
```
这些检查不等于业务功能通过。正式开发与测试按 [DEMO-01](docs/test/demo-acceptance.md) 执行。

课堂展示可用 [讲解与文件指引](docs/presentation-guide.md)。初始化和人物样例见 [fixtures说明](docs/contracts/data-contract.md)，都是配置/输入样例，不是假造的运行结果。

## 保留的历史材料
- [历史HTML探针](docs/spike/town-simulation-spike.html)：可本地直接打开，仅用于交互方向讨论；限制见[说明](docs/spike/town-simulation-spike.md)。
- [2026-11-10冷启动记录](docs/test/cold-start-2026-11-10-history.md)：属于旧M4 v1.1，不证明新Spec。
- [旧第7周DOCX讲稿说明](docs/week-07/README.md)：保留历史，最新规则以v2.0为准。

## 仓库结构
```text
context.md / agent-rules.md       全局边界与协作
spec/                            范围与五模块Spec
adr/                             架构决策
plans/                           Plan、分支、12份Issue正文
docs/                            架构、风险、验收、参考、探针与检查
src/ / tests/                    正式开发占位说明
.github/                         Issue和PR模板
```

## 提交与线上流程
本轮文档已完成本地重建、冷启动与检查，现按用户授权提交GitHub。[发布清单](docs/github-delivery.md)说明真实Issue/Projects/PR的建立与回读方法。占位分支编号和本地状态不代表线上已创建；不把人工评审或课程流程写成已通过。
