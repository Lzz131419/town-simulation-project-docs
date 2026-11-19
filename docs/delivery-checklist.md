# 第6–9周交付要求对照与完成状态

> 2026-11-18；只记录可验证事实。课程资料是任务依据；文档基线已合并；当前工程实现已验证并通过堆叠PR交付，人工评审尚待完成。

## 第6周：上下文与项目管理
| PDF物理页 | 要求 | 本地交付 | 状态/证据 |
| --- | --- | --- | --- |
| 2、11–18 | context目标/场景/Non-Goals≥3/技术约束/禁依赖/风险/术语/变更 | [context](../context.md) | 已重写，7项非目标 |
| 14–17 | AI规则可执行、工具加载说明、白名单/验证 | [agent-rules](../agent-rules.md) | 已重写 |
| 11、19 | 标准目录；无正式业务实现 | src/tests说明、docs/spike | 该要求在文档基线03c9856满足；后续用户授权另进入正式工程实现 |
| 20–24 | Projects五列、有卡片；真实Issue和文档PR演练 | [线上发布清单](github-delivery.md) | 五列私有看板、12个Issue及任务PR已建立；README-only练习PR #35已创建，人工评审待完成，见发布清单 |

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
| 19–22 | spike计划；探针仅docs/spike，不进入src | [plan](spike/plan.md)、[实际结果](spike/atomic-replay-result.md) | 机制探针实际执行；正式实现另有浏览器性能原始样本 |

## 第9周：可评审任务
| PDF物理页 | 要求 | 本地交付 | 状态/证据 |
| --- | --- | --- | --- |
| 2、5–8、15 | 8–12任务、完整八列表、每任务AC或ADR绑定、1–3人日 | [Plan](../plans/mvp1-plan.md) | 12任务、27人日；每功能任务2条AC |
| 9 | 依赖顺序、并行、关键路径 | Plan+tasks.json | DAG无环；关键路径15工作日 |
| 10–11 | 任务分支、真实Issue号、PR准入 | [分支表](../plans/branch-plan.md)、[门禁](review/pr-checklist.md) | 真实Issue #7–#18与PR #21–#32已发布，等待人工Review |
| 12、15–16 | 全部任务录入Projects，This Week有卡片、Review已建 | [12份工单](../plans/issues/README.md) | 12项已录入Review，治理/评审进入This Week；看板仍为私有 |
| 13、24 | 负责人和角色轮换 | [团队](team-guide.md)、Plan | 六名真实组员分工建议；不虚构贡献或评审 |

## 最终验收边界
- 本地文档和静态检查结果见 [validation](review/validation.md)。
- 正式MVP1代码、39项本地测试、浏览器性能与桌面界面验证已完成，见[实现验收](test/implementation-results.md)；不代表人工验收或已合并main。
- 文档提交与开发任务看板分开核验：线上Projects、工单/分支/PR已有真实链接；人工评审、ADR接受及合并仍待完成，不因实现通过预先勾选。
- 原PDF和模板只记录引用，不上传课件本身；保留仓库旧历史以便回滚。
