# 第6–9周交付要求对照与完成状态

> 2026-11-18；只记录可验证事实。课程资料是任务依据；本地交付已检查完成，现按用户授权提交GitHub。

## 第6周：上下文与项目管理
| PDF物理页 | 要求 | 本地交付 | 状态/证据 |
| --- | --- | --- | --- |
| 2、11–18 | context目标/场景/Non-Goals≥3/技术约束/禁依赖/风险/术语/变更 | [context](../context.md) | 已重写，7项非目标 |
| 14–17 | AI规则可执行、工具加载说明、白名单/验证 | [agent-rules](../agent-rules.md) | 已重写 |
| 11、19 | 标准目录；无正式业务实现 | src/tests说明、docs/spike | 静态检查；仅探针机制代码 |
| 20–24 | Projects五列、有卡片；真实Issue和文档PR演练 | [线上发布清单](github-delivery.md) | 待提交阶段操作；不声明已完成 |

## 第7周：范围、模块Spec与冷启动
| PDF物理页 | 要求 | 本地交付 | 状态/证据 |
| --- | --- | --- | --- |
| 2、5、19–20 | scope演示路径、模块清单、是否纳入/负责人/依赖 | [scope](../spec/mvp1-scope.md) | 已重写 |
| 6–15 | 每个MVP1模块七章、用户故事、GWT、正常/边界/异常 | [五模块](../spec/README.md) | 5模块、20条唯一AC；异常表对应实际AC |
| 16–18、21–23 | 干净会话只喂Spec，中立提问、偏差、修订和必要复测 | [冷启动](test/cold-start-01.md) | 已完成两轮独立校验；补充完整Result示例后，本场景复测通过；原始输入/回答与哈希已保存 |

## 第8周：架构与技术风险
| PDF物理页 | 要求 | 本地交付 | 状态/证据 |
| --- | --- | --- | --- |
| 2、5–12 | 模块边界、分层、依赖、接口成功/失败、数据流、冻结范围 | [architecture](architecture.md) | 已重写；明确尚待团队接受 |
| 13–16 | ≥1 ADR，≥2备选、取舍、后果、评审状态 | [ADR-001](../adr/ADR-001-runtime-and-state.md)、[ADR-002](../adr/ADR-002-atomicity-and-replay.md) | 两份提议，无伪造人工签名 |
| 17–19 | AI风险辅助评审、风险概率/影响/应对/负责人/验证 | [dependency](dependency.md)、[复核记录](review/baseline-review.md) | 已记录风险与静态发现 |
| 19–22 | spike计划；探针仅docs/spike，不进入src | [plan](spike/plan.md)、[实际结果](spike/atomic-replay-result.md) | 机制探针实际执行；浏览器性能Mock仍为计划 |

## 第9周：可评审任务
| PDF物理页 | 要求 | 本地交付 | 状态/证据 |
| --- | --- | --- | --- |
| 2、5–8、15 | 8–12任务、完整八列表、每任务AC或ADR绑定、1–3人日 | [Plan](../plans/mvp1-plan.md) | 12任务、27人日；每功能任务2条AC |
| 9 | 依赖顺序、并行、关键路径 | Plan+tasks.json | DAG无环；关键路径15工作日 |
| 10–11 | 任务分支、真实Issue号、PR准入 | [分支表](../plans/branch-plan.md)、[门禁](review/pr-checklist.md) | 模板已备；真实编号待发布 |
| 12、15–16 | 全部任务录入Projects，This Week有卡片、Review已建 | [12份工单](../plans/issues/README.md) | 本地待发布，线上操作未发生 |
| 13、24 | 负责人和角色轮换 | [团队](team-guide.md)、Plan | 六名真实组员分工建议；不虚构贡献或评审 |

## 最终验收边界
- 本地文档和静态检查结果见 [validation](review/validation.md)。
- 正式MVP1代码、业务测试、性能测试没有完成；当前交付的是课程第6–9周基线。
- 文档提交与开发任务看板分开核验：线上Projects、开发任务真实工单/分支编号、PR演练及人工评审仍按实际证据记录，不因文档上传预先勾选。
- 原PDF和模板只记录引用，不上传课件本身；保留仓库旧历史以便回滚。
