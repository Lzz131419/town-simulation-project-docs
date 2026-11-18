# 需求—架构—任务—验证追踪矩阵

所有引用均指本轮基线v2.0（M4经冷启动补充为v2.1，业务与AC编号不变）；每个AC至少有一个实现任务和明确的测试意图。下列测试是未来实现验收，未执行状态不能写成通过。

| Spec/AC | 架构落点 | 任务 | 测试意图 | 状态 |
| --- | --- | --- | --- | --- |
| [M1-AC-01](../spec/module-01-world-time.md) | M1应用/展示 | T02 | 正常与配置/阈值校验；具体断言见该AC | 规划，未实现 |
| [M1-AC-02](../spec/module-01-world-time.md) | M1应用/展示 | T02 | 边界与异常路径；具体断言见该AC | 规划，未实现 |
| [M1-AC-03](../spec/module-01-world-time.md) | M1应用/展示 | T03 | 约束与副作用；具体断言见该AC | 规划，未实现 |
| [M1-AC-04](../spec/module-01-world-time.md) | M1应用/展示 | T03 | 确定性/失败完整性；具体断言见该AC | 规划，未实现 |
| [M2-AC-01](../spec/module-02-resident-life.md) | M2纯规则 | T04 | 正常与配置/阈值校验；具体断言见该AC | 规划，未实现 |
| [M2-AC-02](../spec/module-02-resident-life.md) | M2纯规则 | T04 | 边界与异常路径；具体断言见该AC | 规划，未实现 |
| [M2-AC-03](../spec/module-02-resident-life.md) | M2纯规则 | T05 | 约束与副作用；具体断言见该AC | 规划，未实现 |
| [M2-AC-04](../spec/module-02-resident-life.md) | M2纯规则 | T05 | 确定性/失败完整性；具体断言见该AC | 规划，未实现 |
| [M3-AC-01](../spec/module-03-digital-resident.md) | M3输入校验 | T06 | 正常与配置/阈值校验；具体断言见该AC | 规划，未实现 |
| [M3-AC-02](../spec/module-03-digital-resident.md) | M3输入校验 | T07 | 边界与异常路径；具体断言见该AC | 规划，未实现 |
| [M3-AC-03](../spec/module-03-digital-resident.md) | M3输入校验 | T06 | 约束与副作用；具体断言见该AC | 规划，未实现 |
| [M3-AC-04](../spec/module-03-digital-resident.md) | M3输入校验 | T07 | 确定性/失败完整性；具体断言见该AC | 规划，未实现 |
| [M4-AC-01](../spec/module-04-public-decision.md) | M4状态机 | T08 | 正常与配置/阈值校验；具体断言见该AC | 规划，未实现 |
| [M4-AC-02](../spec/module-04-public-decision.md) | M4状态机 | T08 | 边界与异常路径；具体断言见该AC | 规划，未实现 |
| [M4-AC-03](../spec/module-04-public-decision.md) | M4状态机 | T09 | 约束与副作用；具体断言见该AC | 规划，未实现 |
| [M4-AC-04](../spec/module-04-public-decision.md) | M4状态机 | T09 | 确定性/失败完整性；具体断言见该AC | 规划，未实现 |
| [M5-AC-01](../spec/module-05-audit-snapshot.md) | M5证据存储 | T10 | 正常与配置/阈值校验；具体断言见该AC | 规划，未实现 |
| [M5-AC-02](../spec/module-05-audit-snapshot.md) | M5证据存储 | T10 | 边界与异常路径；具体断言见该AC | 规划，未实现 |
| [M5-AC-03](../spec/module-05-audit-snapshot.md) | M5证据存储 | T11 | 约束与副作用；具体断言见该AC | 规划，未实现 |
| [M5-AC-04](../spec/module-05-audit-snapshot.md) | M5证据存储 | T11 | 确定性/失败完整性；具体断言见该AC | 规划，未实现 |
| [ADR-001](../adr/ADR-001-runtime-and-state.md)、[ADR-002](../adr/ADR-002-atomicity-and-replay.md) | Shared与事务边界 | T01 | 数据契约/夹具与纯函数依赖；SP-01机制探针 | 见探针实际结果 |
| [DEMO-01](test/demo-acceptance.md) | 单页全链路 | T12 | 30天、短缺、投票、快照继续运行、UI/性能证据 | 规划，未实现 |

功能任务各绑定2条AC，没有用一项“实现整个系统”任务掩盖颗粒度。AC内部的数据驱动边界属于同一操作的测试集合。集成任务不替代这些模块测试。
