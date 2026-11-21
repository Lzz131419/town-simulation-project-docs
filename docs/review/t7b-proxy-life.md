# T7b：离线玩家代理生活

## 完成结果

基于 W1 + W2 + T7a 共享未提交改动实现；未回滚、未暂存、未提交，未修改数据库 schema。后端全量 **330 passed**（原基线 320，新增 10 项参数化后用例），前端 `npm run build` 通过，`git diff --check` 通过。

## 离线判定调查与采用方案

- 原有 `POST /api/auth/logout` 在注销 session、断开其 WebSocket 后调用 `runtime.record_departure`。
- 原有 `api/realtime.py` 的 WebSocket finalizer、runtime 的发送失败处理和心跳超时（20 秒）/会话失效处理也调用同一个入口；只要同一玩家还有活跃连接，`runtime.online(uid)` 阻止记录离开。
- 原有 Departure 只存 tick、cash、completed，既不切换 mode，也不标记是否已回归；重复断线会覆盖起点。原有 `GET /api/return-summary` 只查询有限近期事件和快照差值。
- `api/profile.py` 不参与离线判定；`services/commands.py` 负责主动 action/manual 和 control 的 mode 变更；有限计划完成/失败由 domain/plans.py 切换 manual。
- 采用方案 a：复用所有现有离开入口，checkpoint 记录 `mode_at_departure`、`tick`、`event_id`、`away`，mode 临时切 rules。增加 world JSON 内的 `proxy_life` 标记，让该玩家走 NPC 默认日程、天气和无 personality 默认分支，保留其玩家身份；先执行已有任务/计划，之后持续 fallback。
- 登录、现有回归摘要接口、WebSocket 重连均恢复原 mode；manual 回归同时取消托管尚未完成的路径/任务。返回摘要固定保存在 checkpoint，重复读取不把在线期间的新行为计入摘要；新一轮离开建立新 checkpoint。
- Departure 与 world mode 的修改共同使用 runtime 世界锁和同一数据库事务，避免 tick 覆盖；离线记录幂等，WebSocket 清理阶段屏蔽 cancellation 直至 checkpoint 完成；登录密码校验继续在线程中执行，不阻塞健康检查。

## 摘要口径和前端

- 从 Event 表按离开 tick 和 event id 边界汇总，event id 区分同一 tick 离开前后的事件；不新增流水表。
- 自己的行动从 before/after 计算现金流入、现金流出和正向库存增量，兼容易腐品批次数组；levy、订单收入、托管扣款/退款按结构化详情计入。
- `earned` / `spent` 为现金流入/流出：订单托管退款计流入，锁定资金计流出；`cash_change` 仍单独显示实际余额变化，退款不额外创造钱。
- 他人发起的赠礼、采购交付、聚餐根据 partner_id/buyer/participants 归属玩家，不漏掉被动参与。订单事件补充 item/quantity/refund，变质事件补充 items，均为现有 JSON details 扩展。
- `gained_items` 表示本段期间各事件正向收获之和，不是净库存变化；消耗、出售不冲减已收获数量。关键事件模板化，最多 5 条，原 recent 最多 8 条仍兼容。
- 复用 ReturnDialog，展示 away_ticks、收入/支出及关键事件；不再要求 completed > 0 才展示，只有损耗/被动收入时也可看到摘要。前端先取得回归摘要再加载 world，避免显示恢复前的 mode；WebSocket 自动重连通过 return_summary 消息展示本次摘要。

## 测试覆盖与兼容调整

新增 `backend/tests/test_proxy_life.py` 覆盖手动玩家离线后自动行动、跨天 levy、资金守恒、三种 mode 的恢复、重复离开幂等、新离开周期、未离开玩家保持 manual、同 tick 事件边界、精确现金/物资聚合、他人发起聚餐/赠礼/订单、真实变质、WebSocket 断线重连及其他连接仍在线的保护、默认日程和天气分支。

原 `test_offline_plan_runs_to_completion_without_model_calls` 要求离线有限计划执行两步后永久停止，与本次持续托管需求冲突；已改为验证计划完成后持续规则生活、无模型调用、回来恢复原 plan mode。其他有限计划的在线停止测试保留且通过。

## 本任务修改文件

- backend/app/services/proxy_life.py（新增）
- backend/app/runtime.py
- backend/app/api/auth.py
- backend/app/api/realtime.py
- backend/app/api/world.py（在已有 T7a 改动之上，仅替换 return-summary 实现和移除不用的 import）
- backend/app/domain/scheduler.py（在已有改动之上增加 proxy 默认日程、变质分类及退款详情）
- backend/app/domain/orders.py（在已有改动之上补充结构化事件详情）
- backend/tests/test_proxy_life.py（新增）
- backend/tests/test_plan_queue.py
- frontend/src/stores/town.ts（在已有改动之上接收摘要、调整回归加载顺序和展示条件）
- frontend/src/components/dialogs/ReturnDialog.vue
- docs/review/t7b-proxy-life-example.json（真实临时数据库闭环结果）
- docs/review/t7b-proxy-life.md（本报告）

## 全量 pytest 尾部

命令：`cd backend && ../.venv/bin/python -m pytest tests -x -q`

```text
........................................................................ [ 21%]
........................................................................ [ 43%]
........................................................................ [ 65%]
........................................................................ [ 87%]
..........................................                               [100%]
330 passed in 18.69s
```

## 前端构建尾部

命令：`cd frontend && npm run build`

```text
> mist-river-town-client@2.0.0 build
> vue-tsc -b && vite build

vite v6.4.6 building for production...
transforming...
✓ 1661 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                        0.48 kB │ gzip:   0.35 kB
dist/assets/index--1pBi-2w.css        50.98 kB │ gzip:  10.73 kB
dist/assets/phaser-CkuN5Vkn.js         0.47 kB │ gzip:   0.34 kB
dist/assets/TownScene-Bcj3JaL_.js     41.01 kB │ gzip:  16.80 kB
dist/assets/index-CFLxbUyy.js        203.69 kB │ gzip:  73.29 kB
dist/assets/phaser-Czz4FBZH.js     1,481.77 kB │ gzip: 339.84 kB
✓ built in 3.35s
```

## 共享工作树 git diff --stat

以下包含此前 W1/W2/T7a 的未提交改动，不能全部归属 T7b；git diff --stat 不列未跟踪文件，本任务新增文件已在上方单独列出。

```text
 backend/app/api/auth.py                          |  21 ++-
 backend/app/api/realtime.py                      |   8 +-
 backend/app/api/world.py                         |  35 ++--
 backend/app/balance.py                           |  89 ++++++++++
 backend/app/catalog.py                           |  22 +++
 backend/app/domain/actions.py                    | 165 ++++++++++++-----
 backend/app/domain/deliveries.py                 |  10 +-
 backend/app/domain/economy.py                    |  36 ++++
 backend/app/domain/migration.py                  |  32 +++-
 backend/app/domain/orders.py                     |  49 +++--
 backend/app/domain/rules.py                      |   5 +-
 backend/app/domain/scheduler.py                  | 216 ++++++++++++++++++++---
 backend/app/pathfinding.py                       |  17 +-
 backend/app/realtime/protocol.py                 |   6 +
 backend/app/runtime.py                           |  56 ++++--
 backend/app/services/history.py                  |   6 +-
 backend/tests/test_districts.py                  |   7 +-
 backend/tests/test_map_expansion.py              |  11 +-
 backend/tests/test_plan_queue.py                 |  10 +-
 backend/tests/test_reliability.py                |   1 +
 backend/tests/test_world.py                      |   3 +-
 frontend/src/components/DeliveryBoard.vue        |   8 +-
 frontend/src/components/EventDetails.vue         |   8 +-
 frontend/src/components/RecipeBook.vue           |  12 +-
 frontend/src/components/TownInspector.vue        |  74 ++++++--
 frontend/src/components/charts/ResourceChart.vue |   4 +-
 frontend/src/components/dialogs/PlaceDialog.vue  |   4 +-
 frontend/src/components/dialogs/ReturnDialog.vue |  14 +-
 frontend/src/game/Atmosphere.ts                  | 131 +++++++++++++-
 frontend/src/game/ResidentLayer.ts               |  23 ++-
 frontend/src/game/TownScene.ts                   |  47 ++++-
 frontend/src/game/art/map.ts                     |   5 +-
 frontend/src/game/art/vegetation.ts              |  39 +++-
 frontend/src/game/scene-types.ts                 |   5 +-
 frontend/src/realtime/protocol.ts                |  19 +-
 frontend/src/stores/town.ts                      |  21 ++-
 frontend/src/types.ts                            |  17 +-
 frontend/src/views/MarketView.vue                | 123 ++++++++++++-
 frontend/tests/map.spec.ts                       |  22 ++-
 39 files changed, 1155 insertions(+), 226 deletions(-)
```

## 离开 → 托管 → 回归 JSON 样例

在独立临时 SQLite 数据库运行真实 API 登录/manual 控制/登出、180 次 runtime.mutate(tick_world)、再次登录和 GET return-summary；未修改开发运行数据库。完成 20 次行动，收入 84 镇币、支出维护金 2 镇币，余额增加 82，世界总资金始终 2840。

```json
{
  "departure": {
    "tick": 0,
    "cash": 80,
    "completed": 0,
    "mode_at_departure": "manual",
    "away": true,
    "event_id": 2
  },
  "return_summary": {
    "since_tick": 0,
    "current_tick": 180,
    "away_ticks": 180,
    "completed": 20,
    "cash_change": 82,
    "recent": [
      "王崛完成公共工作，获得6镇币",
      "王崛完成公共工作，获得6镇币",
      "王崛完成公共工作，获得6镇币",
      "王崛完成公共工作，获得6镇币",
      "王崛吃一份面包",
      "王崛完成公共工作，获得6镇币",
      "王崛回家休息，恢复精力",
      "王崛回家休息，恢复精力"
    ],
    "summary": {
      "earned": 84,
      "spent": 2,
      "gained_items": {},
      "events": [
        "你赚了84镇币，支出了2镇币"
      ]
    }
  },
  "restored_mode": "manual",
  "economy_total_before": 2840,
  "economy_total_after": 2840
}
```

## 验证范围

本次验证为真实后端 API/数据库/调度器闭环、全量后端回归和前端生产构建；未进行浏览器截图或视觉验收。离线判定沿用现有连接和登出生命周期，未引入新会话系统，也未额外把“从未连接过的玩家”自动标为离开。
