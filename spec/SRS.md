# 软件需求规格总索引（MVP1 v2.0）

本文件只索引当前需求，不再重复初始构想的完整产品愿景。优先级：context全局边界 → mvp1-scope范围 → 各模块Spec可验收行为 → 架构实现方案。遇到冲突先修文档，不任意挑一份实现。

| 需求组 | 规范来源 | 当前承诺 |
| --- | --- | --- |
| FR-WORLD | [M1](module-01-world-time.md) | 固定场景、day=0、控制、展示、一次短缺 |
| FR-LIFE | [M2](module-02-resident-life.md) | 整数经济、需求、社交、资金守恒 |
| FR-PROFILE | [M3](module-03-digital-resident.md) | 16KiB、30+1、白名单授权导入 |
| FR-DECISION | [M4](module-04-public-decision.md) | 固定议案、整数计票、120成本、一次执行 |
| FR-EVIDENCE | [M5](module-05-audit-snapshot.md) | 事件、5MiB快照、版本1、复现 |

原始愿景中的模型、多模板、历史模拟与玩家模式列入 [阶段计划](../plans/phase-1.md) 的后续范围，不计入当前验收。

所有20条AC的任务与测试映射见 [traceability](../docs/traceability.md)。本轮是需求文档交付，正式系统尚未实现。
