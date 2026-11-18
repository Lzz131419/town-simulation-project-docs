# 技术探针

探针只验证所声明的机制或交互风险，不等于正式MVP1实现。代码不进入src/。

| 探针 | 用途 | 状态 |
| --- | --- | --- |
| [atomic-replay-probe.mjs](atomic-replay-probe.mjs) | 副本原子性、revision、RNG续跑 | 实际结果见[报告](atomic-replay-result.md) |
| [town-simulation-spike.html](town-simulation-spike.html) | 历史交互方向 | 原样保留，已知缺陷见[说明](town-simulation-spike.md) |
| 浏览器契约Mock | 交互和性能假设 | 仅[计划](plan.md)，未执行 |

没有把探针的硬编码数值或测试通过当成正式业务通过。
