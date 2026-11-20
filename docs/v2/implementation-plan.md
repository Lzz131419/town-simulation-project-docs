# v2 本地实现计划与实际状态

日期：2026-11-19。以下是本地工作的可审核状态，不代表创建了新 GitHub Issue、PR 或云端发布。成果按小组共享，不虚构个人完成记录。

## 当前工作包

| 编号 | 工作包 | 依赖 | 验收 | 状态与入口 |
| --- | --- | --- | --- | --- |
| V2-T01 | 范围、架构和技术变更 | 无 | V2-AC-01–21 | 本地完成；docs/v2、ADR-003 |
| V2-T02 | FastAPI、数据模型、固定账号 | T01 | AC-01、02 | 本地完成；backend/app/api/auth、models |
| V2-T03 | 共享时钟、WebSocket、持久化 | T02 | AC-01、03、11 | 本地完成；runtime、api/realtime |
| V2-T04 | 寻路、生计、规则与预算 | T03 | AC-03、04、09 | 本地完成；domain、pathfinding |
| V2-T05 | 市场、订单与共建 | T04 | AC-05、06 | 本地完成；domain/orders、actions |
| V2-T06 | 模型适配与 LangGraph | T03、T04 | AC-07、08 | 实现完成，模拟测试通过；真实模型待配置 |
| V2-T07 | 留言、归档、回归与记录 | T03 | AC-10、11、12 | 本地完成；api/messages、archives、world |
| V2-T08 | Vue 工作区与 Phaser 地图 | T04、T05、T07 | AC-01、03、10、11 | 本地完成；frontend/src |
| V2-T09 | 纸面线稿主题、职责拆分 | T06、T08 | 非功能要求 | 本地完成；views、composables、styles、api、domain |
| V2-T10 | 自动化联调、启动与交付资料 | T01–T09 | 全部 | 本地验证；详情见 verification |
| V2-T11 | 高清原创场景、四向人物、相机与地图工具 | T08 | AC-13 | 本地完成；game/art、ResidentLayer、Atmosphere、TownMap |
| V2-T12 | 个人成长目标、徽章与旧数据兼容 | T04、T05、T11 | AC-14 | 本地完成；domain/progression、TownJournal、useProgress |
| V2-T13 | 指定邻居交流与关系反馈 | T04、T11 | AC-15 | 本地完成；domain/actions、TownInspector |
| V2-T14 | 增量同步、慢连接隔离、请求取消与网络恢复 | T03、T08 | AC-16、17 | 本地完成；realtime、runtime、api.ts |
| V2-T15 | 资金回流、NPC日程、经济采样和图表 | T04、T07 | AC-18、19 | 本地完成；economy、scheduler、history、charts |
| V2-T16 | 基础指标、日志与PostgreSQL备份配方 | T03 | 运维检查 | 指标与脚本本地检查通过；真实PG恢复未验收 |
| V2-T17 | 共享地图几何、东岸/南岸、桥梁与分区导航 | T11、T14 | AC-20 | 本地实现；shared/world-map、art、pathfinding、地图迁移 |
| V2-T18 | 新资源循环、工具、食品及新商品订单/托管 | T04、T05、T17 | AC-21 | 本地实现；domain/recipes、catalog、actions、scheduler |
| V2-T19 | 有限计划队列、冲突编辑与失败暂停 | T04、T18 | AC-22 | 本地完成；domain/plans、PlanQueue、usePlanQueue |
| V2-T20 | 手作街区、商埠、新生产链与社区交付 | T17、T18、T19 | AC-23 | 本地完成；domain/deliveries、DeliveryBoard、art/districts、art/industry |
| V2-T21 | 后端异步读写、取消协调、健康检查、版本迁移与覆盖率门禁 | T03、T06、T16 | AC-16、17、24 | 本地完成；infrastructure、bootstrap、migrations、test_backend_engineering |

以上状态中的“完成”指代码已实现并在列明环境验证，不代表完整远景玩法已经完成。模型服务与外部部署有独立验证门槛。

## 仍需真实环境验证

1. 使用成员自己的模型配置，实际测试兼容性、规划质量、错误反馈与服务商计费记录。
2. 确定远程运行环境后，验证 PostgreSQL、容器构建、浏览器多人访问、持久化卷与恢复。
3. Alembic 与旧库升级演练已实现；下一步在真实 PostgreSQL 验证迁移/恢复，再评估实体拆表、历史归档和水平扩展。
4. 六名成员实际试玩，评估订单和共建是否形成合作，再排独立店铺、NPC 个性和长程目标。

## 提交约束

2026-11-20用户明确授权将最新代码与原课程材料全部提交到现有GitHub仓库。本次允许commit/push到main，保留旧版代码与历史，不强制推送，不修改既有Issue/看板或虚构人工评审。此前各轮“仅本地”的验证记录保留为当时事实。提交范围见[交付目录](../submission-2026-11-20.md)。

## Review 准备

新版本的自动化测试、运行方法、模块依赖与真实局限已经记录。后续提交应以 v2 新范围描述变更，不沿用 v1“无依赖、无后端、无模型”的描述，也不把本地验证当作人工评审或云端 CI 通过。
